# auth/auth_manager.py
"""
Authentication — with mobile number support and SMS notifications.
  - register_user() accepts mobile_number, sends welcome SMS
  - login_user()    sends login alert SMS to registered number
  - Allowed email domains: @gmail.com and @skct.edu.in
"""

import re
import streamlit as st
from typing import Tuple, Optional, Dict
from auth.database import insert_user, get_user_by_email, update_last_login

ALLOWED_DOMAINS = ("@gmail.com", "@skct.edu.in")


def _hash_pw(pw: str) -> str:
    import bcrypt
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_pw(pw: str, hashed: str) -> bool:
    import bcrypt
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _valid_email(e: str) -> Tuple[bool, str]:
    e = e.strip().lower()
    if not re.match(r"^[\w.\+\-]+@[\w\-]+\.[a-zA-Z.]{2,}$", e):
        return False, "Please enter a valid email address."
    if not any(e.endswith(d) for d in ALLOWED_DOMAINS):
        return False, "Only @gmail.com and @skct.edu.in emails are allowed."
    return True, ""


def _valid_mobile(mobile: str) -> Tuple[bool, str]:
    """
    Validate Indian mobile number.
    Accepts formats: 9876543210 / +919876543210 / 919876543210
    """
    m = mobile.strip().replace(" ", "").replace("-", "")
    if not m:
        return False, "Mobile number is required."
    # Strip country code
    if m.startswith("+91"):
        m = m[3:]
    elif m.startswith("91") and len(m) == 12:
        m = m[2:]
    if not re.match(r"^[6-9]\d{9}$", m):
        return False, "Enter a valid 10-digit Indian mobile number (starts with 6-9)."
    return True, ""


def _normalise_mobile(mobile: str) -> str:
    """Normalise to +91XXXXXXXXXX format."""
    m = mobile.strip().replace(" ", "").replace("-", "")
    if m.startswith("+91"):
        return m
    if m.startswith("91") and len(m) == 12:
        return "+" + m
    if re.match(r"^[6-9]\d{9}$", m):
        return "+91" + m
    return m


def _valid_pw(pw: str) -> Tuple[bool, str]:
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", pw):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", pw):
        return False, "Password must contain at least one number."
    return True, ""


# ── Register ──────────────────────────────────────────────────────────────────

def register_user(
    name: str,
    email: str,
    pw: str,
    confirm: str,
    mobile: str = "",
) -> Tuple[bool, str]:
    """
    Validate all fields, create account, send welcome SMS.
    Returns (success, message).
    """
    name   = name.strip()
    email  = email.strip().lower()
    mobile = mobile.strip()

    if len(name) < 2:
        return False, "Please enter your full name."

    email_ok, email_msg = _valid_email(email)
    if not email_ok:
        return False, email_msg

    if mobile:
        mob_ok, mob_msg = _valid_mobile(mobile)
        if not mob_ok:
            return False, mob_msg
        mobile = _normalise_mobile(mobile)

    pw_ok, pw_msg = _valid_pw(pw)
    if not pw_ok:
        return False, pw_msg

    if pw != confirm:
        return False, "Passwords do not match."

    if get_user_by_email(email):
        return False, "An account with this email already exists. Please sign in."

    try:
        insert_user(name, email, _hash_pw(pw), mobile)
        first = name.split()[0]

        # Welcome email (non-blocking)
        try:
            from notifications.email_sender import send_welcome_email, email_configured
            if email_configured():
                send_welcome_email(email, name)
        except Exception as e:
            print(f"[auth] Welcome email failed: {e}")

        # Welcome SMS (non-blocking)
        if mobile:
            try:
                from notifications.sms_sender import send_welcome_sms, sms_configured
                if sms_configured():
                    send_welcome_sms(mobile, name)
            except Exception as e:
                print(f"[auth] Welcome SMS failed: {e}")

        return True, f"Welcome, {first}! Your account has been created successfully."

    except Exception as exc:
        return False, f"Registration failed: {exc}"


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(email: str, pw: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Verify credentials.
    On success: sends login SMS notification to registered mobile.
    Returns (success, message, user_dict | None).
    """
    email = email.strip().lower()

    if not email or not pw:
        return False, "Email and password are required.", None

    email_ok, email_msg = _valid_email(email)
    if not email_ok:
        return False, email_msg, None

    user = get_user_by_email(email)
    if not user:
        return False, "No account found with this email.", None
    if not user.get("active", 1):
        return False, "This account has been deactivated.", None
    if not _check_pw(pw, user.get("pw_hash", "")):
        return False, "Incorrect password. Please try again.", None

    update_last_login(email)

    # Login notification email (non-blocking)
    try:
        from notifications.email_sender import send_login_notification, email_configured
        if email_configured():
            send_login_notification(email, user.get("name", "Student"))
    except Exception as e:
        print(f"[auth] Login email failed: {e}")

    # Login notification SMS (non-blocking)
    mobile = user.get("mobile_number", "")
    if mobile:
        try:
            from notifications.sms_sender import send_login_sms, sms_configured
            if sms_configured():
                send_login_sms(mobile, user.get("name", "Student"))
        except Exception as e:
            print(f"[auth] Login SMS failed: {e}")

    return True, "Signed in successfully!", user


# ── Session helpers ───────────────────────────────────────────────────────────

def set_logged_in(user: Dict) -> None:
    st.session_state["_sm_ok"]     = True
    st.session_state["_sm_name"]   = user.get("name", "Student")
    st.session_state["_sm_email"]  = user.get("email", "")
    st.session_state["_sm_uid"]    = user.get("id", 0)
    st.session_state["_sm_mobile"] = user.get("mobile_number", "")


def logout() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith("_sm_") or k in (
            "chat_history","flashcards","quiz_questions","quiz_answers",
            "quiz_submitted","quiz_result","study_plan","summaries",
            "mind_map_data","uploaded_files","vector_store","docs_indexed",
            "fc_index","fc_show_answer","weak_topics","active_page",
            "sq_questions","sq_answers","sq_submitted","sq_mode",
            "sq_result","sq_start","sq_q_start","session_id","session_start",
        ):
            st.session_state.pop(k, None)


def is_logged_in() -> bool:
    return bool(st.session_state.get("_sm_ok", False))


def current_user() -> Dict:
    return {
        "name":   st.session_state.get("_sm_name",   "Student"),
        "email":  st.session_state.get("_sm_email",  ""),
        "id":     st.session_state.get("_sm_uid",    0),
        "mobile": st.session_state.get("_sm_mobile", ""),
    }