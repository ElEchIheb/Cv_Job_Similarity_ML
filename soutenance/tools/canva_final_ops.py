"""Edit operations that turn the 24 kept pages of DAHXP_jZ7rA into the final defense deck (2026-10-11).

Every figure comes from the final thesis / verified results: macro-F1 0.740 [0.720-0.760] (synthetic
3-class test, 1 800 pairs), 0.154 before calibration, TF-IDF 0.746, paired difference -0.006
[-0.028; 0.016]; probes P1 0/0/200 -> 133/67/0; fictitious PDFs 3/2/13; own CVs CONSIDER 62.5 / 63.6;
pytest 174 passed / 1 skipped; Azure demo of 2026-09-13 (previous engine, not redeployed).
Usage: python canva_final_ops.py <design_content.json>  -> writes final_ops_<batch>.json
"""
import json
import os
import sys

FOOT = "  ·  JobTest — PFE 2025/2026"
ASSET = {
    "pipeline": "MAHXvvMwuZ0", "classes": "MAHXvr-AnL0", "uc": "MAHXvmx7hdc", "results": "MAHXviTYCkE",
    "score": "MAHXvs6Zw3E", "evidence": "MAHXviTbh8A", "deep": "MAHXvlSwf10", "result": "MAHXvqFQcnQ",
    "ranking": "MAHXvsiuYLg",
}
# current position (after the page deletion) -> final position
ORDER = [1, 3, 4, 5, 6, 8, 7, 9, 10, 11, 2, 17, 15, 16, 18, 12, 13, 14, 19, 21, 20, 23, 22, 24]

design = json.load(open(sys.argv[1], encoding="utf-8"))
pages = design["design_content"]["pages"]


def flat(els):
    for e in els:
        yield e
        for k in ("children", "elements"):
            yield from flat(e.get(k) or [])


class P:
    def __init__(self, cur):
        self.page = pages[cur - 1]
        self.id = self.page["id"]
        self.final = ORDER.index(cur) + 1
        self.ops = []

    def loc(self, suf):
        e = next(e for e in flat(self.page["elements"]) if e["id"].endswith(suf))
        return f"{self.id}-{e['id']}"

    def t(self, suf, text, **fmt):
        self.ops.append({"type": "replace_text", "locator_id": self.loc(suf), "text": text})
        if fmt:
            self.ops.append({"type": "format_text", "locator_id": self.loc(suf), "formatting": fmt})
        return self

    def w(self, suf, width):
        self.ops.append({"type": "resize_element", "locator_id": self.loc(suf), "width": width})
        return self

    def pos(self, suf, left, top):
        self.ops.append({"type": "position_element", "locator_id": self.loc(suf), "left": left, "top": top})
        return self

    def img(self, suf, asset, left, top, width, height, alt):
        lid = self.loc(suf)
        self.ops += [
            {"type": "update_fill", "locator_id": lid, "asset_type": "image", "asset_id": ASSET[asset], "alt_text": alt},
            {"type": "resize_element", "locator_id": lid, "width": width, "height": height},
            {"type": "position_element", "locator_id": lid, "left": left, "top": top},
        ]
        return self

    def rm(self, *sufs):
        self.ops += [{"type": "delete_element", "locator_id": self.loc(s)} for s in sufs]
        return self

    def num(self, suf):
        return self.t(suf, f"{self.final}{FOOT}")

    def notes(self, text):
        self.ops.append({"type": "replace_speaker_notes", "page_id": self.id, "notes": text})
        return self


def build():
    out = []
    # 1 cover
    p = P(1).t("B1qwP", "Réalisé par : Iheb EL ECH")
    p.t("rSZjm", "Encadrant académique : Dr. Aymen LOUATI\nEncadrante professionnelle : Dr. Emna TRABELSI",
        font_size=30).w("rSZjm", 1150).pos("rSZjm", 165, 930)
    p.notes("JobTest : une plateforme d'aide au recrutement qui rapproche un CV et une offre, explique son "
            "résultat et laisse la décision au recruteur.")
    out.append(p)
    # 2 context and problem
    p = P(3).t("YVQTS", "Contexte et problématique", font_size=58).w("YVQTS", 900).num("xN3g7")
    p.t("6ShXm", "CV hétérogènes, offres en langage libre : le premier tri est long et difficile à justifier.")
    p.t("n3bMZ", "Comment évaluer un CV face à une offre de façon explicable, reproductible et traçable…")
    p.t("1L7Dq", "…sans déléguer la décision d'embauche ?")
    p.notes("Le besoin vient de CyberCloud Solutions. Les outils du marché documentent peu leur logique de "
            "correspondance ; je cherche une aide structurée, pas une décision automatique.")
    out.append(p)
    # 3 objectives
    p = P(4).t("JpS4k", "Objectifs et périmètre").num("3Ncnn")
    p.notes("Huit objectifs. Hors périmètre : décision d'embauche autonome, portail candidat, apprentissage sur "
            "des embauches réelles.")
    out.append(p)
    # 4 needs
    p = P(5).t("DPJQy", "Besoins du recruteur").num("W7kSN")
    p.notes("Un seul acteur métier, le recruteur authentifié. Le candidat est une entité gérée, jamais un "
            "utilisateur de la plateforme.")
    out.append(p)
    # 5 use cases
    p = P(6).img("QrNB0", "uc", 640, 70, 1180, 811, "Diagramme global des cas d'utilisation de JobTest")
    p.num("HSl1v").notes("Le visiteur crée un compte et s'authentifie ; le recruteur gère offres et candidats, "
                         "évalue, classe, consulte l'historique, exporte le PDF. L'analyse approfondie étend "
                         "la consultation d'un résultat.")
    out.append(p)
    # 6 architecture
    p = P(8).num("D05Dw").notes("Nginx est le seul point d'entrée ; Next.js, FastAPI, PostgreSQL et Ollama "
                                "restent sur le réseau Docker interne.")
    out.append(p)
    # 7 data model
    p = P(7).img("TsB6l", "classes", 560, 60, 1254, 940, "Diagramme de classes métier de JobTest")
    p.num("PhR4X").notes("MatchResult est l'élément de traçabilité : score calibré, score brut, version de "
                         "calibration, seuils, sous-scores, méthode et version du modèle.")
    out.append(p)
    # 8 evaluation chain
    p = P(9).t("gJZBZ", "Chaîne d'évaluation d'un CV").w("gJZBZ", 1450).num("DwhVP")
    p.img("M6Pxl", "pipeline", 150, 330, 1620, 290, "Chaîne d'évaluation finale de JobTest")
    p.notes("Le contrôle des preuves intervient avant le calcul ; la calibration transforme le score brut "
            "en score sur 100 avant la décision. La couche 2 commente un résultat déjà calculé.")
    out.append(p)
    # 9 the three signals
    p = P(10).num("zssqB").t("yw5FS", "Compétences : dictionnaire versionné, démontrées ou seulement déclarées")
    p.notes("Une compétence seulement listée compte pour moitié ; une compétence niée ne compte pas.")
    out.append(p)
    # 10 fusion, calibration, verdict
    p = P(11).t("kljN0", "Fusion, calibration et verdict", font_size=70).w("kljN0", 1000)
    p.t("vRnsN", "Score brut 0–1", font_size=46)
    p.t("Dkmcg", "Affiché : score calibré /100\nHIRE ≥ 75  ·  CONSIDER ≥ 55  ·  REJECT", font_size=30)
    p.pos("Dkmcg", 1090, 895)
    p.img("Wdr79", "score", 1130, 300, 720, 549, "Score calibré et verdict affichés par JobTest")
    p.num("prqCb").notes("Le score brut n'a pas d'échelle naturelle. Une calibration versionnée, apprise sur la "
                         "validation synthétique, le ramène sur 100 ; elle plafonne à 100 au-delà de 0,613. "
                         "Les seuils 55 et 75 s'appliquent au score calibré.")
    out.append(p)
    # 11 evidence check (former benchmark page)
    p = P(2).t("nG21C", "Contrôle des preuves").num("B5bSz")
    p.img("8f38g", "evidence", 120, 250, 1120, 630, "Contrôle des preuves : verdict limité à CONSIDER")
    p.t("pW1Vf", "CV hors sujet + exigences de l'offre recopiées\n\nSans contrôle : 200 HIRE sur 200\n"
                 "Avec contrôle : 0 HIRE (133 REJECT, 67 CONSIDER)\n\nValidation synthétique, 200 paires\n"
                 "Limite : une expérience inventée mais rédigée passe encore", font_size=28)
    p.w("pW1Vf", 560).pos("pW1Vf", 1290, 300)
    p.notes("Le bourrage de mots-clés donnait HIRE presque à coup sûr. Texte recopié ignoré, négations retirées, "
            "compétence seulement déclarée pondérée à 0,5, et HIRE plafonné à CONSIDER si moins de la moitié des "
            "compétences sont démontrées. Sur les paires authentiques, aucun verdict ne change.")
    out.append(p)
    # 12 explanation + local deep analysis (interface layout)
    p = P(17).t("vR8yz", "Explication et analyse locale").t("ktBCh", "qwen2.5:1.5b via Ollama\nConsultative : ne "
                                                             "change ni le score ni le verdict", font_size=30)
    p.img("wHzsq", "deep", 620, 186, 1259, 708, "Analyse approfondie générée localement")
    p.notes("Forces, écarts et actions viennent du calcul déterministe. La couche 2 locale produit synthèse, "
            "signaux et questions d'entretien ; un contrôle de cohérence l'empêche de contredire le verdict.")
    out.append(p)
    # 13 stack
    p = P(15).num("vktgg").notes("Next.js et FastAPI, SQLAlchemy avec SQLite en local et PostgreSQL en conteneur, "
                                 "Ollama pour la couche 2, Docker Compose et Nginx pour le déploiement.")
    out.append(p)
    # 14 real flow
    p = P(16).t("ZmYKX", "Parcours réel").t("YcWqn", "Version finale, données fictives : score /100, verdict, "
                                                      "sous-scores bruts", font_size=30)
    p.img("MbLLn", "result", 620, 186, 1259, 708, "Résultat d'une évaluation dans la version finale")
    p.notes("Capture locale de la version finale. Score brut 0,653, au-dessus du plafond de calibration : "
            "affiché 100 alors que 8 compétences sur 11 sont reconnues. La justification signale TypeScript à vérifier.")
    out.append(p)
    # 15 ranking + quality center
    p = P(18).t("SfHjD", "Classement et Quality Center").t("tJKgP", "18 CV fictifs classés ; métriques lues "
                                                           "dans les fichiers versionnés", font_size=30)
    p.img("wBGKl", "ranking", 620, 186, 1259, 708, "Classement multi-CV et AI Quality Center")
    p.rm("Ltnqh")
    p.notes("Le classement départage les égalités à 100 par le score brut. Le Quality Center sépare F1 binaire "
            "et macro-F1, donne la source de chaque chiffre et affiche « non mesuré » pour mes propres CV.")
    out.append(p)
    # 16 protocol and data provenance
    p = P(12).t("qhK2f", "Protocole et provenance des données", font_size=60).num("5qT90")
    p.t("zmplD", "Trois sources ; une seule porte des métriques")
    p.t("xdl2F", "Synthétique : 12 000 paires, graine 42, 8 400 / 1 800 / 1 800")
    p.t("rJgwh", "18 CV fictifs en PDF : essais de classement, sans étiquettes")
    p.t("hRFG0", "Mes propres CV face à des offres réelles : essais qualitatifs")
    p.notes("Ancrages de calibration choisis sur la validation ; test isolé non utilisé pour régler quoi que ce "
            "soit, mais consulté plusieurs fois au cours du projet.")
    out.append(p)
    # 17 quantitative results
    p = P(13).t("WHVW9", "Résultats sur le test synthétique").w("WHVW9", 1500).num("LFs7R")
    p.img("nXDvt", "results", 150, 290, 1600, 465, "Verdicts affichés sur le test synthétique isolé")
    p.t("sVXkV", "Macro-F1 à 3 classes : 0,740 pour la version livrée, contre 0,154 avant calibration", font_size=30)
    p.pos("sVXkV", 150, 800)
    p.t("Q0TRY", "Pas de différence démontrée avec TF-IDF seul (écart −0,006, IC 95 % [−0,028 ; 0,016]). "
                 "Corpus synthétique : ce n'est pas une performance sur des CV réels.", font_size=26)
    p.pos("Q0TRY", 150, 870)
    p.notes("Le macro-F1 évalue les verdicts REJECT / CONSIDER / HIRE contre les classes du générateur. Il ne se "
            "compare pas au F1 binaire du score brut (0,93). La classe intermédiaire reste la plus difficile (F1 0,59).")
    out.append(p)
    # 18 functional trials
    p = P(14).t("kTCHb", "Essais fonctionnels").num("tbZCp")
    p.t("T2SKv", "Aucun jugement de recruteur : aucun F1 n'en est tiré")
    p.t("kBlhg", "18 CV fictifs en PDF : 3 HIRE · 2 CONSIDER · 13 REJECT")
    p.t("1rBKv", "Mes propres CV : parcours complet, verdict CONSIDER (62,5 et 63,6)")
    p.t("FMgP9", "Un profil de reconversion bien rédigé obtient HIRE : l'expérience n'est pas vérifiable")
    p.notes("Les niveaux des CV fictifs sont des niveaux de qualité générale que j'ai fixés, pas une adéquation à "
            "l'offre. Mes deux CV tracés recevaient REJECT avec l'ancienne version du moteur.")
    out.append(p)
    # 19 tests
    p = P(19).t("wPPLM", "Tests et validation").num("sB0bV")
    p.t("mvz7P", "Logique applicative et parcours de bout en bout")
    p.t("2GdsH", "pytest : 174 réussis, 0 échec, 1 ignoré")
    p.t("wcDPh", "Accès, calibration, preuves, cohérence API · historique · PDF")
    p.t("wTxYJ", "Parcours complet rejoué avec les modèles réels")
    p.notes("Les tests unitaires remplacent les embeddings par un substitut déterministe : ils vérifient la "
            "logique, pas la qualité prédictive, mesurée par le banc d'essai.")
    out.append(p)
    # 20 security and deployment
    p = P(21).t("PcWtx", "Sécurité et déploiement").num("jccPR")
    p.t("RLSzc", "Nginx, seul point d'entrée\n5 conteneurs Docker\nPorts métier non exposés\n"
                 "JWT, bcrypt, cloisonnement par recruteur\nVM Azure D2as_v7 : 2 vCPU, 8 Gio", font_size=32)
    p.notes("Un recruteur ne voit que ses offres, candidats et résultats : une ressource d'un autre compte "
            "répond 404.")
    out.append(p)
    # 21 Azure demonstration and observed limits
    p = P(20).t("7hZxb", "Démonstration Azure").num("VgbbN")
    p.t("pDHDS", "13 septembre 2026 · version antérieure du moteur, non redéployée")
    p.t("V6W8M", "5 conteneurs sains, parcours complet servi par Nginx")
    p.t("fVkzv", "Couche 2 sur CPU : 54,3 s par analyse")
    p.t("ynYnD", "HTTP sans TLS, VM unique, pas de sauvegarde automatisée")
    p.notes("Les captures Azure du mémoire documentent cette démonstration historique ; les écrans montrés "
            "aujourd'hui viennent de l'instance locale de la version finale.")
    out.append(p)
    # 22 limits
    p = P(23).t("7BKVH", "Limites").num("hpr5L")
    p.t("qdGdP", "Métriques internes à un corpus synthétique ; calibration apprise sur ses étiquettes")
    p.t("vhrR1", "Expérience décrite non vérifiable par le texte\nAucune annotation par des recruteurs\n"
                 "Démonstration en HTTP sur une VM unique")
    p.notes("Le système n'est pas validé pour de vraies décisions de recrutement.")
    out.append(p)
    # 23 perspectives and conclusion
    p = P(22).t("8WBjk", "Perspectives", font_size=64).num("0rJ9s")
    p.t("wL9pz", "Un prototype fonctionnel et traçable : du CV au verdict expliqué, sans décision automatique")
    p.t("mW1X6", "Corpus réel annoté avec des recruteurs\nCalibration réapprise, étude des biais\n"
                 "TLS, sauvegardes et supervision")
    p.notes("La priorité est de réapprendre la calibration sur des données réelles annotées, avec des recruteurs.")
    out.append(p)
    # 24 thanks
    p = P(24).rm("cLlGZ").notes("Merci. Questions.")
    out.append(p)

    # reorder pages to the final order
    reorder = []
    ids = [pages[c - 1]["id"] for c in ORDER]
    for i in range(1, len(ids)):
        reorder.append({"type": "reorder_page", "page_id": ids[i], "anchor_page_id": ids[i - 1], "position": "after"})
    return out, reorder


if __name__ == "__main__":
    pages_ops, reorder = build()
    here = os.path.dirname(os.path.abspath(sys.argv[1]))
    batches = [pages_ops[0:8], pages_ops[8:16], pages_ops[16:24]]
    for i, b in enumerate(batches, 1):
        ops = [o for p in b for o in p.ops]
        json.dump(ops, open(os.path.join(here, f"final_ops_{i}.json"), "w", encoding="utf-8"), ensure_ascii=False)
        print(i, len(ops))
    json.dump(reorder, open(os.path.join(here, "final_ops_reorder.json"), "w", encoding="utf-8"))
    print("reorder", len(reorder))
