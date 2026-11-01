"""Mic button that fills an answer box with the transcript of a spoken answer."""
import hashlib

import streamlit as st

from src.core.audio_engine import transcribe_audio


def voice_input(answer_key: str, suffix: str = ""):
    """
    Shows a recorder above a text area. Call it BEFORE the text_area with the same key.
    The transcript is added to the answer box, where the user can edit it before submitting.
    `suffix` makes the recorder reset when the question changes.
    """
    if not hasattr(st, "audio_input"):  # older Streamlit: typing still works
        return

    audio = st.audio_input("Or record your answer", key=f"mic_{answer_key}_{suffix}")
    if audio is None:
        return

    data = audio.getvalue()
    fingerprint = hashlib.md5(data).hexdigest()
    done_key = f"mic_done_{answer_key}_{suffix}"
    if st.session_state.get(done_key) == fingerprint:  # already transcribed on an earlier rerun
        return

    with st.spinner("Transcribing your answer..."):
        text, error = transcribe_audio(data, getattr(audio, "type", None) or "audio/wav")
    st.session_state[done_key] = fingerprint

    if error:
        st.warning(error)
        return

    existing = st.session_state.get(answer_key, "").strip()
    st.session_state[answer_key] = f"{existing} {text}".strip()
    st.caption("Transcript added below. Edit it if needed, then submit.")