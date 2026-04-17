# core/ingestion.py
"""
Document ingestion pipeline.
Loads raw files, splits them into chunks, and attaches metadata.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


from utils.file_handler import extract_text

load_dotenv()

CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))


# ── Text splitter ─────────────────────────────────────────────────────────────

def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Return a configured text splitter."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


# ── Single file ingestion ─────────────────────────────────────────────────────

def ingest_file(file_path: str) -> List[Document]:
    """
    Load a single file and return a list of LangChain Documents (chunks).
    Each Document carries metadata: source, page (if PDF), chunk_index.
    """
    file_data = extract_text(file_path)
    source_name = Path(file_path).name
    splitter = get_text_splitter()
    docs: List[Document] = []

    # If we have per-page data (PDF), keep page numbers in metadata
    if "pages" in file_data:
        for page_info in file_data["pages"]:
            page_text = page_info.get("text", "").strip()
            if not page_text:
                continue
            chunks = splitter.split_text(page_text)
            for i, chunk in enumerate(chunks):
                docs.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": source_name,
                        "file_path": file_path,
                        "page": page_info.get("page", 1),
                        "chunk_index": i,
                    }
                ))
    else:
        # Plain text / DOCX — split full text
        chunks = splitter.split_text(file_data["text"])
        for i, chunk in enumerate(chunks):
            docs.append(Document(
                page_content=chunk,
                metadata={
                    "source": source_name,
                    "file_path": file_path,
                    "page": None,
                    "chunk_index": i,
                }
            ))

    return docs


# ── Multi-file ingestion ──────────────────────────────────────────────────────

def ingest_files(file_paths: List[str], progress_callback=None) -> List[Document]:
    """
    Ingest multiple files.
    Optional progress_callback(current: int, total: int, filename: str).
    Returns a flat list of all Documents.
    """
    all_docs = []
    total = len(file_paths)

    for i, path in enumerate(file_paths, start=1):
        if progress_callback:
            progress_callback(i, total, Path(path).name)
        try:
            docs = ingest_file(path)
            all_docs.extend(docs)
        except Exception as e:
            print(f"[ingestion] Failed to ingest {path}: {e}")

    return all_docs


# ── Metadata helpers ──────────────────────────────────────────────────────────

def get_unique_sources(docs: List[Document]) -> List[str]:
    """Return sorted list of unique source filenames from a document list."""
    return sorted({d.metadata.get("source", "unknown") for d in docs})


def filter_docs_by_source(docs: List[Document], source: str) -> List[Document]:
    """Filter documents to only those from a given source filename."""
    return [d for d in docs if d.metadata.get("source") == source]


def docs_summary(docs: List[Document]) -> Dict:
    """Return a stats dict for a list of documents."""
    sources = get_unique_sources(docs)
    return {
        "total_chunks": len(docs),
        "total_sources": len(sources),
        "sources": sources,
        "avg_chunk_length": (
            round(sum(len(d.page_content) for d in docs) / len(docs))
            if docs else 0
        ),
    }