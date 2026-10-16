# Calibration du score et verdicts affichés — octobre 2026

Ce document résume la correction appliquée au moteur de JobTest. Il décrit le
diagnostic, le protocole, les résultats et les limites. Les chiffres proviennent des
fichiers de `evaluation/results/` cités entre parenthèses.

## 1. Diagnostic (avant correction)

Reproductible avec `python evaluation/diagnose_scoring.py` (`diagnostic_pre_fix.json`).

1. **Échelle incompatible avec les bornes métier.** Le score hybride (0,2 TF-IDF +
   0,4 embeddings + 0,4 compétences) était affiché `brut × 100` et lu contre 55 / 75.
   Ses composantes n'ont pas d'échelle commune : sur le test, la médiane de TF-IDF
   vaut 0,09 et son maximum 0,45 ; les embeddings vont de 0,30 à 0,83 ; les
   compétences atteignent au plus 0,67. Même en combinant les maxima observés de
   chaque composante, la fusion n'atteint que 0,69. Le seuil HIRE (75) était donc
   structurellement inaccessible. Sur les 1 800 paires de test : 1 777 REJECT,
   23 CONSIDER, 0 HIRE.
2. **Double conversion 0–1 / 0–100.** `DecisionEngine.to_percentage` traitait toute
   valeur de [0, 1] comme une fraction, alors que le service lui passait déjà un
   pourcentage. Un score de 0,9 % devenait 90 % et donnait HIRE. Avec la méthode
   TF-IDF, 76 paires de test sans recouvrement recevaient ainsi HIRE.
3. **Méthodes non hybrides lues sur la même grille.** Les embeddings dépassent 55 %
   pour 71 % des paires, alors que TF-IDF et compétences restent presque toujours
   sous 55.
4. **Incohérences d'affichage.**
   - La page AI Insights recalculait les bandes avec 75 / 55 codés en dur, sans tenir
     compte des seuils actifs.
   - Le PDF et l'interface présentaient une distance au seuil comme une
     « confiance » en pourcentage.
   - Le PDF colorait les sous-scores bruts selon les bandes de décision.
5. **Documents illisibles.** Un PDF corrompu provoquait une erreur 500 au lieu
   d'un refus 400.

Le checkpoint de production portait bien les poids enregistrés (0,2 / 0,4 / 0,4).
Le corpus ne présente aucune fuite par variante : chaque paire est générée
indépendamment (12 000 CV et 12 000 offres uniques). En revanche, l'étiquette du
générateur est définie par la proportion de compétences du CV recopiées dans l'offre
(75 % pour « fort », 45 % pour « transférable », 0 pour « sans rapport »). Ce choix
avantage mécaniquement les méthodes lexicales.

## 2. Correction

- `src/decisioning/calibration.py` : pour chaque méthode, une transformation
  monotone et linéaire par morceaux du score brut vers l'échelle affichée. Les
  ancrages sont 0 → 0, `cut_consider` → 55, `cut_hire` → 75 et `ceiling` → 100. Le
  classement des candidats ne change pas (AUC identique) et les sous-scores restent
  bruts.
- Les ancrages sont appris **sur la validation seule**. Le critère est le macro-F1 à
  trois classes : verdict REJECT / CONSIDER / HIRE comparé aux classes « sans
  rapport », « transférable » et « fort ».
- Le fichier versionné `models/checkpoints/score_calibration.json` décrit la
  calibration (version `synthetic-v1-2026-10-11-hybrid-documented`).
- Chaque résultat enregistre `score_raw`, `final_score` (score affiché / 100), la
  `calibration_version`, les seuils appliqués et la version du modèle
  (`hybrid-checkpoint-v3`).
- `DecisionEngine` attend désormais un pourcentage. La conversion d'une fraction
  passe par `from_fraction`, de façon explicite.
- **Anciens résultats** (`calibration_version` vide) : score et décision sont
  conservés tels quels. Ils sont marqués « Legacy scale » dans l'historique et exclus
  des moyennes, du taux de HIRE et du meilleur score par candidat.
- Le PDF, l'export CSV, AI Insights, l'AI Quality Center et les réglages
  affichent l'échelle, la version de calibration et les seuils appliqués.

## 3. Protocole et choix de la méthode

1. Sous-scores calculés une fois et mis en cache (`compute_components.py`). TF-IDF
   est appris sur l'apprentissage seul. Les scores du test recalculés coïncident
   exactement avec ceux du benchmark.
2. Sélection (`calibration_study.py select`), sur apprentissage et validation
   uniquement. Les poids de la fusion apprise sont ajustés sur 1 500 paires
   d'apprentissage. Le score de chaque candidat est un macro-F1 en validation croisée
   à cinq plis sur la validation.

   **Règle fixée avant de voir les résultats :** retenir le meilleur macro-F1 parmi
   les candidats dont le taux de rétrogradation sous réécriture par alias n'excède
   pas celui de l'hybride documenté de plus de 5 points.

| Candidat (validation) | Poids T / E / C | Macro-F1 CV | Rétrogradation alias |
|---|---|---|---|
| Hybride documenté | 0,20 / 0,40 / 0,40 | 0,739 | 1,9 % |
| Fusion apprise | 0,75 / 0,05 / 0,20 | **0,780** | 3,9 % |
| TF-IDF seul | 1 / 0 / 0 | 0,736 | 4,5 % |
| Compétences seules | 0 / 0 / 1 | 0,710 | 0,0 % |
| Embeddings seuls | 0 / 1 / 0 | 0,534 | 3,1 % |

3. Lecture unique du test (`calibration_study.py final`), puis tableaux
   comparatifs à paramètres figés (`calibration_report.py`).

**Décision produit.** La règle retenait la fusion apprise. Elle n'est **pas**
déployée par défaut, pour trois raisons :

- son gain mesuré provient d'étiquettes définies par le recouvrement de mots
  recopiés ;
- une pondération dominée par TF-IDF récompense la simple reprise du vocabulaire de
  l'offre : écart de 25,6 points documenté dans `BUGFIXES.md` (Bug 4) ;
- lors du test de bout en bout, un profil partiel rédigé librement obtenait HIRE avec
  la fusion apprise, mais CONSIDER avec l'hybride documenté.

Le produit garde donc l'hybride documenté, calibré sur la validation. Ce choix
n'optimise pas le test : sur le test, c'est la configuration la moins bonne des deux.
La calibration de la fusion apprise est conservée
(`score_calibration.fusion-learned.json`).

## 4. Résultats sur le test isolé synthétique (1 800 paires)

Répartition : 536 sans rapport (29,8 %), 545 transférables (30,3 %), 719 forts (39,9 %).

| Même score, mêmes paires | Macro-F1 3 classes [IC95] | F1 CONSIDER ou mieux | F1 HIRE | Kappa q. | REJECT / CONSIDER / HIRE |
|---|---|---|---|---|---|
| **Avant** : hybride, brut × 100, bornes 55/75 | 0,154 [0,146–0,163] | 0,036 | 0,000 | 0,012 | 1 777 / 23 / 0 |
| **Après** : hybride calibré, bornes 55/75 | **0,740 [0,720–0,760]** | 0,934 | 0,782 | 0,799 | 548 / 557 / 695 |
| TF-IDF calibré (comparaison) | 0,746 [0,726–0,765] | 0,950 | 0,758 | 0,797 | 471 / 641 / 688 |
| Fusion apprise calibrée (non déployée) | 0,780 [0,761–0,799] | 0,957 | 0,792 | 0,833 | 552 / 560 / 688 |

Matrice de confusion de l'« après » (lignes : classe vraie ; colonnes : verdict R / C / H) :

```
sans rapport   459   77    0
transférable    78  325  142
fort            11  155  553
```

Autres résultats :

- **Comparaison appariée** (bootstrap sur les mêmes paires, 2 000 tirages) :
  - hybride documenté − TF-IDF : −0,006, IC95 [−0,028 ; 0,016], donc pas de
    différence démontrée ;
  - fusion apprise − hybride documenté : +0,040, IC95 [0,022 ; 0,058].
- **Classe CONSIDER** : F1 de 0,59, la plus difficile ; elle est surtout confondue
  avec HIRE.
- **Paires multilingues** (CV en anglais, offre en français, n = 120) : exactitude
  0,65, contre 0,75 pour les paires françaises.
- **Domaines les plus faibles** : Blockchain (n = 42, macro-F1 0,63), jeux vidéo/AR
  (n = 92, 0,64). Ces effectifs sont faibles.
- **Robustesse aux alias** (test) : 0,8 % des verdicts rétrogradés.
- **Bourrage de mots-clés** (validation, `stuffing_probe.py`) : ajouter au CV la liste
  des compétences exigées par l'offre fait passer 99 % des profils sans rapport en
  HIRE avec l'hybride documenté. Il en va de même pour toutes les méthodes fondées
  sur les compétences ou les mots-clés.
- **Seuil expérimental 0,2636** (référence, inchangée) : F1 binaire 0,934 ; c'est une
  mesure de qualité du score, pas un verdict affiché.

## 5. Ce qui n'est pas démontré

- Aucune mesure sur données réelles : le dépôt n'en contient pas
  (voir `REAL_DATA_PROTOCOL.md`).
- Les bornes 55 / 75 sont alignées sur les classes d'un générateur synthétique. Ce
  n'est pas une politique d'embauche validée.
- Le système croit le CV sur parole : une liste de compétences recopiée suffit à
  obtenir HIRE. La lecture humaine et l'entretien restent indispensables.
- Les scores des CV rédigés librement occupent une plage différente de celle des
  textes synthétiques. Seuls trois cas de démonstration ont été observés, sans valeur
  statistique.

## 6. Contrôle des preuves (version `hybrid-checkpoint-v4`)

Le bourrage de mots-clés venait d'une extraction des compétences « en sac de mots » : une
liste recopiée comptait autant qu'une expérience décrite, une compétence niée était
comptée, et TF-IDF récompensait tout passage repris de l'offre. `src/nlp/screening.py`
ajoute trois contrôles, dont les paramètres ont été fixés a priori :

- les séquences d'au moins 8 mots consécutifs recopiées de l'offre sont retirées avant le
  calcul des trois composantes (sur le corpus, la plus longue séquence légitime compte
  7 mots) ;
- les mentions niées ne comptent pas comme compétences, et les propositions niées qui citent
  une compétence sont retirées du texte utilisé pour TF-IDF et les embeddings ;
- une compétence seulement déclarée dans une liste compte pour 0,5 ; une compétence citée
  dans l'expérience, les projets, le profil ou une certification est démontrée. HIRE devient
  CONSIDER si le CV recopie l'offre ou si moins de la moitié des compétences correspondantes
  sont démontrées.

Sur les 3 600 paires authentiques de validation et de test, ces changements ne modifient ni
les sous-scores ni les verdicts, et la règle de prudence ne se déclenche jamais. Les
résultats de la section 4 restent donc ceux de la version finale.

Sondes sur la validation (200 paires par scénario, `robustness_probes.py`) ; verdicts
REJECT / CONSIDER / HIRE, sans contrôle puis avec contrôle :

| Scénario | Sans contrôle | Version finale |
|---|---|---|
| Référence : profils sans rapport non modifiés | 174 / 25 / 1 | 174 / 25 / 1 |
| + liste d'exigences recopiée | 0 / 0 / 200 | 133 / 67 / 0 |
| + mêmes compétences réordonnées (section Compétences) | 0 / 0 / 200 | 0 / 200 / 0 |
| + offre entière collée | 0 / 0 / 200 | 174 / 26 / 0 |
| + mention niée des compétences | 0 / 0 / 200 | 175 / 24 / 1 |
| + compétences dans une phrase d'expérience | 0 / 0 / 200 | 0 / 0 / 200 (limite) |
| Référence : adéquations fortes non modifiées | 1 / 33 / 166 | 1 / 33 / 166 |
| Adéquation forte privée de la moitié de ses compétences | 15 / 129 / 56 | 15 / 129 / 56 |
| Adéquation forte allongée | 0 / 16 / 184 | 0 / 16 / 184 |

Limite ouverte : un CV qui affirme une expérience dans une phrase rédigée n'est pas
détecté.

Essais fonctionnels (aucune métrique, faute de jugements de référence) :

- 18 CV fictifs au format PDF face à une offre full-stack
  (`scripts/functional_trials.py`) : 3 HIRE, 2 CONSIDER, 13 REJECT ; historique et PDF
  cohérents.
- Deux CV personnels de l'étudiant, présents dans la base locale, rejoués avec la version finale : CONSIDER
  (62,5 et 63,6). Avec une version antérieure, ils avaient reçu REJECT.

## 7. Figures (AI Quality Center et mémoire)

`python evaluation/make_quality_figures.py` redessine les quatre figures d'évaluation à partir
de `results/calibration_report.json` et de `cache/components_test.csv` uniquement (rien n'est
ajusté). Le script vérifie d'abord que les sous-scores en cache reproduisent la matrice de
confusion du rapport, puis écrit la version anglaise dans `evaluation/figures/` (listée dans
`figures_manifest.json`, seules figures servies par `/ui/quality/figures`) et la version
française dans `img/ai/eval_*.png` du mémoire.

| Figure | Ce qu'elle mesure |
|---|---|
| matrice de confusion des verdicts | verdicts affichés (score calibré, 55 / 75) contre classes synthétiques |
| répartition des verdicts | avant calibration, hybride livré, TF-IDF calibré |
| ROC des scores bruts | qualité du classement de chaque score brut (binaire, sans seuil) |
| score brut de l'hybride par classe | distribution par classe et ancrages de calibration |

Les figures du benchmark du 2026-09-09 (matrices binaires au seuil expérimental, score brut
moyen par domaine, nuage embeddings / compétences, barres F1 sans libellés) sont conservées dans
`figures/archive_2026-09-09/` pour la traçabilité ; elles ne sont plus affichées.
