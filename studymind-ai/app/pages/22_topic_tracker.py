# app/pages/22_topic_tracker.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import get_topic_completion, set_topic_completed, add_topics_from_notes
from analytics.tracker import get_topics_covered

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("# ✅ Topic Completion Tracker")
st.markdown("Track which topics you've studied and what still needs work.")

# Auto-import from quiz/study history
covered = get_topics_covered(uid)
if covered:
    add_topics_from_notes(uid, covered)

# Manual add
with st.expander("➕ Add Topics Manually"):
    new_topics = st.text_area("Enter topics (one per line)", height=100)
    if st.button("Add Topics"):
        topics = [t.strip() for t in new_topics.split("\n") if t.strip()]
        add_topics_from_notes(uid, topics)
        st.success(f"Added {len(topics)} topics!")
        st.rerun()

topics = get_topic_completion(uid)

if not topics:
    st.info("No topics tracked yet. Study topics from quizzes will appear here automatically.")
else:
    done  = sum(1 for t in topics if t["completed"])
    total = len(topics)
    st.markdown(f"### {done}/{total} topics completed")
    st.progress(done / total if total > 0 else 0)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📚 Pending**")
        pending = [t for t in topics if not t["completed"]]
        for t in pending:
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"⭕ {t['topic']}")
            if c2.button("✓", key=f"done_{t['topic']}", help="Mark complete"):
                set_topic_completed(uid, t["topic"], True)
                st.rerun()

    with col2:
        st.markdown("**✅ Completed**")
        completed = [t for t in topics if t["completed"]]
        for t in completed:
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"✅ ~~{t['topic']}~~")
            if c2.button("↩", key=f"undo_{t['topic']}", help="Mark incomplete"):
                set_topic_completed(uid, t["topic"], False)
                st.rerun()