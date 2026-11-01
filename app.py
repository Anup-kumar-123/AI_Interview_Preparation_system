import streamlit as st
from dotenv import load_dotenv

# Load Environment Variables from .env
load_dotenv()

from src.core.llm_engine import llm_engine
from src.utils.ui_styles import (
    apply_custom_css, stretch, sidebar_brand, sidebar_status, hero, interviewer_card, notice,
    score_ring, star_breakdown, tip_card, skill_panel, empty_state, profile_card,
)
from src.services.interview_manager import InterviewSession
from src.services.evaluator import evaluate_star_answer
from src.services.resume_parser import parse_resume
from src.services.analytics_service import render_analytics_dashboard
from src.services.guided_view import get_guided, render_guided_interview, render_guided_report
from src.services.voice_input import voice_input

# Streamlit Page Setup
st.set_page_config(
    page_title="PrepPulse AI - Interview Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply UI Styling
apply_custom_css()

# Session State Initialization (rebuild if an older session object is still in memory after a code change)
if "interview" not in st.session_state or getattr(st.session_state.interview, "VERSION", 0) != InterviewSession.VERSION:
    st.session_state.interview = InterviewSession()
interview = st.session_state.interview

# Keep the typed answer when the user switches pages and comes back
st.session_state["answer_box"] = st.session_state.get("answer_box", "")


def request_next_question():
    """Button callback: clear the answer box and ask the main script to fetch the next question."""
    st.session_state.want_next = True
    st.session_state.answer_box = ""


BTN = stretch(st.button)

# Sidebar Navigation
with st.sidebar:
    st.markdown(sidebar_brand(), unsafe_allow_html=True)
    st.divider()

    menu = st.radio(
        "Workspace Navigation",
        ["🚀 Guided Interview", "🎯 Mock Interview", "📄 Resume & JD Matcher", "📈 Performance Analytics", "⚙️ Persona Settings"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown(sidebar_status(llm_engine.model_name, llm_engine.is_live), unsafe_allow_html=True)

profile_tag = [f"{interview.seniority} {interview.role}"]

# VIEW 0: GUIDED INTERVIEW (profile -> role -> 10 questions -> projects -> report)
if menu == "🚀 Guided Interview":
    render_guided_interview()

# VIEW 1: MOCK INTERVIEW
elif menu == "🎯 Mock Interview":
    st.markdown(
        hero("Step into the interview room",
             "Write your answer in STAR format and get scored the moment you submit.",
             tags=profile_tag),
        unsafe_allow_html=True,
    )

    if llm_engine.client is None:
        st.markdown(notice(f"{llm_engine.last_error} Questions come from a preset list and scores are rough estimates.",
                           "Demo mode"), unsafe_allow_html=True)

    if st.session_state.pop("want_next", False):
        with st.spinner("The interviewer is preparing your next question..."):
            interview.generate_next_question()

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        current_q = interview.get_current_question()
        st.markdown(interviewer_card(current_q, interview.question_number, interview.role), unsafe_allow_html=True)

        voice_input("answer_box", suffix=f"{interview.current_idx}_{len(interview.history)}")

        user_answer = st.text_area(
            "Your answer (STAR format)",
            key="answer_box",
            height=200,
            placeholder="Situation: where were you?  Task: what was needed?  Action: what did you do?  Result: what changed?"
        )

        b1, b2 = st.columns(2)
        with b1:
            submitted = st.button("Submit & evaluate", type="primary", **BTN)
        with b2:
            st.button("Next question", on_click=request_next_question, **BTN)

        if submitted:
            answer = user_answer.strip()
            already = (interview.history and interview.history[-1]["question"] == current_q
                       and interview.history[-1]["answer"] == answer)
            if not answer:
                st.warning("Write an answer first, then submit.")
            elif already:
                st.info("This answer is already scored. Edit it or move to the next question.")
            else:
                with st.spinner("Scoring your answer against STAR..."):
                    eval_res = evaluate_star_answer(current_q, answer)
                    interview.save_response(current_q, answer, eval_res)
                st.success("Score saved to your analytics.")

    with col2:
        latest = interview.latest_eval
        if latest:
            if latest.get("source") == "offline":
                reason = llm_engine.last_error or "Gemini is unavailable."
                st.markdown(notice(f"{reason} This score is a rough estimate from answer structure.",
                                   "Estimated score"), unsafe_allow_html=True)
            st.markdown(score_ring(latest.get("score", 0), "Your STAR score"), unsafe_allow_html=True)
            st.markdown(star_breakdown(latest.get("star_breakdown", {})), unsafe_allow_html=True)
            st.markdown(tip_card(latest.get("improvement_tip", "Keep practicing!")), unsafe_allow_html=True)
        else:
            st.markdown(
                empty_state("🎤", "Waiting for your answer",
                            "Submit a response and your STAR score appears here."),
                unsafe_allow_html=True,
            )

# VIEW 2: RESUME & JD MATCHING
elif menu == "📄 Resume & JD Matcher":
    st.markdown(
        hero("Resume vs. job description",
             "See which required skills your resume already proves and which ones to build next."),
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2, gap="large")
    with col1:
        uploaded_resume = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])
    with col2:
        target_jd = st.text_area("Target job description", height=150, placeholder="Paste the job requirements here...")

    if st.button("Run gap analysis", type="primary"):
        if uploaded_resume and target_jd.strip():
            with st.spinner("Comparing your resume with the role..."):
                st.session_state.resume_result = parse_resume(uploaded_resume, target_jd)
        else:
            st.session_state.resume_result = None
            st.error("Upload a resume and paste a job description to run the analysis.")

    analysis = st.session_state.get("resume_result")
    if analysis:
        if analysis["error"]:
            st.error(analysis["error"])
        elif analysis["match_score"] is None:
            st.info(analysis["note"])
        else:
            r1, r2 = st.columns([1, 3], gap="large")
            with r1:
                st.markdown(score_ring(analysis["match_score"], "Role match", small=True), unsafe_allow_html=True)
            with r2:
                m1, m2 = st.columns(2, gap="medium")
                with m1:
                    st.markdown(skill_panel("Skills you already show", analysis["matched_skills"], "match"),
                                unsafe_allow_html=True)
                with m2:
                    st.markdown(skill_panel("Skills to build", analysis["missing_skills"], "gap"),
                                unsafe_allow_html=True)

# VIEW 3: ANALYTICS DASHBOARD
elif menu == "📈 Performance Analytics":
    st.markdown(
        hero("Your performance over time",
             "Every scored answer lands here, so you can see which STAR areas are improving."),
        unsafe_allow_html=True,
    )
    guided_report = get_guided().report
    if guided_report:
        st.subheader("Guided interview report")
        render_guided_report(guided_report)
        if interview.history:
            st.divider()
            st.subheader("Mock interview practice")
            render_analytics_dashboard(interview.history)
    else:
        render_analytics_dashboard(interview.history)

# VIEW 4: PERSONA SETTINGS
elif menu == "⚙️ Persona Settings":
    st.markdown(
        hero("Set up your interview profile",
             "Choose the role and level you are preparing for."),
        unsafe_allow_html=True,
    )

    roles = ["Machine Learning Engineer", "Software Development Engineer (SDE)", "Data Scientist",
             "System Architect", "Product Manager"]
    levels = ["Junior", "Mid-Level", "Senior", "Lead / Staff"]

    target_role = st.selectbox("Target role", roles,
                               index=roles.index(interview.role) if interview.role in roles else 0)
    seniority_level = st.select_slider("Experience level", options=levels,
                                       value=interview.seniority if interview.seniority in levels else levels[0])

    st.markdown(profile_card(target_role, seniority_level), unsafe_allow_html=True)

    if st.button("Save profile", type="primary"):
        interview.update_persona(target_role, seniority_level)
        st.success(f"Profile saved: **{seniority_level} {target_role}**. Your next questions will match it.")