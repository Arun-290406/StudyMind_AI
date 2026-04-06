# app/pages/05_study_plan.py  — FIXED (no backslash inside f-strings)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from datetime import date, timedelta
import streamlit as st
from utils.session_state import init_session_state
from features.study_planner import generate_study_plan, mark_day_complete, get_today_plan, plan_progress
init_session_state()

st.markdown('<div class="sm-page-title">Study Plan</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">AI-scheduled exam roadmap — adapts to quiz weak areas and your availability</div>', unsafe_allow_html=True)

if not st.session_state.docs_indexed:
    st.markdown('<div class="sm-empty"><div class="sm-empty-ico">📅</div><div class="sm-empty-title">Index documents first</div></div>', unsafe_allow_html=True)
    st.stop()

SCOLORS = {"learn": "#8b5cf6", "review": "#06b6d4", "practice": "#f59e0b", "mock_test": "#f43f5e"}
SICONS  = {"learn": "📖", "review": "🔄", "practice": "✏️", "mock_test": "📝"}
PCOLS   = {"high": "#f43f5e", "medium": "#f59e0b", "low": "#10b981"}

if not st.session_state.study_plan:
    st.markdown('<div class="sm-highlight"><div class="sm-highlight-title">Create Your Study Plan</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    exam_date   = c1.date_input("📅 Exam Date", value=date.today() + timedelta(days=14))
    daily_hours = c2.slider("⏰ Daily hours", 0.5, 8.0, 2.0, step=0.5)
    focus       = c3.text_input("📌 Extra focus", placeholder="e.g. weak in algorithms")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.weak_topics:
        weak_str = ", ".join(st.session_state.weak_topics)
        st.markdown(
            f'<div class="sm-info">📊 Quiz weak areas: <strong>{weak_str}</strong> — these get extra sessions.</div>',
            unsafe_allow_html=True
        )

    if st.button("📅  Generate Study Plan", use_container_width=True):
        if exam_date <= date.today():
            st.error("Exam date must be in the future.")
        else:
            weak = list(st.session_state.weak_topics)
            if focus:
                weak.append(focus)
            with st.spinner("Building your personalized study roadmap…"):
                plan = generate_study_plan(
                    st.session_state.vector_store,
                    exam_date=exam_date,
                    daily_hours=daily_hours,
                    weak_topics=weak
                )
            st.session_state.study_plan = plan
            st.session_state.exam_date  = exam_date
            st.rerun()
else:
    plan = st.session_state.study_plan
    prog = plan_progress(plan)

    # Stats
    st.markdown(f"""
    <div class="sm-stats">
      <div class="sm-stat"><span class="sm-stat-n">{prog['total_days']}</span><span class="sm-stat-l">Total Days</span></div>
      <div class="sm-stat"><span class="sm-stat-n" style="color:#6ee7b7">{prog['completed_days']}</span><span class="sm-stat-l">Done</span></div>
      <div class="sm-stat"><span class="sm-stat-n" style="color:var(--vl)">{prog['remaining_days']}</span><span class="sm-stat-l">Remaining</span></div>
      <div class="sm-stat"><span class="sm-stat-n">{prog['progress_pct']}%</span><span class="sm-stat-l">Progress</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(prog["progress_pct"] / 100)

    if not prog["on_track"] and prog["completed_days"] > 0:
        st.warning("⚠️ Behind schedule — try increasing your daily study hours.")
    elif prog["progress_pct"] > 0:
        st.success("✅ On track! Keep going.")

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

    # Today hero
    today_plan = get_today_plan(plan)
    if today_plan and not today_plan.get("completed"):
        stype = today_plan.get("session_type", "learn")
        color = SCOLORS.get(stype, "#8b5cf6")
        icon  = SICONS.get(stype, "📖")
        dur   = today_plan.get("duration_min", 60)
        stype_label = stype.replace("_", " ").title()
        day_num = today_plan.get("day", "")
        topic   = today_plan.get("topic", "")

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{color}14,{color}07);
                    border:1px solid {color}44; border-radius:20px;
                    padding:1.6rem 1.8rem; margin-bottom:1.5rem; position:relative; overflow:hidden;">
          <div style="position:absolute;top:-30px;right:-30px;width:120px;height:120px;
                      background:{color}18;border-radius:50%;"></div>
          <div style="font-size:10.5px;font-weight:800;letter-spacing:0.1em;text-transform:uppercase;
                      color:{color};margin-bottom:0.4rem;">Today · Day {day_num}</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.35rem;font-weight:800;
                      color:#f1f5f9;margin-bottom:0.7rem;">{icon} {topic}</div>
        """, unsafe_allow_html=True)

        for t in today_plan.get("tasks", []):
            st.markdown(
                f'<div style="color:#94a3b8;font-size:13.5px;margin-bottom:3px;">→ {t}</div>',
                unsafe_allow_html=True
            )

        st.markdown(
            f'<div style="font-size:11px;color:#475569;margin-top:0.5rem;">'
            f'{dur} min · {stype_label}</div></div>',
            unsafe_allow_html=True
        )

        if st.button("✅  Mark Today Complete", use_container_width=True):
            st.session_state.study_plan = mark_day_complete(plan, today_plan["day"])
            st.rerun()

    # Full schedule
    st.markdown('<p class="sm-lbl">Full Schedule</p>', unsafe_allow_html=True)

    for day in plan:
        done     = day.get("completed", False)
        is_today = day.get("real_date") == date.today().isoformat()
        stype    = day.get("session_type", "learn")
        icon     = SICONS.get(stype, "📖")
        prio     = day.get("priority", "medium")
        prio_col = PCOLS.get(prio, "#8b5cf6")
        dur      = day.get("duration_min", 60)
        check    = "✅" if done else ("▶" if is_today else "○")
        day_num  = day.get("day", "")
        day_date = day.get("date", "")
        topic    = day.get("topic", "")

        with st.expander(f"{check}  Day {day_num} — {day_date} · {icon} {topic}", expanded=is_today):
            c1, c2 = st.columns([4, 1])
            with c1:
                for task in day.get("tasks", []):
                    txt = f"~~{task}~~" if done else task
                    st.markdown(f"- {txt}")
            with c2:
                prio_upper = prio.upper()
                st.markdown(
                    f'<div style="text-align:right;">'
                    f'<span style="color:{prio_col};font-size:10px;font-weight:700;">{prio_upper}</span>'
                    f'<br><span style="color:#475569;font-size:11px;">{dur} min</span></div>',
                    unsafe_allow_html=True
                )
            if not done:
                if st.button("Mark Complete", key=f"dc_{day_num}"):
                    st.session_state.study_plan = mark_day_complete(plan, day["day"])
                    st.rerun()

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
    if st.button("🔄  Regenerate Plan", use_container_width=True):
        st.session_state.study_plan = []
        st.rerun()