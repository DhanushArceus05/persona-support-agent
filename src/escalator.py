import json
from datetime import datetime

from src.config import (
    CONFIDENCE_THRESHOLD,
    SENSITIVE_KEYWORDS,
    FRUSTRATION_TURN_LIMIT,
)


# ---------------------------------------------------------------------------
# Escalation decision
# ---------------------------------------------------------------------------

def should_escalate(
    user_message: str,
    persona: str,
    context_chunks: list[dict],
    frustration_streak: int = 0,
) -> tuple[bool, str]:
    """
    Determine whether the current turn should be escalated.

    Parameters
    ----------
    user_message      : Raw user input.
    persona           : Classified persona string.
    context_chunks    : Retrieval results from the RAG pipeline.
    frustration_streak: Consecutive turns the user has been a "Frustrated User".

    Returns
    -------
    (escalate: bool, reason: str)
    """
    # 1. No relevant documents found
    if not context_chunks:
        return True, "no_context"

    # 2. Low retrieval confidence
    best_score = max(c["score"] for c in context_chunks)
    if best_score < CONFIDENCE_THRESHOLD:
        return True, f"low_confidence ({best_score:.3f} < {CONFIDENCE_THRESHOLD})"

    # 3. Sensitive keyword detected in the message
    msg_lower = user_message.lower()
    for kw in SENSITIVE_KEYWORDS:
        if kw in msg_lower:
            return True, f"sensitive_keyword: '{kw}'"

    # 4. Repeated frustration
    if persona == "Frustrated User" and frustration_streak >= FRUSTRATION_TURN_LIMIT:
        return True, f"repeated_frustration (streak={frustration_streak})"

    return False, ""


# ---------------------------------------------------------------------------
# Handoff summary generator
# ---------------------------------------------------------------------------

def generate_handoff_summary(
    user_query: str,
    persona: str,
    context_chunks: list[dict],
    conversation_history: list[dict],
    escalation_reason: str,
) -> dict:
    """
    Build a structured JSON handoff payload for the human agent.

    Parameters
    ----------
    user_query          : The message that triggered escalation.
    persona             : Detected persona.
    context_chunks      : Retrieved document chunks (may be empty).
    conversation_history: Full list of {role, content} dicts for this session.
    escalation_reason   : Short string describing why escalation fired.

    Returns
    -------
    A dict ready to be serialised as the handoff JSON.
    """
    sources_used = list({c["source"] for c in context_chunks}) if context_chunks else []
    best_score = (
        max(c["score"] for c in context_chunks) if context_chunks else 0.0
    )

    # Derive attempted steps from assistant messages in history
    attempted = []
    for turn in conversation_history:
        if turn.get("role") == "assistant" and turn.get("content"):
            # Summarise each previous assistant reply as a 120-char snippet
            snippet = turn["content"][:120].replace("\n", " ").strip()
            if snippet:
                attempted.append(snippet + "…")

    # Recommended next action based on escalation reason
    if "sensitive_keyword" in escalation_reason:
        recommendation = (
            "Route to billing / account specialist. Verify account ownership "
            "before processing any financial or legal action."
        )
    elif "low_confidence" in escalation_reason or "no_context" in escalation_reason:
        recommendation = (
            "Retrieve the relevant knowledge base article manually or consult "
            "Tier-2 support for an up-to-date resolution guide."
        )
    elif "repeated_frustration" in escalation_reason:
        recommendation = (
            "Acknowledge customer frustration personally. Offer a direct callback "
            "or escalated priority ticket."
        )
    else:
        recommendation = "Review full conversation and resolve at Tier-2 level."

    handoff = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "escalation_reason": escalation_reason,
        "persona": persona,
        "issue_summary": user_query[:200],
        "retrieval_confidence": round(best_score, 4),
        "documents_used": sources_used,
        "attempted_steps": attempted[-5:],   # Last 5 assistant responses
        "recommendation": recommendation,
        "conversation_turns": len(conversation_history),
    }
    return handoff


def format_handoff_display(handoff: dict) -> str:
    """Pretty-print the handoff dict as a JSON string for display."""
    return json.dumps(handoff, indent=2)
