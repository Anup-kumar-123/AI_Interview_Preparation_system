import re

from src.core.llm_engine import llm_engine
from src.core.prompt_templates import QUESTION_GENERATION_PROMPT

PRESET_QUESTIONS = [
    "Tell me about a challenging project you built and how you handled technical trade-offs.",
    "How do you isolate and fix performance bottlenecks in production code?",
    "Describe a situation where project requirements changed suddenly. How did you adapt?",
]

# Used only when Gemini is unavailable and the presets are exhausted.
OFFLINE_POOL = [
    "Tell me about a time you disagreed with a teammate on a technical decision. What happened?",
    "Describe a production incident you helped resolve. What was your role?",
    "Walk me through a time you had to learn a new technology quickly to deliver a project.",
    "Tell me about a decision where you had to balance speed against quality.",
    "Describe a time you improved a system's reliability or performance. How did you measure it?",
    "Tell me about a time you mentored someone or raised the standard of your team's work.",
    "Describe a project that failed or fell short. What did you learn?",
    "Tell me about a time you had to explain a complex technical idea to a non-technical stakeholder.",
]


def _clean_question(text: str) -> str:
    """Keeps the first non-empty line and strips numbering, quotes and markdown."""
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            line = re.sub(r"^(\d+[.)]\s*|[-*]\s*)", "", line)
            return line.strip(" \"'*_`")
    return ""


class InterviewSession:
    """Manages state, role configuration, and question generation."""

    VERSION = 2  # bump when attributes change so stale Streamlit sessions are rebuilt

    def __init__(self):
        self.role = "Machine Learning Engineer"
        self.seniority = "Senior"
        self.questions = list(PRESET_QUESTIONS)
        self.current_idx = 0
        self.history = []
        self.latest_eval = None
        self.last_question_source = "preset"  # preset | gemini | offline

    @property
    def question_number(self) -> int:
        return self.current_idx + 1

    def get_current_question(self) -> str:
        return self.questions[self.current_idx]

    def _new_question(self) -> str:
        previous = "\n".join(f"- {q}" for q in self.questions[-8:])
        prompt = QUESTION_GENERATION_PROMPT.format(
            role=self.role,
            seniority=self.seniority,
            context="General technical competency and problem-solving",
            previous=previous,
        )
        text = llm_engine.generate(prompt)
        if text:
            question = _clean_question(text)
            if len(question) > 10 and question not in self.questions:
                self.last_question_source = "gemini"
                return question

        for candidate in OFFLINE_POOL:
            if candidate not in self.questions:
                self.last_question_source = "offline"
                return candidate
        return ""

    def generate_next_question(self):
        """Moves to the next unseen question, generating a fresh one when none is queued."""
        if self.current_idx + 1 < len(self.questions):
            self.current_idx += 1
            self.last_question_source = "preset"
        else:
            question = self._new_question()
            if question:
                self.questions.append(question)
                self.current_idx = len(self.questions) - 1
            else:  # everything used up: start cycling
                self.current_idx = (self.current_idx + 1) % len(self.questions)
        self.latest_eval = None  # a new question should not show the previous score

    def save_response(self, question: str, answer: str, eval_data: dict):
        self.latest_eval = eval_data
        self.history.append({
            "question": question,
            "answer": answer,
            "eval": eval_data,
        })

    def update_persona(self, role: str, seniority: str):
        self.role = role
        self.seniority = seniority
        # Drop queued preset questions so upcoming ones match the new profile.
        self.questions = self.questions[: self.current_idx + 1]
