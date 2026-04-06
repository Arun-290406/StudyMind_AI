# app/pages/04_summary.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from utils.session_state import init_session_state
from features.summarizer import summarize_from_query, summarize_document, summarize_topic
init_session_state()

st.markdown('<div class="sm-page-title">Summaries</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">Structured AI summaries, TL;DRs, and topic breakdowns from your notes</div>', unsafe_allow_html=True)

if not st.session_state.docs_indexed:
    st.markdown('<div class="sm-empty"><div class="sm-empty-ico">📋</div><div class="sm-empty-title">Index documents first</div><div class="sm-empty-sub">Go to Ask Notes and upload your PDFs.</div></div>', unsafe_allow_html=True)
    st.stop()

tab_full, tab_topic, tab_doc, tab_saved = st.tabs(["📋  Full Summary","🎯  Topic Focus","📄  Per Document","💾  Saved"])

with tab_full:
    st.markdown('<div class="sm-highlight"><div class="sm-highlight-title">Generate Summary</div>', unsafe_allow_html=True)
    c1,c2 = st.columns([4,1])
    hint = c1.text_input("Optional focus area", placeholder="Leave blank for all notes")
    st.markdown('</div>', unsafe_allow_html=True)
    if c2.button("📋  Generate", use_container_width=True):
        with st.spinner("Summarizing your notes…"):
            result = summarize_from_query(st.session_state.vector_store, topic=hint)
        key = hint or "__all__"
        st.session_state.summaries[key] = result
        st.rerun()
    if st.session_state.summaries:
        latest = st.session_state.summaries[list(st.session_state.summaries.keys())[-1]]
        if latest.get("tldr"):
            st.markdown(f'<div class="sm-tldr"><div class="sm-tldr-lbl">⚡ TL;DR</div><div style="color:#f1f5f9;line-height:1.65;">{latest["tldr"]}</div></div>', unsafe_allow_html=True)
        if latest.get("sources"):
            chips = "".join(f'<span class="sm-chip">📄 {s}</span>' for s in latest["sources"])
            st.markdown(chips+"<br>", unsafe_allow_html=True)
        st.markdown(latest.get("summary",""))

with tab_topic:
    st.markdown('<p style="color:var(--t2);font-size:14px;margin-bottom:1rem;">Get a laser-focused summary on any specific concept from your notes.</p>', unsafe_allow_html=True)
    topic = st.text_input("Topic name", placeholder="e.g. Backpropagation, Attention Mechanism…")
    if st.button("🎯  Summarize Topic", use_container_width=True, disabled=not topic):
        with st.spinner(f"Finding and summarizing '{topic}'…"):
            text = summarize_topic(st.session_state.vector_store, topic)
        st.markdown(f'<div style="font-family:\'Syne\',sans-serif;font-size:1.4rem;font-weight:800;background:linear-gradient(120deg,#f1f5f9,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:1rem;">{topic}</div>', unsafe_allow_html=True)
        st.markdown(text)
        st.session_state.summaries[topic] = {"topic": topic, "summary": text, "tldr": ""}

with tab_doc:
    if not st.session_state.uploaded_files:
        st.markdown('<div class="sm-empty"><div class="sm-empty-ico">📄</div><div class="sm-empty-title">No documents uploaded</div></div>', unsafe_allow_html=True)
    else:
        selected = st.selectbox("Select document", [f["name"] for f in st.session_state.uploaded_files])
        doc_info = next((f for f in st.session_state.uploaded_files if f["name"] == selected), None)
        ca, cb = st.columns(2)
        if doc_info:
            if ca.button("📋  Full Summary", use_container_width=True):
                with st.spinner(f"Summarizing {selected}…"):
                    result = summarize_document(doc_info["path"])
                st.session_state.summaries[selected] = result; st.rerun()
            if cb.button("⚡  Quick TL;DR", use_container_width=True):
                with st.spinner("Generating TL;DR…"):
                    result = summarize_document(doc_info["path"])
                st.markdown(f'<div class="sm-tldr"><div class="sm-tldr-lbl">TL;DR — {selected}</div><div style="color:#f1f5f9;">{result.get("tldr","")}</div></div>', unsafe_allow_html=True)
        if selected in st.session_state.summaries:
            saved = st.session_state.summaries[selected]
            if saved.get("tldr"):
                st.markdown(f'<div class="sm-tldr"><div class="sm-tldr-lbl">⚡ TL;DR</div><div style="color:#f1f5f9;">{saved["tldr"]}</div></div>', unsafe_allow_html=True)
            st.markdown(saved.get("summary",""))

with tab_saved:
    if not st.session_state.summaries:
        st.markdown('<div class="sm-empty"><div class="sm-empty-ico">💾</div><div class="sm-empty-title">No saved summaries</div><div class="sm-empty-sub">Generate summaries from the other tabs.</div></div>', unsafe_allow_html=True)
    else:
        for key, summary in st.session_state.summaries.items():
            label = summary.get("topic") or summary.get("source") or key
            with st.expander(f"📋  {label}"):
                if summary.get("tldr"):
                    st.markdown(f'<div class="sm-tldr"><div class="sm-tldr-lbl">TL;DR</div><div style="color:#f1f5f9;font-size:13px;">{summary["tldr"][:250]}…</div></div>', unsafe_allow_html=True)
                st.markdown(summary.get("summary",""))
                cx,_ = st.columns([1,5])
                if cx.button("Delete", key=f"ds_{key}"):
                    del st.session_state.summaries[key]; st.rerun()