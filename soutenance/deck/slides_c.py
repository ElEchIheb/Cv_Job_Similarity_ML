"""Slides 25 a 38 : moteur (2/2), realisation, tests, securite, deploiement, conclusion."""
from pathlib import Path

from deck_base import arrow, bars_svg, bd, ic, li, slide

K5 = "V · Moteur intelligent"
K6 = "VI · Réalisation & déploiement"
KC = "Conclusion"
URL = "http://20.51.167.202/"
SHOTS = Path(__file__).resolve().parent / "out" / "assets" / "shots"


def s25():
    outs = "".join(bd(t, "o", "sm") for t in ["trajectoire", "alertes", "justification", "recommandations", "questions d'entretien"])
    guards = [
        ("braces", "Format imposé", ["Aucun champ de score", "Réponse non conforme = rejetée"]),
        ("scale", "Contrôle de cohérence", ["Trop favorable sur un <code>REJECT</code>", "Relance, puis <code>inconsistent</code>"]),
        ("syringe", "Anti-injection de prompt", ["Score calculé <b>avant</b> le modèle", "Injection ⇒ commentaire seulement"]),
    ]
    gh = ""
    for icon, t, pts in guards:
        gh += f"""<div class="card" style="padding:26px 28px;display:flex;flex-direction:column;gap:14px">
  <div class="row ac" style="gap:18px">{ic(icon, 'c', 64)}<div class="ct" style="font-size:32px">{t}</div></div>
  <ul class="pl" style="gap:16px;margin-top:10px">{''.join(f'<li style="font-size:29px">{p}</li>' for p in pts)}</ul></div>"""
    wall = """<svg width="92" height="270" viewBox="0 0 92 270" xmlns="http://www.w3.org/2000/svg">
<rect x="26" y="0" width="40" height="270" rx="8" fill="rgba(239,68,68,.14)" stroke="#EF4444" stroke-width="2.5"/>
<g stroke="#EF4444" stroke-width="2" opacity=".75"><line x1="26" y1="45" x2="66" y2="45"/><line x1="26" y1="90" x2="66" y2="90"/><line x1="26" y1="180" x2="66" y2="180"/><line x1="26" y1="225" x2="66" y2="225"/>
<line x1="46" y1="0" x2="46" y2="45"/><line x1="46" y1="180" x2="46" y2="225"/></g>
<circle cx="46" cy="135" r="34" fill="#190D12" stroke="#EF4444" stroke-width="2.5"/>
<g transform="translate(31,119)" fill="none" stroke="#FCA5A5" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="14" width="24" height="16" rx="3"/><path d="M8 14V9a7 7 0 0 1 14 0v5"/></g></svg>"""
    states = "".join(bd(s, c, "sm") for s, c in [("ok", "g"), ("disabled", "n"), ("unavailable", "n"), ("error", "r"), ("inconsistent", "o")])
    body = f"""<div class="row" style="gap:14px;margin-top:6px;align-items:stretch">
  <div class="card c" style="flex:1;padding:26px 28px;display:flex;flex-direction:column;gap:16px;justify-content:center">
    <div class="row ac" style="gap:18px">{ic('brain-circuit', 'c', 72)}<div><div class="lbl cy">Layer 1</div><div class="ct" style="font-size:34px">Déterministe</div></div></div>
    <div class="row ac" style="gap:14px">{arrow(46)}<span class="bd bd-solid lg" style="font-weight:800">SCORE + VERDICT</span></div>
  </div>
  <div class="col ac jc" style="gap:6px">{wall}<span class="mono rd b" style="font-size:17px;letter-spacing:.08em">RG-06</span></div>
  <div class="card o" style="flex:1.25;padding:26px 28px;display:flex;flex-direction:column;gap:16px;justify-content:center">
    <div class="row ac" style="gap:18px">{ic('sparkles', 'o', 72)}<div><div class="lbl or">Layer 2 · Ollama</div><div class="ct" style="font-size:34px"><code style="font-size:.9em;color:#FCD34D">qwen2.5:1.5b</code></div></div></div>
    <div class="row wrap" style="gap:9px">{outs}</div>
  </div>
</div>
<div class="lbl" style="margin:20px 0 12px">3 garde-fous</div>
<div class="grid gfill" style="grid-template-columns:repeat(3,1fr);gap:18px">{gh}</div>
<div class="row ac jc" style="gap:12px;margin:18px 0 12px"><span class="lbl">États possibles</span>{states}</div>"""
    return slide(25, K5, 'Couche 2 : <span class="g">analyse locale encadrée</span>', body)


def s26():
    why = [("search-x", "Aucun corpus réel accessible"), ("scale", "Contrainte juridique & éthique"), ("scan-text", "Qualité d'extraction maîtrisée"),
           ("circle-help", "Pas de vérité terrain réelle"), ("repeat", "Reproductible (graine fixée)")]
    wh = "".join(f'<div class="card" style="display:flex;align-items:center;gap:20px;padding:0 24px">{ic(i, "sm" + (" c" if k % 2 else ""))}<div class="t28 sb">{t}</div></div>' for k, (i, t) in enumerate(why))
    deg = "".join(bd(t, "n", "sm") for t in ["abréviations", "fautes de frappe", "technologies obsolètes", "paires contradictoires"])
    body = f"""<div class="row fill" style="gap:26px;margin:8px 0 14px">
  <div class="card" style="flex:1.25;padding:30px 32px;display:flex;flex-direction:column;gap:18px">
    <div class="row ac jb"><code style="font-size:27px">cv_job_dataset.csv</code>{bd('graine 42', 'v', '', 'dices')}</div>
    <div class="row" style="align-items:baseline;gap:18px"><span class="big g" style="font-size:132px;padding-bottom:6px">12 000</span><span class="t36 sb">paires CV–offre</span></div>
    <div class="row wrap" style="gap:12px">{bd('20 domaines métier', 'c', '', 'briefcase')}{bd('FR + EN', 'c', '', 'languages')}</div>
    <div class="row wrap" style="gap:10px">{deg}</div>
    <div style="flex:1"></div>
    <div class="lbl">Partition stratifiée</div>
    <div style="display:flex;height:92px;border-radius:18px;overflow:hidden;border:1.5px solid rgba(255,255,255,.14);font:700 30px 'Space Grotesk'">
      <div style="flex:70;background:rgba(139,92,246,.36);display:flex;align-items:center;justify-content:center;gap:12px">8 400 <span class="t22 sb" style="font-family:Inter;color:#DDD6FE">train</span></div>
      <div style="flex:15;background:rgba(34,211,238,.28);display:flex;flex-direction:column;align-items:center;justify-content:center">1 800 <span class="t18 sb" style="font-family:Inter;color:#A5F3FC">validation</span></div>
      <div style="flex:15;background:rgba(16,185,129,.28);display:flex;flex-direction:column;align-items:center;justify-content:center">1 800 <span class="t18 sb" style="font-family:Inter;color:#A7F3D0">test</span></div>
    </div>
  </div>
  <div class="col f1" style="gap:14px">
    <div class="ct" style="font-size:33px">Pourquoi un corpus <span class="g">synthétique</span></div>
    <div class="grid gfill" style="gap:14px">{wh}</div>
  </div>
</div>"""
    return slide(26, K5, 'Protocole expérimental : <span class="g">données & partition</span>', body)


def s27():
    rows = [("TF–IDF", "0,04", "0,93", "0,93", "0,97", "0,95", "0,98", False, True),
            ("Embeddings", "0,54", "0,78", "0,81", "0,89", "0,85", "0,81", False, False),
            ("Compétences", "0,00", "0,89", "0,89", "0,97", "0,93", "0,95", False, False),
            ("Hybride", "0,26", "0,91", "0,94", "0,93", "0,93", "0,96", True, True)]
    tr = ""
    for m, s, a, p, r, f1, auc, hl, bold in rows:
        st = ' style="background:rgba(139,92,246,.2)"' if hl else ""
        b = "font-weight:800;color:#fff" if bold else ""
        tr += (f'<tr{st}><td class="sb" style="color:#fff">{m}</td><td class="num mono">{s}</td><td class="num mono">{a}</td><td class="num mono">{p}</td>'
               f'<td class="num mono">{r}</td><td class="num mono" style="{b}">{f1}</td><td class="num mono" style="{b}">{auc}</td></tr>')
    chart = bars_svg([("TF–IDF", .95, .98, False), ("Embeddings", .85, .81, False), ("Compétences", .93, .95, False), ("Hybride", .93, .96, True)], w=740, h=470, bh=36, gap=106, fs=23)
    body = f"""<div class="row fill" style="gap:26px;margin-top:8px">
  <div class="col" style="flex:1.22;gap:18px">
    <table class="t" style="font-size:29px;flex:1">
      <tr><th>Méthode</th><th>Seuil</th><th>Exact.</th><th>Préc.</th><th>Rappel</th><th>F1</th><th>AUC-ROC</th></tr>{tr}</table>
    <div class="row" style="gap:16px">
      <div class="card gr" style="flex:1;padding:20px 24px"><div class="lbl gn">Fusion</div><div class="row" style="align-items:baseline;gap:10px;margin-top:6px"><span class="big" style="font-size:58px;color:#6EE7B7">55,85</span><span class="t24 sb">ms / paire</span></div></div>
      <div class="card" style="flex:1;padding:20px 24px"><div class="lbl">Embeddings seuls</div><div class="row" style="align-items:baseline;gap:10px;margin-top:6px"><span class="big" style="font-size:58px;color:#D7D7E6">921,60</span><span class="t24 sb">ms / paire</span></div></div>
    </div>
  </div>
  <div class="card f1" style="padding:24px 24px 16px;display:flex;flex-direction:column;gap:10px">
    <div class="row ac jb"><div class="ct" style="font-size:28px">1 800 paires de test</div>
      <div class="row ac" style="gap:16px"><span class="row ac t20 sb" style="gap:8px"><i style="width:22px;height:12px;border-radius:4px;background:#8B5CF6;display:inline-block"></i>F1</span>
      <span class="row ac t20 sb" style="gap:8px"><i style="width:22px;height:12px;border-radius:4px;background:#22D3EE;display:inline-block"></i>AUC-ROC</span></div></div>
    <div style="margin:auto 0">{chart}</div>
  </div>
</div>
<div class="mut t22" style="font-style:italic;margin:18px 0 12px">{li('info')} Le générateur partage un vocabulaire contrôlé → avantage mécanique du lexical</div>"""
    return slide(27, K5, 'Résultats comparatifs : <span class="g">F1 0,93 · AUC 0,96</span> pour l\'hybride', body)


def s28():
    def ba(before, after, lab_b, lab_a):
        return f"""<div class="row ac" style="gap:16px">
  <div class="card r" style="flex:1;padding:16px 18px;text-align:center"><div class="lbl rd">{lab_b}</div><div class="mono b" style="font-size:31px;margin-top:8px;color:#FCA5A5">{before}</div></div>
  {arrow(44, '#34D399')}
  <div class="card gr" style="flex:1;padding:16px 18px;text-align:center"><div class="lbl gn">{lab_a}</div><div class="mono b" style="font-size:31px;margin-top:8px;color:#6EE7B7">{after}</div></div></div>"""
    body = f"""<div class="row fill" style="gap:24px;margin:8px 0 14px">
  <div class="card" style="flex:1.12;padding:28px 28px;display:flex;flex-direction:column;gap:18px">
    <div class="row ac" style="gap:16px">{ic('sliders-horizontal', 'sm')}<div class="ct" style="font-size:32px"><span class="vi">①</span> Poids du moteur</div></div>
    {ba('0,9 / 0,0 / 0,1', '0,2 / 0,4 / 0,4', 'hérité · grid search', 'rétabli · documenté')}
    <div class="lbl" style="margin-top:6px">Même profil, compétences identiques</div>
    <table class="t" style="font-size:25px">
      <tr><th>Poids</th><th>CV calqué</th><th>CV reformulé</th><th>Écart</th></tr>
      <tr><td class="mono">0,9/0,0/0,1</td><td class="mono">99,2 %</td><td class="mono">73,6 %</td><td>{bd('25,6 pts · faille', 'r', 'sm')}</td></tr>
      <tr><td class="mono">0,2/0,4/0,4</td><td class="mono">94,4 %</td><td class="mono">84,8 %</td><td>{bd('9,6 pts · sain', 'g', 'sm')}</td></tr>
    </table>
    <div style="flex:1"></div>
    <div class="t24 mut" style="font-style:italic">Recopier l'annonce ne rapporte plus 25 points.</div>
  </div>
  <div class="card" style="flex:1;padding:28px 28px;display:flex;flex-direction:column;gap:18px">
    <div class="row ac" style="gap:16px">{ic('flask-conical', 'sm c')}<div class="ct" style="font-size:32px"><span class="cy">②</span> Protocole d'évaluation</div></div>
    {ba('0,60 partout', 'calibré / méthode', 'seuil unique', 'sur la validation')}
    <div class="lbl" style="margin-top:6px">Exemple : TF–IDF</div>
    <div class="row ac" style="gap:18px">
      <div style="flex:1;text-align:center"><div class="big rd" style="font-size:74px">0,000</div><div class="t22 mut" style="margin-top:6px">F1 avant</div></div>
      {arrow(54, '#34D399')}
      <div style="flex:1;text-align:center"><div class="big gn" style="font-size:74px">0,950</div><div class="t22 mut" style="margin-top:6px">F1 après</div></div>
    </div>
    <div class="row jc">{bd('AUC inchangée : 0,979', 'c', '', 'equal')}</div>
    <div style="flex:1"></div>
    <div class="card o" style="padding:14px 18px;text-align:center"><span class="t24 sb or">{li('bell-ring')} Alerte auto si AUC ≥ 0,80 et F1 ≤ 0,05</span></div>
  </div>
</div>"""
    return slide(28, K5, 'Honnêteté scientifique : <span class="g">deux corrections assumées</span>', body)


def _logo(slug, color):
    return f'<img src="https://cdn.simpleicons.org/{slug}/{color}" style="width:26px;height:26px;display:block" onerror="this.remove()">'


def s29():
    def chip(t, slug=None, color="white"):
        return f'<span class="bd bd-n" style="gap:11px;font-size:23px;padding:9px 18px">{_logo(slug, color) if slug else ""}{t}</span>'
    rows = [
        ("monitor", "Frontend", "", [("Next.js 14.2.35 · App Router", "nextdotjs", "white"), ("React 18", "react", "61DAFB"), ("TypeScript", "typescript", "3178C6")]),
        ("palette", "Style & animation", "c", [("Tailwind CSS", "tailwindcss", "06B6D4"), ("Framer Motion", "framer", "white"), ("Three.js / react-three-fiber", "threedotjs", "white")]),
        ("server", "Backend", "", [("Python", "python", "FFD43B"), ("FastAPI", "fastapi", "009688"), ("Uvicorn (ASGI)", None, ""), ("Pydantic", "pydantic", "E92063")]),
        ("database", "Persistance", "c", [("SQLAlchemy", "sqlalchemy", "D71F00"), ("SQLite (dev)", "sqlite", "74B8E4"), ("PostgreSQL 16", "postgresql", "6FA8DC")]),
        ("brain-circuit", "IA", "", [("scikit-learn", "scikitlearn", "F7931E"), ("Sentence-Transformers", None, ""), ("spaCy", "spacy", "09A3D5"), ("Ollama · qwen2.5:1.5b", "ollama", "white")]),
        ("file-text", "Documents", "c", [("pdfplumber + PyPDF2", None, ""), ("python-docx", None, ""), ("ReportLab", None, "")]),
        ("cloud", "Infra", "", [("Docker Compose", "docker", "2496ED"), ("Nginx", "nginx", "009639"), ("Microsoft Azure", None, "")]),
    ]
    h = ""
    for icon, lab, c, chips in rows:
        h += f"""<div class="card" style="padding:0 26px;display:flex;align-items:center;gap:22px">
  {ic(icon, 'sm ' + c)}<div class="ct" style="font-size:29px;width:300px;flex:none">{lab}</div>
  <div class="row wrap" style="gap:12px">{''.join(chip(*c3) for c3 in chips)}</div></div>"""
    body = f'<div class="grid gfill" style="gap:13px;margin:6px 0 14px">{h}</div>'
    return slide(29, K6, 'Stack technique <span class="g">complète</span>', body)


def s30():
    items = [("web/", "Pages Next.js, composants, client API", "monitor"), ("src/api/", "FastAPI, routeurs auth + ui", "zap"),
             ("src/matching/", "Évaluation & persistance", "git-merge"), ("src/models/", "TF-IDF, embeddings, compétences", "layers"),
             ("src/fusion/", "Score hybride", "combine"), ("src/decisioning/", "Règles de verdict", "scale"),
             ("src/explainability/", "Explications", "search-check"), ("src/ai/", "Prompts Ollama", "sparkles"),
             ("src/parsing/", "Extraction PDF / DOCX", "file-scan"), ("src/reporting/", "ReportLab", "file-down"),
             ("deploy/nginx/", "Relais HTTP", "shield-check")]

    def rowh(p, d, icon):
        return f"""<div class="card" style="padding:0 24px;display:flex;align-items:center;gap:20px">
  <span style="font-size:40px;color:#FBBF24;display:flex">{li('folder')}</span><code class="b" style="font-size:27px;width:330px;flex:none">{p}</code>
  <span class="t26" style="color:#DDDDEA">{d}</span><span style="margin-left:auto;font-size:30px;color:#A78BFA;display:flex">{li(icon)}</span></div>"""
    left = "".join(rowh(*i) for i in items[:6])
    right = "".join(rowh(*i) for i in items[6:])
    right += f'<div class="card v" style="padding:0 24px;display:flex;align-items:center;gap:18px">{ic("workflow", "sm")}<span class="t26 sb">Une responsabilité par dossier</span></div>'
    body = f"""<div class="row fill" style="gap:22px;margin:8px 0 14px">
  <div class="grid f1" style="grid-auto-rows:1fr;gap:13px">{left}</div><div class="grid f1" style="grid-auto-rows:1fr;gap:13px">{right}</div></div>"""
    return slide(30, K6, 'Architecture du projet : <span class="g">qui fait quoi</span>', body)


def _shot(name, fallback):
    return f"assets/shots/{name}.png" if (SHOTS / f"{name}.png").exists() else f"assets/report/{fallback}"


def s31():
    shots = [("login", "login.png", "Login"), ("overview", "overview.png", "Overview"), ("job_offers", "job_offers.png", "Job Offers"),
             ("analysis_form", "condidate_anal_1.png", "Candidate Analysis"), ("result_score", "condidate_anal_2.png", "Résultat & radar"),
             ("deep_analysis_2", "condidate_anal_5.png", "Deep Analysis"), ("leaderboard_podium", "talent_leader_3.png", "Leaderboard · podium"),
             ("analysis_history", "analysis_history.png", "Analysis History"), ("settings", "plateform_settings.png", "Settings · seuils"),
             ("mobile_overview", "phone_1.jpg", "Vue mobile")]
    h = ""
    for i, (n, fb, cap) in enumerate(shots):
        mobile = n.startswith("mobile")
        img = f'<img src="{_shot(n, fb)}" style="{"object-fit:contain;object-position:center;background:#0A0A14" if mobile else ""}">'
        h += f"""<div class="col" style="gap:10px;min-height:0"><div class="shot" id="shot{i+1}" style="flex:1;min-height:0">{img}</div>
  <div class="row ac" style="gap:10px"><span class="mono cy b t20">{i+1:02d}</span><span class="t24 sb">{cap}</span></div></div>"""
    body = f"""<div class="grid gfill" style="grid-template-columns:repeat(5,1fr);gap:18px;margin-top:6px">{h}</div>
<div class="row jc" style="margin:16px 0 10px">{bd('Interface responsive, vérifiée sur mobile', 'g', '', 'smartphone')}</div>"""
    return slide(31, K6, 'Les interfaces : <span class="g">captures réelles de la plateforme</span>', body)


def s32():
    steps = ["Connexion", "Créer une offre", "Évaluer un CV", "Lire le résultat", "Analyse approfondie", "Export PDF"]
    sh = ""
    for i, s in enumerate(steps):
        sh += f'<div class="card" style="flex:1;padding:16px 10px;text-align:center"><span class="g" style="font:700 30px \'Space Grotesk\'">{i+1}</span><div class="t22 sb" style="margin-top:4px;line-height:1.2">{s}</div></div>'
        if i < 5:
            sh += arrow(26)
    body = f"""<div class="row ac jb" style="margin-top:-6px">
  <div><div class="kicker">{K6}</div>
  <div class="g" style="font:700 104px/1 'Space Grotesk';letter-spacing:.02em;margin-top:14px;padding-bottom:6px">DÉMONSTRATION</div></div>
  <div class="row ac" style="gap:22px">
    <div><div class="lbl" style="text-align:right">Démo en ligne</div><div class="mono cy b" style="font-size:33px;margin-top:8px">{URL}</div></div>
    <div style="background:#fff;border-radius:20px;padding:12px;width:190px;height:190px"><img src="assets/qr.png" style="width:100%;height:100%;display:block"></div>
  </div>
</div>
<div class="row ac" style="gap:6px;margin-top:22px">{sh}</div>
<div class="fill" style="display:flex;justify-content:center;margin:20px 0 6px">
  <div id="vid-slot" style="height:100%;aspect-ratio:16/9;border-radius:22px;border:2.5px dashed rgba(139,92,246,.7);background:rgba(139,92,246,.07);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px">
    <span style="font-size:84px;color:#A78BFA;display:flex">{li('circle-play')}</span>
    <div class="mono b t26 vi" style="letter-spacing:.12em">EMPLACEMENT VIDÉO</div><div class="t22 mut">Enregistrement complet de la plateforme</div></div>
</div>"""
    return slide(32, "", "", body, head=False)


def s33():
    fs = [("F01", "Inscription"), ("F02", "Login"), ("F03", "Refus d'identifiants"), ("F04", "Création d'offre"),
          ("F05", "Évaluation · <code>CONSIDER</code>"), ("F06", "Persistance"), ("F07", "Deep Analysis <code>ok</code>"), ("F08", "PDF 1.4 · 2 pages")]
    fh = "".join(f'<div class="card gr" style="padding:0 16px;display:flex;align-items:center;gap:12px"><span style="color:#34D399;font-size:28px;display:flex">{li("circle-check")}</span><span class="mono gn b t22">{c}</span><span class="t24 sb">{t}</span></div>' for c, t in fs)
    body = f"""<div class="row fill" style="gap:24px;margin:8px 0 14px">
  <div class="card" style="flex:1;padding:28px 30px;display:flex;flex-direction:column;gap:16px">
    <div class="row ac jb"><div class="row ac" style="gap:16px">{ic('test-tube', 'sm')}<div class="ct" style="font-size:32px">Suite de tests</div></div><code style="font-size:26px">pytest · ~45 s</code></div>
    <div class="row" style="align-items:baseline;gap:16px;margin-top:6px"><span class="big g" style="font-size:150px;padding-bottom:8px">106</span><span class="big" style="font-size:66px;color:#8687A0">/ 113</span><span class="t32 sb">réussis</span></div>
    <div style="height:18px;border-radius:9px;background:rgba(255,255,255,.08);display:flex;overflow:hidden"><div style="flex:106;background:linear-gradient(90deg,#8B5CF6,#22D3EE)"></div><div style="flex:6;background:#EF4444"></div><div style="flex:1;background:#6B7280"></div></div>
    <div class="row wrap" style="gap:12px;margin-top:4px">{bd('6 échecs · <code style="color:inherit">test_api_extended.py</code>', 'r', '', 'x')}{bd('1 ignoré', 'n', '', 'minus')}</div>
    <ul class="pl" style="margin-top:4px"><li>Fixtures antérieures au contrôle d'appartenance</li><li>404 attendu, test à mettre à jour</li></ul>
    <div style="flex:1"></div>
    <div class="card o" style="padding:16px 20px;text-align:center"><span class="t26 b or">{li('triangle-alert')} Suite non entièrement verte, maintenance identifiée</span></div>
  </div>
  <div class="card" style="flex:1.05;padding:28px 30px;display:flex;flex-direction:column;gap:16px">
    <div class="row ac jb"><div class="row ac" style="gap:16px">{ic('cloud', 'sm c')}<div class="ct" style="font-size:32px">Bout en bout sur Azure</div></div>{bd('F01 → F08 OK', 'g', '', 'check')}</div>
    <div class="grid gfill" style="grid-template-columns:1fr 1fr;gap:11px">{fh}</div>
    <div class="row wrap jc" style="gap:10px">{bd('5 conteneurs healthy', 'c', 'sm', 'container')}{bd('<code style="color:inherit">nginx -t</code> OK', 'c', 'sm', 'check')}{bd('Swagger accessible', 'c', 'sm', 'book-open')}{bd('PDF : 112 039 octets', 'n', 'sm')}</div>
  </div>
</div>"""
    return slide(33, K6, 'Tests & validation : <span class="g">ce qui est prouvé</span>', body)


def s34():
    ok = ["bcrypt (passlib)", "JWT HS256 + expiration", "<code>_assert_owned</code> par ressource", "Cloisonnement <code>recruiter_id</code>",
          "ORM SQLAlchemy, pas de SQL concaténé", "60 req / min / IP", "Corps limité à 15 Mo", "Secrets hors dépôt · <code>.env</code> 0600", "NSG Azure : TCP 80 + 22"]
    ko = ["HTTP sans TLS", "Jeton en <code>localStorage</code> (XSS)", "SSH à restreindre · UFW inactif", "Pas de WAF ni rotation de secrets",
          "Pas de sauvegarde planifiée", "Upload validé par extension"]
    okh = "".join(f'<div class="row ac" style="gap:12px"><span style="color:#34D399;font-size:25px;display:flex;flex:none">{li("check")}</span><span class="t24">{t}</span></div>' for t in ok)
    koh = "".join(f'<div class="row ac" style="gap:12px"><span style="color:#FBBF24;font-size:25px;display:flex;flex:none">{li("triangle-alert")}</span><span class="t24">{t}</span></div>' for t in ko)
    law = "".join(bd(t, "c", "sm") for t in ["consentement", "finalité", "accès · rectification · suppression", "INPDP"])
    body = f"""<div class="row fill" style="gap:22px;margin-top:6px">
  <div class="card gr" style="flex:1.5;padding:24px 28px;display:flex;flex-direction:column;gap:14px">
    <div class="row ac jb"><div class="ct" style="font-size:31px;color:#6EE7B7">{li('shield-check')} Mis en œuvre</div></div>
    <div class="grid gfill" style="grid-template-columns:1fr 1fr;gap:6px 22px">{okh}</div>
    <div class="card v" style="padding:14px 18px;text-align:center"><span class="t24 b">{li('lock')} LLM exécuté en local → aucun CV envoyé à un tiers</span></div>
  </div>
  <div class="card o" style="flex:1;padding:24px 28px;display:flex;flex-direction:column;gap:14px">
    <div class="ct" style="font-size:31px;color:#FCD34D">{li('triangle-alert')} Limites assumées</div>
    <div class="grid gfill" style="gap:6px">{koh}</div>
  </div>
</div>
<div class="card c" style="margin:16px 0 12px;padding:16px 24px;display:flex;align-items:center;gap:18px">
  {ic('landmark', 'sm c')}<div class="ct" style="font-size:27px;white-space:nowrap">Loi tunisienne n° 2004-63</div>
  <div class="row wrap" style="gap:9px">{law}</div>
  <div style="margin-left:auto">{bd("conditions d'entrée en service", 'o', 'sm', 'flag')}</div>
</div>"""
    return slide(34, K6, 'Sécurité & données personnelles : <span class="g">acquis et limites</span>', body)


def s35():
    def node(x, y, w, h, t, sub, color, hot=False):
        return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:16px;border:2px solid {color};'
                f'background:{"rgba(16,185,129,.16)" if hot else "#15152A"};display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">'
                f'<div style="font:700 26px \'Space Grotesk\'">{t}</div><div class="mono" style="font-size:20px;color:{color};margin-top:3px">{sub}</div></div>')
    W, H = 1060, 790
    n = node(0, 330, 170, 96, "Internet", "public", "#C9C9DC")
    n += node(232, 330, 170, 96, "NSG", "TCP 80 / 22", "#F59E0B")
    n += node(478, 330, 200, 96, "Nginx", ":80", "#34D399", True)
    n += node(770, 196, 230, 92, "Next.js", ":3000", "#A78BFA")
    n += node(770, 448, 230, 92, "FastAPI", ":8000", "#22D3EE")
    n += node(478, 600, 230, 92, "PostgreSQL", ":5432", "#34D399")
    n += node(770, 600, 230, 92, "Ollama", ":11434", "#F59E0B")
    svg = f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="position:absolute;left:0;top:0;font-family:JetBrains Mono,monospace" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="az" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11 Z" fill="#22D3EE"/></marker></defs>
<rect x="202" y="6" width="{W-206}" height="{H-12}" rx="28" fill="rgba(59,130,246,.05)" stroke="#60A5FA" stroke-width="2.5"/>
<text x="228" y="46" fill="#93C5FD" font-size="22" font-weight="700" letter-spacing="1.2">MICROSOFT AZURE — EAST US</text>
<rect x="424" y="74" width="{W-448}" height="{H-106}" rx="24" fill="rgba(34,211,238,.04)" stroke="#22D3EE" stroke-width="2.5"/>
<text x="448" y="112" fill="#67E8F9" font-size="21" font-weight="700" letter-spacing="1.2">VM UBUNTU 24.04 LTS</text>
<rect x="450" y="136" width="{W-500}" height="{H-196}" rx="20" fill="rgba(139,92,246,.06)" stroke="#8B5CF6" stroke-width="2.5" stroke-dasharray="12 9"/>
<text x="474" y="172" fill="#C4B5FD" font-size="20" font-weight="700" letter-spacing="1.2">RÉSEAU DOCKER jobtest</text>
<line x1="170" y1="378" x2="228" y2="378" stroke="#22D3EE" stroke-width="3" marker-end="url(#az)"/>
<line x1="402" y1="378" x2="474" y2="378" stroke="#22D3EE" stroke-width="3" marker-end="url(#az)"/>
<path d="M678,360 H724 V242 H766" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#az)"/>
<path d="M678,396 H724 V494 H766" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#az)"/>
<path d="M885,540 V596" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#az)"/>
<path d="M830,540 V570 H593 V596" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#az)"/>
</svg>"""
    vm = "".join(f'<div class="row ac jb" style="padding:7px 0;border-top:1px solid rgba(255,255,255,.08)"><span class="t22 mut">{a}</span><span class="t22 sb">{b}</span></div>' for a, b in
                 [("Taille", "Standard D2as_v7"), ("Ressources", "2 vCPU · 8 Gio RAM"), ("Disque", "SSD + swap 4 Gio"), ("Coûts", "auto-shutdown ~02 h")])
    ct = "".join(f'<div class="row ac" style="gap:10px;padding:5px 0"><span style="color:#34D399;font-size:20px;display:flex">{li("circle-check")}</span><code style="font-size:21px">{c}</code></div>'
                 for c in ["nginx:1.27-alpine", "web (build)", "api (build)", "postgres:16-alpine", "ollama/ollama:0.5.13"])
    vols = "".join(bd(f'<code style="color:inherit;font-size:19px">{v}</code>', "v", "sm") for v in ["postgres_data", "ollama_data", "embedding_cache"])
    body = f"""<div class="row fill" style="gap:26px;margin:2px 0 12px">
  <div style="position:relative;width:{W}px;height:{H}px;flex:none">{svg}{n}</div>
  <div class="col f1" style="gap:14px">
    <div class="card c" style="padding:18px 22px"><div class="row ac jb"><div class="ct" style="font-size:27px">{li('server')} VM</div><code class="b" style="font-size:23px">vm-jobtest-pfe</code></div><div style="margin-top:8px">{vm}</div></div>
    <div class="card" style="padding:18px 22px"><div class="row ac jb"><div class="ct" style="font-size:27px">{li('container')} 5 conteneurs</div>{bd('healthy', 'g', 'sm')}</div><div style="margin-top:8px">{ct}</div></div>
    <div class="card" style="padding:16px 22px"><div class="lbl">Volumes persistants</div><div class="row wrap" style="gap:8px;margin-top:10px">{vols}</div></div>
  </div>
</div>"""
    return slide(35, K6, 'Déploiement Azure : <span class="g">trois frontières emboîtées</span>', body)


def s36():
    items = [("workflow", "Chaîne complète", "CV → verdict → rapport"), ("layers", "Moteur hybride", "3 signaux documentés"),
             ("repeat", "Décision explicite", "et reproductible"), ("shield-check", "Séparation stricte", "calcul / génératif"),
             ("cloud-upload", "Déploiement conteneurisé", "démontré sur Azure")]
    h = ""
    for i, (icon, t, s) in enumerate(items):
        h += f"""<div class="card" style="padding:0 34px;display:flex;align-items:center;gap:28px">
  <span style="width:76px;height:76px;border-radius:50%;background:linear-gradient(135deg,#8B5CF6,#22D3EE);display:grid;place-items:center;font-size:44px;color:#fff;flex:none">{li('check')}</span>
  <div class="row" style="align-items:baseline;gap:18px"><span style="font:700 40px 'Space Grotesk'">{t}</span><span class="t32 mut">{s}</span></div>
  <span style="margin-left:auto;font-size:44px;color:#A78BFA;display:flex">{li(icon)}</span></div>"""
    body = f'<div class="grid gfill" style="gap:16px;margin:8px 0 14px">{h}</div>'
    return slide(36, KC, 'Apports du projet : <span class="g">5 acquis</span>', body)


def s37():
    cols = [
        ("Court terme", "v", "calendar-clock", ["Domaine + certificat TLS", "Cookies <code>HttpOnly / Secure / SameSite</code>", "Restriction SSH", "Sauvegardes PostgreSQL", "Monitoring", "Correction des tests hérités"]),
        ("Moyen terme", "c", "calendar-range", ["Corpus réel anonymisé & autorisé", "Travail avec des recruteurs", "Enrichir le dictionnaire", "Calibrer les seuils", "Tests de biais", "Évaluation multilingue des explications"]),
        ("Long terme", "gr", "telescope", ["Traitements asynchrones & file de tâches", "Observabilité", "Intégration ATS", "Gouvernance et audit des décisions assistées"]),
    ]
    h = ""
    for i, (t, c, icon, pts) in enumerate(cols):
        h += f"""<div class="card {c}" style="padding:26px 28px;display:flex;flex-direction:column;gap:14px">
  <div class="row ac" style="gap:16px">{ic(icon, 'sm' + (' c' if c == 'c' else ' g' if c == 'gr' else ''))}<div><div class="mono dim b t18">HORIZON {i+1}</div><div class="ct" style="font-size:34px">{t}</div></div></div>
  <ul class="pl" style="gap:20px;margin-top:14px">{''.join(f'<li style="font-size:29px">{p}</li>' for p in pts)}</ul></div>"""
    lim = "".join(bd(t, "o", "", "triangle-alert") for t in ["corpus synthétique", "VM unique, pas de HA", "latence CPU de la couche 2", "dictionnaire incomplet"])
    tl = """<svg width="1752" height="30" viewBox="0 0 1752 30" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="tg" x1="0" x2="1"><stop offset="0" stop-color="#8B5CF6"/><stop offset=".5" stop-color="#22D3EE"/><stop offset="1" stop-color="#34D399"/></linearGradient></defs>
<line x1="10" y1="15" x2="1722" y2="15" stroke="url(#tg)" stroke-width="4" stroke-linecap="round"/><path d="M1716,3 L1742,15 L1716,27 Z" fill="#34D399"/>
<circle cx="284" cy="15" r="11" fill="#0A0A14" stroke="#8B5CF6" stroke-width="4"/><circle cx="876" cy="15" r="11" fill="#0A0A14" stroke="#22D3EE" stroke-width="4"/><circle cx="1468" cy="15" r="11" fill="#0A0A14" stroke="#34D399" stroke-width="4"/></svg>"""
    body = f"""<div style="margin-top:4px">{tl}</div>
<div class="grid gfill" style="grid-template-columns:repeat(3,1fr);gap:20px;margin-top:10px">{h}</div>
<div class="row ac jc wrap" style="gap:12px;margin:18px 0 12px"><span class="lbl">Limites assumées</span>{lim}</div>"""
    return slide(37, KC, 'Limites & <span class="g">perspectives</span>', body)


def s38():
    body = f"""<div style="flex:.9"></div>
<div style="text-align:center">
  <div class="g" style="font:700 124px/1.05 'Space Grotesk';letter-spacing:-.01em;padding-bottom:10px">MERCI POUR<br>VOTRE ATTENTION</div>
  <div style="font:500 44px 'Space Grotesk';color:#C9C9DC;margin-top:24px;font-style:italic">Place aux questions</div>
</div>
<div class="row ac jc" style="gap:28px;margin-top:50px">
  <div style="background:#fff;border-radius:20px;padding:12px;width:176px;height:176px"><img src="assets/qr.png" style="width:100%;height:100%;display:block"></div>
  <div><div class="lbl">Démo en ligne · JobTest</div><div class="mono cy b" style="font-size:38px;margin-top:10px">{URL}</div></div>
</div>
<div style="flex:1"></div>
<div class="row jc ac" style="gap:18px;margin-bottom:8px">
  <div class="logo-pill" style="height:76px;padding:10px 22px"><img src="assets/Logo_ISI_Kef.png" style="max-height:50px"></div>
  <div class="logo-pill" style="height:76px;padding:10px 22px"><img src="assets/Logo_UJ.png" style="max-height:50px"></div>
  <div class="logo-pill" style="height:76px;padding:10px 26px"><img src="assets/Logo_CyberCloud.png" style="max-height:44px"></div>
</div>"""
    return slide(38, "", "", body, head=False)


SLIDES = [s25, s26, s27, s28, s29, s30, s31, s32, s33, s34, s35, s36, s37, s38]
