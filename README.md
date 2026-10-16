# Systeme hybride de matching CV / offre

Ce depot contient un pipeline end-to-end pour parser des CV, extraire les competences, calculer plusieurs scores de matching, fusionner ces scores, expliquer le resultat et exposer le tout via une API FastAPI et une interface Streamlit.

## Structure

- `src/parsing`: parsing PDF/DOCX, nettoyage, segmentation de CV
- `src/nlp`: extraction hybride de competences
- `src/models`: matchers TF-IDF, embeddings et skill-based
- `src/fusion`: fusion hybride et optimisation des poids
- `src/explainability`: explications et recommandations
- `src/evaluation`: evaluation complete, statistiques et figures
- `src/api`: API REST FastAPI
- `frontend`: dashboard Streamlit
- `data/datasets`: dictionnaire de competences, generateur et dataset CSV

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Generation du dataset

```bash
python data/datasets/generate_dataset.py
```

Le script genere `data/datasets/cv_job_dataset.csv`, imprime la distribution des labels et couvre 10 domaines IT.

## Lancer l'API

```bash
uvicorn src.api.main:app --reload
```

Documentation Swagger: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

## Lancer le frontend

Le frontend actuel est l'application **Next.js dans `web/`** (voir sa doc).

> **`frontend/` (Streamlit) — DEPRECATED — superseded by the Next.js app in
> `web/`. Kept for reference only, not maintained.** Exclu des tests/CI de
> routine. Ne pas y développer de nouvelles fonctionnalités.

## Couche 2 — Analyse LLM locale (Ollama, optionnelle)

JobTest ajoute une seconde couche de _raisonnement qualitatif_ par LLM local,
en plus du moteur statistique. Elle est **additive et optionnelle** : si Ollama
n'est pas lancé, le score et la décision fonctionnent exactement comme avant.

```bash
# 1. Installer Ollama : https://ollama.com/download
ollama serve                 # démarrer le serveur (souvent auto-démarré)
ollama pull qwen2.5:1.5b    # modèle par défaut vérifié (~1 Go téléchargé, CPU/8 Go RAM)
curl http://localhost:11434/api/tags   # vérifier
```

Variables (facultatives, valeurs par défaut saines) : `OLLAMA_MODEL`,
`OLLAMA_BASE_URL`, `OLLAMA_TIMEOUT`, `LLM_ENABLED`. Vérification bout-en-bout :

```bash
python scripts/verify_deep_analysis.py
```

Architecture détaillée, choix du modèle, prompt et méthodologie d'évaluation :
voir [`LLM_LAYER.md`](LLM_LAYER.md).

## Evaluation

```bash
python -c "from src.evaluation.evaluator import EvaluationSuite; EvaluationSuite().run_full_evaluation('data/datasets/cv_job_dataset.csv')"
```

Les resultats sont sauvegardes dans `evaluation/results/` et les figures dans `evaluation/figures/`.

## Tests

```bash
pytest
```

## Remarques pratiques

- Les modules NLP lourds sont optionnels a l'execution. Si `spaCy` ou `sentence-transformers` ne sont pas installes, des fallbacks locaux sont utilises.
- Pour une utilisation en production, il est recommande d'installer les modeles spaCy et les poids `sentence-transformers`.
- `docker-compose up --build` permet de lancer l'API et le frontend ensemble.

## Repères rapides pour la soutenance

### Parcours d'une évaluation

- Interface d'évaluation : [web/app/(dashboard)/analysis/page.tsx](web/app/%28dashboard%29/analysis/page.tsx)
- Client HTTP du frontend : [web/lib/api/client.ts](web/lib/api/client.ts)
- Routes utilisées par l'interface : [src/api/routers/ui.py](src/api/routers/ui.py)
- Service central de calcul et de sauvegarde : [src/matching/service.py](src/matching/service.py)
- Extraction du texte PDF/DOCX : [src/parsing/parser.py](src/parsing/parser.py)

### Moteur intelligent

- TF-IDF : [src/models/tfidf_model.py](src/models/tfidf_model.py)
- Similarité sémantique / embeddings : [src/models/embedding_model.py](src/models/embedding_model.py)
- Extraction des compétences : [src/nlp/skill_extractor.py](src/nlp/skill_extractor.py)
- Dictionnaire des compétences : [data/datasets/skills_dictionary.json](data/datasets/skills_dictionary.json)
- Score des compétences : [src/models/skill_matcher.py](src/models/skill_matcher.py)
- Fusion des trois scores et pondérations : [src/fusion/hybrid_scorer.py](src/fusion/hybrid_scorer.py)
- Contrôle des preuves, copies et négations : [src/nlp/screening.py](src/nlp/screening.py)
- Calibration du score sur 100 : [src/decisioning/calibration.py](src/decisioning/calibration.py)
- Paramètres de calibration : [models/checkpoints/score_calibration.json](models/checkpoints/score_calibration.json)
- Verdicts HIRE / CONSIDER / REJECT : [src/decisioning/decision_engine.py](src/decisioning/decision_engine.py)
- Explications et recommandations : [src/explainability/explainer.py](src/explainability/explainer.py)
- Chargement du moteur : [src/models/model_loader.py](src/models/model_loader.py)

### Analyse approfondie

- Instructions données à Qwen : [src/ai/prompts/deep_analysis_prompt.py](src/ai/prompts/deep_analysis_prompt.py)
- Appel à Ollama et contrôle de la réponse : [src/ai/llm_reasoning.py](src/ai/llm_reasoning.py)
- Affichage de l'analyse : [web/components/analysis/DeepAnalysis.tsx](web/components/analysis/DeepAnalysis.tsx)

### Application et données

- Application FastAPI et routes générales : [src/api/main.py](src/api/main.py)
- Inscription et connexion : [src/api/routers/auth.py](src/api/routers/auth.py)
- JWT et hachage des mots de passe : [src/security/auth.py](src/security/auth.py)
- Tables et relations de la base : [src/models_db.py](src/models_db.py)
- Connexion à la base : [src/database.py](src/database.py)
- Génération du rapport PDF : [src/reporting/pdf_generator.py](src/reporting/pdf_generator.py)
- AI Quality Center : [web/app/(dashboard)/quality/page.tsx](web/app/%28dashboard%29/quality/page.tsx)
- Résultats du benchmark : [evaluation/results/](evaluation/results/)
- Figures du benchmark : [evaluation/figures/](evaluation/figures/)

### Validation et déploiement

- Tests automatisés : [tests/](tests/)
- Essais avec des CV réels : [scripts/real_cv_trials.py](scripts/real_cv_trials.py)
- Génération des données synthétiques : [data/datasets/generate_dataset.py](data/datasets/generate_dataset.py)
- Services Docker : [docker-compose.yml](docker-compose.yml)
- Proxy HTTPS Caddy : [deploy/Caddyfile](deploy/Caddyfile)
- Image Docker de l'API : [Dockerfile.api](Dockerfile.api)
- Image Docker Next.js : [web/Dockerfile](web/Dockerfile)

### Rapport

- Rapport PDF : [main.pdf](ISI-LaTeX-Template-master/ISI-LaTeX-Template-master/main.pdf)
- Sources LaTeX : [dossier du rapport](ISI-LaTeX-Template-master/ISI-LaTeX-Template-master/)
