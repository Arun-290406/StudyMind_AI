# app/pages/07_dashboard.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, timedelta, datetime
from utils.session_state import init_session_state
from auth.auth_manager import current_user
from analytics.tracker import (
    get_dashboard_summary, get_study_time_by_day,
    get_quiz_accuracy_by_topic, get_weak_areas,
    get_topics_covered, get_flashcard_stats
)

init_session_state()
user = current_user()
uid  = user.get("id", 0)

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown('<div class="sm-page-title">📊 Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sm-page-sub">Welcome back, <strong>{user["name"].split()[0]}</strong> — '
    f'here\'s your complete learning analytics</div>',
    unsafe_allow_html=True
)

summary = get_dashboard_summary(uid)

# ── KPI CARDS ─────────────────────────────────────────────────────────────────
def kpi_card(icon, value, label, color, delta=""):
    delta_html = f'<div style="font-size:11px;color:{color};opacity:.75;margin-top:2px;">{delta}</div>' if delta else ""
    return f"""
    <div style="background:rgba(255,255,255,.038);border:1px solid {color}33;
                border-radius:18px;padding:1.3rem 1.1rem;text-align:center;
                position:relative;overflow:hidden;transition:all .25s;">
      <div style="position:absolute;top:0;left:0;right:0;height:3px;
                  background:linear-gradient(90deg,{color},{color}88);"></div>
      <div style="font-size:1.9rem;margin-bottom:.3rem;">{icon}</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.85rem;font-weight:800;
                  color:{color};line-height:1;">{value}</div>
      <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;
                  letter-spacing:.09em;margin-top:4px;">{label}</div>
      {delta_html}
    </div>"""

study_hrs  = round(summary["total_study_min"] / 60, 1)
avg_score  = summary["avg_score"]
score_col  = "#059669" if avg_score >= 80 else "#d97706" if avg_score >= 60 else "#e11d48"

k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(kpi_card("⏱️", f"{study_hrs}h", "Study Time", "#a78bfa"), unsafe_allow_html=True)
k2.markdown(kpi_card("📝", summary["total_quizzes"], "Quizzes Taken", "#67e8f9"), unsafe_allow_html=True)
k3.markdown(kpi_card("🎯", f"{avg_score}%", "Avg Quiz Score", score_col), unsafe_allow_html=True)
k4.markdown(kpi_card("🧠", summary["topics_covered"], "Topics Covered", "#6ee7b7"), unsafe_allow_html=True)
k5.markdown(kpi_card("🔥", f"{summary['streak_days']}d", "Study Streak", "#fcd34d"), unsafe_allow_html=True)

st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

# ── CHART HELPERS ─────────────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    plot_bgcolor="rgba(8,13,30,.7)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Plus Jakarta Sans"),
    margin=dict(l=0, r=0, t=16, b=0),
)

# ── ROW 1: Study time + Flashcard confidence ──────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown(
        '<p style="font-family:Syne,sans-serif;font-weight:800;font-size:.97rem;'
        'color:#f8fafc;margin-bottom:.5rem;">📈 Study Time — Last 14 Days</p>',
        unsafe_allow_html=True
    )
    time_data = get_study_time_by_day(uid, days=14)

    if time_data:
        df = pd.DataFrame(time_data)
        # Fill in missing days
        all_days = [(date.today() - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
        df_full  = pd.DataFrame({"day": all_days})
        df_full  = df_full.merge(df, on="day", how="left").fillna(0)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_full["day"], y=df_full["minutes"],
            marker=dict(
                color=df_full["minutes"],
                colorscale=[[0,"#4c1d95"],[0.4,"#7c3aed"],[1,"#a78bfa"]],
                line=dict(width=0),
            ),
            hovertemplate="%{y:.0f} min<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=df_full["day"], y=df_full["minutes"],
            mode="lines", line=dict(color="#67e8f9", width=1.5, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))
        fig.update_layout(
            **CHART_LAYOUT,
            height=240,
            xaxis=dict(gridcolor="rgba(124,58,237,.08)", tickfont_size=10,
                       tickangle=-30, showline=False),
            yaxis=dict(gridcolor="rgba(124,58,237,.08)", title="Minutes",
                       titlefont_size=11),
            bargap=0.3,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            '<div class="sm-empty" style="padding:2rem"><div class="sm-empty-ico">📈</div>'
            '<div class="sm-empty-title">No sessions yet</div>'
            '<div class="sm-empty-sub">Start a session to track your time.</div></div>',
            unsafe_allow_html=True
        )

with col_right:
    st.markdown(
        '<p style="font-family:Syne,sans-serif;font-weight:800;font-size:.97rem;'
        'color:#f8fafc;margin-bottom:.5rem;">🃏 Flashcard Confidence</p>',
        unsafe_allow_html=True
    )
    fc = get_flashcard_stats(uid)
    if fc["total_reviews"] > 0:
        by_r   = fc["by_rating"]
        labels = ["Forgot", "Hard", "OK", "Easy"]
        values = [by_r.get(0, 0), by_r.get(1, 0), by_r.get(3, 0), by_r.get(5, 0)]
        colors = ["#e11d48", "#f59e0b", "#0891b2", "#059669"]
        fig2 = go.Figure(go.Pie(
            labels=labels, values=values, hole=.6,
            marker=dict(colors=colors, line=dict(width=2, color="rgba(8,13,30,.9)")),
            textfont_size=11,
        ))
        fig2.update_layout(
            **CHART_LAYOUT, height=240,
            showlegend=True,
            legend=dict(font=dict(size=11, color="#94a3b8"),
                        bgcolor="rgba(0,0,0,0)", x=1, y=.5),
            annotations=[dict(
                text=f"<b>{fc['good_rate']}%</b><br>Good",
                font=dict(size=13, color="#a78bfa"), showarrow=False
            )],
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            '<div class="sm-empty" style="padding:2rem"><div class="sm-empty-ico">🃏</div>'
            '<div class="sm-empty-title">Review flashcards to see data</div></div>',
            unsafe_allow_html=True
        )

st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

# ── ROW 2: Quiz accuracy + Weak areas ─────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.markdown(
        '<p style="font-family:Syne,sans-serif;font-weight:800;font-size:.97rem;'
        'color:#f8fafc;margin-bottom:.5rem;">📊 Quiz Accuracy by Topic</p>',
        unsafe_allow_html=True
    )
    quiz_data = get_quiz_accuracy_by_topic(uid)
    if quiz_data:
        df2 = pd.DataFrame(quiz_data)
        df2["avg_score"] = df2["avg_score"].round(1)
        bar_colors = [
            "#059669" if s >= 80 else "#f59e0b" if s >= 60 else "#e11d48"
            for s in df2["avg_score"]
        ]
        fig3 = go.Figure(go.Bar(
            x=df2["avg_score"], y=df2["topic"], orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"{v}%" for v in df2["avg_score"]],
            textposition="outside",
            textfont=dict(size=11, color="#94a3b8"),
            hovertemplate="%{y}: %{x}%<extra></extra>",
        ))
        fig3.update_layout(
            **CHART_LAYOUT,
            height=max(220, len(quiz_data) * 40),
            xaxis=dict(range=[0, 110], gridcolor="rgba(124,58,237,.08)",
                       title="Score %", titlefont_size=11),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", automargin=True),
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            '<div class="sm-empty" style="padding:2rem"><div class="sm-empty-ico">📊</div>'
            '<div class="sm-empty-title">Take quizzes to see accuracy</div></div>',
            unsafe_allow_html=True
        )

with col_b:
    st.markdown(
        '<p style="font-family:Syne,sans-serif;font-weight:800;font-size:.97rem;'
        'color:#f8fafc;margin-bottom:.5rem;">❌ Weak Areas (Most Missed)</p>',
        unsafe_allow_html=True
    )
    weak = get_weak_areas(uid, limit=7)
    if weak:
        max_miss = max(w["miss_count"] for w in weak) or 1
        for w in weak:
            pct = round(w["miss_count"] / max_miss * 100)
            last = w.get("last_missed", "")[:10] if w.get("last_missed") else ""
            st.markdown(f"""
            <div style="background:rgba(225,29,72,.07);border:1px solid rgba(225,29,72,.2);
                        border-radius:11px;padding:10px 14px;margin-bottom:7px;">
              <div style="display:flex;justify-content:space-between;align-items:center;
                          margin-bottom:5px;">
                <span style="font-size:13px;font-weight:600;color:#fda4af;">
                  {w["topic"]}</span>
                <span style="font-size:11px;color:#e11d48;font-weight:700;
                             background:rgba(225,29,72,.12);padding:2px 8px;
                             border-radius:100px;">{w["miss_count"]}× missed</span>
              </div>
              <div style="height:4px;background:rgba(225,29,72,.12);border-radius:2px;">
                <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#e11d48,#fb7185);
                            border-radius:2px;transition:width .4s;"></div>
              </div>
              {"" if not last else f'<div style="font-size:10.5px;color:#475569;margin-top:4px;">Last: {last}</div>'}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="sm-empty" style="padding:2rem"><div class="sm-empty-ico">✅</div>'
            '<div class="sm-empty-title">No weak areas detected!</div>'
            '<div class="sm-empty-sub">Take quizzes to identify gaps.</div></div>',
            unsafe_allow_html=True
        )

st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

# ── ROW 3: Topics + Send report ───────────────────────────────────────────────
col_t, col_r = st.columns([3, 2])

with col_t:
    st.markdown(
        '<p style="font-family:Syne,sans-serif;font-weight:800;font-size:.97rem;'
        'color:#f8fafc;margin-bottom:.6rem;">🧠 Topics Covered</p>',
        unsafe_allow_html=True
    )
    topics = get_topics_covered(uid)
    if topics:
        topic_colors = ["#a78bfa","#67e8f9","#6ee7b7","#fcd34d","#fda4af","#f9a8d4"]
        chips = "".join(
            f'<span style="display:inline-block;margin:3px;padding:5px 13px;'
            f'border-radius:100px;background:{topic_colors[i%len(topic_colors)]}18;'
            f'color:{topic_colors[i%len(topic_colors)]};'
            f'border:1px solid {topic_colors[i%len(topic_colors)]}38;'
            f'font-size:12.5px;font-weight:600;">{t}</span>'
            for i, t in enumerate(topics)
        )
        st.markdown(chips, unsafe_allow_html=True)
    else:
        st.markdown(
            '<p style="color:#334155;font-size:13px;">Start studying to track topics.</p>',
            unsafe_allow_html=True
        )

with col_r:
    st.markdown(
        '<p style="font-family:Syne,sans-serif;font-weight:800;font-size:.97rem;'
        'color:#f8fafc;margin-bottom:.6rem;">📧 Email Report</p>',
        unsafe_allow_html=True
    )
    from notifications.email_sender import email_configured
    if email_configured():
        st.markdown(
            '<div style="background:rgba(5,150,105,.08);border:1px solid rgba(5,150,105,.24);'
            'border-radius:11px;padding:.7rem 1rem;font-size:13px;color:#6ee7b7;margin-bottom:.8rem;">'
            '✅ Email notifications are active</div>',
            unsafe_allow_html=True
        )
        if st.button("📧 Send Weekly Report Now", use_container_width=True):
            from notifications.email_sender import send_weekly_report
            send_weekly_report(
                user["email"], user["name"],
                {
                    "study_min":   summary["total_study_min"],
                    "quizzes":     summary["total_quizzes"],
                    "avg_score":   summary["avg_score"],
                    "topics":      summary["topics_covered"],
                    "flashcards":  fc.get("total_reviews", 0) if "fc" in dir() else 0,
                    "streak":      summary["streak_days"],
                }
            )
            st.success("✅ Report sent to your email!")
    else:
        st.markdown(
            '<div style="background:rgba(217,119,6,.08);border:1px solid rgba(217,119,6,.22);'
            'border-radius:11px;padding:.7rem 1rem;font-size:13px;color:#fcd34d;margin-bottom:.8rem;">'
            '⚠️ Configure SMTP in .env to enable email reports</div>',
            unsafe_allow_html=True
        )
        with st.expander("How to enable email?"):
            st.code("""# In your .env file:
SMTP_SENDER=youremail@gmail.com
SMTP_PASSWORD=your-16-char-app-password

# Gmail setup:
# 1. Enable 2-Factor Auth
# 2. Google Account → Security → App Passwords
# 3. Generate password for "Mail"
# 4. Paste 16-char password above""", language="bash")