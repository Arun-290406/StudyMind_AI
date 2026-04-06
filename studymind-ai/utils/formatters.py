# utils/formatters.py
"""
Output formatting helpers used across all pages.
Converts raw LLM outputs into structured Python objects and display-ready strings.
"""

import re
import json
from typing import List, Dict, Optional


# ── Flashcard parsing ─────────────────────────────────────────────────────────

def parse_flashcards(raw_text: str) -> List[Dict]:
    """
    Parse LLM-generated flashcard text into a list of dicts.
    Expected LLM format:
        Q: <question>
        A: <answer>
        DIFFICULTY: easy|medium|hard
        TOPIC: <topic>
        ---
    """
    cards = []
    blocks = raw_text.strip().split("---")

    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        q = _extract_field(block, "Q")
        a = _extract_field(block, "A")
        difficulty = _extract_field(block, "DIFFICULTY", default="medium").lower()
        topic = _extract_field(block, "TOPIC", default="General")

        if q and a:
            cards.append({
                "id": f"fc_{i}",
                "question": q,
                "answer": a,
                "difficulty": difficulty if difficulty in ("easy", "medium", "hard") else "medium",
                "topic": topic,
                "confidence": 0,      # SM-2 confidence rating (0-5)
                "interval": 1,        # days until next review
                "repetitions": 0,     # times reviewed
                "ease_factor": 2.5,   # SM-2 ease factor
                "next_review": None,  # datetime string
            })
    return cards


# ── Quiz parsing ──────────────────────────────────────────────────────────────

def parse_quiz_questions(raw_text: str) -> List[Dict]:
    """
    Parse LLM-generated quiz into a list of question dicts.
    Expected LLM format:
        Q1: <question text>
        A) <option>
        B) <option>
        C) <option>
        D) <option>
        ANSWER: B
        EXPLANATION: <explanation>
        ---
    """
    questions = []
    blocks = raw_text.strip().split("---")

    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        # Extract question text (first line or after Q#:)
        q_match = re.search(r"Q\d*[:.]\s*(.+)", block)
        question_text = q_match.group(1).strip() if q_match else ""

        # Extract options A-D
        options = {}
        for letter in ["A", "B", "C", "D"]:
            opt_match = re.search(rf"{letter}[).]\s*(.+)", block)
            if opt_match:
                options[letter] = opt_match.group(1).strip()

        answer = _extract_field(block, "ANSWER", default="A").strip().upper()
        explanation = _extract_field(block, "EXPLANATION", default="")

        if question_text and options:
            questions.append({
                "id": f"q_{i}",
                "question": question_text,
                "options": options,
                "correct": answer,
                "explanation": explanation,
                "topic": _extract_field(block, "TOPIC", default="General"),
            })
    return questions


# ── Study plan parsing ────────────────────────────────────────────────────────

def parse_study_plan(raw_text: str) -> List[Dict]:
    """
    Parse LLM-generated study plan into daily task dicts.
    Expected JSON array from LLM:
        [{"day": 1, "date": "Mon Jun 10", "topic": "...", "tasks": [...], "duration_min": 60}, ...]
    Falls back to line-by-line parsing.
    """
    # Try JSON first
    try:
        clean = raw_text.strip().strip("```json").strip("```").strip()
        plan = json.loads(clean)
        if isinstance(plan, list):
            return plan
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: simple line parser
    days = []
    for i, line in enumerate(raw_text.strip().splitlines()):
        line = line.strip()
        if line and not line.startswith("#"):
            days.append({
                "day": i + 1,
                "date": f"Day {i+1}",
                "topic": line,
                "tasks": [line],
                "duration_min": 60,
                "completed": False,
            })
    return days


# ── Mind map parsing ──────────────────────────────────────────────────────────

def parse_mind_map(raw_text: str) -> Dict:
    """
    Parse LLM mind map JSON into {nodes, edges}.
    Expected LLM JSON:
        {
          "nodes": [{"id": "n1", "label": "...", "group": "..."}],
          "edges": [{"from": "n1", "to": "n2", "label": "..."}]
        }
    """
    try:
        clean = raw_text.strip().strip("```json").strip("```").strip()
        data = json.loads(clean)
        return {
            "nodes": data.get("nodes", []),
            "edges": data.get("edges", []),
        }
    except (json.JSONDecodeError, ValueError):
        return {"nodes": [], "edges": []}


# ── Citation formatting ───────────────────────────────────────────────────────

def format_citations(citations: List[Dict]) -> str:
    """
    Format a list of citation dicts into a readable markdown string.
    Each citation: {source, page, snippet}
    """
    if not citations:
        return ""
    lines = ["\n\n**Sources:**"]
    for c in citations:
        source = c.get("source", "Unknown")
        page = c.get("page", "")
        page_str = f" · p.{page}" if page else ""
        lines.append(f"- 📄 `{source}`{page_str}")
    return "\n".join(lines)


def format_score_badge(score: float) -> str:
    """Return a colored label string for a quiz score percentage."""
    if score >= 80:
        return f"✅ {score:.0f}% — Excellent!"
    elif score >= 60:
        return f"🟡 {score:.0f}% — Good effort"
    else:
        return f"🔴 {score:.0f}% — Keep practising"


def format_file_size(size_bytes: int) -> str:
    """Human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024**2):.1f} MB"


def truncate(text: str, max_chars: int = 120) -> str:
    """Truncate a string with ellipsis."""
    return text if len(text) <= max_chars else text[:max_chars].rstrip() + "…"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_field(block: str, field: str, default: str = "") -> str:
    """Extract a named field value from a text block."""
    match = re.search(rf"^{field}[:.]\s*(.+)", block, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else default