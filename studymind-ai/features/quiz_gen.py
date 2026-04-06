# features/quiz_gen.py
"""
Smart Quiz Generator.
EXAM_CONFIGS is defined at module level so it can be imported anywhere.
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from core.llm import simple_chat
from core.retriever import retrieve, build_context_string
from utils.formatters import parse_quiz_questions


# ── EXAM_CONFIGS — defined at module level, importable from anywhere ──────────
EXAM_CONFIGS = {
    "practice": {
        "label":          "Practice Mode",
        "time_per_q":     0,
        "negative_marks": 0.0,
        "show_hints":     True,
        "show_answer_now":True,
        "icon":           "📝",
    },
    "exam": {
        "label":          "Exam Mode",
        "time_per_q":     90,
        "negative_marks": 0.25,
        "show_hints":     False,
        "show_answer_now":False,
        "icon":           "🔥",
    },
    "speed": {
        "label":          "Speed Round",
        "time_per_q":     30,
        "negative_marks": 0.0,
        "show_hints":     False,
        "show_answer_now":False,
        "icon":           "⚡",
    },
    "mock": {
        "label":          "Mock Test",
        "time_per_q":     60,
        "negative_marks": 0.33,
        "show_hints":     False,
        "show_answer_now":False,
        "icon":           "📊",
    },
}


# ── Prompts ───────────────────────────────────────────────────────────────────

MCQ_SYSTEM = """You are an expert educator creating multiple-choice exam questions.
Test conceptual understanding, not rote memorisation.
Make distractors plausible but clearly wrong upon reflection.
"""

MCQ_PROMPT = """Create {num_questions} multiple-choice questions from these notes.
Difficulty: {difficulty}

Notes:
{context}

Use EXACTLY this format for each question:
Q1: <question text>
A) <option>
B) <option>
C) <option>
D) <option>
ANSWER: <correct letter>
EXPLANATION: <why this answer is correct>
TOPIC: <topic name>
---

Generate {num_questions} questions now:"""


# ── MCQ Generation ────────────────────────────────────────────────────────────

def generate_mcq_quiz(
    vector_store,
    topic: str = "",
    num_questions: int = 5,
    difficulty: str = "medium",
) -> List[Dict]:
    """
    Generate MCQ questions from the indexed documents.
    Returns list of question dicts. Empty list on failure.
    """
    if vector_store is None:
        return []

    query   = topic if topic else "important concepts definitions principles"
    try:
        docs = retrieve(vector_store, query, k=8)
    except Exception as e:
        print(f"[quiz_gen] Retrieval failed: {e}")
        return []

    if not docs:
        return []

    context = build_context_string(docs, max_chars=5000)
    prompt  = MCQ_PROMPT.format(
        num_questions=num_questions,
        difficulty=difficulty,
        context=context,
    )

    try:
        raw       = simple_chat(prompt, system=MCQ_SYSTEM, temperature=0.6)
        questions = parse_quiz_questions(raw)
    except Exception as e:
        print(f"[quiz_gen] LLM failed: {e}")
        return []

    for i, q in enumerate(questions):
        q["type"]       = "mcq"
        q["difficulty"] = difficulty
        q["index"]      = i
        # Ensure id exists
        if "id" not in q:
            q["id"] = f"q_{i}"

    return questions


# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate_mcq(
    questions: List[Dict],
    answers: Dict[str, str],
    mode: str = "practice",
) -> Dict:
    """
    Score the quiz.
    answers = {question_id: chosen_letter}
    Returns full result dict with per-question breakdown.
    """
    config    = EXAM_CONFIGS.get(mode, EXAM_CONFIGS["practice"])
    neg       = config["negative_marks"]
    results   = []
    raw_score = 0.0

    for q in questions:
        qid     = q.get("id", "")
        chosen  = str(answers.get(qid, "")).strip().upper()
        correct = str(q.get("correct", "")).strip().upper()
        skipped = not bool(chosen)
        is_ok   = (chosen == correct) and not skipped

        if is_ok:
            pts = 1.0
        elif skipped:
            pts = 0.0
        else:
            pts = -neg

        raw_score += pts
        results.append({
            "question":    q.get("question", ""),
            "options":     q.get("options", {}),
            "chosen":      chosen,
            "correct":     correct,
            "is_correct":  is_ok,
            "skipped":     skipped,
            "points":      pts,
            "explanation": q.get("explanation", ""),
            "topic":       q.get("topic", ""),
        })

    total   = len(questions)
    max_pts = float(total)
    pct     = max(0.0, round(raw_score / max_pts * 100, 1)) if max_pts else 0.0
    correct = sum(1 for r in results if r["is_correct"])
    wrong   = sum(1 for r in results if not r["is_correct"] and not r["skipped"])
    skipped = sum(1 for r in results if r["skipped"])
    weak    = list({r["topic"] for r in results if not r["is_correct"] and r.get("topic")})

    return {
        "score_pct":   pct,
        "raw_score":   round(raw_score, 2),
        "max_score":   max_pts,
        "correct":     correct,
        "wrong":       wrong,
        "skipped":     skipped,
        "total":       total,
        "results":     results,
        "weak_topics": weak,
        "mode":        mode,
        "neg_marking": neg,
    }


# ── Short-answer evaluation ────────────────────────────────────────────────────

def evaluate_short_answer(q: str, correct: str, student: str) -> Dict:
    if not student.strip():
        return {"score": 0, "feedback": "No answer provided.", "correct": "no"}
    prompt = (
        f"Question: {q}\n"
        f"Correct Answer: {correct}\n"
        f"Student Answer: {student}\n\n"
        "Evaluate the student answer.\n"
        "SCORE: <0-100>\n"
        "FEEDBACK: <1-2 sentences>\n"
        "CORRECT: yes|partial|no"
    )
    raw   = simple_chat(prompt, temperature=0.1)
    s_m   = re.search(r"SCORE:\s*(\d+)", raw)
    fb_m  = re.search(r"FEEDBACK:\s*(.+)", raw)
    cor_m = re.search(r"CORRECT:\s*(\w+)", raw)
    return {
        "score":    int(s_m.group(1))    if s_m   else 50,
        "feedback": fb_m.group(1).strip()  if fb_m  else "Good attempt.",
        "correct":  cor_m.group(1).lower() if cor_m else "partial",
    }


# ── History stats ─────────────────────────────────────────────────────────────

def quiz_history_stats(history: List[Dict]) -> Dict:
    """Summarise a list of quiz history dicts."""
    if not history:
        return {"attempts": 0, "avg_score": 0, "best": 0, "worst": 0, "trend": "neutral"}
    scores = [h.get("score", 0) for h in history]
    trend  = (
        "improving" if len(scores) > 1 and scores[-1] > scores[-2] else
        "declining" if len(scores) > 1 and scores[-1] < scores[-2] else
        "stable"
    )
    return {
        "attempts":  len(history),
        "avg_score": round(sum(scores) / len(scores), 1),
        "best":      max(scores),
        "worst":     min(scores),
        "trend":     trend,
    }