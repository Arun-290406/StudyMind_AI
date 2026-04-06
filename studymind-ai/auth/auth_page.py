# auth/auth_page.py
"""
StudyMind AI — Login & Register Page
  - Mobile number field in Create Account tab
  - SMS login notification when user signs in
  - Email domain restricted to @gmail.com and @skct.edu.in
  - Password strength bar
  - Success ✅ / Fail ❌ feedback
"""

import re
import streamlit as st
from auth.auth_manager import register_user, login_user, set_logged_in

AUTH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Plus Jakarta Sans',sans-serif!important;color:#f8fafc!important}
#MainMenu,footer,header{visibility:hidden}
.main .block-container{padding:0!important;max-width:100%!important}
[data-testid="stSidebar"]{display:none!important}
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(ellipse 1100px 700px at 0% 0%,rgba(124,58,237,.22) 0%,transparent 65%),
    radial-gradient(ellipse 800px 600px at 100% 100%,rgba(8,145,178,.18) 0%,transparent 60%),
    radial-gradient(ellipse 600px 800px at 55% 45%,rgba(76,29,149,.1) 0%,transparent 65%),
    linear-gradient(160deg,#030712 0%,#080d1e 55%,#030712 100%)!important;
  background-attachment:fixed!important;
}
[data-testid="stAppViewContainer"]::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:linear-gradient(rgba(124,58,237,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(124,58,237,.04) 1px,transparent 1px);
  background-size:50px 50px;
}
.stTextInput input{
  background:rgba(3,7,18,.88)!important;border:1.5px solid rgba(124,58,237,.28)!important;
  border-radius:13px!important;color:#f8fafc!important;
  font-family:'Plus Jakarta Sans',sans-serif!important;
  font-size:14.5px!important;padding:.72rem 1rem!important;
  transition:border-color .22s,box-shadow .22s!important;
}
.stTextInput input:focus{
  border-color:rgba(124,58,237,.75)!important;
  box-shadow:0 0 0 3px rgba(124,58,237,.14),0 0 28px rgba(124,58,237,.07)!important;
}
.stTextInput input::placeholder{color:#1e293b!important}
.stTextInput label{color:#94a3b8!important;font-size:12.5px!important;font-weight:600!important;letter-spacing:.02em!important}
.stButton>button{
  font-family:'Plus Jakarta Sans',sans-serif!important;font-weight:700!important;
  font-size:15px!important;border-radius:13px!important;border:none!important;
  width:100%!important;padding:.82rem!important;letter-spacing:.02em!important;
  background:linear-gradient(135deg,#7c3aed 0%,#4c1d95 100%)!important;color:#fff!important;
  box-shadow:0 6px 24px rgba(124,58,237,.45),inset 0 1px 0 rgba(255,255,255,.14)!important;
  transition:transform .2s,box-shadow .2s,filter .2s!important;
}
.stButton>button:hover{transform:translateY(-2px)!important;filter:brightness(1.1)!important;box-shadow:0 10px 32px rgba(124,58,237,.58)!important;}
.stButton>button:active{transform:translateY(0)!important}
[data-testid="stTabs"] [data-baseweb="tab-list"]{background:rgba(3,7,18,.85)!important;border:1px solid rgba(124,58,237,.24)!important;border-radius:14px!important;padding:5px!important;gap:4px!important;}
[data-testid="stTabs"] [data-baseweb="tab"]{background:transparent!important;border:none!important;border-radius:11px!important;color:#64748b!important;font-family:'Plus Jakarta Sans',sans-serif!important;font-weight:700!important;font-size:14px!important;padding:.52rem 2rem!important;transition:all .22s!important;}
[data-testid="stTabs"] [aria-selected="true"]{background:linear-gradient(135deg,rgba(124,58,237,.38),rgba(76,29,149,.28))!important;color:#f8fafc!important;box-shadow:0 2px 16px rgba(124,58,237,.3),inset 0 1px 0 rgba(255,255,255,.08)!important;}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:transparent!important}
[data-testid="stCheckbox"] label{color:#334155!important;font-size:13px!important}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:rgba(124,58,237,.45);border-radius:4px}
</style>
"""

HERO_HTML = """
<div style="padding:2.5rem 0 2rem;">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:2.8rem;">
    <div style="width:52px;height:52px;border-radius:16px;flex-shrink:0;
                background:linear-gradient(135deg,#7c3aed,#0891b2);
                display:flex;align-items:center;justify-content:center;
                font-size:24px;position:relative;overflow:hidden;
                box-shadow:0 0 0 1px rgba(124,58,237,.45),0 8px 28px rgba(124,58,237,.45);">
      &#129504;
      <div style="position:absolute;top:0;left:0;right:0;height:52%;
                  background:rgba(255,255,255,.2);border-radius:16px 16px 0 0;"></div>
    </div>
    <div>
      <div style="font-family:'Syne',sans-serif;font-size:1.55rem;font-weight:800;
                  background:linear-gradient(120deg,#f8fafc,#a78bfa 55%,#67e8f9);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text;">StudyMind AI</div>
      <div style="font-size:10.5px;color:#334155;letter-spacing:.09em;text-transform:uppercase;margin-top:2px;">
        Powered by RAG + Vector Search</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:.9rem;">
    <div style="width:26px;height:2.5px;background:linear-gradient(90deg,#7c3aed,#0891b2);border-radius:3px;"></div>
    <span style="font-size:11.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#a78bfa;">Your AI Study Partner</span>
  </div>
  <h1 style="font-family:'Syne',sans-serif;font-size:2.75rem;font-weight:800;line-height:1.08;letter-spacing:-.03em;margin-bottom:1rem;">
    Study smarter,<br>
    <span style="background:linear-gradient(120deg,#f8fafc 10%,#a78bfa 50%,#67e8f9 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">not harder.</span>
  </h1>
  <p style="color:#64748b;font-size:.95rem;line-height:1.72;margin-bottom:2.2rem;max-width:400px;">
    Upload your notes, get instant cited answers, generate smart quizzes, build flashcards — all powered by AI.
  </p>
  <div style="display:flex;flex-direction:column;gap:9px;margin-bottom:2rem;">
    <div style="display:flex;align-items:center;gap:12px;padding:11px 14px;background:rgba(255,255,255,.028);border:1px solid rgba(124,58,237,.15);border-radius:13px;">
      <div style="width:34px;height:34px;border-radius:9px;flex-shrink:0;background:rgba(124,58,237,.18);border:1px solid rgba(124,58,237,.3);display:flex;align-items:center;justify-content:center;font-size:15px;">&#128269;</div>
      <div><div style="font-size:13px;font-weight:600;color:#f8fafc;">Ask Your Notes</div><div style="font-size:11.5px;color:#334155;">RAG Q&amp;A with page citations</div></div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;padding:11px 14px;background:rgba(255,255,255,.028);border:1px solid rgba(8,145,178,.15);border-radius:13px;">
      <div style="width:34px;height:34px;border-radius:9px;flex-shrink:0;background:rgba(8,145,178,.14);border:1px solid rgba(8,145,178,.28);display:flex;align-items:center;justify-content:center;font-size:15px;">&#127183;</div>
      <div><div style="font-size:13px;font-weight:600;color:#f8fafc;">Smart Flashcards</div><div style="font-size:11.5px;color:#334155;">SM-2 spaced repetition</div></div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;padding:11px 14px;background:rgba(255,255,255,.028);border:1px solid rgba(5,150,105,.15);border-radius:13px;">
      <div style="width:34px;height:34px;border-radius:9px;flex-shrink:0;background:rgba(5,150,105,.14);border:1px solid rgba(5,150,105,.28);display:flex;align-items:center;justify-content:center;font-size:15px;">&#128220;</div>
      <div><div style="font-size:13px;font-weight:600;color:#f8fafc;">Smart Quiz + Dashboard</div><div style="font-size:11.5px;color:#334155;">MCQs · Analytics · Voice · PDF Export</div></div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:7px;">
    <div style="background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.22);border-radius:11px;padding:.65rem;text-align:center;">
      <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:#a78bfa;">RAG</div>
      <div style="font-size:9.5px;color:#334155;text-transform:uppercase;letter-spacing:.07em;margin-top:1px;">Retrieval</div>
    </div>
    <div style="background:rgba(8,145,178,.08);border:1px solid rgba(8,145,178,.2);border-radius:11px;padding:.65rem;text-align:center;">
      <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:#67e8f9;">FAISS</div>
      <div style="font-size:9.5px;color:#334155;text-transform:uppercase;letter-spacing:.07em;margin-top:1px;">Vectors</div>
    </div>
    <div style="background:rgba(5,150,105,.08);border:1px solid rgba(5,150,105,.2);border-radius:11px;padding:.65rem;text-align:center;">
      <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:#6ee7b7;">SQLite</div>
      <div style="font-size:9.5px;color:#334155;text-transform:uppercase;letter-spacing:.07em;margin-top:1px;">Auth DB</div>
    </div>
    <div style="background:rgba(217,119,6,.08);border:1px solid rgba(217,119,6,.2);border-radius:11px;padding:.65rem;text-align:center;">
      <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:#fcd34d;">SMS</div>
      <div style="font-size:9.5px;color:#334155;text-transform:uppercase;letter-spacing:.07em;margin-top:1px;">Notify</div>
    </div>
  </div>
</div>
"""

CARD_OPEN = """
<div style="background:rgba(8,13,30,.9);border:1px solid rgba(124,58,237,.32);
            border-radius:26px;padding:2.4rem 2.6rem 2rem;position:relative;overflow:hidden;
            box-shadow:0 0 0 1px rgba(124,58,237,.07),0 32px 72px rgba(0,0,0,.6);">
  <div style="position:absolute;top:0;left:0;right:0;height:1px;
              background:linear-gradient(90deg,transparent,rgba(124,58,237,.85),rgba(8,145,178,.6),transparent);"></div>
  <div style="position:absolute;top:-80px;right:-80px;width:200px;height:200px;border-radius:50%;pointer-events:none;
              background:radial-gradient(circle,rgba(124,58,237,.1) 0%,transparent 70%);"></div>
"""
CARD_CLOSE = "</div>"


def _domain_pills() -> str:
    return (
        '<div style="display:flex;gap:6px;margin-top:5px;margin-bottom:2px;">'
        '<span style="font-size:10.5px;font-weight:700;padding:2px 9px;border-radius:100px;'
        'background:rgba(124,58,237,.14);color:#a78bfa;border:1px solid rgba(124,58,237,.28);">@gmail.com</span>'
        '<span style="font-size:10.5px;font-weight:700;padding:2px 9px;border-radius:100px;'
        'background:rgba(8,145,178,.12);color:#67e8f9;border:1px solid rgba(8,145,178,.26);">@skct.edu.in</span>'
        '</div>'
    )


def _pw_strength(pw: str) -> str:
    if not pw:
        return ""
    s = sum([
        len(pw) >= 8,
        bool(re.search(r"[A-Z]", pw)),
        bool(re.search(r"\d", pw)),
        bool(re.search(r"[^A-Za-z0-9]", pw)),
    ])
    cols  = ["#e11d48","#f59e0b","#0891b2","#059669"]
    lbls  = ["Weak","Fair","Good","Strong"]
    col   = cols[s-1] if s else "#1e293b"
    lbl   = lbls[s-1] if s else ""
    bars  = "".join(
        f'<div style="flex:1;height:3px;border-radius:2px;'
        f'background:{""+col if i<s else "#0d1326"};transition:background .3s;"></div>'
        for i in range(4)
    )
    return (
        f'<div style="margin:6px 0 10px;">'
        f'<div style="display:flex;gap:3px;margin-bottom:4px;">{bars}</div>'
        f'<span style="font-size:11.5px;font-weight:700;color:{col};">{lbl}</span>'
        f'</div>'
    )


def _sms_status_badge() -> str:
    """Show SMS configuration status as a small badge."""
    try:
        from notifications.sms_sender import sms_configured, sms_provider_name
        if sms_configured():
            return (
                f'<div style="display:inline-flex;align-items:center;gap:5px;'
                f'background:rgba(5,150,105,.1);border:1px solid rgba(5,150,105,.28);'
                f'border-radius:100px;padding:3px 10px;font-size:11px;color:#6ee7b7;'
                f'font-weight:600;margin-top:5px;">'
                f'✅ SMS via {sms_provider_name()} active</div>'
            )
        else:
            return (
                '<div style="display:inline-flex;align-items:center;gap:5px;'
                'background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.25);'
                'border-radius:100px;padding:3px 10px;font-size:11px;color:#fcd34d;'
                'font-weight:600;margin-top:5px;">'
                '⚠️ SMS not configured — configure in .env</div>'
            )
    except Exception:
        return ""


def show_auth_page() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown("<div style='padding:2rem 2rem 0;'>", unsafe_allow_html=True)

    col_hero, col_form = st.columns([1.15, 1], gap="large")

    # ── LEFT HERO ─────────────────────────────────────────────────────────────
    with col_hero:
        st.markdown(HERO_HTML, unsafe_allow_html=True)

    # ── RIGHT AUTH CARD ───────────────────────────────────────────────────────
    with col_form:
        st.markdown(CARD_OPEN, unsafe_allow_html=True)

        tab_li, tab_rg = st.tabs(["🔑  Sign In", "✨  Create Account"])

        # ════════════════════════════════════
        # SIGN IN
        # ════════════════════════════════════
        with tab_li:
            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

            # Login feedback
            ls = st.session_state.get("_li_state", "")
            lm = st.session_state.get("_li_msg",   "")
            if ls == "success":
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:.9rem 1.1rem;
                            background:rgba(5,150,105,.12);border:1.5px solid rgba(5,150,105,.4);
                            border-radius:13px;margin-bottom:1rem;animation:slideIn .35s ease;">
                  <span style="font-size:22px;">✅</span>
                  <div>
                    <div style="font-weight:700;color:#6ee7b7;font-size:14px;">Login Successful!</div>
                    <div style="font-size:12px;color:#34d399;margin-top:1px;">{lm}</div>
                  </div>
                </div>
                <style>@keyframes slideIn{{from{{opacity:0;transform:translateY(-8px)}}to{{opacity:1;transform:none}}}}</style>
                """, unsafe_allow_html=True)
            elif ls == "failed":
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:.9rem 1.1rem;
                            background:rgba(225,29,72,.1);border:1.5px solid rgba(225,29,72,.4);
                            border-radius:13px;margin-bottom:1rem;animation:shake .35s ease;">
                  <span style="font-size:22px;">❌</span>
                  <div>
                    <div style="font-weight:700;color:#fda4af;font-size:14px;">Login Failed</div>
                    <div style="font-size:12px;color:#fb7185;margin-top:1px;">{lm}</div>
                  </div>
                </div>
                <style>@keyframes shake{{0%,100%{{transform:translateX(0)}}20%{{transform:translateX(-7px)}}40%{{transform:translateX(7px)}}60%{{transform:translateX(-4px)}}80%{{transform:translateX(4px)}}}}</style>
                """, unsafe_allow_html=True)

            li_email = st.text_input("Email address", key="li_email",
                                     placeholder="you@gmail.com  or  you@skct.edu.in")
            st.markdown(_domain_pills(), unsafe_allow_html=True)

            li_pw = st.text_input("Password", key="li_password",
                                  placeholder="Your password", type="password")
            st.checkbox("Keep me signed in for 30 days", key="li_remember")
            st.markdown("<div style='height:.15rem'></div>", unsafe_allow_html=True)

            if st.button("Sign In  →", key="btn_login", use_container_width=True):
                st.session_state["_li_state"] = ""
                st.session_state["_li_msg"]   = ""
                if not li_email.strip() or not li_pw:
                    st.session_state["_li_state"] = "failed"
                    st.session_state["_li_msg"]   = "Please fill in both fields."
                    st.rerun()
                else:
                    with st.spinner("Verifying…"):
                        ok, msg, user = login_user(li_email, li_pw)
                    if ok:
                        st.session_state["_li_state"] = "success"
                        st.session_state["_li_msg"]   = f"Welcome back, {user.get('name','Student')}!"
                        set_logged_in(user)
                        import time; time.sleep(0.5)
                        st.rerun()
                    else:
                        st.session_state["_li_state"] = "failed"
                        st.session_state["_li_msg"]   = msg
                        st.rerun()

            st.markdown(
                '<p style="text-align:center;font-size:12.5px;color:#334155;margin-top:1rem;">'
                'No account? Switch to <strong style="color:#a78bfa;">Create Account</strong> tab.</p>',
                unsafe_allow_html=True,
            )

        # ════════════════════════════════════
        # CREATE ACCOUNT
        # ════════════════════════════════════
        with tab_rg:
            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

            # Register feedback
            rs = st.session_state.get("_rg_state", "")
            rm = st.session_state.get("_rg_msg",   "")
            if rs == "success":
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:.9rem 1.1rem;
                            background:rgba(5,150,105,.12);border:1.5px solid rgba(5,150,105,.4);
                            border-radius:13px;margin-bottom:1rem;">
                  <span style="font-size:22px;">🎉</span>
                  <div>
                    <div style="font-weight:700;color:#6ee7b7;font-size:14px;">Account Created!</div>
                    <div style="font-size:12px;color:#34d399;margin-top:1px;">{rm}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
                st.balloons()
            elif rs == "failed":
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:.9rem 1.1rem;
                            background:rgba(225,29,72,.1);border:1.5px solid rgba(225,29,72,.4);
                            border-radius:13px;margin-bottom:1rem;">
                  <span style="font-size:22px;">❌</span>
                  <div>
                    <div style="font-weight:700;color:#fda4af;font-size:14px;">Registration Failed</div>
                    <div style="font-size:12px;color:#fb7185;margin-top:1px;">{rm}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

            # Name row
            c1, c2 = st.columns(2)
            fn = c1.text_input("First name", key="rg_fn", placeholder="Arjun")
            ln = c2.text_input("Last name",  key="rg_ln", placeholder="Kumar")

            # Email
            rg_email = st.text_input("Email address", key="rg_email",
                                     placeholder="you@gmail.com  or  you@skct.edu.in")
            st.markdown(_domain_pills(), unsafe_allow_html=True)

            # Mobile number — NEW FIELD
            rg_mobile = st.text_input(
                "📱 Mobile number (for SMS alerts)",
                key="rg_mobile",
                placeholder="9876543210  or  +919876543210",
            )
            st.markdown(_sms_status_badge(), unsafe_allow_html=True)

            # Password
            rg_pw = st.text_input("Password", key="rg_pw",
                                  placeholder="Min 8 chars, include a number",
                                  type="password")
            if rg_pw:
                st.markdown(_pw_strength(rg_pw), unsafe_allow_html=True)

            rg_cf = st.text_input("Confirm password", key="rg_cf",
                                  placeholder="Repeat your password", type="password")
            terms = st.checkbox("I agree to the Terms of Service & Privacy Policy",
                                key="rg_terms")
            st.markdown("<div style='height:.15rem'></div>", unsafe_allow_html=True)

            if st.button("Create Account  →", key="btn_register", use_container_width=True):
                st.session_state["_rg_state"] = ""
                st.session_state["_rg_msg"]   = ""
                if not terms:
                    st.session_state["_rg_state"] = "failed"
                    st.session_state["_rg_msg"]   = "Please accept the Terms of Service."
                    st.rerun()
                else:
                    full_name = f"{fn.strip()} {ln.strip()}".strip()
                    with st.spinner("Creating your account…"):
                        ok, msg = register_user(
                            full_name, rg_email, rg_pw, rg_cf,
                            mobile=rg_mobile,
                        )
                    if ok:
                        st.session_state["_rg_state"] = "success"
                        st.session_state["_rg_msg"]   = msg
                        st.rerun()
                    else:
                        st.session_state["_rg_state"] = "failed"
                        st.session_state["_rg_msg"]   = msg
                        st.rerun()

            st.markdown(
                '<p style="text-align:center;font-size:12px;color:#334155;margin-top:1rem;">'
                'Already have an account? Switch to <strong style="color:#a78bfa;">Sign In</strong>.</p>',
                unsafe_allow_html=True,
            )
        st.markdown(CARD_CLOSE, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)