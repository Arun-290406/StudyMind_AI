# features/new_features.py
"""
All 15 new features backend logic.
Import from this file in any page.
"""

import os
import io
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import mysql.connector
from mysql.connector import pooling

load_dotenv()

MYSQL_HOST     = os.getenv("MYSQL_HOST",     "localhost")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER",     "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Admin1234").strip('"').strip("'")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "studymind")

_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="features_pool", pool_size=5,
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE, autocommit=False,
            charset="utf8mb4", collation="utf8mb4_unicode_ci",
        )
    return _pool

def _get_conn():
    return _get_pool().get_connection()

def init_new_tables() -> None:
    """Create all new feature tables."""
    conn = mysql.connector.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE, charset="utf8mb4",
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            user_id      INT NOT NULL,
            type         VARCHAR(20) DEFAULT 'work',
            duration_min INT NOT NULL DEFAULT 25,
            completed    TINYINT NOT NULL DEFAULT 0,
            created_at   DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_notes (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT NOT NULL,
            doc_name   VARCHAR(255) DEFAULT '',
            title      VARCHAR(255) DEFAULT 'Untitled',
            content    TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS topic_completion (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            user_id      INT NOT NULL,
            topic        VARCHAR(255) NOT NULL,
            completed    TINYINT NOT NULL DEFAULT 0,
            completed_at DATETIME,
            UNIQUE KEY unique_user_topic (user_id, topic),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            user_id   INT NOT NULL,
            badge_id  VARCHAR(50) NOT NULL,
            earned_at DATETIME NOT NULL,
            UNIQUE KEY unique_user_badge (user_id, badge_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_challenges (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            user_id        INT NOT NULL,
            challenge_id   VARCHAR(50) NOT NULL,
            challenge_date DATE NOT NULL,
            completed      TINYINT NOT NULL DEFAULT 0,
            completed_at   DATETIME,
            UNIQUE KEY unique_user_date_challenge (user_id, challenge_id, challenge_date),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[features] New tables ready")

init_new_tables()


# ══════════════════════════════════════════════════════
# FEATURE 1 — POMODORO TIMER
# ══════════════════════════════════════════════════════

def log_pomodoro(user_id, ptype: str = "work", duration_min: int = 25, completed: bool = True) -> None:
    if not user_id:
        return
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO pomodoro_sessions (user_id, type, duration_min, completed, created_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (int(user_id), ptype, duration_min, 1 if completed else 0, datetime.utcnow())
        )
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass

def get_pomodoro_stats(user_id) -> Dict:
    if not user_id:
        return {"total_sessions": 0, "total_minutes": 0, "today_sessions": 0}
    try:
        conn  = _get_conn()
        cur   = conn.cursor(dictionary=True)
        uid   = int(user_id)
        today = date.today().strftime("%Y-%m-%d")
        cur.execute(
            "SELECT COUNT(*) as total, COALESCE(SUM(duration_min),0) as mins "
            "FROM pomodoro_sessions WHERE user_id=%s AND completed=1", (uid,)
        )
        row = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) as cnt FROM pomodoro_sessions "
            "WHERE user_id=%s AND completed=1 AND DATE(created_at)=%s",
            (uid, today)
        )
        today_row = cur.fetchone()
        cur.close()
        conn.close()
        return {
            "total_sessions": row["total"],
            "total_minutes":  int(row["mins"]),
            "today_sessions": today_row["cnt"],
        }
    except:
        return {"total_sessions": 0, "total_minutes": 0, "today_sessions": 0}


# ══════════════════════════════════════════════════════
# FEATURE 2 — NOTES
# ══════════════════════════════════════════════════════

def save_note(user_id, title: str, content: str, doc_name: str = "") -> int:
    if not user_id:
        return 0
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        now  = datetime.utcnow()
        cur.execute(
            "INSERT INTO user_notes (user_id, doc_name, title, content, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (int(user_id), doc_name, title, content, now, now)
        )
        conn.commit()
        nid = cur.lastrowid
        cur.close()
        conn.close()
        return nid
    except:
        return 0

def update_note(note_id: int, title: str, content: str) -> None:
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE user_notes SET title=%s, content=%s, updated_at=%s WHERE id=%s",
            (title, content, datetime.utcnow(), note_id)
        )
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass

def delete_note(note_id: int) -> None:
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("DELETE FROM user_notes WHERE id=%s", (note_id,))
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass

def get_notes(user_id, doc_name: str = "") -> List[Dict]:
    if not user_id:
        return []
    try:
        conn = _get_conn()
        cur  = conn.cursor(dictionary=True)
        if doc_name:
            cur.execute(
                "SELECT * FROM user_notes WHERE user_id=%s AND doc_name=%s ORDER BY updated_at DESC",
                (int(user_id), doc_name)
            )
        else:
            cur.execute(
                "SELECT * FROM user_notes WHERE user_id=%s ORDER BY updated_at DESC",
                (int(user_id),)
            )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except:
        return []


# ══════════════════════════════════════════════════════
# FEATURE 3 — STREAK CALENDAR DATA
# ══════════════════════════════════════════════════════

def get_streak_calendar(user_id, days: int = 90) -> Dict[str, int]:
    """Returns {date_str: minutes_studied} for heatmap."""
    if not user_id:
        return {}
    try:
        conn  = _get_conn()
        cur   = conn.cursor(dictionary=True)
        since = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        cur.execute(
            "SELECT DATE(started_at) as day, COALESCE(SUM(duration_min),0) as mins "
            "FROM study_sessions WHERE user_id=%s AND DATE(started_at)>=%s "
            "GROUP BY DATE(started_at)",
            (int(user_id), since)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {str(r["day"]): round(float(r["mins"]), 1) for r in rows}
    except:
        return {}


# ══════════════════════════════════════════════════════
# FEATURE 4 — QUIZ LEADERBOARD
# ══════════════════════════════════════════════════════

def get_quiz_leaderboard(user_id, limit: int = 10) -> List[Dict]:
    """Top scores per topic for this user."""
    if not user_id:
        return []
    try:
        conn = _get_conn()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT topic, MAX(score) as best_score, AVG(score) as avg_score, "
            "COUNT(*) as attempts, MAX(taken_at) as last_attempt "
            "FROM quiz_history WHERE user_id=%s AND topic IS NOT NULL AND topic!='' "
            "GROUP BY topic ORDER BY best_score DESC LIMIT %s",
            (int(user_id), limit)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{
            "topic":        r["topic"],
            "best_score":   round(float(r["best_score"]), 1),
            "avg_score":    round(float(r["avg_score"]), 1),
            "attempts":     r["attempts"],
            "last_attempt": str(r["last_attempt"])[:10] if r["last_attempt"] else "",
        } for r in rows]
    except:
        return []


# ══════════════════════════════════════════════════════
# FEATURE 5 — FLASHCARD PDF EXPORT
# ══════════════════════════════════════════════════════

def export_flashcards_pdf(flashcards: List[Dict], title: str = "My Flashcards") -> bytes:
    """Generate PDF from flashcard list. Returns bytes."""
    try:
        from fpdf import FPDF
        import re

        def clean(text: str) -> str:
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', str(text))
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            text = text.replace('•', '-').replace('–', '-').replace('—', '-')
            return text.encode('latin-1', 'replace').decode('latin-1')

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_fill_color(124, 58, 237)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 14, clean(title), ln=True, fill=True, align="C")
        pdf.ln(6)

        for i, card in enumerate(flashcards, 1):
            q = clean(card.get("question", card.get("front", "")))
            a = clean(card.get("answer", card.get("back", "")))

            # Card number
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(124, 58, 237)
            pdf.cell(0, 6, f"Card {i}", ln=True)

            # Question box
            pdf.set_fill_color(240, 235, 255)
            pdf.set_text_color(30, 30, 30)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 7, f"Q: {q}", fill=True, border=1)
            pdf.ln(1)

            # Answer box
            pdf.set_fill_color(235, 255, 245)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, f"A: {a}", fill=True, border=1)
            pdf.ln(4)

        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 6, f"Generated by StudyMind AI Pro — {date.today()}", align="C")

        return pdf.output(dest="S").encode("latin-1")
    except Exception as e:
        return b""


# ══════════════════════════════════════════════════════
# FEATURE 9 — MULTI-LANGUAGE TRANSLATION
# ══════════════════════════════════════════════════════

def translate_text(text: str, target_lang: str = "Tamil") -> str:
    """Translate text using GPT-4o-mini."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Translate the following text to {target_lang}. Return only the translation, nothing else:\n\n{text}"
            }],
            max_tokens=2000,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Translation failed: {e}"


# ══════════════════════════════════════════════════════
# FEATURE 10 — ESSAY EVALUATOR
# ══════════════════════════════════════════════════════

def evaluate_essay(essay: str, question: str, context: str = "") -> Dict:
    """Grade a long-form answer against context/notes."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        system = """You are an expert academic evaluator. Grade the student's answer strictly.
Return a JSON object with these exact keys:
- score: integer 0-100
- grade: string (A/B/C/D/F)
- strengths: list of 2-3 string bullet points
- improvements: list of 2-3 string bullet points  
- feedback: string (2-3 sentences overall feedback)
- missing_points: list of key points the student missed"""

        user_msg = f"""Question: {question}

Reference Notes/Context:
{context[:3000] if context else 'No specific notes provided — evaluate based on general knowledge.'}

Student Answer:
{essay}

Grade this answer and return JSON only."""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_msg}
            ],
            max_tokens=1000,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "score": 0, "grade": "N/A",
            "strengths": [], "improvements": [],
            "feedback": f"Evaluation failed: {e}",
            "missing_points": []
        }


# ══════════════════════════════════════════════════════
# FEATURE 12 — TOPIC COMPLETION TRACKER
# ══════════════════════════════════════════════════════

def get_topic_completion(user_id) -> List[Dict]:
    if not user_id:
        return []
    try:
        conn = _get_conn()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT topic, completed, completed_at FROM topic_completion "
            "WHERE user_id=%s ORDER BY topic",
            (int(user_id),)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except:
        return []

def set_topic_completed(user_id, topic: str, completed: bool = True) -> None:
    if not user_id or not topic:
        return
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO topic_completion (user_id, topic, completed, completed_at) "
            "VALUES (%s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE completed=%s, completed_at=%s",
            (int(user_id), topic, 1 if completed else 0,
             datetime.utcnow() if completed else None,
             1 if completed else 0,
             datetime.utcnow() if completed else None)
        )
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass

def add_topics_from_notes(user_id, topics: List[str]) -> None:
    """Add topics to completion tracker without marking complete."""
    if not user_id:
        return
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        for topic in topics:
            cur.execute(
                "INSERT IGNORE INTO topic_completion (user_id, topic, completed) "
                "VALUES (%s, %s, 0)",
                (int(user_id), topic.strip())
            )
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass


# ══════════════════════════════════════════════════════
# FEATURE 13 — CONFIDENCE SCORE
# ══════════════════════════════════════════════════════

def get_confidence_scores(user_id) -> List[Dict]:
    """Get confidence score per topic based on recent quiz performance."""
    if not user_id:
        return []
    try:
        conn = _get_conn()
        cur  = conn.cursor(dictionary=True)
        # Weight recent scores more heavily
        cur.execute(
            "SELECT topic, AVG(score) as avg_score, COUNT(*) as attempts, "
            "MAX(score) as best_score "
            "FROM quiz_history WHERE user_id=%s "
            "AND topic IS NOT NULL AND topic!='' "
            "GROUP BY topic ORDER BY avg_score DESC",
            (int(user_id),)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        result = []
        for r in rows:
            avg  = float(r["avg_score"])
            best = float(r["best_score"])
            # Confidence = weighted blend of avg and best
            confidence = round((avg * 0.7) + (best * 0.3), 1)
            result.append({
                "topic":      r["topic"],
                "confidence": min(100, confidence),
                "avg_score":  round(avg, 1),
                "best_score": round(best, 1),
                "attempts":   r["attempts"],
                "level":      "High" if confidence >= 75 else "Medium" if confidence >= 50 else "Low",
            })
        return result
    except:
        return []


# ══════════════════════════════════════════════════════
# FEATURE 14 — BADGES SYSTEM
# ══════════════════════════════════════════════════════

BADGES = {
    "first_quiz":       {"name": "First Quiz",       "icon": "🎯", "desc": "Completed your first quiz"},
    "quiz_master":      {"name": "Quiz Master",       "icon": "🏆", "desc": "Completed 10 quizzes"},
    "perfect_score":    {"name": "Perfect Score",     "icon": "💯", "desc": "Scored 100% on a quiz"},
    "streak_3":         {"name": "3-Day Streak",      "icon": "🔥", "desc": "Studied 3 days in a row"},
    "streak_7":         {"name": "7-Day Streak",      "icon": "⚡", "desc": "Studied 7 days in a row"},
    "streak_30":        {"name": "30-Day Streak",     "icon": "🌟", "desc": "Studied 30 days in a row"},
    "flashcard_100":    {"name": "Card Collector",    "icon": "🃏", "desc": "Reviewed 100 flashcards"},
    "early_bird":       {"name": "Early Bird",        "icon": "🌅", "desc": "Studied before 8 AM"},
    "night_owl":        {"name": "Night Owl",         "icon": "🦉", "desc": "Studied after 10 PM"},
    "note_taker":       {"name": "Note Taker",        "icon": "📝", "desc": "Created 5 notes"},
    "pomodoro_10":      {"name": "Focus Master",      "icon": "🍅", "desc": "Completed 10 Pomodoros"},
    "topic_master":     {"name": "Topic Master",      "icon": "📚", "desc": "Mastered 5 topics (75%+)"},
    "speed_learner":    {"name": "Speed Learner",     "icon": "⚡", "desc": "Completed Speed Round quiz"},
    "multilingual":     {"name": "Multilingual",      "icon": "🌐", "desc": "Used translation feature"},
    "essay_ace":        {"name": "Essay Ace",         "icon": "✍️",  "desc": "Scored A on Essay Evaluator"},
}

def get_user_badges(user_id) -> List[Dict]:
    if not user_id:
        return []
    try:
        conn = _get_conn()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT badge_id, earned_at FROM user_badges WHERE user_id=%s ORDER BY earned_at DESC",
            (int(user_id),)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        result = []
        for r in rows:
            badge_info = BADGES.get(r["badge_id"], {})
            result.append({
                "badge_id":  r["badge_id"],
                "name":      badge_info.get("name", r["badge_id"]),
                "icon":      badge_info.get("icon", "🏅"),
                "desc":      badge_info.get("desc", ""),
                "earned_at": str(r["earned_at"])[:10],
            })
        return result
    except:
        return []

def award_badge(user_id, badge_id: str) -> bool:
    """Award a badge. Returns True if newly awarded, False if already had it."""
    if not user_id or badge_id not in BADGES:
        return False
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT IGNORE INTO user_badges (user_id, badge_id, earned_at) "
            "VALUES (%s, %s, %s)",
            (int(user_id), badge_id, datetime.utcnow())
        )
        conn.commit()
        new = cur.rowcount > 0
        cur.close()
        conn.close()
        return new
    except:
        return False

def check_and_award_badges(user_id) -> List[Dict]:
    """Check all badge conditions and award new ones. Returns list of newly earned badges."""
    if not user_id:
        return []
    newly_earned = []
    try:
        conn = _get_conn()
        cur  = conn.cursor(dictionary=True)
        uid  = int(user_id)

        # Already earned
        cur.execute("SELECT badge_id FROM user_badges WHERE user_id=%s", (uid,))
        earned = {r["badge_id"] for r in cur.fetchall()}

        # Quiz count
        cur.execute("SELECT COUNT(*) as cnt, MAX(score) as best FROM quiz_history WHERE user_id=%s", (uid,))
        qrow = cur.fetchone()
        quiz_count = qrow["cnt"]
        best_score = float(qrow["best"] or 0)

        if quiz_count >= 1  and "first_quiz"    not in earned: newly_earned.append("first_quiz")
        if quiz_count >= 10 and "quiz_master"   not in earned: newly_earned.append("quiz_master")
        if best_score >= 100 and "perfect_score" not in earned: newly_earned.append("perfect_score")

        # Streak
        cur.execute(
            "SELECT DISTINCT DATE(started_at) as day FROM study_sessions "
            "WHERE user_id=%s ORDER BY day DESC LIMIT 30", (uid,)
        )
        days = [r["day"] for r in cur.fetchall()]
        streak = 0
        today  = date.today()
        for i, d in enumerate(days):
            if d == today - timedelta(days=i):
                streak += 1
            else:
                break
        if streak >= 3  and "streak_3"  not in earned: newly_earned.append("streak_3")
        if streak >= 7  and "streak_7"  not in earned: newly_earned.append("streak_7")
        if streak >= 30 and "streak_30" not in earned: newly_earned.append("streak_30")

        # Flashcards
        cur.execute(
            "SELECT COUNT(*) as cnt FROM analytics_events "
            "WHERE user_id=%s AND event_type='flashcard'", (uid,)
        )
        cards = cur.fetchone()["cnt"]
        if cards >= 100 and "flashcard_100" not in earned: newly_earned.append("flashcard_100")

        # Notes
        cur.execute("SELECT COUNT(*) as cnt FROM user_notes WHERE user_id=%s", (uid,))
        notes = cur.fetchone()["cnt"]
        if notes >= 5 and "note_taker" not in earned: newly_earned.append("note_taker")

        # Pomodoro
        cur.execute(
            "SELECT COUNT(*) as cnt FROM pomodoro_sessions "
            "WHERE user_id=%s AND completed=1", (uid,)
        )
        pomos = cur.fetchone()["cnt"]
        if pomos >= 10 and "pomodoro_10" not in earned: newly_earned.append("pomodoro_10")

        # Topic mastery
        cur.execute(
            "SELECT COUNT(DISTINCT topic) as cnt FROM ("
            "SELECT topic, AVG(score) as avg FROM quiz_history "
            "WHERE user_id=%s AND topic IS NOT NULL AND topic!='' "
            "GROUP BY topic HAVING avg >= 75) t",
            (uid,)
        )
        mastered = cur.fetchone()["cnt"]
        if mastered >= 5 and "topic_master" not in earned: newly_earned.append("topic_master")

        cur.close()
        conn.close()

        # Award all new badges
        result = []
        for badge_id in newly_earned:
            if award_badge(uid, badge_id):
                result.append({**BADGES[badge_id], "badge_id": badge_id})
        return result
    except:
        return []


# ══════════════════════════════════════════════════════
# FEATURE 15 — XP CHALLENGES
# ══════════════════════════════════════════════════════

CHALLENGES = {
    "quiz_3":      {"name": "Quiz Champion",   "desc": "Complete 3 quizzes today",       "xp": 50,  "icon": "🎯"},
    "study_30":    {"name": "Study Sprint",    "desc": "Study for 30 minutes today",     "xp": 40,  "icon": "⏱️"},
    "flashcard_20":{"name": "Card Shark",      "desc": "Review 20 flashcards today",     "xp": 30,  "icon": "🃏"},
    "perfect_1":   {"name": "Perfectionist",   "desc": "Score 100% on any quiz today",   "xp": 100, "icon": "💯"},
    "pomodoro_2":  {"name": "Focus Block",     "desc": "Complete 2 Pomodoros today",     "xp": 35,  "icon": "🍅"},
    "note_1":      {"name": "Note Maker",      "desc": "Create 1 note today",            "xp": 20,  "icon": "📝"},
}

def get_daily_challenges_status(user_id) -> List[Dict]:
    if not user_id:
        return []
    today = date.today()
    try:
        conn = _get_conn()
        cur  = conn.cursor(dictionary=True)
        uid  = int(user_id)

        cur.execute(
            "SELECT challenge_id, completed FROM daily_challenges "
            "WHERE user_id=%s AND challenge_date=%s",
            (uid, today)
        )
        completed_map = {r["challenge_id"]: r["completed"] for r in cur.fetchall()}

        # Check actual progress
        today_str = today.strftime("%Y-%m-%d")

        cur.execute(
            "SELECT COUNT(*) as cnt FROM quiz_history "
            "WHERE user_id=%s AND DATE(taken_at)=%s", (uid, today_str)
        )
        quizzes_today = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COALESCE(SUM(duration_min),0) as mins FROM study_sessions "
            "WHERE user_id=%s AND DATE(started_at)=%s", (uid, today_str)
        )
        mins_today = float(cur.fetchone()["mins"])

        cur.execute(
            "SELECT COUNT(*) as cnt FROM analytics_events "
            "WHERE user_id=%s AND event_type='flashcard' AND DATE(created_at)=%s",
            (uid, today_str)
        )
        cards_today = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT MAX(score) as best FROM quiz_history "
            "WHERE user_id=%s AND DATE(taken_at)=%s", (uid, today_str)
        )
        best_today = float(cur.fetchone()["best"] or 0)

        cur.execute(
            "SELECT COUNT(*) as cnt FROM pomodoro_sessions "
            "WHERE user_id=%s AND completed=1 AND DATE(created_at)=%s",
            (uid, today_str)
        )
        pomos_today = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COUNT(*) as cnt FROM user_notes "
            "WHERE user_id=%s AND DATE(created_at)=%s", (uid, today_str)
        )
        notes_today = cur.fetchone()["cnt"]

        cur.close()
        conn.close()

        progress_map = {
            "quiz_3":       (quizzes_today, 3),
            "study_30":     (int(mins_today), 30),
            "flashcard_20": (cards_today, 20),
            "perfect_1":    (1 if best_today >= 100 else 0, 1),
            "pomodoro_2":   (pomos_today, 2),
            "note_1":       (notes_today, 1),
        }

        result = []
        for cid, info in CHALLENGES.items():
            done_val, target = progress_map.get(cid, (0, 1))
            is_complete = done_val >= target
            pct = min(100, int((done_val / target) * 100))
            result.append({
                "id":          cid,
                "name":        info["name"],
                "desc":        info["desc"],
                "xp":          info["xp"],
                "icon":        info["icon"],
                "completed":   is_complete,
                "progress":    done_val,
                "target":      target,
                "percent":     pct,
            })
        return result
    except:
        return []

def complete_challenge(user_id, challenge_id: str) -> int:
    """Mark challenge done and return XP awarded."""
    if not user_id or challenge_id not in CHALLENGES:
        return 0
    try:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT IGNORE INTO daily_challenges "
            "(user_id, challenge_id, challenge_date, completed, completed_at) "
            "VALUES (%s, %s, %s, 1, %s)",
            (int(user_id), challenge_id, date.today(), datetime.utcnow())
        )
        conn.commit()
        new = cur.rowcount > 0
        cur.close()
        conn.close()
        if new:
            xp = CHALLENGES[challenge_id]["xp"]
            # Award XP via tracker
            try:
                from analytics.tracker import award_xp
                award_xp(user_id, xp, f"Challenge: {challenge_id}")
            except:
                pass
            return xp
        return 0
    except:
        return 0