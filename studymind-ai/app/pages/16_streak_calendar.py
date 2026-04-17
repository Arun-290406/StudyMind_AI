# app/pages/16_streak_calendar.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from datetime import date, timedelta
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import get_streak_calendar

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("# 📅 Streak Calendar")
st.markdown("Your GitHub-style study activity heatmap.")

data = get_streak_calendar(uid, days=90)

today   = date.today()
start   = today - timedelta(days=89)
current = start

weeks = []
week  = []
# Pad to start on Monday
pad = current.weekday()
for _ in range(pad):
    week.append(None)

while current <= today:
    week.append(current)
    if len(week) == 7:
        weeks.append(week)
        week = []
    current += timedelta(days=1)
if week:
    while len(week) < 7:
        week.append(None)
    weeks.append(week)

day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def get_color(mins: float) -> str:
    if mins <= 0:   return "#1e293b"
    if mins < 15:   return "#4c1d95"
    if mins < 30:   return "#6d28d9"
    if mins < 60:   return "#7c3aed"
    return "#a78bfa"

# Stats
total_days   = sum(1 for v in data.values() if v > 0)
total_mins   = sum(data.values())
streak       = 0
check        = today
while str(check) in data and data[str(check)] > 0:
    streak += 1
    check -= timedelta(days=1)

c1, c2, c3 = st.columns(3)
c1.metric("Active Days", total_days)
c2.metric("Total Study Time", f"{int(total_mins)} min")
c3.metric("Current Streak", f"{streak} days 🔥")

st.divider()

# Build heatmap HTML
html = '<div style="overflow-x:auto;padding:1rem 0;">'
html += '<div style="display:flex;gap:3px;">'
for week in weeks:
    html += '<div style="display:flex;flex-direction:column;gap:3px;">'
    for d in week:
        if d is None:
            html += '<div style="width:14px;height:14px;"></div>'
        else:
            mins  = data.get(str(d), 0)
            color = get_color(mins)
            tip   = f"{d}: {int(mins)} min" if mins > 0 else str(d)
            html += f'<div title="{tip}" style="width:14px;height:14px;border-radius:3px;background:{color};cursor:pointer;"></div>'
    html += '</div>'
html += '</div>'

# Day labels on left
html += '<div style="display:flex;gap:6px;margin-top:8px;font-size:10px;color:#64748b;">'
for l in ["Less", "", "", "", "More"]:
    c = ["#1e293b","#4c1d95","#6d28d9","#7c3aed","#a78bfa"]
    for i, col in enumerate(c):
        html += f'<div style="width:14px;height:14px;border-radius:3px;background:{col};"></div>'
    if l:
        html += f'<span style="line-height:14px;">{l}</span>'
    break
html += '<div style="width:14px;height:14px;border-radius:3px;background:#4c1d95;"></div>'
html += '<div style="width:14px;height:14px;border-radius:3px;background:#6d28d9;"></div>'
html += '<div style="width:14px;height:14px;border-radius:3px;background:#7c3aed;"></div>'
html += '<div style="width:14px;height:14px;border-radius:3px;background:#a78bfa;"></div>'
html += '<span style="line-height:14px;font-size:10px;color:#64748b;">More</span>'
html += '</div></div>'

st.markdown(html, unsafe_allow_html=True)

st.divider()
st.markdown("### 📊 Recent Activity")
recent = sorted([(k, v) for k, v in data.items() if v > 0], reverse=True)[:10]
if recent:
    for day_str, mins in recent:
        pct = min(100, int((mins / 120) * 100))
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
          <span style="font-size:12px;color:#94a3b8;width:90px;">{day_str}</span>
          <div style="flex:1;background:#1e293b;border-radius:4px;height:8px;">
            <div style="width:{pct}%;background:#7c3aed;border-radius:4px;height:8px;"></div>
          </div>
          <span style="font-size:12px;color:#a78bfa;width:60px;">{int(mins)} min</span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No study sessions yet. Start studying to see your activity!")