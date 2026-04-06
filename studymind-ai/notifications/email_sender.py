# notifications/email_sender.py
"""
Email Notification System for StudyMind AI.
Sends HTML emails for: login alert, welcome, weekly report, achievement.
Uses Gmail SMTP with App Password (no OAuth required).
"""

import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

SMTP_SENDER   = os.getenv("SMTP_SENDER",   "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST     = os.getenv("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
APP_NAME      = os.getenv("APP_NAME",      "StudyMind AI")
APP_URL       = os.getenv("APP_URL",       "http://localhost:8501")


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    if not SMTP_SENDER or not SMTP_PASSWORD:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{APP_NAME} <{SMTP_SENDER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(f"{subject}\n\nOpen {APP_URL}", "plain"))
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo(); smtp.starttls()
            smtp.login(SMTP_SENDER, SMTP_PASSWORD)
            smtp.sendmail(SMTP_SENDER, to_email, msg.as_string())
        print(f"[email] Sent '{subject}' to {to_email}")
        return True
    except Exception as exc:
        print(f"[email] Failed: {exc}")
        return False


def _send_async(to_email: str, subject: str, html_body: str):
    threading.Thread(target=_send_email, args=(to_email, subject, html_body), daemon=True).start()


def _base_template(content: str) -> str:
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.12);">
<tr><td style="background:linear-gradient(135deg,#7c3aed,#4c1d95);padding:28px 36px;text-align:center;">
<div style="font-size:28px;margin-bottom:8px;">&#129504;</div>
<div style="font-size:22px;font-weight:800;color:#fff;">{APP_NAME}</div>
<div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:3px;text-transform:uppercase;letter-spacing:.08em;">Your AI Study Partner</div>
</td></tr>
<tr><td style="background:#fff;padding:36px;">{content}</td></tr>
<tr><td style="background:#f8fafc;padding:20px 36px;text-align:center;border-top:1px solid #e2e8f0;">
<p style="margin:0;font-size:12px;color:#94a3b8;">&copy; {datetime.now().year} {APP_NAME} &nbsp;&middot;&nbsp;
<a href="{APP_URL}" style="color:#7c3aed;text-decoration:none;">Open App</a></p>
</td></tr>
</table></td></tr></table></body></html>"""


def _btn(label: str, url: str) -> str:
    return f'<div style="text-align:center;margin:24px 0;"><a href="{url}" style="display:inline-block;padding:13px 32px;background:linear-gradient(135deg,#7c3aed,#4c1d95);color:#fff;font-weight:700;font-size:15px;text-decoration:none;border-radius:12px;box-shadow:0 4px 16px rgba(124,58,237,.4);">{label}</a></div>'


def send_login_notification(to_email: str, user_name: str, ip_hint: str = "") -> None:
    now = datetime.now().strftime("%d %b %Y at %H:%M")
    content = f"""
<h2 style="margin:0 0 8px;font-size:20px;font-weight:800;color:#0f172a;">&#9989; New Login Detected</h2>
<p style="margin:0 0 20px;font-size:14px;color:#475569;">Hi <strong>{user_name}</strong>, your {APP_NAME} account was just signed in.</p>
<div style="background:#f0fdf4;border-left:4px solid #059669;border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:20px;">
<strong>Date & Time:</strong> {now}<br><strong>Status:</strong> <span style="color:#059669;font-weight:700;">&#10003; Successful</span>
</div>
<p style="font-size:13.5px;color:#475569;">If this wasn't you, please reset your password immediately.</p>
{_btn("Open StudyMind", APP_URL)}"""
    _send_async(to_email, f"[{APP_NAME}] New login to your account", _base_template(content))


def send_welcome_email(to_email: str, user_name: str) -> None:
    first = user_name.split()[0] if user_name else "Student"
    content = f"""
<h2 style="margin:0 0 8px;font-size:22px;font-weight:800;color:#0f172a;">&#127881; Welcome, {first}!</h2>
<p style="margin:0 0 20px;font-size:14px;color:#475569;">Your {APP_NAME} account is ready. Upload your notes, ask questions, generate quizzes and flashcards — all powered by AI.</p>
<div style="background:#f5f3ff;border-left:4px solid #7c3aed;border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:20px;">
&#128161; <strong>Quick Start:</strong> Upload a PDF → click Index → ask any question!
</div>
{_btn("Start Studying Now", APP_URL)}"""
    _send_async(to_email, f"Welcome to {APP_NAME}! 🎉", _base_template(content))


def send_weekly_report(to_email: str, user_name: str, stats: Dict) -> None:
    first = user_name.split()[0] if user_name else "Student"
    hrs   = round(stats.get("study_min", 0) / 60, 1)
    score = stats.get("avg_score", 0)
    content = f"""
<h2 style="margin:0 0 8px;font-size:20px;font-weight:800;color:#0f172a;">&#128202; Weekly Report</h2>
<p style="margin:0 0 20px;font-size:14px;color:#475569;">Hey <strong>{first}</strong>! Here's your study summary:</p>
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
<tr>
<td style="padding:0 6px;text-align:center;"><div style="background:#f5f3ff;border:1px solid #7c3aed33;border-radius:12px;padding:14px;"><div style="font-size:22px;font-weight:800;color:#7c3aed;">{hrs}h</div><div style="font-size:11px;color:#94a3b8;text-transform:uppercase;">Study Time</div></div></td>
<td style="padding:0 6px;text-align:center;"><div style="background:#f0fdf4;border:1px solid #05996933;border-radius:12px;padding:14px;"><div style="font-size:22px;font-weight:800;color:#059669;">{score}%</div><div style="font-size:11px;color:#94a3b8;text-transform:uppercase;">Avg Score</div></div></td>
<td style="padding:0 6px;text-align:center;"><div style="background:#fefce8;border:1px solid #d9770633;border-radius:12px;padding:14px;"><div style="font-size:22px;font-weight:800;color:#d97706;">{stats.get("streak",0)}d</div><div style="font-size:11px;color:#94a3b8;text-transform:uppercase;">Streak</div></div></td>
</tr>
</table>
{_btn("View Dashboard", APP_URL)}"""
    _send_async(to_email, f"[{APP_NAME}] Your Weekly Study Report 📊", _base_template(content))
def email_configured() -> bool:
    return bool(SMTP_SENDER and SMTP_PASSWORD and not SMTP_PASSWORD.startswith("xxxx"))