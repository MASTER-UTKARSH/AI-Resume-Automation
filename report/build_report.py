#!/usr/bin/env python3
"""
B.Tech 5th Semester Project Report Builder (.docx)
Strictly implements JUET Guna 'Project Report Guidelines.pdf'.
Includes 2-pass LibreOffice PDF page-number indexing so List of Figures,
List of Tables, and Table of Contents contain exact rendered page numbers.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor
from PIL import Image
from pypdf import PdfReader

REPORT_DIR = Path("/home/utkarsh21/Desktop/Minor 1/report")
SECTIONS_DIR = REPORT_DIR / "sections"
DIAGRAMS_DIR = REPORT_DIR / "diagrams"
SCREENSHOTS_DIR = DIAGRAMS_DIR / "screenshots"
LOGO_PATH = Path("/home/utkarsh21/Desktop/Minor 1/presentation/juet_logo.png")
OUTPUT_DOCX = REPORT_DIR / "AI_Powered_Resume_Automation_Project_Report.docx"

# Exact codebase paths for Appendix verbatim excerpts
LATEX_EXPORTER_PATH = Path("/home/utkarsh21/Desktop/Minor 1/backend/app/services/latex_exporter.py")
JOB_SCRAPER_PATH = Path("/home/utkarsh21/Desktop/Minor 1/backend/app/services/job_scraper.py")
FORM_MAPPER_PATH = Path("/home/utkarsh21/Desktop/Minor 1/browser-extension/src/automation/form-mapper.ts")
SUBMISSION_ENGINE_PATH = Path("/home/utkarsh21/Desktop/Minor 1/browser-extension/src/automation/submission-engine.ts")


def to_roman(n: int) -> str:
    vals = [
        (1000, "m"), (900, "cm"), (500, "d"), (400, "cd"),
        (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
        (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")
    ]
    res = []
    for v, sym in vals:
        while n >= v:
            res.append(sym)
            n -= v
    return "".join(res)


def set_page_margins(section):
    """JUET Guidelines: A4, Left 3cm, Right/Top/Bottom 2cm, No header."""
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)
    section.different_first_page_header_footer = False

    # Enforce empty header (Guideline: "No header on any page")
    section.header.is_linked_to_previous = False
    for p in section.header.paragraphs:
        p.text = ""


def set_footer_page_number(section, num_format: str = "decimal", start_at: int = 1, enabled: bool = True):
    """Configure centered bottom footer PAGE field or suppress footer completely."""
    section.footer.is_linked_to_previous = False
    for p in list(section.footer.paragraphs):
        p.text = ""

    pg_pr = section._sectPr.find(qn("w:pgNumType"))
    if pg_pr is not None:
        section._sectPr.remove(pg_pr)

    if not enabled:
        return

    pg_num = OxmlElement("w:pgNumType")
    pg_num.set(qn("w:fmt"), num_format)
    pg_num.set(qn("w:start"), str(start_at))
    section._sectPr.append(pg_num)

    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)

    r1 = p.add_run()
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(11)
    fld1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    r1._r.append(fld1)

    r2 = p.add_run()
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(11)
    instr = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls("w"))
    r2._r.append(instr)

    r3 = p.add_run()
    r3.font.name = "Times New Roman"
    r3.font.size = Pt(11)
    fld2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
    r3._r.append(fld2)

    r4 = p.add_run("1" if num_format == "decimal" else "i")
    r4.font.name = "Times New Roman"
    r4.font.size = Pt(11)

    r5 = p.add_run()
    r5.font.name = "Times New Roman"
    r5.font.size = Pt(11)
    fld3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
    r5._r.append(fld3)


def style_run(run, size_pt=12, bold=False, italic=False, font_name="Times New Roman", color=RGBColor(0, 0, 0)):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color


def add_inline_formatted_text(paragraph, text: str, size_pt=12, base_bold=False, color=RGBColor(0, 0, 0)):
    """Supports backtick code styling (Courier New slightly smaller or bold TNR) and **bold**."""
    # Split on `code` and **bold**
    tokens = re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("`") and tok.endswith("`"):
            r = paragraph.add_run(tok[1:-1])
            style_run(r, size_pt=max(10, size_pt - 1), bold=base_bold, font_name="Courier New", color=RGBColor(20, 40, 80))
        elif tok.startswith("**") and tok.endswith("**"):
            r = paragraph.add_run(tok[2:-2])
            style_run(r, size_pt=size_pt, bold=True, font_name="Times New Roman", color=color)
        else:
            r = paragraph.add_run(tok)
            style_run(r, size_pt=size_pt, bold=base_bold, font_name="Times New Roman", color=color)


def add_body_p(doc: Document, text: str, size_pt=12, spacing_before=3, spacing_after=3,
               align=WD_ALIGN_PARAGRAPH.JUSTIFY, line_spacing=1.5):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = line_spacing
    pf.space_before = Pt(spacing_before)
    pf.space_after = Pt(spacing_after)
    add_inline_formatted_text(p, text, size_pt=size_pt)
    return p


def add_prelim_p(doc: Document, text: str, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False):
    """Declaration, Certificate, Acknowledgement, Abstract: Size 14, 1.5 spacing, 6pt before/after."""
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    add_inline_formatted_text(p, text, size_pt=14, base_bold=bold)
    return p


def add_chapter_heading(doc: Document, title: str, page_break=True):
    """Times New Roman 16pt Bold, Centre Aligned, 12pt before/after."""
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(12)
    pf.space_after = Pt(12)
    pf.line_spacing = 1.15
    pf.keep_with_next = True
    r = p.add_run(title)
    style_run(r, size_pt=16, bold=True)
    return p


def add_section_heading(doc: Document, title: str):
    """Times New Roman 14pt Bold, Left Aligned, 6pt before/after."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.15
    pf.keep_with_next = True
    r = p.add_run(title)
    style_run(r, size_pt=14, bold=True)
    return p


def add_subsection_heading(doc: Document, title: str):
    """Times New Roman 12pt Bold, Left Aligned, 6pt before, 3pt after."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.15
    pf.keep_with_next = True
    r = p.add_run(title)
    style_run(r, size_pt=12, bold=True)
    return p


def add_bullet_p(doc: Document, text: str, size_pt=12, numbered_prefix: str = None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.space_before = Pt(3)
    pf.space_after = Pt(3)
    pf.left_indent = Cm(0.8)
    pf.first_line_indent = Cm(-0.4)
    prefix = f"{numbered_prefix} " if numbered_prefix else "•  "
    r_pre = p.add_run(prefix)
    style_run(r_pre, size_pt=size_pt, bold=bool(numbered_prefix))
    add_inline_formatted_text(p, text, size_pt=size_pt)
    return p


def set_cell_shading(cell, fill_hex: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def add_styled_table(doc: Document, caption: str, headers: List[str], rows: List[List[str]], col_widths_cm: List[float] = None, compact: bool = False):
    """Guideline: Table caption placed ABOVE the table."""
    if caption:
        cap_p = doc.add_paragraph()
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_p.paragraph_format.space_before = Pt(8)
        cap_p.paragraph_format.space_after = Pt(4)
        cap_p.paragraph_format.keep_with_next = True
        r_cap = cap_p.add_run(caption)
        style_run(r_cap, size_pt=11, bold=True)

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    pad_v = 36 if compact else 70
    font_sz = 9.5 if compact else 10
    ls = 1.08 if compact else 1.15

    # Header row
    hdr_row = table.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))
    for j, h_text in enumerate(headers):
        cell = hdr_row.cells[j]
        set_cell_shading(cell, "1E293B")
        set_cell_margins(cell, top=55 if compact else 90, bottom=55 if compact else 90, left=100, right=100)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = ls
        r = p.add_run(h_text)
        style_run(r, size_pt=font_sz, bold=True, color=RGBColor(255, 255, 255))

    # Data rows
    for i, row_data in enumerate(rows):
        row = table.rows[i + 1]
        cant_split = OxmlElement("w:cantSplit")
        row._tr.get_or_add_trPr().append(cant_split)
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=pad_v, bottom=pad_v, left=100, right=100)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = ls
            add_inline_formatted_text(p, val, size_pt=font_sz)

    if col_widths_cm:
        for row in table.rows:
            for j, w in enumerate(col_widths_cm):
                row.cells[j].width = Cm(w)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)
    return table


def add_figure(doc: Document, img_path: Path, caption: str, max_w_cm: float = 15.2, max_h_cm: float = 13.5):
    """Guideline: Figure caption placed BELOW the figure."""
    if not img_path.exists():
        raise FileNotFoundError(f"Missing figure: {img_path}")

    with Image.open(img_path) as im:
        w_px, h_px = im.size

    aspect = h_px / w_px
    w_cm = max_w_cm
    h_cm = w_cm * aspect
    if h_cm > max_h_cm:
        h_cm = max_h_cm
        w_cm = h_cm / aspect

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(3)
    p_img.paragraph_format.keep_with_next = True
    run = p_img.add_run()
    run.add_picture(str(img_path), width=Cm(w_cm))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(8)
    r_cap = p_cap.add_run(caption)
    style_run(r_cap, size_pt=11, bold=True, italic=True)


def add_code_block(doc: Document, title: str, code_text: str):
    """Guideline: Coding font Courier New, Size 10, Normal."""
    add_subsection_heading(doc, title)
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"
    cell = tbl.rows[0].cells[0]
    cell.width = Cm(16.0)
    set_cell_shading(cell, "F8FAFC")
    set_cell_margins(cell, top=100, bottom=100, left=140, right=140)

    lines = code_text.rstrip().splitlines()
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.12
    for idx, line in enumerate(lines):
        if idx > 0:
            p.add_run("\n")
        r = p.add_run(line)
        style_run(r, size_pt=10, bold=False, font_name="Courier New", color=RGBColor(15, 23, 42))

    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)


def build_cover_page(doc: Document):
    sec = doc.sections[0]
    set_page_margins(sec)
    set_footer_page_number(sec, enabled=False)

    def c_para(text, size, bold=False, italic=False, before=4, after=4, line_sp=1.25):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = line_sp
        r = p.add_run(text)
        style_run(r, size_pt=size, bold=bold, italic=italic)
        return p

    c_para("AI-POWERED RESUME AUTOMATION SYSTEM", 20, bold=True, before=6, after=4)
    c_para("(CLYDE — MULTI-AGENT CAREER COPILOT)", 13, bold=True, before=0, after=12)

    c_para("A Minor Project-I Report", 14, bold=True, before=8, after=4)
    c_para("Submitted in partial fulfillment of the requirement for the award of degree of", 12, italic=True, before=2, after=6)
    c_para("BACHELOR OF TECHNOLOGY", 15, bold=True, before=4, after=2)
    c_para("IN", 12, bold=True, before=2, after=2)
    c_para("COMPUTER SCIENCE AND ENGINEERING", 14, bold=True, before=2, after=12)

    if LOGO_PATH.exists():
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(6)
        p_logo.paragraph_format.space_after = Pt(12)
        p_logo.add_run().add_picture(str(LOGO_PATH), width=Cm(3.4))

    c_para("Submitted by:", 13, bold=True, before=6, after=6)

    tbl = doc.add_table(rows=4, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    students = [
        ("Student Name", "Enrolment No."),
        ("Utkarsh Shah", "241B278"),
        ("Utsav Kothari", "241B279"),
        ("Yashasv Pandey", "241B295"),
    ]
    for r_idx, (col1, col2) in enumerate(students):
        row = tbl.rows[r_idx]
        for c_idx, txt in enumerate([col1, col2]):
            cell = row.cells[c_idx]
            cell.width = Cm(6.5 if c_idx == 0 else 4.5)
            set_cell_margins(cell, top=50, bottom=50, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(txt)
            style_run(r, size_pt=12, bold=(r_idx == 0))

    c_para("Under the Supervision of:", 13, bold=True, before=18, after=4)
    c_para("Ms. Sarita Sahni", 14, bold=True, before=2, after=20)

    c_para("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", 13, bold=True, before=12, after=3)
    c_para("JAYPEE UNIVERSITY OF ENGINEERING & TECHNOLOGY", 14, bold=True, before=2, after=3)
    c_para("A-B ROAD, RAGHOGARH, DIST. GUNA (M.P.) - 473226, INDIA", 11, bold=True, before=0, after=8)
    c_para("5th Semester  |  2026", 12, bold=True, before=4, after=0)


def build_preliminaries(doc: Document, toc_entries: List[Tuple[str, str]], lof_entries: List[Tuple[str, str]], lot_entries: List[Tuple[str, str]]):
    sec = doc.add_section()
    set_page_margins(sec)
    set_footer_page_number(sec, num_format="lowerRoman", start_at=1, enabled=True)

    # 1. DECLARATION (<= 1 page, Size 14, 1.5 spacing, 6pt before/after)
    add_chapter_heading(doc, "DECLARATION", page_break=False)
    add_prelim_p(
        doc,
        "We hereby certify that the work presented in the Minor Project-I report entitled "
        "\"AI-POWERED RESUME AUTOMATION SYSTEM\" in partial fulfillment of the requirement "
        "for the award of the degree of Bachelor of Technology (5th Semester) in Computer Science "
        "and Engineering submitted at Jaypee University of Engineering & Technology, Guna, "
        "is an authentic record of our own work carried out during the semester under the supervision "
        "of Ms. Sarita Sahni."
    )
    add_prelim_p(
        doc,
        "The matter embodied in this report has not been submitted by us for the award of any "
        "other degree or diploma to this university or any other institution."
    )

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(24)

    sig_tbl = doc.add_table(rows=4, cols=2)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, (s_name, roll) in enumerate([
        ("Utkarsh Shah", "241B278"),
        ("Utsav Kothari", "241B279"),
        ("Yashasv Pandey", "241B295"),
    ]):
        c0 = sig_tbl.rows[idx].cells[0]
        c1 = sig_tbl.rows[idx].cells[1]
        c0.width = Cm(9.5)
        c1.width = Cm(6.0)
        for c in (c0, c1):
            set_cell_margins(c, top=140, bottom=80, left=60, right=60)
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(f"Signature: _______________________\n{s_name} ({roll})")
        style_run(r0, size_pt=13, bold=False)
        p1 = c1.paragraphs[0]
        r1 = p1.add_run("")
        style_run(r1, size_pt=13)
    # Remove outer borders visually from sig table by keeping clean minimal padding or explicit date row
    c_date = sig_tbl.rows[3].cells[0]
    p_dt = c_date.paragraphs[0]
    p_dt.paragraph_format.space_before = Pt(18)
    r_dt = p_dt.add_run("Date: _______________________")
    style_run(r_dt, size_pt=14, bold=False)

    # Remove borders on signature table so it looks like classic thesis signature blocks
    tblPr = sig_tbl._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/>'
        '<w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)

    # 2. CERTIFICATE (Exact JUET Page 6 wording, <= 1 page)
    add_chapter_heading(doc, "CERTIFICATE", page_break=True)
    add_prelim_p(
        doc,
        "This is to certify that the Minor Project-I report entitled "
        "\"AI-POWERED RESUME AUTOMATION SYSTEM\" submitted by Utkarsh Shah (241B278), "
        "Utsav Kothari (241B279), and Yashasv Pandey (241B295) to Jaypee University of "
        "Engineering & Technology, Guna, in partial fulfillment of the requirement for the "
        "award of degree of Bachelor of Technology in Computer Science and Engineering (5th Semester), "
        "is a record of bonafide work carried out by them under my guidance and supervision."
    )
    add_prelim_p(
        doc,
        "The results and software artifacts presented in this report have not been submitted to any "
        "other university or institute for the award of any degree or diploma."
    )

    p_gap = doc.add_paragraph()
    p_gap.paragraph_format.space_before = Pt(36)

    cert_tbl = doc.add_table(rows=2, cols=2)
    cert_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cert_tbl._tbl.tblPr.append(parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/>'
        '<w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>'
        '</w:tblBorders>'
    ))
    c_sup = cert_tbl.rows[0].cells[0]
    c_hod = cert_tbl.rows[0].cells[1]
    c_sup.width = Cm(8.5)
    c_hod.width = Cm(7.5)
    p_sup = c_sup.paragraphs[0]
    p_sup.paragraph_format.line_spacing = 1.4
    r_sup = p_sup.add_run("Supervisor\n\n___________________________\nMs. Sarita Sahni\nDept. of Computer Science & Engg.\nJUET, Guna (M.P.)")
    style_run(r_sup, size_pt=13, bold=False)

    p_hod = c_hod.paragraphs[0]
    p_hod.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_hod.paragraph_format.line_spacing = 1.4
    r_hod = p_hod.add_run("Head of Department\n\n___________________________\nDepartment of CSE\nJUET, Guna (M.P.)")
    style_run(r_hod, size_pt=13, bold=False)

    p_cd = cert_tbl.rows[1].cells[0].paragraphs[0]
    p_cd.paragraph_format.space_before = Pt(28)
    r_cd = p_cd.add_run("Date: _______________________")
    style_run(r_cd, size_pt=14, bold=False)

    # 3. ACKNOWLEDGEMENT (<= 1 page)
    add_chapter_heading(doc, "ACKNOWLEDGEMENT", page_break=True)
    add_prelim_p(
        doc,
        "We express our sincere gratitude to our project supervisor, Ms. Sarita Sahni, "
        "Department of Computer Science and Engineering, Jaypee University of Engineering & Technology, "
        "Guna, for her steady guidance, critical feedback during design reviews, and technical insights "
        "throughout the 5th semester."
    )
    add_prelim_p(
        doc,
        "We are grateful to the Department of Computer Science and Engineering and the faculty "
        "review panel for providing laboratory infrastructure and constructive suggestions while validating "
        "the FastAPI backend and Chrome Manifest V3 extension architecture."
    )
    add_prelim_p(
        doc,
        "Finally, we thank our classmates and friends who helped test edge cases across varied "
        "resume formats and application portal layouts."
    )
    p_ack_sig = doc.add_paragraph()
    p_ack_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_ack_sig.paragraph_format.space_before = Pt(28)
    p_ack_sig.paragraph_format.line_spacing = 1.5
    r_ack = p_ack_sig.add_run("Utkarsh Shah (241B278)\nUtsav Kothari (241B279)\nYashasv Pandey (241B295)")
    style_run(r_ack, size_pt=14, bold=True)

    # 4. ABSTRACT (<= 1 page, Size 14, 1.5 spacing, 6pt before/after)
    add_chapter_heading(doc, "ABSTRACT", page_break=True)
    abs_text = (SECTIONS_DIR / "abstract_ch1_ch2.md").read_text(encoding="utf-8")
    abs_block = abs_text.split("\n---\n")[0].replace("# ABSTRACT", "").strip()
    for para in [p.strip() for p in abs_block.split("\n\n") if p.strip()]:
        # Compact slightly if needed to keep strictly <= 1 page at 14pt!
        add_prelim_p(doc, para)

    # 5. LIST OF FIGURES
    add_chapter_heading(doc, "LIST OF FIGURES", page_break=True)
    lof_rows = [[fig_no, fig_cap, pg] for fig_no, fig_cap, pg in lof_entries]
    add_styled_table(doc, "", ["Figure No.", "Title / Description", "Page No."], lof_rows, col_widths_cm=[2.6, 11.4, 2.0], compact=True)

    # 6. LIST OF TABLES & LIST OF SYMBOLS / ACRONYMS
    add_chapter_heading(doc, "LIST OF TABLES", page_break=True)
    lot_rows = [[t_no, t_cap, pg] for t_no, t_cap, pg in lot_entries]
    add_styled_table(doc, "", ["Table No.", "Title / Description", "Page No."], lot_rows, col_widths_cm=[2.6, 11.4, 2.0], compact=True)

    add_chapter_heading(doc, "LIST OF SYMBOLS AND ACRONYMS", page_break=True)
    acro_rows = [
        ["API", "Application Programming Interface"],
        ["ARIA", "Accessible Rich Internet Applications"],
        ["ATS", "Applicant Tracking System"],
        ["CGPA", "Cumulative Grade Point Average"],
        ["DFD", "Data Flow Diagram"],
        ["DOM", "Document Object Model"],
        ["ER", "Entity-Relationship"],
        ["FAISS", "Facebook AI Similarity Search"],
        ["HTTP / WS", "Hypertext Transfer Protocol / WebSocket"],
        ["JSON", "JavaScript Object Notation"],
        ["LLM", "Large Language Model"],
        ["MV3", "Chrome Extension Manifest Version 3"],
        ["ORM", "Object-Relational Mapping"],
        ["PDF", "Portable Document Format"],
        ["SQL", "Structured Query Language"],
        ["UML", "Unified Modeling Language"],
        ["S_sem, S_skill, S_exp, S_pref", "Weighted Sub-Scores in Hybrid Ranking Formula (0.40, 0.30, 0.15, 0.15)"],
        ["M_ghost", "GhostJobDetector Penalty Multiplier (0.75, 0.90, 0.95, or 1.00)"],
    ]
    add_styled_table(doc, "", ["Symbol / Acronym", "Full Term / Engineering Meaning"], acro_rows, col_widths_cm=[5.0, 11.0], compact=True)

    # 7. TABLE OF CONTENTS
    add_chapter_heading(doc, "TABLE OF CONTENTS", page_break=True)
    toc_rows = [[sec_title, pg] for sec_title, pg in toc_entries]
    add_styled_table(doc, "", ["Chapter / Section Title", "Page No."], toc_rows, col_widths_cm=[13.8, 2.2], compact=True)


def render_markdown_chapter(doc: Document, md_text: str, after_hooks: Dict[str, callable] = None, first_chapter: bool = False):
    """Parse structured markdown section files into exact JUET Word styling."""
    after_hooks = after_hooks or {}
    lines = md_text.splitlines()
    i = 0
    in_table = False
    table_caption = ""
    table_headers = []
    table_rows = []
    seen_first_chapter = False

    def flush_table():
        nonlocal in_table, table_caption, table_headers, table_rows
        if table_headers:
            add_styled_table(doc, table_caption, table_headers, table_rows)
            if table_caption:
                prefix = table_caption.split(":")[0].strip()
                if prefix in after_hooks:
                    after_hooks[prefix]()
        in_table = False
        table_caption = ""
        table_headers = []
        table_rows = []

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped or stripped == "---":
            if in_table:
                flush_table()
            i += 1
            continue

        # Table caption line (**Table X.Y: ...**)
        if stripped.startswith("**Table ") and stripped.endswith("**"):
            if in_table:
                flush_table()
            table_caption = stripped.strip("*")
            i += 1
            continue

        # Markdown table row
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.match(r"^:?-{2,}:?$", c) for c in cells):
                i += 1
                continue
            if not in_table:
                in_table = True
                table_headers = cells
            else:
                table_rows.append(cells)
            i += 1
            continue
        elif in_table:
            flush_table()

        if stripped.startswith("# "):
            heading_txt = stripped[2:].strip()
            use_pb = not (first_chapter and not seen_first_chapter)
            seen_first_chapter = True
            add_chapter_heading(doc, heading_txt, page_break=use_pb)
            if heading_txt in after_hooks:
                after_hooks[heading_txt]()
        elif stripped.startswith("## "):
            heading_txt = stripped[3:].strip()
            add_section_heading(doc, heading_txt)
            if heading_txt in after_hooks:
                after_hooks[heading_txt]()
        elif stripped.startswith("### "):
            heading_txt = stripped[4:].strip()
            add_subsection_heading(doc, heading_txt)
            if heading_txt in after_hooks:
                after_hooks[heading_txt]()
        elif stripped.startswith("- "):
            add_bullet_p(doc, stripped[2:].strip())
        elif re.match(r"^\d+\.\s+", stripped):
            m = re.match(r"^(\d+\.)\s+(.*)$", stripped)
            add_bullet_p(doc, m.group(2), numbered_prefix=m.group(1))
        else:
            p = add_body_p(doc, stripped)
            # Check section-level inline figure triggers (e.g. "Figure 3.1")
            for hook_key in list(after_hooks.keys()):
                if hook_key.startswith("AFTER_TEXT:") and hook_key.split(":", 1)[1] in stripped:
                    after_hooks.pop(hook_key)()

        i += 1

    if in_table:
        flush_table()


def build_main_body(doc: Document):
    sec = doc.add_section()
    set_page_margins(sec)
    set_footer_page_number(sec, num_format="decimal", start_at=1, enabled=True)

    # Parse Abstract/Ch1/Ch2 (skip Abstract portion)
    abs_ch1_ch2 = (SECTIONS_DIR / "abstract_ch1_ch2.md").read_text(encoding="utf-8")
    ch1_ch2_text = abs_ch1_ch2.split("\n---\n", 1)[1].strip()
    render_markdown_chapter(doc, ch1_ch2_text, first_chapter=True)

    # Parse Ch3 & Ch4 with figures injected cleanly at text anchor points
    ch3_ch4_text = (SECTIONS_DIR / "ch3_ch4.md").read_text(encoding="utf-8")

    ch3_ch4_hooks = {
        "AFTER_TEXT:Figure 3.1 illustrates": lambda: add_figure(
            doc, DIAGRAMS_DIR / "fig3_1_system_architecture.png",
            "Figure 3.1: Four-Layer System Architecture of Clyde (FastAPI, ML Services, and Chrome MV3)", max_w_cm=15.4, max_h_cm=11.8
        ),
        "AFTER_TEXT:Figure 3.2 traces": lambda: add_figure(
            doc, DIAGRAMS_DIR / "fig3_2_dfd_level0_level1.png",
            "Figure 3.2: Data Flow Diagram (Level 0 Context View and Level 1 Process Pipeline)", max_w_cm=15.4, max_h_cm=11.5
        ),
        "AFTER_TEXT:Figure 3.3 shows": lambda: add_figure(
            doc, DIAGRAMS_DIR / "fig3_3_use_case_diagram.png",
            "Figure 3.3: System Use Case Diagram Across Student, Agent Services, and ATS Portals", max_w_cm=15.4, max_h_cm=11.5
        ),
        "AFTER_TEXT:Figure 3.4 illustrates": lambda: add_figure(
            doc, DIAGRAMS_DIR / "fig3_4_sequence_diagram.png",
            "Figure 3.4: End-to-End Sequence Diagram from Tailoring Request to Human Approval Gate", max_w_cm=15.4, max_h_cm=11.5
        ),
        "AFTER_TEXT:Figure 3.5 captures": lambda: add_figure(
            doc, DIAGRAMS_DIR / "fig3_5_class_diagram.png",
            "Figure 3.5: Backend Service and Extension Class Architecture Diagram", max_w_cm=15.4, max_h_cm=11.5
        ),
        "AFTER_TEXT:rather than comparing a revised resume": lambda: (
            add_figure(
                doc, DIAGRAMS_DIR / "fig3_6_er_diagram.png",
                "Figure 3.6: 19-Table Entity-Relationship (ER) Schema in backend/app/database/models.py", max_w_cm=15.4, max_h_cm=11.5
            ),
            add_styled_table(
                doc,
                "Table 3.1: Relational Database Schema Summary (19 SQLAlchemy Tables)",
                ["Domain Group", "Table Names", "Primary Purpose"],
                [
                    ["Candidate & Resumes (8)", "`users`, `resumes`, `resume_versions`, `candidate_profiles`, `candidate_skills`, `candidate_education`, `candidate_experience`, `candidate_projects`", "Stores immutable base profiles, extracted skills, academic credentials, and versioned resume drafts."],
                    ["Discovery & Matching (4)", "`companies`, `job_sources`, `jobs`, `job_matches`", "Stores verified employer domains, scraped job postings, hybrid factor sub-scores, and final rank."],
                    ["Application Tracking (3)", "`cover_letters`, `applications`, `application_events`", "Tracks tailored cover letters, submission lifecycle status, and time-stamped audit events."],
                    ["Agents & Telemetry (4)", "`workflows`, `agent_runs`, `provider_health`, `embedding_references`", "Logs Drafter-Reviewer workflow states, provider latencies, and FAISS vector index mappings."]
                ],
                col_widths_cm=[3.8, 6.2, 6.0]
            ),
            add_styled_table(
                doc,
                "Table 3.2: FastAPI REST and WebSocket Endpoint Reference",
                ["Route Path", "Method", "Router Module", "Responsibility"],
                [
                    ["`/api/resumes/upload`", "POST", "`resumes.py`", "Parses PDF/text resume, runs `PostingGuard`, populates SQL + FAISS index."],
                    ["`/api/resumes/tailor-audit`", "POST", "`resumes.py`", "Runs `ModelRouter` tailoring loop and `FactVerifier` metric audit."],
                    ["`/api/resumes/{id}/export-latex`", "POST", "`resumes.py`", "Generates escaped Jake's Resume `.tex` source and runs Tectonic check."],
                    ["`/api/resumes/{id}/pdf`", "GET", "`resumes.py`", "Compiles and streams downloadable single-column ATS resume PDF."],
                    ["`/api/jobs/match`", "POST", "`jobs.py`", "Executes FAISS vector query, 4-factor scoring, and `GhostJobDetector`."],
                    ["`/api/jobs/scrape`", "POST", "`jobs.py`", "Fetches live job URL, strips hidden HTML/Unicode, and extracts skills."],
                    ["`/api/agent/chat`", "POST", "`agent.py`", "Routes conversational requests, tailors active profile, triggers apply actions."],
                    ["`/api/telemetry/events`", "GET", "`telemetry.py`", "Streams last 50 asynchronous `EventBus` records for UI monitoring."],
                    ["`/api/extension/token`", "GET", "`extension.py`", "Issues short-lived session authentication token for Chrome MV3."],
                    ["`/api/extension/ws`", "WS", "`extension.py`", "Bidirectional typed command/result WebSocket channel with Chrome."]
                ],
                col_widths_cm=[4.8, 1.5, 2.7, 7.0]
            )
        ),
        "AFTER_TEXT:Figure 4.1 shows": lambda: add_figure(
            doc, DIAGRAMS_DIR / "fig4_1_extension_flow.png",
            "Figure 4.1: Chrome Manifest V3 Extension WebSocket Lifecycle and Safety Execution Flow", max_w_cm=15.0, max_h_cm=11.0
        ),
        "AFTER_TEXT:Figure 4.2 displays": lambda: add_figure(
            doc, SCREENSHOTS_DIR / "ui_resume_library.png",
            "Figure 4.2: Clyde Web Interface Showing Parsed Resume Library and Verified Skill Extraction", max_w_cm=14.8, max_h_cm=9.5
        ),
        "AFTER_TEXT:Figure 4.3 shows": lambda: add_figure(
            doc, SCREENSHOTS_DIR / "ui_job_discovery.png",
            "Figure 4.3: Job Discovery Console Showing Four-Factor Match Scores and Ghost Job Verification Badges", max_w_cm=14.8, max_h_cm=9.5
        ),
        "AFTER_TEXT:Figure 4.4 captures": lambda: (
            add_figure(
                doc, SCREENSHOTS_DIR / "ui_copilot_apply.png",
                "Figure 4.4: AI Career Copilot Conversational Tailoring and Live Apify Job Card Dispatch", max_w_cm=14.8, max_h_cm=9.5
            ),
            add_figure(
                doc, SCREENSHOTS_DIR / "ui_resume_modal.png",
                "Figure 4.5: Compiled Single-Column ATS LaTeX Resume Preview Modal Inside Dashboard", max_w_cm=14.8, max_h_cm=9.5
            ),
        ),
        "AFTER_TEXT:Figure 4.6 views": lambda: (
            add_figure(
                doc, SCREENSHOTS_DIR / "ui_telemetry.png",
                "Figure 4.6: Real-Time EventBus Agent Telemetry and Provider Latency Monitor", max_w_cm=14.8, max_h_cm=9.5
            ),
            add_figure(
                doc, SCREENSHOTS_DIR / "ui_extension_autofill.png",
                "Figure 4.7: Chrome Manifest V3 Extension Autofill and Mandatory Pre-Submit Confirmation Screen on BrowserOS Neo", max_w_cm=14.8, max_h_cm=9.5
            ),
        ),
    }

    render_markdown_chapter(doc, ch3_ch4_text, after_hooks=ch3_ch4_hooks)

    # Parse Ch5, Ch6, References
    ch5_full = (SECTIONS_DIR / "ch5_ch6_refs.md").read_text(encoding="utf-8")
    ch5_ch6_part, refs_part = ch5_full.split("# REFERENCES", 1)

    ch5_hooks = {
        "AFTER_TEXT:Figure 5.1 plots": lambda: add_figure(
            doc, DIAGRAMS_DIR / "fig5_1_matching_scores.png",
            "Figure 5.1: Four-Factor Hybrid Match Score Breakdown Across Five Target Engineering Openings", max_w_cm=15.0, max_h_cm=9.2
        ),
        "AFTER_TEXT:Figure 5.2 summarizes": lambda: add_figure(
            doc, DIAGRAMS_DIR / "fig5_2_latency_benchmarks.png",
            "Figure 5.2: Observed Execution Latency Profile Across Backend CPU, Tectonic PDF, Groq, and Apify Stages", max_w_cm=15.0, max_h_cm=9.2
        ),
    }
    render_markdown_chapter(doc, ch5_ch6_part.strip(), after_hooks=ch5_hooks)

    # APPENDICES (before or after References per arrangement -> Guidelines list Appendices before References OR References then Appendices; guidelines say: Chapter 6 -> Appendices -> References -> Last Page)
    build_appendices(doc)

    # REFERENCES (IEEE format)
    add_chapter_heading(doc, "REFERENCES", page_break=True)
    ref_paras = [r.strip() for r in refs_part.strip().split("\n\n") if r.strip()]
    for ref in ref_paras:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf = p.paragraph_format
        pf.line_spacing = 1.5
        pf.space_before = Pt(3)
        pf.space_after = Pt(4)
        pf.left_indent = Cm(0.9)
        pf.first_line_indent = Cm(-0.9)
        # Handle *italic* book/journal titles in IEEE entries cleanly
        parts = re.split(r"(\*[^*]+\*)", ref)
        for pt_txt in parts:
            if not pt_txt:
                continue
            if pt_txt.startswith("*") and pt_txt.endswith("*"):
                r = p.add_run(pt_txt[1:-1])
                style_run(r, size_pt=12, italic=True)
            else:
                r = p.add_run(pt_txt)
                style_run(r, size_pt=12, italic=False)

    # LAST PAGE: Personal Details with Passport Size Photograph Placeholders (In Uniform)
    build_personal_details_page(doc)


def read_lines_slice(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1 : end])


def build_appendices(doc: Document):
    # APPENDIX A
    add_chapter_heading(doc, "APPENDIX A: CORE BACKEND SOURCE CODE", page_break=True)
    add_body_p(
        doc,
        "This appendix reproduces verbatim excerpts from the backend LaTeX grounding gate and "
        "live job posting sanitization service implemented in Python (`backend/app/services/`)."
    )

    latex_excerpt = read_lines_slice(LATEX_EXPORTER_PATH, 151, 177) + "\n\n" + read_lines_slice(LATEX_EXPORTER_PATH, 427, 463)
    add_code_block(doc, "Listing A.1: Pre-Export FactVerifier Gate and LaTeX Escaping (latex_exporter.py)", latex_excerpt)

    scraper_excerpt = read_lines_slice(JOB_SCRAPER_PATH, 29, 80)
    add_code_block(doc, "Listing A.2: Live Posting Ingestion & PostingGuard Filter (job_scraper.py)", scraper_excerpt)

    # APPENDIX B
    add_chapter_heading(doc, "APPENDIX B: CHROME EXTENSION AUTOMATION SOURCE CODE", page_break=True)
    add_body_p(
        doc,
        "This appendix reproduces verbatim TypeScript modules handling deterministic eight-level DOM "
        "field mapping (`form-mapper.ts`) and mandatory human-in-the-loop approval validation (`submission-engine.ts`)."
    )

    mapper_excerpt = read_lines_slice(FORM_MAPPER_PATH, 225, 299)
    add_code_block(doc, "Listing B.1: Deterministic Field Scoring and Validation (form-mapper.ts)", mapper_excerpt)

    sub_excerpt = read_lines_slice(SUBMISSION_ENGINE_PATH, 58, 126)
    add_code_block(doc, "Listing B.2: Pre-Submission Approval & CAPTCHA Safety Gate (submission-engine.ts)", sub_excerpt)

    # APPENDIX C
    add_chapter_heading(doc, "APPENDIX C: SAMPLE LATEX OUTPUT & VERIFICATION LOGS", page_break=True)
    add_body_p(
        doc,
        "Listing C.1 shows a generated single-column Overleaf-compatible resume preamble and bullet item "
        "produced by `LatexExporter.generate_latex_source`. Listings C.2 and C.3 record live execution logs "
        "from the Python backend (`unittest`) and Chrome extension (`Vitest`) verification runs."
    )

    sample_tex = r"""%-------------------------
% Clyde AI Career Copilot - Tailored ATS Resume
% Based on: Jake's Resume / sb2nov (Single-Column ATS Format)
% Compatible with: Overleaf, Tectonic, pdflatex, XeLaTeX
%------------------------
\documentclass[letterpaper,11pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{tabularx}

% Candidate: Utkarsh Shah | JUET Guna (241B278)
\section{Projects \& Engineering Experience}
  \resumeSubHeadingListStart
    \resumeProjectHeading
      {\textbf{AI-Powered Resume Automation Platform} $|$ \emph{Python, FastAPI, FAISS, TypeScript}}{2026}
      \resumeItemListStart
        \resumeItem{Engineered a FAISS IndexFlatIP job matching pipeline with four-factor hybrid ranking}
        \resumeItem{Implemented decoupled EventBus supporting Redis Pub/Sub with asyncio failover}
      \resumeItemListEnd
  \resumeSubHeadingListEnd"""
    add_code_block(doc, "Listing C.1: Generated Single-Column Overleaf/Tectonic Resume Excerpt (.tex)", sample_tex)

    backend_log = """$ python3 -m unittest discover "backend/tests" -v
test_relational_cascade (test_database.TestDatabaseSchema) ... ok
test_seeded_companies_and_jobs (test_database.TestDatabaseSchema) ... ok
test_seeded_users (test_database.TestDatabaseSchema) ... ok
test_event_bus_publish_subscribe (test_event_agents.TestEventAgents) ... ok
test_model_router_and_telemetry (test_event_agents.TestEventAgents) ... ok
test_faiss_vector_normalization_and_indexing (test_faiss_matching.TestFAISSAndMatching) ... ok
test_multi_factor_job_matching (test_faiss_matching.TestFAISSAndMatching) ... ok
test_drafter_reviewer_multi_agent_orchestration (test_integrated_workflow.TestIntegratedWorkflow) ... ok
test_fact_verifier_detects_hallucinations (test_integrated_workflow.TestIntegratedWorkflow) ... ok
test_ghost_job_detector_repost_and_silence_tiers (test_integrated_workflow.TestIntegratedWorkflow) ... ok
test_job_scraper_parsing_and_sanitization (test_integrated_workflow.TestIntegratedWorkflow) ... ok
test_posting_guard_source_host_verification (test_integrated_workflow.TestIntegratedWorkflow) ... ok
test_posting_guard_strips_injections_and_hidden_chars (test_integrated_workflow.TestIntegratedWorkflow) ... ok
test_compile_pdf_with_tectonic (test_latex_exporter.TestLatexExporter) ... ok
test_fact_verifier_audit_in_latex_export (test_latex_exporter.TestLatexExporter) ... ok
test_generate_latex_source (test_latex_exporter.TestLatexExporter) ... ok
test_latex_escaping_and_bolding (test_latex_exporter.TestLatexExporter) ... ok
test_tailored_bullets_injection (test_latex_exporter.TestLatexExporter) ... ok
test_tectonic_binary_detection (test_latex_exporter.TestLatexExporter) ... ok
test_url_sanitization (test_latex_exporter.TestLatexExporter) ... ok
test_download_compiled_pdf_endpoint (test_resume_latex_api.TestResumeLatexApi) ... ok
test_download_resume_latex_source (test_resume_latex_api.TestResumeLatexApi) ... ok
test_export_tailored_latex_endpoint (test_resume_latex_api.TestResumeLatexApi) ... ok
test_text_parsing_and_ats_score (test_resume_parser.TestResumeParser) ... ok
----------------------------------------------------------------------
Ran 24 tests in 18.400s — OK"""
    add_code_block(doc, "Listing C.2: Backend Verification Suite Execution Log (unittest)", backend_log)

    ext_log = """$ cd browser-extension && npx vitest run
 RUN  v2.1.9 /home/utkarsh21/Desktop/Minor 1/browser-extension

  ✓ tests/unit/form-mapper.test.ts (3) 1042ms
  ✓ tests/unit/autofill-engine.test.ts (5) 452ms
  ✓ tests/unit/submission-security.test.ts (4)
  ✓ tests/unit/platform-detection.test.ts (8)
  ✓ tests/unit/websocket-protocol.test.ts (4)

 Test Files  5 passed (5)
      Tests  24 passed (24)
   Duration  19.76s"""
    add_code_block(doc, "Listing C.3: Chrome Manifest V3 Extension Unit Test Execution Log (Vitest + JSDOM)", ext_log)


def build_personal_details_page(doc: Document):
    add_chapter_heading(doc, "PERSONAL DETAILS", page_break=True)
    add_body_p(
        doc,
        "Student team identification details and designated passport-size photograph placeholders "
        "(in university uniform) for the 5th Semester Minor Project-I cohort at JUET Guna:",
        spacing_after=6
    )

    students = [
        ("Utkarsh Shah", "241B278"),
        ("Utsav Kothari", "241B279"),
        ("Yashasv Pandey", "241B295"),
    ]

    for idx, (name, roll) in enumerate(students):
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.style = "Table Grid"
        row = tbl.rows[0]
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

        # Left cell: structured details
        c_info = row.cells[0]
        c_info.width = Cm(12.0)
        set_cell_margins(c_info, top=65, bottom=65, left=120, right=100)
        c_info.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p_info = c_info.paragraphs[0]
        p_info.paragraph_format.line_spacing = 1.25
        p_info.paragraph_format.space_before = Pt(1)
        p_info.paragraph_format.space_after = Pt(1)
        details = (
            f"Name: {name}\n"
            f"Enrolment No.: {roll}\n"
            f"Programme & Semester: B.Tech (CSE), 5th Semester\n"
            f"Email ID: _______________________________\n"
            f"Mobile No.: _____________________________\n"
            f"Permanent Address: ______________________"
        )
        r_det = p_info.add_run(details)
        style_run(r_det, size_pt=10.5)

        # Right cell: Passport photo placeholder box
        c_photo = row.cells[1]
        c_photo.width = Cm(4.0)
        set_cell_shading(c_photo, "F8FAFC")
        set_cell_margins(c_photo, top=140, bottom=140, left=80, right=80)
        c_photo.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p_ph = c_photo.paragraphs[0]
        p_ph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ph.paragraph_format.line_spacing = 1.15
        r_ph = p_ph.add_run("Paste Passport Size\nPhotograph\n(In Uniform)\n[3.5 cm x 4.5 cm]")
        style_run(r_ph, size_pt=9.5, italic=True, color=RGBColor(100, 116, 139))

        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(6 if idx < 2 else 0)


def compile_and_index_pdf(docx_path: Path) -> Tuple[int, List[Tuple[str, str]], List[Tuple[str, str]], List[Tuple[str, str]], Dict[str, int]]:
    """Convert .docx -> temporary PDF via LibreOffice and scan exact rendered page numbers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        cmd = ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(docx_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        pdf_path = tmp_path / (docx_path.stem + ".pdf")
        reader = PdfReader(str(pdf_path))
        pages_text = [page.extract_text() or "" for page in reader.pages]

    total_pages = len(pages_text)

    # Identify boundary between Prelim (Roman) and Chapter 1 (Arabic page 1)
    ch1_idx = None
    decl_idx = None
    for idx, txt in enumerate(pages_text):
        norm = " ".join(txt.split())
        if decl_idx is None and "DECLARATION" in norm and "We hereby certify" in norm:
            decl_idx = idx
        if ch1_idx is None and "CHAPTER 1: INTRODUCTION" in norm and "1.1 Background" in norm:
            ch1_idx = idx
            break

    if decl_idx is None:
        decl_idx = 1
    if ch1_idx is None:
        ch1_idx = 8

    def fmt_page_label(pdf_idx: int) -> str:
        if pdf_idx < decl_idx:
            return "-"
        if pdf_idx < ch1_idx:
            return to_roman(pdf_idx - decl_idx + 1)
        return str(pdf_idx - ch1_idx + 1)

    # Find exact page for List of Figures, List of Tables, ToC items
    toc_targets = [
        ("DECLARATION", "Declaration"),
        ("CERTIFICATE", "Certificate"),
        ("ACKNOWLEDGEMENT", "Acknowledgement"),
        ("ABSTRACT", "Abstract"),
        ("LIST OF FIGURES", "List of Figures"),
        ("LIST OF TABLES", "List of Tables"),
        ("LIST OF SYMBOLS AND ACRONYMS", "List of Symbols and Acronyms"),
        ("TABLE OF CONTENTS", "Table of Contents"),
        ("CHAPTER 1: INTRODUCTION", "Chapter 1: Introduction"),
        ("1.1 Background of the Study", "    1.1 Background of the Study"),
        ("1.2 Problem Statement", "    1.2 Problem Statement"),
        ("1.3 Objectives", "    1.3 Objectives"),
        ("1.4 Scope of the Project", "    1.4 Scope of the Project"),
        ("1.5 Organization of the Report", "    1.5 Organization of the Report"),
        ("CHAPTER 2: LITERATURE REVIEW AND BACKGROUND WORK", "Chapter 2: Literature Review and Background Work"),
        ("2.1 Existing Systems and Related Work", "    2.1 Existing Systems and Related Work"),
        ("2.2 Limitations of Existing Work", "    2.2 Limitations of Existing Work"),
        ("2.3 Need for the Proposed System", "    2.3 Need for the Proposed System"),
        ("CHAPTER 3: SYSTEM DESIGN AND METHODOLOGY", "Chapter 3: System Design and Methodology"),
        ("3.1 System Architecture", "    3.1 System Architecture"),
        ("3.2 Design Methodology", "    3.2 Design Methodology"),
        ("3.3 Data Flow and UML Diagrams", "    3.3 Data Flow and UML Diagrams"),
        ("CHAPTER 4: SYSTEM IMPLEMENTATION AND TESTING", "Chapter 4: System Implementation and Testing"),
        ("4.1 Tools and Technologies Used", "    4.1 Tools and Technologies Used"),
        ("4.2 Implementation Details", "    4.2 Implementation Details"),
        ("4.3 Testing Methods", "    4.3 Testing Methods"),
        ("4.4 Test Results", "    4.4 Test Results"),
        ("CHAPTER 5: RESULTS AND DISCUSSION", "Chapter 5: Results and Discussion"),
        ("5.1 Results Analysis", "    5.1 Results Analysis"),
        ("5.2 Performance Evaluation", "    5.2 Performance Evaluation"),
        ("5.3 Discussion and Engineering Findings", "    5.3 Discussion and Engineering Findings"),
        ("CHAPTER 6: CONCLUSION AND FUTURE WORK", "Chapter 6: Conclusion and Future Work"),
        ("6.1 Conclusion", "    6.1 Conclusion"),
        ("6.2 Future Work", "    6.2 Future Work"),
        ("APPENDIX A: CORE BACKEND SOURCE CODE", "Appendix A: Core Backend Source Code"),
        ("APPENDIX B: CHROME EXTENSION AUTOMATION SOURCE CODE", "Appendix B: Chrome Extension Automation Source Code"),
        ("APPENDIX C: SAMPLE LATEX OUTPUT", "Appendix C: Sample LaTeX Output & Verification Logs"),
        ("REFERENCES", "References"),
        ("PERSONAL DETAILS", "Personal Details (with Photo Placeholders)"),
    ]

    toc_entries = []
    search_start = 1
    for needle, label in toc_targets:
        found_label = "-"
        # Preliminaries scanned before ch1_idx; chapters scanned from search_start onward
        start_idx = 1 if label in {"Declaration", "Certificate", "Acknowledgement", "Abstract", "List of Figures", "List of Tables", "List of Symbols and Acronyms", "Table of Contents"} else ch1_idx
        for p_idx in range(start_idx, total_pages):
            norm = " ".join(pages_text[p_idx].split())
            # For ToC page itself, avoid matching the row inside ToC/LoF by checking start_idx
            if label not in {"Declaration", "Certificate", "Acknowledgement", "Abstract", "List of Figures", "List of Tables", "List of Symbols and Acronyms", "Table of Contents"}:
                pass
            if needle in norm:
                found_label = fmt_page_label(p_idx)
                break
        toc_entries.append((label, found_label))

    # Extract Figures and Tables from Ch1 onward
    fig_defs = [
        ("Figure 3.1", "Four-Layer System Architecture of Clyde (FastAPI, ML Services, and Chrome MV3)"),
        ("Figure 3.2", "Data Flow Diagram (Level 0 Context View and Level 1 Process Pipeline)"),
        ("Figure 3.3", "System Use Case Diagram Across Student, Agent Services, and ATS Portals"),
        ("Figure 3.4", "End-to-End Sequence Diagram from Tailoring Request to Human Approval Gate"),
        ("Figure 3.5", "Backend Service and Extension Class Architecture Diagram"),
        ("Figure 3.6", "19-Table Entity-Relationship (ER) Schema in backend/app/database/models.py"),
        ("Figure 4.1", "Chrome Manifest V3 Extension WebSocket Lifecycle and Safety Execution Flow"),
        ("Figure 4.2", "Clyde Web Interface Showing Parsed Resume Library and Verified Skill Extraction"),
        ("Figure 4.3", "Job Discovery Console Showing Four-Factor Match Scores and Ghost Job Verification Badges"),
        ("Figure 4.4", "AI Career Copilot Conversational Tailoring and Live Apify Job Card Dispatch"),
        ("Figure 4.5", "Compiled Single-Column ATS LaTeX Resume Preview Modal Inside Dashboard"),
        ("Figure 4.6", "Real-Time EventBus Agent Telemetry and Provider Latency Monitor"),
        ("Figure 4.7", "Chrome Manifest V3 Extension Autofill and Mandatory Pre-Submit Confirmation Screen on BrowserOS Neo"),
        ("Figure 5.1", "Four-Factor Hybrid Match Score Breakdown Across Five Target Engineering Openings"),
        ("Figure 5.2", "Observed Execution Latency Profile Across Backend CPU, Tectonic PDF, Groq, and Apify Stages"),
    ]
    lof_entries = []
    for f_no, f_cap in fig_defs:
        pg = "-"
        for p_idx in range(ch1_idx, total_pages):
            norm = " ".join(pages_text[p_idx].split())
            if f"{f_no}:" in norm:
                pg = fmt_page_label(p_idx)
                break
        lof_entries.append((f_no, f_cap, pg))

    tab_defs = [
        ("Table 2.1", "Comparison of Existing Career Automation Systems"),
        ("Table 3.1", "Relational Database Schema Summary (19 SQLAlchemy Tables)"),
        ("Table 3.2", "FastAPI REST and WebSocket Endpoint Reference"),
        ("Table 4.1", "Software Stack and Dependencies"),
        ("Table 4.2", "Automated and End-to-End Verification Results"),
        ("Table 5.1", "Four-Factor Hybrid Ranking Results (Healthy vs. Ghost-Penalized)"),
        ("Table 5.2", "Observed Subsystem Execution Latencies"),
    ]
    lot_entries = []
    for t_no, t_cap in tab_defs:
        pg = "-"
        for p_idx in range(ch1_idx, total_pages):
            norm = " ".join(pages_text[p_idx].split())
            if f"{t_no}:" in norm:
                pg = fmt_page_label(p_idx)
                break
        lot_entries.append((t_no, t_cap, pg))

    stats = {
        "total_pages": total_pages,
        "decl_idx": decl_idx,
        "ch1_idx": ch1_idx,
        "prelim_pages": ch1_idx - decl_idx,
        "main_pages": total_pages - ch1_idx,
    }
    return total_pages, toc_entries, lof_entries, lot_entries, stats


def build_doc(toc_entries, lof_entries, lot_entries):
    doc = Document()
    # Set Base Normal font to Times New Roman 12pt
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(12)

    build_cover_page(doc)
    build_preliminaries(doc, toc_entries, lof_entries, lot_entries)
    build_main_body(doc)
    doc.save(str(OUTPUT_DOCX))


def main():
    # Pass 1: Placeholder page numbers
    placeholder_toc = [("Loading...", "-")] * 35
    placeholder_lof = [(f"Figure {i}", "Placeholder", "-") for i in range(1, 16)]
    placeholder_lot = [(f"Table {i}", "Placeholder", "-") for i in range(1, 8)]

    build_doc(placeholder_toc, placeholder_lof, placeholder_lot)
    total_p1, toc_entries, lof_entries, lot_entries, stats1 = compile_and_index_pdf(OUTPUT_DOCX)
    print(f"Pass 1 compiled: total={total_p1} pages | prelim={stats1['prelim_pages']} | main={stats1['main_pages']}")

    # Pass 2: Inject exact rendered Roman + Arabic page numbers and verify stability
    build_doc(toc_entries, lof_entries, lot_entries)
    total_p2, toc_entries2, lof_entries2, lot_entries2, stats2 = compile_and_index_pdf(OUTPUT_DOCX)
    if total_p2 != total_p1:
        print(f"Pass 2 shifted page count ({total_p1} -> {total_p2}), running Pass 3 stabilization...")
        build_doc(toc_entries2, lof_entries2, lot_entries2)
        total_p2, toc_entries2, lof_entries2, lot_entries2, stats2 = compile_and_index_pdf(OUTPUT_DOCX)

    print(f"Final DOCX saved: {OUTPUT_DOCX}")
    print(f"Final rendered pages: total={total_p2} (Cover=1, Prelim={stats2['prelim_pages']}, Main={stats2['main_pages']})")
    for title, pg in toc_entries2:
        print(f"  {title:52s} -> {pg}")


if __name__ == "__main__":
    main()

