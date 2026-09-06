"""
src/reporting/pdf_generator.py
Professional HR-style PDF report generator for JobTest AI Platform.
Uses reportlab for pure-Python PDF generation with Unicode support.
"""
from __future__ import annotations

import io
import math
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import
import matplotlib.pyplot as plt
import numpy as np

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.lib.utils import ImageReader  # noqa: F401 — kept for optional direct use
    from reportlab.platypus import (
        Flowable,
        HRFlowable,
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover
    REPORTLAB_AVAILABLE = False


# ─────────────────────────────────────────────
# Colour palette — professional dark-blue HR theme
# ─────────────────────────────────────────────
class _Palette:
    PRIMARY       = colors.HexColor("#1A2B4A")   # deep navy
    SECONDARY     = colors.HexColor("#2563EB")   # vivid blue
    ACCENT        = colors.HexColor("#10B981")   # emerald green
    WARNING       = colors.HexColor("#F59E0B")   # amber
    DANGER        = colors.HexColor("#EF4444")   # red
    LIGHT_BG      = colors.HexColor("#F8FAFC")   # near-white
    BORDER        = colors.HexColor("#E2E8F0")   # light grey
    TEXT_DARK     = colors.HexColor("#1E293B")   # slate 900
    TEXT_MUTED    = colors.HexColor("#64748B")   # slate 500
    WHITE         = colors.white
    HIRE_GREEN    = colors.HexColor("#D1FAE5")
    CONSIDER_AMB  = colors.HexColor("#FEF3C7")
    REJECT_RED    = colors.HexColor("#FEE2E2")


# ─────────────────────────────────────────────
# Chart helpers
# ─────────────────────────────────────────────

def _render_donut_chart(score: float, label: str = "") -> io.BytesIO:
    """Render a donut / gauge chart and return PNG bytes."""
    fig, ax = plt.subplots(figsize=(3.2, 3.2), subplot_kw={"aspect": "equal"})
    fig.patch.set_facecolor("#F8FAFC")

    pct = min(max(score, 0.0), 100.0)
    color = "#10B981" if pct >= 75 else ("#F59E0B" if pct >= 55 else "#EF4444")

    wedge_props = {"width": 0.35, "edgecolor": "white", "linewidth": 2}
    ax.pie(
        [pct, 100 - pct],
        startangle=90,
        colors=[color, "#E2E8F0"],
        wedgeprops=wedge_props,
        counterclock=False,
    )
    ax.text(0, 0, f"{pct:.0f}%", ha="center", va="center",
            fontsize=22, fontweight="bold", color="#1E293B")
    if label:
        ax.text(0, -0.55, label, ha="center", va="center",
                fontsize=8, color="#64748B")
    ax.axis("off")
    plt.tight_layout(pad=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _render_radar_chart(radar_data: Dict) -> io.BytesIO:
    """Render a radar/spider chart from explainer radar_data and return PNG bytes."""
    labels     = radar_data.get("labels", [])
    cv_scores  = radar_data.get("cv_scores", [])
    job_req    = radar_data.get("job_requirements", [])

    if not labels:
        # empty placeholder
        fig, ax = plt.subplots(figsize=(3.5, 3.5))
        ax.text(0.5, 0.5, "No radar data", ha="center", va="center")
        ax.axis("off")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120)
        plt.close(fig)
        buf.seek(0)
        return buf

    n      = len(labels)
    angles = [x / float(n) * 2 * math.pi for x in range(n)]
    angles += angles[:1]

    cv_vals  = [v / 100.0 for v in cv_scores]  + [cv_scores[0] / 100.0]
    job_vals = [v / 100.0 for v in job_req]    + [job_req[0] / 100.0]

    fig, ax = plt.subplots(figsize=(3.8, 3.8),
                           subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")

    ax.plot(angles, cv_vals,  color="#2563EB", linewidth=2, label="Candidate")
    ax.fill(angles, cv_vals,  color="#2563EB", alpha=0.18)
    ax.plot(angles, job_vals, color="#10B981", linewidth=1.5,
            linestyle="--", label="Required")
    ax.fill(angles, job_vals, color="#10B981", alpha=0.08)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=7, color="#1E293B")
    ax.set_yticklabels([])
    ax.set_ylim(0, 1)
    ax.spines["polar"].set_color("#E2E8F0")
    ax.tick_params(colors="#64748B")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1),
              fontsize=7, framealpha=0.7)
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _render_score_bar(label: str, score: float, max_score: float = 100.0) -> io.BytesIO:
    """Render a horizontal bar chart for component scores."""
    components = list(label.items()) if isinstance(label, dict) else []
    if not components:
        components = [("Score", score)]

    fig, ax = plt.subplots(figsize=(5.5, max(1.5, len(components) * 0.55)))
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")

    names  = [c[0] for c in components]
    values = [min(float(c[1]), max_score) for c in components]
    colors_list = ["#2563EB" if v >= 75 else ("#F59E0B" if v >= 55 else "#EF4444")
                   for v in values]

    bars = ax.barh(names, values, color=colors_list, height=0.5,
                   edgecolor="white", linewidth=1)
    for bar, val in zip(bars, values):
        ax.text(min(val + 1.5, max_score - 5), bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", fontsize=8, color="#1E293B")

    ax.set_xlim(0, max_score)
    ax.set_xlabel("Score (%)", fontsize=8, color="#64748B")
    ax.tick_params(labelsize=8, colors="#1E293B")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#E2E8F0")
    ax.set_facecolor("#F8FAFC")
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────
# Flowable: coloured section header band
# ─────────────────────────────────────────────
class _SectionHeader(Flowable):  # type: ignore[misc]
    def __init__(self, title: str, width: float = 17 * cm) -> None:
        super().__init__()
        self.title = title
        self.width = width
        self.height = 0.7 * cm

    def draw(self) -> None:
        self.canv.setFillColor(_Palette.PRIMARY)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self.canv.setFillColor(_Palette.WHITE)
        self.canv.setFont("Helvetica-Bold", 10)
        self.canv.drawString(0.3 * cm, 0.17 * cm, self.title.upper())


class _ScoreBadge(Flowable):  # type: ignore[misc]
    """Inline coloured badge for HIRE / CONSIDER / REJECT."""

    _COLOURS = {
        "HIRE":    ("#D1FAE5", "#065F46"),
        "CONSIDER": ("#FEF3C7", "#92400E"),
        "REJECT":  ("#FEE2E2", "#991B1B"),
    }

    def __init__(self, text: str, width: float = 5 * cm) -> None:
        super().__init__()
        self.text = text.upper()
        self.width = width
        self.height = 0.8 * cm
        bg_hex, fg_hex = self._COLOURS.get(self.text, ("#E2E8F0", "#1E293B"))
        self.bg  = colors.HexColor(bg_hex)
        self.fg  = colors.HexColor(fg_hex)

    def draw(self) -> None:
        r = 0.15 * cm
        self.canv.setFillColor(self.bg)
        self.canv.roundRect(0, 0, self.width, self.height, r, fill=1, stroke=0)
        self.canv.setFillColor(self.fg)
        self.canv.setFont("Helvetica-Bold", 11)
        self.canv.drawCentredString(self.width / 2, 0.2 * cm, self.text)


# ─────────────────────────────────────────────
# Main PDF generator class
# ─────────────────────────────────────────────
class MatchReportPDF:
    """
    Generates a professional HR-style PDF evaluation report.

    Usage::

        generator = MatchReportPDF()
        pdf_bytes = generator.generate(
            result=hybrid_result,
            explanation=explanation,
            recommendations=recommendations,
            candidate_name="Alice Martin",
            job_title="Senior ML Engineer",
        )
        # pdf_bytes is a bytes object ready to stream or save
    """

    PAGE_W, PAGE_H = A4
    MARGIN = 1.5 * cm

    def __init__(self) -> None:
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Run: pip install reportlab"
            )
        self._styles = self._build_styles()

    # ── Style sheet ──────────────────────────────────────────────────────────
    @staticmethod
    def _build_styles() -> dict:
        base = getSampleStyleSheet()
        styles: dict = {}

        def _ps(name: str, **kwargs) -> ParagraphStyle:
            return ParagraphStyle(name, parent=base["Normal"], **kwargs)

        styles["title"] = _ps(
            "RPT_Title",
            fontSize=22, fontName="Helvetica-Bold",
            textColor=_Palette.PRIMARY, alignment=TA_CENTER,
            spaceAfter=4,
        )
        styles["subtitle"] = _ps(
            "RPT_Subtitle",
            fontSize=11, fontName="Helvetica",
            textColor=_Palette.TEXT_MUTED, alignment=TA_CENTER,
            spaceAfter=2,
        )
        styles["section"] = _ps(
            "RPT_Section",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=_Palette.WHITE,
        )
        styles["body"] = _ps(
            "RPT_Body",
            fontSize=9, fontName="Helvetica",
            textColor=_Palette.TEXT_DARK,
            leading=13, spaceAfter=3,
        )
        styles["label"] = _ps(
            "RPT_Label",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=_Palette.TEXT_MUTED,
        )
        styles["value"] = _ps(
            "RPT_Value",
            fontSize=9, fontName="Helvetica",
            textColor=_Palette.TEXT_DARK,
        )
        styles["bullet_green"] = _ps(
            "RPT_BulletGreen",
            fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#065F46"),
            leftIndent=12, leading=13,
        )
        styles["bullet_red"] = _ps(
            "RPT_BulletRed",
            fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#991B1B"),
            leftIndent=12, leading=13,
        )
        styles["bullet_amber"] = _ps(
            "RPT_BulletAmber",
            fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#92400E"),
            leftIndent=12, leading=13,
        )
        styles["verdict"] = _ps(
            "RPT_Verdict",
            fontSize=13, fontName="Helvetica-Bold",
            textColor=_Palette.PRIMARY, alignment=TA_CENTER,
        )
        styles["meta"] = _ps(
            "RPT_Meta",
            fontSize=7.5, fontName="Helvetica",
            textColor=_Palette.TEXT_MUTED, alignment=TA_RIGHT,
        )
        styles["footer"] = _ps(
            "RPT_Footer",
            fontSize=7, fontName="Helvetica",
            textColor=_Palette.TEXT_MUTED, alignment=TA_CENTER,
        )
        styles["recommendation"] = _ps(
            "RPT_Recommendation",
            fontSize=9, fontName="Helvetica-Oblique",
            textColor=_Palette.TEXT_DARK,
            leading=14, spaceAfter=4,
        )
        return styles

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(
        self,
        report_id: str,
        generated_at: str,
        candidate_name: str,
        job_title: str,
    ) -> List:
        st = self._styles
        elems: List = []

        # Logo area (text-based since no image asset available)
        header_data = [
            [
                Paragraph("<b><font color='#2563EB'>Job</font><font color='#1A2B4A'>Test</font> <font size='9' color='#64748B'>AI Recruitment Platform</font></b>",
                           ParagraphStyle("Logo", fontSize=16, fontName="Helvetica-Bold",
                                          textColor=_Palette.PRIMARY)),
                Paragraph(
                    f"Report ID: <b>{report_id}</b><br/>Generated: {generated_at}",
                    st["meta"],
                ),
            ]
        ]
        tbl = Table(header_data, colWidths=[10 * cm, 7 * cm])
        tbl.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ]))
        elems.append(tbl)
        elems.append(HRFlowable(width="100%", thickness=2,
                                color=_Palette.SECONDARY, spaceAfter=6))

        # Title block
        elems.append(Paragraph("CANDIDATE EVALUATION REPORT", st["title"]))
        elems.append(Paragraph(
            f"Position: <b>{job_title or 'N/A'}</b> &nbsp;|&nbsp; Candidate: <b>{candidate_name or 'N/A'}</b>",
            st["subtitle"],
        ))
        elems.append(Spacer(1, 0.3 * cm))
        return elems

    # ── Info table ────────────────────────────────────────────────────────────
    def _build_info_table(
        self,
        candidate_name: str,
        job_title: str,
        skill_details: Dict,
        explanation: Dict,
    ) -> List:
        st = self._styles
        elems: List = [_SectionHeader("01 — Candidate Profile"), Spacer(1, 0.2 * cm)]

        cv_payload  = skill_details.get("cv_payload", {})
        job_payload = skill_details.get("job_payload", {})

        def _row(label: str, value: str) -> List:
            return [
                Paragraph(label, st["label"]),
                Paragraph(str(value) if value else "—", st["value"]),
            ]

        years_exp = cv_payload.get("years_experience", 0)
        edu_level = cv_payload.get("education_level", "unknown").capitalize()
        domain    = cv_payload.get("domain", "N/A").replace("_", " ").title()
        verdict_colour = explanation.get("color", "orange")
        verdict_text   = explanation.get("verdict", "N/A")

        candidate_data = [
            _row("Full Name",           candidate_name or "N/A"),
            _row("Target Position",     job_title or "N/A"),
            _row("Domain",              domain),
            _row("Education Level",     edu_level),
            _row("Years of Experience", f"{years_exp} year(s)" if years_exp else "Not detected"),
            _row("Evaluation Verdict",  verdict_text),
        ]

        tbl = Table(candidate_data, colWidths=[4 * cm, 12.5 * cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (0, -1), _Palette.LIGHT_BG),
            ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8.5),
            ("GRID",         (0, 0), (-1, -1), 0.5, _Palette.BORDER),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [_Palette.WHITE, _Palette.LIGHT_BG]),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]))
        elems.append(tbl)
        elems.append(Spacer(1, 0.4 * cm))
        return elems

    # ── Score section ─────────────────────────────────────────────────────────
    def _build_score_section(self, result: Dict, explanation: Dict) -> List:
        elems: List = [_SectionHeader("02 — AI Match Score"), Spacer(1, 0.25 * cm)]

        pct          = float(result.get("percentage", 0.0))
        component_scores = result.get("component_scores", {})
        verdict      = explanation.get("verdict", "N/A")

        # Donut chart
        donut_buf = _render_donut_chart(pct, verdict)
        donut_img = Image(donut_buf, width=5.5 * cm, height=5.5 * cm)

        # Component scores bar chart — normalise keys
        comp_display = {
            k.replace("_score", "").upper(): round(float(v) * 100, 1)
            for k, v in component_scores.items()
        }
        # Always show all 3 components with 0 as fallback
        for key in ("TFIDF", "EMBEDDING", "SKILL"):
            comp_display.setdefault(key, 0.0)

        bar_buf = _render_score_bar(comp_display, pct)
        bar_img = Image(bar_buf, width=9.5 * cm, height=4.5 * cm)

        score_data = [[donut_img, bar_img]]
        tbl = Table(score_data, colWidths=[6 * cm, 10.5 * cm])
        tbl.setStyle(TableStyle([
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",   (0, 0), (0, 0),   "CENTER"),
        ]))
        elems.append(tbl)
        elems.append(Spacer(1, 0.3 * cm))
        return elems

    # ── Radar / Competency section ────────────────────────────────────────────
    def _build_radar_section(self, explanation: Dict) -> List:
        elems: List = [_SectionHeader("03 — Competency Analysis"), Spacer(1, 0.25 * cm)]

        radar_data = explanation.get("radar_data", {})
        radar_buf  = _render_radar_chart(radar_data)
        radar_img  = Image(radar_buf, width=8 * cm, height=7 * cm)

        # Build competency table alongside radar
        labels    = radar_data.get("labels", [])
        cv_scores = radar_data.get("cv_scores", [])
        job_req   = radar_data.get("job_requirements", [])

        st = self._styles
        comp_rows = [
            [
                Paragraph("<b>Dimension</b>", st["label"]),
                Paragraph("<b>Candidate</b>", st["label"]),
                Paragraph("<b>Required</b>",  st["label"]),
                Paragraph("<b>Gap</b>",        st["label"]),
            ]
        ]
        for label, cv, req in zip(labels, cv_scores, job_req):
            gap = cv - req
            gap_text = f"+{gap:.0f}" if gap >= 0 else f"{gap:.0f}"
            gap_colour = "#065F46" if gap >= 0 else "#991B1B"
            comp_rows.append([
                Paragraph(label, st["body"]),
                Paragraph(f"{cv:.0f}%", st["body"]),
                Paragraph(f"{req:.0f}%", st["body"]),
                Paragraph(f"<font color='{gap_colour}'><b>{gap_text}</b></font>", st["body"]),
            ])

        comp_tbl = Table(comp_rows, colWidths=[3.5 * cm, 2 * cm, 2 * cm, 1.8 * cm])
        comp_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), _Palette.PRIMARY),
            ("TEXTCOLOR",     (0, 0), (-1, 0), _Palette.WHITE),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("GRID",          (0, 0), (-1, -1), 0.5, _Palette.BORDER),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_Palette.WHITE, _Palette.LIGHT_BG]),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ]))

        layout_data = [[radar_img, comp_tbl]]
        layout_tbl  = Table(layout_data, colWidths=[8.5 * cm, 9 * cm])
        layout_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (1, 0), (1, 0), 12),
        ]))
        elems.append(layout_tbl)
        elems.append(Spacer(1, 0.35 * cm))
        return elems

    # ── Skills analysis ───────────────────────────────────────────────────────
    def _build_skills_section(self, explanation: Dict) -> List:
        elems: List = [_SectionHeader("04 — Skills Analysis"), Spacer(1, 0.25 * cm)]

        skill_analysis = explanation.get("skill_analysis", {})
        matching       = skill_analysis.get("matching_skills", [])
        missing        = skill_analysis.get("missing_skills", [])
        extra          = skill_analysis.get("extra_skills", [])
        critical_miss  = skill_analysis.get("critical_missing", [])
        coverage       = skill_analysis.get("skill_coverage", "N/A")

        st = self._styles

        def _chip_list(items: List[str], color: str) -> str:
            if not items:
                return "<font color='#64748B'>None detected</font>"
            chips = [f"<font color='{color}'>● {item}</font>" for item in items]
            return "  ".join(chips)

        rows = [
            ["✅ Matched Skills",    _chip_list(matching, "#065F46")],
            ["❌ Missing Skills",    _chip_list(missing,  "#991B1B")],
            ["⚠️  Critical Missing", _chip_list(critical_miss, "#92400E")],
            ["➕ Extra Skills",      _chip_list(extra,    "#1D4ED8")],
            ["📊 Coverage",          coverage],
        ]
        tbl_data = [
            [Paragraph(r[0], st["label"]), Paragraph(r[1], st["body"])]
            for r in rows
        ]
        tbl = Table(tbl_data, colWidths=[4.5 * cm, 12 * cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, -1), _Palette.LIGHT_BG),
            ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
            ("GRID",          (0, 0), (-1, -1), 0.5, _Palette.BORDER),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [_Palette.WHITE, _Palette.LIGHT_BG]),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elems.append(tbl)
        elems.append(Spacer(1, 0.35 * cm))
        return elems

    # ── Strengths & Weaknesses ────────────────────────────────────────────────
    def _build_swot_section(self, explanation: Dict) -> List:
        elems: List = [_SectionHeader("05 — Strengths & Gaps"), Spacer(1, 0.25 * cm)]

        gap = explanation.get("gap_analysis", {})
        strengths      = gap.get("strengths", [])
        blocking_gaps  = gap.get("blocking_gaps", [])
        minor_gaps     = gap.get("minor_gaps", [])

        st = self._styles

        def _make_bullet_list(items: List[str], style_key: str, prefix: str) -> List:
            if not items:
                return [Paragraph(f"{prefix} None identified", st["body"])]
            return [Paragraph(f"{prefix} {item}", st[style_key]) for item in items]

        strength_paras    = _make_bullet_list(strengths,     "bullet_green", "✔")
        blocking_paras    = _make_bullet_list(blocking_gaps, "bullet_red",   "✘")
        minor_paras       = _make_bullet_list(minor_gaps,    "bullet_amber", "△")

        # Two-column layout
        left_col: List = [
            Paragraph("<b>STRENGTHS</b>", ParagraphStyle(
                "SwotH", fontSize=9, fontName="Helvetica-Bold",
                textColor=colors.HexColor("#065F46"), spaceAfter=4)),
        ] + strength_paras

        right_col: List = [
            Paragraph("<b>BLOCKING GAPS</b>", ParagraphStyle(
                "SwotH2", fontSize=9, fontName="Helvetica-Bold",
                textColor=colors.HexColor("#991B1B"), spaceAfter=4)),
        ] + blocking_paras + [Spacer(1, 0.2 * cm)] + [
            Paragraph("<b>MINOR GAPS</b>", ParagraphStyle(
                "SwotH3", fontSize=9, fontName="Helvetica-Bold",
                textColor=colors.HexColor("#92400E"), spaceAfter=4)),
        ] + minor_paras

        layout = Table([[left_col, right_col]], colWidths=[8.25 * cm, 8.25 * cm])
        layout.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX",           (0, 0), (0, 0), 1, colors.HexColor("#D1FAE5")),
            ("BOX",           (1, 0), (1, 0), 1, colors.HexColor("#FEE2E2")),
            ("BACKGROUND",    (0, 0), (0, 0), colors.HexColor("#F0FDF4")),
            ("BACKGROUND",    (1, 0), (1, 0), colors.HexColor("#FFF5F5")),
        ]))
        elems.append(layout)
        elems.append(Spacer(1, 0.35 * cm))
        return elems

    # ── Recommendations ───────────────────────────────────────────────────────
    def _build_recommendations_section(self, recommendations: Dict) -> List:
        elems: List = [_SectionHeader("06 — Improvement Recommendations"), Spacer(1, 0.25 * cm)]

        st = self._styles
        actions = recommendations.get("priority_actions", [])
        cv_improvements = recommendations.get("cv_improvements", [])
        keywords   = recommendations.get("keywords_to_add", [])
        learning   = recommendations.get("learning_time_estimate", "N/A")
        potential  = recommendations.get("match_potential", "N/A")

        if actions:
            elems.append(Paragraph("<b>Priority Learning Actions</b>", st["label"]))
            elems.append(Spacer(1, 0.1 * cm))
            action_rows = [[
                Paragraph("<b>Skill</b>", st["label"]),
                Paragraph("<b>Importance</b>", st["label"]),
                Paragraph("<b>Resource</b>", st["label"]),
            ]]
            for action in actions[:6]:
                imp_colour = "#991B1B" if action.get("importance") == "critique" else "#92400E"
                action_rows.append([
                    Paragraph(action.get("skill", ""), st["body"]),
                    Paragraph(
                        f"<font color='{imp_colour}'><b>{action.get('importance','').capitalize()}</b></font>",
                        st["body"],
                    ),
                    Paragraph(
                        f"<link href='{action.get('resource','')}'><font color='#2563EB'>{action.get('resource','')[:40]}...</font></link>"
                        if len(action.get("resource","")) > 40
                        else f"<link href='{action.get('resource','')}'><font color='#2563EB'>{action.get('resource','')}</font></link>",
                        st["body"],
                    ),
                ])
            a_tbl = Table(action_rows, colWidths=[3.5 * cm, 2.5 * cm, 10.5 * cm])
            a_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), _Palette.PRIMARY),
                ("TEXTCOLOR",     (0, 0), (-1, 0), _Palette.WHITE),
                ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("GRID",          (0, 0), (-1, -1), 0.5, _Palette.BORDER),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_Palette.WHITE, _Palette.LIGHT_BG]),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elems.append(a_tbl)
            elems.append(Spacer(1, 0.25 * cm))

        if cv_improvements:
            elems.append(Paragraph("<b>CV Improvement Suggestions</b>", st["label"]))
            for item in cv_improvements:
                elems.append(Paragraph(f"• {item}", st["body"]))
            elems.append(Spacer(1, 0.15 * cm))

        summary_data = [
            [Paragraph("⏱ Estimated Learning Time", st["label"]),
             Paragraph(learning, st["body"])],
            [Paragraph("📈 Match Potential After Improvement", st["label"]),
             Paragraph(potential, st["body"])],
            [Paragraph("🔑 Keywords to Add to CV", st["label"]),
             Paragraph(", ".join(keywords) if keywords else "—", st["body"])],
        ]
        s_tbl = Table(summary_data, colWidths=[5.5 * cm, 11 * cm])
        s_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, -1), _Palette.LIGHT_BG),
            ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
            ("GRID",          (0, 0), (-1, -1), 0.5, _Palette.BORDER),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [_Palette.WHITE, _Palette.LIGHT_BG]),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elems.append(s_tbl)
        elems.append(Spacer(1, 0.35 * cm))
        return elems

    # ── Recruiter Decision Support ────────────────────────────────────────────
    def _build_decision_section(self, result: Dict, explanation: Dict) -> List:
        elems: List = [_SectionHeader("07 — Recruiter Decision Support"), Spacer(1, 0.25 * cm)]

        st = self._styles
        pct     = float(result.get("percentage", 0.0))
        verdict = explanation.get("verdict", "N/A")
        color   = explanation.get("color", "orange")

        # Determine recommendation
        hiring_rec = explanation.get("hiring_recommendation", {})
        if hiring_rec:
            decision      = hiring_rec.get("decision", "CONSIDER")
            justification = hiring_rec.get("justification", "")
            confidence    = hiring_rec.get("confidence", 0.0)
        else:
            if pct >= 75:
                decision = "HIRE"
                justification = (
                    f"The candidate scores {pct:.0f}% overall, demonstrating strong alignment "
                    "with the job requirements in terms of technical skills and experience."
                )
                confidence = 0.85
            elif pct >= 55:
                decision = "CONSIDER"
                justification = (
                    f"The candidate scores {pct:.0f}%, showing partial fit. "
                    "A technical interview is recommended to validate the identified gaps."
                )
                confidence = 0.65
            else:
                decision = "REJECT"
                justification = (
                    f"The candidate scores {pct:.0f}%, indicating insufficient match. "
                    "Critical skill gaps exist that would require substantial training."
                )
                confidence = 0.75

        # Badge + justification side by side
        badge    = _ScoreBadge(decision, width=4 * cm)
        just_para = Paragraph(
            f"<b>Recommendation:</b> {justification}<br/>"
            f"<font color='#64748B'>Confidence: {confidence*100:.0f}%</font>",
            st["recommendation"],
        )
        dec_layout = Table(
            [[badge, just_para]],
            colWidths=[4.5 * cm, 12 * cm],
        )
        dec_layout.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BOX",           (0, 0), (-1, -1), 1, _Palette.BORDER),
            ("BACKGROUND",    (0, 0), (-1, -1), _Palette.LIGHT_BG),
        ]))
        elems.append(dec_layout)
        elems.append(Spacer(1, 0.25 * cm))

        # Interview questions suggestion
        elems.append(Paragraph("<b>Suggested Interview Focus Areas</b>", st["label"]))
        skill_analysis = explanation.get("skill_analysis", {})
        missing = skill_analysis.get("missing_skills", [])
        critical = skill_analysis.get("critical_missing", [])
        interview_qs = []
        for skill in (critical or missing)[:4]:
            interview_qs.append(
                f"• Can you describe a project where you applied <b>{skill}</b>?"
            )
        if not interview_qs:
            interview_qs = [
                "• Describe your most technically complex project.",
                "• How do you keep up with industry developments?",
            ]
        for q in interview_qs:
            elems.append(Paragraph(q, st["body"]))
        elems.append(Spacer(1, 0.35 * cm))
        return elems

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self, report_id: str) -> List:
        st = self._styles
        elems: List = [
            HRFlowable(width="100%", thickness=1, color=_Palette.BORDER, spaceAfter=4),
            Paragraph(
                f"This report was automatically generated by JobTest AI Platform · "
                f"Report ID: {report_id} · For internal HR use only · "
                "Results are AI-assisted and should be validated by a qualified recruiter.",
                st["footer"],
            ),
        ]
        return elems

    # ── Public API ────────────────────────────────────────────────────────────
    def generate(
        self,
        result: Dict,
        explanation: Dict,
        recommendations: Dict,
        candidate_name: str = "Unknown Candidate",
        job_title: str = "Unknown Position",
    ) -> bytes:
        """
        Generate a complete PDF evaluation report.

        Parameters
        ----------
        result : dict
            Output from HybridMatcher.predict() or _model_result()
        explanation : dict
            Output from MatchingExplainer.explain()
        recommendations : dict
            Output from RecommendationEngine.generate()
        candidate_name : str
            Display name for the candidate
        job_title : str
            Display name for the job position

        Returns
        -------
        bytes
            Raw PDF bytes suitable for streaming to a browser
        """
        buf        = io.BytesIO()
        report_id  = str(uuid.uuid4()).split("-")[0].upper()
        generated  = datetime.now().strftime("%B %d, %Y — %H:%M")

        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=self.MARGIN,
            rightMargin=self.MARGIN,
            topMargin=self.MARGIN,
            bottomMargin=self.MARGIN + 0.5 * cm,
        )

        skill_details = result.get("skill_details", {})

        story: List = []
        story += self._build_header(report_id, generated, candidate_name, job_title)
        story += self._build_info_table(candidate_name, job_title, skill_details, explanation)
        story += self._build_score_section(result, explanation)
        story += self._build_radar_section(explanation)
        story += self._build_skills_section(explanation)
        story += self._build_swot_section(explanation)
        story += self._build_recommendations_section(recommendations)
        story += self._build_decision_section(result, explanation)
        story += self._build_footer(report_id)

        doc.build(story)
        return buf.getvalue()
