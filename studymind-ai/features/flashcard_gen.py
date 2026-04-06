# features/flashcard_gen.py
"""
Flashcard generation from notes + SM-2 spaced repetition scheduler.
Generates Q&A flashcards and manages review intervals based on user confidence.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from core.llm import simple_chat
from core.retriever import retrieve, build_context_string
from utils.formatters import parse_flashcards


# ── Prompts ───────────────────────────────────────────────────────────────────

FLASHCARD_SYSTEM = """You are an expert educator creating study flashcards.
Generate clear, concise flashcards from the provided study notes.
Each card should test one specific concept, fact, or definition.
"""

FLASHCARD_PROMPT = """Create {num_cards} flashcards from the following notes.

Notes:
{context}

For EACH flashcard use EXACTLY this format:
Q: <clear question>
A: <concise answer (1-3 sentences)>
DIFFICULTY: easy|medium|hard
TOPIC: <topic name>
---

Generate {num_cards} flashcards now:"""


# ── Generation ────────────────────────────────────────────────────────────────

def generate_flashcards(
    vector_store,
    topic: str = "",
    num_cards: int = 10,
    difficulty_filter: str = "all",
) -> List[Dict]:
    """
    Generate flashcards from indexed notes.
    topic: optional focus area (empty = all notes)
    num_cards: how many cards to generate
    difficulty_filter: "all" | "easy" | "medium" | "hard"
    Returns list of flashcard dicts.
    """
    query = topic if topic else "key concepts definitions important terms"
    docs  = retrieve(vector_store, query, k=8)
    context = build_context_string(docs, max_chars=5000)

    prompt = FLASHCARD_PROMPT.format(num_cards=num_cards, context=context)
    raw = simple_chat(prompt, system=FLASHCARD_SYSTEM, temperature=0.7)
    cards = parse_flashcards(raw)

    # Apply difficulty filter
    if difficulty_filter != "all":
        cards = [c for c in cards if c["difficulty"] == difficulty_filter]

    # Set initial SM-2 values
    now = datetime.now()
    for card in cards:
        card["next_review"] = now.isoformat()
        card["created_at"]  = now.isoformat()

    return cards


def generate_flashcards_from_text(text: str, num_cards: int = 10) -> List[Dict]:
    """Generate flashcards directly from a raw text string (no vector store needed)."""
    context = text[:5000]
    prompt  = FLASHCARD_PROMPT.format(num_cards=num_cards, context=context)
    raw     = simple_chat(prompt, system=FLASHCARD_SYSTEM, temperature=0.7)
    cards   = parse_flashcards(raw)
    now     = datetime.now()
    for card in cards:
        card["next_review"] = now.isoformat()
        card["created_at"]  = now.isoformat()
    return cards


# ── SM-2 Spaced Repetition ────────────────────────────────────────────────────

def update_card_sm2(card: Dict, rating: int) -> Dict:
    """
    Update a flashcard using the SM-2 algorithm.
    rating: 0=forgot, 1=hard, 2=ok, 3=easy, 4=very easy, 5=perfect

    Returns the updated card dict.
    """
    card = card.copy()

    # Quality threshold: below 3 resets
    if rating < 3:
        card["repetitions"] = 0
        card["interval"]    = 1
    else:
        if card["repetitions"] == 0:
            card["interval"] = 1
        elif card["repetitions"] == 1:
            card["interval"] = 6
        else:
            card["interval"] = round(card["interval"] * card["ease_factor"])

        card["repetitions"] += 1

    # Update ease factor (min 1.3)
    card["ease_factor"] = max(
        1.3,
        card["ease_factor"] + 0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02)
    )

    # Set next review date
    next_dt = datetime.now() + timedelta(days=card["interval"])
    card["next_review"] = next_dt.isoformat()
    card["confidence"]  = rating
    card["last_rated"]  = datetime.now().isoformat()

    return card


def get_due_cards(flashcards: List[Dict]) -> List[Dict]:
    """Return cards whose next_review date has passed (due today)."""
    now = datetime.now()
    due = []
    for card in flashcards:
        if card.get("next_review"):
            next_dt = datetime.fromisoformat(card["next_review"])
            if next_dt <= now:
                due.append(card)
        else:
            due.append(card)  # unreviewed card
    return due


def sort_cards_by_priority(flashcards: List[Dict]) -> List[Dict]:
    """Sort cards: due first, then by lowest confidence."""
    now = datetime.now()

    def priority(card):
        overdue_days = 0
        if card.get("next_review"):
            next_dt = datetime.fromisoformat(card["next_review"])
            overdue_days = max(0, (now - next_dt).days)
        confidence = card.get("confidence", 0)
        return (-overdue_days, confidence)

    return sorted(flashcards, key=priority)


def flashcard_stats(flashcards: List[Dict]) -> Dict:
    """Return summary statistics for a flashcard set."""
    if not flashcards:
        return {"total": 0, "due": 0, "easy": 0, "medium": 0, "hard": 0, "avg_confidence": 0}

    due   = len(get_due_cards(flashcards))
    easy  = sum(1 for c in flashcards if c.get("difficulty") == "easy")
    med   = sum(1 for c in flashcards if c.get("difficulty") == "medium")
    hard  = sum(1 for c in flashcards if c.get("difficulty") == "hard")
    avg_conf = sum(c.get("confidence", 0) for c in flashcards) / len(flashcards)

    return {
        "total": len(flashcards),
        "due": due,
        "easy": easy,
        "medium": med,
        "hard": hard,
        "avg_confidence": round(avg_conf, 1),
    }