# app/pages/10_multi_doc.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from pathlib import Path
from utils.session_state import init_session_state
from utils.file_handler import validate_file, save_uploaded_file, get_file_info
from auth.auth_manager import current_user
from core.ingestion import ingest_files, docs_summary
from core.vector_store import build_vector_store, delete_vector_store
from features.qa_chain import answer_question
from search.smart_search import (
    tag_document, register_document, get_user_documents,
    get_all_tags, get_docs_by_tag, smart_search
)
init_session_state()
user = current_user()
uid  = user.get("id", 0)

st.markdown('<div class="sm-page-title">📂 Multi-Document Chat</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">Upload multiple PDFs · auto-tag by topic · chat per document or all at once</div>', unsafe_allow_html=True)

tab_docs, tab_chat, tab_search = st.tabs(["📚 My Documents", "💬 Chat", "🔍 Smart Search"])

# ══ DOCUMENTS TAB ═════════════════════════════════════════════════════════════
with tab_docs:
    col_up, col_list = st.columns([1, 1.6], gap="large")

    with col_up:
        st.markdown('<p class="sm-lbl">Add Document</p>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(124,58,237,.07);border:1px solid rgba(124,58,237,.18);
                    border-radius:13px;padding:1rem 1.2rem;margin-bottom:1rem;font-size:13px;
                    color:#94a3b8;line-height:1.6;">
          Upload documents here. Each document is auto-tagged with its key topics.
          You can then chat with individual documents or search across all of them.
        </div>""", unsafe_allow_html=True)

        uploaded = st.file_uploader("PDF, DOCX, TXT", type=["pdf","docx","txt","md"], key="md_up")
        subject  = st.text_input("Subject / Category", placeholder="e.g. Machine Learning, OS, DBMS", key="md_sub")

        if uploaded and st.button("⚡ Upload & Auto-Tag", use_container_width=True, key="md_upload_btn"):
            valid, err = validate_file(uploaded)
            if not valid:
                st.error(f"❌ {err}")
            else:
                with st.spinner("Uploading & extracting topics…"):
                    saved_path = str(save_uploaded_file(uploaded))
                    info       = get_file_info(saved_path)
                    register_document(uid, info["name"], saved_path, subject,
                                      info["size_mb"], info.get("num_pages", 0))
                    from utils.file_handler import extract_text
                    data   = extract_text(saved_path)
                    topics = tag_document(uid, info["name"], data["text"])

                existing = [f["name"] for f in st.session_state.uploaded_files]
                if info["name"] not in existing:
                    st.session_state.uploaded_files.append(info)

                st.success(f"✅ **{info['name']}** added!")
                chips = " ".join(
                    f'<span class="sm-badge badge-v" style="font-size:10px;">{t}</span>'
                    for t in topics[:8]
                )
                st.markdown(f"**Auto-tags:** {chips}", unsafe_allow_html=True)
                st.rerun()

    with col_list:
        st.markdown('<p class="sm-lbl">Your Documents</p>', unsafe_allow_html=True)
        docs = get_user_documents(uid)
        if not docs:
            st.markdown("""
            <div class="sm-empty" style="padding:2rem;">
              <div class="sm-empty-ico">📂</div>
              <div class="sm-empty-title">No documents yet</div>
              <div class="sm-empty-sub">Upload your first PDF on the left.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for doc in docs:
                subj = doc.get("subject") or "Uncategorised"
                with st.expander(f"📄 **{doc['name']}** · *{subj}*"):
                    col1, col2 = st.columns(2)
                    col1.markdown(f"**Size:** {doc['size_mb']} MB")
                    col2.markdown(f"**Pages:** {doc.get('pages') or '—'}")
                    if doc.get("tags"):
                        chips = " ".join(
                            f'<span class="sm-badge badge-v" style="font-size:10px;">{t}</span>'
                            for t in doc["tags"][:10]
                        )
                        st.markdown(f"**Topics:** {chips}", unsafe_allow_html=True)
                    else:
                        st.markdown('<span style="font-size:12px;color:#475569;">No tags yet</span>', unsafe_allow_html=True)

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

    # Index all button
    if st.session_state.uploaded_files:
        if st.button("⚡ Index All Documents for Q&A", use_container_width=True, key="md_index_all"):
            paths = [f["path"] for f in st.session_state.uploaded_files]
            bar   = st.progress(0, text="Indexing…")
            def _cb(cur, tot, name): bar.progress(cur/tot, text=f"Indexing {name}…")
            with st.spinner("Building vector index…"):
                doc_chunks = ingest_files(paths, progress_callback=_cb)
                vs = build_vector_store(doc_chunks)
                st.session_state.vector_store = vs
                st.session_state.docs_indexed = True
                s = docs_summary(doc_chunks)
            bar.empty()
            st.success(f"✅ Indexed **{s['total_chunks']}** chunks from **{s['total_sources']}** documents!")
            st.rerun()
    else:
        st.info("Upload documents above, then index them for Q&A.")

# ══ CHAT TAB ══════════════════════════════════════════════════════════════════
with tab_chat:
    if not st.session_state.docs_indexed:
        st.markdown("""
        <div style="background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.25);
                    border-radius:14px;padding:1.2rem 1.5rem;text-align:center;">
          <div style="font-size:1.5rem;margin-bottom:.4rem;">⚡</div>
          <div style="font-weight:700;color:#fcd34d;font-size:14px;">Index your documents first</div>
          <div style="font-size:12.5px;color:#64748b;margin-top:.3rem;">
            Go to My Documents tab → Upload → Index All</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Document selector
        all_docs = get_user_documents(uid)
        doc_opts = ["📚 All Documents"] + [f"📄 {d['name']}" for d in all_docs]
        sel = st.selectbox("Chat with:", doc_opts, key="md_sel")
        source_filter = None if sel.startswith("📚") else sel.replace("📄 ","")

        if source_filter:
            st.markdown(
                f'<div class="sm-info">💬 Scoped to: <strong>{source_filter}</strong></div>',
                unsafe_allow_html=True
            )

        # Per-document chat history
        chat_key = f"md_chat_{sel}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        # Display history
        if not st.session_state[chat_key]:
            st.markdown("""
            <div class="sm-empty" style="padding:2.5rem;">
              <div class="sm-empty-ico">💬</div>
              <div class="sm-empty-title">Start a conversation</div>
              <div class="sm-empty-sub">Ask anything about the selected document(s).</div>
            </div>""", unsafe_allow_html=True)
        else:
            for msg in st.session_state[chat_key]:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🧠"):
                        st.markdown(msg["content"])
                        if msg.get("citations"):
                            with st.expander("📎 Sources"):
                                for c in msg["citations"]:
                                    pg = f" · p.{c['page']}" if c.get("page") else ""
                                    st.markdown(f'<span class="sm-chip">📄 {c["source"]}{pg}</span>', unsafe_allow_html=True)

        user_q = st.chat_input(f"Ask about {sel}…", key=f"ci_{sel}")
        if user_q:
            st.session_state[chat_key].append({"role":"user","content":user_q,"citations":[]})
            with st.spinner("Searching documents…"):
                result = answer_question(
                    st.session_state.vector_store, user_q, k=5,
                    chat_history=st.session_state[chat_key][:-1],
                    source_filter=source_filter,
                )
            st.session_state[chat_key].append({
                "role":"assistant","content":result["answer"],
                "citations":result["citations"],
            })
            st.rerun()

        if st.session_state.get(chat_key):
            if st.button("🗑️ Clear Chat", key=f"cc_{sel}", use_container_width=False):
                st.session_state[chat_key] = []; st.rerun()

# ══ SMART SEARCH TAB ══════════════════════════════════════════════════════════
with tab_search:
    if not st.session_state.docs_indexed:
        st.info("Index your documents first.")
    else:
        all_tags = get_all_tags(uid)
        st.markdown('<p class="sm-lbl">Search Across All Documents</p>', unsafe_allow_html=True)

        col_q, col_tag, col_btn = st.columns([4, 2, 1])
        query     = col_q.text_input("Search query", placeholder="What are support vector machines?", key="ss_q", label_visibility="collapsed")
        tag_filter = col_tag.selectbox("Filter by tag", ["All tags"] + all_tags, key="ss_tag", label_visibility="collapsed")
        do_search = col_btn.button("🔍", use_container_width=True, key="ss_go")

        if do_search:
            if not query.strip():
                st.warning("Enter a search query.")
            else:
                tf = None if tag_filter == "All tags" else tag_filter
                with st.spinner("Searching…"):
                    results = smart_search(
                        st.session_state.vector_store, query, k=6,
                        tag_filter=tf, user_id=uid
                    )
                if results:
                    st.markdown(
                        f'<p style="color:#94a3b8;font-size:13px;margin:.5rem 0 .8rem;">'
                        f'Found <strong style="color:#a78bfa;">{len(results)}</strong> results</p>',
                        unsafe_allow_html=True
                    )
                    for r in results:
                        pg    = f" · Page {r['page']}" if r.get("page") else ""
                        score = r.get("score", 0)
                        with st.expander(f"📄 {r['source']}{pg}  —  {score:.0%} relevance"):
                            st.markdown(
                                f'<p style="font-size:14px;color:#f8fafc;line-height:1.7;">'
                                f'{r["content"][:500]}…</p>',
                                unsafe_allow_html=True
                            )
                else:
                    st.info("No results found. Try a different query or remove the tag filter.")

        # Tag browser
        if all_tags:
            st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
            st.markdown('<p class="sm-lbl">Browse by Tag</p>', unsafe_allow_html=True)
            selected_tag = st.selectbox("Select a topic tag", all_tags, key="tag_browse")
            if selected_tag:
                tagged = get_docs_by_tag(uid, selected_tag)
                if tagged:
                    st.markdown(
                        f'<p style="font-size:13px;color:#94a3b8;">'
                        f'Documents tagged <strong style="color:#a78bfa;">"{selected_tag}"</strong>:</p>',
                        unsafe_allow_html=True
                    )
                    for d in tagged:
                        st.markdown(
                            f'<span class="sm-chip">📄 {d}</span>',
                            unsafe_allow_html=True
                        )