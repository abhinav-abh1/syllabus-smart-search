import google.generativeai as genai
from django.conf import settings
from google.api_core.exceptions import ResourceExhausted
import logging

genai.configure(api_key=settings.GEMINI_API_KEY)
logger = logging.getLogger(__name__)


def generate_study_material(topic, contents):
    """
    Generates HIGHLY ACCURATE study material.
    RULES:
    - Use ONLY the given textbook text
    - Do NOT add new facts
    - Do NOT assume knowledge
    - Rephrase and structure strictly
    """

    # Combine only the most relevant extracted text
    source_text = "\n".join(f"- {c.content}" for c in contents[:6])

    prompt = f"""
You are an academic content formatter.

TASK:
Convert the given textbook content into structured study material.

STRICT RULES:
1. Use ONLY the information present in the text below.
2. Do NOT add new facts, examples, or explanations.
3. Do NOT use outside knowledge.
4. Rephrase for clarity, but preserve original meaning.
5. If information is insufficient, say "Based on textbook content".

FORMAT EXACTLY AS:
Definition:
Key Points:
Explanation:
Exam Notes:

TEXTBOOK CONTENT:
{source_text}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()

    except ResourceExhausted:
        logger.warning("AI quota exceeded – using grounded fallback")

        # 🔒 Grounded fallback (no hallucination)
        return (
            f"Definition:\n{contents[0].content if contents else ''}\n\n"
            f"Key Points:\nRefer textbook points above.\n\n"
            f"Explanation:\nBased strictly on extracted textbook content.\n\n"
            f"Exam Notes:\nStudy the definition and explanation as given in the textbook."
        )

    except Exception as e:
        logger.error(f"AI study material error: {e}")

    return None
