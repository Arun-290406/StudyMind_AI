# app/main.py — StudyMind AI Pro (Final)
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st

st.set_page_config(
    page_title="StudyMind AI Pro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth.auth_manager import is_logged_in, logout, current_user
from auth.auth_page    import show_auth_page

if not is_logged_in():
    show_auth_page()
    st.stop()

from app.theme import inject_theme
from utils.session_state import init_session_state, flush_notifications, get_overall_progress
from core.vector_store import delete_vector_store
from analytics.tracker import start_session, end_session

inject_theme()
init_session_state()
user   = current_user()
stats  = get_overall_progress()
active = st.session_state.get("active_page", "Home")

# Start analytics session
if "session_id" not in st.session_state:
    uid = user.get("id", 0)
    if uid:
        st.session_state["session_id"]    = start_session(uid, "General")
        st.session_state["session_start"] = time.time()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sm-logo-wrap">
      <div class="sm-logo-name">StudyMind <span class="sm-ai-pill">PRO</span></div>
      <div class="sm-logo-sub">RAG · Analytics · Voice · Email</div>
    </div>""", unsafe_allow_html=True)

    initials = "".join(w[0].upper() for w in user["name"].split()[:2]) if user["name"] else "ST"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;
                background:rgba(124,58,237,.08);border:1px solid rgba(124,58,237,.22);
                border-radius:12px;margin-bottom:10px;">
      <div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;
                  background:linear-gradient(135deg,#7c3aed,#0891b2);
                  display:flex;align-items:center;justify-content:center;
                  font-family:Syne,sans-serif;font-weight:800;font-size:13px;color:#fff;">
        {initials}</div>
      <div style="min-width:0;">
        <div style="font-size:13px;font-weight:600;color:#f8fafc;">{user["name"]}</div>
        <div style="font-size:10.5px;color:#334155;overflow:hidden;text-overflow:ellipsis;
                    white-space:nowrap;max-width:145px;">{user["email"]}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.docs_indexed:
        n = len(st.session_state.uploaded_files)
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:7px 12px;background:rgba(5,150,105,.08);border:1px solid rgba(5,150,105,.24);border-radius:10px;margin-bottom:4px;"><span class="sm-pulse"></span><span style="font-size:12px;color:#6ee7b7;font-weight:600;">{n} doc{"s" if n!=1 else ""} indexed</span></div>', unsafe_allow_html=True)
        if st.button("🗑️  Clear Index", use_container_width=True, key="sb_clr"):
            delete_vector_store(); st.session_state.vector_store=None; st.session_state.docs_indexed=False; st.session_state.uploaded_files=[]; st.session_state.chat_history=[]; st.rerun()
    else:
        st.markdown('<div style="display:flex;align-items:center;gap:8px;padding:7px 12px;background:rgba(217,119,6,.08);border:1px solid rgba(217,119,6,.24);border-radius:10px;margin-bottom:10px;"><span style="width:7px;height:7px;background:#d97706;border-radius:50%;flex-shrink:0;"></span><span style="font-size:12px;color:#fcd34d;font-weight:600;">No documents indexed</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sm-lbl" style="padding:0 4px;">Core</p>', unsafe_allow_html=True)
    for icon, label in [("🏠","Home"),("🔍","Ask Notes"),("🃏","Flashcards"),("📝","Quiz Me"),("📋","Summary"),("📅","Study Plan"),("🗺️","Mind Map")]:
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.active_page=label; st.rerun()

    st.markdown('<div class="sm-div" style="margin:.4rem 0;"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sm-lbl" style="padding:0 4px;">Pro Features</p>', unsafe_allow_html=True)
    for icon, label in [("📊","Dashboard"),("🎤","Voice"),("🧪","Smart Quiz"),("📂","Multi-Doc"),("📥","Exports")]:
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.active_page=label; st.rerun()

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sm-lbl" style="padding:0 4px;">Session</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="sm-stats"><div class="sm-stat"><span class="sm-stat-n">{stats["docs_uploaded"]}</span><span class="sm-stat-l">Docs</span></div><div class="sm-stat"><span class="sm-stat-n">{stats["total_flashcards"]}</span><span class="sm-stat-l">Cards</span></div><div class="sm-stat"><span class="sm-stat-n">{stats["quiz_attempts"]}</span><span class="sm-stat-l">Quizzes</span></div><div class="sm-stat"><span class="sm-stat-n" style="font-size:1.05rem">{stats["avg_quiz_score"]}%</span><span class="sm-stat-l">Avg</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
    if st.button("🚪  Sign Out", use_container_width=True, key="btn_lo"):
        if "session_id" in st.session_state and "session_start" in st.session_state:
            dur = (time.time() - st.session_state["session_start"]) / 60
            end_session(st.session_state["session_id"], dur)
        logout(); st.rerun()
    st.markdown('<p style="font-size:10px;color:#1e293b;text-align:center;padding-top:5px;">SQLite · FAISS · LangChain · Streamlit</p>', unsafe_allow_html=True)

# ── ROUTING ────────────────────────────────────────────────────────────────────
flush_notifications()
base = os.path.dirname(os.path.abspath(__file__))
PAGE_MAP = {
    "Ask Notes":  "pages/01_ask_notes.py",
    "Flashcards": "pages/02_flashcards.py",
    "Quiz Me":    "pages/03_quiz.py",
    "Summary":    "pages/04_summary.py",
    "Study Plan": "pages/05_study_plan.py",
    "Mind Map":   "pages/06_mind_map.py",
    "Dashboard":  "pages/07_dashboard.py",
    "Voice":      "pages/08_voice.py",
    "Smart Quiz": "pages/09_smart_quiz.py",
    "Multi-Doc":  "pages/10_multi_doc.py",
    "Exports":    "pages/11_exports.py",
}

if active == "Home":
    first = user["name"].split()[0] if user["name"] else "Student"
    st.markdown(f'<div class="sm-page-title">Welcome back, {first}! 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="sm-page-sub">StudyMind AI Pro — analytics, voice, multi-doc chat, email notifications</div>', unsafe_allow_html=True)

    if not st.session_state.docs_indexed:
        st.markdown('<div style="background:linear-gradient(135deg,rgba(124,58,237,.1),rgba(8,145,178,.06));border:1px solid rgba(124,58,237,.28);border-radius:20px;padding:1.8rem 2.2rem;margin-bottom:2rem;position:relative;overflow:hidden;"><div style="position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(124,58,237,.65),transparent);"></div><div style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;color:#f8fafc;margin-bottom:.5rem;">🚀 Get started in 3 steps</div><div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:.8rem;"><span style="background:rgba(124,58,237,.18);border:1px solid rgba(124,58,237,.32);border-radius:10px;padding:7px 14px;font-size:13px;color:#a78bfa;font-weight:600;">1️⃣ Upload PDF / DOCX / TXT</span><span style="background:rgba(8,145,178,.12);border:1px solid rgba(8,145,178,.28);border-radius:10px;padding:7px 14px;font-size:13px;color:#67e8f9;font-weight:600;">2️⃣ Click Index Documents</span><span style="background:rgba(5,150,105,.12);border:1px solid rgba(5,150,105,.28);border-radius:10px;padding:7px 14px;font-size:13px;color:#6ee7b7;font-weight:600;">3️⃣ Ask Anything!</span></div></div>', unsafe_allow_html=True)
        if st.button("📁 Upload & Index Now →", key="home_upload"): st.session_state.active_page="Ask Notes"; st.rerun()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Documents",stats["docs_uploaded"]); c2.metric("Flashcards",stats["total_flashcards"]); c3.metric("Quizzes",stats["quiz_attempts"]); c4.metric("Avg Score",f"{stats['avg_quiz_score']}%")
    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

    st.markdown('<p style="font-family:Syne,sans-serif;font-size:1rem;font-weight:800;color:#f8fafc;margin-bottom:.6rem;">✨ Core Features</p>', unsafe_allow_html=True)
    feats1 = [("🔍","Ask Your Notes","RAG Q&A with page citations","Ask Notes"),("🃏","Flashcards","SM-2 spaced repetition","Flashcards"),("📝","Quiz Me","MCQs with explanations","Quiz Me"),("📋","Summary","AI document summaries","Summary"),("📅","Study Plan","AI exam schedule","Study Plan"),("🗺️","Mind Map","Knowledge graph","Mind Map")]
    r1, r2 = st.columns(3), st.columns(3)
    for i,(ico,ttl,dsc,pg) in enumerate(feats1):
        with (r1 if i<3 else r2)[i%3]:
            st.markdown(f'<div class="sm-feat"><span class="sm-feat-ico">{ico}</span><div class="sm-feat-title">{ttl}</div><div class="sm-feat-desc">{dsc}</div></div>', unsafe_allow_html=True)
            if st.button("Open →", key=f"hf_{pg}", use_container_width=True): st.session_state.active_page=pg; st.rerun()

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-family:Syne,sans-serif;font-size:1rem;font-weight:800;color:#f8fafc;margin-bottom:.6rem;">⭐ Pro Features</p>', unsafe_allow_html=True)
    feats2 = [("📊","Analytics Dashboard","Study time · accuracy · weak areas","Dashboard"),("🎤","Voice Assistant","Ask by voice · hear answers","Voice"),("🧪","Smart Quiz","Exam mode · timer · negative marks","Smart Quiz"),("📂","Multi-Doc Chat","Chat per PDF with auto-tagging","Multi-Doc"),("📥","PDF Export","Download summaries & flashcards","Exports")]
    r3, r4 = st.columns(3), st.columns(3)
    for i,(ico,ttl,dsc,pg) in enumerate(feats2):
        col = r3[i%3] if i<3 else r4[i%3]
        with col:
            st.markdown(f'<div class="sm-feat" style="border-color:rgba(8,145,178,.2);"><span class="sm-feat-ico">{ico}</span><div class="sm-feat-title">{ttl}</div><div class="sm-feat-desc">{dsc}</div></div>', unsafe_allow_html=True)
            if st.button("Open →", key=f"hf2_{pg}", use_container_width=True): st.session_state.active_page=pg; st.rerun()

elif active in PAGE_MAP:
    path = os.path.join(base, PAGE_MAP[active])
    try:
        with open(path, encoding="utf-8") as f: exec(f.read(), {"__file__": path})
    except FileNotFoundError: st.error(f"Page not found: `{path}`")
    except SyntaxError as e: st.error(f"Syntax error: {e}"); st.code(str(e))
    except Exception as e: st.error(f"Error: {e}"); st.exception(e)