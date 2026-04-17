# app/pages/18_badges.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import get_user_badges, check_and_award_badges, BADGES

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("# 🏅 Badges & Achievements")
st.markdown("Earn badges by reaching study milestones.")

# Check and award any new badges
new_badges = check_and_award_badges(uid)
for b in new_badges:
    st.toast(f"{b['icon']} New badge earned: {b['name']}!", icon="🎉")

earned     = get_user_badges(uid)
earned_ids = {b["badge_id"] for b in earned}

st.markdown(f"### You've earned **{len(earned)}** of **{len(BADGES)}** badges")
st.progress(len(earned) / len(BADGES))
st.divider()

cols = st.columns(3)
for i, (bid, info) in enumerate(BADGES.items()):
    is_earned = bid in earned_ids
    earn_date = next((b["earned_at"] for b in earned if b["badge_id"]==bid), "")
    bg        = "rgba(124,58,237,.15)" if is_earned else "rgba(30,41,59,.5)"
    border    = "rgba(124,58,237,.5)"  if is_earned else "rgba(51,65,85,.4)"
    opacity   = "1" if is_earned else "0.4"
    with cols[i % 3]:
        st.markdown(f"""
        <div style="background:{bg};border:1px solid {border};border-radius:14px;
                    padding:1.2rem;text-align:center;margin-bottom:12px;opacity:{opacity};">
          <div style="font-size:2rem;margin-bottom:6px;">{info['icon']}</div>
          <div style="font-weight:700;color:#f8fafc;font-size:13px;">{info['name']}</div>
          <div style="font-size:11px;color:#64748b;margin-top:4px;">{info['desc']}</div>
          {f'<div style="font-size:10px;color:#a78bfa;margin-top:6px;">✅ Earned {earn_date}</div>' if is_earned else '<div style="font-size:10px;color:#334155;margin-top:6px;">🔒 Locked</div>'}
        </div>""", unsafe_allow_html=True)