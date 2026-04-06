# utils/session_state.py
"""
Centralized Streamlit session state manager.
Call init_session_state() at the top of every page.
"""

import streamlit as st
from datetime import datetime


def init_session_state():
    """Initialize all session state keys with safe defaults."""

    defaults = {
        # ── Document store ──────────────────────────────────────────────
        "uploaded_files": [],          # list of {name, path, size, pages}
        "vector_store": None,          # loaded VectorStore object
        "retriever": None,             # loaded Retriever object
        "docs_indexed": False,         # whether files have been embedded

        # ── Chat history ─────────────────────────────────────────────────
        "chat_history": [],            # list of {role, content, citations, timestamp}
        "current_subject": "General",  # active subject label

        # ── Flashcards ───────────────────────────────────────────────────
        "flashcards": [],              # list of FlashCard dicts
        "fc_index": 0,                 # current card index in practice mode
        "fc_show_answer": False,       # toggle answer visibility
        "fc_session_results": [],      # list of {card_id, rating} for this session

        # ── Quiz ─────────────────────────────────────────────────────────
        "quiz_questions": [],          # list of Question dicts
        "quiz_answers": {},            # {question_id: chosen_option}
        "quiz_submitted": False,       # whether quiz was evaluated
        "quiz_score": 0,               # last quiz percentage score
        "quiz_history": [],            # list of {date, score, topic, num_questions}

        # ── Summary ──────────────────────────────────────────────────────
        "summaries": {},               # {filename: summary_text}

        # ── Study Plan ───────────────────────────────────────────────────
        "study_plan": [],              # list of DayPlan dicts
        "exam_date": None,             # datetime.date object
        "weak_topics": [],             # list of topic strings

        # ── Mind Map ─────────────────────────────────────────────────────
        "mind_map_data": None,         # {nodes: [...], edges: [...]}

        # ── UI state ─────────────────────────────────────────────────────
        "active_page": "Ask Notes",
        "sidebar_subject_filter": "All",
        "theme": "dark",
        "notifications": [],           # list of {msg, type, timestamp}
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_chat_message(role: str, content: str, citations: list = None):
    """Append a message to chat history."""
    st.session_state.chat_history.append({
        "role": role,
        "content": content,
        "citations": citations or [],
        "timestamp": datetime.now().strftime("%H:%M"),
    })


def clear_chat():
    """Reset chat history."""
    st.session_state.chat_history = []


def add_notification(message: str, msg_type: str = "info"):
    """Queue a toast notification. Types: info | success | warning | error"""
    st.session_state.notifications.append({
        "msg": message,
        "type": msg_type,
        "timestamp": datetime.now(),
    })


def flush_notifications():
    """Display and clear all queued notifications."""
    for notif in st.session_state.notifications:
        if notif["type"] == "success":
            st.success(notif["msg"])
        elif notif["type"] == "warning":
            st.warning(notif["msg"])
        elif notif["type"] == "error":
            st.error(notif["msg"])
        else:
            st.info(notif["msg"])
    st.session_state.notifications = []


def reset_quiz():
    """Clear quiz state for a fresh quiz."""
    st.session_state.quiz_questions = []
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_score = 0


def get_overall_progress() -> dict:
    """Return a summary dict of the user's study progress."""
    total_cards = len(st.session_state.flashcards)
    reviewed = len(st.session_state.fc_session_results)
    avg_quiz = (
        sum(h["score"] for h in st.session_state.quiz_history) /
        len(st.session_state.quiz_history)
        if st.session_state.quiz_history else 0
    )
    return {
        "total_flashcards": total_cards,
        "flashcards_reviewed": reviewed,
        "quiz_attempts": len(st.session_state.quiz_history),
        "avg_quiz_score": round(avg_quiz, 1),
        "docs_uploaded": len(st.session_state.uploaded_files),
        "summaries_generated": len(st.session_state.summaries),
    }