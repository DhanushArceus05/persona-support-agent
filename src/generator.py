

import os
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, CHAT_MODEL

# ---------------------------------------------------------------------------
# Persona prompt
# ---------------------------------------------------------------------------

_PERSONA_INSTRUCTIONS: dict[str, str] = {
    "Technical Expert": (
        "You are a Senior Systems Engineer and Support Specialist. "
        "The user is technically proficient. Provide precise root-cause analysis, "
        "configuration parameters, API pathways, log inspection steps, and code "
        "snippets where relevant. Use technical terminology accurately. "
        "Structure your answer with clear headings or numbered steps."
    ),
    "Frustrated User": (
        "You are a warm, deeply empathetic Customer Care Specialist. "
        "The user is upset or stressed — your first priority is to validate their "
        "feelings before offering solutions. Begin with a genuine, human acknowledgement "
        "of their difficulty. Use simple, jargon-free language. "
        "Present actions as short, clearly numbered bullet points. "
        "End with a reassuring closing statement."
    ),
    "Business Executive": (
        "You are a concise Client Relations Director communicating with a senior "
        "business stakeholder. Prioritise direct answers, estimated resolution "
        "timelines, and operational impact summaries. Omit low-level technical "
        "details unless explicitly asked. Keep the response brief, professional, "
        "and outcome-focused."
    ),
}

_CRITICAL_RULES = (
    "CRITICAL RULES — follow these without exception:\n"
    "• Base your response ONLY on the FACTUAL CONTEXT DOCUMENTS provided below.\n"
    "• Do NOT hallucinate, invent, or assume facts not present in the documents.\n"
    "• If the documents do not contain sufficient information to answer, say so "
    "  honestly and suggest the user contact a specialist.\n"
    "• Always cite which document(s) informed your answer (e.g. '[source: billing_policy.txt]').\n"
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_adaptive_response(
    user_query: str,
    persona: str,
    context_chunks: list[dict],
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Generate a persona-adapted, context-grounded response.

    Parameters
    ----------
    user_query          : The user's current message.
    persona             : One of the three persona strings.
    context_chunks      : Retrieved RAG chunks [{text, source, score}, …].
    conversation_history: Optional list of {role, content} for multi-turn memory.

    Returns
    -------
    The assistant's response as a string.
    """
    if not GEMINI_API_KEY:
        raise EnvironmentError("GEMINI_API_KEY is not set.")

    persona_instr = _PERSONA_INSTRUCTIONS.get(
        persona, _PERSONA_INSTRUCTIONS["Frustrated User"]
    )

    # Build context block
    context_block = "\n\n".join(
        f"[Source: {c['source']} | Relevance: {c['score']:.2f}]\n{c['text']}"
        for c in context_chunks
    )

    full_system_prompt = (
        f"{persona_instr}\n\n"
        f"{_CRITICAL_RULES}\n\n"
        "FACTUAL CONTEXT DOCUMENTS:\n"
        "──────────────────────────\n"
        f"{context_block}\n"
        "──────────────────────────"
    )

    # Build Gemini contents list for multi-turn support
    contents: list = []
    if conversation_history:
        for turn in conversation_history[-10:]:  # Keep last 10 turns to stay within context
           role = turn.get("role", "user")

           if role == "assistant":
               role = "model"
           elif role not in ["user", "model"]:
               role = "user"

           text = turn.get("content", "")
           if text:
               contents.append(types.Content(role=role, parts=[types.Part(text=text)]))

    # Append the current user query
    contents.append(types.Content(role="user", parts=[types.Part(text=user_query)]))

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=full_system_prompt,
            temperature=0.25,
            max_output_tokens=1024,
        ),
    )

    return response.text.strip()
