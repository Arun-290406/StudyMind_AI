# app/pages/01_ask_notes.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from pathlib import Path
from utils.session_state import init_session_state, add_chat_message
from utils.file_handler import validate_file, save_uploaded_file, get_file_info
from core.ingestion import ingest_files, docs_summary
from core.vector_store import build_vector_store, load_vector_store, index_exists, delete_vector_store
from features.qa_chain import answer_question
init_session_state()

st.markdown('<div class="sm-page-title">🔍 Ask Your Notes</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">RAG-powered Q&amp;A — every answer cited directly from your uploaded documents</div>', unsafe_allow_html=True)

with st.expander("📁 Upload & Index Documents", expanded=not st.session_state.docs_indexed):
    uploaded = st.file_uploader("Drop PDF, DOCX, TXT or MD files", type=["pdf","docx","txt","md"], accept_multiple_files=True)
    if uploaded:
        new_paths = []
        for uf in uploaded:
            valid, err = validate_file(uf)
            if not valid: st.error(f"❌ {uf.name}: {err}"); continue
            saved = str(save_uploaded_file(uf))
            existing = [f["name"] for f in st.session_state.uploaded_files]
            if Path(saved).name not in existing:
                st.session_state.uploaded_files.append(get_file_info(saved))
                new_paths.append(saved)
        if new_paths:
            st.success(f"✅ {len(new_paths)} file(s) added — click Index to enable Q&A.")

    if st.session_state.uploaded_files:
        chips = "".join(f'<span class="sm-chip">📄 {f["name"]} <span style="color:var(--t3);margin-left:3px">{f["size_mb"]} MB</span></span>' for f in st.session_state.uploaded_files)
        st.markdown(chips, unsafe_allow_html=True)
        st.write("")

    col_idx, col_clr = st.columns([3, 1])
    with col_idx:
        if st.button("⚡ Index All Documents", use_container_width=True, disabled=not st.session_state.uploaded_files):
            paths = [f["path"] for f in st.session_state.uploaded_files]
            bar = st.progress(0, text="Preparing…")
            def _cb(cur,tot,name): bar.progress(cur/tot, text=f"Chunking {name}…")
            with st.spinner("Embedding & indexing…"):
                docs = ingest_files(paths, progress_callback=_cb)
                vs   = build_vector_store(docs)
                st.session_state.vector_store = vs
                st.session_state.docs_indexed = True
                s = docs_summary(docs)
            bar.empty()
            st.success(f"✅ Indexed **{s['total_chunks']}** chunks from **{s['total_sources']}** source(s).")
            st.rerun()
    with col_clr:
        if st.button("Clear All", use_container_width=True):
            delete_vector_store()
            st.session_state.uploaded_files = []
            st.session_state.vector_store = None
            st.session_state.docs_indexed = False
            st.rerun()

if not st.session_state.docs_indexed and index_exists():
    try:
        vs = load_vector_store()
        if vs: st.session_state.vector_store = vs; st.session_state.docs_indexed = True
    except Exception: pass

if st.session_state.docs_indexed:
    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sm-lbl">Quick Questions</p>', unsafe_allow_html=True)
    SUGG = ["Summarize the main topics","What are the key definitions?","Explain the most important concept","Likely exam questions?"]
    cols = st.columns(4)
    for i,s in enumerate(SUGG):
        if cols[i].button(s, key=f"sug_{i}", use_container_width=True):
            st.session_state._pending_q = s

st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

# Voice toggle
show_voice = st.toggle("🔊 Speak answers aloud (TTS)", key="tts_on", value=False)

if not st.session_state.chat_history:
    st.markdown('<div class="sm-empty"><div class="sm-empty-ico">🧠</div><div class="sm-empty-title">Ready to answer from your notes</div><div class="sm-empty-sub">Upload &amp; index documents above, then ask anything.</div></div>', unsafe_allow_html=True)
else:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"): st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🧠"):
                st.markdown(msg["content"])
                if show_voice and msg.get("content"):
                    try:
                        from voice.voice_assistant import is_tts_available, speak_in_streamlit
                        if is_tts_available(): speak_in_streamlit(msg["content"][:500])
                    except Exception: pass
                if msg.get("citations"):
                    with st.expander("📎 View Sources"):
                        for c in msg["citations"]:
                            pg = f" · p.{c['page']}" if c.get("page") else ""
                            sc = c.get("score", 0)
                            st.markdown(f'<span class="sm-chip">📄 {c["source"]}{pg}</span><span style="font-size:11px;color:var(--t3);margin-left:6px;">relevance {sc:.0%}</span>', unsafe_allow_html=True)

col_chat, col_clr = st.columns([6, 1])
with col_chat:
    user_input = st.chat_input("Ask anything from your notes…", disabled=not st.session_state.docs_indexed)
with col_clr:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Clear", use_container_width=True):
        st.session_state.chat_history = []; st.rerun()

if hasattr(st.session_state, "_pending_q"):
    user_input = st.session_state._pending_q
    del st.session_state._pending_q

if user_input and st.session_state.docs_indexed:
    add_chat_message("user", user_input)
    with st.spinner("Searching your notes…"):
        result = answer_question(st.session_state.vector_store, user_input, k=5, chat_history=st.session_state.chat_history[:-1])
    add_chat_message("assistant", result["answer"], citations=result["citations"])
    st.rerun()
elif user_input:
    st.warning("⚠️ Please upload and index documents first.")