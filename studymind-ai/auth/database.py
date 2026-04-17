# auth/database.py — MySQL version for Streamlit Cloud
import os
import threading
import mysql.connector
from mysql.connector import pooling
from datetime import datetime
from typing import Optional, Dict, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st

def _cfg():
    # Try Streamlit secrets first, then environment variables
    try:
        return {
            "host":     st.secrets["MYSQL_HOST"],
            "port":     int(st.secrets["MYSQL_PORT"]),
            "user":     st.secrets["MYSQL_USER"],
            "password": st.secrets["MYSQL_PASSWORD"],
            "database": st.secrets["MYSQL_DATABASE"],
        }
    except Exception:
        return {
            "host":     os.getenv("MYSQL_HOST", "localhost"),
            "port":     int(os.getenv("MYSQL_PORT", "3306")),
            "user":     os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", "Admin1234"),
            "database": os.getenv("MYSQL_DATABASE", "studymind"),
        }

_pool = None
_lock = threading.Lock()

def _get_pool():
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                cfg = _cfg()
                ssl_ca = os.getenv("MYSQL_SSL_CA", "ca.pem")
                ssl_args = {}
                if os.path.exists(ssl_ca):
                    ssl_args = {"ssl_ca": ssl_ca, "ssl_verify_cert": True}
                _pool = pooling.MySQLConnectionPool(
                    pool_name="studymind",
                    pool_size=3,
                    **cfg,
                    **ssl_args,
                    autocommit=True,
                    charset="utf8mb4",
                    collation="utf8mb4_unicode_ci",
                )
    return _pool

def _conn():
    return _get_pool().get_connection()

def init_db():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            name          VARCHAR(255) NOT NULL,
            email         VARCHAR(255) NOT NULL UNIQUE,
            pw_hash       TEXT NOT NULL,
            mobile_number VARCHAR(20) DEFAULT '',
            created_at    DATETIME NOT NULL,
            last_login    DATETIME,
            active        TINYINT NOT NULL DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            user_id       INT NOT NULL,
            topic         VARCHAR(255),
            score         FLOAT NOT NULL,
            num_questions INT NOT NULL,
            taken_at      DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id      INT PRIMARY KEY,
            total_cards  INT NOT NULL DEFAULT 0,
            total_docs   INT NOT NULL DEFAULT 0,
            study_streak INT NOT NULL DEFAULT 0,
            last_study   DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[db] MySQL ready")

def insert_user(name: str, email: str, pw_hash: str, mobile: str = "") -> int:
    conn = _conn()
    cur = conn.cursor()
    now = datetime.utcnow()
    cur.execute(
        "INSERT INTO users (name, email, pw_hash, mobile_number, created_at, active) VALUES (%s,%s,%s,%s,%s,1)",
        (name.strip(), email.lower().strip(), pw_hash, mobile.strip(), now)
    )
    uid = cur.lastrowid
    cur.execute("INSERT IGNORE INTO user_stats (user_id) VALUES (%s)", (uid,))
    conn.commit()
    cur.close()
    conn.close()
    return uid

def get_user_by_email(email: str) -> Optional[Dict]:
    conn = _conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE LOWER(email)=%s", (email.lower().strip(),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = _conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def update_last_login(email: str) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_login=%s WHERE LOWER(email)=%s",
                (datetime.utcnow(), email.lower().strip()))
    conn.commit()
    cur.close()
    conn.close()

def update_user_stats(user_id: int, **kwargs) -> None:
    if not kwargs:
        return
    conn = _conn()
    cur = conn.cursor()
    fields = ", ".join(f"{k}=%s" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    cur.execute(f"UPDATE user_stats SET {fields} WHERE user_id=%s", values)
    conn.commit()
    cur.close()
    conn.close()

def get_user_stats(user_id: int) -> Dict:
    conn = _conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM user_stats WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row or {}

def insert_quiz_result(user_id: int, topic: str, score: float, num_q: int) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO quiz_history (user_id, topic, score, num_questions, taken_at) VALUES (%s,%s,%s,%s,%s)",
        (user_id, topic, score, num_q, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()

def get_quiz_history(user_id: int, limit: int = 20) -> List[Dict]:
    conn = _conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM quiz_history WHERE user_id=%s ORDER BY taken_at DESC LIMIT %s",
        (user_id, limit)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def db_info() -> Dict:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"type": "MySQL (Aiven)", "user_count": count}

init_db()