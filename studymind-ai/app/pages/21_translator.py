# app/pages/21_translator.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import translate_text, award_badge, check_and_award_badges

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("# 🌐 Multi-language Translator")
st.markdown("Translate summaries, flashcards, and notes to Tamil or Hindi.")

lang    = st.selectbox("Target Language", ["Tamil", "Hindi", "Telugu", "Malayalam", "Kannada"])
content = st.text_area("Text to Translate", height=200, placeholder="Paste any study content here...")

if st.button("🌐 Translate", use_container_width=True):
    if not content.strip():
        st.warning("Please enter text to translate.")
    else:
        with st.spinner(f"Translating to {lang}..."):
            result = translate_text(content, lang)
        st.markdown(f"### {lang} Translation")
        st.markdown(f"""
        <div style="background:rgba(8,145,178,.08);border:1px solid rgba(8,145,178,.25);
                    border-radius:12px;padding:1.2rem;font-size:15px;line-height:1.8;color:#f8fafc;">
          {result}
        </div>""", unsafe_allow_html=True)
        st.download_button("⬇️ Download Translation", result, file_name=f"translation_{lang.lower()}.txt")
        new_badges = check_and_award_badges(uid)
        award_badge(uid, "multilingual")
        for b in new_badges:
            st.toast(f"{b['icon']} Badge: {b['name']}!", icon="🏅")