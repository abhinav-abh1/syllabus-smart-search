import google.generativeai as genai
from django.conf import settings
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable
import logging

genai.configure(api_key=settings.GEMINI_API_KEY)
logger = logging.getLogger(__name__)


def generate_reference_definition(topic: str) -> str | None:
    """
    Generate a short, textbook-style reference definition using Gemini.
    This definition is NEVER shown to the user — it is only used
    as a semantic query vector.

    Returns:
        str  → clean definition
        None → if generation fails
    """
    if not topic or not topic.strip():
        return None

    topic = topic.strip()

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = (
            f"Write a clear, concise, formal definition of the term '{topic}' "
            f"exactly as it would appear in a standard university textbook. "
            f"Requirements:\n"
            f"- One or two sentences only\n"
            f"- No examples\n"
            f"- No extra explanation\n"
            f"- Academic and precise language"
        )

        response = model.generate_content(
            prompt,
            request_options={"timeout": 20}   # prevent long hangs
        )

        if response and hasattr(response, "text") and response.text:
            definition = response.text.strip()

            # Clean common AI artifacts
            definition = definition.replace("**", "").replace("*", "").strip()

            if len(definition.split()) < 5:
                logger.warning(f"Gemini returned too short definition for '{topic}'")
                return None

            logger.info(f"[Gemini] Reference definition generated for: {topic}")
            return definition

        return None

    except ResourceExhausted:
        logger.warning("Gemini quota exceeded. Using academic fallback.")
        return _fallback_definition(topic)

    except (DeadlineExceeded, ServiceUnavailable) as e:
        logger.warning(f"Gemini temporary error ({type(e).__name__}). Using fallback.")
        return _fallback_definition(topic)

    except Exception as e:
        logger.error(f"Gemini unexpected error for '{topic}': {e}")
        return None


def _fallback_definition(topic: str) -> str:
    """
    Simple academic-style fallback when Gemini is unavailable.
    Still better than returning None (which breaks the pipeline).
    """
    return (
        f"{topic} is a fundamental concept that is formally defined in "
        f"standard university-level textbooks of the subject."
    )