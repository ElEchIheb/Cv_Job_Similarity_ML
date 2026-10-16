# Protocole minimal d'évaluation de JobTest sur données réelles

**État au 11 octobre 2026 : aucune évaluation sur données réelles n'a été réalisée.**
Le dépôt ne contient aucun jeu de CV et d'offres réels dont l'usage soit autorisé et
dont les étiquettes aient été établies par des recruteurs. Les 41 CV de la base
locale de démonstration n'ont ni étiquette ni provenance documentée : ils ne sont
pas utilisés.

Ce document décrit ce qu'il faut réunir pour mesurer honnêtement JobTest sur des
candidatures authentiques, et comment le script `evaluation/evaluate_real.py` les
exploite.

## 1. Ce que vous devez fournir

| Élément | Minimum | Recommandé | Pourquoi |
|---|---|---|---|
| Offres réelles distinctes | 8 | 15 ou plus | Le découpage se fait par offre : aucune offre n'apparaît à la fois dans la partie de réglage et dans la partie de test. |
| Paires CV–offre | 120 | 300 ou plus | Avec 60 paires de test, l'intervalle de confiance d'un F1 dépasse encore ±0,10. |
| Annotateurs (recruteurs) | 2 indépendants | 3 | Mesurer l'accord inter-annotateurs et départager les désaccords. |
| Répartition des étiquettes | au moins 20 paires par classe | — | Sans exemples HIRE, le seuil HIRE ne peut être ni réglé ni évalué. |

Autorisations à obtenir **avant** toute collecte :

1. un accord écrit de l'entreprise d'accueil (ou de l'organisme détenteur des CV)
   précisant la finalité : évaluation académique d'un outil d'aide à la présélection ;
2. une base légale au sens de la loi organique tunisienne n° 2004-63 sur la protection
   des données personnelles. Au choix : consentement explicite des candidats, ou
   anonymisation préalable effectuée par le détenteur des données, qui ne transmet
   que des textes anonymisés ;
3. la validation de l'encadrant académique ; un éventuel avis de l'INPDP si
   l'établissement l'exige ;
4. une durée de conservation définie (par exemple jusqu'à la soutenance), puis la
   suppression.

À ne pas utiliser : CV trouvés sur Internet ou sur des réseaux professionnels, CV de
proches sans consentement écrit, ou « vrais » CV fabriqués pour l'occasion.

## 2. Anonymisation (avant que les données n'atteignent le poste de développement)

- Supprimer nom, prénom, photo, courriel, téléphone, adresse, date de naissance,
  nationalité, situation familiale, liens de profils et identifiants.
- Remplacer les employeurs et écoles rares par une catégorie (« grande entreprise de
  télécommunications », « école d'ingénieurs publique ») lorsqu'ils permettent une
  réidentification.
- Conserver le contenu utile au rapprochement : intitulés, compétences, durées,
  technologies, langues.
- Attribuer un `pair_id` et un `job_id` opaques. La table de correspondance, si elle
  existe, reste chez le détenteur des données.

## 3. Annotation par les recruteurs

Chaque recruteur lit l'offre puis le CV anonymisé et choisit **une** étiquette, sans
voir le score de JobTest :

- **HIRE** : je convoquerais ce profil en entretien en priorité ;
- **CONSIDER** : profil à examiner, avec des réserves que je saurais formuler ;
- **REJECT** : je ne retiendrais pas ce profil pour cette offre.

Les deux annotations (`label_a`, `label_b`) sont faites indépendamment. Les
désaccords sont tranchés par discussion ou par un troisième annotateur
(`label_final`). L'accord est rapporté (kappa pondéré quadratique) : un kappa
inférieur à 0,4 signifie que la cible elle-même est mal définie, et aucun seuil ne
doit alors être « validé ».

## 4. Format et stockage

Fichier `data/real/pairs.csv` (répertoire exclu de Git) :

```
pair_id,job_id,cv_text,job_text,label_a,label_b,label_final
P001,J01,"<texte anonymisé>","<texte de l'offre>",CONSIDER,HIRE,HIRE
```

- Traitement uniquement local : le script n'appelle aucun service externe, et la
  couche LLM n'est pas sollicitée.
- Les sorties (`evaluation/results/real_eval.json`, également exclu de Git) ne
  contiennent que des agrégats, sans texte ni identifiant.
- Aucune capture d'écran ou extrait de ces CV ne doit figurer dans le mémoire.

## 5. Procédure de mesure (implémentée dans `evaluate_real.py`)

1. Calculer l'accord inter-annotateurs.
2. Découper par `job_id` en deux moitiés (réglage / test, graine 42) **avant**
   tout réglage, puis enregistrer l'affectation.
3. Scorer toutes les paires avec le modèle de production.
4. Sur la moitié test, rapporter :
   - les verdicts produits par la calibration actuelle (apprise sur données
     synthétiques) ;
   - les verdicts obtenus avec des bornes réapprises sur la seule moitié de réglage ;
   - la matrice de confusion 3×3, le macro-F1, le kappa et les intervalles bootstrap.
5. Conclure seulement si la moitié test compte au moins 60 paires et si chaque
   classe y est représentée.
6. Si la calibration réapprise est retenue, la versionner sous un nouveau nom (par
   exemple `real-v1-<date>`) en documentant sa provenance. Les résultats déjà
   enregistrés gardent la version avec laquelle ils ont été calculés.

## 6. Ce que cette évaluation ne mesurera toujours pas

Les étiquettes reflètent le jugement d'un ou deux recruteurs, pas la qualité d'une
embauche ni la performance future du candidat. Les biais (genre, âge, origine,
parcours atypiques) demandent une étude séparée, avec des attributs collectés de
manière licite et des effectifs suffisants.
