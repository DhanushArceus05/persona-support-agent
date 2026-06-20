# 🤖 Persona-Adaptive Customer Support Agent

An intelligent AI-powered customer support system that classifies users into communication personas, retrieves relevant knowledge from a document base using RAG, generates contextually appropriate responses, and escalates complex issues to human agents automatically.

---

## 📌 Project Overview

This system solves a core challenge in AI customer support: **one tone does not fit all customers**. A developer debugging an API error needs code-level precision. A frustrated user needs empathy first. A business executive needs a 3-line answer about operational impact.

This agent automatically detects which type of customer it is talking to and adapts every response — tone, depth, structure, and vocabulary — accordingly.

**Key capabilities:**
- Real-time persona detection using Gemini LLM structured output
- RAG pipeline with ChromaDB for hallucination-free, grounded responses
- Three adaptive response templates (Technical Expert, Frustrated User, Business Executive)
- Automatic escalation on low confidence, sensitive topics, or repeated frustration
- Structured human handoff JSON on escalation
- Multi-turn conversation memory
- Streamlit chat UI with session metrics

---

## 🧰 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.11+ |
| LLM | Google Gemini 2.0 Flash | via `google-genai` |
| Embeddings | Gemini text-embedding-004 | via `google-genai` |
| Vector Database | ChromaDB (persistent) | ≥ 0.4.0 |
| Document Chunking | LangChain RecursiveCharacterTextSplitter | ≥ 0.1.0 |
| PDF Parsing | pypdf | ≥ 3.0.0 |
| UI | Streamlit | ≥ 1.30.0 |
| Config | python-dotenv | ≥ 1.0.0 |

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER MESSAGE                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   1. PERSONA CLASSIFIER                         │
│  Gemini + Structured JSON Output                                │
│  → persona: "Technical Expert" | "Frustrated User"             │
│             | "Business Executive"                              │
│  → confidence: 0.0–1.0                                         │
│  → reasoning: string                                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                     ┌──────────┴──────────┐
                     │                     │
                     ▼                     ▼
      ┌──────────────────────┐   ┌──────────────────────┐
      │  2. RAG PIPELINE     │   │  Frustration Streak  │
      │  • Load documents    │   │  Counter (session)   │
      │  • Chunk text        │   └──────────────────────┘
      │  • Embed chunks      │
      │  • ChromaDB store    │
      │  • Cosine similarity │
      │  → Top-K chunks      │
      └──────────┬───────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   3. ESCALATION CHECK                           │
│  Conditions:                                                    │
│  a) No context chunks retrieved          → ESCALATE            │
│  b) Best similarity score < 0.45         → ESCALATE            │
│  c) Sensitive keyword detected           → ESCALATE            │
│  d) Frustrated User streak ≥ 3 turns     → ESCALATE            │
└──────────────┬──────────────────────────┬───────────────────────┘
               │ No Escalation            │ Escalate
               ▼                          ▼
┌──────────────────────────┐  ┌──────────────────────────────────┐
│  4. ADAPTIVE GENERATOR   │  │  5. HUMAN HANDOFF                │
│  Persona-specific prompt │  │  Structured JSON summary:        │
│  + RAG context injected  │  │  • detected_persona              │
│  + Conversation history  │  │  • issue_summary                 │
│  → Grounded response     │  │  • retrieval_confidence          │
└──────────────────────────┘  │  • documents_used                │
               │              │  • attempted_steps               │
               └──────────────┤  • recommendation                │
                              └──────────────────────────────────┘
                                           │
                                           ▼
                              ┌──────────────────────────┐
                              │     STREAMLIT UI          │
                              │  Displays: message,       │
                              │  persona badge, sources,  │
                              │  response, escalation     │
                              │  status, handoff JSON     │
                              └──────────────────────────┘
```

---

## 👤 Persona Detection Strategy

### Classification Method
Persona detection is performed by Gemini using **structured JSON output** with a constrained response schema. The model is given a carefully crafted system prompt and returns exactly one of three enum values alongside a confidence score.

### Prompt Design
The system prompt instructs Gemini to analyse:
- **Vocabulary and terminology** (technical jargon vs. plain language vs. business terms)
- **Emotional tone** (neutral, frustrated, urgent, professional)
- **Request structure** (diagnostic vs. emotional vs. outcome-focused)

Temperature is set to `0.1` for near-deterministic classification results.

### Decision Rules
| Signal | Persona |
|---|---|
| API, error codes, logs, configurations, code | Technical Expert |
| Exclamation marks, "nothing works", urgency, complaints | Frustrated User |
| ROI, timeline, business impact, SLA, resolution ETA | Business Executive |

---

## 📚 RAG Pipeline Design

### 1. Chunking Strategy
- **Splitter**: `RecursiveCharacterTextSplitter` — splits on `\n\n`, then `\n`, then ` `, preserving semantic units
- **Chunk size**: 500 characters — focuses each chunk on a single topic
- **Chunk overlap**: 50 characters — prevents context loss at boundaries

### 2. Embedding Model
- **Model**: `text-embedding-004` (Google Gemini)
- **Dimensions**: 768
- **Why**: State-of-the-art semantic understanding; tightly integrated with the generation model

### 3. Vector Database
- **Database**: ChromaDB (persistent local)
- **Distance metric**: Cosine similarity
- **Why ChromaDB**: Zero-ops local deployment, persistent across restarts, no external service required

### 4. Retrieval Strategy
- **Top-K**: 3 most similar chunks retrieved per query
- **Score**: Cosine similarity (ChromaDB distance converted: `score = 1 - distance/2`)
- **Metadata**: Source filename and chunk index stored alongside each vector

---

## 🚨 Escalation Logic

Escalation fires when **any** of the following conditions are met:

| Trigger | Condition | Configurable In |
|---|---|---|
| No context | Zero chunks retrieved | Hardcoded (empty results) |
| Low confidence | Best similarity < `0.45` | `src/config.py` → `CONFIDENCE_THRESHOLD` |
| Sensitive keyword | Billing, refund, legal, fraud, etc. | `src/config.py` → `SENSITIVE_KEYWORDS` |
| Repeated frustration | Frustrated User for ≥ 3 consecutive turns | `src/config.py` → `FRUSTRATION_TURN_LIMIT` |

All thresholds are centralised in `src/config.py` for easy tuning.

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.11 or higher
- A Google AI Studio API key (free tier available at aistudio.google.com)

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/persona-support-agent.git
cd persona-support-agent
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and add your key:
# GEMINI_API_KEY="your_key_here"
```

### 5. Run the Application
```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

> **First run**: The knowledge base is indexed on startup (~30 seconds). Subsequent runs load the persisted ChromaDB index instantly.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google AI Studio API key for Gemini LLM and embeddings |

---

## 💬 Example Queries

| # | Query | Expected Persona | Expected Behaviour |
|---|---|---|---|
| 1 | *"Where is the guide to clear cookies? It's been an hour and nothing is loading on your interface!"* | Frustrated User | Empathise first, then list simple numbered steps to clear cache |
| 2 | *"What are the header parameter requirements for your bearer token auth implementation?"* | Technical Expert | Output HTTP header format, OAuth scope details, code snippets |
| 3 | *"Our operational uptime is decreasing. We need a timeline of when billing disputes are resolved."* | Business Executive | Concise: SLA percentages, resolution timeline, no jargon |
| 4 | *"I'm experiencing a ECONNREFUSED error with the database integration — check the connector logs."* | Technical Expert | Retrieve DB troubleshooting doc, IP allowlist config, port check steps |
| 5 | *"My billing statement has unexpected duplicate charges. I demand an immediate refund!"* | Frustrated User | **Trigger escalation** — sensitive keyword detected; generate handoff JSON |

---

## 📁 Project Structure

```
persona-support-agent/
│
├── data/                              # Knowledge base documents
│   ├── api_troubleshooting.md         # API auth errors and fixes
│   ├── billing_policy.txt             # Subscription and refund policy
│   ├── account_security_faq.md        # Password, 2FA, team management
│   ├── sla_uptime_policy.txt          # SLA commitments and credits
│   ├── onboarding_guide.md            # First-time setup guide
│   ├── database_integration.md        # DB connector troubleshooting
│   ├── performance_optimization.txt   # Rate limits and performance tips
│   ├── error_codes_reference.md       # HTTP and platform error codes
│   ├── browser_cache_troubleshooting.txt  # Browser/cache fix guide
│   └── password_reset_guide.pdf       # PDF: Password & 2FA recovery
│
├── src/
│   ├── __init__.py
│   ├── config.py          # All constants and thresholds
│   ├── classifier.py      # Gemini-based persona detector
│   ├── rag_pipeline.py    # Document loader, embedder, retriever
│   ├── generator.py       # Persona-adaptive response generator
│   └── escalator.py       # Escalation logic and handoff builder
│
├── app.py                 # Streamlit UI
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚠️ Known Limitations

1. **Embedding rate limits**: Ingesting large document sets may hit Gemini embedding API rate limits. The pipeline includes a 50 ms sleep between calls; increase this for larger corpora.
2. **Context window**: Only the last 10 conversation turns are included in multi-turn generation to stay within the model's context window.
3. **Language**: The system is optimised for English. Multilingual support would require language detection and localised persona prompts.
4. **Concurrent users**: ChromaDB's persistent client is not thread-safe for concurrent writes. For production multi-user deployment, use a dedicated vector DB service (Qdrant, Pinecone, Weaviate).
5. **Persona ambiguity**: Some messages exhibit mixed signals (e.g., a frustrated executive). The classifier returns the dominant signal, but edge cases may be misclassified.

---

## 🚀 Future Improvements

- [ ] LangGraph multi-agent architecture with specialist sub-agents per persona
- [ ] Sentiment drift tracking across multi-turn conversations
- [ ] User feedback collection (thumbs up/down) stored in SQLite
- [ ] Analytics dashboard showing persona distribution over sessions
- [ ] Hybrid search (BM25 keyword + vector similarity)
- [ ] Support for DOCX documents in the knowledge base
- [ ] Streaming token-by-token response generation in the UI
