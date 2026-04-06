# app/pages/03_quiz.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from datetime import datetime
from utils.session_state import init_session_state
from auth.auth_manager import current_user
from features.quiz_gen import generate_mcq_quiz, evaluate_mcq, quiz_history_stats
from analytics.tracker import log_weak_area
init_session_state()
user = current_user(); uid = user.get("id", 0)

st.markdown('<div class="sm-page-title">📝 Quiz Me</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">AI-generated MCQs from your notes · scoring · explanations · weak area detection</div>', unsafe_allow_html=True)

if not st.session_state.docs_indexed:
    st.markdown('<div class="sm-empty"><div class="sm-empty-ico">📁</div><div class="sm-empty-title">Index documents first</div><div class="sm-empty-sub">Upload your notes from Ask Notes page.</div></div>', unsafe_allow_html=True)
    st.stop()

st.markdown("""
<div style="background:rgba(225,29,72,.07);border:1px solid rgba(225,29,72,.2);
            border-radius:13px;padding:.8rem 1.2rem;margin-bottom:1rem;
            display:flex;align-items:center;gap:10px;">
  <span style="font-size:1.4rem;">🔥</span>
  <div><div style="font-weight:700;color:#fda4af;font-size:13.5px;">
    Want Exam Mode, Timers &amp; Negative Marking?</div>
  <div style="font-size:12px;color:#64748b;">Navigate to Smart Quiz in the sidebar.</div></div>
</div>""", unsafe_allow_html=True)

tab_q, tab_hist = st.tabs(["📝 Take Quiz", "📊 History"])

with tab_q:
    if not st.session_state.get("quiz_questions"):
        st.markdown('<div class="sm-highlight"><div class="sm-highlight-title">Configure Quiz</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        topic = c1.text_input("Topic focus", placeholder="e.g. Operating Systems")
        num_q = c2.slider("Questions", 3, 15, 5)
        diff  = c3.selectbox("Difficulty", ["medium","easy","hard"])
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("🚀 Generate Quiz", use_container_width=True):
            with st.spinner("Generating questions…"):
                qs = generate_mcq_quiz(st.session_state.vector_store, topic=topic, num_questions=num_q, difficulty=diff)
            if qs:
                st.session_state.quiz_questions = qs; st.session_state.quiz_answers = {}; st.session_state.quiz_submitted = False; st.rerun()
            else:
                st.error("Could not generate questions. Try uploading more detailed notes.")

    elif not st.session_state.get("quiz_submitted"):
        qs = st.session_state.quiz_questions
        answered = len(st.session_state.quiz_answers); total = len(qs)
        st.progress(answered/total if total else 0, text=f"{answered}/{total} answered")
        st.write("")
        for i, q in enumerate(qs):
            st.markdown(f'<div class="sm-card" style="margin-bottom:1rem;"><div style="font-size:10.5px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:.09em;margin-bottom:.5rem;">Q{i+1} · {q.get("topic","")}</div><div style="font-size:15px;font-weight:600;color:#f8fafc;margin-bottom:1rem;line-height:1.5;">{q["question"]}</div>', unsafe_allow_html=True)
            opts = q.get("options",{}); choices = [f"{k}) {v}" for k,v in sorted(opts.items())]
            cur = st.session_state.quiz_answers.get(q["id"]); cur_i = None
            if cur:
                for j,c in enumerate(choices):
                    if c.startswith(cur): cur_i=j; break
            sel = st.radio(f"_q{q['id']}", choices, index=cur_i, key=f"r_{q['id']}", label_visibility="collapsed")
            if sel: st.session_state.quiz_answers[q["id"]] = sel[0]
            st.markdown('</div>', unsafe_allow_html=True)
        if st.button("✅ Submit Quiz", use_container_width=True, disabled=len(st.session_state.quiz_answers)!=total):
            result = evaluate_mcq(qs, st.session_state.quiz_answers)
            st.session_state.quiz_result = result; st.session_state.quiz_submitted = True
            for t in result.get("weak_topics",[]): log_weak_area(uid, t)
            if "quiz_history" not in st.session_state: st.session_state["quiz_history"] = []
            st.session_state["quiz_history"].append({"date":datetime.now().strftime("%b %d, %H:%M"),"score":result["score_pct"],"topic":qs[0].get("topic","General"),"num_questions":total})
            st.rerun()
    else:
        result = st.session_state.get("quiz_result",{})
        score  = result.get("score_pct",0)
        color  = "#059669" if score>=80 else "#f59e0b" if score>=60 else "#e11d48"
        icon   = "🏆" if score>=80 else "👍" if score>=60 else "📖"
        st.markdown(f'<div class="sm-score" style="border:1px solid {color}44;background:rgba(0,0,0,.3);"><div class="sm-score-n" style="color:{color};">{score:.1f}%</div><div class="sm-score-l">{icon} {"Excellent!" if score>=80 else "Good effort!" if score>=60 else "Keep practising!"}</div><div class="sm-score-sub">✅ {result.get("correct",0)} correct · ❌ {result.get("wrong",0)} wrong · {len(st.session_state.get("quiz_questions",[]))} total</div></div>', unsafe_allow_html=True)
        if result.get("weak_topics"): st.markdown(f'<div class="sm-info">📌 Weak areas: <strong>{", ".join(result["weak_topics"])}</strong> — logged to Dashboard.</div>', unsafe_allow_html=True)
        if st.button("🆕 New Quiz", use_container_width=True):
            for k in ["quiz_questions","quiz_answers","quiz_submitted","quiz_result"]: st.session_state.pop(k,None)
            st.rerun()

with tab_hist:
    history = st.session_state.get("quiz_history",[])
    if not history:
        st.markdown('<div class="sm-empty"><div class="sm-empty-ico">📊</div><div class="sm-empty-title">No history yet</div></div>', unsafe_allow_html=True)
    else:
        s = quiz_history_stats(history)
        st.markdown(f'<div class="sm-stats"><div class="sm-stat"><span class="sm-stat-n">{s["attempts"]}</span><span class="sm-stat-l">Attempts</span></div><div class="sm-stat"><span class="sm-stat-n">{s["avg_score"]}%</span><span class="sm-stat-l">Avg</span></div><div class="sm-stat"><span class="sm-stat-n" style="color:#6ee7b7">{s["best"]}%</span><span class="sm-stat-l">Best</span></div></div>', unsafe_allow_html=True)
        for h in reversed(history):
            sc = h["score"]; col = "#6ee7b7" if sc>=80 else "#fcd34d" if sc>=60 else "#fda4af"
            st.markdown(f'<div class="sm-day"><div class="sm-day-num">{h.get("date","")}</div><div class="sm-day-topic">📋 {h.get("topic","General")} · {h.get("num_questions",0)}q</div><div class="sm-day-meta" style="color:{col};font-weight:700;font-size:15px;">{sc}%</div></div>', unsafe_allow_html=True)