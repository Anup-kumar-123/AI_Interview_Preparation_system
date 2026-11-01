STAR_EVALUATION_PROMPT = """You are an expert technical interviewer and executive talent coach.
Evaluate the candidate's interview response using the STAR (Situation, Task, Action, Result) method.
Be honest: a vague, very short, or off-topic answer must receive a low score.

Question: {question}
Candidate Answer: {answer}

Respond ONLY with a valid JSON object matching this exact schema:
{{
  "score": <integer score between 0 and 100>,
  "star_breakdown": {{
    "situation_task": "<1-2 sentence analysis of how well context was set>",
    "action": "<1-2 sentence analysis of technical actions taken>",
    "result": "<1-2 sentence analysis of impact or outcomes>"
  }},
  "dimension_scores": {{
    "situation": <integer 0-100>,
    "action": <integer 0-100>,
    "result": <integer 0-100>,
    "clarity": <integer 0-100>,
    "technical_depth": <integer 0-100>
  }},
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvement_tip": "<1 specific, actionable advice string>"
}}
Do not include markdown code block formatting like ```json. Return raw JSON text only.
"""

QUESTION_GENERATION_PROMPT = """You are a senior technical interviewer conducting a mock interview.
Role: {role}
Seniority Level: {seniority}
Context / Skills to target: {context}

Questions already asked (do NOT repeat or paraphrase them):
{previous}

Generate ONE concise, realistic behavioral or technical-experience question appropriate for this role and seniority level.
It should invite a STAR-style answer (a real past situation).
Return ONLY the question text, with no numbering, quotes or preamble.
"""


# ---------------------------------------------------------------------------
# Guided Interview prompts
# ---------------------------------------------------------------------------
ROLE_QUESTION_SET_PROMPT = """You are a senior interviewer hiring for IT roles.
Candidate: {name}. Education: {education}. Qualifications: {qualifications}.
Experience: {years} years of IT experience ({level} level).
Target role: {role}.

Write exactly {count} DIFFERENT interview questions for this candidate.
- About 70% must be technical questions specific to the {role} role, the rest behavioral or problem-solving.
- Match the difficulty to the level: Entry = fundamentals and basic hands-on; Mid = design, trade-offs and debugging; High = architecture, scale, leadership and decision making.
- For variety in this session, lean on these topics: {topics}. Session id: {nonce}.
- Do NOT repeat or paraphrase these earlier questions:
{avoid}

Return ONLY a JSON array of {count} strings, with no numbering and no markdown fences.
"""

PROJECT_QUESTION_PROMPT = """You are a senior interviewer reviewing a candidate's projects.
Target role: {role}. Experience level: {level}.

Candidate's projects:
{projects}

Write exactly {count} probing questions that make the candidate explain what THEY personally did.
Cover a mix of: their own contribution, a technical decision and its trade-offs, the hardest problem, testing or validation, and measurable impact.
Spread the questions across the projects. Session id: {nonce}.

Return ONLY a JSON array of {count} objects like {{"project": "<exact project name>", "question": "<question text>"}}, with no markdown fences.
"""

INTERVIEW_REPORT_PROMPT = """You are a senior hiring manager and interview coach for IT roles.
Candidate: {name}. Education: {education}. Qualifications: {qualifications}.
Experience: {years} years ({level} level). Target role: {role}.

Score each answer from 0 to 100 against the expectations for a {level}-level {role}. Answers marked (skipped) get 0.
Role questions are judged on correctness and depth; behavioral and project questions on STAR structure (Situation, Task, Action, Result), personal ownership and measurable impact.
Be fair and specific. Do not inflate scores.

Interview transcript:
{transcript}

Respond ONLY with valid JSON in exactly this schema:
{{
  "per_question": [
    {{"n": <question number>, "score": <integer 0-100>, "feedback": "<1-2 sentences: what was good and what was missing>"}}
  ],
  "dimension_scores": {{
    "technical_knowledge": <integer 0-100>,
    "problem_solving": <integer 0-100>,
    "communication": <integer 0-100>,
    "star_structure": <integer 0-100>,
    "depth": <integer 0-100>,
    "impact": <integer 0-100>,
    "project_ownership": <integer 0-100>
  }},
  "summary": "<2-3 sentence overall assessment>",
  "strengths": ["<up to 3 items>"],
  "improvements": ["<up to 3 items>"],
  "suggestions": ["<5 specific, actionable suggestions to perform better in future interviews, useful whatever the score>"]
}}
Return raw JSON only, with no markdown code fences.
"""
