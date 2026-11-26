"""
Generates editable .drawio (diagrams.net XML) technical diagrams and matching
300 DPI PNG exports + Matplotlib evaluation charts for the B.Tech Project Report.
"""
import os
import html
import xml.etree.ElementTree as ET
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

OUT_DIR = Path("/home/utkarsh21/Desktop/Minor 1/report/diagrams")
OUT_DIR.mkdir(parents=True, exist_ok=True)


class DiagramBuilder:
    """Builds synchronized .drawio XML and 300-DPI Matplotlib PNG from one specification."""

    def __init__(self, name: str, width: float = 1200, height: float = 750, title: str = ""):
        self.name = name
        self.width = width
        self.height = height
        self.title = title
        self.nodes = []
        self.edges = []
        self.groups = []
        self._id_counter = 2

    def next_id(self) -> str:
        val = str(self._id_counter)
        self._id_counter += 1
        return val

    def add_group(self, x: float, y: float, w: float, h: float, label: str, fill="#F8FAFC", stroke="#94A3B8"):
        self.groups.append({
            "id": self.next_id(), "x": x, "y": y, "w": w, "h": h,
            "label": label, "fill": fill, "stroke": stroke
        })

    def add_box(self, key: str, x: float, y: float, w: float, h: float, label: str,
                fill="#EFF6FF", stroke="#1E40AF", shape="rect", font_size=11, bold=True):
        self.nodes.append({
            "id": self.next_id(), "key": key, "x": x, "y": y, "w": w, "h": h,
            "label": label, "fill": fill, "stroke": stroke, "shape": shape,
            "font_size": font_size, "bold": bold
        })

    def add_edge(self, src_key: str, dst_key: str, label: str = "", dashed: bool = False,
                 src_side: str = "auto", dst_side: str = "auto", color: str = "#334155"):
        self.edges.append({
            "id": self.next_id(), "src": src_key, "dst": dst_key, "label": label,
            "dashed": dashed, "src_side": src_side, "dst_side": dst_side, "color": color
        })

    def _find_node(self, key: str):
        for n in self.nodes:
            if n["key"] == key:
                return n
        raise KeyError(f"Unknown node key: {key}")

    def _anchor(self, node, side: str, other):
        cx, cy = node["x"] + node["w"] / 2, node["y"] + node["h"] / 2
        ox, oy = other["x"] + other["w"] / 2, other["y"] + other["h"] / 2
        if side == "auto":
            dx, dy = ox - cx, oy - cy
            if abs(dx) > abs(dy) * 1.1:
                side = "right" if dx > 0 else "left"
            else:
                side = "bottom" if dy > 0 else "top"
        if side == "top":
            return (cx, node["y"])
        if side == "bottom":
            return (cx, node["y"] + node["h"])
        if side == "left":
            return (node["x"], cy)
        return (node["x"] + node["w"], cy)

    def save_drawio(self):
        mxfile = ET.Element("mxfile", host="app.diagrams.net", modified="2026-11-25T00:00:00.000Z", agent="JUET-CSE-DrawIO", version="24.0.0")
        diagram = ET.SubElement(mxfile, "diagram", id="diag-1", name=self.name)
        model = ET.SubElement(diagram, "mxGraphModel", dx="1422", dy="794", grid="1", gridSize="10",
                              guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                              pageScale="1", pageWidth=str(int(self.width)), pageHeight=str(int(self.height)))
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")

        for g in self.groups:
            style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={g['fill']};strokeColor={g['stroke']};dashed=1;verticalAlign=top;fontStyle=1;fontSize=12;spacingTop=6;fontColor=#0F172A;"
            cell = ET.SubElement(root, "mxCell", id=g["id"], value=g["label"], style=style, vertex="1", parent="1")
            ET.SubElement(cell, "mxGeometry", x=str(g["x"]), y=str(g["y"]), width=str(g["w"]), height=str(g["h"]), **{"as": "geometry"})

        for n in self.nodes:
            shape_style = ""
            if n["shape"] == "ellipse":
                shape_style = "ellipse;"
            elif n["shape"] == "diamond":
                shape_style = "rhombus;"
            elif n["shape"] == "cylinder":
                shape_style = "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=12;"
            else:
                shape_style = "rounded=1;"
            fw = "1" if n["bold"] else "0"
            style = f"{shape_style}whiteSpace=wrap;html=1;fillColor={n['fill']};strokeColor={n['stroke']};strokeWidth=1.5;fontSize={n['font_size']};fontStyle={fw};fontColor=#0F172A;"
            cell = ET.SubElement(root, "mxCell", id=n["id"], value=n["label"].replace("\n", "<br>"), style=style, vertex="1", parent="1")
            ET.SubElement(cell, "mxGeometry", x=str(n["x"]), y=str(n["y"]), width=str(n["w"]), height=str(n["h"]), **{"as": "geometry"})

        for e in self.edges:
            sn = self._find_node(e["src"])
            dn = self._find_node(e["dst"])
            dash = "dashed=1;" if e["dashed"] else ""
            style = f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;{dash}strokeColor={e['color']};strokeWidth=1.4;fontSize=10;fontColor=#1E293B;"
            cell = ET.SubElement(root, "mxCell", id=e["id"], value=e["label"], style=style, edge="1", parent="1", source=sn["id"], target=dn["id"])
            ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})

        tree = ET.ElementTree(mxfile)
        ET.indent(tree, space="  ")
        out_path = OUT_DIR / f"{self.name}.drawio"
        tree.write(out_path, encoding="utf-8", xml_declaration=True)
        return out_path

    def save_png(self, dpi=300):
        fig_w = self.width / 100.0
        fig_h = self.height / 100.0
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
        ax.set_xlim(0, self.width)
        ax.set_ylim(self.height, 0)
        ax.axis("off")
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")

        if self.title:
            ax.text(self.width / 2, 22, self.title, ha="center", va="center",
                    fontsize=13, fontweight="bold", color="#0F172A", family="DejaVu Sans")

        # Draw groups
        for g in self.groups:
            rect = FancyBboxPatch((g["x"], g["y"]), g["w"], g["h"],
                                  boxstyle="round,pad=0.3,rounding_size=8",
                                  facecolor=g["fill"], edgecolor=g["stroke"],
                                  linestyle="--", linewidth=1.2, zorder=1)
            ax.add_patch(rect)
            ax.text(g["x"] + 12, g["y"] + 16, g["label"], ha="left", va="center",
                    fontsize=9.5, fontweight="bold", color="#334155", family="DejaVu Sans", zorder=2)

        # Draw nodes
        for n in self.nodes:
            cx = n["x"] + n["w"] / 2
            cy = n["y"] + n["h"] / 2
            if n["shape"] == "ellipse":
                patch = patches.Ellipse((cx, cy), n["w"], n["h"], facecolor=n["fill"],
                                        edgecolor=n["stroke"], linewidth=1.5, zorder=3)
                ax.add_patch(patch)
            elif n["shape"] == "diamond":
                pts = [(cx, n["y"]), (n["x"] + n["w"], cy), (cx, n["y"] + n["h"]), (n["x"], cy)]
                patch = patches.Polygon(pts, closed=True, facecolor=n["fill"],
                                        edgecolor=n["stroke"], linewidth=1.5, zorder=3)
                ax.add_patch(patch)
            elif n["shape"] == "cylinder":
                rect = FancyBboxPatch((n["x"], n["y"] + 6), n["w"], n["h"] - 12,
                                      boxstyle="round,pad=0.2,rounding_size=6",
                                      facecolor=n["fill"], edgecolor=n["stroke"], linewidth=1.5, zorder=3)
                ax.add_patch(rect)
                top_e = patches.Ellipse((cx, n["y"] + 8), n["w"], 14, facecolor=n["fill"],
                                        edgecolor=n["stroke"], linewidth=1.4, zorder=4)
                ax.add_patch(top_e)
            else:
                patch = FancyBboxPatch((n["x"], n["y"]), n["w"], n["h"],
                                       boxstyle="round,pad=0.2,rounding_size=7",
                                       facecolor=n["fill"], edgecolor=n["stroke"], linewidth=1.5, zorder=3)
                ax.add_patch(patch)

            ax.text(cx, cy + (3 if n["shape"] == "cylinder" else 0), n["label"],
                    ha="center", va="center",
                    fontsize=n["font_size"] * 0.82,
                    fontweight="bold" if n["bold"] else "normal",
                    color="#0F172A", family="DejaVu Sans", zorder=5, linespacing=1.25)

        # Draw edges
        for e in self.edges:
            sn = self._find_node(e["src"])
            dn = self._find_node(e["dst"])
            p1 = self._anchor(sn, e["src_side"], dn)
            p2 = self._anchor(dn, e["dst_side"], sn)
            ls = "--" if e["dashed"] else "-"
            edge_z = 2 if e["dashed"] else 6
            arrow = FancyArrowPatch(
                p1, p2,
                arrowstyle="-|>,head_length=6,head_width=3.5",
                linestyle=ls, linewidth=1.3, color=e["color"],
                connectionstyle="arc3,rad=0.03", zorder=edge_z
            )
            ax.add_patch(arrow)
            if e["label"]:
                mx = (p1[0] + p2[0]) / 2
                my = (p1[1] + p2[1]) / 2
                ax.text(mx, my - 4, e["label"], ha="center", va="center",
                        fontsize=7.6, color="#1E293B", family="DejaVu Sans",
                        bbox=dict(boxstyle="round,pad=0.18", facecolor="#FFFFFF", edgecolor="#E2E8F0", alpha=0.95),
                        zorder=7)

        out_path = OUT_DIR / f"{self.name}.png"
        plt.tight_layout(pad=0.2)
        plt.savefig(out_path, dpi=dpi, facecolor="#FFFFFF")
        plt.close(fig)
        return out_path

    def build(self):
        d = self.save_drawio()
        p = self.save_png()
        print(f"Built {d.name} & {p.name}")


def build_system_architecture():
    b = DiagramBuilder("fig3_1_system_architecture", 1180, 760, "System Architecture: Clyde AI-Powered Resume Automation Platform")

    # Layer 1: Client & Extension
    b.add_group(40, 48, 1100, 125, "Layer 1: Presentation & Browser Execution Layer", "#F8FAFC", "#64748B")
    b.add_box("ui", 80, 92, 320, 64, "Clyde Dark Editorial Web App\n(HTML5, Tailwind CSS, Vanilla JS)", "#EFF6FF", "#1D4ED8")
    b.add_box("ext_sw", 445, 92, 280, 64, "Chrome MV3 Background Worker\n(WebSocketManager, MessageRouter)", "#FEF3C7", "#B45309")
    b.add_box("ext_cs", 825, 92, 285, 64, "Content Script & Platform Adapters\n(FormMapper, Autofill, Approval Gate)", "#FEF3C7", "#B45309")

    # Layer 2: API Gateway & Orchestration
    b.add_group(40, 205, 1100, 132, "Layer 2: FastAPI Gateway, Event Bus & Model Router", "#F8FAFC", "#64748B")
    b.add_box("api", 75, 252, 285, 68, "FastAPI REST & WS Gateway\n(/agent, /resumes, /jobs, /extension/ws)", "#ECFDF5", "#047857")
    b.add_box("bus", 425, 252, 290, 68, "Asynchronous Event Bus\n(Redis Pub/Sub + In-Memory Failover)", "#ECFDF5", "#047857")
    b.add_box("router", 785, 252, 320, 68, "Central Model Router\n(GLM Drafter, Qwen Reviewer, Groq LPU)", "#F3E8FF", "#6D28D9")

    # Layer 3: Domain Intelligence Engines
    b.add_group(40, 370, 1100, 165, "Layer 3: Domain Intelligence & Security Modules", "#F8FAFC", "#64748B")
    b.add_box("parser", 70, 418, 190, 95, "Resume Parser &\nLaTeX Exporter\n(PyPDF + Tectonic)", "#E0F2FE", "#0369A1")
    b.add_box("guard", 285, 418, 190, 95, "PostingGuard\nSecurity Gate\n(Unicode & CSS Scan)", "#FFE4E6", "#BE123C")
    b.add_box("match", 500, 418, 200, 95, "Hybrid Matching &\nGhost Job Detector\n(4-Factor Formula)", "#E0F2FE", "#0369A1")
    b.add_box("fact", 725, 418, 185, 95, "FactVerifier\nAnti-Hallucination\n(Provenance Audit)", "#FFE4E6", "#BE123C")
    b.add_box("scraper", 935, 418, 180, 95, "Apify Live Job\nScraper Service\n(Naukri / ATS Feeds)", "#E0F2FE", "#0369A1")

    # Layer 4: Persistence
    b.add_group(40, 568, 1100, 148, "Layer 4: Relational & Vector Persistence Layer", "#F8FAFC", "#64748B")
    b.add_box("db", 150, 612, 405, 84, "SQLAlchemy Relational Database (19 Tables)\nUsers, Resumes, Versions, Profiles, Jobs, Matches, Workflows", "#F1F5F9", "#334155", shape="cylinder")
    b.add_box("faiss", 635, 612, 405, 84, "FAISS Vector Store (IndexFlatIP, 128-D)\nL2-Normalized Cosine Retrieval (jobs.faiss, resumes.faiss)", "#F1F5F9", "#334155", shape="cylinder")

    # Edges
    b.add_edge("ui", "api", "REST / JSON", src_side="bottom", dst_side="top")
    b.add_edge("ext_sw", "api", "WSS / Token", src_side="bottom", dst_side="top")
    b.add_edge("ext_sw", "ext_cs", "chrome.tabs", src_side="right", dst_side="left")
    b.add_edge("api", "bus", "Publish Events", src_side="right", dst_side="left")
    b.add_edge("bus", "router", "Orchestrate", src_side="right", dst_side="left")
    b.add_edge("api", "parser", "Upload / Export", src_side="bottom", dst_side="top")
    b.add_edge("api", "guard", "Sanitize", src_side="bottom", dst_side="top")
    b.add_edge("api", "match", "Rank Jobs", src_side="bottom", dst_side="top")
    b.add_edge("router", "fact", "Audit Bullets", src_side="bottom", dst_side="top")
    b.add_edge("api", "scraper", "Scrape Live", src_side="bottom", dst_side="top")
    b.add_edge("parser", "db", "Persist Profile", src_side="bottom", dst_side="top")
    b.add_edge("match", "db", "Save Matches", src_side="bottom", dst_side="top")
    b.add_edge("match", "faiss", "Top-K Cosine", src_side="bottom", dst_side="top")
    b.add_edge("scraper", "faiss", "Index Vectors", src_side="bottom", dst_side="top")

    b.build()


def build_dfd():
    b = DiagramBuilder("fig3_2_dfd_level0_level1", 1180, 740, "Data Flow Diagram (Level 0 Context & Level 1 Core Processing)")

    # Level 0 Context (Left panel)
    b.add_group(35, 55, 360, 645, "DFD Level 0: Context Diagram", "#FAFAFA", "#64748B")
    b.add_box("cand0", 115, 110, 200, 56, "Candidate / Student\n(User)", "#EFF6FF", "#1D4ED8")
    b.add_box("sys0", 90, 290, 250, 95, "0.0\nAI-Powered Resume\nAutomation System", "#ECFDF5", "#047857", shape="ellipse")
    b.add_box("llm0", 115, 495, 200, 56, "LLM Inference & Apify\nExternal Services", "#F3E8FF", "#6D28D9")
    b.add_box("port0", 115, 610, 200, 56, "Target ATS &\nJob Application Portals", "#FEF3C7", "#B45309")

    b.add_edge("cand0", "sys0", "PDF Resume / Queries", src_side="bottom", dst_side="top")
    b.add_edge("sys0", "llm0", "Prompts / Scrape Req", src_side="bottom", dst_side="top")
    b.add_edge("sys0", "port0", "Approved Autofill", src_side="right", dst_side="right", dashed=True)

    # Level 1 Data Flow (Right panel)
    b.add_group(425, 55, 720, 645, "DFD Level 1: Internal Processing Pipeline", "#FAFAFA", "#64748B")
    b.add_box("p1", 465, 110, 195, 68, "1.0 Resume Ingestion\n& PostingGuard Audit", "#E0F2FE", "#0369A1")
    b.add_box("p2", 725, 110, 195, 68, "2.0 Vector Indexing\n(128-D FAISS Store)", "#E0F2FE", "#0369A1")
    b.add_box("p3", 940, 245, 180, 74, "3.0 Live Job Scraping\n& Ghost Detection", "#E0F2FE", "#0369A1")
    b.add_box("p4", 630, 245, 220, 74, "4.0 4-Factor Hybrid\nJob Matching Engine", "#ECFDF5", "#047857")
    b.add_box("p5", 455, 395, 210, 74, "5.0 Drafter-Reviewer\n& FactVerifier Gate", "#F3E8FF", "#6D28D9")
    b.add_box("p6", 730, 395, 200, 74, "6.0 LaTeX Compiler\n(Tectonic ATS PDF)", "#ECFDF5", "#047857")
    b.add_box("p7", 545, 540, 255, 74, "7.0 Extension WebSocket\nForm Mapper & Approval", "#FEF3C7", "#B45309")
    b.add_box("d1", 940, 542, 180, 68, "D1: SQLAlchemy DB\n(19 Normalized Tables)", "#F1F5F9", "#334155", shape="cylinder")

    b.add_edge("p1", "p2", "Clean Profile", src_side="right", dst_side="left")
    b.add_edge("p2", "p4", "Vectors", src_side="bottom", dst_side="top")
    b.add_edge("p3", "p4", "Sanitized JDs", src_side="left", dst_side="right")
    b.add_edge("p4", "p5", "Matched JD", src_side="bottom", dst_side="top")
    b.add_edge("p5", "p6", "Verified Bullets", src_side="right", dst_side="left")
    b.add_edge("p6", "p7", "ATS Resume PDF", src_side="bottom", dst_side="top")
    b.add_edge("p5", "p7", "Profile Payload", src_side="bottom", dst_side="top")
    b.add_edge("p3", "d1", "Save JDs", src_side="bottom", dst_side="top", dashed=True)
    b.add_edge("p7", "d1", "Log Event", src_side="right", dst_side="left", dashed=True)

    b.build()


def build_use_case():
    b = DiagramBuilder("fig3_3_use_case_diagram", 1100, 720, "UML Use Case Diagram: Clyde Career Automation System")

    # System Boundary
    b.add_group(250, 55, 600, 625, "Clyde AI Career Automation System Boundary", "#F8FAFC", "#334155")

    # Actors
    b.add_box("actor_stu", 40, 260, 150, 70, "<<Actor>>\nCandidate /\nJUET Student", "#EFF6FF", "#1D4ED8", shape="ellipse")
    b.add_box("actor_llm", 910, 140, 150, 70, "<<Actor>>\nLLM Providers\n(Groq/GLM/Qwen)", "#F3E8FF", "#6D28D9", shape="ellipse")
    b.add_box("actor_apify", 910, 310, 150, 70, "<<Actor>>\nApify Live\nJob Scraper", "#E0F2FE", "#0369A1", shape="ellipse")
    b.add_box("actor_ats", 910, 485, 150, 70, "<<Actor>>\nExternal ATS\nJob Portals", "#FEF3C7", "#B45309", shape="ellipse")

    # Use cases
    ucs = [
        ("uc1", 310, 95, 220, 58, "UC1: Upload & Parse\nPDF Resume"),
        ("uc2", 570, 95, 220, 58, "UC2: Run PostingGuard\nSecurity Scan"),
        ("uc3", 310, 200, 220, 58, "UC3: Discover Live Jobs\nby City & Skills"),
        ("uc4", 570, 200, 220, 58, "UC4: Compute 4-Factor\nFAISS Match Score"),
        ("uc5", 310, 315, 220, 58, "UC5: Tailor Resume\n(Drafter-Reviewer Loop)"),
        ("uc6", 570, 315, 220, 58, "UC6: Audit Provenance\n(FactVerifier Gate)"),
        ("uc7", 310, 430, 220, 58, "UC7: Compile & Export\nJake's LaTeX PDF"),
        ("uc8", 570, 430, 220, 58, "UC8: Map & Autofill\nForm via Extension"),
        ("uc9", 440, 560, 230, 64, "UC9: Review Preview &\nApprove Final Submission"),
    ]
    for k, x, y, w, h, lbl in ucs:
        b.add_box(k, x, y, w, h, lbl, "#FFFFFF", "#1E40AF", shape="ellipse", font_size=10)

    for uc in ["uc1", "uc3", "uc5", "uc7", "uc8", "uc9"]:
        b.add_edge("actor_stu", uc, "", src_side="right", dst_side="left")

    b.add_edge("uc1", "uc2", "<<include>>", dashed=True, src_side="right", dst_side="left")
    b.add_edge("uc3", "uc4", "<<include>>", dashed=True, src_side="right", dst_side="left")
    b.add_edge("uc5", "uc6", "<<include>>", dashed=True, src_side="right", dst_side="left")
    b.add_edge("uc8", "uc9", "<<include>>", dashed=True, src_side="bottom", dst_side="top")
    b.add_edge("uc5", "actor_llm", "", src_side="right", dst_side="left")
    b.add_edge("uc3", "actor_apify", "", src_side="right", dst_side="left")
    b.add_edge("uc8", "actor_ats", "", src_side="right", dst_side="left")
    b.add_edge("uc9", "actor_ats", "Manual Confirm", src_side="right", dst_side="left")

    b.build()


def build_sequence():
    b = DiagramBuilder("fig3_4_sequence_diagram", 1180, 740, "UML Sequence Diagram: Autonomous Tailor, Extension Autofill & Approval Gate")

    lifelines = [
        ("u", 50, "Candidate\n(Browser UI)", "#EFF6FF", "#1D4ED8"),
        ("api", 230, "FastAPI\n(/agent/chat)", "#ECFDF5", "#047857"),
        ("mr", 415, "ModelRouter\n& FactVerifier", "#F3E8FF", "#6D28D9"),
        ("ws", 605, "ExtensionWS\nManager", "#ECFDF5", "#047857"),
        ("sw", 795, "MV3 Service\nWorker", "#FEF3C7", "#B45309"),
        ("cs", 985, "ContentScript\n& FormMapper", "#FEF3C7", "#B45309"),
    ]
    for key, x, lbl, fill, stroke in lifelines:
        b.add_box(key, x, 60, 145, 54, lbl, fill, stroke, font_size=10)
        b.add_box(f"{key}_end", x + 52, 665, 40, 26, "End", "#F1F5F9", "#94A3B8", font_size=8, bold=False)
        b.add_edge(key, f"{key}_end", "", dashed=True, src_side="bottom", dst_side="top", color="#94A3B8")

    # Sequence step nodes positioned along rows
    steps = [
        ("s1", 65, 145, 115, 36, "1. Submit Prompt", "#FFFFFF", "#1D4ED8"),
        ("s2", 245, 145, 115, 36, "2. Resolve Job\n& Profile", "#FFFFFF", "#047857"),
        ("s3", 430, 215, 115, 42, "3. Drafter(GLM)\nReviewer(Qwen)", "#FFFFFF", "#6D28D9"),
        ("s4", 430, 285, 115, 42, "4. Audit 100%\nProvenance", "#FFE4E6", "#BE123C"),
        ("s5", 245, 355, 115, 38, "5. Update DB &\nReturn Cards", "#FFFFFF", "#047857"),
        ("s6", 620, 355, 115, 38, "6. Broadcast\nFILL_FORM", "#FFFFFF", "#047857"),
        ("s7", 810, 425, 115, 42, "7. Query Tab &\nInject content.js", "#FFFFFF", "#B45309"),
        ("s8", 1000, 425, 125, 42, "8. Map Inputs &\nAttach Resume", "#FFFFFF", "#B45309"),
        ("s9", 1000, 505, 125, 42, "9. Validate &\nBuild Preview", "#FFFFFF", "#B45309"),
        ("s10", 620, 575, 115, 42, "10. Emit\nAPPLICATION_READY", "#ECFDF5", "#047857"),
        ("s11", 65, 575, 115, 42, "11. Manual User\nApproval Gate", "#FFE4E6", "#BE123C"),
    ]
    for k, x, y, w, h, lbl, fill, st in steps:
        b.add_box(k, x, y, w, h, lbl, fill, st, font_size=9)

    b.add_edge("s1", "s2", "POST /chat", src_side="right", dst_side="left")
    b.add_edge("s2", "s3", "Tailor Req", src_side="right", dst_side="left")
    b.add_edge("s3", "s4", "Verify", src_side="bottom", dst_side="top")
    b.add_edge("s4", "s5", "Verified", src_side="left", dst_side="right")
    b.add_edge("s5", "s6", "Dispatch", src_side="right", dst_side="left")
    b.add_edge("s6", "s7", "WebSocket", src_side="right", dst_side="left")
    b.add_edge("s7", "s8", "CMD_FILL", src_side="right", dst_side="left")
    b.add_edge("s8", "s9", "DOM Events", src_side="bottom", dst_side="top")
    b.add_edge("s9", "s10", "FORM_FILLED", src_side="left", dst_side="right")
    b.add_edge("s10", "s11", "Hold Review", src_side="left", dst_side="right", dashed=True)

    b.build()


def build_class_diagram():
    b = DiagramBuilder("fig3_5_class_diagram", 1180, 740, "UML Class Diagram: Core Backend Services & Extension Architecture")

    classes = [
        ("c_router", 45, 70, 260, 145, "ModelRouter\n----------------\n+ providers: Dict\n+ routing_rules: Dict\n----------------\n+ route(task_type): str\n+ generate_response()\n+ orchestrate_drafter_reviewer()"),
        ("c_fact", 355, 70, 250, 145, "FactVerifier\n----------------\n+ FORBIDDEN_BUZZWORDS: Set\n+ QUANT_METRIC_REGEX\n----------------\n+ extract_source_facts()\n+ audit_tailored_bullet()\n+ audit_tailored_resume()"),
        ("c_guard", 650, 70, 240, 145, "PostingGuard\n----------------\n+ INVISIBLE: str\n+ HIDDEN_STYLE: Pattern\n----------------\n+ clean_text(raw): Dict\n+ verify_source_host(url)"),
        ("c_bus", 930, 70, 210, 145, "EventBus\n----------------\n+ _redis_client\n+ _subscribers: Dict\n----------------\n+ connect()\n+ subscribe()\n+ publish(event_type)"),

        ("c_parser", 45, 275, 250, 155, "ResumeParser\n----------------\n+ COMMON_SKILLS: List\n----------------\n+ extract_text_from_pdf()\n+ parse_text(text): Dict\n+ save_parsed_profile()"),
        ("c_vec", 345, 275, 260, 155, "VectorStore\n----------------\n+ dim: int = 128\n+ job_index: IndexFlatIP\n+ resume_index: IndexFlatIP\n----------------\n+ generate_embedding()\n+ add_job() / add_resume()\n+ search_jobs_for_resume()"),
        ("c_match", 650, 275, 260, 155, "MatchingEngine\n----------------\n+ WEIGHT_SEMANTIC = 0.40\n+ WEIGHT_SKILLS = 0.30\n----------------\n+ compute_match()\n+ match_candidate_against_all()"),
        ("c_ghost", 945, 275, 195, 155, "GhostJobDetector\n----------------\n+ structural_flags: List\n+ outcome_flags: List\n----------------\n+ evaluate_job_legitimacy()"),

        ("c_ws", 45, 505, 265, 175, "WebSocketManager (TS)\n----------------\n- ws: WebSocket\n- reconnectAttempts: int\n----------------\n+ connect()\n+ scheduleReconnect()\n+ send(eventType, payload)"),
        ("c_mr", 355, 505, 265, 175, "MessageRouter (TS)\n----------------\n- wsManager: WebSocketMgr\n----------------\n+ handleBackendEvent()\n+ queryTargetTabs(url)\n+ sendTabMessageWithRetry()"),
        ("c_fm", 665, 505, 240, 175, "FormMapper (TS)\n----------------\n- rules: DetectionRule[]\n----------------\n+ extractFormFields(doc)\n+ resolveProfileValue()\n+ validateForm(fields)"),
        ("c_af", 940, 505, 200, 175, "AutofillEngine (TS)\n----------------\n+ fillField(field, val)\n+ fillBatch(actions)\n+ attachResumePDF()"),
    ]
    for k, x, y, w, h, lbl in classes:
        fill = "#FEF3C7" if "(TS)" in lbl else "#EFF6FF"
        stroke = "#B45309" if "(TS)" in lbl else "#1E40AF"
        b.add_box(k, x, y, w, h, lbl, fill, stroke, font_size=9.5, bold=False)

    b.add_edge("c_router", "c_fact", "audits", src_side="right", dst_side="left")
    b.add_edge("c_match", "c_vec", "queries", src_side="left", dst_side="right")
    b.add_edge("c_match", "c_ghost", "penalizes", src_side="right", dst_side="left")
    b.add_edge("c_parser", "c_guard", "sanitizes", src_side="top", dst_side="bottom", dashed=True)
    b.add_edge("c_ws", "c_mr", "routes", src_side="right", dst_side="left")
    b.add_edge("c_mr", "c_fm", "dispatches", src_side="right", dst_side="left")
    b.add_edge("c_fm", "c_af", "action plan", src_side="right", dst_side="left")

    b.build()


def build_er_diagram():
    b = DiagramBuilder("fig3_6_er_diagram", 1180, 740, "Entity-Relationship (ER) Diagram: 19-Table Multi-User Relational Schema")

    entities = [
        ("e_user", 50, 80, 190, 95, "User\nPK user_id\nemail, full_name\ncreated_at"),
        ("e_res", 295, 80, 205, 95, "Resume\nPK resume_id\nFK user_id\ncurrent_version_id"),
        ("e_ver", 555, 80, 210, 95, "ResumeVersion\nPK version_id\nFK resume_id\nresume_content, ats_score"),
        ("e_wf", 840, 80, 280, 95, "Workflow & AgentRun\nPK workflow_id | PK agent_run_id\nFK user_id, status, start/end_time"),

        ("e_prof", 50, 265, 225, 110, "CandidateProfile\nPK profile_id\nFK user_id, FK resume_id\nfull_name, email, phone, headline"),
        ("e_skill", 330, 240, 195, 70, "CandidateSkill\nPK skill_id, FK profile_id\nskill_name, category"),
        ("e_edu", 330, 330, 195, 70, "CandidateEducation\nPK edu_id, FK profile_id\ninstitution, degree, gpa"),
        ("e_exp", 570, 240, 205, 70, "CandidateExperience\nPK exp_id, FK profile_id\ncompany, role, dates"),
        ("e_proj", 570, 330, 205, 70, "CandidateProject\nPK project_id, FK profile_id\ntitle, technologies"),

        ("e_comp", 840, 265, 280, 95, "Company & JobSource\nPK company_id | PK source_id\nname, website, industry, type"),
        ("e_job", 840, 445, 280, 115, "Job\nPK job_id\nFK company_id, FK source_id\ntitle, required_skills, location, job_url"),
        ("e_match", 460, 465, 280, 115, "JobMatch\nPK match_id\nFK user_id, FK job_id\nmatch_score, semantic, skills, reason"),
        ("e_app", 50, 465, 310, 125, "Application & ApplicationEvent\nPK application_id | PK event_id\nFK user_id, FK job_id, FK resume_id\nstatus, event_type, timestamp"),
        ("e_emb", 460, 620, 660, 75, "CoverLetter, ProviderHealth & EmbeddingReference\nCoverLetter(FK user_id, job_id) | ProviderHealth(provider, healthy) | EmbeddingReference(entity_id, vector_id)"),
    ]
    for k, x, y, w, h, lbl in entities:
        b.add_box(k, x, y, w, h, lbl, "#F8FAFC", "#0F172A", font_size=9, bold=False)

    b.add_edge("e_user", "e_res", "1:N", src_side="right", dst_side="left")
    b.add_edge("e_res", "e_ver", "1:N", src_side="right", dst_side="left")
    b.add_edge("e_user", "e_prof", "1:N", src_side="bottom", dst_side="top")
    b.add_edge("e_user", "e_wf", "1:N", src_side="top", dst_side="top", dashed=True)
    b.add_edge("e_prof", "e_skill", "1:N", src_side="right", dst_side="left")
    b.add_edge("e_prof", "e_edu", "1:N", src_side="right", dst_side="left")
    b.add_edge("e_skill", "e_exp", "", src_side="right", dst_side="left", dashed=True)
    b.add_edge("e_edu", "e_proj", "", src_side="right", dst_side="left", dashed=True)
    b.add_edge("e_comp", "e_job", "1:N", src_side="bottom", dst_side="top")
    b.add_edge("e_job", "e_match", "1:N", src_side="left", dst_side="right")
    b.add_edge("e_job", "e_app", "1:N", src_side="bottom", dst_side="bottom", dashed=True)
    b.add_edge("e_prof", "e_app", "1:N", src_side="bottom", dst_side="top")

    b.build()


def build_extension_flowchart():
    b = DiagramBuilder("fig4_1_extension_flow", 1040, 770, "Flowchart: Chrome Manifest V3 Form Autofill & Security Approval Gate")

    b.add_box("st", 340, 52, 260, 52, "Start: Backend Dispatches\nFILL_FORM via WebSocket", "#ECFDF5", "#047857", shape="ellipse")
    b.add_box("dedup", 305, 128, 330, 62, "TaskManager: Check task_id\nDuplicate?", "#FEF3C7", "#B45309", shape="diamond")
    b.add_box("tab", 300, 215, 340, 56, "MessageRouter.queryTargetTabs()\nMatch Open Tab or Create & Wait", "#EFF6FF", "#1D4ED8")
    b.add_box("inj", 300, 298, 340, 56, "sendTabMessageWithRetry()\nInject content.js (Max 6 Retries)", "#EFF6FF", "#1D4ED8")
    b.add_box("adap", 300, 382, 340, 56, "PlatformRegistry.getAdapterForPage()\nSelect Greenhouse/Lever/Workday/Generic", "#E0F2FE", "#0369A1")
    b.add_box("map", 295, 466, 350, 64, "FormMapper (8-Level Strategy)\n& AutofillEngine (React Prototype Setter)\n+ DataTransfer Resume PDF Attach", "#F3E8FF", "#6D28D9")
    b.add_box("prev", 300, 558, 340, 56, "SubmissionEngine.generatePreview()\nEmit FORM_FILLED & APPLICATION_READY", "#ECFDF5", "#047857")
    b.add_box("gate", 290, 640, 360, 78, "SECURITY APPROVAL GATE:\nUser Reviewed & Approved?\n(Never Auto-Submits)", "#FFE4E6", "#BE123C", shape="diamond")
    b.add_box("ign", 755, 134, 210, 50, "Ignore Duplicate\nLog Warning", "#F1F5F9", "#64748B")
    b.add_box("sub", 755, 654, 230, 54, "Execute Submission\nwith Approval Token", "#ECFDF5", "#047857", shape="ellipse")

    b.add_edge("st", "dedup", "", src_side="bottom", dst_side="top")
    b.add_edge("dedup", "ign", "Yes", src_side="right", dst_side="left")
    b.add_edge("dedup", "tab", "No", src_side="bottom", dst_side="top")
    b.add_edge("tab", "inj", "", src_side="bottom", dst_side="top")
    b.add_edge("inj", "adap", "", src_side="bottom", dst_side="top")
    b.add_edge("adap", "map", "", src_side="bottom", dst_side="top")
    b.add_edge("map", "prev", "", src_side="bottom", dst_side="top")
    b.add_edge("prev", "gate", "", src_side="bottom", dst_side="top")
    b.add_edge("gate", "sub", "Explicit Approval", src_side="right", dst_side="left")

    b.build()


def build_evaluation_charts():
    # Chart 1: 4-Factor Hybrid Match Score Breakdown across Benchmark Openings
    roles = [
        "NVIDIA\nAI & DL Intern",
        "GlobalFoundries\nAI Strategist",
        "Bajaj Finance\nExec. Debt Mgmt",
        "Canonical\nJr. Python Eng",
        "Microsoft\nML Research Intern"
    ]
    semantic = np.array([59.3, 62.1, 54.0, 68.5, 58.2])
    skills = np.array([87.5, 83.3, 100.0, 80.0, 62.5])
    exp = np.array([95.0, 95.0, 75.0, 95.0, 95.0])
    pref = np.array([95.0, 95.0, 80.0, 95.0, 95.0])
    overall = 0.40 * semantic + 0.30 * skills + 0.15 * exp + 0.15 * pref

    x = np.arange(len(roles))
    width = 0.18

    fig, ax = plt.subplots(figsize=(10.5, 5.2), dpi=300)
    ax.bar(x - 1.5 * width, semantic, width, label="FAISS Semantic (40%)", color="#3B82F6")
    ax.bar(x - 0.5 * width, skills, width, label="Skill Overlap (30%)", color="#10B981")
    ax.bar(x + 0.5 * width, exp, width, label="Experience Alignment (15%)", color="#F59E0B")
    ax.bar(x + 1.5 * width, overall, width, label="Composite Match Score (%)", color="#1E293B")

    for i, v in enumerate(overall):
        ax.text(x[i] + 1.5 * width, v + 1.8, f"{v:.1f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_ylabel("Score (%)", fontsize=10, fontweight="bold")
    ax.set_title("4-Factor Hybrid Job Matching Score Breakdown (Candidate: Utkarsh Shah)", fontsize=11.5, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(roles, fontsize=9)
    ax.set_ylim(0, 115)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="upper right", fontsize=8.5, ncol=2)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig5_1_matching_scores.png", dpi=300)
    plt.close(fig)

    # Chart 2: Component Latency & Execution Verification Benchmarks
    ops = [
        "FAISS Index\nQuery (top_k=20)",
        "Resume Parsing\n& ATS Scoring",
        "Extension WS\nForm Autofill",
        "Tectonic PDF\nCompilation",
        "Groq LLM Chat\n(Discovery)",
        "Apify Naukri\nLive Scrape"
    ]
    latencies_ms = [18, 185, 220, 1950, 3055, 6731]
    colors = ["#10B981", "#10B981", "#3B82F6", "#F59E0B", "#8B5CF6", "#EC4899"]

    fig, ax = plt.subplots(figsize=(10.0, 4.8), dpi=300)
    bars = ax.barh(ops, latencies_ms, color=colors, height=0.55)
    for bar, val in zip(bars, latencies_ms):
        ax.text(val + 120, bar.get_y() + bar.get_height() / 2, f"{val} ms", va="center", ha="left", fontsize=9, fontweight="bold")

    ax.set_xlabel("Observed Execution Latency (ms)", fontsize=10, fontweight="bold")
    ax.set_title("Measured End-to-End Subsystems Latency Profile", fontsize=11.5, fontweight="bold", pad=12)
    ax.set_xlim(0, 7800)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig5_2_latency_benchmarks.png", dpi=300)
    plt.close(fig)
    print("Built fig5_1_matching_scores.png & fig5_2_latency_benchmarks.png")


if __name__ == "__main__":
    build_system_architecture()
    build_dfd()
    build_use_case()
    build_sequence()
    build_class_diagram()
    build_er_diagram()
    build_extension_flowchart()
    build_evaluation_charts()
