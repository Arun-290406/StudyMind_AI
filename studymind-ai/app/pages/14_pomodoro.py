# app/pages/14_pomodoro.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import time
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import log_pomodoro, get_pomodoro_stats, check_and_award_badges

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("""
<style>
.pomo-ring{display:flex;flex-direction:column;align-items:center;justify-content:center;
  width:220px;height:220px;border-radius:50%;margin:1rem auto;
  border:8px solid #7c3aed;box-shadow:0 0 40px rgba(124,58,237,.4);}
.pomo-time{font-family:Syne,sans-serif;font-size:3.2rem;font-weight:800;color:#f8fafc;}
.pomo-label{font-size:13px;color:#94a3b8;margin-top:4px;}
</style>""", unsafe_allow_html=True)

st.markdown("# 🍅 Pomodoro Timer")
st.markdown("Stay focused with 25-minute work sessions and 5-minute breaks.")

stats = get_pomodoro_stats(uid)
c1, c2, c3 = st.columns(3)
c1.metric("Total Sessions", stats["total_sessions"])
c2.metric("Total Minutes", stats["total_minutes"])
c3.metric("Today", stats["today_sessions"])

st.divider()

mode_col, _ = st.columns([1, 2])
with mode_col:
    mode = st.radio("Mode", ["🎯 Work (25 min)", "☕ Short Break (5 min)", "🛋️ Long Break (15 min)"], key="pomo_mode")

duration = 25 if "Work" in mode else 5 if "Short" in mode else 15
ptype    = "work" if "Work" in mode else "break"

if "pomo_running"   not in st.session_state: st.session_state.pomo_running   = False
if "pomo_start"     not in st.session_state: st.session_state.pomo_start     = None
if "pomo_duration"  not in st.session_state: st.session_state.pomo_duration  = duration * 60
if "pomo_completed" not in st.session_state: st.session_state.pomo_completed = False

total_secs   = duration * 60
elapsed      = int(time.time() - st.session_state.pomo_start) if st.session_state.pomo_start else 0
remaining    = max(0, total_secs - elapsed)
mins, secs   = divmod(remaining, 60)
pct          = 1.0 - (remaining / total_secs) if total_secs > 0 else 1.0

ring_color = "#7c3aed" if ptype == "work" else "#059669"
st.markdown(f"""
<div class="pomo-ring" style="border-color:{ring_color};box-shadow:0 0 40px {ring_color}55;">
  <div class="pomo-time">{mins:02d}:{secs:02d}</div>
  <div class="pomo-label">{"Work Session" if ptype=="work" else "Break Time"}</div>
</div>""", unsafe_allow_html=True)

st.progress(pct)

b1, b2, b3 = st.columns(3)
if b1.button("▶️ Start", use_container_width=True, disabled=st.session_state.pomo_running):
    st.session_state.pomo_running   = True
    st.session_state.pomo_start     = time.time()
    st.session_state.pomo_completed = False
    st.rerun()

if b2.button("⏸ Pause / Stop", use_container_width=True, disabled=not st.session_state.pomo_running):
    st.session_state.pomo_running = False
    st.session_state.pomo_start   = None
    st.rerun()

if b3.button("🔄 Reset", use_container_width=True):
    st.session_state.pomo_running   = False
    st.session_state.pomo_start     = None
    st.session_state.pomo_completed = False
    st.rerun()

if st.session_state.pomo_running:
    if remaining <= 0:
        st.session_state.pomo_running   = False
        st.session_state.pomo_completed = True
        log_pomodoro(uid, ptype, duration, completed=True)
        # Check badges
        new_badges = check_and_award_badges(uid)
        for b in new_badges:
            st.toast(f"{b['icon']} Badge earned: {b['name']}!", icon="🏅")
        st.balloons()
        st.success(f"✅ {'Work session' if ptype=='work' else 'Break'} complete! +{duration} minutes logged.")
        st.rerun()
    else:
        time.sleep(1)
        st.rerun()

if st.session_state.pomo_completed:
    st.success("🎉 Session logged to your study time!")