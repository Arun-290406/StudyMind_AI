import os
import sys
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from analytics.tracker import get_recent_activity
from auth.auth_manager import current_user
from utils.session_state import init_session_state

init_session_state()
user = current_user()
uid = user.get("id", 0)

st.markdown('<div class="sm-page-title">History</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sm-page-sub">A timeline of recent study sessions, quizzes, topic coverage, flashcard reviews, and XP gains.</div>',
    unsafe_allow_html=True,
)

kind_meta = {
    "session": {"label": "Study Session", "badge": "badge-v", "icon": "⏱️"},
    "quiz": {"label": "Quiz", "badge": "badge-c", "icon": "📝"},
    "topic": {"label": "Topic", "badge": "badge-em", "icon": "🧠"},
    "flashcard": {"label": "Flashcard", "badge": "badge-a", "icon": "🃏"},
    "xp": {"label": "XP", "badge": "badge-v", "icon": "✨"},
}

events = get_recent_activity(uid, limit=30)

if not events:
    st.markdown(
        '<div class="sm-empty"><div class="sm-empty-ico">🕘</div><div class="sm-empty-title">No history yet</div><div class="sm-empty-sub">Use the app a bit more and your activity timeline will appear here.</div></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="sm-highlight"><div class="sm-highlight-title">Recent Activity</div><div class="sm-page-sub" style="margin:0;">Showing the latest {len(events)} events for {user["name"].split()[0]}.</div></div>',
        unsafe_allow_html=True,
    )

    for item in events:
        meta = kind_meta.get(item["kind"], {"label": "Activity", "badge": "badge-v", "icon": "•"})
        raw_time = item.get("event_time") or ""
        try:
            dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            stamp = dt.strftime("%b %d, %Y • %I:%M %p")
        except Exception:
            stamp = raw_time[:19] if raw_time else "Unknown time"

        extra = (item.get("meta") or "").strip()
        extra_html = f'<div style="font-size:11px;color:var(--t3);margin-top:4px;">{extra}</div>' if extra else ''
        title = item.get("title") or meta["label"]
        detail = item.get("detail") or ""

        card_html = (
            f'<div class="sm-panel" style="margin-bottom:.85rem;">'
            f'<div style="display:flex;gap:12px;align-items:flex-start;">'
            f'<div style="width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;'
            f'background:rgba(124,58,237,.12);border:1px solid rgba(124,58,237,.22);font-size:18px;flex-shrink:0;">{meta["icon"]}</div>'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">'
            f'<span class="sm-badge {meta["badge"]}">{meta["label"]}</span>'
            f'<span style="font-size:11px;color:var(--t3);">{stamp}</span>'
            f'</div>'
            f'<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:800;color:var(--t1);margin-top:.4rem;">{title}</div>'
            f'<div style="font-size:13px;color:var(--t2);margin-top:.2rem;">{detail}</div>'
            f'{extra_html}'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)
