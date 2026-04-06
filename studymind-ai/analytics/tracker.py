# analytics/tracker.py
"""
Analytics tracker — SQLite-backed study event persistence.
ALL functions used across the project are defined here.

Functions:
  start_session()         - called in main.py on login
  end_session()           - called in main.py on logout
  log_topic()             - called when topics are covered
  log_weak_area()         - called after quiz results
  log_flashcard_review()  - called from flashcard page
  get_dashboard_summary() - called from dashboard page
  get_study_time_by_day() - Plotly chart data
  get_quiz_accuracy_by_topic() - Plotly chart data
  get_weak_areas()        - weak area list
  get_topics_covered()    - topic chips
  get_flashcard_stats()   - donut chart data
"""

import os
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "./data/db/studymind.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_analytics_tables() -> None:
    """Create all analytics tables. Safe to call on every startup."""
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            subject      TEXT    DEFAULT '',
            duration_min REAL    NOT NULL DEFAULT 0,
            started_at   TEXT    NOT NULL,
            ended_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS topic_coverage (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            topic       TEXT    NOT NULL,
            source_doc  TEXT    DEFAULT '',
            covered_at  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS weak_areas (
            user_id     INTEGER NOT NULL,
            topic       TEXT    NOT NULL,
            miss_count  INTEGER NOT NULL DEFAULT 1,
            last_missed TEXT    NOT NULL,
            PRIMARY KEY (user_id, topic)
        );

        CREATE TABLE IF NOT EXISTS flashcard_reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            card_id     TEXT    NOT NULL,
            rating      INTEGER NOT NULL,
            reviewed_at TEXT    NOT NULL
        );
    """)
    c.commit()
    c.close()


# Auto-initialise when module is imported
init_analytics_tables()


# ── Session tracking ──────────────────────────────────────────────────────────

def start_session(user_id: int, subject: str = "") -> int:
    """
    Record the start of a study session.
    Returns the new session_id (store in st.session_state).
    Called from app/main.py on login.
    """
    if not user_id:
        return 0
    c = _conn()
    cur = c.execute(
        "INSERT INTO study_sessions (user_id, subject, started_at) VALUES (?, ?, ?)",
        (user_id, subject or "", datetime.utcnow().isoformat())
    )
    c.commit()
    sid = cur.lastrowid
    c.close()
    return sid


def end_session(session_id: int, duration_min: float) -> None:
    """
    Update a session record with its duration.
    Called from app/main.py on logout.
    """
    if not session_id:
        return
    c = _conn()
    c.execute(
        "UPDATE study_sessions SET ended_at=?, duration_min=? WHERE id=?",
        (datetime.utcnow().isoformat(), round(max(0.0, duration_min), 2), session_id)
    )
    c.commit()
    c.close()


def log_topic(user_id: int, topic: str, source_doc: str = "") -> None:
    """Record that a topic was covered."""
    if not user_id or not topic:
        return
    c = _conn()
    c.execute(
        "INSERT INTO topic_coverage (user_id, topic, source_doc, covered_at) VALUES (?,?,?,?)",
        (user_id, topic.strip(), source_doc, datetime.utcnow().isoformat())
    )
    c.commit()
    c.close()


def log_weak_area(user_id: int, topic: str) -> None:
    """
    Upsert a weak area — increment miss_count if already exists.
    Called from quiz pages after evaluating results.
    """
    if not user_id or not topic:
        return
    c = _conn()
    c.execute("""
        INSERT INTO weak_areas (user_id, topic, miss_count, last_missed)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(user_id, topic) DO UPDATE SET
            miss_count  = miss_count + 1,
            last_missed = excluded.last_missed
    """, (user_id, topic.strip(), datetime.utcnow().isoformat()))
    c.commit()
    c.close()


def log_flashcard_review(user_id: int, card_id: str, rating: int) -> None:
    """Record a flashcard review with its quality rating (0–5)."""
    if not user_id:
        return
    c = _conn()
    c.execute(
        "INSERT INTO flashcard_reviews (user_id, card_id, rating, reviewed_at) VALUES (?,?,?,?)",
        (user_id, card_id, int(rating), datetime.utcnow().isoformat())
    )
    c.commit()
    c.close()


# ── Dashboard summary ─────────────────────────────────────────────────────────

def get_dashboard_summary(user_id: int) -> Dict:
    """
    Return aggregated stats for the dashboard KPI cards.
    Called from app/pages/07_dashboard.py.
    """
    if not user_id:
        return {
            "total_study_min": 0, "total_quizzes": 0,
            "avg_score": 0, "topics_covered": 0, "streak_days": 0,
        }
    c = _conn()
    total_time = c.execute(
        "SELECT COALESCE(SUM(duration_min), 0) FROM study_sessions WHERE user_id=?",
        (user_id,)
    ).fetchone()[0]

    total_quizzes = c.execute(
        "SELECT COUNT(*) FROM quiz_history WHERE user_id=?", (user_id,)
    ).fetchone()[0]

    avg_score = c.execute(
        "SELECT COALESCE(AVG(score), 0) FROM quiz_history WHERE user_id=?", (user_id,)
    ).fetchone()[0]

    total_topics = c.execute(
        "SELECT COUNT(DISTINCT topic) FROM topic_coverage WHERE user_id=?", (user_id,)
    ).fetchone()[0]

    streak = _calc_streak(user_id, c)
    c.close()

    return {
        "total_study_min": round(float(total_time), 1),
        "total_quizzes":   int(total_quizzes),
        "avg_score":       round(float(avg_score), 1),
        "topics_covered":  int(total_topics),
        "streak_days":     streak,
    }


# ── Chart data ────────────────────────────────────────────────────────────────

def get_study_time_by_day(user_id: int, days: int = 14) -> List[Dict]:
    """Return list of {day, minutes} for the past N days."""
    if not user_id:
        return []
    since = (date.today() - timedelta(days=days)).isoformat()
    c = _conn()
    rows = c.execute("""
        SELECT DATE(started_at) AS day, SUM(duration_min) AS minutes
        FROM   study_sessions
        WHERE  user_id=? AND started_at >= ?
        GROUP  BY day
        ORDER  BY day
    """, (user_id, since)).fetchall()
    c.close()
    return [{"day": r["day"], "minutes": round(float(r["minutes"]), 1)} for r in rows]


def get_quiz_accuracy_by_topic(user_id: int) -> List[Dict]:
    """Return list of {topic, avg_score, attempts} ordered by score asc."""
    if not user_id:
        return []
    c = _conn()
    rows = c.execute("""
        SELECT topic, AVG(score) AS avg_score, COUNT(*) AS attempts
        FROM   quiz_history
        WHERE  user_id=? AND topic IS NOT NULL AND topic != ''
        GROUP  BY topic
        ORDER  BY avg_score ASC
    """, (user_id,)).fetchall()
    c.close()
    return [
        {"topic": r["topic"], "avg_score": round(float(r["avg_score"]), 1), "attempts": r["attempts"]}
        for r in rows
    ]


def get_weak_areas(user_id: int, limit: int = 8) -> List[Dict]:
    """Return the most-missed topics, descending by miss_count."""
    if not user_id:
        return []
    c = _conn()
    rows = c.execute("""
        SELECT topic, miss_count, last_missed
        FROM   weak_areas
        WHERE  user_id=?
        ORDER  BY miss_count DESC
        LIMIT  ?
    """, (user_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_topics_covered(user_id: int) -> List[str]:
    """Return distinct topics the user has studied."""
    if not user_id:
        return []
    c = _conn()
    rows = c.execute("""
        SELECT DISTINCT topic FROM topic_coverage
        WHERE user_id=? ORDER BY topic
    """, (user_id,)).fetchall()
    c.close()
    return [r["topic"] for r in rows]


def get_flashcard_stats(user_id: int) -> Dict:
    """Return flashcard review statistics for the donut chart."""
    if not user_id:
        return {"total_reviews": 0, "good_rate": 0, "by_rating": {}}
    c = _conn()
    rows = c.execute("""
        SELECT rating, COUNT(*) AS cnt
        FROM   flashcard_reviews
        WHERE  user_id=?
        GROUP  BY rating
    """, (user_id,)).fetchall()
    c.close()

    total = sum(r["cnt"] for r in rows)
    good  = sum(r["cnt"] for r in rows if r["rating"] >= 3)
    return {
        "total_reviews": total,
        "good_rate":     round(good / total * 100, 1) if total else 0,
        "by_rating":     {r["rating"]: r["cnt"] for r in rows},
    }


def get_quiz_history(user_id: int, limit: int = 20) -> List[Dict]:
    """Return recent quiz results for a user."""
    if not user_id:
        return []
    c = _conn()
    rows = c.execute(
        "SELECT * FROM quiz_history WHERE user_id=? ORDER BY taken_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def insert_quiz_result(user_id: int, topic: str, score: float, num_q: int) -> None:
    """Persist a quiz result. Called from quiz pages."""
    if not user_id:
        return
    c = _conn()
    c.execute(
        "INSERT INTO quiz_history (user_id, topic, score, num_questions, taken_at) VALUES (?,?,?,?,?)",
        (user_id, topic or "", round(score, 1), int(num_q), datetime.utcnow().isoformat())
    )
    c.commit()
    c.close()


# ── Streak helper ─────────────────────────────────────────────────────────────

def _calc_streak(user_id: int, c: sqlite3.Connection) -> int:
    """Calculate current consecutive study day streak."""
    rows = c.execute("""
        SELECT DISTINCT DATE(started_at) AS day
        FROM   study_sessions
        WHERE  user_id=?
        ORDER  BY day DESC
        LIMIT  60
    """, (user_id,)).fetchall()

    if not rows:
        return 0

    streak = 0
    today  = date.today()
    for i, row in enumerate(rows):
        try:
            d = date.fromisoformat(row["day"])
            if d == today - timedelta(days=i):
                streak += 1
            else:
                break
        except Exception:
            break
    return streak