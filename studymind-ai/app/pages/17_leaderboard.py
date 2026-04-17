# app/pages/17_leaderboard.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import get_quiz_leaderboard, get_confidence_scores

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("# 🏆 Quiz Leaderboard & Confidence")
st.markdown("Your personal best scores and topic confidence levels.")

tab_lb, tab_conf = st.tabs(["🥇 Best Scores", "💪 Confidence Scores"])

with tab_lb:
    leaderboard = get_quiz_leaderboard(uid)
    if not leaderboard:
        st.info("Complete some quizzes to see your leaderboard!")
    else:
        medals = ["🥇", "🥈", "🥉"]
        for i, row in enumerate(leaderboard):
            medal = medals[i] if i < 3 else f"#{i+1}"
            color = "#fcd34d" if i==0 else "#94a3b8" if i==1 else "#cd7f32" if i==2 else "#64748b"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;
                        background:rgba(124,58,237,.06);border:1px solid rgba(124,58,237,.2);
                        border-radius:12px;margin-bottom:8px;">
              <span style="font-size:1.6rem;width:36px;">{medal}</span>
              <div style="flex:1;">
                <div style="font-weight:700;color:#f8fafc;font-size:14px;">{row['topic']}</div>
                <div style="font-size:12px;color:#64748b;">{row['attempts']} attempts · Last: {row['last_attempt']}</div>
              </div>
              <div style="text-align:right;">
                <div style="font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:{color};">{row['best_score']}%</div>
                <div style="font-size:11px;color:#64748b;">Avg: {row['avg_score']}%</div>
              </div>
            </div>""", unsafe_allow_html=True)

with tab_conf:
    confidence = get_confidence_scores(uid)
    if not confidence:
        st.info("Take quizzes to build your confidence scores!")
    else:
        for item in confidence:
            color = "#6ee7b7" if item["level"]=="High" else "#fcd34d" if item["level"]=="Medium" else "#fda4af"
            conf  = item["confidence"]
            st.markdown(f"""
            <div style="margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-weight:600;color:#f8fafc;">{item['topic']}</span>
                <span style="font-size:13px;color:{color};font-weight:700;">{conf}% · {item['level']}</span>
              </div>
              <div style="background:#1e293b;border-radius:6px;height:10px;">
                <div style="width:{conf}%;background:{color};border-radius:6px;height:10px;transition:width .3s;"></div>
              </div>
              <div style="font-size:11px;color:#64748b;margin-top:2px;">
                Avg: {item['avg_score']}% · Best: {item['best_score']}% · {item['attempts']} attempts
              </div>
            </div>""", unsafe_allow_html=True)