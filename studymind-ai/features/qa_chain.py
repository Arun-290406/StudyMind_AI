# features/qa_chain.py
"""
Q&A chain with RAG retrieval + citation grounding — FIXED version.

Changes:
1. answer_question() catches ValueError from retriever (dimension mismatch)
   and returns a user-friendly message with instructions.
2. stream_answer() handles errors the same way.
3. Added a "no context" guard that returns a helpful message instead of
   sending an empty context to the LLM.
"""

from typing import Dict, List, Generator

from langchain.schema import Document
from core.llm import simple_chat, stream_chat
from core.retriever import retrieve, build_context_string, extract_citations


QA_SYSTEM = """You are StudyMind, an expert AI study assistant.
Answer questions ONLY using the provided context from the student's uploaded notes.

Rules:
1. Base every answer strictly on the given context — do not use outside knowledge.
2. If the answer is not in the context, say: "I couldn't find this in your notes."
3. Be clear, concise, and educational. Use bullet points for multi-part answers.
4. Reference the source document and page number after your answer when available.
5. Explain concepts at an undergraduate level unless told otherwise.
"""


def answer_question(
    vector_store,
    question: str,
    k: int = 5,
    chat_history: List[Dict] = None,
) -> Dict:
    """
    Answer using RAG. Returns {answer, citations, context_docs}.
    Never raises — all errors become user-visible messages.
    """
    # 1. Retrieve
    try:
        docs = retrieve(vector_store, question, k=k)
    except ValueError as e:
        return {
            "answer": (
                f"⚠️ **Index error:** {e}\n\n"
                "**How to fix:** Go to the **Ask Notes** page, click **Clear All**, "
                "then re-upload and re-index your documents."
            ),
            "citations": [],
            "context_docs": [],
        }
    except Exception as e:
        return {
            "answer": f"⚠️ Retrieval error: {e}",
            "citations": [],
            "context_docs": [],
        }

    if not docs:
        return {
            "answer": (
                "I couldn't find relevant information in your uploaded notes. "
                "Try rephrasing your question, or upload more detailed documents."
            ),
            "citations": [],
            "context_docs": [],
        }

    # 2. Build prompt
    context     = build_context_string(docs)
    history_str = _format_history(chat_history or [])
    prompt      = f"""Context from student's notes:\n{context}\n\n{history_str}Question: {question}\n\nAnswer:"""

    # 3. Call LLM
    answer = simple_chat(prompt, system=QA_SYSTEM, temperature=0.1)

    return {
        "answer":       answer,
        "citations":    extract_citations(docs),
        "context_docs": docs,
    }


def stream_answer(
    vector_store,
    question: str,
    k: int = 5,
    chat_history: List[Dict] = None,
) -> Generator:
    """Streaming version — yields tokens then a final metadata dict."""
    try:
        docs = retrieve(vector_store, question, k=k)
    except ValueError as e:
        yield (
            f"⚠️ **Index mismatch:** {e}\n\n"
            "Please clear the index (Ask Notes → Clear All) and re-upload your documents."
        )
        return
    except Exception as e:
        yield f"⚠️ Retrieval error: {e}"
        return

    if not docs:
        yield "I couldn't find relevant information in your uploaded notes."
        return

    context     = build_context_string(docs)
    history_str = _format_history(chat_history or [])
    citations   = extract_citations(docs)
    prompt      = f"Context from student's notes:\n{context}\n\n{history_str}Question: {question}\n\nAnswer:"

    for token in stream_chat(prompt, system=QA_SYSTEM, temperature=0.1):
        yield token

    yield {"__citations__": citations, "__docs__": len(docs)}


def explain_concept(vector_store, concept: str) -> Dict:
    """Detailed concept explanation with analogy."""
    q = (
        f"Explain '{concept}' in detail. "
        "Include: definition, key points, and a simple analogy."
    )
    return answer_question(vector_store, q, k=6)


def _format_history(history: List[Dict], max_turns: int = 4) -> str:
    if not history:
        return ""
    recent = history[-(max_turns * 2):]
    lines  = ["Previous conversation:"]
    for msg in recent:
        role = "Student" if msg["role"] == "user" else "StudyMind"
        lines.append(f"{role}: {msg['content'][:300]}")
    return "\n".join(lines) + "\n\n"