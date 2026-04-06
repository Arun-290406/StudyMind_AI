# notifications/sms_sender.py
"""
SMS Notification System for StudyMind AI.

Supports two providers:
  1. Twilio     — International (free trial: $15 credit, US/UK/India)
  2. Fast2SMS   — India-only (cheapest for Indian numbers, free trial available)

Setup:
  For Twilio:
    SMS_PROVIDER=twilio
    TWILIO_ACCOUNT_SID=ACxxxx
    TWILIO_AUTH_TOKEN=xxxx
    TWILIO_FROM_NUMBER=+1xxxxxxxxxx

  For Fast2SMS (India):
    SMS_PROVIDER=fast2sms
    FAST2SMS_API_KEY=your_api_key

  Set in .env file.
"""

import os
import threading
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

SMS_PROVIDER       = os.getenv("SMS_PROVIDER", "").lower()          # "twilio" or "fast2sms"
TWILIO_SID         = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN       = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM        = os.getenv("TWILIO_FROM_NUMBER", "")
FAST2SMS_KEY       = os.getenv("FAST2SMS_API_KEY", "")
APP_NAME           = os.getenv("APP_NAME", "StudyMind AI")


# ─────────────────────────────────────────────────────────────────────────────
# Provider implementations
# ─────────────────────────────────────────────────────────────────────────────

def _send_twilio(to_number: str, message: str) -> bool:
    """Send SMS via Twilio."""
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM]):
        print("[sms] Twilio not configured.")
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(body=message, from_=TWILIO_FROM, to=to_number)
        print(f"[sms] Twilio SMS sent to {to_number[:6]}***")
        return True
    except ImportError:
        print("[sms] Twilio not installed. Run: pip install twilio")
        return False
    except Exception as e:
        print(f"[sms] Twilio send failed: {e}")
        return False


def _send_fast2sms(to_number: str, message: str) -> bool:
    """
    Send SMS via Fast2SMS (India).
    Strips country code — Fast2SMS uses 10-digit Indian numbers.
    """
    if not FAST2SMS_KEY:
        print("[sms] Fast2SMS API key not configured.")
        return False
    try:
        import requests
        # Strip +91 prefix if present
        number = to_number.strip().replace(" ", "")
        if number.startswith("+91"):
            number = number[3:]
        elif number.startswith("91") and len(number) == 12:
            number = number[2:]

        resp = requests.post(
            "https://www.fast2sms.com/dev/bulkV2",
            headers={"authorization": FAST2SMS_KEY},
            data={
                "route":   "q",
                "message": message,
                "numbers": number,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("return") is True:
            print(f"[sms] Fast2SMS sent to {number[:4]}***")
            return True
        else:
            print(f"[sms] Fast2SMS error: {data}")
            return False
    except ImportError:
        print("[sms] requests not installed. Run: pip install requests")
        return False
    except Exception as e:
        print(f"[sms] Fast2SMS send failed: {e}")
        return False


def _send_sms_sync(to_number: str, message: str) -> bool:
    """Choose provider and send synchronously."""
    if not to_number or not to_number.strip():
        return False

    if SMS_PROVIDER == "twilio":
        return _send_twilio(to_number, message)
    elif SMS_PROVIDER == "fast2sms":
        return _send_fast2sms(to_number, message)
    else:
        print(f"[sms] SMS_PROVIDER not set. Set 'twilio' or 'fast2sms' in .env")
        return False


def _send_async(to_number: str, message: str) -> None:
    """Send SMS in a background thread — never blocks the UI."""
    t = threading.Thread(
        target=_send_sms_sync, args=(to_number, message), daemon=True
    )
    t.start()


# ─────────────────────────────────────────────────────────────────────────────
# Message templates
# ─────────────────────────────────────────────────────────────────────────────

def send_login_sms(mobile: str, user_name: str) -> None:
    """
    Send a login security alert SMS.
    Called from auth_manager.py after successful login.
    Non-blocking — runs in background thread.
    """
    now     = datetime.now().strftime("%d %b %Y at %H:%M")
    first   = user_name.split()[0] if user_name else "Student"
    message = (
        f"Hi {first}! Your {APP_NAME} account was just logged in "
        f"on {now}. "
        f"If this wasn't you, please change your password immediately. "
        f"- {APP_NAME}"
    )
    _send_async(mobile, message)


def send_welcome_sms(mobile: str, user_name: str) -> None:
    """
    Send a welcome SMS after successful registration.
    Called from auth_manager.py after register_user().
    """
    first   = user_name.split()[0] if user_name else "Student"
    message = (
        f"Welcome to {APP_NAME}, {first}! "
        f"Your account has been created successfully. "
        f"Start uploading your notes and studying smarter! "
        f"- {APP_NAME}"
    )
    _send_async(mobile, message)


def send_custom_sms(mobile: str, message: str) -> None:
    """Send any custom SMS message."""
    _send_async(mobile, message)


def sms_configured() -> bool:
    """Return True if SMS is properly configured."""
    if SMS_PROVIDER == "twilio":
        return bool(TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM)
    elif SMS_PROVIDER == "fast2sms":
        return bool(FAST2SMS_KEY)
    return False


def sms_provider_name() -> str:
    if SMS_PROVIDER == "twilio":
        return "Twilio"
    elif SMS_PROVIDER == "fast2sms":
        return "Fast2SMS (India)"
    return "Not configured"