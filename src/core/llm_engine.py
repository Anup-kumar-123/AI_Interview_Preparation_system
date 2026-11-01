import os
import time
from typing import Optional

from dotenv import load_dotenv

from src.utils.logger import logger

load_dotenv()

try:
    from google import genai
except ImportError:  # keep the app alive; it will run in demo mode
    genai = None
    logger.error("Package 'google-genai' is not installed. Run: python -m pip install google-genai")


def _read_api_key() -> Optional[str]:
    """Reads GEMINI_API_KEY from the environment (.env)"""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            key = None
    key = (key or "").strip().strip("\"'").strip()
    return key or None


def _friendly_error(exc: Exception) -> str:
    msg = str(exc)
    low = msg.lower()
    if any(t in low for t in ("api key", "api_key", "permission_denied", "unauthenticated", "401", "403")):
        return "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file."
    if any(t in low for t in ("429", "resource_exhausted", "quota")):
        return "Gemini quota or rate limit reached. Try again in a minute."
    if any(t in low for t in ("404", "not found")):
        return "Gemini model not found. Check LLM_MODEL in your .env file."
    return f"Gemini request failed: {msg[:140]}"


class LLMEngine:
    def __init__(self):
        self.api_key = _read_api_key()
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
        self.client = None
        self.last_error: Optional[str] = None

        if not self.api_key:
            self.last_error = "No GEMINI_API_KEY found. Add it to your .env file."
            logger.warning(self.last_error)
        elif genai is None:
            self.last_error = "The google-genai package is not installed."
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                self.last_error = _friendly_error(e)
                logger.error(f"Could not create Gemini client: {e}")

    @property
    def is_live(self) -> bool:
        """True when a Gemini client exists and the last call did not fail."""
        return self.client is not None and self.last_error is None

    def generate(self, prompt: str, attempts: int = 2) -> Optional[str]:
        """Returns model text, or None when Gemini is unavailable or the call failed."""
        if not self.client:
            return None

        for attempt in range(1, attempts + 1):
            try:
                response = self.client.models.generate_content(model=self.model_name, contents=prompt)
                text = (response.text or "").strip()
                if text:
                    self.last_error = None
                    return text
                logger.warning("Gemini returned an empty response.")
                return None
            except Exception as e:
                self.last_error = _friendly_error(e)
                logger.error(f"Gemini call failed (attempt {attempt}/{attempts}): {e}")
                transient = any(t in str(e).lower() for t in ("503", "unavailable", "overloaded", "timeout", "429"))
                if attempt < attempts and transient:
                    time.sleep(1.5 * attempt)
                    continue
                return None
        return None

    def generate_response(self, prompt: str) -> str:
        """Backwards-compatible helper: returns text, or an empty string on failure."""
        return self.generate(prompt) or ""


llm_engine = LLMEngine()
