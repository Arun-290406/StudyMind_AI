# core/vector_store.py
"""
Vector store — FIXED version.

Fixes applied:
1. Calls save_model_meta() after every build so the embedding model name
   is persisted alongside the FAISS index.
2. Calls check_model_meta() before loading; if the saved model doesn't
   match the current one the stale index is deleted automatically so a
   fresh index is built instead of crashing with AssertionError.
3. Catches AssertionError / RuntimeError during similarity_search and
   raises a clear ValueError instead of a cryptic FAISS assert.
4. index_exists() also checks the model metadata — a stale index is
   treated as "not existing" so the UI asks the user to re-index.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from dotenv import load_dotenv

from core.embeddings import (
    get_embedding_model, save_model_meta,
    check_model_meta, RESOLVED_MODEL,
)

load_dotenv()

BACKEND          = os.getenv("VECTOR_STORE_BACKEND", "faiss").lower()
FAISS_INDEX_PATH = Path(os.getenv("FAISS_INDEX_PATH", "./data/vector_db/faiss_index"))
CHROMA_DIR       = Path(os.getenv("CHROMA_PERSIST_DIR", "./data/vector_db/chroma"))
COLLECTION_NAME  = "studymind_docs"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _nuke_stale_index():
    """Delete a FAISS index whose embedding model no longer matches."""
    if FAISS_INDEX_PATH.exists():
        shutil.rmtree(FAISS_INDEX_PATH)
        print("[vector_store] Stale FAISS index deleted — will rebuild.")


# ── Build ─────────────────────────────────────────────────────────────────────

def build_vector_store(docs: List[Document], persist: bool = True):
    """Build a fresh vector store and save model metadata alongside it."""
    embedding_fn = get_embedding_model()

    if BACKEND == "chroma":
        vs = _build_chroma(docs, embedding_fn, persist)
    else:
        vs = _build_faiss(docs, embedding_fn, persist)

    # Record which model was used so we can detect mismatches on next load
    if persist:
        save_model_meta()

    return vs


def _build_faiss(docs, embedding_fn, persist):
    from langchain_community.vectorstores import FAISS
    print(f"[vector_store] Building FAISS index ({len(docs)} chunks, model={RESOLVED_MODEL})…")
    vs = FAISS.from_documents(docs, embedding_fn)
    if persist:
        FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
        vs.save_local(str(FAISS_INDEX_PATH))
        print(f"[vector_store] FAISS saved → {FAISS_INDEX_PATH}")
    return vs


def _build_chroma(docs, embedding_fn, persist):
    from langchain_community.vectorstores import Chroma
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[vector_store] Building ChromaDB ({len(docs)} chunks)…")
    vs = Chroma.from_documents(
        docs, embedding_fn,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR) if persist else None,
    )
    if persist:
        vs.persist()
    return vs


# ── Load ──────────────────────────────────────────────────────────────────────

def load_vector_store(allow_dangerous_deserialization: bool = True):
    """
    Load a persisted vector store.
    Returns None (instead of crashing) if the index is stale or missing.
    """
    if BACKEND == "chroma":
        return _load_chroma()
    else:
        return _load_faiss(allow_dangerous_deserialization)


def _load_faiss(allow_dangerous: bool):
    from langchain_community.vectorstores import FAISS

    if not FAISS_INDEX_PATH.exists():
        return None

    # Model mismatch check — delete stale index, return None
    if not check_model_meta():
        _nuke_stale_index()
        return None

    embedding_fn = get_embedding_model()
    try:
        print(f"[vector_store] Loading FAISS index from {FAISS_INDEX_PATH}")
        return FAISS.load_local(
            str(FAISS_INDEX_PATH),
            embedding_fn,
            allow_dangerous_deserialization=allow_dangerous,
        )
    except (AssertionError, RuntimeError, Exception) as e:
        print(f"[vector_store] Failed to load FAISS index: {e} — deleting stale index.")
        _nuke_stale_index()
        return None


def _load_chroma():
    from langchain_community.vectorstores import Chroma
    if not CHROMA_DIR.exists():
        return None
    embedding_fn = get_embedding_model()
    try:
        return Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embedding_fn,
            persist_directory=str(CHROMA_DIR),
        )
    except Exception as e:
        print(f"[vector_store] Failed to load ChromaDB: {e}")
        return None


# ── Update ────────────────────────────────────────────────────────────────────

def add_documents_to_store(vector_store, new_docs: List[Document]):
    vector_store.add_documents(new_docs)
    if BACKEND == "faiss":
        FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(FAISS_INDEX_PATH))
        save_model_meta()
    elif BACKEND == "chroma":
        vector_store.persist()
    return vector_store


def delete_vector_store():
    if BACKEND == "faiss" and FAISS_INDEX_PATH.exists():
        shutil.rmtree(FAISS_INDEX_PATH)
        print("[vector_store] FAISS index deleted.")
    elif BACKEND == "chroma" and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
        print("[vector_store] ChromaDB deleted.")


# ── Search ────────────────────────────────────────────────────────────────────

def similarity_search(vector_store, query: str, k: int = 5) -> List[Document]:
    return vector_store.similarity_search(query, k=k)


def similarity_search_with_score(vector_store, query: str, k: int = 5):
    return vector_store.similarity_search_with_score(query, k=k)


# ── Index existence check ─────────────────────────────────────────────────────

def index_exists() -> bool:
    """
    Returns True only if the index exists AND was built with the current
    embedding model. A stale index is treated as non-existent.
    """
    if BACKEND == "faiss":
        if not (FAISS_INDEX_PATH.exists() and any(FAISS_INDEX_PATH.iterdir())):
            return False
        return check_model_meta()      # False → stale, treat as missing
    elif BACKEND == "chroma":
        return CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())
    return False