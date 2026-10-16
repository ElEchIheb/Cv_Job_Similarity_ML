"""Slides 13 a 24 : besoins, regles, conception UML, architecture, moteur (1/2)."""
from deck_base import arrow, bd, ic, li, seq_svg, slide

K3 = "III · Spécification et analyse des besoins"
K4 = "IV · Conception"
K5 = "V · Moteur intelligent"


def s13():
    cards = [
        ("lock-keyhole", "", "AUTH", "BF-AUTH-01→03", ["Inscription", "Login JWT", "Déconnexion"]),
        ("briefcase", "c", "OFFRES", "BF-JOB-01→04", ["CRUD complet", "<code>OPEN / ON_HOLD / CLOSED</code>", "Code auto <code>JOB-YYYY-NNN</code>"]),
        ("users", "", "CANDIDATS", "BF-CAND-01→03", ["Liste par recruteur", "Pipeline : <code>NEW → UNDER_REVIEW → SHORTLISTED → INTERVIEW → HIRED / REJECTED</code>"]),
        ("scan-search", "c", "ÉVALUATION", "BF-EVAL-01→03", ["Texte ou PDF/DOCX", "Verdict explicable", "Résultat persisté"]),
        ("sparkles", "", "COMPLÉMENTS", "BF-LLM-01 · BF-REPORT-01 · BF-RANK-01/02", ["Analyse approfondie", "Rapport PDF", "Classement + CSV"]),
        ("sliders-horizontal", "c", "PILOTAGE", "BF-HIST-01 · BF-QUALITY-01/02 · BF-SETTINGS-01", ["Historique", "AI Insights · Quality Center", "Seuils réglables"]),
    ]
    h = ""
    for icon, c, t, code, pts in cards:
        lis = "".join(f'<li style="font-size:30px">{p}</li>' for p in pts)
        h += f"""<div class="card" style="padding:30px 32px;display:flex;flex-direction:column;gap:20px">
  <div class="row ac" style="gap:18px">{ic(icon, c, 68)}<div><div class="ct" style="font-size:38px;letter-spacing:.02em">{t}</div>
  <div class="mono cy" style="font-size:19px;margin-top:5px">{code}</div></div></div>
  <ul class="pl" style="margin-top:10px;gap:16px">{lis}</ul></div>"""
    body = f'<div class="grid gfill" style="grid-template-columns:repeat(3,1fr);gap:22px;margin:8px 0 14px">{h}</div>'
    return slide(13, K3, 'Besoins fonctionnels : <span class="g">6 familles</span>', body)


def s14():
    items = [
        ("shield-check", "BNF-SEC", "Sécurité", "JWT + appartenance"),
        ("eye-off", "BNF-PRIV", "Confidentialité", "Cloisonnement par recruteur"),
        ("search-check", "BNF-EXPL", "Explicabilité", "Même politique partout"),
        ("repeat", "BNF-REPRO", "Reproductibilité", "Poids & seuils persistés"),
        ("gauge", "BNF-PERF", "Performance", "Layer 2 non bloquante (~54 s CPU)"),
        ("heart-pulse", "BNF-RES", "Fiabilité", "Ollama indisponible ≠ échec"),
        ("smartphone", "BNF-ERG", "Ergonomie", "Responsive + <code>prefers-reduced-motion</code>"),
        ("container", "BNF-PORT", "Portabilité", "Docker Compose"),
    ]
    h = ""
    for i, (icon, code, t, s) in enumerate(items):
        h += f"""<div class="card" style="padding:28px 26px;display:flex;flex-direction:column;gap:14px">
  <div class="row ac jb">{ic(icon, 'c' if (i + i // 4) % 2 else '', 76)}<span class="mono cy b t22">{code}</span></div>
  <div class="ct" style="font-size:35px;margin-top:auto">{t}</div><div class="t26" style="color:#D3D3E2;line-height:1.3;min-height:68px">{s}</div></div>"""
    body = f"""<div class="grid gfill" style="grid-template-columns:repeat(4,1fr);gap:22px;margin:8px 0 14px">{h}</div>"""
    return slide(14, K3, 'Besoins non fonctionnels <span class="g">(ISO/IEC 25010)</span>', body)


def s15():
    rg = [
        ("RG-01", "Un recruteur ne voit que ses données"), ("RG-02", "Offre évaluée → non supprimable"),
        ("RG-03", "Candidat évalué → non supprimable"), ("RG-04", "Décision selon seuils actifs"),
        ("RG-05", "<code>Potential Fit &lt; Strong Fit</code>"), ("RG-06", "La couche LLM ne modifie JAMAIS le score ni le verdict"),
        ("RG-07", "AI Insights ne persiste rien"), ("RG-08", "Deep Analysis persistée seulement si <code>ok</code>"),
        ("RG-09", "L'historique garde ses métadonnées"), ("RG-10", "Uploads : PDF/DOCX avec texte lisible"),
    ]

    def row(code, t):
        hot = code == "RG-06"
        return f"""<div class="card {'v glow' if hot else ''}" style="padding:0 26px;display:flex;align-items:center;gap:22px;{'border-width:2.5px;' if hot else ''}">
  <span class="mono b" style="font-size:24px;padding:9px 16px;border-radius:12px;flex:none;{'background:linear-gradient(90deg,#8B5CF6,#22D3EE);color:#fff' if hot else 'background:rgba(34,211,238,.1);color:#67E8F9;border:1.5px solid rgba(34,211,238,.35)'}">{code}</span>
  <span style="font-size:{'29' if hot else '28'}px;font-weight:{'800' if hot else '500'};line-height:1.22">{t}</span>{('<span style="margin-left:auto;font-size:38px;color:#C4B5FD">' + li('shield-check') + '</span>') if hot else ''}</div>"""
    left = "".join(row(*r) for r in rg[:5])
    right = "".join(row(*r) for r in rg[5:])
    body = f"""<div class="row fill" style="gap:24px;margin:8px 0 14px">
  <div class="grid f1" style="grid-auto-rows:1fr;gap:16px">{left}</div>
  <div class="grid f1" style="grid-auto-rows:1fr;gap:16px">{right}</div>
</div>"""
    return slide(15, K3, 'Règles de gestion : <span class="g">RG-01 → RG-10</span>', body)


def _stick(x, y, label, sub, color):
    return (f'<g stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round"><circle cx="{x}" cy="{y}" r="24"/>'
            f'<line x1="{x}" y1="{y+24}" x2="{x}" y2="{y+100}"/><line x1="{x-40}" y1="{y+52}" x2="{x+40}" y2="{y+52}"/>'
            f'<line x1="{x}" y1="{y+100}" x2="{x-34}" y2="{y+156}"/><line x1="{x}" y1="{y+100}" x2="{x+34}" y2="{y+156}"/></g>'
            f'<text x="{x}" y="{y+198}" text-anchor="middle" fill="#F4F4FA" font-size="27" font-weight="700">{label}</text>'
            f'<text x="{x}" y="{y+230}" text-anchor="middle" fill="#A9A9C0" font-size="22">{sub}</text>')


def s16():
    W, H = 1752, 800
    o = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="display:block;font-family:Inter,sans-serif">',
         '<defs><marker id="ua" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11" fill="none" stroke="#F59E0B" stroke-width="2"/></marker></defs>',
         f'<rect x="270" y="6" width="1200" height="{H-12}" rx="26" fill="rgba(34,211,238,.035)" stroke="rgba(34,211,238,.65)" stroke-width="2.5"/>',
         '<text x="300" y="50" fill="#22D3EE" font-size="24" font-weight="700" font-family="JetBrains Mono,monospace" letter-spacing="2">SYSTÈME JOBTEST</text>']
    o.append(_stick(120, 150, "Visiteur", "non authentifié", "#A78BFA"))
    o.append(_stick(1630, 290, "Recruteur", "authentifié", "#22D3EE"))
    left = [("Créer un compte", 215), ("S'authentifier", 330)]
    main = ["Consulter le tableau de bord", "Gérer les offres", "Gérer les candidats", "Évaluer un CV",
            "Consulter les résultats explicables", "Demander une analyse approfondie",
            "Exploiter les résultats : rapport, classement, historique", "Qualité IA et configuration des seuils"]
    for lab, y in left:
        o.append(f'<line x1="166" y1="210" x2="{470-163}" y2="{y}" stroke="#A78BFA" stroke-width="2.2"/>')
        o.append(f'<ellipse cx="470" cy="{y}" rx="165" ry="38" fill="#17172B" stroke="#8B5CF6" stroke-width="2.2"/>')
        o.append(f'<text x="470" y="{y+8}" text-anchor="middle" fill="#F4F4FA" font-size="26" font-weight="600">{lab}</text>')
    cx, rx, ry = 1050, 385, 37
    ys = [104 + i * 88 for i in range(8)]
    for lab, y in zip(main, ys):
        o.append(f'<line x1="1584" y1="350" x2="{cx+rx}" y2="{y}" stroke="#22D3EE" stroke-width="2" opacity=".85"/>')
    for i, (lab, y) in enumerate(zip(main, ys)):
        hot = i in (3, 4, 5)
        o.append(f'<ellipse cx="{cx}" cy="{y}" rx="{rx}" ry="{ry}" fill="{"#221A3D" if hot else "#17172B"}" stroke="{"#A78BFA" if hot else "rgba(34,211,238,.75)"}" stroke-width="2.2"/>')
        o.append(f'<text x="{cx}" y="{y+8}" text-anchor="middle" fill="#F4F4FA" font-size="26" font-weight="600">{lab}</text>')
    # include : evaluer -> resultats ; extend : analyse approfondie -> resultats
    xi = cx - rx - 2
    o.append(f'<path d="M{xi+26},{ys[3]+22} C{xi-70},{ys[3]+40} {xi-70},{ys[4]-40} {xi+22},{ys[4]-24}" fill="none" stroke="#F59E0B" stroke-width="2.4" stroke-dasharray="7 6" marker-end="url(#ua)"/>')
    o.append(f'<text x="{xi-52}" y="{(ys[3]+ys[4])/2+7}" text-anchor="end" fill="#FBBF24" font-size="21" font-style="italic">«include»</text>')
    o.append(f'<path d="M{xi+26},{ys[5]-22} C{xi-70},{ys[5]-40} {xi-70},{ys[4]+40} {xi+22},{ys[4]+24}" fill="none" stroke="#F59E0B" stroke-width="2.4" stroke-dasharray="7 6" marker-end="url(#ua)"/>')
    o.append(f'<text x="{xi-52}" y="{(ys[4]+ys[5])/2+7}" text-anchor="end" fill="#FBBF24" font-size="21" font-style="italic">«extend»</text>')
    o.append("</svg>")
    body = f'<div style="margin-top:2px">{"".join(o)}</div>'
    return slide(16, K4, "Diagramme global des <span class=\"g\">cas d'utilisation</span>", body)


def s17():
    ucs = [
        ("UC-01", "Authentification", "key-round", ["Créer un compte", "Se connecter (JWT)", "Fermer la session"], ""),
        ("UC-02", "Offres", "briefcase", ["Créer / modifier", "Clôturer / rouvrir", "Supprimer si non évaluée"], ""),
        ("UC-03", "Candidats", "users", ["Lister ses candidats", "Mettre à jour le statut", "Supprimer si non évalué"], ""),
        ("UC-04", "Évaluer un CV", "scan-search", ["Choisir une offre", "Texte ou PDF/DOCX", "Verdict persisté"], "v"),
        ("UC-05", "Analyse approfondie", "sparkles", ["Contexte du résultat", "Appel Ollama local", "Persistée si <code>ok</code>"], "o"),
        ("UC-06", "Rapport PDF", "file-down", ["Exporter le résultat", "Génération ReportLab", "Aucun recalcul"], ""),
        ("UC-07", "Classement multi-CV", "trophy", ["Une offre, plusieurs CV", "Tri par score", "Export CSV"], ""),
        ("UC-08", "Historique", "history", ["Liste par date", "Filtres multicritères", "Détail vérifié"], ""),
    ]
    h = ""
    for code, t, icon, pts, c in ucs:
        lis = "".join(f'<li style="font-size:28px">{p}</li>' for p in pts)
        ext = bd("«extend»", "o", "sm") if code == "UC-05" else ""
        h += f"""<div class="card {c}" style="padding:26px 26px;display:flex;flex-direction:column;gap:14px">
  <div class="row ac jb"><span class="mono cy b" style="font-size:24px">{code}</span>{ext}{ic(icon, 'sm c' if c != 'v' else 'sm')}</div>
  <div class="ct" style="font-size:35px;margin-top:8px">{t}</div><ul class="pl" style="gap:14px;margin-top:8px">{lis}</ul></div>"""
    body = f'<div class="grid gfill" style="grid-template-columns:repeat(4,1fr);gap:20px;margin:8px 0 14px">{h}</div>'
    return slide(17, K4, "Cas d'utilisation raffinés : <span class=\"g\">UC-01 → UC-08</span>", body)


def _cls(x, y, w, name, attrs, color, soft):
    rows = "".join(f'<div style="font:500 21px/1.42 \'JetBrains Mono\',monospace;color:#DCDCEA">{a}</div>' for a in attrs)
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;border-radius:16px;overflow:hidden;border:2px solid {color};background:#12121F">'
            f'<div style="background:{soft};padding:11px 18px;font:700 27px \'Space Grotesk\';color:#fff;border-bottom:2px solid {color};text-align:center">{name}</div>'
            f'<div style="padding:12px 18px 14px">{rows}</div></div>')


def s18():
    W, H = 1752, 800
    b = ""
    b += _cls(150, 0, 380, "User", ["id · name · email", "password · role"], "#60A5FA", "rgba(96,165,250,.28)")
    b += _cls(0, 300, 330, "Candidate", ["phone", "resume_text", "skills[] · cv_file"], "#34D399", "rgba(52,211,153,.24)")
    b += _cls(350, 300, 310, "Recruiter", ["company", "position", "department"], "#A78BFA", "rgba(167,139,250,.28)")
    b += _cls(790, 60, 410, "JobOffer", ["job_code · title", "status : OPEN|ON_HOLD|CLOSED", "required_skills[]", "recruiter_id"], "#FB923C", "rgba(251,146,60,.26)")
    b += _cls(1340, 60, 410, "Application", ["candidate_id", "job_offer_id", "status · score"], "#2DD4BF", "rgba(45,212,191,.24)")
    b += _cls(1340, 420, 410, "MatchResult", ["score : float", "details : json", "created_at"], "#F87171", "rgba(248,113,113,.26)")
    b += _cls(820, 470, 340, "Skill", ["name", "category"], "#FBBF24", "rgba(251,191,36,.24)")
    L = "#C9C9DC"
    t = lambda x, y, s, anchor="middle", it=False: f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="#E7E7F3" font-size="22" font-weight="600"{" font-style=\"italic\"" if it else ""}>{s}</text>'
    svg = f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="position:absolute;left:0;top:0;font-family:Inter,sans-serif" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="tri" markerWidth="22" markerHeight="22" refX="20" refY="11" orient="auto"><path d="M2,2 L20,11 L2,20 Z" fill="#0A0A14" stroke="{L}" stroke-width="2"/></marker>
<marker id="ar" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11" fill="none" stroke="{L}" stroke-width="2"/></marker></defs>
<path d="M165,300 V236 H290 V150" fill="none" stroke="{L}" stroke-width="2.4" marker-end="url(#tri)"/>
<path d="M505,300 V236 H390 V150" fill="none" stroke="{L}" stroke-width="2.4" marker-end="url(#tri)"/>
<path d="M660,350 H752 V160 H788" fill="none" stroke="{L}" stroke-width="2.4" marker-end="url(#ar)"/>
{t(684, 338, '1')}{t(742, 190, '0..*', 'end')}{t(734, 262, 'publie', 'end', True)}
<path d="M1200,150 H1338" fill="none" stroke="{L}" stroke-width="2.4" marker-end="url(#ar)"/>
{t(1218, 138, '1')}{t(1310, 138, '0..*')}{t(1270, 184, 'reçoit', 'middle', True)}
<path d="M1545,246 V418" fill="none" stroke="{L}" stroke-width="2.4" marker-end="url(#ar)"/>
{t(1566, 276, '1', 'start')}{t(1566, 404, '0..1', 'start')}{t(1528, 340, 'a un', 'end', True)}
<path d="M990,290 V468" fill="none" stroke="{L}" stroke-width="2.4" marker-end="url(#ar)"/>
{t(1010, 320, '*', 'start')}{t(1010, 454, '*', 'start')}{t(972, 388, 'requiert', 'end', True)}
<path d="M818,560 H600 Q165,560 165,480" fill="none" stroke="{L}" stroke-width="2.4" marker-end="url(#ar)"/>
{t(800, 548, '*', 'end')}{t(190, 520, '*', 'start')}{t(500, 590, 'possède', 'middle', True)}
</svg>"""
    note = f"""<div class="card v" style="position:absolute;left:820px;top:660px;width:930px;padding:20px 26px;display:flex;align-items:center;gap:18px">
  {ic('database', 'sm')}<div class="t26"><code class="b">llm_analysis_json</code> stocké <b>dans</b> MatchResult — pas de table dédiée</div></div>"""
    leg = f"""<div style="position:absolute;left:0;top:690px" class="row ac">{bd('héritage', 'n', 'sm', 'triangle')}{bd('association', 'n', 'sm', 'arrow-right')}</div>"""
    body = f'<div style="position:relative;width:{W}px;height:{H}px;margin-top:2px">{svg}{b}{note}{leg}</div>'
    return slide(18, K4, 'Diagramme de classes : <span class="g">le modèle métier</span>', body)


def s19():
    actors = ["Recruteur", "Next.js", "FastAPI", "Service d'évaluation", "Layer 1", "PostgreSQL"]
    msgs = [
        (0, 1, "lance l'évaluation", "call"),
        (1, 2, "POST /ui/evaluate", "call"),
        (2, 3, "valider CV + propriété offre", "call"),
        (3, 4, "TF-IDF, embeddings, compétences", "call"),
        (4, 4, "agréger 0,2 / 0,4 / 0,4", "self"),
        (4, 3, "décision + explication", "ret"),
        (3, 5, "persist_evaluation", "call"),
        (5, 3, "match_id", "ret"),
        (3, 1, "score, verdict, explication", "ret"),
        (1, 0, "résultat affiché", "ret"),
    ]
    svg = seq_svg(1752, 790, actors, msgs, fs=22, top=70, step=66, first=52, colors={4: "#22D3EE", 5: "#34D399"})
    body = f'<div style="margin-top:6px">{svg}</div>'
    return slide(19, K4, "Séquence : <span class=\"g\">évaluation d'un CV</span> — le flux central", body)


def s20():
    la = ["Recruteur", "Next.js", "FastAPI", "Ollama", "PostgreSQL"]
    lw = 1030
    lx = [lw * (i + 0.5) / 5 for i in range(5)]
    lm = [
        (0, 1, "demande l'analyse", "call"),
        (1, 2, "POST deep-analysis(match_id)", "call"),
        (2, 4, "lire MatchResult", "call"),
        (2, 2, "contexte structuré", "self"),
        (2, 3, "/api/chat", "call"),
        (3, 2, "réponse JSON", "ret"),
        (0, 0, 34, "gap"),
        (2, 4, "persister l'analyse", "call"),
        (0, 0, 26, "gap"),
        (2, 1, "disabled | unavailable | error | inconsistent", "ret"),
    ]
    top, step, first = 62, 54, 42
    y_alt = top + first + 6 * step - 16
    frames = [(lx[0] + 40, lw - 12, y_alt + 6, y_alt + 76, "alt ok", "#34D399"), (lx[0] + 40, lw - 12, y_alt + 86, y_alt + 160, "sinon", "#F59E0B")]
    left = seq_svg(lw, 610, la, lm, fs=19, top=top, step=step, first=first, frames=frames, colors={3: "#F59E0B", 4: "#34D399"})
    ra = ["Recruteur", "Next.js", "FastAPI", "ReportLab"]
    rm = [(0, 1, "Export", "call"), (1, 2, "POST /report/pdf", "call"), (2, 3, "générer le document", "call"),
          (3, 2, "PDF", "ret"), (2, 1, "application/pdf", "ret"), (1, 0, "téléchargement", "ret")]
    right = seq_svg(612, 520, ra, rm, fs=19, top=62, step=70, first=52, colors={3: "#22D3EE"})
    body = f"""<div class="row fill" style="gap:26px;margin:4px 0 14px">
  <div class="card" style="padding:22px 22px 20px;display:flex;flex-direction:column;gap:12px;width:1076px;flex:none">
    <div class="row ac jb"><div class="ct" style="font-size:29px">{li('sparkles')} Deep Analysis</div>{bd('Couche 2 · optionnelle', 'o', 'sm')}</div>
    {left}
    <div class="card r" style="padding:14px 20px;text-align:center"><span class="t26 b rd">{li('shield-alert')} Score et verdict inchangés dans tous les cas</span></div>
  </div>
  <div class="card f1" style="padding:22px 20px;display:flex;flex-direction:column;gap:12px">
    <div class="row ac jb"><div class="ct" style="font-size:29px">{li('file-down')} Rapport PDF</div></div>
    {right}
    <div style="flex:1"></div>
    <div class="card c" style="padding:14px 20px;text-align:center"><span class="t26 b cy">{li('ban')} Aucun recalcul</span></div>
  </div>
</div>"""
    return slide(20, K4, 'Séquences : <span class="g">analyse approfondie</span> + <span class="g">rapport PDF</span>', body)


def s21():
    def node(x, y, w, h, t, sub, color, icon, hot=False):
        return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:18px;border:2px solid {color};'
                f'background:{"rgba(139,92,246,.2)" if hot else "#15152A"};display:flex;align-items:center;gap:16px;padding:0 20px">'
                f'<span style="font-size:36px;color:{color};display:flex">{li(icon)}</span><div><div style="font:700 27px \'Space Grotesk\'">{t}</div>'
                f'<div class="mono" style="font-size:20px;color:{color};margin-top:3px">{sub}</div></div></div>')
    W, H = 1110, 790
    n = ""
    n += node(0, 215, 232, 120, "Navigateur", "recruteur", "#C9C9DC", "globe")
    n += node(305, 215, 285, 120, "Nginx", ":80 · exposé", "#34D399", "shield-check", True)
    n += node(790, 78, 290, 112, "Next.js", ":3000", "#A78BFA", "layout-dashboard")
    n += node(790, 358, 290, 112, "FastAPI", ":8000", "#22D3EE", "zap")
    n += node(305, 532, 250, 108, "Layer 1", "moteur hybride", "#22D3EE", "brain-circuit")
    n += node(580, 532, 250, 108, "PostgreSQL", ":5432", "#34D399", "database")
    n += node(855, 532, 225, 108, "Ollama", ":11434", "#F59E0B", "sparkles")
    svg = f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="position:absolute;left:0;top:0;font-family:Inter,sans-serif" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="aa" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11 Z" fill="#22D3EE"/></marker></defs>
<rect x="275" y="8" width="{W-279}" height="660" rx="26" fill="rgba(139,92,246,.05)" stroke="#8B5CF6" stroke-width="2.5" stroke-dasharray="12 9"/>
<text x="300" y="46" fill="#C4B5FD" font-size="22" font-weight="700" font-family="JetBrains Mono,monospace" letter-spacing="1.5">RÉSEAU DOCKER INTERNE</text>
<line x1="232" y1="275" x2="301" y2="275" stroke="#22D3EE" stroke-width="3" marker-end="url(#aa)"/>
<text x="266" y="258" text-anchor="middle" fill="#67E8F9" font-size="21" font-weight="700">HTTP</text>
<path d="M590,252 H690 V134 H786" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#aa)"/>
<text x="738" y="120" text-anchor="middle" fill="#67E8F9" font-size="26" font-weight="700" font-family="JetBrains Mono,monospace">/</text>
<path d="M590,298 H690 V414 H786" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#aa)"/>
<text x="738" y="446" text-anchor="middle" fill="#67E8F9" font-size="22" font-weight="700" font-family="JetBrains Mono,monospace">/api/v1</text>
<path d="M935,470 V500 M430,500 H967" fill="none" stroke="#22D3EE" stroke-width="3"/>
<path d="M430,500 V528" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#aa)"/>
<path d="M705,500 V528" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#aa)"/>
<path d="M967,500 V528" fill="none" stroke="#22D3EE" stroke-width="3" marker-end="url(#aa)"/>
</svg>"""
    badge = f'<div style="position:absolute;left:275px;top:700px;width:{W-279}px;text-align:center">{bd("Ports 3000 / 8000 / 5432 / 11434 non publiés", "g", "lg", "lock")}</div>'
    mods = [("web/", "UI"), ("src/api/", "HTTP + JWT"), ("src/matching/", "orchestration"), ("src/models|fusion/", "scores"),
            ("src/explainability/", "explications"), ("src/ai/", "Ollama"), ("src/reporting/", "PDF"), ("src/models_db.py", "ORM")]
    ml = "".join(f'<div class="row ac jb" style="flex:1;border-top:1px solid rgba(255,255,255,.09)"><code style="font-size:24px">{a}</code><span class="t26 sb">{b}</span></div>' for a, b in mods)
    body = f"""<div class="row fill" style="gap:30px;margin:4px 0 14px">
  <div style="position:relative;width:{W}px;height:{H}px;flex:none">{svg}{n}{badge}</div>
  <div class="card f1" style="padding:26px 30px;display:flex;flex-direction:column">
    <div class="row ac" style="gap:16px;margin-bottom:16px">{ic('folder-tree', 'sm')}<div class="ct">Modules & responsabilités</div></div>{ml}
  </div>
</div>"""
    return slide(21, K4, 'Architecture logique : <span class="g">un seul point d\'entrée</span>', body)


def s22():
    def st(n, icon, t, sub, c="", hot=False, chips=""):
        return f"""<div class="card {'v glow' if hot else ''}" style="flex:1;padding:28px 18px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:18px;height:440px">
  <div class="mono cy b t22">{n}</div>{ic(icon, c, 92)}
  <div style="font:700 31px/1.18 'Space Grotesk'">{t}</div>{chips or f'<div class="mut t24" style="line-height:1.3">{sub}</div>'}</div>"""
    chips3 = f'<div class="col" style="gap:8px;align-items:center">{bd("TF–IDF", "v", "sm")}{bd("Embeddings", "c", "sm")}{bd("Compétences", "v", "sm")}</div>'
    dec = f'<div class="col" style="gap:8px;align-items:center">{bd("HIRE", "g", "sm")}{bd("CONSIDER", "o", "sm")}{bd("REJECT", "r", "sm")}</div>'
    body = f"""<div class="row ac" style="gap:10px;margin-top:14px">
  {st('01', 'file-stack', 'CV + Offre', 'PDF · DOCX · TXT')}{arrow(34)}
  {st('02', 'scissors', 'Extraction & segmentation', 'sections FR / EN', 'c')}{arrow(34)}
  {st('03', 'layers', '3 signaux', '', '', False, chips3)}{arrow(34)}
  {st('04', 'combine', 'Fusion pondérée', '0,2 · 0,4 · 0,4', 'c', True)}{arrow(34)}
  {st('05', 'badge-check', 'Décision', '', 'g', False, dec)}
</div>
<div class="row" style="justify-content:flex-end;padding-right:150px;margin:14px 0">{arrow(60, '#F59E0B', dashed=True, vertical=True)}</div>
<div class="card o" style="border-style:dashed;border-width:2.5px;padding:24px 32px;display:flex;align-items:center;gap:24px;margin-left:520px">
  {ic('sparkles', 'o', 76)}<div><div class="ct" style="font-size:32px">Couche 2 optionnelle</div><div class="t26 mut" style="margin-top:4px">analyse locale & questions d'entretien</div></div>
  <div style="margin-left:auto">{bd('additive, non décisionnelle', 'o', 'lg', 'shield-check')}</div>
</div><div style="flex:1"></div>"""
    return slide(22, K5, 'Pipeline de rapprochement : <span class="g">du document à la décision</span>', body)


def s23():
    def wbar(lab, v):
        return f'<div class="row ac" style="gap:12px"><span class="t22" style="width:150px;color:#D3D3E2">{lab}</span><div style="flex:1;height:12px;border-radius:6px;background:rgba(255,255,255,.08)"><div style="width:{v/0.4*100:.0f}%;height:100%;border-radius:6px;background:linear-gradient(90deg,#8B5CF6,#22D3EE)"></div></div><span class="mono cy t22 b">{str(v).replace(".", ",")}{"0" if len(str(v)) == 3 else ""}</span></div>'
    bars = "".join(wbar(l, v) for l, v in [("expérience", 0.40), ("compétences", 0.30), ("résumé", 0.15), ("formation", 0.10), ("langues", 0.05)])
    f = lambda s: f'<div class="mono" style="font-size:25px;color:#E9E4FF;background:rgba(139,92,246,.14);border:1.5px solid rgba(139,92,246,.4);border-radius:14px;padding:14px 16px;text-align:center;line-height:1.35">{s}</div>'
    body = f"""<div class="grid gfill" style="grid-template-columns:1fr 1.18fr 1fr;gap:22px;margin:8px 0 14px">
  <div class="card" style="padding:28px;display:flex;flex-direction:column;gap:18px">
    <div class="row ac" style="gap:18px">{ic('text-search', '', 72)}<div><div class="lbl vi">① Lexical</div><div class="ct" style="font-size:36px">TF–IDF</div></div></div>
    {f('S<sub>TFIDF</sub> = cos(v<sub>CV</sub>, v<sub>offre</sub>)')}
    <ul class="pl" style="gap:18px;margin-top:10px"><li style="font-size:31px">n-grammes 1–3</li><li style="font-size:31px">10 000 features max</li><li style="font-size:31px">Similarité cosinus</li></ul>
    <div style="margin-top:auto">{bd('Sensible aux synonymes', 'r', '', 'triangle-alert')}</div>
  </div>
  <div class="card v" style="padding:28px;display:flex;flex-direction:column;gap:16px">
    <div class="row ac" style="gap:18px">{ic('brain', '', 72)}<div><div class="lbl cy">② Sémantique</div><div class="ct" style="font-size:36px">Embeddings</div></div></div>
    {f('S<sub>emb</sub> = 0,7·moy(en, multi) + 0,3·sections')}
    <div class="col" style="gap:8px"><code style="font-size:21px">all-mpnet-base-v2</code><code style="font-size:21px">paraphrase-multilingual-mpnet-base-v2</code>
    <span class="t22 mut">repli : <code>HashingVectorizer</code></span></div>
    <div class="lbl" style="margin-top:4px">Pondération par sections</div><div class="col" style="gap:9px">{bars}</div>
  </div>
  <div class="card" style="padding:28px;display:flex;flex-direction:column;gap:18px">
    <div class="row ac" style="gap:18px">{ic('list-checks', 'c', 72)}<div><div class="lbl vi">③ Compétences</div><div class="ct" style="font-size:33px;line-height:1.1">Dictionnaire versionné</div></div></div>
    {f('techniques 0,70 · comportementales 0,30')}
    <div class="col" style="gap:20px;align-items:flex-start;margin-top:14px">
      {bd('+0,05 &nbsp;bonus domaine', 'g', 'lg', 'plus')}{bd('≤ +0,10 &nbsp;certifications', 'g', 'lg', 'plus')}{bd('≤ −0,20 &nbsp;critiques absentes', 'r', 'lg', 'minus')}
    </div>
    <div style="margin-top:auto">{bd('Trouvées · manquantes · critiques', 'c', 'sm', 'search-check')}</div>
  </div>
</div>"""
    return slide(23, K5, 'Les <span class="g">3 composantes</span> du score', body)


def s24():
    def band(rng, name, col, soft, txt, w):
        return f"""<div style="display:flex;align-items:center;gap:26px;border-radius:20px;border:2px solid {col};background:{soft};padding:0 30px;flex:1;width:{w}%">
  <span class="mono b" style="font-size:31px;color:#fff;width:210px;flex:none">{rng}</span>
  <span style="font:800 38px 'Space Grotesk';color:{col};width:250px;flex:none">{name}</span>
  <span class="t28" style="color:#E7E7F3;font-style:italic">{txt}</span></div>"""
    body = f"""<div class="card v glow" style="text-align:center;padding:38px 20px;margin-top:10px;border-width:2px">
  <div style="font:700 78px/1.1 'Space Grotesk';letter-spacing:-.01em">
    <span class="g">S<sub style="font-size:.5em">hybride</sub></span> = <span class="vi">0,2</span>·S<sub style="font-size:.5em">TFIDF</sub> + <span class="cy">0,4</span>·S<sub style="font-size:.5em">emb</sub> + <span class="cy">0,4</span>·S<sub style="font-size:.5em">skill</sub></div>
</div>
<div class="col fill" style="gap:14px;margin-top:26px">
  {band('[75 – 100]', 'HIRE', '#34D399', 'rgba(16,185,129,.13)', 'adéquation forte, à examiner en priorité', 100)}
  {band('[55 – 75[', 'CONSIDER', '#FBBF24', 'rgba(245,158,11,.13)', 'à examiner avec réserves', 86)}
  {band('[0 – 55[', 'REJECT', '#F87171', 'rgba(239,68,68,.13)', 'adéquation insuffisante', 72)}
</div>
<div class="row jc" style="margin:24px 0 14px">{bd('Seuils réglables par le recruteur et enregistrés avec chaque résultat', 'c', 'lg', 'sliders-horizontal')}</div>"""
    return slide(24, K5, 'Fusion hybride & <span class="g">décision</span>', body)


SLIDES = [s13, s14, s15, s16, s17, s18, s19, s20, s21, s22, s23, s24]
