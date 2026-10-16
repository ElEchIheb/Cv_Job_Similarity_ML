"""Slides 1 a 12 : titre, sommaire, introduction, contexte, methodologie, acteurs."""
from deck_base import arrow, bd, ic, li, slide

K1 = "I · Contexte général"
K2 = "II · Méthodologie"
K3 = "III · Spécification et analyse des besoins"


def s01():
    body = f"""
<div class="row jb ac" style="margin-top:-6px">
  <div class="row ac" style="gap:18px">
    <div class="logo-pill"><img src="assets/Logo_ISI_Kef.png"></div>
    <div class="logo-pill"><img src="assets/Logo_UJ.png"></div>
  </div>
  <div class="logo-pill" style="padding:14px 30px"><img src="assets/Logo_CyberCloud.png" style="max-height:60px"></div>
</div>
<div class="col" style="gap:0;margin-top:54px">
  <div class="lbl" style="font-size:20px;color:#B9B9D0">Projet de fin d'études · Mastère Professionnel — Applications Web Intelligentes</div>
  <div class="g" style="font:700 66px/1.13 'Space Grotesk';letter-spacing:-.018em;margin-top:24px;max-width:1700px;padding-bottom:8px">
    Conception et développement d'une plateforme intelligente d'aide au recrutement et de mise en correspondance entre CV et offres d'emploi</div>
  <div class="row ac" style="margin-top:34px;gap:16px">
    <span class="bd bd-solid lg" style="font:700 34px 'Space Grotesk';padding:13px 34px">{li('sparkles')} JobTest</span>
    {bd('Moteur hybride', 'v', 'lg')}{bd('Explicable', 'c', 'lg')}{bd('Décision humaine', 'g', 'lg')}
  </div>
</div>
<div style="flex:1"></div>
<div class="grid" style="grid-template-columns:1fr 1.15fr 1.25fr 1.2fr;gap:20px">
  <div class="card" style="padding:22px 26px"><div class="lbl">Présenté par</div><div class="t32 b" style="margin-top:9px">Iheb El Ech</div></div>
  <div class="card" style="padding:22px 26px"><div class="lbl">Encadrant académique</div><div class="t32 b" style="margin-top:9px">Dr. Aymen Louati</div></div>
  <div class="card" style="padding:22px 26px"><div class="lbl">Encadrante professionnelle</div><div class="t32 b" style="margin-top:9px">Dr. Emna Trabelsi</div></div>
  <div class="card" style="padding:22px 26px"><div class="lbl">Organisme d'accueil</div><div class="t32 b" style="margin-top:9px">CyberCloud Solutions</div></div>
</div>
<div class="row jb ac" style="margin-top:24px;font-size:24px;color:#C9C9DC;height:44px">
  <span>Institut Supérieur d'Informatique du Kef — Université de Jendouba</span>
  <span class="row ac" style="gap:14px"><span class="lbl" style="font-size:20px">Soutenu le</span>
    <span style="display:inline-block;width:330px;height:40px;border-bottom:2px dashed rgba(255,255,255,.4)"></span></span>
  <span class="b">Année universitaire 2025–2026</span>
</div>"""
    return slide(1, "", "", body, head=False)


def s02():
    items = [
        ("I", "Contexte", "building-2", "Entreprise · Existant · Problématique"),
        ("II", "Méthodologie", "workflow", "Modèle en cascade"),
        ("III", "Besoins", "list-checks", "Acteurs · BF · BNF · Règles"),
        ("IV", "Conception", "pencil-ruler", "UML · Séquences · Architecture"),
        ("V", "Moteur intelligent", "brain-circuit", "TF–IDF · Embeddings · Compétences"),
        ("VI", "Réalisation & Déploiement", "rocket", "Stack · Démo · Tests · Azure"),
        ("✓", "Conclusion", "flag", "Apports · Limites · Perspectives"),
    ]
    cards = ""
    for i, (num, t, icon, sub) in enumerate(items):
        key = i == 4
        cards += f"""<div class="card {'v glow' if key else ''}" style="display:flex;align-items:center;gap:28px;padding:0 34px;{'grid-column:span 2;' if i == 6 else ''}">
  <div class="g" style="font:700 76px/1 'Space Grotesk';width:120px;flex:none;text-align:center">{num}</div>
  {ic(icon, 'c' if i % 2 else '', 88)}
  <div><div class="ct" style="font-size:40px">{t}</div><div class="mut t28" style="margin-top:8px">{sub}</div></div>
</div>"""
    body = f'<div class="grid gfill" style="grid-template-columns:1fr 1fr;gap:22px;margin:6px 0 14px">{cards}</div>'
    return slide(2, "Plan de la présentation", 'Sommaire', body)


def s03():
    cards = [
        ("files", "", "PDF · DOCX · TXT", "CV hétérogènes", "font-size:42px;white-space:nowrap"),
        ("message-square-text", "c", "Langage libre", "Offres d'emploi", "font-size:46px;white-space:nowrap"),
        ("layers", "", "3", "signaux fusionnés", "font-size:150px"),
        ("user-check", "g", "0", "décision automatisée", "font-size:150px"),
    ]
    h = ""
    for icon, c, big, lab, st in cards:
        h += f"""<div class="card" style="padding:36px 34px;display:flex;flex-direction:column;gap:22px">
  {ic(icon, c, 84)}<div class="big g" style="{st};padding-bottom:8px;margin-top:auto">{big}</div><div class="t34 sb" style="color:#DADAE8">{lab}</div></div>"""
    body = f"""<div class="grid fill" style="grid-template-columns:repeat(4,1fr);margin-top:14px">{h}</div>
<div class="card v glow" style="text-align:center;padding:34px;margin:28px 0 14px">
  <span style="font:700 48px 'Space Grotesk'">Assister le recruteur, <span class="g">pas le remplacer.</span></span></div>"""
    return slide(3, "Introduction", '« Trier des CV coûte du temps. <span class="g">Décider reste humain.</span> »', body)


def s04():
    acts = [
        ("compass", "", "Conseil & transformation numérique"),
        ("server", "c", "Infrastructure : serveurs, stockage, postes"),
        ("radar", "", "Sécurité Internet, network forensics"),
        ("shield-check", "c", "Cybersécurité, XDR, Cloud, DevOps"),
    ]
    tiles = "".join(f'<div class="card" style="display:flex;align-items:center;gap:24px;padding:0 30px">{ic(i, c, 84)}<div class="t30 sb" style="line-height:1.25">{t}</div></div>' for i, c, t in acts)
    rows = [("user", "PFE individuel"), ("calendar-range", "Mars → août 2026"), ("laptop", "Mode distant / hybride"), ("lightbulb", "Sujet proposé par l'entreprise")]
    cad = "".join(f'<div class="row ac" style="gap:22px;flex:1;border-top:1px solid rgba(255,255,255,.09)">{ic(i, "c", 68)}<span class="t32 sb">{t}</span></div>' for i, t in rows)
    body = f"""<div class="row fill" style="gap:30px;margin:8px 0 14px">
  <div class="col f1" style="gap:24px">
    <div class="row ac" style="gap:30px">
      <div class="logo-pill" style="height:150px;width:360px;padding:20px 30px"><img src="assets/Logo_CyberCloud.png" style="max-height:100px"></div>
      <div class="col" style="gap:18px">
        <div class="b" style="font:700 38px 'Space Grotesk'">Services & conseil en informatique</div>
        <div class="row wrap" style="gap:12px">{bd('Fondée en 2017', 'v', icon='calendar')}{bd('Grand Tunis', 'c', icon='map-pin')}{bd('2–10 personnes', 'n', icon='users')}</div>
      </div>
    </div>
    <div class="lbl" style="margin-top:8px">Activités & domaines d'expertise</div>
    <div class="grid gfill" style="grid-template-columns:1fr 1fr;gap:20px">{tiles}</div>
  </div>
  <div class="card v" style="width:610px;padding:32px 36px;display:flex;flex-direction:column">
    <div class="row ac" style="gap:18px;margin-bottom:22px">{ic('graduation-cap', '', 72)}<div class="ct" style="font-size:40px">Cadre du stage</div></div>
    {cad}
  </div>
</div>"""
    return slide(4, K1, 'Organisme d\'accueil : <span class="g">CyberCloud Solutions</span>', body)


def s05():
    steps = ["Lire l'offre", "Définir critères", "Ouvrir les CV", "Repérer compétences", "Garder / écarter"]
    tl = ""
    for i, s in enumerate(steps):
        tl += f'<div class="card" style="padding:26px 10px;text-align:center;flex:1;min-height:170px;display:flex;flex-direction:column;justify-content:center"><div class="mono vi t26 b">{i+1:02d}</div><div class="t28 sb" style="margin-top:12px;line-height:1.2">{s}</div></div>'
        if i < len(steps) - 1:
            tl += arrow(34)
    body = f"""<div class="row fill" style="gap:28px;margin:8px 0 14px">
  <div class="card" style="flex:1.85;padding:36px 34px;display:flex;flex-direction:column">
    <div class="row ac" style="gap:18px">{ic('hand', '', 68)}<div class="ct" style="font-size:38px"><span class="vi">①</span> Processus manuel</div></div>
    <div style="flex:1"></div>
    <div class="row ac" style="gap:8px">{tl}</div>
    <div class="row ac jc" style="margin:34px 0 28px">{arrow(70, '#F87171', vertical=True)}</div>
    <div class="row jc wrap" style="gap:16px">{bd('Coûteux à répéter', 'r', 'lg', 'timer')}{bd('Peu traçable', 'r', 'lg', 'eye-off')}{bd('Formats disparates', 'r', 'lg', 'files')}</div>
    <div style="flex:1"></div>
  </div>
  <div class="card" style="flex:1;padding:36px 34px;display:flex;flex-direction:column">
    <div class="row ac" style="gap:18px">{ic('search', 'c', 68)}<div class="ct" style="font-size:36px;line-height:1.15"><span class="cy">②</span> ATS & approches lexicales</div></div>
    <div style="flex:1"></div>
    <div class="col" style="gap:16px;align-items:flex-start">
      {bd('Recherche par mots-clés', 'c', 'lg', 'text-search')}{bd('Filtres & champs structurés', 'c', 'lg', 'list-filter')}
    </div>
    <div class="row ac" style="margin:30px 0 26px;padding-left:60px">{arrow(70, '#F87171', vertical=True)}</div>
    <div class="col" style="gap:16px;align-items:flex-start">
      {bd('Paraphrases ignorées', 'r', 'lg', 'x')}{bd('CV multilingues', 'r', 'lg', 'languages')}{bd('Vocabulaire non identique', 'r', 'lg', 'unlink')}
    </div>
    <div style="flex:1"></div>
  </div>
</div>"""
    return slide(5, K1, "Étude de l'existant : <span class=\"g\">deux approches, deux limites</span>", body)


def s06():
    rows = [
        ("Correspondance CV/offre", "Recherche IA + recommandations", "Tri <i>best match</i>", "Talent Matching pondéré", "Hybride : lexical + sémantique + compétences"),
        ("Éléments explicatifs", "Synthèse IA, granularité non doc.", "Score IA non décomposé", "Scorecards", "Sous-scores + écarts + recommandations"),
        ("Analyse des écarts de compétences", "Non documenté", "Non documenté", "Non documenté", "Trouvées / manquantes / critiques"),
        ("Classement & export", "Export non documenté", "Export non documenté", "Rapport XLS", "Multi-CV + historique + rapport PDF"),
        ("Contrôle & données", "Non documenté", "Doc. sécurité générique", "Non documenté", "Cloisonnement par recruteur, VM Azure"),
    ]
    tr = ""
    for r in rows:
        tds = "".join(f'<td style="{"color:#8687A0" if "on documenté" in c else ""}">{c}</td>' for c in r[1:4])
        tr += f'<tr><td class="sb" style="color:#fff">{r[0]}</td>{tds}<td class="hl sb">{r[4]}</td></tr>'
    body = f"""<table class="t" style="margin-top:8px;font-size:27px;flex:1">
<colgroup><col style="width:19%"><col style="width:19%"><col style="width:17%"><col style="width:17%"><col style="width:28%"></colgroup>
<tr style="height:76px"><th>Critère</th><th>LinkedIn Recruiter</th><th>Workable</th><th>Greenhouse</th><th class="hl" style="font-size:25px">{li('sparkles')} JobTest</th></tr>{tr}</table>
<div class="mut t22" style="font-style:italic;margin:22px 0 12px">« non documenté » = aucune preuve dans les pages officielles consultées (13/09/2026)</div>"""
    return slide(6, K1, 'Benchmark des solutions : <span class="g">où se situe JobTest</span>', body)


def s07():
    svg = """<svg width="980" height="740" viewBox="0 0 1000 720" xmlns="http://www.w3.org/2000/svg" style="display:block;font-family:'Space Grotesk',sans-serif">
<defs><radialGradient id="cg" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#EF4444" stop-opacity=".55"/><stop offset="1" stop-color="#EF4444" stop-opacity=".0"/></radialGradient></defs>
<circle cx="500" cy="240" r="225" fill="rgba(139,92,246,.16)" stroke="#8B5CF6" stroke-width="2.5"/>
<circle cx="345" cy="475" r="225" fill="rgba(34,211,238,.11)" stroke="#22D3EE" stroke-width="2.5"/>
<circle cx="655" cy="475" r="225" fill="rgba(167,139,250,.11)" stroke="#A78BFA" stroke-width="2.5"/>
<circle cx="500" cy="400" r="130" fill="url(#cg)"/>
<text x="500" y="118" text-anchor="middle" fill="#F4F4FA" font-size="36" font-weight="700">Analyse du texte</text>
<text x="235" y="555" text-anchor="middle" fill="#F4F4FA" font-size="36" font-weight="700">Règle de</text>
<text x="235" y="598" text-anchor="middle" fill="#F4F4FA" font-size="36" font-weight="700">décision</text>
<text x="765" y="555" text-anchor="middle" fill="#F4F4FA" font-size="36" font-weight="700">Explication</text>
<text x="765" y="598" text-anchor="middle" fill="#F4F4FA" font-size="36" font-weight="700">fournie</text>
<rect x="335" y="352" width="330" height="104" rx="52" fill="#1A0F16" stroke="#EF4444" stroke-width="3"/>
<text x="500" y="395" text-anchor="middle" fill="#FCA5A5" font-size="29" font-weight="800" letter-spacing="1.5">COHÉRENCE</text>
<text x="500" y="433" text-anchor="middle" fill="#FCA5A5" font-size="29" font-weight="800" letter-spacing="1.5">MANQUANTE</text>
</svg>"""
    pts = [("scan-text", "", "Analyse", "Le texte est comparé"), ("scale", "c", "Décision", "Une règle tranche"), ("message-circle-question", "", "Explication", "Une justification s'affiche")]
    side = "".join(f'<div class="card" style="display:flex;gap:24px;align-items:center;padding:26px 30px">{ic(i, c, 80)}<div><div class="ct" style="font-size:36px">{t}</div><div class="mut t28" style="margin-top:6px">{s}</div></div></div>' for i, c, t, s in pts)
    body = f"""<div class="row ac fill" style="gap:50px">
  <div style="flex:none;margin-top:-10px">{svg}</div>
  <div class="col f1" style="gap:20px">
    <div class="lbl">Trois briques souvent séparées</div>{side}
    <div class="card r" style="padding:28px 30px;margin-top:8px"><div class="t32 b rd">{li('triangle-alert')} &nbsp;Le manque : leur cohérence</div></div>
  </div>
</div>"""
    return slide(7, K1, "Critique de l'existant : <span class=\"g\">le vrai manque</span>", body)


def s08():
    body = f"""<div style="flex:.7"></div>
<div class="card v glow" style="padding:66px 80px;text-align:center;border-width:2px">
  <div style="font:700 28px 'JetBrains Mono';letter-spacing:.22em;color:#22D3EE">PROBLÉMATIQUE</div>
  <div style="font:700 58px/1.3 'Space Grotesk';margin-top:30px;letter-spacing:-.01em">
    Comment fournir au recruteur une évaluation CV/offre à la fois
    <span class="g">hybride</span>, <span class="g">explicable</span>, <span class="g">reproductible</span> et <span class="g">persistante</span>
    — sans lui déléguer la décision d'embauche&nbsp;?</div>
</div>
<div class="row jc wrap" style="gap:20px;margin-top:50px">
  {bd('Contenu hétérogène', 'v', 'lg', 'files')}{bd('Vérifiable par ses composantes', 'c', 'lg', 'list-checks')}{bd('Reproductible', 'v', 'lg', 'repeat')}{bd('Génératif encadré', 'c', 'lg', 'shield-check')}
</div><div style="flex:1"></div>"""
    return slide(8, K1, "", body, head=False)


def s09():
    def mini(icon, t, s, c=""):
        return f'<div class="card" style="display:flex;align-items:center;gap:22px;padding:0 28px;flex:1">{ic(icon, c, 76)}<div><div class="t32 b">{t}</div><div class="mut t24" style="margin-top:5px">{s}</div></div></div>'
    outs = [("gauge", "Score global %", "0 → 100", "c"), ("badge-check", "Verdict", "HIRE · CONSIDER · REJECT", "g"),
            ("list-checks", "Compétences", "trouvées / manquantes", ""), ("lightbulb", "Recommandations", "actions prioritaires", "o")]
    band = "".join(bd(t, "n", "lg", icon=i) for i, t in [("history", "Historique"), ("trophy", "Classement multi-CV"), ("file-down", "Rapport PDF"), ("git-compare-arrows", "AI Insights"), ("activity", "AI Quality Center")])
    body = f"""<div class="row fill" style="gap:22px;margin-top:8px;align-items:stretch">
  <div class="col" style="width:440px;gap:22px;justify-content:center">
    <div style="height:150px;display:flex">{mini('file-user', 'CV', 'texte · PDF · DOCX')}</div>
    <div style="height:150px;display:flex">{mini('briefcase', "Offre d'emploi", 'description + compétences', 'c')}</div>
  </div>
  <div class="row ac">{arrow(70)}</div>
  <div class="card v glow" style="width:480px;padding:30px;text-align:center;border-width:2px;display:flex;flex-direction:column;justify-content:center">
    <div style="display:flex;justify-content:center">{ic('brain-circuit', '', 104)}</div>
    <div style="font:700 46px 'Space Grotesk';margin-top:22px" class="g">MOTEUR HYBRIDE</div>
    <div class="col" style="gap:12px;margin-top:26px;align-items:center">{bd('TF–IDF', 'v', 'lg')}{bd('Embeddings', 'c', 'lg')}{bd('Compétences', 'v', 'lg')}</div>
  </div>
  <div class="row ac">{arrow(70)}</div>
  <div class="col f1" style="gap:16px">{''.join(mini(i, t, s, c) for i, t, s, c in outs)}</div>
</div>
<div class="row jc wrap" style="gap:14px;margin:28px 0 14px">{band}</div>"""
    return slide(9, K1, 'Solution proposée : <span class="g">JobTest</span>', body)


def s10():
    items = [("route", "Workflow recruteur"), ("file-up", "CV texte ou fichier"), ("layers", "3 signaux fusionnés"), ("scale", "Décision cohérente"),
             ("search-check", "Résultat explicable"), ("database", "Historique persistant"), ("file-chart-column", "Rapport + classement"), ("cloud-upload", "Déploiement démontrable")]
    h = ""
    for i, (icon, t) in enumerate(items):
        h += f"""<div class="card" style="padding:24px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;text-align:center">
  {ic(icon, 'c' if (i + i // 4) % 2 else '', 112)}<div style="font:700 35px/1.2 'Space Grotesk'">{t}</div>
  <div class="mono dim t22">OBJ-{i+1:02d}</div></div>"""
    body = f'<div class="grid gfill" style="grid-template-columns:repeat(4,1fr);gap:24px;margin:8px 0 14px">{h}</div>'
    return slide(10, K1, 'Objectifs du projet : <span class="g">8 engagements</span>', body)


def s11():
    steps = ["Besoins", "Analyse", "Conception", "Implémentation", "Validation & correction", "Déploiement"]
    dx, dy, bw, bh = 150, 122, 440, 92
    boxes, arrows = "", ""
    for i, s in enumerate(steps):
        x, y = i * dx, i * dy
        hot = i == 4
        boxes += (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{bw}px;height:{bh}px;border-radius:20px;display:flex;align-items:center;gap:20px;padding:0 26px;'
                  f'background:{"rgba(139,92,246,.24)" if hot else "rgba(255,255,255,.06)"};border:1.5px solid {"#8B5CF6" if hot else "rgba(255,255,255,.16)"}">'
                  f'<span class="g" style="font:700 46px \'Space Grotesk\'">{i+1}</span><span style="font:600 30px Inter">{s}</span></div>')
        if i < len(steps) - 1:
            ax = x + 70
            arrows += f'<path d="M{ax},{y+bh+4} V{y+dy+bh/2} H{x+dx-12}" fill="none" stroke="#22D3EE" stroke-width="3.5" marker-end="url(#wa)"/>'
    back = ""
    for i in (4, 3):  # validation -> implementation, implementation -> conception
        x, y = i * dx, i * dy
        bx = x + bw - 70
        back += f'<path d="M{bx},{y-4} V{y-dy+bh/2} H{x-dx+bw+14}" fill="none" stroke="#F59E0B" stroke-width="3.5" stroke-dasharray="9 8" marker-end="url(#wb)"/>'
    W, H = 5 * dx + bw + 10, 5 * dy + bh + 10
    svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="position:absolute;left:0;top:0" xmlns="http://www.w3.org/2000/svg">'
           '<defs><marker id="wa" markerWidth="12" markerHeight="12" refX="9" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11 Z" fill="#22D3EE"/></marker>'
           '<marker id="wb" markerWidth="12" markerHeight="12" refX="9" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11 Z" fill="#F59E0B"/></marker></defs>'
           f'{arrows}{back}</svg>')
    just = [("package-check", "Livrables stabilisés"), ("book-open", "Fil de lecture clair"), ("refresh-ccw", "Boucles de correction assumées")]
    jc = "".join(f'<div class="card" style="display:flex;align-items:center;gap:22px;padding:26px 28px">{ic(i, "c", 72)}<div class="t30 b" style="line-height:1.2">{t}</div></div>' for i, t in just)
    body = f"""<div class="row fill" style="gap:34px;margin-top:10px">
  <div style="position:relative;width:{W}px;height:{H}px;flex:none">{svg}{boxes}
    <div style="position:absolute;left:{4*dx+bw+30}px;top:{2*dy+20}px;display:none"></div></div>
  <div class="col f1" style="gap:20px">
    <div class="lbl">Pourquoi ce modèle</div>{jc}
    <div class="row ac" style="gap:14px;margin-top:10px"><svg width="70" height="14"><line x1="0" y1="7" x2="70" y2="7" stroke="#F59E0B" stroke-width="3.5" stroke-dasharray="9 8"/></svg><span class="t24 or sb">retours de correction</span></div>
    <div class="mut t22" style="font-style:italic">Royce (1970) : cascade avec retours contrôlés</div>
  </div>
</div>"""
    return slide(11, K2, 'Modèle en cascade <span class="g">avec retours de correction</span>', body)


def s12():
    def actor(icon, t, s, c="", tag=""):
        return f"""<div class="card {c}" style="padding:28px 28px;display:flex;gap:22px;align-items:center">
  {ic(icon, 'c' if c == 'c' else '', 88)}<div><div class="ct" style="font-size:36px">{t}</div><div class="mut t26" style="margin-top:4px">{s}</div>{tag}</div></div>"""
    uc = lambda t, c="n": f'<span class="bd bd-{c} lg">{t}</span>'
    body = f"""<div class="row fill" style="gap:20px;margin:8px 0 14px;align-items:stretch">
  <div class="col" style="width:440px;gap:0;justify-content:space-around">
    {actor('user', 'Visiteur', 'non authentifié')}
    {actor('user-check', 'Recruteur', 'authentifié', 'v', '<div style="margin-top:12px">' + bd('acteur principal', 'v', 'sm') + '</div>')}
  </div>
  <div class="col" style="gap:0;justify-content:space-around">{arrow(60)}{arrow(60, '#A78BFA')}</div>
  <div class="f1" style="border:2.5px solid rgba(34,211,238,.6);border-radius:28px;padding:30px 32px;background:rgba(34,211,238,.035);display:flex;flex-direction:column;gap:20px">
    <div class="mono cy b t26" style="letter-spacing:.1em">SYSTÈME JOBTEST</div>
    <div class="row wrap" style="gap:14px">{uc('Créer un compte')}{uc('Se connecter')}</div>
    <div class="hr"></div>
    <div class="lbl">Fonctions métier</div>
    <div class="row wrap" style="gap:14px">{uc('Offres', 'v')}{uc('Candidats', 'v')}{uc('Évaluation', 'v')}{uc('Analyse approfondie', 'v')}{uc('Rapport PDF', 'v')}{uc('Classement', 'v')}{uc('Historique', 'v')}{uc('Seuils', 'v')}</div>
    <div style="flex:1"></div>
    <div class="card o" style="padding:22px 26px;display:flex;align-items:center;gap:20px">
      {ic('id-card', 'o', 72)}<div><div class="t32 b">Candidat</div><div class="t26 or">entité métier, jamais utilisateur</div></div></div>
  </div>
  <div class="col" style="width:350px;justify-content:flex-end">
    <div class="card" style="padding:26px 26px;border-style:dashed">
      {ic('wrench', 'c', 68)}<div class="ct" style="font-size:31px;margin-top:16px">Maintenance / QA</div>
      <div class="mut t24" style="margin-top:10px">partie prenante technique</div>
      <div style="margin-top:14px">{bd('hors parcours', 'n', 'sm')}</div></div>
  </div>
</div>"""
    return slide(12, K3, 'Acteurs et <span class="g">parties prenantes</span>', body)


SLIDES = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12]
