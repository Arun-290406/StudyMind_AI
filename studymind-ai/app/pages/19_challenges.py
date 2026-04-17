# app/pages/19_challenges.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from datetime import date
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import get_daily_challenges_status, complete_challenge

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("# ⚡ Daily XP Challenges")
st.markdown(f"Today's challenges — {date.today().strftime('%A, %d %B %Y')}")

challenges = get_daily_challenges_status(uid)
total_xp   = sum(c["xp"] for c in challenges if c["completed"])
max_xp     = sum(c["xp"] for c in challenges)

st.markdown(f"### 🌟 {total_xp} / {max_xp} XP earned today")
st.progress(total_xp / max_xp if max_xp > 0 else 0)
st.divider()

for ch in challenges:
    color  = "#6ee7b7" if ch["completed"] else "#7c3aed"
    bg     = "rgba(5,150,105,.1)"  if ch["completed"] else "rgba(124,58,237,.08)"
    border = "rgba(5,150,105,.35)" if ch["completed"] else "rgba(124,58,237,.25)"
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {border};border-radius:14px;
                padding:1rem 1.2rem;margin-bottom:10px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="display:flex;align-items:center;gap:10px;">
          <span style="font-size:1.5rem;">{ch['icon']}</span>
          <div>
            <div style="font-weight:700;color:#f8fafc;">{ch['name']}</div>
            <div style="font-size:12px;color:#64748b;">{ch['desc']}</div>
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-family:Syne,sans-serif;font-weight:800;color:{color};font-size:1.1rem;">
            +{ch['xp']} XP
          </div>
          <div style="font-size:11px;color:#64748b;">{ch['progress']}/{ch['target']}</div>
        </div>
      </div>
      <div style="margin-top:8px;background:#0d1326;border-radius:4px;height:6px;">
        <div style="width:{ch['percent']}%;background:{color};border-radius:4px;height:6px;"></div>
      </div>
      {"<div style='font-size:12px;color:#6ee7b7;margin-top:6px;font-weight:600;'>✅ Completed!</div>" if ch['completed'] else ""}
    </div>""", unsafe_allow_html=True)