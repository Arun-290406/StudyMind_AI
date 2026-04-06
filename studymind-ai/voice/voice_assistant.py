# voice/voice_assistant.py
"""
Voice Assistant — Text-to-Speech + Speech-to-Text
ALL functions used across the project are defined here.

Functions:
  speak_in_streamlit()       - render Streamlit audio player (used in 01_ask_notes, 08_voice)
  text_to_speech_bytes()     - convert text → MP3 bytes
  get_audio_b64()            - base64-encoded MP3 for HTML embed
  transcribe_audio_file()    - transcribe WAV file path
  transcribe_uploaded_audio() - transcribe Streamlit UploadedFile
  transcribe_with_whisper()  - OpenAI Whisper API (optional)
  is_tts_available()         - check if gTTS is installed
  is_stt_available()         - check if SpeechRecognition is installed
"""

import os
import io
import base64
import tempfile
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


# ── Text-to-Speech (gTTS) ─────────────────────────────────────────────────────

def text_to_speech_bytes(text: str, lang: str = "en") -> Optional[bytes]:
    """
    Convert text → MP3 bytes using gTTS.
    Returns None if gTTS is not installed or fails.
    """
    try:
        from gtts import gTTS
        tts = gTTS(text=str(text)[:2000], lang=lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except ImportError:
        print("[voice] gTTS not installed. Run: pip install gTTS")
        return None
    except Exception as e:
        print(f"[voice] TTS failed: {e}")
        return None


def speak_in_streamlit(text: str, lang: str = "en") -> None:
    """
    Render a Streamlit audio player that plays the given text.
    This is the primary TTS function — called from:
      - app/pages/01_ask_notes.py (voice toggle)
      - app/pages/08_voice.py (voice assistant page)
    """
    import streamlit as st

    audio_bytes = text_to_speech_bytes(text, lang=lang)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")
    else:
        st.warning(
            "⚠️ Text-to-speech unavailable. "
            "Install gTTS: `pip install gTTS`",
            icon="🔊"
        )


def get_audio_b64(text: str, lang: str = "en") -> str:
    """Return base64-encoded MP3 for embedding in HTML autoplay."""
    audio_bytes = text_to_speech_bytes(text, lang=lang)
    if not audio_bytes:
        return ""
    return base64.b64encode(audio_bytes).decode("utf-8")


# ── Speech-to-Text (SpeechRecognition) ────────────────────────────────────────

def transcribe_audio_file(audio_path: str) -> str:
    """
    Transcribe a WAV/MP3 file from disk using Google Speech Recognition.
    Returns the transcribed string, or "" on failure.
    """
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)
        return r.recognize_google(audio)
    except ImportError:
        print("[voice] SpeechRecognition not installed. Run: pip install SpeechRecognition")
        return ""
    except Exception as e:
        print(f"[voice] STT transcription failed: {e}")
        return ""


def transcribe_uploaded_audio(uploaded_file) -> str:
    """
    Transcribe a Streamlit UploadedFile (wav/mp3).
    Called from app/pages/08_voice.py.
    """
    try:
        import speech_recognition as sr
        r = sr.Recognizer()

        content = uploaded_file.read()
        uploaded_file.seek(0)   # reset for re-use

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = ""
        try:
            with sr.AudioFile(tmp_path) as source:
                audio = r.record(source)
            result = r.recognize_google(audio)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        return result

    except ImportError:
        print("[voice] SpeechRecognition not installed. Run: pip install SpeechRecognition")
        return ""
    except Exception as e:
        print(f"[voice] Upload transcription failed: {e}")
        return ""


def transcribe_with_whisper(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Transcribe audio using OpenAI Whisper API (higher quality).
    Falls back gracefully if no API key or openai package.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-your"):
        return ""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model="whisper-1", file=f
                )
            return result.text
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    except ImportError:
        return ""
    except Exception as e:
        print(f"[voice] Whisper transcription failed: {e}")
        return ""


# ── Availability checks ───────────────────────────────────────────────────────

def is_tts_available() -> bool:
    """Return True if gTTS is installed and importable."""
    try:
        from gtts import gTTS  # noqa: F401
        return True
    except ImportError:
        return False


def is_stt_available() -> bool:
    """Return True if SpeechRecognition is installed and importable."""
    try:
        import speech_recognition as sr  # noqa: F401
        return True
    except ImportError:
        return False