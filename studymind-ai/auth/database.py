# auth/database.py
"""
SQLite database — with mobile_number support for SMS notifications.

Schema changes:
  users table now includes: mobile_number TEXT (e.g. "+919876543210")

Migration: If you have an existing studymind.db, the ALTER TABLE
           statement below adds the column safely if missing.
"""

import os
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "./data/db/studymind.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn


def init_db() -> None:
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL,
            email          TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            pw_hash        TEXT    NOT NULL,
            mobile_number  TEXT    DEFAULT '',
            created_at     TEXT    NOT NULL,
            last_login     TEXT,
            active         INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS quiz_history (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            topic          TEXT,
            score          REAL    NOT NULL,
            num_questions  INTEGER NOT NULL,
            taken_at       TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            user_id       INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            total_cards   INTEGER NOT NULL DEFAULT 0,
            total_docs    INTEGER NOT NULL DEFAULT 0,
            study_streak  INTEGER NOT NULL DEFAULT 0,
            last_study    TEXT
        );
    """)
    conn.commit()

    # ── Safe migration: add mobile_number if upgrading from old DB ────────────
    try:
        conn.execute("ALTER TABLE users ADD COLUMN mobile_number TEXT DEFAULT ''")
        conn.commit()
        print("[db] Migrated: added mobile_number column")
    except sqlite3.OperationalError:
        pass  # Column already exists — expected for new installs

    print(f"[db] SQLite ready → {DB_PATH}")


# ── User CRUD ─────────────────────────────────────────────────────────────────

def insert_user(name: str, email: str, pw_hash: str, mobile: str = "") -> int:
    """Insert new user with optional mobile number. Returns new row id."""
    conn = _get_conn()
    now  = datetime.utcnow().isoformat()
    cur  = conn.execute(
        "INSERT INTO users (name, email, pw_hash, mobile_number, created_at, active) "
        "VALUES (?,?,?,?,?,1)",
        (name.strip(), email.lower().strip(), pw_hash, mobile.strip(), now)
    )
    conn.execute("INSERT INTO user_stats (user_id) VALUES (?)", (cur.lastrowid,))
    conn.commit()
    return cur.lastrowid


def get_user_by_email(email: str) -> Optional[Dict]:
    conn = _get_conn()
    row  = conn.execute(
        "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)
    ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = _get_conn()
    row  = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_last_login(email: str) -> None:
    conn = _get_conn()
    conn.execute(
        "UPDATE users SET last_login = ? WHERE email = ? COLLATE NOCASE",
        (datetime.utcnow().isoformat(), email.strip())
    )
    conn.commit()


def update_user_stats(user_id: int, **kwargs) -> None:
    if not kwargs:
        return
    conn   = _get_conn()
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    conn.execute(f"UPDATE user_stats SET {fields} WHERE user_id = ?", values)
    conn.commit()


def get_user_stats(user_id: int) -> Dict:
    conn = _get_conn()
    row  = conn.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else {}


def insert_quiz_result(user_id: int, topic: str, score: float, num_q: int) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO quiz_history (user_id, topic, score, num_questions, taken_at) VALUES (?,?,?,?,?)",
        (user_id, topic, score, num_q, datetime.utcnow().isoformat())
    )
    conn.commit()


def get_quiz_history(user_id: int, limit: int = 20) -> List[Dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM quiz_history WHERE user_id = ? ORDER BY taken_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    return [dict(r) for r in rows]


def db_info() -> Dict:
    conn  = _get_conn()
    users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return {
        "path":       str(DB_PATH),
        "exists":     DB_PATH.exists(),
        "size_kb":    round(DB_PATH.stat().st_size / 1024, 1) if DB_PATH.exists() else 0,
        "user_count": users,
    }
init_db()