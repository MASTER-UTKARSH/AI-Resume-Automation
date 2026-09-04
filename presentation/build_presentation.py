#!/usr/bin/env python3
"""
Script to generate the Minor Project Presentation PPT for JUET Guna.
Adheres strictly to Presentation format.pptx, PPT_Instructions.pdf, and project data.
"""

import os
import sys
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# --- Color Palette (Matching JUET template & Modern Academic Style) ---
COLOR_NAVY = RGBColor(0x1B, 0x36, 0x5D)        # Deep Navy for primary headers
COLOR_STEEL = RGBColor(0x36, 0x60, 0x92)       # Steel Blue for section accents
COLOR_ORANGE = RGBColor(0xD9, 0x53, 0x1E)      # Template Accent Orange
COLOR_DARK_TEXT = RGBColor(0x1E, 0x29, 0x3B)   # Slate 800 for high readability
COLOR_MUTED_TEXT = RGBColor(0x47, 0x55, 0x69)  # Slate 600 for subtext
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_BG_CARD = RGBColor(0xF8, 0xFA, 0xFC)     # Slate 50 card fill
COLOR_BORDER = RGBColor(0xCB, 0xD5, 0xE1)      # Slate 300 border
COLOR_CARD_ALT = RGBColor(0xF1, 0xF5, 0xF9)    # Slate 100
COLOR_HIGHLIGHT_BLUE = RGBColor(0x25, 0x63, 0xEB)
COLOR_SUCCESS_BG = RGBColor(0xDC, 0xFC, 0xE7)
COLOR_SUCCESS_TXT = RGBColor(0x15, 0x80, 0x3D)
COLOR_PROG_BG = RGBColor(0xFE, 0xF9, 0xC3)
COLOR_PROG_TXT = RGBColor(0xA1, 0x62, 0x07)
COLOR_PEND_BG = RGBColor(0xF1, 0xF5, 0xF9)
COLOR_PEND_TXT = RGBColor(0x64, 0x74, 0x8B)

FONT_HEADING = "Arial"
FONT_BODY = "Calibri"

def add_slide_number(slide, num_str):
    """Adds the slide number inside the orange block of the template."""
    txBox = slide.shapes.add_textbox(Inches(0.0), Inches(1.39), Inches(0.58), Inches(0.27))
    tf = txBox.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.0)
    tf.margin_right = Inches(0.0)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.0)
    p = tf.paragraphs[0]
    p.text = str(num_str)
    p.alignment = PP_ALIGN.CENTER
    p.font.name = FONT_HEADING
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

def create_card(slide, left, top, width, height, bg_color=COLOR_BG_CARD, border_color=COLOR_BORDER):
    """Creates a stylized rectangular card container."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape

def format_cell(cell, text, bold=False, size=11, color=COLOR_DARK_TEXT, bg_color=None, align=PP_ALIGN.LEFT):
    """Utility to style a table cell."""
    cell.text = text
    if bg_color:
        cell.fill.solid()
        cell.fill.fore_color.rgb = bg_color
    p = cell.text_frame.paragraphs[0]
    p.alignment = align
    p.font.name = FONT_BODY
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE

def main():
    prs = Presentation('Presentation format.pptx')
    slide_layout = prs.slide_layouts[1] # Title and Content
    
    # --- SLIDE 1: Cover Slide (Update Existing Slide 1) ---
    slide1 = prs.slides[0]
    title1 = slide1.shapes.title
    title1.text = "AI-POWERED RESUME AUTOMATION SYSTEM"
    for p in title1.text_frame.paragraphs:
        p.font.name = FONT_HEADING
        p.font.size = Pt(27)
        p.font.bold = True
        p.font.color.rgb = COLOR_NAVY
        p.alignment = PP_ALIGN.CENTER
        
    for shape in slide1.shapes:
        if shape.has_text_frame:
            txt = shape.text_frame.text
            if "Student 1" in txt or "by:" in txt:
                tf = shape.text_frame
                tf.clear()
                p0 = tf.paragraphs[0]
                p0.text = "by:"
                p0.font.bold = True
                p0.font.size = Pt(13)
                p0.font.color.rgb = COLOR_NAVY
                p0.alignment = PP_ALIGN.CENTER
                
                students = [
                    "Utkarsh Shah (241B278)",
                    "Utsav Kothari (241B279)",
                    "Yashasv Pandey (241B295)"
                ]
                for st in students:
                    p = tf.add_paragraph()
                    p.text = st
                    p.font.size = Pt(13)
                    p.font.bold = True
                    p.font.color.rgb = COLOR_DARK_TEXT
                    p.alignment = PP_ALIGN.CENTER
            elif "Under the supervision" in txt or "Guide Name" in txt:
                tf = shape.text_frame
                tf.clear()
                p0 = tf.paragraphs[0]
                p0.text = "Under the supervision of:"
                p0.font.bold = True
                p0.font.size = Pt(13)
                p0.font.color.rgb = COLOR_NAVY
                p0.alignment = PP_ALIGN.CENTER
                
                p1 = tf.add_paragraph()
                p1.text = "Ms. Sarita Sahni"
                p1.font.size = Pt(15)
                p1.font.bold = True
                p1.font.color.rgb = COLOR_STEEL
                p1.alignment = PP_ALIGN.CENTER

    # Remove template slides 2, 3, 4
    while len(prs.slides) > 1:
        rId = prs.slides._sldIdLst[1].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[1]

    # --- SLIDE 2: Table of Contents ---
    slide2 = prs.slides.add_slide(slide_layout)
    slide2.shapes.title.text = "Table of Contents"
    slide2.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide2.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide2.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide2.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide2, 2)
    
    for shp in list(slide2.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    agenda_items = [
        ("1. Introduction", "Project overview, core objectives & target users"),
        ("2. Problem Statement", "Key challenges in entry-level job applications"),
        ("3. Literature Review", "Existing solutions, comparison matrix & gaps"),
        ("4. Work Plan", "10-week milestones & current progress log"),
        ("5. Individual Contribution", "Role allocation & modular ownership"),
        ("6. Work Done So Far", "System architecture, behavioral workflow & Clyde UI"),
        ("7. Work to be Done", "Browser extension, portal adapters & evaluation"),
        ("8. Conclusion", "Progress summary & expected outcomes"),
        ("9. References", "Academic citations in official IEEE format")
    ]
    
    col_w = Inches(4.25)
    row_h = Inches(0.92)
    left_col = Inches(0.65)
    right_col = Inches(5.1)
    
    for i, (title, desc) in enumerate(agenda_items):
        c_left = left_col if i < 5 else right_col
        row_idx = i if i < 5 else i - 5
        c_top = Inches(1.85) + row_idx * Inches(1.02)
        
        card = create_card(slide2, c_left, c_top, col_w, row_h, COLOR_BG_CARD, COLOR_BORDER)
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.2)
        tf.margin_top = Inches(0.12)
        
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_STEEL
        
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = COLOR_MUTED_TEXT

    # --- SLIDE 3: 1. Introduction ---
    slide3 = prs.slides.add_slide(slide_layout)
    slide3.shapes.title.text = "1. Introduction"
    slide3.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide3.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide3.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide3.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide3, 3)
    
    for shp in list(slide3.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    card_l = create_card(slide3, Inches(0.65), Inches(1.85), Inches(4.25), Inches(3.8), COLOR_BG_CARD, COLOR_BORDER)
    tf_l = card_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = Inches(0.25)
    tf_l.margin_right = Inches(0.2)
    tf_l.margin_top = Inches(0.2)
    
    p = tf_l.paragraphs[0]
    p.text = "Project Overview"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    overview_bullets = [
        "AI-assisted career copilot designed specifically for college students and freshers.",
        "Solves the fragmented job hunting journey by uniting discovery, evaluation, document tailoring, and tracking.",
        "Extracts normalized candidate profiles from unstructured resumes to eliminate redundant parsing.",
        "Combines LLM language comprehension with deterministic scoring and safety rules."
    ]
    for b in overview_bullets:
        p = tf_l.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)

    card_r = create_card(slide3, Inches(5.1), Inches(1.85), Inches(4.25), Inches(3.8), COLOR_BG_CARD, COLOR_BORDER)
    tf_r = card_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = Inches(0.25)
    tf_r.margin_right = Inches(0.2)
    tf_r.margin_top = Inches(0.2)
    
    p = tf_r.paragraphs[0]
    p.text = "Project Objectives"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    objectives_bullets = [
        "Reduce repetitive effort in searching, customizing, and applying across multiple job boards.",
        "Deliver multi-factor job compatibility ranking (semantic similarity, skills match, preferences).",
        "Generate ATS-compliant, tailored resumes and targeted cover letters without fabrications.",
        "Establish Human-In-The-Loop approval gates: automation assists, but user retains final authorization."
    ]
    for b in objectives_bullets:
        p = tf_r.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)

    card_b = create_card(slide3, Inches(0.65), Inches(5.8), Inches(8.7), Inches(0.95), COLOR_CARD_ALT, COLOR_STEEL)
    tf_b = card_b.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = Inches(0.2)
    tf_b.margin_top = Inches(0.12)
    
    p = tf_b.paragraphs[0]
    p.text = "End-to-End Application Workflow Pipeline:"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    p2 = tf_b.add_paragraph()
    p2.text = "Resume Upload  ➜  Profile Structuring  ➜  Job Discovery  ➜  Multi-Factor Match  ➜  ATS Tailoring  ➜  Reviewer Check  ➜  User Approval  ➜  Extension Autofill  ➜  Status Tracking"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(9.5)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_DARK_TEXT
    p2.space_before = Pt(4)

    # --- SLIDE 4: 2. Problem Statement ---
    slide4 = prs.slides.add_slide(slide_layout)
    slide4.shapes.title.text = "2. Problem Statement"
    slide4.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide4.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide4.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide4.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide4, 4)
    
    for shp in list(slide4.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    card1 = create_card(slide4, Inches(0.65), Inches(1.85), Inches(4.25), Inches(3.6), COLOR_BG_CARD, COLOR_BORDER)
    tf1 = card1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = Inches(0.25)
    tf1.margin_top = Inches(0.2)
    
    p = tf1.paragraphs[0]
    p.text = "Challenges Faced by Students"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    c1_bullets = [
        "Fragmented Portals: Students spend endless hours navigating company websites, LinkedIn, and internship boards.",
        "Generic Resumes: Submitting a single static resume leads to immediate rejection by ATS filters.",
        "Repetitive Tailoring: Manually customizing resumes and cover letters for dozens of roles causes severe burnout.",
        "Lost Applications: Tracking status, versions, and application dates in spreadsheets is tedious and error-prone."
    ]
    for b in c1_bullets:
        p = tf1.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(6)

    card2 = create_card(slide4, Inches(5.1), Inches(1.85), Inches(4.25), Inches(3.6), COLOR_BG_CARD, COLOR_BORDER)
    tf2 = card2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = Inches(0.25)
    tf2.margin_top = Inches(0.2)
    
    p = tf2.paragraphs[0]
    p.text = "Flaws in Current Automation"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_ORANGE
    
    c2_bullets = [
        "Uncontrolled Scripts: Existing bot appliers submit without user oversight, risking bans and wrong applications.",
        "Hallucinated Claims: Naive LLM resume builders frequently invent fake experience or stuffed keywords.",
        "No Session Reusability: Cloud automation tools require storing credentials, risking security leaks.",
        "Disconnected Tooling: Resume builders, job alerts, and tracker boards operate in isolated silos."
    ]
    for b in c2_bullets:
        p = tf2.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(6)

    card_core = create_card(slide4, Inches(0.65), Inches(5.6), Inches(8.7), Inches(1.15), COLOR_CARD_ALT, COLOR_STEEL)
    tf_core = card_core.text_frame
    tf_core.word_wrap = True
    tf_core.margin_left = Inches(0.25)
    tf_core.margin_top = Inches(0.12)
    
    p = tf_core.paragraphs[0]
    p.text = "Core Problem Addressed:"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    p2 = tf_core.add_paragraph()
    p2.text = "“How can an intelligent, multi-agent system eliminate repetitive job application effort while preserving ATS relevance, document truthfulness, and guaranteed user approval at every critical step?”"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(11.5)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_NAVY
    p2.space_before = Pt(4)

    # --- SLIDE 5: 3. Literature Review & Research Gap ---
    slide5 = prs.slides.add_slide(slide_layout)
    slide5.shapes.title.text = "3. Literature Review & Research Gap"
    slide5.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide5.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide5.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide5.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide5, 5)
    
    for shp in list(slide5.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    # Table
    table_shape = slide5.shapes.add_table(5, 6, Inches(0.65), Inches(1.85), Inches(8.7), Inches(2.2))
    table = table_shape.table
    table.columns[0].width = Inches(2.1)
    table.columns[1].width = Inches(1.3)
    table.columns[2].width = Inches(1.3)
    table.columns[3].width = Inches(1.3)
    table.columns[4].width = Inches(1.3)
    table.columns[5].width = Inches(1.4)

    headers = ["System / Approach", "Job Discovery", "Resume Tailoring", "Auto Apply", "Tracking", "User Approval"]
    for col_idx, h in enumerate(headers):
        format_cell(table.cell(0, col_idx), h, bold=True, size=10.5, color=COLOR_WHITE, bg_color=COLOR_STEEL, align=PP_ALIGN.CENTER)

    matrix_rows = [
        ("Traditional Job Boards (LinkedIn, Indeed)", "Yes", "Limited", "No", "Limited", "N/A"),
        ("Auto-Apply Bots (AIHawk, Scripts)", "Limited", "Basic / None", "Yes (Aggressive)", "Limited", "No (Risk of Bans)"),
        ("AI Resume Builders (Novoresume, etc.)", "No", "Yes (Manual)", "No", "No", "N/A"),
        ("Proposed System (Career Copilot)", "Yes (Hybrid Adapters)", "Yes (ATS Verified)", "Supported Portals", "Yes (Real-time)", "Yes (Mandatory Gate)")
    ]

    for row_idx, r in enumerate(matrix_rows):
        bg = COLOR_WHITE if row_idx % 2 == 0 else COLOR_CARD_ALT
        if row_idx == 3:
            bg = COLOR_SUCCESS_BG
        for col_idx, val in enumerate(r):
            bold = True if (row_idx == 3 or col_idx == 0) else False
            color = COLOR_SUCCESS_TXT if row_idx == 3 else COLOR_DARK_TEXT
            align = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.CENTER
            format_cell(table.cell(row_idx + 1, col_idx), val, bold=bold, size=9.5, color=color, bg_color=bg, align=align)

    card_gap = create_card(slide5, Inches(0.65), Inches(4.3), Inches(4.25), Inches(2.55), COLOR_BG_CARD, COLOR_BORDER)
    tf_gap = card_gap.text_frame
    tf_gap.word_wrap = True
    tf_gap.margin_left = Inches(0.2)
    tf_gap.margin_top = Inches(0.15)
    
    p = tf_gap.paragraphs[0]
    p.text = "Identified Research Gaps"
    p.font.name = FONT_HEADING
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_ORANGE
    
    gaps = [
        "Fragmented Tooling: Job search, document drafting, and application tracking are isolated.",
        "Unverified AI Output: Generic LLM resumes suffer from keyword stuffing and inaccurate claims.",
        "Safety Neglect: Autonomous scripts submit without user review, risking irrelevance and bans."
    ]
    for g in gaps:
        p = tf_gap.add_paragraph()
        p.text = "• " + g
        p.font.name = FONT_BODY
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(4)

    card_imp = create_card(slide5, Inches(5.1), Inches(4.3), Inches(4.25), Inches(2.55), COLOR_BG_CARD, COLOR_BORDER)
    tf_imp = card_imp.text_frame
    tf_imp.word_wrap = True
    tf_imp.margin_left = Inches(0.2)
    tf_imp.margin_top = Inches(0.15)
    
    p = tf_imp.paragraphs[0]
    p.text = "Proposed Improvements & Innovation"
    p.font.name = FONT_HEADING
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    imps = [
        "Unified Multi-Agent Architecture: Orchestrates parsing, matching, tailoring, and tracking.",
        "Drafter ➜ Reviewer ➜ Verification Loop: Deterministic scoring and PDF verification eliminate hallucinated claims.",
        "Browser Extension Architecture: Executes actions within the user's active session without exposing credentials."
    ]
    for im in imps:
        p = tf_imp.add_paragraph()
        p.text = "• " + im
        p.font.name = FONT_BODY
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(4)

    # --- SLIDE 6: 4. Work Plan ---
    slide6 = prs.slides.add_slide(slide_layout)
    slide6.shapes.title.text = "4. Work Plan"
    slide6.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide6.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide6.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide6.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide6, 6)
    
    for shp in list(slide6.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    table_shape6 = slide6.shapes.add_table(11, 3, Inches(0.65), Inches(1.85), Inches(8.7), Inches(4.6))
    table6 = table_shape6.table
    table6.columns[0].width = Inches(1.5)
    table6.columns[1].width = Inches(5.2)
    table6.columns[2].width = Inches(2.0)

    format_cell(table6.cell(0, 0), "Week", bold=True, size=11, color=COLOR_WHITE, bg_color=COLOR_STEEL, align=PP_ALIGN.CENTER)
    format_cell(table6.cell(0, 1), "Planned Work", bold=True, size=11, color=COLOR_WHITE, bg_color=COLOR_STEEL, align=PP_ALIGN.LEFT)
    format_cell(table6.cell(0, 2), "Status", bold=True, size=11, color=COLOR_WHITE, bg_color=COLOR_STEEL, align=PP_ALIGN.CENTER)

    weeks = [
        ("Week 1", "Problem identification, student user interviews, and requirement analysis", "Completed", COLOR_SUCCESS_BG, COLOR_SUCCESS_TXT),
        ("Week 2", "Literature review, existing system benchmarking (AIHawk, LoopCV, LinkedIn bots)", "Completed", COLOR_SUCCESS_BG, COLOR_SUCCESS_TXT),
        ("Week 3", "Frontend architecture, Clyde Dark Editorial design system & component mockup", "Completed", COLOR_SUCCESS_BG, COLOR_SUCCESS_TXT),
        ("Week 4", "Backend event-driven multi-agent architecture and FastAPI service design", "Completed", COLOR_SUCCESS_BG, COLOR_SUCCESS_TXT),
        ("Week 5", "Multi-user database schema, relational domain modeling, and FAISS vector design", "Completed", COLOR_SUCCESS_BG, COLOR_SUCCESS_TXT),
        ("Week 6", "Resume upload, structured candidate profile parsing, and profile data models", "Completed", COLOR_SUCCESS_BG, COLOR_SUCCESS_TXT),
        ("Week 7", "FAISS vector embedding pipeline and multi-factor semantic job matching module", "Completed", COLOR_SUCCESS_BG, COLOR_SUCCESS_TXT),
        ("Week 8", "AI Agent workflows (ATS agent, Drafter-Reviewer revision loop, model router)", "In Progress", COLOR_PROG_BG, COLOR_PROG_TXT),
        ("Week 9", "Browser extension development, supported portal form mapping & autofill engine", "In Progress", COLOR_PROG_BG, COLOR_PROG_TXT),
        ("Week 10", "System integration, ATS benchmark evaluation, user testing & final viva presentation", "Pending", COLOR_PEND_BG, COLOR_PEND_TXT),
    ]

    for idx, (w, task, status, s_bg, s_txt) in enumerate(weeks):
        bg = COLOR_WHITE if idx % 2 == 0 else COLOR_CARD_ALT
        format_cell(table6.cell(idx+1, 0), w, bold=True, size=10, color=COLOR_STEEL, bg_color=bg, align=PP_ALIGN.CENTER)
        format_cell(table6.cell(idx+1, 1), task, bold=False, size=10, color=COLOR_DARK_TEXT, bg_color=bg, align=PP_ALIGN.LEFT)
        format_cell(table6.cell(idx+1, 2), status, bold=True, size=10, color=s_txt, bg_color=s_bg, align=PP_ALIGN.CENTER)

    p_note = slide6.shapes.add_textbox(Inches(0.65), Inches(6.55), Inches(8.7), Inches(0.3)).text_frame.paragraphs[0]
    p_note.text = "* Status directly aligns with official weekly reports (Completed up to Frontend, Resume Parsing, AI Agent, and FAISS)."
    p_note.font.name = FONT_BODY
    p_note.font.size = Pt(9.5)
    p_note.font.italic = True
    p_note.font.color.rgb = COLOR_MUTED_TEXT

    # --- SLIDE 7: 5. Individual Contribution ---
    slide7 = prs.slides.add_slide(slide_layout)
    slide7.shapes.title.text = "5. Individual Contribution"
    slide7.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide7.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide7.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide7.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide7, 7)
    
    for shp in list(slide7.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    table_shape7 = slide7.shapes.add_table(4, 3, Inches(0.65), Inches(1.85), Inches(8.7), Inches(3.2))
    table7 = table_shape7.table
    table7.columns[0].width = Inches(2.2)
    table7.columns[1].width = Inches(1.6)
    table7.columns[2].width = Inches(4.9)

    format_cell(table7.cell(0, 0), "Member Name", bold=True, size=11, color=COLOR_WHITE, bg_color=COLOR_STEEL, align=PP_ALIGN.LEFT)
    format_cell(table7.cell(0, 1), "Enrollment No.", bold=True, size=11, color=COLOR_WHITE, bg_color=COLOR_STEEL, align=PP_ALIGN.CENTER)
    format_cell(table7.cell(0, 2), "Core Contribution & System Ownership", bold=True, size=11, color=COLOR_WHITE, bg_color=COLOR_STEEL, align=PP_ALIGN.LEFT)

    team_data = [
        ("Utkarsh Shah", "241B278", "System Architecture, Event-Driven Backend (FastAPI, Redis event queue), Multi-Agent Orchestration & Model Router (GLM, Qwen, Groq)."),
        ("Utsav Kothari", "241B279", "Frontend Architecture, Clyde Dark Editorial UI/UX implementation, Agent Dashboard, Resume Center, and WebSocket state management."),
        ("Yashasv Pandey", "241B295", "Resume Parsing Engine, Structured Profile Extraction, FAISS Vector Embedding Store, and Multi-Factor Job Matching Algorithm.")
    ]

    for idx, (name, enr, contrib) in enumerate(team_data):
        bg = COLOR_WHITE if idx % 2 == 0 else COLOR_CARD_ALT
        format_cell(table7.cell(idx+1, 0), name, bold=True, size=11, color=COLOR_NAVY, bg_color=bg, align=PP_ALIGN.LEFT)
        format_cell(table7.cell(idx+1, 1), enr, bold=True, size=11, color=COLOR_STEEL, bg_color=bg, align=PP_ALIGN.CENTER)
        format_cell(table7.cell(idx+1, 2), contrib, bold=False, size=10.5, color=COLOR_DARK_TEXT, bg_color=bg, align=PP_ALIGN.LEFT)

    card_collab = create_card(slide7, Inches(0.65), Inches(5.3), Inches(8.7), Inches(1.4), COLOR_BG_CARD, COLOR_BORDER)
    tf_c = card_collab.text_frame
    tf_c.word_wrap = True
    tf_c.margin_left = Inches(0.25)
    tf_c.margin_top = Inches(0.15)
    
    p = tf_c.paragraphs[0]
    p.text = "Collaborative Team Responsibilities"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    collab_bullets = [
        "Joint requirement engineering and analysis of college student job-application friction points.",
        "Collaborative system design, behavioral sequence modeling, and end-to-end data pipeline validation.",
        "Unified testing, ATS scoring benchmark evaluation, documentation, and department presentation."
    ]
    for b in collab_bullets:
        p = tf_c.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(4)

    # --- SLIDE 8: 6. Work Done So Far - System Architecture (Structural UML) ---
    slide8 = prs.slides.add_slide(slide_layout)
    slide8.shapes.title.text = "6. Work Done So Far: System Architecture"
    slide8.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide8.shapes.title.text_frame.paragraphs[0].font.size = Pt(22)
    slide8.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide8.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide8, 8)
    
    for shp in list(slide8.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    tier_w = Inches(8.7)
    
    # Tier 1: Client Layer (Zero text in container card itself)
    create_card(slide8, Inches(0.65), Inches(1.80), tier_w, Inches(1.28), COLOR_BG_CARD, COLOR_STEEL)
    lbl1 = slide8.shapes.add_textbox(Inches(0.85), Inches(1.83), Inches(8.3), Inches(0.28))
    lbl1.text_frame.word_wrap = False
    lbl1.text_frame.margin_left = Inches(0.0)
    lbl1.text_frame.margin_top = Inches(0.0)
    p = lbl1.text_frame.paragraphs[0]
    p.text = "1. PRESENTATION & CLIENT LAYER (React 18, TypeScript, Clyde Dark Editorial UI)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    sub_w = Inches(1.95)
    sub_h = Inches(0.78)
    sub_top = Inches(2.18)
    t1_modules = [
        ("Agent Dashboard", "Natural language chat, task activity & telemetry"),
        ("Resume Center", "PDF upload, structured profile & ATS versioning"),
        ("Job Discovery", "Semantic match scores, filters & role cards"),
        ("Browser Extension", "DOM inspection, form mapper & session autofill")
    ]
    for idx, (m_t, m_d) in enumerate(t1_modules):
        s_box = create_card(slide8, Inches(0.80) + idx * Inches(2.12), sub_top, sub_w, sub_h, COLOR_WHITE, COLOR_BORDER)
        stf = s_box.text_frame
        stf.word_wrap = True
        stf.margin_left = Inches(0.12)
        stf.margin_top = Inches(0.08)
        sp1 = stf.paragraphs[0]
        sp1.text = m_t
        sp1.font.bold = True
        sp1.font.size = Pt(9.5)
        sp1.font.color.rgb = COLOR_NAVY
        sp2 = stf.add_paragraph()
        sp2.text = m_d
        sp2.font.size = Pt(7.5)
        sp2.font.color.rgb = COLOR_MUTED_TEXT

    # Tier 2: Multi-Agent Layer
    create_card(slide8, Inches(0.65), Inches(3.22), tier_w, Inches(2.10), COLOR_CARD_ALT, COLOR_NAVY)
    lbl2 = slide8.shapes.add_textbox(Inches(0.85), Inches(3.26), Inches(8.3), Inches(0.28))
    lbl2.text_frame.word_wrap = False
    lbl2.text_frame.margin_left = Inches(0.0)
    lbl2.text_frame.margin_top = Inches(0.0)
    p = lbl2.text_frame.paragraphs[0]
    p.text = "2. EVENT-DRIVEN MULTI-AGENT BACKEND LAYER (FastAPI Gateway + Redis Event Bus)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY
    
    agents = [
        ("Orchestrator Agent", "Workflow planner"),
        ("Resume Agent", "Parser & tailor"),
        ("Job Discovery Agent", "Source adapters"),
        ("ATS Agent", "Scoring & verifier"),
        ("Cover Letter Agent", "Targeted drafting"),
        ("Reviewer Agent", "Quality & audit"),
        ("Application Agent", "Submission logic"),
        ("Tracking Agent", "Telemetry & logs")
    ]
    a_w = Inches(1.95)
    a_h = Inches(0.48)
    for idx, (a_n, a_r) in enumerate(agents):
        col_i = idx % 4
        row_i = idx // 4
        c_left = Inches(0.80) + col_i * Inches(2.12)
        c_top = Inches(3.58) + row_i * Inches(0.56)
        abox = create_card(slide8, c_left, c_top, a_w, a_h, COLOR_WHITE, COLOR_BORDER)
        atf = abox.text_frame
        atf.word_wrap = True
        atf.margin_left = Inches(0.10)
        atf.margin_top = Inches(0.05)
        ap1 = atf.paragraphs[0]
        ap1.text = a_n
        ap1.font.bold = True
        ap1.font.size = Pt(9)
        ap1.font.color.rgb = COLOR_STEEL
        ap2 = atf.add_paragraph()
        ap2.text = a_r
        ap2.font.size = Pt(7)
        ap2.font.color.rgb = COLOR_MUTED_TEXT

    mr_box = create_card(slide8, Inches(0.80), Inches(4.78), Inches(8.40), Inches(0.40), COLOR_NAVY, None)
    mrtf = mr_box.text_frame
    mrtf.word_wrap = True
    mrtf.margin_left = Inches(0.15)
    mrtf.margin_top = Inches(0.06)
    mrp = mrtf.paragraphs[0]
    mrp.text = "Central Model Router: GLM (Drafting/Writing) | Qwen (Reasoning) | Groq (Fast Inference) | Ollama (Local Fallback)"
    mrp.font.name = FONT_BODY
    mrp.font.size = Pt(8.5)
    mrp.font.bold = True
    mrp.font.color.rgb = COLOR_WHITE
    mrp.alignment = PP_ALIGN.CENTER

    # Tier 3: Storage & Vector Layer
    create_card(slide8, Inches(0.65), Inches(5.45), tier_w, Inches(1.35), COLOR_BG_CARD, COLOR_STEEL)
    lbl3 = slide8.shapes.add_textbox(Inches(0.85), Inches(5.50), Inches(8.3), Inches(0.28))
    lbl3.text_frame.word_wrap = False
    lbl3.text_frame.margin_left = Inches(0.0)
    lbl3.text_frame.margin_top = Inches(0.0)
    p = lbl3.text_frame.paragraphs[0]
    p.text = "3. DATA PERSISTENCE & VECTOR INTELLIGENCE LAYER"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    t3_modules = [
        ("PostgreSQL (Relational Store)", "Multi-user tables: Users, Resumes, Jobs, Applications, Events"),
        ("FAISS (Vector Store)", "High-performance embedding indices for resume & job vectors"),
        ("Redis (Cache & Event Queue)", "Decoupled pub/sub event bus, transient states, rate limiting")
    ]
    for idx, (s_n, s_d) in enumerate(t3_modules):
        s_box = create_card(slide8, Inches(0.80) + idx * Inches(2.86), Inches(5.82), Inches(2.68), Inches(0.82), COLOR_WHITE, COLOR_BORDER)
        stf = s_box.text_frame
        stf.word_wrap = True
        stf.margin_left = Inches(0.12)
        stf.margin_top = Inches(0.08)
        sp1 = stf.paragraphs[0]
        sp1.text = s_n
        sp1.font.bold = True
        sp1.font.size = Pt(9.5)
        sp1.font.color.rgb = COLOR_NAVY
        sp2 = stf.add_paragraph()
        sp2.text = s_d
        sp2.font.size = Pt(7.5)
        sp2.font.color.rgb = COLOR_MUTED_TEXT

    # --- SLIDE 9: 6. Work Done So Far - Behavioral Design & Database (Workflow) ---
    slide9 = prs.slides.add_slide(slide_layout)
    slide9.shapes.title.text = "6. Work Done So Far: Behavioral Workflow & Data"
    slide9.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide9.shapes.title.text_frame.paragraphs[0].font.size = Pt(20)
    slide9.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide9.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide9, 9)
    
    for shp in list(slide9.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    flow_card = create_card(slide9, Inches(0.65), Inches(1.80), Inches(4.25), Inches(4.90), COLOR_BG_CARD, COLOR_BORDER)
    tf_flow = flow_card.text_frame
    tf_flow.word_wrap = True
    tf_flow.margin_left = Inches(0.2)
    tf_flow.margin_top = Inches(0.15)
    
    p = tf_flow.paragraphs[0]
    p.text = "End-to-End Behavioral Workflow"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    workflow_steps = [
        "1. Ingestion: Candidate uploads resume PDF to Resume Center.",
        "2. Structuring: Resume Agent extracts skills, education, projects.",
        "3. Profile Persistence: Normalized profile saved in PostgreSQL.",
        "4. Job Discovery: Hybrid adapters query API/boards/career pages.",
        "5. Multi-Factor Match: FAISS vector similarity + deterministic scoring.",
        "6. Resume Tailoring: Resume Agent tailors bullet points to JD.",
        "7. Quality Review: Reviewer Agent checks claims & keyword density.",
        "8. PDF Verification: Text extracted from rendered PDF for check.",
        "9. Cover Letter: Tailored company letter drafted & verified.",
        "10. Safety Gate: Mandatory user approval prompt on UI.",
        "11. Dispatch: Application Agent transmits action plan to extension.",
        "12. Submission: Browser extension autofills & submits in session.",
        "13. Tracking: Tracking Agent logs timestamp & status in DB."
    ]
    for st in workflow_steps:
        p = tf_flow.add_paragraph()
        p.text = st
        p.font.name = FONT_BODY
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(2.5)

    db_card = create_card(slide9, Inches(5.1), Inches(1.80), Inches(4.25), Inches(2.35), COLOR_BG_CARD, COLOR_BORDER)
    tf_db = db_card.text_frame
    tf_db.word_wrap = True
    tf_db.margin_left = Inches(0.2)
    tf_db.margin_top = Inches(0.15)
    
    p = tf_db.paragraphs[0]
    p.text = "Multi-User Database Schema Domains"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    db_domains = [
        "Candidate Domain: users, resumes, resume_versions, candidate_profiles, extracted_skills, education, projects.",
        "Job Domain: companies, job_sources, jobs, job_matches.",
        "Application Domain: cover_letters, applications (Status: Saved, Ready, Applied, Interview, Rejected), events.",
        "Agent Domain: workflows, agent_runs, provider_health."
    ]
    for d in db_domains:
        p = tf_db.add_paragraph()
        p.text = "• " + d
        p.font.name = FONT_BODY
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(3)

    qc_card = create_card(slide9, Inches(5.1), Inches(4.35), Inches(4.25), Inches(2.35), COLOR_CARD_ALT, COLOR_STEEL)
    tf_qc = qc_card.text_frame
    tf_qc.word_wrap = True
    tf_qc.margin_left = Inches(0.2)
    tf_qc.margin_top = Inches(0.15)
    
    p = tf_qc.paragraphs[0]
    p.text = "AI Quality Pipeline & Safety Model"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    qc_points = [
        "Drafter ➜ Reviewer ➜ Revision Loop: Independent Reviewer Agent audits drafts against strict rules before finalizing.",
        "Anti-Hallucination: Rejects unsupported experience claims.",
        "Keyword Verification: Prevents spammy keyword stuffing.",
        "Hybrid Approval Policy: Low-risk tasks (search, match, ATS scoring) run autonomously; Critical actions (version commit, application submission) require explicit user click."
    ]
    for q in qc_points:
        p = tf_qc.add_paragraph()
        p.text = "• " + q
        p.font.name = FONT_BODY
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(3)

    # --- SLIDE 10: 6. Work Done So Far - Application UI & Working Modules ---
    slide10 = prs.slides.add_slide(slide_layout)
    slide10.shapes.title.text = "6. Work Done So Far: Application UI (Clyde Copilot)"
    slide10.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide10.shapes.title.text_frame.paragraphs[0].font.size = Pt(21)
    slide10.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide10.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide10, 10)
    
    for shp in list(slide10.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    img_w = Inches(4.05)
    img_h = Inches(1.88)
    
    ui_screens = [
        ("stitch_ai_career_copilot/clyde_ai_assistant_animated/screen.png", 
         "1. AI Career Copilot Dashboard (Chat & Telemetry)", 
         Inches(0.65), Inches(1.80)),
        ("stitch_ai_career_copilot/clyde_resumes/screen.png", 
         "2. Resume Optimization Center (Profiles & Versions)", 
         Inches(5.10), Inches(1.80)),
        ("stitch_ai_career_copilot/clyde_jobs/screen.png", 
         "3. Job Discovery & Match Ranking (FAISS Similarity)", 
         Inches(0.65), Inches(4.35)),
        ("stitch_ai_career_copilot/clyde_ats_analysis/screen.png", 
         "4. ATS Keyword & Gap Analysis (Deterministic Scoring)", 
         Inches(5.10), Inches(4.35))
    ]

    for img_path, title, left, top in ui_screens:
        # Title banner card above screenshot
        t_card = create_card(slide10, left, top, Inches(4.25), Inches(0.36), COLOR_CARD_ALT, COLOR_STEEL)
        tf_t = t_card.text_frame
        tf_t.margin_left = Inches(0.12)
        tf_t.margin_top = Inches(0.04)
        p = tf_t.paragraphs[0]
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_NAVY

        # Embed screenshot with a clean border frame
        if os.path.exists(img_path):
            slide10.shapes.add_picture(img_path, left + Inches(0.10), top + Inches(0.42), img_w, img_h)

    # --- SLIDE 11: 7. Work to be Done ---
    slide11 = prs.slides.add_slide(slide_layout)
    slide11.shapes.title.text = "7. Work to be Done"
    slide11.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide11.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide11.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide11.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide11, 11)
    
    for shp in list(slide11.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    card_rem1 = create_card(slide11, Inches(0.65), Inches(1.85), Inches(4.25), Inches(4.6), COLOR_BG_CARD, COLOR_BORDER)
    tf_r1 = card_rem1.text_frame
    tf_r1.word_wrap = True
    tf_r1.margin_left = Inches(0.25)
    tf_r1.margin_top = Inches(0.2)
    
    p = tf_r1.paragraphs[0]
    p.text = "Implementation Tasks Ahead"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    r1_bullets = [
        "Browser Extension Completion: Implement content scripts and form autofill engine for Workday, Greenhouse, and LinkedIn.",
        "Model Router Integration: Finalize automatic provider failover (GLM ➜ Qwen ➜ Groq ➜ Ollama fallback).",
        "PDF Verification Pipeline: Deploy deterministic text-extraction verification to ensure rendered PDF matches approved structured resume.",
        "Full Multi-User Migration: Finalize database migrations for production multi-user session management."
    ]
    for b in r1_bullets:
        p = tf_r1.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)

    card_rem2 = create_card(slide11, Inches(5.1), Inches(1.85), Inches(4.25), Inches(4.6), COLOR_BG_CARD, COLOR_BORDER)
    tf_r2 = card_rem2.text_frame
    tf_r2.word_wrap = True
    tf_r2.margin_left = Inches(0.25)
    tf_r2.margin_top = Inches(0.2)
    
    p = tf_r2.paragraphs[0]
    p.text = "Testing, Evaluation & Benchmarking"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    r2_bullets = [
        "ATS Pass Rate Benchmark: Measure keyword match improvements on 50+ real software and AI internship descriptions.",
        "Submission Accuracy Testing: Test form autofill precision on complex multi-step application forms.",
        "Latency & Reliability Audits: Benchmark end-to-end processing times across Redis queue and multi-agent pipelines.",
        "User Evaluation Study: Run pilot trials with JUET students to collect feedback on approval UX and match relevance."
    ]
    for b in r2_bullets:
        p = tf_r2.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(8)

    # --- SLIDE 12: 8. Conclusion ---
    slide12 = prs.slides.add_slide(slide_layout)
    slide12.shapes.title.text = "8. Conclusion & Expected Outcomes"
    slide12.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide12.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide12.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide12.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide12, 12)
    
    for shp in list(slide12.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    card_c1 = create_card(slide12, Inches(0.65), Inches(1.85), Inches(4.25), Inches(3.6), COLOR_BG_CARD, COLOR_BORDER)
    tf_c1 = card_c1.text_frame
    tf_c1.word_wrap = True
    tf_c1.margin_left = Inches(0.25)
    tf_c1.margin_top = Inches(0.2)
    
    p = tf_c1.paragraphs[0]
    p.text = "Summary of Progress So Far"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    c1_bullets = [
        "Completed rigorous requirement engineering and literature benchmark.",
        "Finalized full event-driven multi-agent architecture and database schema.",
        "Developed full modern Clyde Dark Editorial frontend dashboard.",
        "Functional working modules: Resume PDF parsing, structured candidate profiles, AI agent chat, and FAISS vector similarity search."
    ]
    for b in c1_bullets:
        p = tf_c1.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(6)

    card_c2 = create_card(slide12, Inches(5.1), Inches(1.85), Inches(4.25), Inches(3.6), COLOR_BG_CARD, COLOR_BORDER)
    tf_c2 = card_c2.text_frame
    tf_c2.word_wrap = True
    tf_c2.margin_left = Inches(0.25)
    tf_c2.margin_top = Inches(0.2)
    
    p = tf_c2.paragraphs[0]
    p.text = "Expected Project Outcomes"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    c2_bullets = [
        "A complete, student-centric career copilot reducing application fatigue by >80%.",
        "Significantly higher ATS shortlisting rates through tailored, truthful resumes.",
        "100% user safety with zero credential storage and mandatory human approval.",
        "A robust, extensible architectural benchmark for event-driven academic multi-agent systems."
    ]
    for b in c2_bullets:
        p = tf_c2.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(6)

    card_take = create_card(slide12, Inches(0.65), Inches(5.6), Inches(8.7), Inches(1.15), COLOR_CARD_ALT, COLOR_STEEL)
    tf_take = card_take.text_frame
    tf_take.word_wrap = True
    tf_take.margin_left = Inches(0.25)
    tf_take.margin_top = Inches(0.12)
    
    p = tf_take.paragraphs[0]
    p.text = "Core Takeaway:"
    p.font.name = FONT_HEADING
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    p2 = tf_take.add_paragraph()
    p2.text = "“The system does not replace the student’s judgment—it eliminates repetitive manual toil, unlocks deep opportunity visibility, and guarantees that every submitted application is relevant, verified, and user-approved.”"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(11.5)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_NAVY
    p2.space_before = Pt(4)

    # --- SLIDE 13: 9. References (IEEE Format) ---
    slide13 = prs.slides.add_slide(slide_layout)
    slide13.shapes.title.text = "9. References"
    slide13.shapes.title.text_frame.paragraphs[0].font.name = FONT_HEADING
    slide13.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
    slide13.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide13.shapes.title.text_frame.paragraphs[0].font.color.rgb = COLOR_NAVY
    add_slide_number(slide13, 13)
    
    for shp in list(slide13.shapes):
        if shp.name.startswith("Content Placeholder"):
            sp = shp._element
            sp.getparent().remove(sp)

    ref_card = create_card(slide13, Inches(0.65), Inches(1.85), Inches(8.7), Inches(4.85), COLOR_BG_CARD, COLOR_BORDER)
    tf_ref = ref_card.text_frame
    tf_ref.word_wrap = True
    tf_ref.margin_left = Inches(0.3)
    tf_ref.margin_right = Inches(0.3)
    tf_ref.margin_top = Inches(0.25)
    
    p = tf_ref.paragraphs[0]
    p.text = "Academic & Technical References (IEEE Format)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    
    refs = [
        "[1] M. Lorentzen, “AI Job Search,” GitHub repository, 2026. [Online]. Available: https://github.com/MadsLorentzen/ai-job-search. [Accessed: Sep. 4, 2026].",
        "[2] feder-cr, “Jobs Applier AI Agent AIHawk,” GitHub repository, 2026. [Online]. Available: https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk. [Accessed: Sep. 4, 2026].",
        "[3] jomacs, “LinkedIn Auto Jobs Applier with AI,” GitHub repository, 2026. [Online]. Available: https://github.com/jomacs/linkedIn_auto_jobs_applier_with_AI. [Accessed: Sep. 4, 2026].",
        "[4] S. Fer, “Career Ops,” GitHub repository, 2026. [Online]. Available: https://github.com/santifer/career-ops. [Accessed: Sep. 4, 2026].",
        "[5] LoopCV, “LoopCV: Job Search Automation Platform,” 2026. [Online]. Available: https://www.loopcv.pro/. [Accessed: Sep. 4, 2026]."
    ]
    for r in refs:
        p = tf_ref.add_paragraph()
        p.text = r
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_before = Pt(12)

    # --- SLIDE 14: Thank You (Using Template Section Header Layout 2) ---
    slide14 = prs.slides.add_slide(prs.slide_layouts[2])
    
    # Remove default title & text placeholders
    for sp in list(slide14.shapes):
        if sp.name.startswith("Text") or sp.name.startswith("Title"):
            p = sp._element
            p.getparent().remove(p)
            
    # Slide number inside the orange box of Section Header layout
    # (Orange box on layout 2: left=0, top=1.75in, width=1.3in, height=0.7in)
    num_box = slide14.shapes.add_textbox(Inches(0.0), Inches(1.85), Inches(1.30), Inches(0.50))
    tf_num = num_box.text_frame
    tf_num.word_wrap = False
    p_num = tf_num.paragraphs[0]
    p_num.text = "14"
    p_num.alignment = PP_ALIGN.CENTER
    p_num.font.name = FONT_HEADING
    p_num.font.size = Pt(22)
    p_num.font.bold = True
    p_num.font.color.rgb = COLOR_WHITE
    
    # Add JUET logo centered at top above the ribbon
    if os.path.exists("juet_logo.png"):
        slide14.shapes.add_picture("juet_logo.png", Inches(4.33), Inches(0.166), Inches(1.33), Inches(1.58))
        
    # Main Thank you text
    txBox = slide14.shapes.add_textbox(Inches(1.0), Inches(2.90), Inches(8.0), Inches(1.10))
    p = txBox.text_frame.paragraphs[0]
    p.text = "Thank You"
    p.font.name = FONT_HEADING
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY
    p.alignment = PP_ALIGN.CENTER
    
    # Q&A prompt
    txBox_qa = slide14.shapes.add_textbox(Inches(1.0), Inches(4.15), Inches(8.0), Inches(0.55))
    p = txBox_qa.text_frame.paragraphs[0]
    p.text = "Questions & Discussion"
    p.font.name = FONT_BODY
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_STEEL
    p.alignment = PP_ALIGN.CENTER
    
    # Team credits
    txBox_team = slide14.shapes.add_textbox(Inches(1.0), Inches(5.10), Inches(8.0), Inches(1.50))
    p = txBox_team.text_frame.paragraphs[0]
    p.text = "Utkarsh Shah (241B278)   |   Utsav Kothari (241B279)   |   Yashasv Pandey (241B295)"
    p.font.name = FONT_BODY
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_DARK_TEXT
    p.alignment = PP_ALIGN.CENTER
    
    p2 = txBox_team.text_frame.add_paragraph()
    p2.text = "Under the supervision of: Ms. Sarita Sahni"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(13)
    p2.font.color.rgb = COLOR_STEEL
    p2.font.bold = True
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(6)

    p3 = txBox_team.text_frame.add_paragraph()
    p3.text = "Jaypee University of Engineering & Technology, Guna"
    p3.font.name = FONT_BODY
    p3.font.size = Pt(12)
    p3.font.color.rgb = COLOR_MUTED_TEXT
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(6)

    # Save to Workspace
    out_path = "AI_Powered_Resume_Automation_Presentation.pptx"
    prs.save(out_path)
    print(f"Presentation saved successfully to {out_path}. Total slides: {len(prs.slides)}")

if __name__ == "__main__":
    main()
