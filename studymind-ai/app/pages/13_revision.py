import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from analytics.tracker import get_quiz_mistakes, get_topic_mastery, get_user_gamification
from auth.auth_manager import current_user
from utils.session_state import init_session_state

init_session_state()
user = current_user()
uid = user.get("id", 0)

st.markdown('<div class="sm-page-title">Revision Mode</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sm-page-sub">Focus on weak topics, revisit missed questions, and turn analytics into action.</div>',
    unsafe_allow_html=True,
)

mastery = get_topic_mastery(uid)
mistakes = get_quiz_mistakes(uid, limit=12)
gamification = get_user_gamification(uid)

st.markdown(
    f'<div class="sm-stats"><div class="sm-stat"><span class="sm-stat-n">{gamification["xp"]}</span><span class="sm-stat-l">XP</span></div><div class="sm-stat"><span class="sm-stat-n">{gamification["level"]}</span><span class="sm-stat-l">Level</span></div><div class="sm-stat"><span class="sm-stat-n">{gamification["streak_days"]}</span><span class="sm-stat-l">Streak</span></div><div class="sm-stat"><span class="sm-stat-n">{len(mistakes)}</span><span class="sm-stat-l">Mistakes</span></div></div>',
    unsafe_allow_html=True,
)

col_a, col_b = st.columns([2, 3])

with col_a:
    st.markdown('<div class="sm-panel"><div class="sm-panel-title">Topic Mastery Tracker</div><div class="sm-panel-sub">Weak topics are shown first so you know where to revise.</div>', unsafe_allow_html=True)
    if not mastery:
        st.markdown('<div class="sm-empty" style="padding:2rem 1rem"><div class="sm-empty-title">No mastery data yet</div><div class="sm-empty-sub">Complete quizzes to build topic mastery.</div></div>', unsafe_allow_html=True)
    else:
        for item in mastery:
            color = "#fda4af" if item["mastery_level"] == "weak" else "#fcd34d" if item["mastery_level"] == "improving" else "#6ee7b7"
            st.markdown(
                f'<div class="sm-list-card" style="background:rgba(124,58,237,.05);border-color:rgba(124,58,237,.18);"><div style="display:flex;justify-content:space-between;gap:8px;align-items:center;"><div style="font-weight:700;color:#f8fafc;">{item["topic"]}</div><span class="sm-badge badge-v" style="color:{color};border-color:{color}55;background:{color}18;">{item["mastery_level"]}</span></div><div style="font-size:12px;color:#94a3b8;margin-top:.35rem;">Avg {item["avg_score"]}% · Last {item["last_score"]}% · {item["attempts"]} attempt(s)</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="sm-panel"><div class="sm-panel-title">Retake Wrong Answers Only</div><div class="sm-panel-sub">Load recently missed questions into Quiz Me for focused practice.</div>', unsafe_allow_html=True)
    if not mistakes:
        st.markdown('<div class="sm-empty" style="padding:2rem 1rem"><div class="sm-empty-title">No saved mistakes</div><div class="sm-empty-sub">Wrong quiz answers will appear here automatically.</div></div>', unsafe_allow_html=True)
    else:
        if st.button("Load Revision Quiz", use_container_width=True):
            retry_questions = []
            for idx, item in enumerate(mistakes):
                retry_questions.append(
                    {
                        "id": f"rev_{item['id']}_{idx}",
                        "question": item["question_text"],
                        "options": item.get("options", {}),
                        "correct": item.get("correct_answer", ""),
                        "explanation": item.get("explanation", ""),
                        "topic": item.get("topic") or "General",
                        "difficulty": "revision",
                    }
                )
            st.session_state.quiz_questions = retry_questions
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.active_page = "Quiz Me"
            st.rerun()

        for item in mistakes:
            st.markdown(
                f'<div class="sm-list-card"><div style="font-weight:700;color:#f8fafc;">{item["question_text"]}</div><div style="font-size:12px;color:#94a3b8;margin-top:.35rem;">Topic: {item.get("topic") or "General"} · Missed {item.get("miss_count", 1)} time(s)</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)
