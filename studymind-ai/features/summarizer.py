# features/summarizer.py
"""
Document summarization feature.
Generates chapter summaries, key-concept lists, and TL;DR overviews.
Uses map-reduce pattern for large documents.
"""

from typing import List, Dict, Optional

from core.llm import simple_chat
from core.retriever import retrieve, build_context_string
from utils.file_handler import extract_text


# ── Prompts ───────────────────────────────────────────────────────────────────

SUMMARY_SYSTEM = """You are an expert academic summarizer.
Create structured, comprehensive summaries that help students study effectively.
Use clear headings, bullet points, and highlight the most important concepts.
"""

FULL_SUMMARY_PROMPT = """Summarize the following study notes into a structured summary.

Notes:
{context}

Create a summary with these sections:
## Overview
(2-3 sentence high-level overview)

## Key Concepts
(bullet list of the most important concepts with brief explanations)

## Definitions
(important terms and their definitions)

## Key Takeaways
(3-5 most important points to remember)

## Possible Exam Topics
(likely exam questions based on this content)

Summary:"""

TLDR_PROMPT = """Summarize the following notes in 3-5 bullet points.
Each bullet should be one crisp sentence capturing a key idea.

Notes:
{context}

TL;DR:"""

TOPIC_SUMMARY_PROMPT = """Summarize everything in the notes about: {topic}

Notes:
{context}

Focus specifically on {topic}. Be concise but comprehensive.
Summary:"""

CHUNK_SUMMARY_PROMPT = """Summarize this section of study material in 2-3 sentences:

{text}

Summary:"""


# ── Full document summary ─────────────────────────────────────────────────────

def summarize_document(file_path: str, max_chars: int = 8000) -> Dict:
    """
    Summarize a document directly from its file path.
    Uses map-reduce for large docs.
    Returns {summary, tldr, key_concepts, source}.
    """
    import os
    data = extract_text(file_path)
    text = data["text"]
    source = os.path.basename(file_path)

    if len(text) > max_chars:
        summary = _map_reduce_summarize(text, max_chars)
    else:
        prompt  = FULL_SUMMARY_PROMPT.format(context=text[:max_chars])
        summary = simple_chat(prompt, system=SUMMARY_SYSTEM, temperature=0.3)

    tldr_prompt = TLDR_PROMPT.format(context=text[:3000])
    tldr        = simple_chat(tldr_prompt, temperature=0.3)

    return {
        "source":  source,
        "summary": summary,
        "tldr":    tldr,
        "word_count": len(text.split()),
    }


def summarize_from_query(vector_store, topic: str = "") -> Dict:
    """
    Summarize relevant notes for a given topic using RAG retrieval.
    """
    query = topic if topic else "main concepts key ideas overview"
    docs  = retrieve(vector_store, query, k=8)
    context = build_context_string(docs, max_chars=6000)

    prompt  = FULL_SUMMARY_PROMPT.format(context=context)
    summary = simple_chat(prompt, system=SUMMARY_SYSTEM, temperature=0.3)

    tldr_prompt = TLDR_PROMPT.format(context=context[:2000])
    tldr        = simple_chat(tldr_prompt, temperature=0.3)

    return {
        "topic":   topic or "All Notes",
        "summary": summary,
        "tldr":    tldr,
        "sources": list({d.metadata.get("source") for d in docs}),
    }


def summarize_topic(vector_store, topic: str) -> str:
    """Get a focused summary on a specific topic."""
    docs    = retrieve(vector_store, topic, k=6)
    context = build_context_string(docs, max_chars=4000)
    prompt  = TOPIC_SUMMARY_PROMPT.format(topic=topic, context=context)
    return simple_chat(prompt, system=SUMMARY_SYSTEM, temperature=0.3)


def get_tldr(vector_store) -> str:
    """Get a quick TL;DR summary of all indexed notes."""
    docs    = retrieve(vector_store, "overview main topics key points", k=10)
    context = build_context_string(docs, max_chars=3000)
    prompt  = TLDR_PROMPT.format(context=context)
    return simple_chat(prompt, temperature=0.4)


# ── Map-Reduce for large documents ────────────────────────────────────────────

def _map_reduce_summarize(text: str, chunk_size: int = 3000) -> str:
    """
    Map-reduce summarization for documents larger than the context window.
    Step 1 (Map): Summarize each chunk independently.
    Step 2 (Reduce): Combine chunk summaries into a final summary.
    """
    # Split into overlapping chunks
    chunks = []
    step   = chunk_size - 300  # small overlap
    for i in range(0, len(text), step):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)

    # Map: summarize each chunk
    chunk_summaries = []
    for chunk in chunks[:8]:  # cap at 8 chunks
        prompt = CHUNK_SUMMARY_PROMPT.format(text=chunk)
        summary = simple_chat(prompt, temperature=0.3)
        chunk_summaries.append(summary)

    # Reduce: combine all chunk summaries
    combined = "\n\n".join(chunk_summaries)
    final_prompt = FULL_SUMMARY_PROMPT.format(context=combined)
    return simple_chat(final_prompt, system=SUMMARY_SYSTEM, temperature=0.3)