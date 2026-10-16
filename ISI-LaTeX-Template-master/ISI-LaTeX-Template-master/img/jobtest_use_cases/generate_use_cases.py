"""Generate the nine JobTest use-case diagrams (SVG, then PNG at 180 DPI).

Usage:  python generate_use_cases.py          # SVG + PNG next to this script
        python generate_use_cases.py --svg    # SVG only

UML conventions applied (UML 2.5.1):
- solid line            : association between an actor and a use case;
- dashed arrow «include»: behaviour always required by the base use case,
                          arrow from the base to the included use case;
- dashed arrow «extend» : optional or conditional behaviour,
                          arrow from the extending use case to the base;
- hollow-triangle arrow : generalisation; the child use cases are alternative
                          specialisations of an abstract parent (shown in
                          italics), so "Gérer ..." never implies that every
                          child operation is executed.
Actors are always drawn outside the system boundary.
PNG rendering uses Playwright with the system Edge/Chrome browser.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
DPI = 180
SCALE = 1.875  # 1500 px wide SVG -> ~2800 px PNG, as in the original export


def text_block(x, y, text, size=26, weight="normal", anchor="middle", italic=False, halo=False):
    rows = text.split("\n")
    start = y - ((len(rows) - 1) * size * 0.59) + size * 0.35
    cls = "txt halo" if halo else "txt"
    style = ' font-style="italic"' if italic else ""
    body = [f'<text x="{x}" y="{start:.1f}" text-anchor="{anchor}" class="{cls}" '
            f'font-size="{size}" font-weight="{weight}"{style}>']
    for i, row in enumerate(rows):
        body.append(f'<tspan x="{x}" dy="{0 if i == 0 else size * 1.18:.1f}">{escape(row)}</tspan>')
    body.append("</text>")
    return "".join(body)


class Diagram:
    def __init__(self, width, height, boundary):
        self.w, self.h = width, height
        self.bx, self.by, self.bw, self.bh = boundary
        self.cases: dict[str, tuple] = {}
        self.actors: dict[str, tuple] = {}
        self.parts: list[str] = []

    # ── elements ─────────────────────────────────────────────────────────
    def actor(self, key, x, y, label):
        self.actors[key] = (x, y)
        self.parts.append(
            f'<circle cx="{x}" cy="{y-90}" r="30" class="stroke"/>'
            f'<line x1="{x}" y1="{y-60}" x2="{x}" y2="{y+35}" class="stroke"/>'
            f'<line x1="{x-55}" y1="{y-20}" x2="{x+55}" y2="{y-20}" class="stroke"/>'
            f'<line x1="{x}" y1="{y+35}" x2="{x-45}" y2="{y+105}" class="stroke"/>'
            f'<line x1="{x}" y1="{y+35}" x2="{x+45}" y2="{y+105}" class="stroke"/>'
            + text_block(x, y + 150, label, 26, "bold")
        )

    def case(self, key, x, y, w, h, label, abstract=False):
        self.cases[key] = (x, y, w / 2, h / 2)
        self.parts.append(f'<ellipse cx="{x}" cy="{y}" rx="{w/2}" ry="{h/2}" class="usecase"/>'
                          + text_block(x, y, label, 26, italic=abstract))

    # ── geometry ─────────────────────────────────────────────────────────
    def _edge(self, key, tx, ty):
        """Point on the ellipse `key` in the direction of (tx, ty)."""
        cx, cy, a, b = self.cases[key]
        dx, dy = tx - cx, ty - cy
        t = 1.0 / math.sqrt((dx / a) ** 2 + (dy / b) ** 2)
        return cx + t * dx, cy + t * dy

    def _actor_anchor(self, key, tx):
        x, y = self.actors[key]
        return (x + 60 if tx > x else x - 60), y - 20

    # ── relations ────────────────────────────────────────────────────────
    def assoc(self, actor, case):
        cx, cy, a, _ = self.cases[case]
        ax, ay = self._actor_anchor(actor, cx)
        # Attach to the horizontal extremity facing the actor so that lines
        # fanning out of the actor never cut through a neighbouring ellipse.
        ex, ey = (cx + a if ax > cx else cx - a), cy
        self.parts.append(f'<line x1="{ax}" y1="{ay}" x2="{ex:.1f}" y2="{ey:.1f}" class="stroke"/>')

    def dep(self, source, target, kind, label_dx=0, label_dy=-16):
        """«include»: source = base. «extend»: source = extending use case."""
        sx, sy = self._edge(source, *self.cases[target][:2])
        tx, ty = self._edge(target, *self.cases[source][:2])
        mx, my = (sx + tx) / 2 + label_dx, (sy + ty) / 2 + label_dy
        self.parts.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" class="dep" marker-end="url(#open)"/>'
            + text_block(mx, my, f"«{kind}»", 22, halo=True))

    def generalisation(self, parent, children, bus_x):
        """Children joined on a vertical bus, one hollow triangle on the parent."""
        px, py = self.cases[parent][:2]
        ys = []
        for child in children:
            cx, cy, a, _ = self.cases[child]
            edge_x = cx - a if bus_x < cx else cx + a
            self.parts.append(f'<line x1="{edge_x}" y1="{cy}" x2="{bus_x}" y2="{cy}" class="stroke thin"/>')
            ys.append(cy)
        ys.append(py)
        self.parts.append(f'<line x1="{bus_x}" y1="{min(ys)}" x2="{bus_x}" y2="{max(ys)}" class="stroke thin"/>')
        ex, ey = self._edge(parent, bus_x, py)
        self.parts.append(f'<line x1="{bus_x}" y1="{py}" x2="{ex:.1f}" y2="{ey:.1f}" '
                          f'class="stroke thin" marker-end="url(#gen)"/>')

    def note(self, x, y, text):
        self.parts.append(text_block(x, y, text, 22, italic=True))

    # ── output ───────────────────────────────────────────────────────────
    def svg(self):
        head = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">
<defs>
  <marker id="open" markerWidth="18" markerHeight="14" refX="16" refY="7" orient="auto" markerUnits="userSpaceOnUse"><path d="M1,1 L16,7 L1,13" fill="none" stroke="#263238" stroke-width="2.4"/></marker>
  <marker id="gen" markerWidth="26" markerHeight="24" refX="24" refY="12" orient="auto" markerUnits="userSpaceOnUse"><path d="M1,1 L24,12 L1,23 z" fill="white" stroke="#17202a" stroke-width="2.4"/></marker>
</defs>
<style>
  .txt {{ font-family: 'DejaVu Sans', Arial, sans-serif; fill:#17202a; }}
  .halo {{ paint-order: stroke; stroke: white; stroke-width: 7px; stroke-linejoin: round; }}
  .boundary {{ fill:#fbfcfd; stroke:#34495e; stroke-width:2.5; }}
  .usecase {{ fill:#eef5ff; stroke:#245b9e; stroke-width:2.5; }}
  .stroke {{ fill:none; stroke:#17202a; stroke-width:3; }}
  .thin {{ stroke-width:2.4; }}
  .dep {{ fill:none; stroke:#263238; stroke-width:2.4; stroke-dasharray:11 8; }}
</style>
<rect width="100%" height="100%" fill="white"/>
<rect x="{self.bx}" y="{self.by}" width="{self.bw}" height="{self.bh}" rx="8" class="boundary"/>
{text_block(self.bx + 30, self.by + 36, "Système JobTest", 27, "bold", "start")}
'''
        return head + "".join(self.parts) + "</svg>"


def build() -> dict[str, Diagram]:
    d: dict[str, Diagram] = {}

    # 01 — Global view
    g = Diagram(1600, 1080, (250, 30, 1080, 1020))
    g.actor("vis", 115, 330, "Visiteur non\nauthentifié")
    g.actor("rec", 1470, 560, "Recruteur\nauthentifié")
    g.case("signup", 540, 230, 330, 76, "Créer un compte")
    g.case("login", 540, 380, 330, 76, "S’authentifier")
    labels = [
        ("dash", "Consulter le tableau de bord"), ("offers", "Gérer les offres"),
        ("cands", "Gérer les candidats"), ("eval", "Évaluer un CV"),
        ("result", "Consulter un résultat"), ("pdf", "Générer un rapport PDF"),
        ("rank", "Classer plusieurs CV"), ("hist", "Consulter l’historique"),
        ("quality", "Comparer les méthodes et\nconsulter le benchmark"),
        ("settings", "Régler les seuils de décision"),
    ]
    for i, (key, label) in enumerate(labels):
        g.case(key, 1040, 110 + i * 98, 430 if "\n" in label else 400, 84 if "\n" in label else 72, label)
    g.case("deep", 560, 502, 380, 84, "Demander une analyse\napprofondie")
    g.assoc("vis", "signup"); g.assoc("vis", "login")
    for key, _ in labels:
        g.assoc("rec", key)
    g.dep("deep", "result", "extend", label_dy=-22)
    d["01_global"] = g

    # 02 — UC-01 authentication
    a = Diagram(1600, 820, (250, 30, 1080, 760))
    a.actor("vis", 115, 380, "Visiteur non\nauthentifié")
    a.actor("rec", 1470, 460, "Recruteur\nauthentifié")
    a.case("signup", 560, 240, 340, 90, "Créer un compte")
    a.case("login", 560, 480, 340, 90, "S’authentifier")
    a.case("profile", 1030, 330, 380, 90, "Consulter son profil")
    a.case("logout", 1030, 590, 340, 90, "Se déconnecter")
    a.assoc("vis", "signup"); a.assoc("vis", "login")
    a.assoc("rec", "profile"); a.assoc("rec", "logout")
    d["02_authentification"] = a

    # 03 — UC-02 job offers (alternatives as specialisations)
    o = Diagram(1500, 900, (260, 30, 1180, 840))
    o.actor("rec", 120, 450, "Recruteur\nauthentifié")
    o.case("manage", 520, 450, 340, 100, "Gérer les offres\nd’emploi", abstract=True)
    o.case("list", 1110, 130, 380, 82, "Consulter ses offres")
    o.case("create", 1110, 285, 400, 92, "Créer une offre\n(code automatique)")
    o.case("edit", 1110, 440, 380, 82, "Modifier une offre")
    o.case("status", 1110, 590, 400, 92, "Ouvrir ou clôturer\nune offre")
    o.case("delete", 1110, 755, 420, 100, "Supprimer une offre\n[aucune évaluation liée]")
    o.assoc("rec", "manage")
    o.generalisation("manage", ["list", "create", "edit", "status", "delete"], bus_x=820)
    d["03_offres"] = o

    # 04 — UC-03 candidates
    c = Diagram(1500, 900, (260, 30, 1180, 840))
    c.actor("rec", 120, 450, "Recruteur\nauthentifié")
    c.case("manage", 520, 450, 340, 100, "Gérer les candidats", abstract=True)
    c.case("list", 1110, 210, 440, 100, "Consulter la liste et\nl’activité d’évaluation")
    c.case("update", 1110, 450, 440, 100, "Modifier l’identité et\nle statut du pipeline")
    c.case("delete", 1110, 690, 440, 100, "Supprimer un candidat\n[aucun résultat associé]")
    c.assoc("rec", "manage")
    c.generalisation("manage", ["list", "update", "delete"], bus_x=820)
    d["04_candidats"] = c

    # 05 — UC-04 CV evaluation
    e = Diagram(1500, 900, (260, 30, 1180, 840))
    e.actor("rec", 120, 400, "Recruteur\nauthentifié")
    e.case("eval", 520, 400, 320, 92, "Évaluer un CV")
    e.case("offer", 1080, 130, 440, 92, "Choisir une offre active\n(ouverte ou en attente)")
    e.case("cv", 1080, 300, 440, 96, "Saisir le CV ou\ntéléverser un PDF/DOCX")
    e.case("compute", 1080, 480, 440, 96, "Calculer et enregistrer\nun résultat explicable")
    e.case("view", 1080, 650, 380, 84, "Consulter le résultat")
    e.case("method", 520, 720, 420, 96, "Choisir une autre méthode\n(hybride par défaut)")
    e.assoc("rec", "eval")
    for key in ("offer", "cv", "compute", "view"):
        e.dep("eval", key, "include")
    e.dep("method", "eval", "extend", label_dx=70, label_dy=0)
    d["05_evaluation_cv"] = e

    # 06 — UC-05 optional deep analysis
    p = Diagram(1500, 720, (260, 30, 1180, 660))
    p.actor("rec", 120, 330, "Recruteur\nauthentifié")
    p.case("result", 560, 270, 380, 96, "Consulter un résultat\nd’évaluation")
    p.case("request", 1080, 270, 400, 96, "Demander une analyse\napprofondie")
    p.case("status", 1080, 540, 440, 110, "Consulter l’état et le contenu\nde l’analyse approfondie")
    p.assoc("rec", "result")
    p.dep("request", "result", "extend", label_dy=-20)
    p.note(815, 345, "[résultat persistant]")
    p.dep("request", "status", "include", label_dx=70, label_dy=0)
    d["06_analyse_approfondie"] = p

    # 07 — UC-06 PDF report
    r = Diagram(1500, 900, (260, 30, 1180, 840))
    r.actor("rec", 120, 450, "Recruteur\nauthentifié")
    r.case("generate", 530, 450, 380, 92, "Générer un rapport PDF")
    r.case("select", 1080, 280, 420, 96, "Sélectionner un résultat\ndéjà calculé")
    r.case("download", 1080, 620, 380, 92, "Télécharger le document")
    r.assoc("rec", "generate")
    r.dep("generate", "select", "include")
    r.dep("generate", "download", "include")
    d["07_rapport_pdf"] = r

    # 08 — UC-07 ranking
    k = Diagram(1500, 900, (260, 30, 1180, 840))
    k.actor("rec", 120, 400, "Recruteur\nauthentifié")
    k.case("rank", 510, 400, 360, 92, "Classer plusieurs CV")
    k.case("offer", 1080, 140, 440, 92, "Choisir une offre active\n(ouverte ou en attente)")
    k.case("upload", 1080, 320, 440, 96, "Téléverser plusieurs CV\nau format PDF/DOCX")
    k.case("display", 1080, 510, 440, 96, "Afficher le classement\npar score décroissant")
    k.case("export", 1080, 730, 400, 92, "Exporter le classement\nau format CSV")
    k.assoc("rec", "rank")
    for key in ("offer", "upload", "display"):
        k.dep("rank", key, "include")
    k.dep("export", "display", "extend", label_dx=70, label_dy=0)
    d["08_classement"] = k

    # 09 — UC-08 history
    h = Diagram(1500, 900, (260, 30, 1180, 840))
    h.actor("rec", 120, 450, "Recruteur\nauthentifié")
    h.case("history", 510, 450, 360, 92, "Consulter l’historique")
    h.case("list", 1080, 200, 420, 92, "Lister ses évaluations")
    h.case("filter", 1080, 450, 440, 100, "Filtrer par code, offre\nou courriel")
    h.case("detail", 1080, 700, 420, 96, "Consulter le détail\nd’un résultat")
    h.assoc("rec", "history")
    h.dep("history", "list", "include")
    h.dep("filter", "history", "extend")
    h.dep("detail", "history", "extend", label_dy=-22)
    d["09_historique"] = h
    return d


def render_png(svg_paths: list[Path]) -> None:
    from playwright.sync_api import sync_playwright
    from PIL import Image

    with sync_playwright() as pw:
        browser = None
        for channel in ("msedge", "chrome"):
            try:
                browser = pw.chromium.launch(channel=channel)
                break
            except Exception:
                continue
        if browser is None:
            browser = pw.chromium.launch()
        for path in svg_paths:
            text = path.read_text(encoding="utf-8")
            w = int(text.split('width="', 1)[1].split('"', 1)[0])
            h = int(text.split('height="', 1)[1].split('"', 1)[0])
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=SCALE)
            page.goto(path.as_uri())
            png = path.with_suffix(".png")
            page.screenshot(path=str(png), full_page=False)
            page.close()
            with Image.open(png) as im:
                im.convert("RGB").save(png, dpi=(DPI, DPI))
        browser.close()


def main() -> None:
    paths = []
    for name, diagram in build().items():
        path = OUT / f"{name}.svg"
        path.write_text(diagram.svg(), encoding="utf-8")
        paths.append(path)
    if "--svg" not in sys.argv:
        render_png(paths)
    print(OUT)


if __name__ == "__main__":
    main()
