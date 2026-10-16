"""Generate the Canva edit operations that fill the 48-page deck built from the blue template.

The Canva connector is driven from the chat session, not from Python: this script only turns the
slide content below into `edit-design` operations (ops.json) and into the presenter notes file.
Usage: python canva_ops.py [first_page last_page]   -> prints the operations of that page range.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(ROOT, "templates", "design_DAHXP_jZ7rA.json")
# template layout used by each page of the deck, in order
SEQ = [1, 2, 14, 3, 6, 14, 17, 15, 6, 7, 9, 12, 11, 17, 8, 14, 9, 10, 14, 18, 19, 20, 21, 25, 22, 23, 17, 12, 17,
       14, 15, 14, 14, 17, 14, 26, 9, 10, 27, 27, 27, 14, 14, 17, 28, 29, 30, 31]
ASSET = {
    "isi": "MAHXP-Bf3Q4", "uj": "MAHXP6Xgy2s", "cyber": "MAHXP-VAH4M", "uc": "MAHXP-YayXc", "uc04": "MAHXP2uQR2k",
    "uc05": "MAHXP2LTU_Q", "classes": "MAHXP_CG6aE", "seq": "MAHXPw3m2O8", "seqdeep": "MAHXP9LkX74",
    "archi": "MAHXP8loTZY", "azure": "MAHXP0zkqpI", "pipeline": "MAHXPxq9-lk", "cascade": "MAHXP9xD0YM",
    "bench": "MAHXPy1WWro", "results": "MAHXP30_knE", "qr": "MAHXP0paTME", "overview": "MAHXPyT_Lyg",
    "result": "MAHXPy5Y4SY", "scorecard": "MAHXP3qot_k", "leaderboard": "MAHXPwC7ZWU",
}
# page-number text element of each layout
NUM = {2: "tnGTb", 14: "SRJHk", 3: "Xnppc", 6: "FsN4h", 17: "B5bSz", 15: "MdK5R", 7: "lvDQK", 9: "3Ncnn",
       12: "0ND5X", 11: "Pfgnj", 8: "8b2SC", 10: "1R3nN", 18: "YW5Xg", 19: "HSl1v", 20: "6Fzt2", 21: "PNChW",
       25: "PhR4X", 22: "X33gT", 23: "cBw5m", 26: "MRrfK", 28: "HNGb9", 29: "0rJ9s", 30: "hpr5L"}
# 3x3 numbered grids (layouts 9 and 10): label, number, circle for each cell, row by row
GRID = {
    9: [("zTYhQ", "h5t7K", "y5tDN"), ("B5mgt", "v8XBl", "rLzgF"), ("qS5yK", "2l7Ws", "gp7qM"),
        ("ZzHK6", "zgSJY", "dZsjX"), ("Z4cc5", "kfyXz", "tzW9N"), ("nQKtl", "fCBql", "sKnf0"),
        ("wz36M", "YVtV4", "qjrYg"), ("hjGpV", "9D1nM", "HQMND"), ("TZBCt", "XWGpq", "bk9gX")],
    10: [("XB680", "cvg2B", "Qscm7"), ("t3dwh", "Ghg7b", "2lwPh"), ("qNyk7", "4MqVz", "XJG8H"),
         ("PnfBn", "6RjGs", "fQ1wn"), ("c9cVF", "tvzWN", "Xt01l"), ("4GPzV", "7Cj8m", "hBYJP"),
         ("tZ6Pk", "R6gJM", "prNLy"), ("8Z0gf", "mlmpC", "G8DJs"), ("rpVgC", "PNYwK", "4hbdr")],
}
GRID_CENTER = [992, 1274, 1568]

pages = json.load(open(DUMP, encoding="utf-8"))["design_content"]["pages"]


def flat(els):
    for e in els:
        yield e
        for k in ("children", "elements"):
            yield from flat(e.get(k) or [])


class Page:
    def __init__(self, n):
        self.n, self.layout, self.ops = n, SEQ[n - 1], []
        self.els = list(flat(pages[n - 1]["elements"]))
        self.base = list(flat(pages[SEQ.index(self.layout)]["elements"]))
        self.id = pages[n - 1]["id"]

    def el(self, suf):
        i = next(i for i, e in enumerate(self.base) if e["id"].endswith(suf))
        return self.els[i]

    def loc(self, suf):
        return self.el(suf)["locator_id"]

    def op(self, type_, suf=None, **kw):
        o = {"type": type_}
        if suf:
            o["locator_id"] = self.loc(suf)
        o.update(kw)
        self.ops.append(o)
        return self

    def t(self, suf, text, **fmt):
        self.op("replace_text", suf, text=text)
        return self.fmt(suf, **fmt) if fmt else self

    def far(self, suf, find, repl):
        return self.op("find_and_replace_text", suf, find_text=find, replace_text=repl)

    def fmt(self, suf, **fmt):
        return self.op("format_text", suf, formatting=fmt)

    def w(self, suf, width):
        return self.op("resize_element", suf, width=width)

    def pos(self, suf, left, top):
        return self.op("position_element", suf, left=left, top=top)

    def rm(self, *sufs):
        for s in sufs:
            self.op("delete_element", s)
        return self

    def img(self, suf, asset, left, top, width, height, alt, unrotate=False):
        if unrotate:
            self.op("rotate_element", suf, rotation=0)
        self.op("resize_element", suf, width=width, height=height)
        self.pos(suf, left, top)
        self.op("update_fill", suf, asset_type="image", asset_id=ASSET[asset], alt_text=alt)
        return self.op("crop_media", suf, left=0, top=0, width=width, height=height)

    def add_img(self, asset, left, top, width, height, alt):
        return self.op("insert_fill", page_id=self.id, asset_type="image", asset_id=ASSET[asset], alt_text=alt,
                       left=left, top=top, width=width, height=height)

    def add_text(self, text, left, top, width):
        return self.op("add_text", page_id=self.id, text=text, left=left, top=top, width=width)

    def number(self):
        if self.layout in NUM:
            s = NUM[self.layout]
            self.t(s, f"{self.n - 1}  ·  JobTest — PFE 2025/2026", font_size=22, text_align="start")
            self.w(s, 520).pos(s, 36, 1034)
        return self

    def notes(self, text):
        return self.op("replace_speaker_notes", page_id=self.id, notes=text)


def divider(n, title_suf, num_suf, title, num, two_lines=False):
    p = Page(n).t(title_suf, title).t(num_suf, num)
    if two_lines and p.el(title_suf)["top"] > 450:
        p.pos(title_suf, round(p.el(title_suf)["left"]), 430)
    return p


def bullets14(n, title, sub, b1, b2, b3, title_fs=None):
    p = Page(n).t("gJxC4", title).w("gJxC4", 1320).t("HsFx0", sub)
    if title_fs:
        p.fmt("gJxC4", font_size=title_fs)
    for suf, txt in (("jgw33", b1), ("stqkc", b2), ("zCzk9", b3)):
        p.t(suf, txt)
    return p


def figure17(n, title, asset, box, alt):
    p = Page(n).t("nG21C", title)
    return p.img("8f38g", asset, *box, alt)


def side_figure(n, label_suf, label, img_suf, asset, box, alt, extra=None, unrotate=False):
    p = Page(n).t(label_suf, label)
    p.img(img_suf, asset, *box, alt, unrotate=unrotate)
    if extra:
        p.rm(extra)
    return p


def grid(n, side_suf, side, labels, width=290):
    p = Page(n)
    if side:
        p.t(side_suf, side)
    cells = GRID[p.layout]
    for i, (lab, num, circle) in enumerate(cells):
        if i < len(labels):
            p.t(lab, labels[i])
            need = max(len(x) for x in labels[i].split()) * 20 + 12
            if need > p.el(lab)["width"]:
                p.w(lab, need).pos(lab, GRID_CENTER[i % 3] - need // 2, round(p.el(lab)["top"]))
        else:
            p.rm(lab, num, circle)
    return p


def bullets6(n, title, texts, tops=(353, 489, 625), keep_icon=True):
    p = Page(n)
    if title:
        p.t("HyH1N", title)
    if not keep_icon:
        p.rm("YT26R")
    for (txt_suf, tri_suf), txt, top in zip((("RFssy", "jHBTQ"), ("rVn21", "ZnLPD"), ("pR4Cv", "sDkXs")), texts, tops):
        p.t(txt_suf, txt, text_align="start").w(txt_suf, 870).pos(txt_suf, 998, top).pos(tri_suf, 912, top + 2)
    return p


def build():
    P = []
    # 1 — title
    p = Page(1)
    p.t("MwjxH", "Conception et développement d'une plateforme intelligente d'aide au recrutement et de mise en "
                 "correspondance entre CV et offres d'emploi", font_size=54, text_align="start")
    p.far("B1qwP", "HASSYAOUI Wajdi", "Iheb EL ECH")
    p.far("rSZjm", "Mr Samir Gara", "Dr. Aymen LOUATI").far("rSZjm", "Mme BETTAYEB SOUHA ", "Dr. Emna TRABELSI")
    p.far("xNCBY", "2023/2024", "2025/2026")
    p.img("rxhqN", "isi", 108, 100, 520, 88, "Institut Supérieur d'Informatique du Kef")
    p.img("XtFBJ", "cyber", 1500, 85, 300, 119, "CyberCloud Solutions")
    p.add_img("uj", 800, 90, 400, 108, "Université de Jendouba")
    p.add_text("Mastère Professionnel — Applications Web Intelligentes · JobTest", 165, 322, 1500)
    p.add_text("Soutenu le : ____ / ____ / 2026", 165, 770, 900)
    P.append(p)
    # 2 — plan
    p = Page(2).t("1P30K", "Plan")
    for suf, txt in zip(("2fp3z", "D9lG7", "ZNJq5", "hbzNR", "SPh8x", "SNytt"),
                        ("Contexte général", "Méthodologie", "Spécification des besoins", "Conception",
                         "Moteur intelligent", "Réalisation et conclusion")):
        p.t(suf, txt, text_align="start").w(suf, 900).pos(suf, 580, round(p.el(suf)["top"]))
    P.append(p)
    P.append(bullets14(3, "Introduction", "Trier des CV coûte du temps. Décider reste humain.",
                       "CV hétérogènes, offres en langage libre", "3 signaux fusionnés, 0 décision automatisée",
                       "Assister le recruteur, pas le remplacer"))
    P.append(divider(4, "JSzZ2", "DwfGn", "Contexte général", "01", two_lines=True))
    # 5 — host company
    p = bullets6(5, "Organisme d'accueil", ("Fondée en 2017, Grand Tunis, 2 à 10 personnes",
                                            "Conseil, infrastructure, cybersécurité, cloud",
                                            "PFE individuel, mars à août 2026, hybride"), keep_icon=False)
    p.img("Nn3mr", "cyber", 120, 420, 430, 170, "Logo CyberCloud Solutions")
    P.append(p)
    P.append(bullets14(6, "Étude de l'existant", "Deux pratiques, les mêmes limites",
                       "Tri manuel : coûteux, peu traçable", "ATS par mots-clés : paraphrases ignorées",
                       "CV multilingues, formats disparates"))
    p = figure17(7, "Benchmark des solutions", "bench", (150, 320, 1560, 564), "Tableau comparatif des solutions")
    p.add_text("« Non documenté » : aucune preuve dans les pages officielles consultées (13/09/2026)", 150, 920, 1500)
    P.append(p)
    # 8 — what is missing
    p = Page(8).t("gcl17", "Critique de l'existant")
    for suf, txt, top in (("WPJtk", "Analyse du texte", 423), ("7vz4m", "Règle de décision", 564),
                          ("6sS4s", "Explication fournie", 706)):
        p.t(suf, txt).w(suf, 400).pos(suf, 253, top)
    p.rm("DNdd7", "1s2Mx", "30N2B")
    p.t("gNKPH", "Trois briques séparées").w("gNKPH", 620).pos("gNKPH", 143, 830)
    p.t("61Tr3", "Cohérence\nmanquante", font_size=84).w("61Tr3", 640).pos("61Tr3", 1160, 545)
    P.append(p)
    P.append(bullets6(9, None, ("Comment fournir au recruteur une évaluation CV/offre hybride, explicable, "
                                "reproductible et persistante…", "…sans lui déléguer la décision d'embauche ?",
                                "Vérifiable par ses composantes, génératif encadré"), tops=(290, 520, 680)))
    p = Page(10)
    p.t("TxRNr", "Un moteur hybride compare le CV à l'offre : score, verdict, écarts de compétences.",
        text_align="start")
    p.t("VvYSZ", "Autour : historique, classement multi-CV, rapport PDF et analyse approfondie.", text_align="start")
    P.append(p)
    P.append(grid(11, "JpS4k", "Objectifs du projet",
                  ["Workflow recruteur", "CV texte ou fichier", "3 signaux fusionnés", "Décision cohérente",
                   "Résultat explicable", "Historique persistant", "Rapport et classement",
                   "Déploiement démontrable"]))
    P.append(divider(12, "Hqw6l", "LbNkF", "Méthodologie", "02"))
    p = Page(13).t("jc7NR", "Choix méthodologique").w("jc7NR", 1400).pos("jc7NR", 290, 86).pos("DVGFz", 1278, 652)
    P.append(p)
    P.append(figure17(14, "Modèle en cascade", "cascade", (300, 290, 1330, 680), "Déroulement en cascade du projet"))
    P.append(divider(15, "Sc6N9", "yjmCl", "Spécification des besoins", "03", two_lines=True))
    P.append(bullets14(16, "Acteurs du système", "Deux acteurs, un seul rôle métier",
                       "Visiteur : créer un compte, se connecter", "Recruteur authentifié : acteur principal",
                       "Candidat : entité métier, jamais utilisateur"))
    P.append(grid(17, None, None, ["Authentification JWT", "Gestion des offres", "Suivi des candidats",
                                   "Évaluation d'un CV", "Analyse approfondie", "Rapport PDF",
                                   "Classement multi-CV", "Historique", "Pilotage et seuils"]))
    P.append(grid(18, None, None, ["Sécurité", "Confidentialité", "Explicabilité", "Reproductibilité",
                                   "Performance", "Fiabilité", "Ergonomie", "Portabilité"], width=300))
    # 19 — business rules
    p = Page(19).t("gJxC4", "Règles de gestion").w("gJxC4", 1320).t("HsFx0", "Dix règles, une seule à retenir")
    p.rm("7g5rN", "pC3pY")
    p.t("jgw33", "RG-01  Un recruteur ne voit que ses données\nRG-02  Offre évaluée : non supprimable\n"
                 "RG-03  Candidat évalué : non supprimable\nRG-04  Décision selon les seuils actifs\n"
                 "RG-05  Potential Fit < Strong Fit", font_size=30).w("jgw33", 1250).pos("jgw33", 516, 335)
    p.pos("s5g7C", 434, 585)
    p.t("stqkc", "RG-06  Le LLM ne modifie jamais le score ni le verdict", color="#17e3b2").w("stqkc", 1250)
    p.pos("stqkc", 516, 578)
    p.t("zCzk9", "RG-07  AI Insights ne persiste rien\nRG-08  Deep Analysis persistée seulement si ok\n"
                 "RG-09  L'historique garde ses métadonnées\nRG-10  Uploads : PDF ou DOCX avec texte lisible",
        font_size=30).w("zCzk9", 1250).pos("zCzk9", 516, 730)
    P.append(p)
    P.append(divider(20, "VCtP4", "GGcJt", "Conception", "04"))
    P.append(side_figure(21, "Dk6Q4", "Cas\nd'utilisation\nglobal", "QrNB0", "uc", (420, 150, 1440, 777),
                         "Diagramme global des cas d'utilisation", unrotate=True))
    P.append(side_figure(22, "J4Pg3", "UC-04\nÉvaluer\nun CV", "W0sTs", "uc04", (420, 150, 1440, 778),
                         "Cas d'utilisation UC-04", extra="l214m"))
    P.append(side_figure(23, "25KzQ", "UC-05\nAnalyse\napprofondie", "H3d4b", "uc05", (440, 140, 1400, 785),
                         "Cas d'utilisation UC-05", extra="D4VJY"))
    P.append(side_figure(24, "hFGtB", "Diagramme\nde classes", "TsB6l", "classes", (430, 265, 1440, 553),
                         "Diagramme de classes métier"))
    P.append(side_figure(25, "80y4J", "Séquence\nÉvaluation\nd'un CV", "DKF0C", "seq", (440, 140, 1400, 786),
                         "Séquence d'évaluation d'un CV", extra="Tg5KY"))
    P.append(side_figure(26, "Y3Ttw", "Séquence\nAnalyse\napprofondie", "ZrxtZ", "seqdeep", (420, 220, 1440, 653),
                         "Séquence d'analyse approfondie"))
    P.append(figure17(27, "Architecture logique", "archi", (506, 300, 907, 720), "Architecture logique de JobTest"))
    p = divider(28, "Hqw6l", "LbNkF", "Moteur intelligent", "05", two_lines=True)
    p.op("update_fill", "psM9X", asset_type="image", asset_id=ASSET["result"], alt_text="Résultat d'analyse JobTest")
    P.append(p)
    P.append(figure17(29, "Pipeline de rapprochement", "pipeline", (150, 470, 1560, 259), "Pipeline de rapprochement"))
    P.append(bullets14(30, "Les 3 composantes du score", "Trois signaux calculés séparément, puis fusionnés",
                       "Lexical : TF-IDF, n-grammes 1 à 3, cosinus", "Sémantique : embeddings MPNet multilingues",
                       "Compétences : dictionnaire versionné, bonus et pénalités", title_fs=64))
    # 31 — fusion and decision
    p = Page(31).t("gcl17", "Fusion hybride et décision")
    for suf, txt, top in (("WPJtk", "0,2 × TF-IDF", 423), ("7vz4m", "0,4 × Embeddings", 564),
                          ("6sS4s", "0,4 × Compétences", 706)):
        p.t(suf, txt).w(suf, 400).pos(suf, 253, top)
    p.rm("DNdd7", "1s2Mx")
    p.t("gNKPH", "Score hybride").w("gNKPH", 620).pos("gNKPH", 143, 830)
    p.img("30N2B", "scorecard", 1130, 330, 720, 548, "Score et verdict affichés par JobTest")
    p.t("61Tr3", "HIRE ≥ 75 %  ·  CONSIDER ≥ 55 %  ·  REJECT", font_size=34).w("61Tr3", 800).pos("61Tr3", 1090, 915)
    P.append(p)
    P.append(bullets14(32, "Couche 2 : analyse locale", "Ollama qwen2.5:1.5b commente, il ne décide jamais",
                       "Format imposé : aucun champ de score", "Contrôle de cohérence, puis état inconsistent",
                       "Score calculé avant le modèle : anti-injection"))
    P.append(bullets14(33, "Protocole expérimental", "cv_job_dataset.csv, corpus synthétique, graine 42",
                       "12 000 paires CV-offre, 20 domaines, FR + EN", "8 400 train · 1 800 validation · 1 800 test",
                       "Synthétique : aucun corpus réel accessible"))
    p = figure17(34, "Résultats comparatifs", "results", (150, 360, 1570, 409), "Résultats des quatre méthodes")
    p.add_text("1 800 paires de test  ·  Fusion : 55,85 ms/paire  ·  Embeddings seuls : 921,60 ms/paire", 150, 830, 1500)
    p.add_text("Le générateur partage un vocabulaire contrôlé : avantage mécanique du lexical.", 150, 900, 1500)
    P.append(p)
    P.append(bullets14(35, "Deux corrections assumées", "Deux défauts trouvés, montrés et corrigés",
                       "Poids 0,9 / 0,0 / 0,1 rétablis à 0,2 / 0,4 / 0,4", "Écart de reformulation : 25,6 → 9,6 points",
                       "Seuil calibré par méthode : F1 0,000 → 0,950", title_fs=64))
    P.append(divider(36, "5rvSQ", "ghH5f", "Réalisation", "06"))
    P.append(grid(37, "JpS4k", "Stack technique",
                  ["Next.js 14\nReact 18", "Tailwind\nThree.js", "FastAPI\nPydantic", "SQLAlchemy\nPostgreSQL 16",
                   "scikit-learn\nspaCy", "Sentence\nTransformers", "Ollama\nqwen2.5:1.5b", "pdfplumber\nReportLab",
                   "Docker\nNginx · Azure"]))
    P.append(grid(38, "MJ62N", "Architecture du projet",
                  ["web/\nInterface Next.js", "api/\nFastAPI + JWT", "matching/\nOrchestration",
                   "models/\nTrois scores", "fusion/\nScore hybride", "decisioning/\nVerdict",
                   "explainability/\nExplications", "ai/\nPrompts Ollama", "reporting/\nRapport PDF"]))
    for n, sub, asset, alt in ((39, "Tableau de bord", "overview", "Vue d'ensemble JobTest"),
                               (40, "Résultat d'analyse", "result", "Résultat d'analyse d'un candidat")):
        p = Page(n).t("ZmYKX", "Les interfaces").t("YcWqn", sub)
        p.op("update_fill", "MbLLn", asset_type="image", asset_id=ASSET[asset], alt_text=alt)
        p.op("crop_media", "MbLLn", left=0, top=0, width=1259, height=708)
        P.append(p)
    p = Page(41).t("ZmYKX", "Démonstration").t("YcWqn", "20.51.167.202", font_size=40)
    p.op("update_fill", "MbLLn", asset_type="image", asset_id=ASSET["leaderboard"],
         alt_text="Emplacement de la vidéo de démonstration")
    p.op("crop_media", "MbLLn", left=0, top=0, width=1259, height=708)
    p.add_img("qr", 220, 640, 240, 240, "QR code vers http://20.51.167.202/")
    P.append(p)
    P.append(bullets14(42, "Tests et validation", "Une suite pas entièrement verte, et c'est dit",
                       "pytest : 106 réussis sur 113, en 45 s", "6 échecs hérités, 1 ignoré : maintenance identifiée",
                       "8 contrôles de bout en bout validés sur Azure"))
    P.append(bullets14(43, "Sécurité et données", "Loi tunisienne n° 2004-63 : des conditions d'entrée en service",
                       "En place : bcrypt, JWT, cloisonnement par recruteur", "LLM local : aucun CV envoyé à un tiers",
                       "Limites : HTTP sans TLS, jeton en localStorage"))
    p = figure17(44, "Déploiement Azure", "azure", (880, 280, 829, 740), "Architecture de déploiement sur Azure")
    p.add_text("vm-jobtest-pfe\nStandard D2as_v7\n2 vCPU · 8 Gio RAM\nUbuntu 24.04 LTS\n5 conteneurs healthy", 150, 420, 650)
    P.append(p)
    P.append(Page(45).t("3D2hK", "07"))
    p = Page(46)
    p.t("wL9pz", "Une chaîne complète : CV, verdict, rapport\nUn moteur hybride à 3 signaux documentés")
    p.t("mW1X6", "Une décision explicite et reproductible\nCalcul et génératif strictement séparés\n"
                 "Un déploiement conteneurisé démontré").pos("mW1X6", 977, 590)
    P.append(p)
    p = Page(47)
    p.t("qdGdP", "Limites : corpus synthétique, VM unique, latence CPU de la couche 2", text_align="start")
    p.t("vhrR1", "Court terme : TLS, cookies sécurisés, sauvegardes\nMoyen terme : corpus réel, recruteurs, biais\n"
                 "Long terme : asynchrone, intégration ATS").w("vhrR1", 940)
    P.append(p)
    P.append(Page(48))
    return P


# presenter notes: page -> slide number of livrables/Notes_presentateur.md, or a text written for this deck
NOTES = {
    1: 1,
    2: "La présentation suit le plan habituel de l'institut : le contexte général et la problématique, la méthodologie, "
       "la spécification des besoins, puis la conception UML. J'ajoute une partie sur le moteur intelligent, qui est le "
       "cœur du travail, avant la réalisation, la démonstration et la conclusion.",
    3: 3,
    4: "Je commence par le contexte : l'organisme d'accueil, l'étude de l'existant, la problématique, puis la solution proposée.",
    5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10,
    12: "Deuxième partie : la méthodologie de travail retenue pour ce projet.",
    13: "Trois démarches étaient envisageables : Scrum, le modèle en V et le modèle en cascade. J'ai retenu la cascade. "
        "C'est un PFE individuel, dont les livrables peuvent être stabilisés un par un ; les rituels d'équipe d'une "
        "méthode agile apportaient peu à une personne seule, et la cascade donne un fil de lecture clair au mémoire.",
    14: 11,
    15: "Troisième partie : qui utilise le système, ce qu'il doit faire, et les qualités qu'on attend de lui.",
    16: 12, 17: 13, 18: 14, 19: 15,
    20: "Quatrième partie : la conception, avec les cas d'utilisation, le diagramme de classes, les séquences et l'architecture.",
    21: 16,
    22: "Parmi les huit cas d'utilisation raffinés, de UC-01 à UC-08, je montre le cas central : UC-04, évaluer un CV. "
        "Le recruteur choisit une offre qui lui appartient, saisit le CV ou téléverse un PDF ou un DOCX, choisit la "
        "méthode d'appariement ; le système calcule, enregistre un résultat explicable, puis l'affiche. Les autres cas "
        "couvrent l'authentification, les offres, les candidats, le rapport PDF, le classement multi-CV et l'historique.",
    23: "UC-05, l'analyse approfondie, est une extension de la consultation d'un résultat : elle est optionnelle et vient "
        "toujours après. Le contexte est reconstruit depuis le résultat enregistré, Ollama est appelé en local, et "
        "l'analyse n'est conservée que si elle est valide. Le recruteur consulte ensuite son état et son contenu.",
    24: 18, 25: 19,
    26: "Voici la séquence de l'analyse approfondie. L'API relit le MatchResult, construit un contexte structuré et "
        "appelle Ollama. Si la réponse est valide, elle est persistée ; sinon l'API renvoie un état contrôlé : disabled, "
        "unavailable, error ou inconsistent. Dans tous les cas, le score et le verdict restent inchangés. Le rapport PDF "
        "suit la même logique : l'interface transmet le résultat existant, ReportLab compose le document, rien n'est recalculé.",
    27: 21,
    28: "J'arrive au cœur du projet : le moteur de rapprochement, sa règle de décision et son évaluation.",
    29: 22, 30: 23, 31: 24, 32: 25, 33: 26, 34: 27, 35: 28,
    36: "Dernière partie : les technologies, l'organisation du code, les interfaces, la démonstration, puis les tests, "
        "la sécurité et le déploiement.",
    37: 29, 38: 30,
    39: "Voici les interfaces réelles de la plateforme, capturées sur l'instance déployée. Le tableau de bord donne au "
        "recruteur ses indicateurs : candidats évalués, compatibilité moyenne, offres actives et analyses récentes. "
        "L'interface est responsive et a été vérifiée sur mobile.",
    40: "La page de résultat affiche le score global, le verdict et un radar de compétences, puis le détail des trois "
        "sous-scores. L'analyse approfondie vient en dessous. Le recruteur peut exporter le rapport PDF, classer "
        "plusieurs CV dans le Talent Leaderboard, retrouver l'historique et régler ses seuils dans les paramètres.",
    41: 32, 42: 33, 43: 34, 44: 35,
    45: "Je termine par les apports du projet, ses limites et les perspectives.",
    46: 36, 47: 37, 48: 38,
}


def old_notes():
    md = open(os.path.join(ROOT, "livrables", "Notes_presentateur.md"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^## Slide (\d+) — .*?\n\n(.*?)\n\n", md, re.S | re.M):
        out[int(m.group(1))] = m.group(2).strip()
    return out, md


def main():
    built = build()
    old, md = old_notes()
    titles = {}
    for p in built:
        note = NOTES[p.n]
        note = old[note] if isinstance(note, int) else note
        p.number().notes(note)
        titles[p.n] = note
    json.dump({p.n: p.ops for p in built}, open(os.path.join(ROOT, "canva_assets", "ops.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    if len(sys.argv) == 3:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        ops = [o for p in built if a <= p.n <= b for o in p.ops]
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(ops, ensure_ascii=False, separators=(",", ":")))
    else:
        print({p.n: len(p.ops) for p in built})
    return titles, md


if __name__ == "__main__":
    main()
