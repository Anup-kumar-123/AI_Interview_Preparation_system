"""
Guided Interview engine (profile -> role -> 10 questions -> projects -> report).

All state lives in one GuidedInterview object kept in st.session_state.
Gemini is used when available; every step has an offline fallback so the flow never breaks.
"""
import json
import random
import re
import uuid
from statistics import mean

from src.core.llm_engine import llm_engine
from src.core.prompt_templates import (
    INTERVIEW_REPORT_PROMPT, PROJECT_QUESTION_PROMPT, ROLE_QUESTION_SET_PROMPT,
)
from src.core.question_bank import (
    ROLE_TOPICS, level_from_years, offline_project_questions, offline_role_questions,
)
from src.services.evaluator import _clamp, _estimate, _extract_json
from src.utils.logger import logger

NUM_ROLE_QUESTIONS = 10

DIM_LABELS = {
    "technical_knowledge": "Technical knowledge",
    "problem_solving": "Problem solving",
    "communication": "Communication",
    "star_structure": "STAR structure",
    "depth": "Depth and detail",
    "impact": "Impact and results",
    "project_ownership": "Project ownership",
}

# (advice when the score is below 75, advice when it is 75 or more)
SUGGESTION_BANK = {
    "technical_knowledge": (
        "Rebuild your {role} fundamentals: pick the three topics you hesitated on, write a one-page summary of each, and explain them aloud without notes.",
        "Stretch your technical range: read one engineering article a week on advanced {role} topics and practise explaining the trade-offs.",
    ),
    "problem_solving": (
        "Practise thinking aloud: state the problem, list two options, compare their trade-offs, then commit to one. Interviewers score your reasoning as much as the answer.",
        "Practise harder open-ended problems under a timer, and ask clarifying questions before you start solving.",
    ),
    "communication": (
        "Keep answers to about two minutes: lead with the point, support it with one example, and close with a one-line takeaway.",
        "Record yourself answering and trim filler words so your delivery stays crisp.",
    ),
    "star_structure": (
        "Use STAR on every experience question: one sentence of Situation, one of Task, most of the time on Action, and finish with a concrete Result.",
        "After the Result, add a short 'what I learned' line to show growth.",
    ),
    "depth": (
        "Add specifics: name the tools, versions, data sizes and the options you rejected. Concrete detail makes an answer credible.",
        "Prepare one deep-dive story per key skill that can survive three follow-up questions.",
    ),
    "impact": (
        "End every story with a number, such as percent improvement, time saved or users affected. If you lack metrics, estimate the before and after.",
        "Link your numbers to business outcomes such as revenue, cost or customer satisfaction.",
    ),
    "project_ownership": (
        "For each project, prepare a 60-second pitch: the problem, your exact role, the key decision you made and the result. Say 'I' for what you did and 'we' only for team outcomes.",
        "Be ready to discuss what went wrong on your projects, how you would scale them, and what you would redo.",
    ),
}


def _unique(items):
    seen, out = set(), []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def _parse_list(text):
    """Extracts the first JSON array from a model reply."""
    if not text:
        return []
    cleaned = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _avg(values):
    return round(mean(values)) if values else 0


def readiness_label(score: int) -> str:
    if score >= 85:
        return "Interview-ready"
    if score >= 70:
        return "Strong, polish a few areas"
    if score >= 50:
        return "Developing, keep practising"
    return "Early stage, build the foundations"


class GuidedInterview:
    """State machine for the guided interview."""

    VERSION = 1

    def __init__(self):
        self.seen = []  # every role question already asked in this browser session (survives reset)
        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self):
        self.stage = "profile"  # profile | role | questions | projects | project_qa | report
        self.profile = {}
        self.role = ""
        self.questions = []
        self.answers = []
        self.q_idx = 0
        self.question_source = ""
        self.projects = []
        self.project_questions = []
        self.project_answers = []
        self.pq_idx = 0
        self.project_source = ""
        self.report = None

    # ---------------------------------------------------------- step 1: profile
    def set_profile(self, name, education, field, qualifications, years):
        years = int(years)
        self.profile = {
            "name": name.strip(),
            "education": education,
            "field": field.strip(),
            "qualifications": qualifications.strip(),
            "years": years,
            "level": level_from_years(years),
        }
        self.stage = "role"

    def _education_text(self):
        p = self.profile
        return f"{p['education']} in {p['field']}" if p.get("field") else p["education"]

    # ------------------------------------------------------------ step 2: role
    def start_interview(self, role):
        self.role = role
        self._build_role_questions()
        self.answers, self.q_idx = [], 0
        self.stage = "questions"

    def _build_role_questions(self):
        p = self.profile
        llm_qs = []
        if llm_engine.client:
            topics = ROLE_TOPICS.get(self.role, [])
            prompt = ROLE_QUESTION_SET_PROMPT.format(
                count=NUM_ROLE_QUESTIONS, role=self.role, level=p["level"], years=p["years"],
                name=p["name"], education=self._education_text(),
                qualifications=p["qualifications"] or "not provided",
                topics=", ".join(random.sample(topics, k=min(4, len(topics)))) or "core skills",
                avoid="\n".join(f"- {q}" for q in self.seen[-20:]) or "None",
                nonce=uuid.uuid4().hex[:8],
            )
            reply = llm_engine.generate(prompt)
            llm_qs = [q for q in _parse_list(reply) if isinstance(q, str) and len(q.strip()) > 10]

        questions = _unique(llm_qs)[:NUM_ROLE_QUESTIONS]
        if len(questions) < NUM_ROLE_QUESTIONS:
            have = {q.lower() for q in questions}
            for q in offline_role_questions(self.role, p["level"], NUM_ROLE_QUESTIONS,
                                            avoid=set(self.seen) | have):
                if len(questions) >= NUM_ROLE_QUESTIONS:
                    break
                if q.lower() not in have:
                    questions.append(q)
                    have.add(q.lower())

        self.question_source = ("gemini" if len(llm_qs) >= NUM_ROLE_QUESTIONS
                                else "mixed" if llm_qs else "offline")
        self.questions = questions
        self.seen.extend(questions)

    # ------------------------------------------------------- step 3: questions
    def submit_answer(self, text):
        text = (text or "").strip()
        self.answers.append({"question": self.questions[self.q_idx], "answer": text, "skipped": not text})
        self.q_idx += 1
        if self.q_idx >= len(self.questions):
            self.stage = "projects"

    # -------------------------------------------------------- step 4: projects
    def set_projects(self, projects):
        self.projects = [p for p in projects if p["name"].strip() and p["description"].strip()]

    def generate_project_questions(self):
        count = min(5, max(3, 2 + len(self.projects)))  # 1 project -> 3 questions ... 3 projects -> 5
        names = [p["name"] for p in self.projects]
        result = []

        if llm_engine.client:
            listing = "\n".join(
                f"{i + 1}. {p['name']} | Tech: {p.get('tech') or 'not given'} | Description: {p['description']}"
                for i, p in enumerate(self.projects))
            prompt = PROJECT_QUESTION_PROMPT.format(
                count=count, role=self.role, level=self.profile["level"],
                projects=listing, nonce=uuid.uuid4().hex[:8])
            for item in _parse_list(llm_engine.generate(prompt)):
                if not isinstance(item, dict):
                    continue
                question = str(item.get("question", "")).strip()
                if len(question) < 10:
                    continue
                project = str(item.get("project", "")).strip()
                match = next((n for n in names if n.lower() == project.lower()), None)
                result.append({"project": match or names[len(result) % len(names)], "question": question})

        llm_count = len(result)
        result = result[:count]
        if len(result) < count:
            have = {r["question"].lower() for r in result}
            for item in offline_project_questions(self.projects, count * 2):
                if len(result) >= count:
                    break
                if item["question"].lower() not in have:
                    result.append(item)
                    have.add(item["question"].lower())

        self.project_source = "gemini" if llm_count >= count else "mixed" if llm_count else "offline"
        self.project_questions = result
        self.project_answers, self.pq_idx = [], 0
        self.stage = "project_qa"

    def submit_project_answer(self, text):
        text = (text or "").strip()
        item = self.project_questions[self.pq_idx]
        self.project_answers.append({"project": item["project"], "question": item["question"],
                                     "answer": text, "skipped": not text})
        self.pq_idx += 1
        if self.pq_idx >= len(self.project_questions):
            self.stage = "report"
            self.report = None

    # ---------------------------------------------------------- step 5: report
    def _items(self):
        items = []
        for a in self.answers:
            items.append({"kind": "role", "project": "", **a})
        for a in self.project_answers:
            items.append({"kind": "project", **a})
        for n, item in enumerate(items, start=1):
            item["n"] = n
        return items

    def finalize(self):
        items = self._items()
        self.report = self._evaluate_with_llm(items) or self._evaluate_offline(items)
        return self.report

    def _transcript(self, items):
        blocks = []
        for it in items:
            tag = f"project question about {it['project']}" if it["kind"] == "project" else "role question"
            blocks.append(f"[{it['n']}] ({tag})\nQ: {it['question']}\nA: {it['answer'] or '(skipped)'}")
        return "\n\n".join(blocks)

    def _evaluate_with_llm(self, items):
        if not llm_engine.client:
            return None
        p = self.profile
        prompt = INTERVIEW_REPORT_PROMPT.format(
            name=p["name"], education=self._education_text(), qualifications=p["qualifications"] or "not provided",
            years=p["years"], level=p["level"], role=self.role, transcript=self._transcript(items))
        reply = llm_engine.generate(prompt, attempts=2)
        if not reply:
            return None
        try:
            data = _extract_json(reply)
        except Exception:
            logger.warning("Could not parse the Gemini interview report; using offline scoring.")
            return None
        if not isinstance(data, dict):
            return None

        by_n = {}
        for entry in data.get("per_question") or []:
            try:
                by_n[int(entry.get("n"))] = entry
            except (TypeError, ValueError, AttributeError):
                continue
        if not by_n:
            return None

        scored = []
        for it in items:
            if it["skipped"]:
                scored.append({"score": 0, "feedback": "Skipped, so this answer could not be scored."})
            elif it["n"] in by_n:
                e = by_n[it["n"]]
                scored.append({"score": _clamp(e.get("score")), "feedback": str(e.get("feedback", "")).strip()})
            else:
                est = _estimate(it["answer"])
                scored.append({"score": est["score"], "feedback": est["improvement_tip"]})

        overall = _avg([s["score"] for s in scored])
        raw = data.get("dimension_scores") if isinstance(data.get("dimension_scores"), dict) else {}
        dims = {k: _clamp(raw.get(k), overall) for k in DIM_LABELS}
        if all(it["skipped"] for it in items):
            dims = {k: 0 for k in DIM_LABELS}

        def as_list(key):
            value = data.get(key)
            return [str(x).strip() for x in value if str(x).strip()] if isinstance(value, list) else []

        return self._assemble(items, scored, dims, "gemini",
                              summary=str(data.get("summary", "")).strip(),
                              strengths=as_list("strengths"), improvements=as_list("improvements"),
                              llm_suggestions=as_list("suggestions"))

    def _evaluate_offline(self, items):
        scored, per_dims = [], []
        for it in items:
            if it["skipped"]:
                scored.append({"score": 0, "feedback": "Skipped, so this answer could not be scored."})
                per_dims.append(None)
                continue
            est = _estimate(it["answer"])
            worked = f"What worked: {', '.join(est['strengths'])}. " if est["strengths"] else ""
            scored.append({"score": est["score"], "feedback": f"{worked}Next: {est['improvement_tip']}"})
            per_dims.append(est["dimension_scores"])

        def collect(key, kinds=("role", "project")):
            return [(d[key] if d else 0) for it, d in zip(items, per_dims) if it["kind"] in kinds]

        def star(kinds):
            return [(mean([d["situation"], d["action"], d["result"]]) if d else 0)
                    for it, d in zip(items, per_dims) if it["kind"] in kinds]

        project_own = [(mean([d["action"], d["result"]]) if d else 0)
                       for it, d in zip(items, per_dims) if it["kind"] == "project"]
        dims = {
            "technical_knowledge": _avg(collect("technical_depth", ("role",))),
            "problem_solving": _avg(collect("action")),
            "communication": _avg(collect("clarity")),
            "star_structure": _avg(star(("role", "project"))),
            "depth": _avg(collect("technical_depth")),
            "impact": _avg(collect("result")),
            "project_ownership": _avg(project_own),
        }
        return self._assemble(items, scored, dims, "offline")

    def _assemble(self, items, scored, dims, source, summary="", strengths=None, improvements=None,
                  llm_suggestions=None):
        per_question = []
        for it, s in zip(items, scored):
            per_question.append({
                "n": it["n"], "kind": it["kind"], "project": it["project"], "question": it["question"],
                "answer": it["answer"], "skipped": it["skipped"], "score": s["score"], "feedback": s["feedback"],
            })

        overall = _avg([q["score"] for q in per_question])
        role_scores = [q["score"] for q in per_question if q["kind"] == "role"]
        project_scores = [q["score"] for q in per_question if q["kind"] == "project"]
        ranked = sorted(dims.items(), key=lambda kv: kv[1])
        answered = sum(1 for q in per_question if not q["skipped"])

        if not summary:
            summary = (f"You scored {overall}/100 and answered {answered} of {len(per_question)} questions. "
                       f"Your strongest area was {DIM_LABELS[ranked[-1][0]].lower()} and the biggest opportunity "
                       f"is {DIM_LABELS[ranked[0][0]].lower()}.")
        if not strengths:
            strengths = [f"{DIM_LABELS[k]} ({v}/100)" for k, v in reversed(ranked[-2:]) if v > 0] \
                or ["You completed the interview, which is the first step to improving."]
        if not improvements:
            improvements = [f"{DIM_LABELS[k]} ({v}/100)" for k, v in ranked[:2]]

        skipped = len(per_question) - answered
        return {
            "candidate": {**self.profile, "role": self.role},
            "overall": overall,
            "readiness": readiness_label(overall),
            "section_scores": {"role": _avg(role_scores), "project": _avg(project_scores)},
            "dimension_scores": dims,
            "per_question": per_question,
            "summary": summary,
            "strengths": strengths[:4],
            "improvements": improvements[:4],
            "suggestions": self._suggestions(dims, skipped, llm_suggestions or []),
            "answered": answered,
            "total": len(per_question),
            "source": source,
        }

    def _suggestions(self, dims, skipped, llm_suggestions):
        """Always returns actionable advice, whatever the score."""
        ordered = [k for k, _ in sorted(dims.items(), key=lambda kv: kv[1])]
        rule_based = []
        for key in ordered[:3]:
            low, high = SUGGESTION_BANK[key]
            rule_based.append((low if dims[key] < 75 else high).format(role=self.role))

        topics = ROLE_TOPICS.get(self.role, [])
        if topics:
            picks = ", ".join(random.sample(topics, k=min(3, len(topics))))
            rule_based.append(f"Plan your next study block around these {self.role} topics: {picks}.")
        if skipped:
            rule_based.append(f"You skipped {skipped} question(s). Next time, give a partial answer: "
                              "saying how you would approach it still earns credit.")
        rule_based.append("Repeat this guided interview within a week. A fresh set of questions gives you a clear benchmark against today's score.")

        merged = _unique(llm_suggestions[:5] + rule_based)
        return merged[:7]
