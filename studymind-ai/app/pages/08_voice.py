# app/pages/08_voice.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from utils.session_state import init_session_state
from voice.voice_assistant import (
    speak_in_streamlit, transcribe_uploaded_audio,
    is_tts_available, is_stt_available, text_to_speech_bytes
)
from features.qa_chain import answer_question
init_session_state()

st.markdown('<div class="sm-page-title">🎤 Voice Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">Ask questions by voice · hear AI answers spoken aloud · multilingual TTS</div>', unsafe_allow_html=True)

# ── Status row ─────────────────────────────────────────────────────────────────
tts_ok = is_tts_available()
stt_ok = is_stt_available()
c1, c2, c3 = st.columns(3)
for col, ok, label, install in [
    (c1, tts_ok, "🔊 Text-to-Speech", "pip install gTTS"),
    (c2, stt_ok, "🎤 Speech-to-Text", "pip install SpeechRecognition"),
    (c3, True,   "🧠 RAG Q&A",        "Included"),
]:
    col.markdown(
        f'<div style="padding:9px 12px;border-radius:11px;border:1px solid;text-align:center;'
        f'font-size:12.5px;font-weight:600;'
        f'{"background:rgba(5,150,105,.09);border-color:rgba(5,150,105,.3);color:#6ee7b7" if ok else "background:rgba(245,158,11,.09);border-color:rgba(245,158,11,.3);color:#fcd34d"};">'
        f'{"✅" if ok else "⚙️"} {label}</div>',
        unsafe_allow_html=True
    )

st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

if not st.session_state.docs_indexed:
    st.markdown("""
    <div style="background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.25);
                border-radius:14px;padding:1.2rem 1.5rem;text-align:center;">
      <div style="font-size:1.8rem;margin-bottom:.5rem;">📁</div>
      <div style="font-weight:700;color:#fcd34d;font-size:14px;">Index documents first</div>
      <div style="font-size:12.5px;color:#64748b;margin-top:.3rem;">
        Go to Ask Notes, upload your PDFs, and click Index.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

tab_upload, tab_type, tab_how = st.tabs(["🎤 Voice Upload", "⌨️ Type & Listen", "❓ How It Works"])

# ── TAB 1: VOICE UPLOAD ────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("""
    <div style="background:rgba(124,58,237,.07);border:1px solid rgba(124,58,237,.2);
                border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
      <div style="font-weight:700;color:#a78bfa;font-size:14px;margin-bottom:.4rem;">
        🎙️ Record your question, upload below</div>
      <div style="font-size:13px;color:#64748b;line-height:1.65;">
        Use your phone's Voice Recorder app or Windows Sound Recorder.<br>
        Save as <strong>WAV</strong> format, then upload below.
      </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_audio = st.file_uploader("Upload WAV question", type=["wav"], key="va_up")
    lang_col, _ = st.columns([1, 2])
    tts_lang = lang_col.selectbox("Response language", ["en","ta","hi","fr","de","es"],
        format_func=lambda x: {"en":"English 🇬🇧","ta":"Tamil 🇮🇳","hi":"Hindi 🇮🇳",
                               "fr":"French 🇫🇷","de":"German 🇩🇪","es":"Spanish 🇪🇸"}[x],
        key="va_lang1")

    if uploaded_audio:
        st.audio(uploaded_audio, format="audio/wav")
        with st.spinner("🎙️ Transcribing your voice…"):
            transcript = transcribe_uploaded_audio(uploaded_audio)

        if transcript:
            st.markdown(f"""
            <div style="background:rgba(8,145,178,.08);border:1px solid rgba(8,145,178,.22);
                        border-radius:13px;padding:1rem 1.2rem;margin:.8rem 0;">
              <div style="font-size:10.5px;color:#67e8f9;font-weight:700;
                          text-transform:uppercase;letter-spacing:.09em;margin-bottom:.4rem;">
                Your Question</div>
              <div style="font-size:15px;color:#f8fafc;font-weight:500;">
                "{transcript}"</div>
            </div>""", unsafe_allow_html=True)

            with st.spinner("🧠 Searching your notes…"):
                result = answer_question(st.session_state.vector_store, transcript, k=5)

            answer_text = result["answer"]
            st.markdown(f"""
            <div style="background:rgba(5,150,105,.08);border:1px solid rgba(5,150,105,.22);
                        border-radius:13px;padding:1rem 1.2rem;margin:.8rem 0;">
              <div style="font-size:10.5px;color:#6ee7b7;font-weight:700;
                          text-transform:uppercase;letter-spacing:.09em;margin-bottom:.4rem;">
                AI Answer</div>
              <div style="font-size:14px;color:#f8fafc;line-height:1.7;">
                {answer_text[:600]}</div>
            </div>""", unsafe_allow_html=True)

            if tts_ok:
                st.markdown("**🔊 Listen to the answer:**")
                speak_in_streamlit(answer_text[:600])
            else:
                st.info("Install gTTS for audio output: `pip install gTTS`")

            if result.get("citations"):
                with st.expander("📎 Sources cited"):
                    for c in result["citations"]:
                        pg = f" · p.{c['page']}" if c.get("page") else ""
                        st.markdown(f'<span class="sm-chip">📄 {c["source"]}{pg}</span>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Could not transcribe the audio. Try speaking more clearly.")

# ── TAB 2: TYPE & LISTEN ──────────────────────────────────────────────────────
with tab_type:
    st.markdown(
        '<p style="color:#94a3b8;font-size:13.5px;margin-bottom:1rem;">'
        'Type any question and hear the AI answer spoken aloud.</p>',
        unsafe_allow_html=True
    )

    question = st.text_input(
        "Your question", placeholder="e.g. Explain the concept of gradient descent",
        key="va_q"
    )
    col_lang, col_btn = st.columns([1, 2])
    tts_lang2 = col_lang.selectbox(
        "Language", ["en","ta","hi","fr","de","es"],
        format_func=lambda x: {"en":"English","ta":"Tamil","hi":"Hindi",
                               "fr":"French","de":"German","es":"Spanish"}[x],
        key="va_lang2"
    )

    if col_btn.button("🔍 Answer + 🔊 Speak", use_container_width=True, key="va_ask"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Generating answer…"):
                result = answer_question(st.session_state.vector_store, question, k=5)

            answer_text = result["answer"]

            st.markdown(f"""
            <div class="sm-card" style="margin:.8rem 0;">
              <div style="font-size:10.5px;color:#a78bfa;font-weight:700;
                          text-transform:uppercase;letter-spacing:.09em;margin-bottom:.6rem;">
                Answer</div>
              <div style="font-size:14.5px;color:#f8fafc;line-height:1.72;">
                {answer_text}</div>
            </div>""", unsafe_allow_html=True)

            if tts_ok:
                st.markdown("**🔊 Audio answer:**")
                # Generate audio with selected language
                try:
                    from gtts import gTTS
                    import io
                    tts = gTTS(text=answer_text[:600], lang=tts_lang2, slow=False)
                    buf = io.BytesIO()
                    tts.write_to_fp(buf)
                    buf.seek(0)
                    st.audio(buf.read(), format="audio/mp3")
                except Exception:
                    speak_in_streamlit(answer_text[:600])
            else:
                st.info("Install gTTS: `pip install gTTS`")

            if result.get("citations"):
                with st.expander("📎 Sources"):
                    for c in result["citations"]:
                        pg = f" · p.{c['page']}" if c.get("page") else ""
                        st.markdown(f'<span class="sm-chip">📄 {c["source"]}{pg}</span>', unsafe_allow_html=True)

    # ── Chat history for voice tab
    if "voice_history" not in st.session_state:
        st.session_state["voice_history"] = []

    if st.session_state["voice_history"]:
        st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
        st.markdown('<p class="sm-lbl">Previous Questions</p>', unsafe_allow_html=True)
        for item in reversed(st.session_state["voice_history"][-5:]):
            st.markdown(f'<div style="padding:6px 10px;font-size:13px;color:#64748b;'
                        f'border-left:3px solid rgba(124,58,237,.35);margin-bottom:4px;">'
                        f'Q: {item}</div>', unsafe_allow_html=True)

# ── TAB 3: HOW IT WORKS ────────────────────────────────────────────────────────
with tab_how:
    st.markdown("""
    <div style="display:flex;flex-direction:column;gap:12px;margin-top:.5rem;">

      <div style="display:flex;gap:14px;align-items:flex-start;padding:14px 16px;
                  background:rgba(255,255,255,.025);border:1px solid rgba(124,58,237,.15);
                  border-radius:13px;">
        <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
                    background:linear-gradient(135deg,#7c3aed,#4c1d95);
                    display:flex;align-items:center;justify-content:center;
                    font-weight:800;color:#fff;font-size:14px;">1</div>
        <div>
          <div style="font-weight:700;color:#f8fafc;font-size:14px;margin-bottom:3px;">
            Record your question</div>
          <div style="font-size:13px;color:#64748b;line-height:1.55;">
            Use your phone's Voice Recorder or Windows Sound Recorder.
            Speak clearly in a quiet environment. Save as WAV format.</div>
        </div>
      </div>

      <div style="display:flex;gap:14px;align-items:flex-start;padding:14px 16px;
                  background:rgba(255,255,255,.025);border:1px solid rgba(8,145,178,.15);
                  border-radius:13px;">
        <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
                    background:linear-gradient(135deg,#0891b2,#0e7490);
                    display:flex;align-items:center;justify-content:center;
                    font-weight:800;color:#fff;font-size:14px;">2</div>
        <div>
          <div style="font-weight:700;color:#f8fafc;font-size:14px;margin-bottom:3px;">
            Upload & Transcribe</div>
          <div style="font-size:13px;color:#64748b;line-height:1.55;">
            Upload the WAV file above. Google Speech Recognition transcribes your voice
            to text automatically (requires internet).</div>
        </div>
      </div>

      <div style="display:flex;gap:14px;align-items:flex-start;padding:14px 16px;
                  background:rgba(255,255,255,.025);border:1px solid rgba(5,150,105,.15);
                  border-radius:13px;">
        <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
                    background:linear-gradient(135deg,#059669,#047857);
                    display:flex;align-items:center;justify-content:center;
                    font-weight:800;color:#fff;font-size:14px;">3</div>
        <div>
          <div style="font-weight:700;color:#f8fafc;font-size:14px;margin-bottom:3px;">
            RAG Search + AI Answer</div>
          <div style="font-size:13px;color:#64748b;line-height:1.55;">
            Your question is searched against your indexed documents using FAISS vector search.
            The LLM generates a cited answer grounded in your notes.</div>
        </div>
      </div>

      <div style="display:flex;gap:14px;align-items:flex-start;padding:14px 16px;
                  background:rgba(255,255,255,.025);border:1px solid rgba(217,119,6,.15);
                  border-radius:13px;">
        <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
                    background:linear-gradient(135deg,#d97706,#b45309);
                    display:flex;align-items:center;justify-content:center;
                    font-weight:800;color:#fff;font-size:14px;">4</div>
        <div>
          <div style="font-weight:700;color:#f8fafc;font-size:14px;margin-bottom:3px;">
            Text-to-Speech Playback</div>
          <div style="font-size:13px;color:#64748b;line-height:1.55;">
            gTTS converts the answer to natural speech. Supports English, Tamil, Hindi,
            French, German and Spanish.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)