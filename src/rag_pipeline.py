import os
import glob
import time

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from google import genai

from src.config import (
    GEMINI_API_KEY,
    EMBED_MODEL,
    CHROMA_DB_DIR,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    DATA_DIR,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_txt_or_md(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _read_pdf(filepath: str) -> str:
    reader = PdfReader(filepath)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def _load_documents(data_dir: str) -> list[dict]:
    """
    Walk *data_dir* and return a list of {name, content} dicts.
    Supported extensions: .txt  .md  .pdf
    """
    documents = []
    patterns = ["*.txt", "*.md", "*.pdf"]
    for pattern in patterns:
        for filepath in glob.glob(os.path.join(data_dir, pattern)):
            fname = os.path.basename(filepath)
            ext = os.path.splitext(fname)[1].lower()
            try:
                if ext == ".pdf":
                    content = _read_pdf(filepath)
                else:
                    content = _read_txt_or_md(filepath)
                if content.strip():
                    documents.append({"name": fname, "content": content})
                    print(f"  [load] {fname} ({len(content):,} chars)")
            except Exception as exc:
                print(f"  [warn] Could not read {fname}: {exc}")
    return documents


# ---------------------------------------------------------------------------
# Main pipeline class
# ---------------------------------------------------------------------------

class LocalRAGPipeline:
    """
    Encapsulates the full RAG workflow: ingest → embed → store → retrieve.
    """

    def __init__(self, db_dir: str = CHROMA_DB_DIR):
        if not GEMINI_API_KEY:
            raise EnvironmentError("GEMINI_API_KEY is not set.")

        self._genai = genai.Client(api_key=GEMINI_API_KEY)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        # Persistent ChromaDB — survives across sessions
        self._chroma = chromadb.PersistentClient(path=db_dir)
        self._col = self._chroma.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Embedding ────────────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float]:
        """Return the embedding vector for *text* using Gemini."""
        resp = self._genai.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
        )
        return resp.embeddings[0].values

    # ── Ingestion ────────────────────────────────────────────────────────────

    def ingest_document(self, doc_name: str, content: str) -> int:
        """
        Chunk *content*, embed each chunk, and upsert into ChromaDB.

        Returns the number of chunks stored.
        """
        chunks = self._splitter.split_text(content)
        count = 0
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_name}_chunk_{idx}"
            # Skip if already indexed
            existing = self._col.get(ids=[chunk_id])
            if existing and existing["ids"]:
                continue
            embedding = self._embed(chunk)
            self._col.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[{"source": doc_name, "chunk_index": idx}],
                documents=[chunk],
            )
            count += 1
            # Small sleep to avoid rate-limit bursts
            time.sleep(0.05)
        return count

    def ingest_all(self, data_dir: str = DATA_DIR) -> int:
        """
        Load every supported document from *data_dir* and ingest them.

        Returns total number of NEW chunks stored.
        """
        print(f"\n[RAG] Loading documents from '{data_dir}' …")
        docs = _load_documents(data_dir)
        if not docs:
            print("[RAG] ⚠  No documents found. Populate the /data directory first.")
            return 0

        total = 0
        for doc in docs:
            n = self.ingest_document(doc["name"], doc["content"])
            print(f"  [index] {doc['name']} → {n} new chunks")
            total += n
        print(f"[RAG] Ingestion complete. {total} new chunks added "
              f"({self._col.count()} total in DB).\n")
        return total

    # ── Retrieval ────────────────────────────────────────────────────────────

    def retrieve_context(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """
        Embed *query* and return the top-*k* most similar document chunks.

        Each item in the returned list:
        {
            "text":   str,    # raw chunk text
            "source": str,    # filename
            "score":  float,  # cosine similarity 0–1 (higher = better)
        }
        """
        if self._col.count() == 0:
            return []

        query_vec = self._embed(query)
        results = self._col.query(
            query_embeddings=[query_vec],
            n_results=min(top_k, self._col.count()),
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]
            for doc, meta, dist in zip(docs, metas, dists):
                # ChromaDB cosine distance ∈ [0, 2]; convert to similarity ∈ [0, 1]
                score = max(0.0, 1.0 - dist / 2.0)
                items.append({
                    "text": doc,
                    "source": meta.get("source", "unknown"),
                    "score": round(score, 4),
                })
        return items

    def collection_size(self) -> int:
        return self._col.count()


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    rag = LocalRAGPipeline()
    rag.ingest_all()
    hits = rag.retrieve_context("How do I reset my password?")
    for h in hits:
        print(f"\n[{h['score']:.3f}] {h['source']}\n{h['text'][:200]}")
