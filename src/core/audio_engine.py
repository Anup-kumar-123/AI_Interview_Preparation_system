"""Speech-to-text for spoken interview answers, using the Gemini connection the app already has."""
from src.core.llm_engine import _friendly_error, llm_engine
from src.utils.logger import logger

try:
    from google.genai import types
except ImportError:
    types = None

TRANSCRIBE_PROMPT = (
    "Transcribe this spoken interview answer exactly as it was said, with natural punctuation. "
    "Return ONLY the transcript text. If there is no speech, return nothing."
)
MAX_AUDIO_BYTES = 15 * 1024 * 1024


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav"):
    """Returns (text, error). On success error is None; on failure text is an empty string."""
    if not audio_bytes:
        return "", "No audio was recorded."
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        return "", "That recording is too long. Keep each answer under a few minutes."
    if not llm_engine.client or types is None:
        return "", "Voice answers need a working Gemini key. You can still type your answer."

    try:
        response = llm_engine.client.models.generate_content(
            model=llm_engine.model_name,
            contents=[TRANSCRIBE_PROMPT, types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)],
        )
        text = (response.text or "").strip()
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        return "", _friendly_error(e)

    if not text:
        return "", "No speech detected. Try again a little closer to the microphone."
    return text, None


def process_audio_input(audio_bytes: bytes) -> str:
    """Backwards-compatible helper: returns the transcript, or an empty string on failure."""
    return transcribe_audio(audio_bytes)[0]