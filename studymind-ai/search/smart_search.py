# search/smart_search.py
"""
Smart Search & Auto-Tagging for StudyMind AI.
ALL functions used across the project are defined here.

Functions:
  tag_document()       - extract + store tags for a document (used in 10_multi_doc.py)
  register_document()  - save doc metadata to SQLite
  get_user_documents() - list all docs with their tags
  get_all_tags()       - all distinct tags for a user
  get_docs_by_tag()    - docs that match a tag
  smart_search()       - semantic search with optional tag filter
  extract_topics_keybert()  - KeyBERT keyword extraction
  extract_topics_llm()      - LLM-based topic extraction
"""

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()
DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "./data/db/studymind.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def _init_tables() -> None:
    """Create search/tagging tables. Safe to call on every import."""
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS doc_tags (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            doc_name   TEXT    NOT NULL,
            tag        TEXT    NOT NULL,
            score      REAL    DEFAULT 1.0,
            created_at TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS doc_registry (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            name       TEXT    NOT NULL,
            subject    TEXT    DEFAULT '',
            path       TEXT    NOT NULL,
            size_mb    REAL    DEFAULT 0,
            pages      INTEGER DEFAULT 0,
            added_at   TEXT    NOT NULL,
            UNIQUE(user_id, name)
        );
    """)
    c.commit()
    c.close()


_init_tables()


# ── Topic extraction ──────────────────────────────────────────────────────────

def extract_topics_keybert(text: str, top_n: int = 10) -> List[str]:
    """
    Extract key topics using KeyBERT (offline, fast, no API).
    Falls back to frequency-based extraction if KeyBERT not installed.
    """
    try:
        from keybert import KeyBERT
        kw_model = KeyBERT()
        keywords = kw_model.extract_keywords(
            str(text)[:3000],
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=top_n,
        )
        return [kw[0] for kw in keywords if kw[0]]
    except ImportError:
        print("[search] KeyBERT not installed — using fallback. Run: pip install keybert")
        return _fallback_topics(text)
    except Exception as e:
        print(f"[search] KeyBERT failed ({e}), using fallback")
        return _fallback_topics(text)


def _fallback_topics(text: str) -> List[str]:
    """Simple word-frequency fallback when KeyBERT is unavailable."""
    STOPWORDS = {
        "this","that","with","from","have","will","they","been","were","their",
        "which","would","could","should","about","there","after","before",
        "these","those","what","when","where","also","into","some","other",
        "more","most","than","then","such","each","much","many","over",
    }
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        if w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    top = sorted(freq.items(), key=lambda x: -x[1])[:12]
    return [w for w, _ in top]


def extract_topics_llm(text: str) -> List[str]:
    """
    Extract topics using the configured LLM (better quality than KeyBERT).
    Falls back to KeyBERT on failure.
    """
    import json
    try:
        from core.llm import simple_chat
        prompt = (
            "Extract the 8 most important topics/concepts from this text. "
            "Return ONLY a JSON array of short strings. No markdown, no preamble.\n\n"
            f"Text:\n{str(text)[:2000]}"
        )
        raw = simple_chat(prompt, temperature=0.2)
        # Strip any markdown code fences
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        topics = json.loads(clean)
        if isinstance(topics, list):
            return [str(t).strip() for t in topics[:10] if t]
    except Exception as e:
        print(f"[search] LLM topic extraction failed ({e}), using KeyBERT")
    return extract_topics_keybert(text)


# ── Document registry ─────────────────────────────────────────────────────────

def register_document(
    user_id: int,
    doc_name: str,
    path: str,
    subject: str = "",
    size_mb: float = 0.0,
    pages: int = 0,
) -> None:
    """Save a document to the registry. UPSERT on (user_id, name)."""
    c = _conn()
    c.execute("""
        INSERT OR REPLACE INTO doc_registry
            (user_id, name, subject, path, size_mb, pages, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, doc_name, subject or "", path,
          round(size_mb, 2), int(pages), datetime.utcnow().isoformat()))
    c.commit()
    c.close()


def tag_document(
    user_id: int,
    doc_name: str,
    text: str,
    use_llm: bool = False,
) -> List[str]:
    """
    Extract and store tags for a document.
    Called from app/pages/10_multi_doc.py after upload.
    Returns the list of extracted topic strings.
    """
    topics = extract_topics_llm(text) if use_llm else extract_topics_keybert(text)

    c = _conn()
    now = datetime.utcnow().isoformat()
    # Clear old tags for this doc first
    c.execute(
        "DELETE FROM doc_tags WHERE user_id=? AND doc_name=?",
        (user_id, doc_name)
    )
    # Insert new tags
    c.executemany(
        "INSERT INTO doc_tags (user_id, doc_name, tag, created_at) VALUES (?,?,?,?)",
        [(user_id, doc_name, t, now) for t in topics if t]
    )
    c.commit()
    c.close()
    return topics


# ── Queries ───────────────────────────────────────────────────────────────────

def get_user_documents(user_id: int) -> List[Dict]:
    """
    Return all registered documents with their tags.
    Called from app/pages/10_multi_doc.py.
    """
    if not user_id:
        return []
    c = _conn()
    rows = c.execute(
        "SELECT * FROM doc_registry WHERE user_id=? ORDER BY added_at DESC",
        (user_id,)
    ).fetchall()

    docs = []
    for r in rows:
        d = dict(r)
        tag_rows = c.execute(
            "SELECT tag FROM doc_tags WHERE user_id=? AND doc_name=?",
            (user_id, d["name"])
        ).fetchall()
        d["tags"] = [t["tag"] for t in tag_rows]
        docs.append(d)

    c.close()
    return docs


def get_all_tags(user_id: int) -> List[str]:
    """Return all distinct tags for a user, sorted alphabetically."""
    if not user_id:
        return []
    c = _conn()
    rows = c.execute(
        "SELECT DISTINCT tag FROM doc_tags WHERE user_id=? ORDER BY tag",
        (user_id,)
    ).fetchall()
    c.close()
    return [r["tag"] for r in rows]


def get_docs_by_tag(user_id: int, tag: str) -> List[str]:
    """Return document names that match the given tag (partial match)."""
    if not user_id or not tag:
        return []
    c = _conn()
    rows = c.execute(
        "SELECT DISTINCT doc_name FROM doc_tags WHERE user_id=? AND tag LIKE ?",
        (user_id, f"%{tag}%")
    ).fetchall()
    c.close()
    return [r["doc_name"] for r in rows]


# ── Semantic search ───────────────────────────────────────────────────────────

def smart_search(
    vector_store,
    query: str,
    k: int = 8,
    tag_filter: Optional[str] = None,
    user_id: Optional[int] = None,
) -> List[Dict]:
    """
    Semantic search across indexed documents.
    Optionally filter results to docs that have a specific tag.
    Called from app/pages/10_multi_doc.py.
    """
    if vector_store is None:
        return []

    try:
        from core.retriever import retrieve
        docs = retrieve(vector_store, query, k=k * 2)
    except Exception as e:
        print(f"[search] Retrieval failed: {e}")
        return []

    # Apply tag filter
    tagged_docs: Optional[List[str]] = None
    if tag_filter and user_id:
        tagged_docs = get_docs_by_tag(user_id, tag_filter)

    results = []
    for doc in docs:
        source = doc.metadata.get("source", "")

        if tagged_docs is not None:
            # Check if source matches any tagged document
            matches = any(td in source or source in td for td in tagged_docs)
            if not matches:
                continue

        results.append({
            "content": doc.page_content,
            "source":  source,
            "page":    doc.metadata.get("page"),
            "score":   doc.metadata.get("similarity_score", 0),
        })

        if len(results) >= k:
            break

    return results