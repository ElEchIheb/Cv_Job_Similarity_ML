from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path("output/jobtest_use_cases")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1500, 900


def lines(text):
    return text.split("\n")


def text_block(x, y, text, size=25, weight="normal", anchor="middle"):
    rows = lines(text)
    start = y - ((len(rows) - 1) * size * 0.58)
    body = [f'<text x="{x}" y="{start}" text-anchor="{anchor}" class="txt" font-size="{size}" font-weight="{weight}">']
    for i, row in enumerate(rows):
        body.append(f'<tspan x="{x}" dy="{0 if i == 0 else size * 1.18}">{escape(row)}</tspan>')
    body.append('</text>')
    return "".join(body)


def ellipse(x, y, w, h, label):
    return (
        f'<ellipse cx="{x}" cy="{y}" rx="{w/2}" ry="{h/2}" class="usecase"/>'
        + text_block(x, y + 8, label, 23)
    )


def actor(x, y, label):
    return (
        f'<circle cx="{x}" cy="{y-90}" r="30" class="actor"/>'
        f'<line x1="{x}" y1="{y-60}" x2="{x}" y2="{y+35}" class="actor"/>'
        f'<line x1="{x-55}" y1="{y-20}" x2="{x+55}" y2="{y-20}" class="actor"/>'
        f'<line x1="{x}" y1="{y+35}" x2="{x-45}" y2="{y+105}" class="actor"/>'
        f'<line x1="{x}" y1="{y+35}" x2="{x+45}" y2="{y+105}" class="actor"/>'
        + text_block(x, y + 150, label, 24, "bold")
    )


def association(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="assoc"/>'


def dependency(x1, y1, x2, y2, kind):
    mx, my = (x1+x2)/2, (y1+y2)/2
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="dep" marker-end="url(#arrow)"/>'
        + text_block(mx, my-12, f'«{kind}»', 19, anchor="middle")
    )


def svg(title, actors, cases, links, filename):
    chunks = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,8 L10,4 z" fill="#263238"/></marker>
</defs>
<style>
  .txt {{ font-family: 'DejaVu Sans', Arial, sans-serif; fill:#17202a; }}
  .boundary {{ fill:#fbfcfd; stroke:#34495e; stroke-width:2.5; }}
  .usecase {{ fill:#eef5ff; stroke:#245b9e; stroke-width:2.5; }}
  .actor,.assoc {{ fill:none; stroke:#17202a; stroke-width:3; }}
  .dep {{ fill:none; stroke:#263238; stroke-width:2.2; stroke-dasharray:10 8; }}
</style>
<rect width="100%" height="100%" fill="white"/>
{text_block(W/2, 55, title, 32, 'bold')}
<rect x="260" y="95" width="1180" height="745" rx="8" class="boundary"/>
{text_block(295, 135, 'Système JobTest', 25, 'bold', 'start')}
''']
    for x, y, label in actors:
        chunks.append(actor(x, y, label))
    for key, x, y, w, h, label in cases:
        chunks.append(ellipse(x, y, w, h, label))
    for link in links:
        chunks.append(association(*link[1:]) if link[0] == "a" else dependency(*link[1:]))
    chunks.append('</svg>')
    (OUT / filename).write_text("".join(chunks), encoding="utf-8")


svg("Diagramme global des cas d’utilisation", [(120,430,"Visiteur non\nauthentifié"),(1370,430,"Recruteur\nauthentifié")], [
 ("signup",430,210,300,78,"Créer un compte"),("login",430,330,300,78,"S’authentifier"),
 ("dash",830,175,330,72,"Consulter le tableau de bord"),("offers",830,270,280,72,"Gérer les offres"),
 ("cands",830,365,280,72,"Gérer les candidats"),("eval",830,460,280,72,"Évaluer un CV"),
 ("result",830,555,350,72,"Consulter les résultats"),("deep",830,650,360,72,"Demander une analyse approfondie"),
 ("exploit",830,755,530,78,"Exploiter les résultats\n(rapport, classement et historique)"),
],[("a",175,410,280,210),("a",175,435,280,330),("a",1315,360,995,175),("a",1315,385,970,270),("a",1315,410,970,365),("a",1315,435,970,460),("a",1315,460,1005,555),("a",1315,485,1010,650),("a",1315,510,1095,755)],"01_global.svg")

svg("UC-01 — Authentification et gestion de session",[(120,400,"Visiteur non\nauthentifié"),(1370,500,"Recruteur\nauthentifié")],[
 ("signup",520,260,330,90,"Créer un compte"),("login",520,470,330,90,"S’authentifier"),
 ("profile",980,360,360,90,"Consulter son profil"),("logout",980,590,320,90,"Se déconnecter"),
],[("a",175,370,355,260),("a",175,420,355,470),("a",1315,470,1160,360),("a",1315,525,1140,590)],"02_authentification.svg")

svg("UC-02 — Gestion des offres d’emploi",[(120,430,"Recruteur\nauthentifié")],[
 ("manage",500,430,330,95,"Gérer les offres\nd’emploi"),("list",1010,185,330,82,"Consulter ses offres"),
 ("create",1010,310,360,90,"Créer une offre\n(code automatique)"),("edit",1010,435,310,82,"Modifier une offre"),
 ("status",1010,560,330,82,"Changer le statut"),("delete",1010,700,390,95,"Supprimer une offre\nsans évaluation liée"),
],[("a",175,430,335,430),("d",660,400,845,185,"include"),("d",660,415,830,310,"include"),("d",660,430,855,435,"include"),("d",660,445,845,560,"include"),("d",660,460,815,700,"extend")],"03_offres.svg")

svg("UC-03 — Gestion des candidats",[(120,430,"Recruteur\nauthentifié")],[
 ("manage",500,430,330,95,"Gérer les candidats"),("list",1010,195,330,82,"Consulter la liste"),
 ("update",1010,335,390,95,"Mettre à jour l’identité\net le statut du pipeline"),("activity",1010,500,380,92,"Consulter l’activité\nd’évaluation"),
 ("delete",1010,680,410,100,"Supprimer un candidat\nsans résultat associé"),
],[("a",175,430,335,430),("d",660,400,845,195,"include"),("d",660,420,815,335,"include"),("d",660,445,820,500,"include"),("d",660,465,805,680,"extend")],"04_candidats.svg")

svg("UC-04 — Évaluation d’un CV",[(120,430,"Recruteur\nauthentifié")],[
 ("eval",480,430,310,92,"Évaluer un CV"),("offer",990,175,340,84,"Choisir une offre possédée"),
 ("cv",990,310,390,96,"Saisir le CV ou\ntéléverser un PDF/DOCX"),("method",990,445,360,90,"Choisir la méthode\nd’appariement"),
 ("compute",990,590,390,96,"Calculer et enregistrer\nun résultat explicable"),("view",990,735,370,90,"Consulter le résultat"),
],[("a",175,430,325,430),("d",635,400,820,175,"include"),("d",635,415,795,310,"include"),("d",635,430,810,445,"include"),("d",635,445,795,590,"include"),("d",635,460,805,735,"include")],"05_evaluation_cv.svg")

svg("UC-05 — Analyse approfondie optionnelle",[(120,430,"Recruteur\nauthentifié")],[
 ("result",520,350,360,92,"Consulter un résultat\nd’évaluation"),("request",1000,350,390,92,"Demander une analyse\napprofondie"),
 ("status",1000,590,420,105,"Consulter l’état et le contenu\nde l’analyse approfondie"),
],[("a",175,430,340,350),("d",805,350,700,350,"extend"),("d",1000,396,1000,537,"include")],"06_analyse_approfondie.svg")

svg("UC-06 — Génération du rapport PDF",[(120,430,"Recruteur\nauthentifié")],[
 ("generate",500,430,360,92,"Générer un rapport PDF"),("select",1010,280,390,92,"Sélectionner un résultat\ndéjà calculé"),
 ("download",1010,580,360,92,"Télécharger le document"),
],[("a",175,430,320,430),("d",680,405,815,280,"include"),("d",680,455,830,580,"include")],"07_rapport_pdf.svg")

svg("UC-07 — Classement de plusieurs candidats",[(120,430,"Recruteur\nauthentifié")],[
 ("rank",470,430,350,92,"Classer plusieurs candidats"),("offer",990,190,350,86,"Choisir une offre ouverte"),
 ("upload",990,335,390,96,"Téléverser plusieurs CV\nau format PDF/DOCX"),("display",990,500,420,96,"Afficher le classement\npar score décroissant"),
 ("export",990,680,360,90,"Exporter le classement\nau format CSV"),
],[("a",175,430,295,430),("d",645,400,815,190,"include"),("d",645,420,795,335,"include"),("d",645,445,780,500,"include"),("d",990,635,990,548,"extend")],"08_classement.svg")

svg("UC-08 — Historique et consultation des résultats",[(120,430,"Recruteur\nauthentifié")],[
 ("history",480,430,360,92,"Consulter l’historique"),("list",1010,210,370,92,"Lister ses évaluations"),
 ("filter",1010,430,400,100,"Filtrer par code, offre\nou courriel"),("detail",1010,650,390,94,"Consulter le détail\nd’un résultat"),
],[("a",175,430,300,430),("d",660,400,825,210,"include"),("d",1010,380,1010,256,"extend"),("d",825,650,825,235,"extend")],"09_historique.svg")

print(OUT.resolve())
