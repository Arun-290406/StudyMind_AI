# app/pages/11_exports.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from utils.session_state import init_session_state
from auth.auth_manager import current_user
init_session_state()
user = current_user()

st.markdown('<div class="sm-page-title">📥 PDF Export</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sm-page-sub">Download your summaries, flashcards, and quiz results as beautiful PDFs</div>',
    unsafe_allow_html=True
)

# ── Status overview ────────────────────────────────────────────────────────────
docs_ok      = st.session_state.get("docs_indexed", False)
flashcards   = st.session_state.get("flashcards", [])
quiz_result  = st.session_state.get("sq_result") or st.session_state.get("quiz_result")
quiz_qs      = st.session_state.get("sq_questions") or st.session_state.get("quiz_questions", [])
summary_data = st.session_state.get("export_summary") or st.session_state.get("current_summary")

# Status bar
s1, s2, s3 = st.columns(3)
s1.markdown(f"""
<div style="background:{"rgba(5,150,105,.1)" if docs_ok else "rgba(245,158,11,.08)"};
            border:1px solid {"rgba(5,150,105,.3)" if docs_ok else "rgba(245,158,11,.25)"};
            border-radius:13px;padding:.9rem;text-align:center;">
  <div style="font-size:1.4rem;">{"✅" if docs_ok else "⚠️"}</div>
  <div style="font-size:13px;font-weight:700;color:{"#6ee7b7" if docs_ok else "#fcd34d"};margin-top:.3rem;">Documents</div>
  <div style="font-size:11.5px;color:#64748b;">{"Indexed & ready" if docs_ok else "Not indexed yet"}</div>
</div>""", unsafe_allow_html=True)

s2.markdown(f"""
<div style="background:{"rgba(5,150,105,.1)" if flashcards else "rgba(245,158,11,.08)"};
            border:1px solid {"rgba(5,150,105,.3)" if flashcards else "rgba(245,158,11,.25)"};
            border-radius:13px;padding:.9rem;text-align:center;">
  <div style="font-size:1.4rem;">{"🃏" if flashcards else "⚠️"}</div>
  <div style="font-size:13px;font-weight:700;color:{"#6ee7b7" if flashcards else "#fcd34d"};margin-top:.3rem;">Flashcards</div>
  <div style="font-size:11.5px;color:#64748b;">{f"{len(flashcards)} cards ready" if flashcards else "None generated"}</div>
</div>""", unsafe_allow_html=True)

s3.markdown(f"""
<div style="background:{"rgba(5,150,105,.1)" if quiz_result else "rgba(245,158,11,.08)"};
            border:1px solid {"rgba(5,150,105,.3)" if quiz_result else "rgba(245,158,11,.25)"};
            border-radius:13px;padding:.9rem;text-align:center;">
  <div style="font-size:1.4rem;">{"📝" if quiz_result else "⚠️"}</div>
  <div style="font-size:13px;font-weight:700;color:{"#6ee7b7" if quiz_result else "#fcd34d"};margin-top:.3rem;">Quiz Result</div>
  <div style="font-size:11.5px;color:#64748b;">{f"{quiz_result.get('score_pct',0):.1f}% score" if quiz_result else "No quiz taken"}</div>
</div>""", unsafe_allow_html=True)

st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

tab_sum, tab_fc, tab_quiz, tab_notes = st.tabs([
    "📋 Summary PDF", "🃏 Flashcards PDF", "📝 Quiz PDF", "📖 Notes PDF"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SUMMARY PDF
# ══════════════════════════════════════════════════════════════════════════════
with tab_sum:
    st.markdown("""
    <div style="background:rgba(124,58,237,.07);border:1px solid rgba(124,58,237,.2);
                border-radius:13px;padding:1rem 1.3rem;margin-bottom:1rem;font-size:13.5px;color:#94a3b8;">
      Generate an AI summary from your indexed documents, then download as PDF.
      You can also generate one from the <strong>Summary</strong> page and come back here.
    </div>""", unsafe_allow_html=True)

    title = st.text_input("Report title", placeholder="e.g. Compiler Design — Chapter 3 Summary",
                          key="exp_title")
    topic = st.text_input("Topic focus (optional)", placeholder="e.g. Lexical Analysis",
                          key="exp_topic")

    col_gen, col_dl = st.columns(2)

    if not docs_ok:
        st.warning("⚠️ Index your documents first from **Ask Notes** → Index All Documents.")
    else:
        if col_gen.button("📋 Generate Summary Now", use_container_width=True, key="exp_gen_sum"):
            with st.spinner("Generating summary from your notes…"):
                try:
                    from features.summarizer import summarize_from_query
                    result = summarize_from_query(st.session_state.vector_store, topic=topic)
                    st.session_state["export_summary"] = result
                    summary_data = result
                    st.success("✅ Summary generated!")
                except Exception as e:
                    st.error(f"❌ Summary generation failed: {e}")

    # Show preview + download if summary exists
    if summary_data:
        st.markdown(f"""
        <div style="background:rgba(124,58,237,.07);border:1px solid rgba(124,58,237,.2);
                    border-radius:12px;padding:1rem 1.2rem;margin:.8rem 0;">
          <div style="font-size:10.5px;font-weight:700;color:#a78bfa;text-transform:uppercase;
                      letter-spacing:.09em;margin-bottom:.5rem;">TL;DR Preview</div>
          <div style="font-size:13.5px;color:#f8fafc;line-height:1.65;">
            {str(summary_data.get("tldr",""))[:300]}{"…" if len(str(summary_data.get("tldr","")))>300 else ""}
          </div>
        </div>""", unsafe_allow_html=True)

        try:
            from features.pdf_export import export_summary_pdf
            pdf_bytes = export_summary_pdf(
                title        = title or "Study Summary",
                summary_text = summary_data.get("summary", ""),
                tldr         = summary_data.get("tldr", ""),
                source_docs  = summary_data.get("sources", []),
                user_name    = user.get("name", "Student"),
            )
            st.download_button(
                "⬇️ Download Summary PDF", pdf_bytes,
                f"summary_{topic or 'notes'}.pdf", "application/pdf",
                key="dl_sum", use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}. Install fpdf2: pip install fpdf2")
    else:
        st.markdown("""
        <div class="sm-empty" style="padding:2rem;">
          <div class="sm-empty-ico">📋</div>
          <div class="sm-empty-title">No summary yet</div>
          <div class="sm-empty-sub">Click "Generate Summary Now" above, or first generate one from the Summary page.</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — FLASHCARDS PDF
# ══════════════════════════════════════════════════════════════════════════════
with tab_fc:
    st.markdown("""
    <div style="background:rgba(8,145,178,.07);border:1px solid rgba(8,145,178,.2);
                border-radius:13px;padding:1rem 1.3rem;margin-bottom:1rem;font-size:13.5px;color:#94a3b8;">
      Export your flashcard deck as a printable PDF. Generate cards from the
      <strong>Flashcards</strong> page first.
    </div>""", unsafe_allow_html=True)

    if not flashcards:
        st.markdown("""
        <div class="sm-empty" style="padding:2rem;">
          <div class="sm-empty-ico">🃏</div>
          <div class="sm-empty-title">No flashcards generated yet</div>
          <div class="sm-empty-sub">Go to Flashcards → Generate Flashcards, then come back here.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Go to Flashcards →", key="goto_fc"):
            st.session_state.active_page = "Flashcards"; st.rerun()
    else:
        fc_title    = st.text_input("Deck title", placeholder="My Flashcard Deck", key="fc_pdf_t")
        diff_filter = st.selectbox("Filter by difficulty", ["All","easy","medium","hard"], key="fc_diff")
        filtered    = flashcards if diff_filter == "All" else [c for c in flashcards if c.get("difficulty") == diff_filter]

        st.markdown(f'<p style="font-size:13px;color:#94a3b8;margin-bottom:.8rem;">{len(filtered)} cards will be exported</p>', unsafe_allow_html=True)

        # Preview first 3
        for card in filtered[:3]:
            diff  = card.get("difficulty", "medium")
            color = {"easy":"#059669","medium":"#f59e0b","hard":"#e11d48"}.get(diff, "#a78bfa")
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06);
                        border-radius:10px;padding:.8rem 1rem;margin-bottom:6px;">
              <span style="font-size:10px;font-weight:700;color:{color};text-transform:uppercase;
                           padding:2px 7px;border-radius:100px;background:{color}22;">{diff}</span>
              <div style="font-size:13.5px;color:#f8fafc;margin-top:.4rem;font-weight:500;">
                {card.get("question","")[:90]}{"…" if len(card.get("question",""))>90 else ""}</div>
            </div>""", unsafe_allow_html=True)

        if len(filtered) > 3:
            st.markdown(f'<p style="font-size:12px;color:#334155;text-align:center;">+{len(filtered)-3} more cards in PDF</p>', unsafe_allow_html=True)

        if filtered:
            try:
                from features.pdf_export import export_flashcards_pdf
                pdf_bytes = export_flashcards_pdf(
                    filtered,
                    subject   = fc_title or "Flashcard Deck",
                    user_name = user.get("name", "Student"),
                )
                st.download_button(
                    "⬇️ Download Flashcards PDF", pdf_bytes,
                    "flashcards.pdf", "application/pdf",
                    key="dl_fc", use_container_width=True,
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}. Install fpdf2: pip install fpdf2")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — QUIZ RESULTS PDF
# ══════════════════════════════════════════════════════════════════════════════
with tab_quiz:
    st.markdown("""
    <div style="background:rgba(5,150,105,.07);border:1px solid rgba(5,150,105,.2);
                border-radius:13px;padding:1rem 1.3rem;margin-bottom:1rem;font-size:13.5px;color:#94a3b8;">
      Download your latest quiz results with per-question review and explanations.
      Take a quiz from <strong>Quiz Me</strong> or <strong>Smart Quiz</strong> first.
    </div>""", unsafe_allow_html=True)

    if not quiz_result or not quiz_qs:
        st.markdown("""
        <div class="sm-empty" style="padding:2rem;">
          <div class="sm-empty-ico">📝</div>
          <div class="sm-empty-title">No quiz results yet</div>
          <div class="sm-empty-sub">Take a quiz from Quiz Me or Smart Quiz, then come back here.</div>
        </div>""", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button("Go to Quiz Me →", key="goto_quiz"):
            st.session_state.active_page = "Quiz Me"; st.rerun()
        if col2.button("Go to Smart Quiz →", key="goto_sq"):
            st.session_state.active_page = "Smart Quiz"; st.rerun()
    else:
        score   = quiz_result.get("score_pct", 0)
        mode    = quiz_result.get("mode", "practice").title()
        correct = quiz_result.get("correct", 0)
        wrong   = quiz_result.get("wrong", 0)
        total   = len(quiz_qs)
        color   = "#059669" if score >= 80 else "#f59e0b" if score >= 60 else "#e11d48"
        ans     = st.session_state.get("sq_answers") or st.session_state.get("quiz_answers", {})

        st.markdown(f"""
        <div style="background:rgba(0,0,0,.3);border:1px solid {color}44;border-radius:18px;
                    padding:1.6rem 2rem;text-align:center;margin-bottom:1.2rem;">
          <div style="font-family:Syne,sans-serif;font-size:3rem;font-weight:800;
                      color:{color};line-height:1;">{score:.1f}%</div>
          <div style="font-size:13.5px;color:#94a3b8;margin-top:.4rem;">
            {mode} mode &nbsp;·&nbsp; ✅ {correct} correct &nbsp;·&nbsp;
            ❌ {wrong} wrong &nbsp;·&nbsp; {total} questions
          </div>
        </div>""", unsafe_allow_html=True)

        try:
            from features.pdf_export import export_quiz_pdf
            pdf_bytes = export_quiz_pdf(
                quiz_qs, ans, score,
                topic     = "Quiz Results",
                user_name = user.get("name", "Student"),
            )
            st.download_button(
                "⬇️ Download Quiz Results PDF", pdf_bytes,
                "quiz_results.pdf", "application/pdf",
                key="dl_quiz", use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}. Install fpdf2: pip install fpdf2")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — NOTES PDF (raw text export)
# ══════════════════════════════════════════════════════════════════════════════
with tab_notes:
    st.markdown("""
    <div style="background:rgba(217,119,6,.07);border:1px solid rgba(217,119,6,.2);
                border-radius:13px;padding:1rem 1.3rem;margin-bottom:1rem;font-size:13.5px;color:#94a3b8;">
      Export your uploaded documents' extracted text as a clean PDF for offline reading.
    </div>""", unsafe_allow_html=True)

    uploaded_files = st.session_state.get("uploaded_files", [])
    if not uploaded_files:
        st.markdown("""
        <div class="sm-empty" style="padding:2rem;">
          <div class="sm-empty-ico">📖</div>
          <div class="sm-empty-title">No documents uploaded</div>
          <div class="sm-empty-sub">Upload documents from Ask Notes first.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="font-size:13px;color:#94a3b8;margin-bottom:.8rem;">Select document to export:</p>', unsafe_allow_html=True)
        doc_names = [f["name"] for f in uploaded_files]
        selected  = st.selectbox("Document", doc_names, key="notes_sel")

        if st.button("📖 Export Notes as PDF", use_container_width=True, key="exp_notes"):
            doc_info = next((f for f in uploaded_files if f["name"] == selected), None)
            if doc_info:
                with st.spinner("Extracting text and building PDF…"):
                    try:
                        from utils.file_handler import extract_text
                        from features.pdf_export import export_summary_pdf
                        data      = extract_text(doc_info["path"])
                        text      = data.get("text", "")
                        pdf_bytes = export_summary_pdf(
                            title        = selected,
                            summary_text = text[:15000],  # cap at 15k chars
                            tldr         = f"Extracted from: {selected}",
                            source_docs  = [selected],
                            user_name    = user.get("name", "Student"),
                        )
                        st.download_button(
                            "⬇️ Download Notes PDF", pdf_bytes,
                            f"notes_{selected}.pdf", "application/pdf",
                            key="dl_notes",
                        )
                        st.success(f"✅ {len(text):,} characters extracted from {selected}")
                    except Exception as e:
                        st.error(f"Export failed: {e}")