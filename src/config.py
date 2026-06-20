import os
from dotenv import load_dotenv

load_dotenv()

# ── API ──────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

# ── Model identifiers ────────────────────────────────────────────────────────
CHAT_MODEL: str = "gemini-2.5-flash"          # Generation model
EMBED_MODEL: str = "gemini-embedding-001"        # Embedding model

# ── Vector DB ────────────────────────────────────────────────────────────────
CHROMA_DB_DIR: str = "./chroma_db"
COLLECTION_NAME: str = "support_kb"

# ── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 50

# ── Retrieval ────────────────────────────────────────────────────────────────
TOP_K: int = 3

# ── Escalation thresholds ────────────────────────────────────────────────────
# Cosine similarity score below this → escalate
CONFIDENCE_THRESHOLD: float = 0.45

# Keywords that always trigger escalation regardless of confidence
SENSITIVE_KEYWORDS: list[str] = [
    "refund", "billing dispute", "chargeback", "legal", "lawsuit",
    "fraud", "unauthorized charge", "account closure", "gdpr",
    "data breach", "cancel subscription", "money back",
]

# Number of consecutive frustrated turns before forced escalation
FRUSTRATION_TURN_LIMIT: int = 3

# ── Data directory ────────────────────────────────────────────────────────────
DATA_DIR: str = "./data"
