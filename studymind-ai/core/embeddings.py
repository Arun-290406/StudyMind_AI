# core/embeddings.py
"""
Embedding model wrapper — FIXED version.

Root cause of AssertionError (assert d == self.d):
  The FAISS index was built with one embedding model (e.g. OpenAI 1536-dim),
  but queried with a different model (e.g. all-MiniLM 384-dim).
  This module uses a module-level singleton so the SAME model instance is
  always returned for both indexing AND querying within a session.

Rules:
  - If OPENAI_API_KEY is valid  → OpenAI text-embedding-3-small (1536 dims)
  - Otherwise                   → all-MiniLM-L6-v2 via HuggingFace (384 dims)
  - The chosen model is recorded in data/vector_db/embedding_model.txt
  - On load, we verify the saved model matches the current one; if not,
    the stale index is deleted so a fresh one is built automatically.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
META_FILE       = Path(os.getenv("FAISS_INDEX_PATH", "./data/vector_db/faiss_index")) / "embedding_model.txt"

# ── Decide which backend to use ───────────────────────────────────────────────
_use_openai = (
    bool(OPENAI_API_KEY)
    and not OPENAI_API_KEY.startswith("sk-your")
    and not EMBEDDING_MODEL.startswith("all-")
    and not EMBEDDING_MODEL.startswith("sentence-")
)

# Final resolved model name (used as the canonical key stored to disk)
RESOLVED_MODEL = EMBEDDING_MODEL if _use_openai else "all-MiniLM-L6-v2"

# Module-level singleton — created once, reused always
_embedding_instance = None


def get_embedding_model():
    """
    Return the singleton embedding model.
    Always returns the SAME instance so index & query dimensions always match.
    """
    global _embedding_instance
    if _embedding_instance is not None:
        return _embedding_instance

    if _use_openai:
        from langchain_openai import OpenAIEmbeddings
        print(f"[embeddings] Using OpenAI model: {EMBEDDING_MODEL}")
        _embedding_instance = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
        )
    else:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print(f"[embeddings] Using local model: {RESOLVED_MODEL}")
        _embedding_instance = HuggingFaceEmbeddings(
            model_name=RESOLVED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _embedding_instance


def save_model_meta():
    """Write the resolved model name next to the FAISS index."""
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    META_FILE.write_text(RESOLVED_MODEL, encoding="utf-8")


def check_model_meta() -> bool:
    """
    Return True if the saved model matches the current one.
    Return False (stale index) if they differ or file doesn't exist.
    """
    if not META_FILE.exists():
        return False
    saved = META_FILE.read_text(encoding="utf-8").strip()
    match = (saved == RESOLVED_MODEL)
    if not match:
        print(f"[embeddings] Model mismatch: saved='{saved}' current='{RESOLVED_MODEL}'")
    return match


def embed_texts(texts: List[str]) -> List[List[float]]:
    return get_embedding_model().embed_documents(texts)


def embed_query(query: str) -> List[float]:
    return get_embedding_model().embed_query(query)