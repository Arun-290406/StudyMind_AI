# features/study_planner.py
"""
AI-powered study plan generator.
Creates a personalized study schedule based on:
  - Exam date
  - Topics from uploaded notes
  - Student's weak areas (from quiz results)
  - Daily study availability
"""

import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

from core.llm import simple_chat
from core.retriever import retrieve, build_context_string
from utils.formatters import parse_study_plan


# ── Prompts ───────────────────────────────────────────────────────────────────

PLANNER_SYSTEM = """You are an expert academic coach creating personalized study plans.
Create realistic, achievable study schedules that balance depth with review.
Prioritize weak areas and ensure spaced repetition across the plan.
"""

PLANNER_PROMPT = """Create a detailed {num_days}-day study plan for a student preparing for an exam.

Subject material topics (from their notes):
{topics}

Student's weak areas (from quiz results):
{weak_areas}

Daily study time available: {daily_hours} hours
Exam date: {exam_date}
Days until exam: {days_until}

Output a JSON array ONLY. No extra text. Format:
[
  {{
    "day": 1,
    "date": "Mon Jun 10",
    "topic": "Topic name",
    "tasks": ["Task 1", "Task 2", "Task 3"],
    "duration_min": 90,
    "session_type": "learn|review|practice|mock_test",
    "priority": "high|medium|low",
    "completed": false
  }},
  ...
]

Ensure:
- Weak areas appear 2x more than strong topics
- Final 2 days = full review + mock test
- Daily duration matches {daily_hours} hours
- Mix session types across the week

JSON array:"""

TOPIC_EXTRACTOR_PROMPT = """Extract a list of main topics from the following study notes.
Return ONLY a JSON array of topic strings. No extra text.

Notes:
{context}

Example output: ["Neural Networks", "Backpropagation", "Loss Functions"]

Topics JSON:"""


# ── Plan generation ───────────────────────────────────────────────────────────

def generate_study_plan(
    vector_store,
    exam_date: date,
    daily_hours: float = 2.0,
    weak_topics: List[str] = None,
) -> List[Dict]:
    """
    Generate a study plan from now until exam_date.
    Returns list of day-plan dicts.
    """
    today         = date.today()
    days_until    = (exam_date - today).days
    num_days      = max(1, days_until)

    # Extract topics from notes
    topics = extract_topics_from_notes(vector_store)
    topics_str = "\n".join(f"- {t}" for t in topics) if topics else "General study material"

    # Weak areas
    weak_str = (
        "\n".join(f"- {t}" for t in weak_topics)
        if weak_topics else "None identified yet (take a quiz to find weak areas)"
    )

    prompt = PLANNER_PROMPT.format(
        num_days=min(num_days, 30),   # cap at 30-day plan
        topics=topics_str,
        weak_areas=weak_str,
        daily_hours=daily_hours,
        exam_date=exam_date.strftime("%B %d, %Y"),
        days_until=days_until,
    )

    raw  = simple_chat(prompt, system=PLANNER_SYSTEM, temperature=0.4)
    plan = parse_study_plan(raw)

    # Attach real dates
    for i, day in enumerate(plan):
        day_date = today + timedelta(days=i)
        day["real_date"] = day_date.isoformat()
        day["day"]       = i + 1

    return plan


def extract_topics_from_notes(vector_store, max_topics: int = 15) -> List[str]:
    """Extract main topics from indexed notes using the LLM."""
    docs    = retrieve(vector_store, "main topics overview key concepts", k=10)
    context = build_context_string(docs, max_chars=4000)

    prompt = TOPIC_EXTRACTOR_PROMPT.format(context=context)
    raw    = simple_chat(prompt, temperature=0.3)

    try:
        clean  = raw.strip().strip("```json").strip("```").strip()
        topics = json.loads(clean)
        if isinstance(topics, list):
            return topics[:max_topics]
    except Exception:
        pass

    # Fallback: split by newlines
    lines = [l.strip("- •").strip() for l in raw.splitlines() if l.strip()]
    return [l for l in lines if l][:max_topics]


# ── Plan management ───────────────────────────────────────────────────────────

def mark_day_complete(plan: List[Dict], day_number: int) -> List[Dict]:
    """Mark a day as completed and return the updated plan."""
    for day in plan:
        if day["day"] == day_number:
            day["completed"] = True
            day["completed_at"] = datetime.now().isoformat()
            break
    return plan


def get_today_plan(plan: List[Dict]) -> Optional[Dict]:
    """Return today's plan entry, or None if not found."""
    today = date.today().isoformat()
    for day in plan:
        if day.get("real_date") == today:
            return day
    # Fall back to first incomplete day
    for day in plan:
        if not day.get("completed"):
            return day
    return None


def plan_progress(plan: List[Dict]) -> Dict:
    """Return progress statistics for the study plan."""
    total     = len(plan)
    completed = sum(1 for d in plan if d.get("completed"))
    remaining = total - completed
    pct       = round(completed / total * 100) if total else 0

    return {
        "total_days":     total,
        "completed_days": completed,
        "remaining_days": remaining,
        "progress_pct":   pct,
        "on_track":       completed >= _expected_completed(plan),
    }


def _expected_completed(plan: List[Dict]) -> int:
    """How many days should be done by today."""
    today = date.today().isoformat()
    count = 0
    for day in plan:
        if day.get("real_date", "") <= today:
            count += 1
    return count