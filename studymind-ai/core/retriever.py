# core/retriever.py
"""
RAG retrieval pipeline — FIXED version.

Fixes applied:
1. retrieve() wraps similarity_search_with_score in try/except so an
   AssertionError from FAISS (dimension mismatch) surfaces as a clear
   ValueError rather than crashing the whole app.
2. Uses regular similarity_search as a safe fallback when scores fail.
3. Lowered SCORE_THRESHOLD so the local 384-dim model (which returns
   higher L2 distances) still returns results.
"""

import os
from typing import List, Dict

from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv()

TOP_K            = int(os.getenv("TOP_K_RETRIEVAL", 5))
SCORE_THRESHOLD  = 0.1   # lowered: all-MiniLM L2 distances are larger than OpenAI cosine


# ── Retriever factory ─────────────────────────────────────────────────────────

def get_retriever(vector_store, k: int = TOP_K, use_mmr: bool = True):
    """Return a LangChain retriever (MMR for diverse results)."""
    if use_mmr:
        return vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": k * 3, "lambda_mult": 0.6},
        )
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


# ── Safe retrieval ────────────────────────────────────────────────────────────

def retrieve(vector_store, query: str, k: int = TOP_K) -> List[Document]:
    """
    Retrieve top-k relevant chunks.
    Falls back to plain similarity_search if scored search fails.
    """
    # Try scored search first
    try:
        results = vector_store.similarity_search_with_score(query, k=k * 2)
        filtered = []
        for doc, score in results:
            # FAISS L2 distance → similarity (lower distance = higher similarity)
            similarity = 1.0 / (1.0 + float(score))
            if similarity >= SCORE_THRESHOLD:
                doc.metadata["similarity_score"] = round(similarity, 4)
                filtered.append(doc)
            if len(filtered) >= k:
                break
        if filtered:
            return filtered
        # If nothing passed threshold, return top-k without filtering
        docs_only = [doc for doc, _ in results[:k]]
        for doc in docs_only:
            if "similarity_score" not in doc.metadata:
                doc.metadata["similarity_score"] = 0.0
        return docs_only

    except (AssertionError, RuntimeError) as e:
        # Dimension mismatch — surface clearly
        raise ValueError(
            f"FAISS dimension mismatch — the stored index was built with a different "
            f"embedding model. Please clear the index and re-upload your documents. "
            f"(Details: {e})"
        ) from e
    except Exception as e:
        # Other search error — fall back to plain search
        print(f"[retriever] Scored search failed ({e}), falling back to plain search.")
        try:
            docs = vector_store.similarity_search(query, k=k)
            for doc in docs:
                doc.metadata.setdefault("similarity_score", 0.0)
            return docs
        except Exception as e2:
            raise ValueError(f"Retrieval failed entirely: {e2}") from e2


def retrieve_from_source(
    vector_store, query: str, source_name: str, k: int = TOP_K
) -> List[Document]:
    """Retrieve chunks scoped to a specific source file."""
    all_results = retrieve(vector_store, query, k=k * 3)
    return [d for d in all_results if d.metadata.get("source") == source_name][:k]


# ── Context assembly ──────────────────────────────────────────────────────────

def build_context_string(docs: List[Document], max_chars: int = 6000) -> str:
    """Assemble retrieved chunks into a prompt context string."""
    parts = []
    total = 0
    for doc in docs:
        source   = doc.metadata.get("source", "unknown")
        page     = doc.metadata.get("page")
        page_str = f", page {page}" if page else ""
        chunk    = f"[Source: {source}{page_str}]\n{doc.page_content}"
        if total + len(chunk) > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                parts.append(chunk[:remaining] + "…")
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n\n---\n\n".join(parts)


def extract_citations(docs: List[Document]) -> List[Dict]:
    """Extract citation metadata from retrieved documents."""
    citations, seen = [], set()
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        page   = doc.metadata.get("page")
        key    = f"{source}:{page}"
        if key not in seen:
            seen.add(key)
            citations.append({
                "source":  source,
                "page":    page,
                "snippet": doc.page_content[:120] + "…",
                "score":   doc.metadata.get("similarity_score", 0),
            })
    return citations