import json
import re

from src.core.llm_engine import llm_engine
from src.core.prompt_templates import STAR_EVALUATION_PROMPT

DIMENSIONS = ("situation", "action", "result", "clarity", "technical_depth")


def _clamp(value, default=0) -> int:
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return default


def _extract_json(text: str):
    """Pulls the first JSON object out of a model reply, tolerating code fences and extra prose."""
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _normalize(data: dict) -> dict:
    """Guarantees every key the UI relies on exists with a sane type."""
    score = _clamp(data.get("score"), 0)
    breakdown = data.get("star_breakdown") if isinstance(data.get("star_breakdown"), dict) else {}
    dims_in = data.get("dimension_scores") if isinstance(data.get("dimension_scores"), dict) else {}
    strengths = data.get("strengths") if isinstance(data.get("strengths"), list) else []
    return {
        "score": score,
        "star_breakdown": {
            "situation_task": str(breakdown.get("situation_task", "N/A")),
            "action": str(breakdown.get("action", "N/A")),
            "result": str(breakdown.get("result", "N/A")),
        },
        "dimension_scores": {d: _clamp(dims_in.get(d), score) for d in DIMENSIONS},
        "strengths": [str(s) for s in strengths][:4],
        "improvement_tip": str(data.get("improvement_tip") or "Add one concrete, measurable result."),
        "source": "gemini",
    }


# --------------------------------------------------------------------------
# Offline estimate (used only when Gemini is unavailable). It is a rough
# heuristic on answer structure, and the UI labels it as an estimate.
# --------------------------------------------------------------------------
_SITUATION = ("when ", "situation", "project", "team", "context", "challenge", "problem", "company", "client",
              "deadline", "worked on", "we had", "our ")
_ACTION = ("i built", "i designed", "i implemented", "i led", "i developed", "i created", "i wrote", "i deployed",
           "i optimized", "i optimised", "i refactored", "i introduced", "i automated", "i migrated", "i analyzed",
           "i analysed", "i decided", "i proposed", "i set up", "i debugged", "i tested")
_RESULT = ("result", "resulting", "reduced", "improved", "increased", "achieved", "saved", "decreased", "delivered",
           "launched", "outcome", "led to", "as a result", "cut ")


def _estimate(answer: str) -> dict:
    text = answer.lower()
    words = len(answer.split())
    has_sit = any(k in text for k in _SITUATION)
    actions = sum(1 for k in _ACTION if k in text)
    has_res = any(k in text for k in _RESULT)
    has_num = bool(re.search(r"\d", answer))
    length = min(1.0, words / 100)

    dims = {
        "situation": 45 + (30 if has_sit else 0) + 25 * min(1.0, words / 60),
        "action": 40 + min(actions, 3) * 15 + 15 * min(1.0, words / 80),
        "result": 35 + (30 if has_res else 0) + (30 if has_num else 0),
        "clarity": 40 + 45 * length + (10 if answer.count(".") >= 2 else 0),
        "technical_depth": 40 + min(actions, 3) * 10 + (20 if has_num else 0) + 10 * length,
    }
    dims = {k: _clamp(v) for k, v in dims.items()}
    score = _clamp(0.2 * dims["situation"] + 0.3 * dims["action"] + 0.3 * dims["result"]
                   + 0.1 * dims["clarity"] + 0.1 * dims["technical_depth"])

    if not has_num:
        tip = "Add at least one number, such as a percentage, a latency, or a cost saved."
    elif not has_res:
        tip = "Finish with the outcome: what changed because of what you did?"
    elif words < 60:
        tip = "Expand the Action part: name the tools, the options you weighed, and why you chose one."
    else:
        tip = "Mention the trade-off you made and what you would do differently next time."

    strengths = []
    if has_sit:
        strengths.append("You set the scene")
    if actions:
        strengths.append("You described your own actions")
    if has_num:
        strengths.append("You used numbers")

    return {
        "score": score,
        "star_breakdown": {
            "situation_task": "Context is present." if has_sit else "Open with the situation and your task before the action.",
            "action": "Your own actions are described." if actions else "Say what YOU did, using first-person verbs.",
            "result": ("Outcome and numbers included." if has_res and has_num else
                       "Outcome mentioned; quantify it." if has_res else "No clear result yet; state the impact."),
        },
        "dimension_scores": dims,
        "strengths": strengths or ["You attempted a structured answer"],
        "improvement_tip": tip,
        "source": "offline",
    }


def evaluate_star_answer(question: str, answer: str) -> dict:
    """Grades a response with Gemini; falls back to a labelled offline estimate if Gemini is unavailable."""
    prompt = STAR_EVALUATION_PROMPT.format(question=question, answer=answer)
    response_text = llm_engine.generate(prompt)

    if response_text is None:
        return _estimate(answer)

    try:
        return _normalize(_extract_json(response_text))
    except Exception:
        return _estimate(answer)
