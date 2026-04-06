# app/pages/09_smart_quiz.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import time
from datetime import datetime
from utils.session_state import init_session_state
from auth.auth_manager import current_user
from features.quiz_gen import generate_mcq_quiz, evaluate_mcq, EXAM_CONFIGS
from analytics.tracker import log_weak_area
init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown('<div class="sm-page-title">🧪 Smart Quiz</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">Exam Mode · Speed Round · Mock Test · Negative Marking · Timer</div>', unsafe_allow_html=True)

if not st.session_state.docs_indexed:
    st.markdown("""
    <div style="background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.25);
                border-radius:14px;padding:1.5rem 2rem;text-align:center;">
      <div style="font-size:2rem;margin-bottom:.5rem;">📁</div>
      <div style="font-weight:700;color:#fcd34d;font-size:15px;">Index documents first</div>
      <div style="font-size:13px;color:#64748b;margin-top:.3rem;">
        Go to Ask Notes → upload your PDFs → click Index All</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Colour helpers ─────────────────────────────────────────────────────────────
MODE_COLORS  = {
    "practice": ("rgba(8,145,178,.15)",  "rgba(8,145,178,.4)"),
    "exam":     ("rgba(225,29,72,.15)",  "rgba(225,29,72,.4)"),
    "speed":    ("rgba(245,158,11,.15)", "rgba(245,158,11,.4)"),
    "mock":     ("rgba(124,58,237,.15)", "rgba(124,58,237,.4)"),
}

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — SETUP (no questions yet)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.get("sq_questions"):

    # ── Config bar ───────────────────────────────────────────────────────────
    st.markdown('<div class="sm-highlight"><div class="sm-highlight-title">Configure Your Quiz</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    topic  = c1.text_input("Topic focus (optional)", placeholder="e.g. Compiler Design")
    num_q  = c2.slider("Number of questions", 3, 20, 5)
    diff   = c3.selectbox("Difficulty", ["medium", "easy", "hard"])
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Mode cards ───────────────────────────────────────────────────────────
    st.markdown('<p style="font-family:Syne,sans-serif;font-weight:800;font-size:1rem;color:#f8fafc;margin-bottom:.8rem;">Select Quiz Mode</p>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    mode_cols = [col1, col2, col3, col4]

    for i, (mk, mv) in enumerate(EXAM_CONFIGS.items()):
        bg, border = MODE_COLORS.get(mk, ("rgba(124,58,237,.1)","rgba(124,58,237,.3)"))
        with mode_cols[i]:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};border-radius:14px;
                        padding:1.1rem .9rem;text-align:center;margin-bottom:6px;
                        position:relative;overflow:hidden;">
              <div style="position:absolute;top:0;left:0;right:0;height:2px;
                          background:{border};"></div>
              <div style="font-size:1.8rem;margin-bottom:.4rem;">{mv['icon']}</div>
              <div style="font-family:Syne,sans-serif;font-weight:800;font-size:13.5px;
                          color:#f8fafc;margin-bottom:.4rem;">{mv['label']}</div>
              <div style="font-size:11px;color:#64748b;line-height:1.5;">
                {"No timer" if mv["time_per_q"]==0 else f"⏱ {mv['time_per_q']}s / question"}<br>
                {f"📉 −{mv['negative_marks']} for wrong" if mv["negative_marks"]>0 else "✅ No penalty"}
              </div>
            </div>""", unsafe_allow_html=True)

            if st.button(f"Start {mv['icon']}", key=f"start_{mk}", use_container_width=True):
                with st.spinner(f"Generating {mv['label']}…"):
                    qs = generate_mcq_quiz(
                        st.session_state.vector_store,
                        topic=topic, num_questions=num_q, difficulty=diff,
                    )
                if qs:
                    st.session_state["sq_questions"]  = qs
                    st.session_state["sq_answers"]    = {}
                    st.session_state["sq_submitted"]  = False
                    st.session_state["sq_mode"]       = mk
                    st.session_state["sq_start"]      = time.time()
                    st.session_state["sq_q_start"]    = time.time()
                    st.rerun()
                else:
                    st.error("❌ Could not generate questions. Upload more detailed notes and try again.")

    # ── Tips ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
      <div style="background:rgba(8,145,178,.08);border:1px solid rgba(8,145,178,.2);
                  border-radius:11px;padding:.9rem;font-size:12px;color:#94a3b8;line-height:1.55;">
        <div style="font-weight:700;color:#67e8f9;margin-bottom:.3rem;">📝 Practice Mode</div>
        No time limit. No penalty. Hints shown. Best for learning new material.
      </div>
      <div style="background:rgba(225,29,72,.08);border:1px solid rgba(225,29,72,.2);
                  border-radius:11px;padding:.9rem;font-size:12px;color:#94a3b8;line-height:1.55;">
        <div style="font-weight:700;color:#fda4af;margin-bottom:.3rem;">🔥 Exam Mode</div>
        90 seconds per question. −0.25 for wrong answers. Simulates real exam pressure.
      </div>
      <div style="background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);
                  border-radius:11px;padding:.9rem;font-size:12px;color:#94a3b8;line-height:1.55;">
        <div style="font-weight:700;color:#fcd34d;margin-bottom:.3rem;">⚡ Speed Round</div>
        30 seconds per question. No penalty. Tests quick recall and fast thinking.
      </div>
      <div style="background:rgba(124,58,237,.08);border:1px solid rgba(124,58,237,.2);
                  border-radius:11px;padding:.9rem;font-size:12px;color:#94a3b8;line-height:1.55;">
        <div style="font-weight:700;color:#a78bfa;margin-bottom:.3rem;">📊 Mock Test</div>
        60 seconds per question. −1/3 penalty. Full exam simulation with scoring.
      </div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — ACTIVE QUIZ
# ══════════════════════════════════════════════════════════════════════════════
elif not st.session_state.get("sq_submitted"):
    qs     = st.session_state["sq_questions"]
    mode   = st.session_state.get("sq_mode", "practice")
    config = EXAM_CONFIGS.get(mode, EXAM_CONFIGS["practice"])
    answered = len([v for v in st.session_state["sq_answers"].values() if v])
    total    = len(qs)
    bg, border = MODE_COLORS.get(mode, ("rgba(124,58,237,.1)","rgba(124,58,237,.3)"))

    # Mode banner
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {border};border-radius:13px;
                padding:.8rem 1.3rem;display:flex;align-items:center;
                gap:12px;margin-bottom:1rem;">
      <span style="font-size:1.5rem;">{config['icon']}</span>
      <div style="flex:1;">
        <span style="font-family:Syne,sans-serif;font-weight:800;font-size:14px;
                     color:#f8fafc;">{config['label']}</span>
        <span style="font-size:12px;color:#64748b;margin-left:10px;">
          {f"⏱ {config['time_per_q']}s/question  ·  " if config['time_per_q']>0 else ""}
          {f"📉 −{config['negative_marks']} for wrong" if config['negative_marks']>0 else "No penalty"}
        </span>
      </div>
      <span style="font-size:13px;color:#a78bfa;font-weight:700;">
        {answered}/{total} answered
      </span>
    </div>""", unsafe_allow_html=True)

    # Progress bar
    st.progress(answered / total if total else 0)

    # Timer (for timed modes)
    time_pq = config["time_per_q"]
    if time_pq > 0:
        elapsed   = time.time() - st.session_state.get("sq_q_start", time.time())
        remaining = max(0.0, time_pq - elapsed)
        pct       = remaining / time_pq
        bar_col   = "#059669" if pct > 0.5 else "#f59e0b" if pct > 0.25 else "#e11d48"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin:.6rem 0;">
          <span style="font-size:13px;color:#94a3b8;font-weight:600;">⏱️ Time left:</span>
          <span style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;
                       color:{bar_col};">{remaining:.0f}s</span>
        </div>
        <div style="height:5px;background:rgba(255,255,255,.06);border-radius:3px;
                    margin-bottom:1rem;">
          <div style="width:{pct*100:.1f}%;height:100%;background:{bar_col};
                      border-radius:3px;transition:width .5s;"></div>
        </div>""", unsafe_allow_html=True)

    st.write("")

    # Questions
    for i, q in enumerate(qs):
        qid  = q.get("id", str(i))
        opts = q.get("options", {})
        if not opts:
            continue
        choices = [f"{k}) {v}" for k, v in sorted(opts.items())]

        # Find current selection index
        cur_letter = st.session_state["sq_answers"].get(qid, "")
        cur_idx    = None
        if cur_letter:
            for j, ch in enumerate(choices):
                if ch.startswith(cur_letter):
                    cur_idx = j
                    break

        st.markdown(f"""
        <div class="sm-card" style="margin-bottom:1rem;">
          <div style="font-size:10px;color:#64748b;font-weight:700;text-transform:uppercase;
                      letter-spacing:.1em;margin-bottom:.5rem;">
            Q{i+1} of {total}
            {"  ·  " + q.get("topic","") if q.get("topic") else ""}
            {"  ·  " + q.get("difficulty","").upper() if q.get("difficulty") else ""}
          </div>
          <div style="font-size:15px;font-weight:600;color:#f8fafc;
                      line-height:1.6;margin-bottom:1rem;">
            {q.get("question", "")}
          </div>""", unsafe_allow_html=True)

        sel = st.radio(
            f"answer_{qid}",
            choices,
            index=cur_idx,
            key=f"sq_r_{qid}",
            label_visibility="collapsed",
        )
        if sel:
            st.session_state["sq_answers"][qid] = sel[0]  # store letter only

        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    # Submit + Cancel buttons
    can_submit = len([v for v in st.session_state["sq_answers"].values() if v]) == total
    col_sub, col_can = st.columns([4, 1])

    with col_sub:
        if st.button("✅  Submit Quiz", use_container_width=True,
                     disabled=not can_submit, key="sq_submit_btn"):
            result = evaluate_mcq(qs, st.session_state["sq_answers"], mode=mode)
            st.session_state["sq_result"]    = result
            st.session_state["sq_submitted"] = True
            # Log weak areas to analytics
            for t in result.get("weak_topics", []):
                if uid:
                    log_weak_area(uid, t)
            # Save to session quiz history
            if "quiz_history" not in st.session_state:
                st.session_state["quiz_history"] = []
            st.session_state["quiz_history"].append({
                "date":          datetime.now().strftime("%b %d, %H:%M"),
                "score":         result["score_pct"],
                "topic":         qs[0].get("topic", "General") if qs else "General",
                "num_questions": total,
                "mode":          mode,
            })
            st.rerun()

    with col_can:
        if st.button("🔄 Cancel", use_container_width=True, key="sq_cancel"):
            for k in ["sq_questions","sq_answers","sq_submitted","sq_mode","sq_result","sq_start","sq_q_start"]:
                st.session_state.pop(k, None)
            st.rerun()

    if not can_submit:
        st.markdown(
            f'<p style="text-align:center;font-size:12.5px;color:#475569;margin-top:.5rem;">'
            f'Answer all {total} questions to submit.</p>',
            unsafe_allow_html=True
        )

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
else:
    result = st.session_state.get("sq_result", {})
    mode   = result.get("mode", "practice")
    config = EXAM_CONFIGS.get(mode, EXAM_CONFIGS["practice"])
    score  = result.get("score_pct", 0)
    bg, border = MODE_COLORS.get(mode, ("rgba(124,58,237,.1)","rgba(124,58,237,.3)"))
    color  = "#059669" if score >= 80 else "#f59e0b" if score >= 60 else "#e11d48"

    # Score banner
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {border};border-radius:24px;
                padding:2.2rem;text-align:center;margin-bottom:1.5rem;position:relative;overflow:hidden;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;background:{border};"></div>
      <div style="font-size:1rem;color:{color};font-weight:700;margin-bottom:.4rem;">
        {config['icon']} {config['label']}
      </div>
      <div style="font-family:Syne,sans-serif;font-size:4rem;font-weight:800;
                  color:{color};line-height:1;">{score:.1f}%</div>
      <div style="font-size:1.1rem;color:#94a3b8;margin-top:.5rem;">
        {"🏆 Excellent! Keep it up!" if score>=80 else "👍 Good effort!" if score>=60 else "📖 More practice needed!"}
      </div>
      <div style="font-size:13px;color:#64748b;margin-top:.6rem;">
        ✅ {result.get("correct",0)} correct &nbsp;·&nbsp;
        ❌ {result.get("wrong",0)} wrong &nbsp;·&nbsp;
        ⏭️ {result.get("skipped",0)} skipped &nbsp;·&nbsp;
        {result.get("total",0)} total
        {f"&nbsp;·&nbsp; Raw score: {result.get('raw_score',0):.2f}/{result.get('max_score',0):.0f}" if config["negative_marks"]>0 else ""}
      </div>
    </div>""", unsafe_allow_html=True)

    # Weak areas alert
    if result.get("weak_topics"):
        topics_str = ", ".join(result["weak_topics"])
        st.markdown(f"""
        <div style="background:rgba(225,29,72,.08);border:1px solid rgba(225,29,72,.22);
                    border-radius:12px;padding:.9rem 1.2rem;margin-bottom:1rem;">
          <span style="font-weight:700;color:#fda4af;">📌 Weak areas detected:</span>
          <span style="color:#94a3b8;font-size:13.5px;"> {topics_str}</span>
          <span style="font-size:12px;color:#475569;"> — logged to your Dashboard.</span>
        </div>""", unsafe_allow_html=True)

    # PDF download
    try:
        from features.pdf_export import export_quiz_pdf
        pdf_bytes = export_quiz_pdf(
            st.session_state.get("sq_questions", []),
            st.session_state.get("sq_answers", {}),
            score, topic="Smart Quiz Results", user_name=user.get("name","Student"),
        )
        st.download_button(
            "📥  Download Results as PDF", pdf_bytes,
            "smart_quiz_results.pdf", "application/pdf",
            key="sq_pdf_dl"
        )
    except Exception as e:
        st.caption(f"PDF export unavailable: {e}")

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

    # Question-by-question review
    st.markdown('<p style="font-family:Syne,sans-serif;font-weight:800;font-size:1rem;color:#f8fafc;margin-bottom:.8rem;">📋 Full Review</p>', unsafe_allow_html=True)

    for i, r in enumerate(result.get("results", [])):
        icon = "✅" if r["is_correct"] else "⏭️" if r["skipped"] else "❌"
        pts  = r.get("points", 0)
        pts_label = f"+{pts:.0f}" if pts > 0 else (f"{pts:.2f}" if pts < 0 else "0")

        with st.expander(f"{icon}  Q{i+1}. {r['question'][:70]}…  ({pts_label} pts)"):
            # Options
            for letter, text in sorted(r.get("options", {}).items()):
                is_correct = r.get("correct","") == letter
                is_chosen  = r.get("chosen","")  == letter
                if is_correct:
                    st.markdown(
                        f'<div style="background:rgba(5,150,105,.1);border:1.5px solid rgba(5,150,105,.35);'
                        f'border-radius:9px;padding:.55rem .9rem;margin:3px 0;color:#6ee7b7;">'
                        f'✅ <strong>{letter})</strong> {text}</div>',
                        unsafe_allow_html=True
                    )
                elif is_chosen:
                    st.markdown(
                        f'<div style="background:rgba(225,29,72,.09);border:1.5px solid rgba(225,29,72,.3);'
                        f'border-radius:9px;padding:.55rem .9rem;margin:3px 0;color:#fda4af;">'
                        f'❌ <strong>{letter})</strong> {text}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="padding:.45rem .9rem;margin:2px 0;color:#475569;">'
                        f'&nbsp;&nbsp;&nbsp;<strong>{letter})</strong> {text}</div>',
                        unsafe_allow_html=True
                    )

            # Explanation
            if r.get("explanation"):
                st.markdown(
                    f'<div style="background:rgba(8,145,178,.08);border-left:3px solid rgba(8,145,178,.45);'
                    f'border-radius:0 10px 10px 0;padding:.8rem 1rem;margin-top:.6rem;">'
                    f'<span style="font-size:11px;font-weight:700;color:#67e8f9;'
                    f'text-transform:uppercase;letter-spacing:.08em;">💡 Explanation</span><br>'
                    f'<span style="font-size:13.5px;color:#f8fafc;">{r["explanation"]}</span></div>',
                    unsafe_allow_html=True
                )

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

    # Action buttons
    c1, c2 = st.columns(2)
    if c1.button("🆕  New Quiz", use_container_width=True, key="sq_new"):
        for k in ["sq_questions","sq_answers","sq_submitted","sq_mode","sq_result","sq_start","sq_q_start"]:
            st.session_state.pop(k, None)
        st.rerun()

    if c2.button("🔁  Retry Same Quiz", use_container_width=True, key="sq_retry"):
        st.session_state["sq_answers"]   = {}
        st.session_state["sq_submitted"] = False
        if "sq_result" in st.session_state:
            del st.session_state["sq_result"]
        st.rerun()