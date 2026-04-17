# app/pages/20_essay_evaluator.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from auth.auth_manager import current_user
from utils.session_state import init_session_state
from features.new_features import evaluate_essay, award_badge, check_and_award_badges

init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown("# ✍️ Essay & Answer Evaluator")
st.markdown("Get AI feedback on your long-form answers graded against your notes.")

question = st.text_input("Question / Topic", placeholder="e.g. Explain the working of a Turing Machine")
context  = ""
if st.session_state.get("docs_indexed") and st.session_state.get("vector_store"):
    use_notes = st.checkbox("Grade against my uploaded notes", value=True)
    if use_notes:
        try:
            from core.retriever import get_relevant_chunks
            chunks  = get_relevant_chunks(question, st.session_state.vector_store, k=5)
            context = "\n".join([c.page_content for c in chunks]) if chunks else ""
        except:
            pass

essay = st.text_area("Your Answer", height=280, placeholder="Write your answer here...")

if st.button("📊 Evaluate My Answer", use_container_width=True):
    if not question.strip():
        st.warning("Please enter a question.")
    elif not essay.strip():
        st.warning("Please write your answer.")
    else:
        with st.spinner("AI is grading your answer..."):
            result = evaluate_essay(essay, question, context)

        score  = result.get("score", 0)
        grade  = result.get("grade", "N/A")
        color  = "#6ee7b7" if score>=80 else "#fcd34d" if score>=60 else "#fda4af"

        st.markdown(f"""
        <div style="background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.3);
                    border-radius:16px;padding:1.5rem;text-align:center;margin:1rem 0;">
          <div style="font-family:Syne,sans-serif;font-size:3rem;font-weight:800;color:{color};">{score}/100</div>
          <div style="font-size:1.2rem;font-weight:700;color:#f8fafc;">Grade: {grade}</div>
          <div style="font-size:13px;color:#94a3b8;margin-top:6px;">{result.get('feedback','')}</div>
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**✅ Strengths**")
            for s in result.get("strengths", []):
                st.markdown(f"- {s}")
        with c2:
            st.markdown("**📈 Improvements**")
            for s in result.get("improvements", []):
                st.markdown(f"- {s}")

        if result.get("missing_points"):
            st.markdown("**📌 Missing Key Points**")
            for p in result["missing_points"]:
                st.markdown(f"- {p}")

        if grade == "A":
            new_badges = check_and_award_badges(uid)
            award_badge(uid, "essay_ace")
            for b in new_badges:
                st.toast(f"{b['icon']} Badge: {b['name']}!", icon="🏅")