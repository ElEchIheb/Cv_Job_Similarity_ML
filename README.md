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

NeuralHire ajoute une seconde couche de *raisonnement qualitatif* par LLM local,
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

