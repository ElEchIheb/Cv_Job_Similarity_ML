"""
scripts/verify_deep_analysis.py

End-to-end verification of NeuralHire's Layer 2 (LLM deep analysis) against a
REAL local Ollama server. Run this on a machine where Ollama is installed:

    ollama serve            # (if not already running)
    ollama pull llama3.2:3b
    python scripts/verify_deep_analysis.py

It runs Layer 1 (the real statistical engine) on the Alex Martin / Full Stack
Web Developer case, then feeds those results to Layer 2 and prints the actual
LLM output. If Ollama is unreachable it exits cleanly with setup instructions
(the point being: Layer 2 degrades gracefully, it never breaks Layer 1).

Override the model with OLLAMA_MODEL, e.g.:
    OLLAMA_MODEL=qwen2.5:3b python scripts/verify_deep_analysis.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # project root on path
warnings.filterwarnings("ignore")

# ── Test case ─────────────────────────────────────────────────────────────────
CV_TEXT = """Alex Martin — Full Stack Web Developer

EXPERIENCE
Full Stack Web Developer — TechSolutions, 2023-2026
Designed, developed, and maintained modern web applications with REST API
integration and relational databases. Collaborated in an agile team.

SKILLS
HTML, CSS, JavaScript, React, Node.js, Express, MongoDB, SQL, Git, REST API, Docker

SOFT SKILLS
Communication, teamwork, problem solving

EDUCATION
BSc Computer Science
"""

JOB_TEXT = """Full Stack Web Developer

We are looking for a developer to design, develop, and maintain modern web
applications, build REST API services, and work with relational databases.

Required skills: HTML, CSS, JavaScript, React, Node.js, Express, MongoDB, SQL,
Git, REST API, Docker.
"""


def build_layer1_evaluation() -> dict:
    """Run the real statistical engine. Falls back to a skill+explainer
    reconstruction if the heavy embedding model can't load in this environment
    (Layer 2 only needs the structured results, not the models)."""
    try:
        from src.models.model_loader import load_production_models
        from src.matching.service import run_evaluation
        models = load_production_models()
        payload = run_evaluation(models, CV_TEXT, JOB_TEXT, model_key="hybrid")
        # normalise decision object to dict for downstream consumers
        dec = payload["decision"]
        payload["decision"] = dec.as_dict() if hasattr(dec, "as_dict") else dec
        print("[Layer 1] Ran full production hybrid pipeline.")
        return payload
    except Exception as exc:  # noqa: BLE001
        print(f"[Layer 1] Full pipeline unavailable ({type(exc).__name__}: {exc}).")
        print("[Layer 1] Falling back to skill+explainer reconstruction.")
        from src.models.skill_matcher import SkillMatcher
        from src.explainability.explainer import MatchingExplainer
        det = SkillMatcher().predict_detailed(CV_TEXT, JOB_TEXT)
        pct = round((0.2 * 0.5 + 0.4 * 0.8 + 0.4 * det["score"]) * 100, 1)
        result = {
            "percentage": pct,
            "final_score": pct / 100.0,
            "component_scores": {"tfidf_score": 0.5, "embedding_score": 0.8, "skill_score": det["score"]},
            "skill_details": det,
        }
        explanation = MatchingExplainer().explain(CV_TEXT, JOB_TEXT, result)
        decision = {
            "decision": "HIRE" if pct >= 75 else "CONSIDER" if pct >= 55 else "REJECT",
            "band_label": explanation.get("hiring_recommendation", {}).get("band_label", ""),
        }
        return {"result": result, "explanation": explanation, "decision": decision}


def main() -> int:
    from src.config import settings
    from src.ai import llm_reasoning as L

    print("=" * 74)
    print(f"NeuralHire — Layer 2 verification  (model={settings.OLLAMA_MODEL}, "
          f"url={settings.OLLAMA_BASE_URL})")
    print("=" * 74)

    health = L.check_availability()
    print(f"[Ollama] available={health['available']}  models={health['models']}")
    if not health["available"]:
        print(f"[Ollama] {health['error']}")
        print("\nInstall/start Ollama then re-run. Layer 1 (scoring) is unaffected.")
        return 2

    evaluation = build_layer1_evaluation()
    stat = evaluation["result"]
    print(f"[Layer 1] score={stat['percentage']}%  decision={evaluation['decision']['decision']}  "
          f"coverage={evaluation['explanation'].get('skill_analysis', {}).get('skill_coverage')}")

    print("\n[Layer 2] Calling the LLM (this can take 10-60s on CPU)…")
    env = L.generate_deep_analysis(CV_TEXT, JOB_TEXT, evaluation)
    print(f"[Layer 2] status={env['status']}  latency={env['latency_ms']} ms")

    if env["status"] != "ok":
        print(f"[Layer 2] error: {env['error']}")
        return 1

    print("\n" + "-" * 74)
    print("ai_deep_analysis.analysis:")
    print("-" * 74)
    print(json.dumps(env["analysis"], indent=2, ensure_ascii=False))
    print("\nOK — real LLM output produced and schema-validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
