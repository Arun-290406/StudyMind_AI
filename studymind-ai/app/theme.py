# app/theme.py — StudyMind AI Design System v4
"""
Deep-space aurora glassmorphism.
Fonts: Syne 800 (headings) + Plus Jakarta Sans (body)
"""

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

:root{
  --v:#7c3aed;--vl:#a78bfa;--vd:#4c1d95;
  --c:#0891b2;--cl:#67e8f9;
  --em:#059669;--rose:#e11d48;--amb:#d97706;
  --t1:#f8fafc;--t2:#94a3b8;--t3:#334155;--t4:#1e293b;
  --glass:rgba(255,255,255,0.038);--gb:rgba(124,58,237,0.2);
  --r8:8px;--r12:12px;--r16:16px;--r20:20px;--r24:24px;
}

#MainMenu,footer,header{visibility:hidden}
html,body,[class*="css"]{font-family:'Plus Jakarta Sans',sans-serif!important;color:var(--t1)!important}
.main .block-container{padding:1.8rem 2.4rem 4rem!important;max-width:1320px!important}

/* Aurora background */
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(ellipse 1000px 700px at 5% 0%,rgba(124,58,237,.18) 0%,transparent 65%),
    radial-gradient(ellipse 800px 600px at 95% 100%,rgba(8,145,178,.14) 0%,transparent 60%),
    radial-gradient(ellipse 600px 800px at 55% 45%,rgba(76,29,149,.08) 0%,transparent 65%),
    linear-gradient(180deg,#030712 0%,#080d1e 60%,#030712 100%)!important;
  background-attachment:fixed!important;
}
[data-testid="stAppViewContainer"]::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:
    linear-gradient(rgba(124,58,237,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(124,58,237,.04) 1px,transparent 1px);
  background-size:52px 52px;
}

/* Sidebar */
[data-testid="stSidebar"]{
  background:rgba(3,7,18,.93)!important;
  backdrop-filter:blur(32px) saturate(180%)!important;
  border-right:1px solid rgba(124,58,237,.18)!important;
  box-shadow:6px 0 56px rgba(0,0,0,.65)!important;
}
[data-testid="stSidebar"]>div:first-child{padding-top:0!important}

/* Text inputs */
.stTextInput input,.stTextArea textarea{
  background:rgba(8,13,30,.88)!important;
  border:1px solid rgba(124,58,237,.26)!important;
  border-radius:var(--r12)!important;color:var(--t1)!important;
  font-family:'Plus Jakarta Sans',sans-serif!important;font-size:14px!important;
  transition:border-color .22s,box-shadow .22s!important;
}
.stTextInput input:focus,.stTextArea textarea:focus{
  border-color:rgba(124,58,237,.72)!important;
  box-shadow:0 0 0 3px rgba(124,58,237,.13),0 0 28px rgba(124,58,237,.07)!important;
}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#1e293b!important}
.stTextInput label,.stTextArea label{color:var(--t2)!important;font-size:12.5px!important;font-weight:600!important}

/* Buttons */
.stButton>button{
  font-family:'Plus Jakarta Sans',sans-serif!important;font-weight:700!important;
  font-size:13.5px!important;border-radius:var(--r12)!important;border:none!important;
  padding:.55rem 1.3rem!important;
  background:linear-gradient(135deg,#7c3aed 0%,#4c1d95 100%)!important;
  color:#fff!important;letter-spacing:.01em!important;
  box-shadow:0 4px 18px rgba(124,58,237,.4),inset 0 1px 0 rgba(255,255,255,.12)!important;
  transition:transform .2s,box-shadow .2s,filter .2s!important;
}
.stButton>button:hover{
  transform:translateY(-2px)!important;filter:brightness(1.08)!important;
  box-shadow:0 8px 28px rgba(124,58,237,.55)!important;
}
.stButton>button:active{transform:translateY(0)!important}
.stButton>button[kind="secondary"]{
  background:rgba(124,58,237,.1)!important;
  border:1px solid rgba(124,58,237,.3)!important;
  color:var(--vl)!important;box-shadow:none!important;
}

/* Chat input */
[data-testid="stChatInput"]{
  background:rgba(8,13,30,.92)!important;
  border:1px solid rgba(124,58,237,.3)!important;
  border-radius:100px!important;
}
[data-testid="stChatInput"]:focus-within{
  border-color:rgba(124,58,237,.65)!important;
  box-shadow:0 0 0 3px rgba(124,58,237,.12)!important;
}
[data-testid="stChatInput"] textarea{color:var(--t1)!important;background:transparent!important}
[data-testid="stChatInput"] button{
  background:linear-gradient(135deg,#7c3aed,#4c1d95)!important;
  border-radius:50%!important;width:36px!important;height:36px!important;
  box-shadow:0 2px 12px rgba(124,58,237,.5)!important;
}

/* File uploader */
[data-testid="stFileUploader"]{
  background:rgba(124,58,237,.03)!important;
  border:2px dashed rgba(124,58,237,.32)!important;
  border-radius:var(--r16)!important;transition:all .25s!important;
}
[data-testid="stFileUploader"]:hover{
  background:rgba(124,58,237,.07)!important;border-color:rgba(124,58,237,.58)!important;
}

/* Progress */
.stProgress>div>div{background:rgba(124,58,237,.12)!important;border-radius:100px!important;height:6px!important}
.stProgress>div>div>div>div{
  background:linear-gradient(90deg,#7c3aed,#0891b2)!important;
  border-radius:100px!important;box-shadow:0 0 12px rgba(124,58,237,.5)!important;
}

/* Metrics */
[data-testid="stMetric"]{
  background:var(--glass)!important;border:1px solid var(--gb)!important;
  border-radius:var(--r16)!important;padding:1.2rem 1.4rem!important;
  transition:transform .25s,box-shadow .25s,border-color .25s!important;
}
[data-testid="stMetric"]:hover{
  transform:translateY(-3px)!important;border-color:rgba(124,58,237,.4)!important;
  box-shadow:0 8px 32px rgba(124,58,237,.15)!important;
}
[data-testid="stMetricValue"]{font-family:'Syne',sans-serif!important;font-size:2rem!important;font-weight:800!important;color:var(--vl)!important}
[data-testid="stMetricLabel"]{font-size:11px!important;text-transform:uppercase!important;letter-spacing:.09em!important;color:var(--t2)!important}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"]{
  background:rgba(8,13,30,.7)!important;
  border:1px solid rgba(124,58,237,.18)!important;
  border-radius:var(--r12)!important;padding:4px!important;gap:2px!important;
}
[data-testid="stTabs"] [data-baseweb="tab"]{
  background:transparent!important;border:none!important;border-radius:var(--r8)!important;
  color:var(--t2)!important;font-family:'Plus Jakarta Sans',sans-serif!important;
  font-weight:600!important;font-size:13px!important;padding:.45rem 1.1rem!important;transition:all .2s!important;
}
[data-testid="stTabs"] [aria-selected="true"]{
  background:linear-gradient(135deg,rgba(124,58,237,.32),rgba(8,145,178,.15))!important;
  color:var(--t1)!important;box-shadow:0 2px 14px rgba(124,58,237,.25)!important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:transparent!important}

/* Expander */
[data-testid="stExpander"]{
  background:var(--glass)!important;border:1px solid var(--gb)!important;
  border-radius:var(--r12)!important;overflow:hidden!important;
}
[data-testid="stExpander"]:hover{border-color:rgba(124,58,237,.35)!important}
[data-testid="stExpander"] summary{color:var(--t1)!important;font-weight:600!important;font-size:14px!important}

/* Select */
[data-baseweb="select"]>div:first-child{
  background:rgba(8,13,30,.88)!important;
  border:1px solid rgba(124,58,237,.26)!important;
  border-radius:var(--r12)!important;color:var(--t1)!important;
}

/* Chat messages */
[data-testid="stChatMessage"]{
  background:var(--glass)!important;border:1px solid var(--gb)!important;
  border-radius:var(--r16)!important;transition:border-color .2s!important;
}
[data-testid="stChatMessage"]:hover{border-color:rgba(124,58,237,.32)!important}

/* Misc */
hr{border:none!important;border-top:1px solid rgba(124,58,237,.15)!important}
[data-testid="stAlert"]{border-radius:var(--r12)!important;border:none!important}
[data-testid="stRadio"] label{color:var(--t1)!important;font-family:'Plus Jakarta Sans',sans-serif!important}
[data-testid="stCheckbox"] label{color:var(--t1)!important;font-family:'Plus Jakarta Sans',sans-serif!important}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:rgba(8,13,30,.4);border-radius:10px}
::-webkit-scrollbar-thumb{background:rgba(124,58,237,.42);border-radius:10px}

/* ═══════════════════════════════════════════════════════════════════
   CUSTOM COMPONENT CLASSES
   ═══════════════════════════════════════════════════════════════════ */

/* Page header */
.sm-page-title{
  font-family:'Syne',sans-serif;font-size:2.4rem;font-weight:800;line-height:1.12;
  background:linear-gradient(120deg,#f8fafc 20%,#a78bfa 55%,#67e8f9 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  margin-bottom:.3rem;letter-spacing:-.02em;
}
.sm-page-sub{color:var(--t2);font-size:.93rem;margin-bottom:1.8rem;line-height:1.6}

/* Glass card */
.sm-card{
  background:var(--glass);border:1px solid var(--gb);border-radius:var(--r20);
  padding:1.6rem;position:relative;overflow:hidden;
  transition:border-color .28s,box-shadow .28s,transform .28s;
}
.sm-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(124,58,237,.55),transparent);
}
.sm-card:hover{border-color:rgba(124,58,237,.38);box-shadow:0 8px 40px rgba(124,58,237,.12);transform:translateY(-2px)}

/* Stats grid */
.sm-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin:1rem 0}
.sm-stat{
  background:var(--glass);border:1px solid var(--gb);border-radius:var(--r16);
  padding:.95rem;text-align:center;transition:all .25s;position:relative;overflow:hidden;
}
.sm-stat::after{
  content:'';position:absolute;bottom:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,#7c3aed,#0891b2);
  transform:scaleX(0);transition:transform .28s;border-radius:2px;
}
.sm-stat:hover{border-color:rgba(124,58,237,.38);transform:translateY(-3px);box-shadow:0 8px 24px rgba(124,58,237,.12)}
.sm-stat:hover::after{transform:scaleX(1)}
.sm-stat-n{font-family:'Syne',sans-serif;font-size:1.75rem;font-weight:800;color:var(--vl);display:block}
.sm-stat-l{font-size:10px;color:var(--t2);text-transform:uppercase;letter-spacing:.09em;display:block;margin-top:2px}

/* Badges */
.sm-badge{display:inline-block;padding:3px 10px;border-radius:100px;
  font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}
.badge-v{background:rgba(124,58,237,.18);color:#a78bfa;border:1px solid rgba(124,58,237,.3)}
.badge-c{background:rgba(8,145,178,.14);color:#67e8f9;border:1px solid rgba(8,145,178,.28)}
.badge-em{background:rgba(5,150,105,.14);color:#6ee7b7;border:1px solid rgba(5,150,105,.28)}
.badge-r{background:rgba(225,29,72,.14);color:#fda4af;border:1px solid rgba(225,29,72,.28)}
.badge-a{background:rgba(217,119,6,.14);color:#fcd34d;border:1px solid rgba(217,119,6,.28)}

/* Divider */
.sm-div{height:1px;border:none;
  background:linear-gradient(90deg,transparent,rgba(124,58,237,.4),transparent);
  margin:1.4rem 0}

/* Labels */
.sm-lbl{font-size:10.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:var(--t3);margin-bottom:.5rem;font-family:'Plus Jakarta Sans',sans-serif}

/* Info panels */
.sm-info{background:rgba(124,58,237,.07);border-left:3px solid var(--v);
  border-radius:0 var(--r12) var(--r12) 0;padding:.9rem 1.1rem;margin:.8rem 0}

/* TL;DR */
.sm-tldr{background:linear-gradient(135deg,rgba(124,58,237,.09),rgba(8,145,178,.05));
  border:1px solid rgba(124,58,237,.22);border-radius:var(--r12);padding:1rem 1.2rem;margin-bottom:1.2rem}
.sm-tldr-lbl{font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;
  color:var(--vl);margin-bottom:.4rem}

/* File chips */
.sm-chip{display:inline-flex;align-items:center;gap:6px;
  background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.22);
  border-radius:8px;padding:4px 11px;font-size:12px;color:var(--t1);margin:3px}

/* Empty states */
.sm-empty{text-align:center;padding:4rem 2rem}
.sm-empty-ico{font-size:3.5rem;margin-bottom:1rem;filter:grayscale(.2)}
.sm-empty-title{font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:var(--t1);margin-bottom:.4rem}
.sm-empty-sub{font-size:.87rem;color:var(--t2)}

/* Sidebar elements */
.sm-logo-wrap{padding:1.4rem 1.1rem 1rem;border-bottom:1px solid rgba(124,58,237,.18);margin-bottom:1rem}
.sm-logo-name{font-family:'Syne',sans-serif;font-size:1.45rem;font-weight:800;
  background:linear-gradient(135deg,#f8fafc,#a78bfa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.sm-logo-sub{font-size:10.5px;color:var(--t3);margin-top:2px;letter-spacing:.04em}
.sm-ai-pill{display:inline-block;
  background:linear-gradient(135deg,rgba(124,58,237,.32),rgba(8,145,178,.22));
  border:1px solid rgba(124,58,237,.44);color:#a78bfa;
  font-size:9px;font-weight:800;padding:2px 7px;border-radius:100px;
  margin-left:5px;vertical-align:middle;letter-spacing:.08em;font-family:'Syne',sans-serif}

.sm-pulse{display:inline-block;width:7px;height:7px;background:#059669;border-radius:50%;
  animation:pulse 2.2s ease-out infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(5,150,105,.65)}
  70%{box-shadow:0 0 0 9px rgba(5,150,105,0)}100%{box-shadow:0 0 0 0 rgba(5,150,105,0)}}

/* Feature cards for homepage */
.sm-feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:1.5rem 0}
.sm-feat{background:var(--glass);border:1px solid var(--gb);border-radius:var(--r16);
  padding:1.4rem;transition:all .25s;cursor:default;position:relative;overflow:hidden}
.sm-feat::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(124,58,237,.45),transparent)}
.sm-feat:hover{border-color:rgba(124,58,237,.38);transform:translateY(-3px);
  box-shadow:0 8px 32px rgba(124,58,237,.12)}
.sm-feat-ico{font-size:1.8rem;margin-bottom:.7rem;display:block}
.sm-feat-title{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
  color:var(--t1);margin-bottom:.3rem}
.sm-feat-desc{font-size:12px;color:var(--t3);line-height:1.5}

/* Flashcard */
.sm-fc{background:var(--glass);border:1px solid var(--gb);border-radius:var(--r24);
  padding:2.8rem 2rem;text-align:center;min-height:230px;
  display:flex;align-items:center;justify-content:center;flex-direction:column;
  position:relative;overflow:hidden;transition:all .3s}
.sm-fc::before{content:'';position:absolute;inset:0;
  background:conic-gradient(from 0deg at 50% 50%,transparent 0deg,rgba(124,58,237,.06) 60deg,
    transparent 120deg,rgba(8,145,178,.04) 180deg,transparent 240deg,rgba(124,58,237,.06) 300deg,transparent 360deg);
  animation:fc-spin 10s linear infinite}
@keyframes fc-spin{to{transform:rotate(360deg)}}
.sm-fc:hover{border-color:rgba(124,58,237,.42);box-shadow:0 0 40px rgba(124,58,237,.12)}
.sm-fc-q{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;color:var(--t1);
  line-height:1.55;position:relative;z-index:1}
.sm-fc-hint{font-size:11px;color:var(--t3);text-transform:uppercase;letter-spacing:.08em;
  margin-top:.8rem;position:relative;z-index:1}

/* Score banner */
.sm-score{border-radius:var(--r24);padding:2.5rem;text-align:center;
  position:relative;overflow:hidden;margin-bottom:1.5rem}
.sm-score::before{content:'';position:absolute;inset:-50%;
  background:conic-gradient(from 0deg,transparent 0%,rgba(124,58,237,.12) 25%,
    rgba(8,145,178,.08) 50%,rgba(124,58,237,.12) 75%,transparent 100%);
  animation:score-spin 8s linear infinite}
@keyframes score-spin{to{transform:rotate(360deg)}}
.sm-score-n{font-family:'Syne',sans-serif;font-size:4.5rem;font-weight:800;position:relative;z-index:1;line-height:1}
.sm-score-l{font-size:1rem;color:var(--t2);position:relative;z-index:1;margin-top:.4rem}
.sm-score-sub{font-size:12px;color:var(--t3);position:relative;z-index:1;margin-top:.3rem}

/* Day plan */
.sm-day{background:rgba(255,255,255,.025);border:1px solid var(--gb);border-radius:var(--r12);
  padding:.85rem 1.1rem;margin-bottom:6px;display:flex;align-items:center;gap:12px;transition:all .2s}
.sm-day:hover{border-color:rgba(124,58,237,.32);transform:translateX(4px)}
.sm-day.today{border-color:rgba(124,58,237,.5);box-shadow:0 0 24px rgba(124,58,237,.1)}
.sm-day-num{font-size:10px;font-weight:700;color:var(--t3);text-transform:uppercase;
  letter-spacing:.06em;min-width:30px}
.sm-day-topic{font-size:14px;font-weight:500;color:var(--t1);flex:1}
.sm-day-meta{font-size:11px;color:var(--t3)}

/* Highlight box */
.sm-highlight{background:linear-gradient(135deg,rgba(124,58,237,.08),rgba(8,145,178,.04));
  border:1px solid rgba(124,58,237,.22);border-radius:var(--r16);padding:1.3rem 1.5rem;margin-bottom:1.2rem}
.sm-highlight-title{font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;color:var(--t1);margin-bottom:.9rem}
</style>
"""
def inject_theme() -> None:
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)