"""Streamlit screens for the Guided Interview and its report dashboard."""
import html

import plotly.graph_objects as go
import streamlit as st

from src.core.llm_engine import llm_engine
from src.core.question_bank import IT_ROLES, ROLE_TOPICS
from src.services.guided_interview import DIM_LABELS, NUM_ROLE_QUESTIONS, GuidedInterview
from src.services.voice_input import voice_input
from src.utils.ui_styles import (
    bullet_panel, dimension_bars, hero, interviewer_card, notice, readiness_badge,
    score_ring, skill_panel, stepper, stretch, suggestion_cards,
)

STEP_LABELS = ["Profile", "Role", "Questions", "Projects", "Report"]
STAGE_TO_STEP = {"profile": 0, "role": 1, "questions": 2, "projects": 3, "project_qa": 3, "report": 4}
EDUCATION = ["Diploma", "Bachelor's degree", "Master's degree", "PhD", "Bootcamp / self-taught", "Other"]
VIOLET, MINT = "#7C5CFF", "#4ADE9C"


def get_guided() -> GuidedInterview:
    """Returns the guided interview kept in session state (rebuilt if the class changed)."""
    current = st.session_state.get("guided")
    if current is None or getattr(current, "VERSION", 0) != GuidedInterview.VERSION:
        st.session_state.guided = GuidedInterview()
    return st.session_state.guided


# ------------------------------------------------------------------ callbacks
def _cb_stage(stage):
    st.session_state.guided.stage = stage


def _cb_reset():
    st.session_state.guided.reset()


def _cb_answer(kind, key, skip):
    g = st.session_state.guided
    text = "" if skip else st.session_state.get(key, "")
    if kind == "role":
        g.submit_answer(text)
    else:
        g.submit_project_answer(text)


# ------------------------------------------------------------------- screens
def render_guided_interview():
    g = get_guided()
    st.markdown(stepper(STAGE_TO_STEP[g.stage], STEP_LABELS), unsafe_allow_html=True)
    if g.stage == "profile":
        _profile_step(g)
    elif g.stage == "role":
        _role_step(g)
    elif g.stage == "questions":
        _qa_step(g, "role")
    elif g.stage == "projects":
        _projects_step(g)
    elif g.stage == "project_qa":
        _qa_step(g, "project")
    else:
        _report_step(g)


def _profile_step(g):
    st.markdown(hero("Let's start with you",
                     "Your experience decides how demanding the questions will be."), unsafe_allow_html=True)
    p = g.profile
    with st.form("g_profile_form"):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            name = st.text_input("Full name", value=p.get("name", ""))
            education = st.selectbox(
                "Highest education", EDUCATION,
                index=EDUCATION.index(p["education"]) if p.get("education") in EDUCATION else 1)
            field = st.text_input("Degree or field of study", value=p.get("field", ""),
                                  placeholder="e.g. B.Tech in Computer Science")
        with c2:
            years = st.slider("Years of IT experience", 0, 10, int(p.get("years", 1)))
            qualifications = st.text_area("Qualifications and certifications", value=p.get("qualifications", ""),
                                          height=118, placeholder="e.g. AWS Cloud Practitioner, Google Data Analytics")
        submitted = st.form_submit_button("Continue", type="primary", **stretch(st.form_submit_button))
    st.caption("0 to 2 years is Entry level, 3 to 6 is Mid level, and 7 to 10 is High level.")

    if submitted:
        if not name.strip():
            st.error("Enter your name to continue.")
        else:
            g.set_profile(name, education, field, qualifications, years)
            st.rerun()


def _role_step(g):
    p = g.profile
    st.markdown(hero(
        "Which role are you preparing for?",
        f"{p['name']}, choose a role and I will prepare {NUM_ROLE_QUESTIONS} questions for a {p['level'].lower()}-level candidate.",
        tags=[f"{p['level']} level", f"{p['years']} years in IT"]), unsafe_allow_html=True)

    role = st.selectbox("Target role", IT_ROLES, index=IT_ROLES.index(g.role) if g.role in IT_ROLES else 0)
    st.markdown(skill_panel("What this interview can cover", ROLE_TOPICS.get(role, []), "match"),
                unsafe_allow_html=True)
    st.write("")

    btn = stretch(st.button)
    b1, b2 = st.columns(2)
    with b1:
        st.button("Back", on_click=_cb_stage, args=("profile",), **btn)
    with b2:
        if st.button("Start interview", type="primary", **btn):
            with st.spinner("Preparing your questions..."):
                g.start_interview(role)
            st.rerun()


def _qa_step(g, kind):
    if kind == "role":
        total, idx = len(g.questions), g.q_idx
        question, context, source = g.questions[idx], g.role, g.question_source
        title, desc = "Role interview", "Answer in your own words. Use real examples where you can."
    else:
        total, idx = len(g.project_questions), g.pq_idx
        item = g.project_questions[idx]
        question, context, source = item["question"], item["project"], g.project_source
        title, desc = "Project deep-dive", "Explain what you personally did. Say 'I' for your own work."

    st.markdown(hero(title, desc), unsafe_allow_html=True)
    if idx == 0 and source != "gemini":
        reason = "" if llm_engine.client else f"{llm_engine.last_error} "
        st.markdown(notice(f"{reason}Some or all questions come from the built-in question bank.", "Offline questions"),
                    unsafe_allow_html=True)

    st.progress(idx / total, text=f"Question {idx + 1} of {total}")
    st.markdown(interviewer_card(question, idx + 1, context), unsafe_allow_html=True)

    key = f"g_{kind}_ans_{idx}"
    st.session_state[key] = st.session_state.get(key, "")  # keep a half-written answer if the user switches pages
    voice_input(key)
    st.text_area("Your answer", key=key, height=200,
                 placeholder="Situation, task, what you did, and the result. Numbers make it stronger.")

    btn = stretch(st.button)
    last = idx + 1 == total
    b1, b2 = st.columns(2)
    with b1:
        st.button("Save and finish" if last else "Save and next", type="primary",
                  on_click=_cb_answer, args=(kind, key, False), **btn)
    with b2:
        st.button("Skip this question", on_click=_cb_answer, args=(kind, key, True), **btn)
    st.button("Start over", on_click=_cb_reset)


def _projects_step(g):
    st.markdown(hero("Now, your projects",
                     "Describe up to three projects. I will ask 3 to 5 questions about what you personally did."),
                unsafe_allow_html=True)

    st.session_state["g_proj_count"] = st.session_state.get("g_proj_count", 1)
    count = st.radio("How many projects do you want to discuss?", [1, 2, 3], horizontal=True, key="g_proj_count")

    drafts = []
    for i in range(count):
        for suffix in ("name", "tech", "desc"):
            k = f"g_p{suffix}_{i}"
            st.session_state[k] = st.session_state.get(k, "")
        with st.container(border=True):
            st.markdown(f"**Project {i + 1}**")
            c1, c2 = st.columns(2)
            name = c1.text_input("Project name", key=f"g_pname_{i}")
            tech = c2.text_input("Tech stack", key=f"g_ptech_{i}", placeholder="e.g. Python, FastAPI, PostgreSQL")
            desc = st.text_area("What was it, what was your role, and what was the outcome?",
                                key=f"g_pdesc_{i}", height=110)
        drafts.append({"name": name.strip(), "tech": tech.strip(), "description": desc.strip()})

    if st.button("Continue to project questions", type="primary"):
        missing = [i + 1 for i, d in enumerate(drafts) if not d["name"] or len(d["description"]) < 20]
        if missing:
            st.error("Add a name and a short description (at least 20 characters) for project "
                     + ", ".join(map(str, missing)) + ".")
        else:
            with st.spinner("Preparing your project questions..."):
                g.set_projects(drafts)
                g.generate_project_questions()
            st.rerun()
    st.button("Start over", on_click=_cb_reset)


def _report_step(g):
    if g.report is None:
        with st.spinner("Scoring your full interview..."):
            g.finalize()
    r = g.report
    c = r["candidate"]
    st.markdown(hero("Your interview report",
                     f"{c['name']}, here is how you did as a {c['level'].lower()}-level {c['role']}.",
                     tags=[f"{c['level']} level", f"{c['years']} years in IT", c["role"]]), unsafe_allow_html=True)
    render_guided_report(r)
    st.write("")
    st.button("Start a new interview", type="primary", on_click=_cb_reset)


# ------------------------------------------------------------- report dashboard
def render_guided_report(report):
    """Score, dimensions, strengths and suggestions. Shared by the guided flow and the analytics page."""
    if report["source"] == "offline":
        reason = llm_engine.last_error or "Gemini was unavailable."
        st.markdown(notice(f"{reason} Scores are rough estimates based on answer structure.", "Estimated scores"),
                    unsafe_allow_html=True)

    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown(score_ring(report["overall"], "Overall score"), unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'>{readiness_badge(report['readiness'], report['overall'])}</div>",
                    unsafe_allow_html=True)
    with right:
        st.markdown(f"<div class='panel'><h4>Summary</h4><p style='margin:0;line-height:1.6'>"
                    f"{html.escape(report['summary'])}</p></div>", unsafe_allow_html=True)
        st.write("")
        m1, m2, m3 = st.columns(3)
        m1.metric("Role questions", report["section_scores"]["role"])
        m2.metric("Project questions", report["section_scores"]["project"])
        m3.metric("Answered", f"{report['answered']}/{report['total']}")

    st.subheader("Skill dimensions")
    d1, d2 = st.columns(2, gap="large")
    dims = report["dimension_scores"]
    with d1:
        theta = [DIM_LABELS[k] for k in DIM_LABELS]
        values = [dims.get(k, 0) for k in DIM_LABELS]
        fig = go.Figure(go.Scatterpolar(
            r=values + values[:1], theta=theta + theta[:1], fill="toself",
            line=dict(color=MINT, width=2), fillcolor="rgba(74,222,156,.18)"))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=380,
            margin=dict(l=40, r=40, t=20, b=20), font=dict(family="Figtree, sans-serif", color="#ECEBFF"),
            polar=dict(bgcolor="rgba(0,0,0,0)",
                       radialaxis=dict(range=[0, 100], gridcolor="rgba(154,156,196,.2)"),
                       angularaxis=dict(gridcolor="rgba(154,156,196,.2)")))
        st.plotly_chart(fig, **stretch(st.plotly_chart))
    with d2:
        st.markdown(dimension_bars([(DIM_LABELS[k], dims.get(k, 0)) for k in DIM_LABELS]), unsafe_allow_html=True)

    p1, p2 = st.columns(2, gap="large")
    with p1:
        st.markdown(bullet_panel("What went well", report["strengths"]), unsafe_allow_html=True)
    with p2:
        st.markdown(bullet_panel("Where to improve", report["improvements"]), unsafe_allow_html=True)

    st.subheader("How to do better next time")
    st.markdown(suggestion_cards(report["suggestions"]), unsafe_allow_html=True)

    st.subheader("Answer review")
    for q in report["per_question"]:
        tag = f"Project: {q['project']}" if q["kind"] == "project" else "Role"
        title = q["question"] if len(q["question"]) <= 70 else q["question"][:67] + "..."
        with st.expander(f"{q['n']}. {q['score']}/100 - {title}"):
            st.caption(tag)
            st.markdown("**Question**")
            st.write(q["question"])
            st.markdown("**Your answer**")
            st.write(q["answer"] or "(skipped)")
            st.markdown(f"**Feedback:** {q['feedback']}")