# app/pages/15_notes.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import save_note, update_note, delete_note, get_notes, check_and_award_badges

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("# 📝 My Notes")
st.markdown("Create and manage personal notes alongside your study materials.")

tab_new, tab_view = st.tabs(["✏️ New Note", "📚 My Notes"])

with tab_new:
    doc_name = st.text_input("Document/Topic (optional)", placeholder="e.g. FLAT Unit 2")
    title    = st.text_input("Note Title", placeholder="e.g. Key Concepts")
    content  = st.text_area("Content", height=300, placeholder="Write your notes here...")
    if st.button("💾 Save Note", use_container_width=True):
        if title.strip() and content.strip():
            nid = save_note(uid, title.strip(), content.strip(), doc_name.strip())
            if nid:
                new_badges = check_and_award_badges(uid)
                for b in new_badges:
                    st.toast(f"{b['icon']} Badge earned: {b['name']}!", icon="🏅")
                st.success("✅ Note saved!")
                st.rerun()
            else:
                st.error("Failed to save note.")
        else:
            st.warning("Please enter a title and content.")

with tab_view:
    notes = get_notes(uid)
    if not notes:
        st.info("No notes yet. Create your first note!")
    else:
        st.markdown(f"**{len(notes)} notes**")
        for note in notes:
            with st.expander(f"📄 {note['title']} — {str(note['updated_at'])[:10]}"):
                if note.get("doc_name"):
                    st.caption(f"📁 {note['doc_name']}")
                edit_title   = st.text_input("Title",   value=note["title"],   key=f"et_{note['id']}")
                edit_content = st.text_area("Content",  value=note["content"], key=f"ec_{note['id']}", height=200)
                c1, c2 = st.columns(2)
                if c1.button("💾 Update", key=f"upd_{note['id']}", use_container_width=True):
                    update_note(note["id"], edit_title, edit_content)
                    st.success("Updated!")
                    st.rerun()
                if c2.button("🗑️ Delete", key=f"del_{note['id']}", use_container_width=True):
                    delete_note(note["id"])
                    st.rerun()