# app/pages/02_flashcards.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from utils.session_state import init_session_state
from features.flashcard_gen import (
    generate_flashcards, update_card_sm2,
    get_due_cards, sort_cards_by_priority, flashcard_stats
)
init_session_state()

st.markdown('<div class="sm-page-title">Flashcards</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">AI-generated cards with SM-2 spaced repetition — study smarter, not harder</div>', unsafe_allow_html=True)

tab_gen, tab_practice, tab_browse = st.tabs(["⚡  Generate", "🃏  Practice", "📋  Browse All"])

# ── GENERATE ──────────────────────────────────────────────────────────────────
with tab_gen:
    if not st.session_state.docs_indexed:
        st.markdown('<div class="sm-empty"><div class="sm-empty-ico">📁</div><div class="sm-empty-title">Index documents first</div><div class="sm-empty-sub">Go to Ask Notes and upload your PDFs.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sm-highlight"><div class="sm-highlight-title">Generation Settings</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        topic = c1.text_input("Focus topic", placeholder="e.g. Backpropagation")
        num   = c2.slider("Number of cards", 5, 30, 10)
        diff  = c3.selectbox("Difficulty", ["all","easy","medium","hard"])
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("⚡  Generate Flashcards", use_container_width=True):
            with st.spinner("Generating flashcards from your notes…"):
                cards = generate_flashcards(st.session_state.vector_store, topic=topic, num_cards=num, difficulty_filter=diff)
            st.session_state.flashcards.extend(cards)
            st.success(f"✅ Generated **{len(cards)}** flashcards!")
            st.rerun()

        if st.session_state.flashcards:
            st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)
            s = flashcard_stats(st.session_state.flashcards)
            st.markdown(f"""
            <div class="sm-stats">
              <div class="sm-stat"><span class="sm-stat-n">{s['total']}</span><span class="sm-stat-l">Total</span></div>
              <div class="sm-stat"><span class="sm-stat-n" style="color:#67e8f9">{s['due']}</span><span class="sm-stat-l">Due Today</span></div>
              <div class="sm-stat"><span class="sm-stat-n" style="color:#6ee7b7">{s['easy']}</span><span class="sm-stat-l">Easy</span></div>
              <div class="sm-stat"><span class="sm-stat-n" style="color:#fcd34d">{s['medium']}</span><span class="sm-stat-l">Medium</span></div>
              <div class="sm-stat"><span class="sm-stat-n" style="color:#fda4af">{s['hard']}</span><span class="sm-stat-l">Hard</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button("🗑️  Clear All Cards", use_container_width=True):
                st.session_state.flashcards = []
                st.session_state.fc_index = 0
                st.rerun()

# ── PRACTICE ──────────────────────────────────────────────────────────────────
with tab_practice:
    cards = sort_cards_by_priority(st.session_state.flashcards)
    due   = get_due_cards(cards)

    if not cards:
        st.markdown('<div class="sm-empty"><div class="sm-empty-ico">🃏</div><div class="sm-empty-title">No flashcards yet</div><div class="sm-empty-sub">Generate cards from the Generate tab.</div></div>', unsafe_allow_html=True)
    elif not due:
        st.markdown("""
        <div style="text-align:center;padding:3.5rem 2rem;">
          <div style="font-size:3rem;margin-bottom:0.8rem;">🎉</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:800;color:#f1f5f9;">All caught up!</div>
          <div style="color:var(--t2);margin-top:0.4rem;font-size:14px;">No cards due for review right now. Great work!</div>
        </div>""", unsafe_allow_html=True)
    else:
        idx  = st.session_state.fc_index % len(due)
        card = due[idx]
        pct  = (idx + 1) / len(due)

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
          <span style="font-size:12px;color:var(--t2);">Card {idx+1} of {len(due)} due</span>
          <span style="font-size:12px;color:var(--vl);">{int(pct*100)}% through session</span>
        </div>""", unsafe_allow_html=True)
        st.progress(pct)

        diff_map = {"easy":"badge-em","medium":"badge-a","hard":"badge-r"}
        badge = diff_map.get(card.get("difficulty","medium"),"badge-v")
        st.markdown(
            f'<span class="sm-badge {badge}">{card.get("difficulty","medium")}</span>&nbsp;'
            f'<span style="color:var(--t3);font-size:12px;">{card.get("topic","")}</span>',
            unsafe_allow_html=True
        )

        st.markdown(f"""
        <div class="sm-fc">
          <div class="sm-fc-q">{card["question"]}</div>
          <div class="sm-fc-hint">{"" if st.session_state.fc_show_answer else "tap to reveal answer"}</div>
        </div>""", unsafe_allow_html=True)

        if not st.session_state.fc_show_answer:
            if st.button("👁️  Reveal Answer", use_container_width=True):
                st.session_state.fc_show_answer = True; st.rerun()
        else:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba(16,185,129,0.09),rgba(6,182,212,0.05));
                        border:1px solid rgba(16,185,129,0.26);border-radius:var(--r16);
                        padding:1.4rem 1.6rem;margin:0.7rem 0;">
              <div style="font-size:10px;font-weight:800;letter-spacing:0.1em;text-transform:uppercase;color:#6ee7b7;margin-bottom:0.5rem;">Answer</div>
              <div style="color:#f1f5f9;line-height:1.68;font-size:15px;">{card["answer"]}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<p style="font-size:13px;color:var(--t2);font-weight:500;margin:0.8rem 0 0.3rem;">How well did you know this?</p>', unsafe_allow_html=True)
            c1,c2,c3,c4 = st.columns(4)
            def _rate(r):
                updated = update_card_sm2(card, r)
                for i,c in enumerate(st.session_state.flashcards):
                    if c["id"] == card["id"]: st.session_state.flashcards[i] = updated; break
                st.session_state.fc_index += 1
                st.session_state.fc_show_answer = False
                st.rerun()
            if c1.button("😕 Forgot",  use_container_width=True): _rate(0)
            if c2.button("😐 Hard",    use_container_width=True): _rate(1)
            if c3.button("🙂 Good",    use_container_width=True): _rate(3)
            if c4.button("😄 Easy",    use_container_width=True): _rate(5)

# ── BROWSE ────────────────────────────────────────────────────────────────────
with tab_browse:
    if not st.session_state.flashcards:
        st.markdown('<div class="sm-empty"><div class="sm-empty-ico">📋</div><div class="sm-empty-title">No cards yet</div></div>', unsafe_allow_html=True)
    else:
        search = st.text_input("🔍  Search cards", placeholder="Search by question or topic…")
        show   = st.session_state.flashcards
        if search: show = [c for c in show if search.lower() in c["question"].lower() or search.lower() in c.get("topic","").lower()]

        for card in show:
            d = card.get("difficulty","medium")
            icon = {"easy":"🟢","medium":"🟡","hard":"🔴"}.get(d,"⚪")
            with st.expander(f"{icon}  {card['question'][:78]}…"):
                st.markdown(f"""
                <div style="background:rgba(139,92,246,0.07);border-radius:var(--r12);padding:1rem;margin-bottom:0.6rem;">
                  <div style="font-size:10px;color:var(--vl);font-weight:800;letter-spacing:0.1em;margin-bottom:0.3rem;">ANSWER</div>
                  <div style="color:#f1f5f9;line-height:1.6;">{card["answer"]}</div>
                </div>""", unsafe_allow_html=True)
                mc, ml, mt, md = st.columns([1,1,2,1])
                mc.markdown(f'<span class="sm-badge badge-v">{d}</span>', unsafe_allow_html=True)
                ml.markdown(f'<span style="font-size:12px;color:var(--t3)">Next {card.get("interval",1)}d</span>', unsafe_allow_html=True)
                mt.markdown(f'<span style="font-size:12px;color:var(--t3)">{card.get("topic","")}</span>', unsafe_allow_html=True)
                if md.button("Delete", key=f"del_{card['id']}"):
                    st.session_state.flashcards = [c for c in st.session_state.flashcards if c["id"] != card["id"]]
                    st.rerun()