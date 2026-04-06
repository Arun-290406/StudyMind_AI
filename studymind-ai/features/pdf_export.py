# features/pdf_export.py
"""
PDF Export — generate beautiful PDFs for:
  - Summary reports
  - Flashcard decks
  - Quiz results
  - Study notes
Uses fpdf2 (pure Python, no wkhtmltopdf needed).
"""

import io
import re
from datetime import datetime
from typing import List, Dict, Optional


def _clean(text: str) -> str:
    """Remove markdown syntax and non-latin chars for PDF safety."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*',     r'\1', text)
    text = re.sub(r'#+\s',          '',    text)
    text = re.sub(r'`(.*?)`',       r'\1', text)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class StudyMindPDF:
    """Base PDF class with consistent branding."""

    PURPLE = (124, 58, 237)
    CYAN   = (8, 145, 178)
    DARK   = (15, 23, 42)
    GRAY   = (100, 116, 139)
    WHITE  = (255, 255, 255)
    BG     = (248, 250, 252)

    def __init__(self):
        from fpdf import FPDF
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=18)
        self.pdf.add_page()
        self._header()

    def _header(self):
        p = self.pdf
        # Purple header bar
        p.set_fill_color(*self.PURPLE)
        p.rect(0, 0, 210, 22, "F")
        p.set_text_color(*self.WHITE)
        p.set_font("Helvetica", "B", 14)
        p.set_y(6)
        p.cell(0, 10, "StudyMind AI", ln=False, align="L", x=10)
        p.set_font("Helvetica", "", 9)
        p.cell(0, 10, f"Generated {datetime.now().strftime('%d %b %Y, %H:%M')}", align="R")
        p.ln(20)
        p.set_text_color(*self.DARK)

    def _section_header(self, title: str):
        p = self.pdf
        p.set_fill_color(*self.BG)
        p.set_draw_color(*self.PURPLE)
        p.set_line_width(0.5)
        p.rect(10, p.get_y(), 190, 9, "FD")
        p.set_font("Helvetica", "B", 11)
        p.set_text_color(*self.PURPLE)
        p.cell(0, 9, f"  {_clean(title)}", ln=True, x=10)
        p.set_text_color(*self.DARK)
        p.ln(3)

    def _body_text(self, text: str, indent: int = 12):
        p = self.pdf
        p.set_font("Helvetica", "", 10)
        p.set_text_color(*self.DARK)
        for line in _clean(text).split("\n"):
            line = line.strip()
            if not line:
                p.ln(3)
                continue
            if line.startswith("- ") or line.startswith("* "):
                p.set_x(indent + 3)
                p.set_font("Helvetica", "", 10)
                p.multi_cell(190 - indent, 5.5, f"• {line[2:]}")
            elif line.startswith("#"):
                p.set_font("Helvetica", "B", 11)
                p.multi_cell(0, 6, line.lstrip("# ").strip(), x=indent)
                p.set_font("Helvetica", "", 10)
            else:
                p.set_x(indent)
                p.multi_cell(190 - indent, 5.5, line)

    def output_bytes(self) -> bytes:
        return self.pdf.output()


# ── Summary PDF ───────────────────────────────────────────────────────────────

def export_summary_pdf(
    title: str,
    summary_text: str,
    tldr: str = "",
    source_docs: List[str] = None,
    user_name: str = "",
) -> bytes:
    doc = StudyMindPDF()
    p   = doc.pdf

    # Title
    p.set_font("Helvetica", "B", 18)
    p.set_text_color(*StudyMindPDF.PURPLE)
    p.cell(0, 12, _clean(title), ln=True, x=10)
    p.set_text_color(*StudyMindPDF.GRAY)
    p.set_font("Helvetica", "", 9)
    info = f"Prepared for: {user_name}  |  Sources: {', '.join(source_docs or [])}"
    p.cell(0, 6, _clean(info), ln=True, x=10)
    p.ln(5)

    # TL;DR
    if tldr:
        doc._section_header("TL;DR — Quick Summary")
        p.set_fill_color(230, 240, 255)
        p.set_x(10)
        p.set_font("Helvetica", "I", 10)
        p.set_text_color(*StudyMindPDF.DARK)
        p.multi_cell(190, 6, _clean(tldr))
        p.ln(4)

    # Full summary
    doc._section_header("Detailed Summary")
    doc._body_text(summary_text)

    return doc.output_bytes()


# ── Flashcard PDF ─────────────────────────────────────────────────────────────

def export_flashcards_pdf(
    flashcards: List[Dict],
    subject: str = "Study Flashcards",
    user_name: str = "",
) -> bytes:
    doc = StudyMindPDF()
    p   = doc.pdf

    p.set_font("Helvetica", "B", 18)
    p.set_text_color(*StudyMindPDF.PURPLE)
    p.cell(0, 12, _clean(subject), ln=True, x=10)
    p.set_font("Helvetica", "", 9)
    p.set_text_color(*StudyMindPDF.GRAY)
    p.cell(0, 6, f"Total: {len(flashcards)} cards  |  {user_name}", ln=True, x=10)
    p.ln(5)

    diff_colors = {
        "easy":   (16, 185, 129),
        "medium": (245, 158, 11),
        "hard":   (239, 68, 68),
    }

    for i, card in enumerate(flashcards, 1):
        diff  = card.get("difficulty", "medium")
        color = diff_colors.get(diff, (124, 58, 237))

        # Card box
        y = p.get_y()
        if y > 250:
            p.add_page()
            y = p.get_y()

        p.set_fill_color(248, 250, 252)
        p.set_draw_color(*color)
        p.set_line_width(0.8)
        p.rect(10, y, 190, 28, "FD")

        # Card number + difficulty
        p.set_font("Helvetica", "B", 8)
        p.set_text_color(*color)
        p.set_xy(12, y + 2)
        p.cell(0, 4, f"#{i}  {diff.upper()}  •  {card.get('topic','')}")

        # Question
        p.set_font("Helvetica", "B", 10)
        p.set_text_color(*StudyMindPDF.DARK)
        p.set_xy(12, y + 7)
        q_text = _clean(card.get("question", ""))[:100]
        p.cell(0, 5, f"Q: {q_text}")

        # Answer
        p.set_font("Helvetica", "", 9.5)
        p.set_text_color(*StudyMindPDF.GRAY)
        p.set_xy(12, y + 14)
        a_text = _clean(card.get("answer", ""))[:120]
        p.cell(0, 5, f"A: {a_text}")

        p.set_y(y + 31)

    return doc.output_bytes()


# ── Quiz Result PDF ───────────────────────────────────────────────────────────

def export_quiz_pdf(
    questions: List[Dict],
    answers: Dict,
    score_pct: float,
    topic: str = "Quiz Results",
    user_name: str = "",
) -> bytes:
    doc = StudyMindPDF()
    p   = doc.pdf

    p.set_font("Helvetica", "B", 18)
    p.set_text_color(*StudyMindPDF.PURPLE)
    p.cell(0, 12, _clean(topic), ln=True, x=10)

    score_col = (16,185,129) if score_pct >= 80 else (245,158,11) if score_pct >= 60 else (239,68,68)
    p.set_font("Helvetica", "B", 28)
    p.set_text_color(*score_col)
    p.cell(0, 16, f"{score_pct:.0f}%", ln=True, x=10)

    p.set_font("Helvetica", "", 10)
    p.set_text_color(*StudyMindPDF.GRAY)
    p.cell(0, 6, f"Student: {user_name}  |  {len(questions)} questions", ln=True, x=10)
    p.ln(4)

    doc._section_header("Question Review")

    for i, q in enumerate(questions, 1):
        chosen  = answers.get(q.get("id", ""), "")
        correct = q.get("correct", "")
        is_ok   = chosen.upper() == correct.upper()
        icon    = "[CORRECT]" if is_ok else "[WRONG]"
        col     = (16,185,129) if is_ok else (239,68,68)

        if p.get_y() > 255: p.add_page()

        p.set_font("Helvetica", "B", 10)
        p.set_text_color(*col)
        p.set_x(10)
        p.cell(0, 6, f"{icon}  Q{i}: {_clean(q.get('question',''))[:80]}", ln=True)

        for letter, text in sorted(q.get("options", {}).items()):
            is_correct_opt = letter == correct
            is_chosen_opt  = letter == chosen
            prefix = "[ANSWER] " if is_correct_opt else ("[YOU] " if is_chosen_opt else "      ")
            c = (16,185,129) if is_correct_opt else ((239,68,68) if is_chosen_opt else StudyMindPDF.GRAY)
            p.set_text_color(*c)
            p.set_font("Helvetica", "B" if is_correct_opt else "", 9)
            p.set_x(18)
            p.cell(0, 5, f"{prefix}{letter}) {_clean(text)[:70]}", ln=True)

        if q.get("explanation"):
            p.set_text_color(8, 145, 178)
            p.set_font("Helvetica", "I", 9)
            p.set_x(18)
            p.multi_cell(170, 5, f"Explanation: {_clean(q['explanation'])[:200]}")
        p.ln(3)

    return doc.output_bytes()
