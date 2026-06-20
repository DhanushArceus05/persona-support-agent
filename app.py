"""Main Streamlit application"""

import json
import time
import sys
import os

import streamlit as st

# ── Page config — must be first Streamlit call ────────────────────────────────
st.set_page_config(
    page_title="AI Support Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from src.config import GEMINI_API_KEY, DATA_DIR, CONFIDENCE_THRESHOLD
from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response
from src.escalator import should_escalate, generate_handoff_summary, format_handoff_display

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] {
    background: #0f172a;
    color: #e2e8f0;
}
[data-testid="stSidebar"] {
    background: #1e293b;
    border-right: 1px solid #334155;
}
[data-testid="stHeader"] { background: transparent; }

/* ── Chat messages ── */
.user-bubble {
    background: #1d4ed8;
    color: #eff6ff;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    margin: 8px 0 8px 60px;
    font-size: 0.95rem;
    line-height: 1.55;
}
.assistant-bubble {
    background: #1e293b;
    color: #e2e8f0;
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
    margin: 8px 60px 8px 0;
    font-size: 0.95rem;
    line-height: 1.55;
    border: 1px solid #334155;
}
.escalated-bubble {
    background: #7f1d1d;
    color: #fecaca;
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
    margin: 8px 60px 8px 0;
    font-size: 0.95rem;
    border: 1px solid #991b1b;
}

/* ── Persona badge ── */
.persona-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
}
.badge-tech   { background: #0c4a6e; color: #7dd3fc; }
.badge-frust  { background: #78350f; color: #fcd34d; }
.badge-exec   { background: #064e3b; color: #6ee7b7; }
.badge-unkn   { background: #312e81; color: #c4b5fd; }

/* ── Sources ── */
.source-chip {
    display: inline-block;
    background: #0f172a;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.7rem;
    color: #94a3b8;
    margin: 2px 3px;
}
.source-score { color: #4ade80; font-weight: 600; }

/* ── Handoff card ── */
.handoff-card {
    background: #1c1917;
    border: 1px solid #92400e;
    border-radius: 8px;
    padding: 12px 14px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #fde68a;
    white-space: pre-wrap;
    margin-top: 8px;
}

/* ── Input ── */
[data-testid="stChatInput"] textarea {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #475569 !important;
}

/* ── Metrics ── */
[data-testid="stMetricValue"] { color: #38bdf8; }
[data-testid="stMetricLabel"] { color: #94a3b8; }

/* ── Sidebar text ── */
.sidebar-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 12px 0 4px;
}

/* ── Status indicator ── */
.status-ok  { color: #4ade80; }
.status-err { color: #f87171; }
.status-warn { color: #fbbf24; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

PERSONA_BADGE_CLASS = {
    "Technical Expert": "badge-tech",
    "Frustrated User": "badge-frust",
    "Business Executive": "badge-exec",
}
PERSONA_ICON = {
    "Technical Expert": "⚙️",
    "Frustrated User": "😤",
    "Business Executive": "💼",
}


def persona_badge_html(persona: str) -> str:
    cls = PERSONA_BADGE_CLASS.get(persona, "badge-unkn")
    icon = PERSONA_ICON.get(persona, "🤖")
    return f'<span class="persona-badge {cls}">{icon} {persona}</span>'


def sources_html(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    chips = "".join(
        f'<span class="source-chip">📄 {c["source"]} '
        f'<span class="source-score">{c["score"]:.2f}</span></span>'
        for c in chunks
    )
    return f"<div style='margin-top:6px'>{chips}</div>"


# ── Session state initialisation ──────────────────────────────────────────────

def _init_state():
    defaults = {
        "messages": [],            # [{role, content, persona, chunks, escalated, handoff}]
        "rag": None,               # LocalRAGPipeline instance
        "indexed": False,          # Whether documents have been ingested
        "frustration_streak": 0,   # Consecutive Frustrated User turns
        "total_turns": 0,
        "escalation_count": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ── RAG initialisation ────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_rag_pipeline() -> LocalRAGPipeline:
    return LocalRAGPipeline()


def ensure_indexed():
    """Ingest documents once per session."""
    if not st.session_state.indexed:
        rag = get_rag_pipeline()
        with st.spinner("📚 Indexing knowledge base — this takes ~30 seconds on first run…"):
            rag.ingest_all(DATA_DIR)
        st.session_state.rag = rag
        st.session_state.indexed = True
    elif st.session_state.rag is None:
        st.session_state.rag = get_rag_pipeline()


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🤖 AI Support Agent")
    st.markdown("*Persona-Adaptive Customer Support*")
    st.divider()

    # API key status
    if GEMINI_API_KEY:
        st.markdown('<p class="status-ok">● Gemini API connected</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-err">● GEMINI_API_KEY not set</p>', unsafe_allow_html=True)
        st.info("Add `GEMINI_API_KEY=...` to your `.env` file and restart.")

    # KB status
    if st.session_state.indexed:
        rag = st.session_state.rag
        count = rag.collection_size() if rag else 0
        st.markdown(f'<p class="status-ok">● Knowledge base ready ({count} chunks)</p>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-warn">● Knowledge base not yet indexed</p>',
                    unsafe_allow_html=True)

    st.divider()

    # Stats
    st.markdown('<p class="sidebar-label">Session Stats</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Turns", st.session_state.total_turns)
    col2.metric("Escalations", st.session_state.escalation_count)

    st.divider()
    st.markdown('<p class="sidebar-label">Escalation Threshold</p>', unsafe_allow_html=True)
    st.caption(f"Confidence < {CONFIDENCE_THRESHOLD:.2f} triggers human handoff")

    st.divider()
    st.markdown('<p class="sidebar-label">Try These</p>', unsafe_allow_html=True)
    example_queries = [
        "Where is the guide to clear cookies? It's been an hour and nothing is loading!",
        "What are the header parameter requirements for bearer token auth?",
        "Our uptime is decreasing. When will billing disputes be resolved?",
        "I'm getting a 401 error on the API — check the authentication logs.",
        "My billing statement has duplicate charges. I demand an immediate refund!",
    ]
    for q in example_queries:
        if st.button(q[:55] + ("…" if len(q) > 55 else ""), use_container_width=True):
            st.session_state["_inject_query"] = q
            st.rerun()

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.frustration_streak = 0
        st.session_state.total_turns = 0
        st.session_state.escalation_count = 0
        st.rerun()


# ── Main layout ───────────────────────────────────────────────────────────────

st.markdown("## 🤖 Customer Support Agent")
st.caption("Powered by Gemini · RAG · Persona Detection · Human Escalation")

if not GEMINI_API_KEY:
    st.error("⚠️ **GEMINI_API_KEY** is not configured. Please add it to your `.env` file and restart.")
    st.stop()

# Index on first load
ensure_indexed()

# ── Render chat history ───────────────────────────────────────────────────────

chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            bubble_cls = "escalated-bubble" if msg.get("escalated") else "assistant-bubble"
            persona = msg.get("persona", "")
            chunks  = msg.get("chunks", [])

            badge_html   = persona_badge_html(persona) if persona else ""
            sources      = sources_html(chunks)
            content_html = msg["content"].replace("\n", "<br>")

            st.markdown(
                f'<div class="{bubble_cls}">'
                f'{badge_html}<br>{content_html}'
                f'{sources}'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Expandable handoff JSON
            if msg.get("handoff"):
                with st.expander("📋 Human Handoff Summary (click to view)"):
                    st.code(format_handoff_display(msg["handoff"]), language="json")


# ── Chat input processing ─────────────────────────────────────────────────────

# Handle sidebar example injection
injected = st.session_state.pop("_inject_query", None)

user_input = st.chat_input("Type your support question…") or injected

if user_input:
    # 1. Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.total_turns += 1

    with st.spinner("🔍 Classifying persona…"):
        try:
            classification = classify_customer_persona(user_input)
        except Exception as e:
            st.error(f"Classification error: {e}")
            st.stop()

    persona     = classification["persona"]
    confidence  = classification["confidence"]
    reasoning   = classification["reasoning"]

    # Track frustration streak
    if persona == "Frustrated User":
        st.session_state.frustration_streak += 1
    else:
        st.session_state.frustration_streak = 0

    with st.spinner("📖 Searching knowledge base…"):
        rag = st.session_state.rag
        chunks = rag.retrieve_context(user_input)

    # Build history
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]   # Exclude current user msg
    ]

    # 4. Escalation check
    escalate, reason = should_escalate(
        user_message=user_input,
        persona=persona,
        context_chunks=chunks,
        frustration_streak=st.session_state.frustration_streak,
    )

    if escalate:
        st.session_state.escalation_count += 1
        handoff = generate_handoff_summary(
            user_query=user_input,
            persona=persona,
            context_chunks=chunks,
            conversation_history=history,
            escalation_reason=reason,
        )
        response_text = (
            "I'm sorry — I wasn't able to find a precise solution for your request in our "
            "knowledge base. I'm connecting you with a human support specialist right away. "
            "Your case has been summarised and our team will reach out shortly. "
            f"\n\n*Escalation reason: {reason}*"
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "persona": persona,
            "chunks": chunks,
            "escalated": True,
            "handoff": handoff,
        })
    else:
        with st.spinner("✍️ Generating response…"):
            try:
                response_text = generate_adaptive_response(
                    user_query=user_input,
                    persona=persona,
                    context_chunks=chunks,
                    conversation_history=history,
                )
            except Exception as e:
                response_text = f"⚠️ Generation error: {e}"

        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "persona": persona,
            "chunks": chunks,
            "escalated": False,
            "handoff": None,
        })

    st.rerun()
