import json
import os

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, CHAT_MODEL

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "persona": {
            "type": "STRING",
            "enum": ["Technical Expert", "Frustrated User", "Business Executive"],
        },
        "confidence": {"type": "NUMBER"},
        "reasoning": {"type": "STRING"},
    },
    "required": ["persona", "confidence", "reasoning"],
}

_SYSTEM_INSTRUCTION = (
    "You are an advanced customer-persona classification engine. "
    "Analyse the sentiment, vocabulary, technical depth, and tone of the incoming "
    "support message and classify it into exactly ONE of the three personas below:\n\n"
    "1. 'Technical Expert'  — Uses technical jargon; asks about APIs, error codes, "
    "   configurations, logs, or code; wants detailed root-cause analysis.\n"
    "2. 'Frustrated User'   — Uses emotional or urgent language, exclamation marks, "
    "   expresses repeated frustration, or demands immediate action.\n"
    "3. 'Business Executive'— Focuses on business impact, ROI, timelines, or SLA; "
    "   prefers concise, outcome-focused communication.\n\n"
    "Respond ONLY with the requested JSON structure. No extra text."
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_customer_persona(user_message: str) -> dict:
    """
    Analyse *user_message* and return a persona classification dict.

    Returns
    -------
    {
        "persona":    "Technical Expert" | "Frustrated User" | "Business Executive",
        "confidence": float,   # 0.0 – 1.0
        "reasoning":  str
    }
    """
    if not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=_RESPONSE_SCHEMA,
            temperature=0.1,   # Low temp for deterministic classification
        ),
    )

    result = json.loads(response.text)
    # Clamp confidence to [0, 1] defensively
    result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
    return result


# ---------------------------------------------------------------------------
# Standalone smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = [
        "Our production API key stopped working with 401 Unauthorized. Check logs immediately.",
        "I've been waiting for hours and NOTHING is working! This is unacceptable!!!",
        "What's the estimated resolution time and the business impact on our SLA?",
    ]
    for msg in samples:
        print(f"\nMessage : {msg}")
        print(json.dumps(classify_customer_persona(msg), indent=2))
