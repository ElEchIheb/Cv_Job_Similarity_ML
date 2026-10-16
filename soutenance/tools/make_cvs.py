from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from demo_data import CVS

OUT = Path(__file__).resolve().parent.parent / "demo" / "cvs"
OUT.mkdir(parents=True, exist_ok=True)
h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=HexColor("#1F2937"))
sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=12, leading=16, textColor=HexColor("#6D28D9"))
small = ParagraphStyle("small", fontName="Helvetica", fontSize=9.5, leading=13, textColor=HexColor("#6B7280"))
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=HexColor("#111827"), spaceBefore=12, spaceAfter=3)
body = ParagraphStyle("body", fontName="Helvetica", fontSize=10.5, leading=15, textColor=HexColor("#374151"), spaceAfter=3)
for key, c in CVS.items():
    doc = SimpleDocTemplate(str(OUT / f"{key}.pdf"), pagesize=A4, leftMargin=54, rightMargin=54, topMargin=50, bottomMargin=50,
                            title=f"CV {c['name']} (fictif - demonstration JobTest)")
    st = [Paragraph(c["name"], h1), Paragraph(c["headline"], sub), Paragraph(c["email"] + "  |  CV fictif - demonstration", small),
          Spacer(1, 6), HRFlowable(width="100%", color=HexColor("#8B5CF6"), thickness=1.2)]
    for title, lines in c["sections"]:
        st.append(Paragraph(title, h2))
        for l in lines: st.append(Paragraph(l, body))
    doc.build(st)
    print("ok", key)
