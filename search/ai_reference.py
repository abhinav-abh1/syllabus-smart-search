import google.generativeai as genai
from django.conf import settings

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


def generate_reference_definition(topic):
    """
    Generates a hidden, textbook-style definition using Gemini (FREE).
    This definition is NOT shown to the user.
    """

    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    prompt = (
        f"Define '{topic}' clearly and concisely as it would appear "
        f"in a university textbook. "
        f"Do not give examples. Do not explain further."
    )

    response = model.generate_content(prompt)
    definition = response.text.strip()

    # 🔍 Log to server console
    print("\n===== GEMINI AI REFERENCE DEFINITION (HIDDEN) =====")
    print(definition)
    print("=================================================\n")

    return definition
