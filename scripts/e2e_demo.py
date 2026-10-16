"""End-to-end check of the evaluation chain with demo data and REAL models.

Runs the FastAPI app in-process against a temporary SQLite database (the
development database is never touched) with the production checkpoint and the
versioned score calibration:

  register -> create offer -> evaluate a strong / weak / DOCX CV -> history ->
  detail -> overview -> PDF export -> isolation of a second recruiter.

The CVs and the offer below are fictitious demo texts written for this check.
Usage: python scripts/e2e_demo.py
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = Path(tempfile.mkdtemp(prefix="jobtest_e2e_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TMP / 'e2e.db').as_posix()}"
os.environ.setdefault("LLM_ENABLED", "false")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

JOB = {
    "title": "Data Engineer (demo)",
    "description": ("We are hiring a data engineer to build batch and streaming pipelines. "
                    "Required: Python, SQL, Apache Airflow, Apache Spark, Docker. "
                    "Nice to have: Kafka, AWS, dbt. Team work and communication matter."),
    "required_skills": "python, sql, airflow, spark, docker",
}
STRONG_CV = ("PROFILE\nData engineer with 5 years of experience building ETL pipelines.\n\n"
             "EXPERIENCE\n2021-2026 Data Engineer: designed Airflow DAGs and Spark jobs in Python, "
             "modelled data in SQL and dbt, packaged services with Docker, streamed events with Kafka on AWS.\n\n"
             "SKILLS\nPython, SQL, Apache Airflow, Apache Spark, Docker, Kafka, AWS, dbt\n\n"
             "SOFT SKILLS\nteamwork, communication")
WEAK_CV = ("PROFILE\nGraphic designer with 3 years of experience in branding.\n\n"
           "EXPERIENCE\n2022-2025 Designer: produced visual identities and print layouts.\n\n"
           "SKILLS\nAdobe Illustrator, Photoshop, InDesign, typography, colour theory")
PARTIAL_CV = ("PROFILE\nBackend developer with 4 years of experience.\n\n"
              "EXPERIENCE\n2022-2026 Backend developer: REST APIs in Python with Django and PostgreSQL, "
              "SQL optimisation, Docker deployments.\n\n"
              "SKILLS\nPython, Django, PostgreSQL, SQL, Docker, Git")


def main() -> dict:
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    out: dict = {"database": os.environ["DATABASE_URL"]}

    def login(prefix: str) -> dict:
        email = f"{prefix}_{uuid.uuid4().hex[:6]}@demo.test"
        client.post("/api/v1/auth/register", json={"email": email, "password": "demo-password-1", "full_name": "Demo"})
        token = client.post("/api/v1/auth/login", data={"username": email, "password": "demo-password-1"}).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    a = login("recruiter_a")
    job_id = client.post("/api/v1/ui/job-offers", json=JOB, headers=a).json()["id"]

    evaluations = {}
    stuffed = WEAK_CV + "\n\nSKILLS\ndocker, spark, python, airflow, sql, kafka, aws, dbt"
    for name, cv in (("strong", STRONG_CV), ("partial", PARTIAL_CV), ("weak", WEAK_CV), ("stuffed", stuffed)):
        r = client.post("/api/v1/ui/evaluate", json={"cv_text": cv, "job_offer_id": job_id,
                                                     "candidate_name": f"Demo {name}"}, headers=a)
        assert r.status_code == 200, r.text
        body = r.json()
        evaluations[name] = body
        out[f"evaluate_{name}"] = {
            "raw_score": body["result"]["raw_score"],
            "displayed_score": body["result"]["percentage"],
            "calibration_version": body["result"]["calibration_version"],
            "decision": body["decision"]["decision"],
            "explanation_decision": body["explanation"]["hiring_recommendation"]["decision"],
            "components": body["result"]["component_scores"],
        }

    from docx import Document
    doc = Document()
    for line in STRONG_CV.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    r = client.post("/api/v1/ui/evaluate/file", data={"job_offer_id": str(job_id), "candidate_name": "Demo docx"},
                    files={"cv_file": ("demo_cv.docx", buf.getvalue(),
                                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                    headers=a)
    assert r.status_code == 200, r.text
    out["evaluate_docx"] = {"displayed_score": r.json()["result"]["percentage"], "decision": r.json()["decision"]["decision"]}

    rows = client.get("/api/v1/ui/matches", headers=a).json()
    out["history"] = [{k: row[k] for k in ("candidate_name", "final_score", "score_raw", "decision",
                                           "calibration_version", "legacy_scale",
                                           "potential_fit_threshold", "strong_fit_threshold")} for row in rows]
    by_name = {row["candidate_name"]: row for row in rows}
    for name, body in evaluations.items():
        row = by_name[f"Demo {name}"]
        assert row["decision"] == body["decision"]["decision"]
        assert abs(row["final_score"] * 100 - body["result"]["percentage"]) < 0.06
        detail = client.get(f"/api/v1/ui/matches/{row['id']}", headers=a).json()
        assert detail["decision"] == row["decision"]
    out["overview"] = client.get("/api/v1/ui/overview", headers=a).json()

    # Keyword-stuffed CV: HIRE must be withheld consistently in API, history and PDF.
    st = evaluations["stuffed"]
    rec = st["explanation"]["hiring_recommendation"]
    assert st["decision"]["decision"] != "HIRE" and rec["decision"] == st["decision"]["decision"]
    r = client.post("/api/v1/report/pdf", json={"result": st["result"], "explanation": st["explanation"],
                                                "recommendations": st["recommendations"],
                                                "candidate_name": "Demo stuffed", "job_title": JOB["title"]}, headers=a)
    from PyPDF2 import PdfReader
    stuffed_pdf = " ".join(" ".join((p.extract_text() or "").split()) for p in PdfReader(io.BytesIO(r.content)).pages)
    out["stuffed_check"] = {"decision": st["decision"]["decision"], "evidence_gap": rec.get("evidence_gap"),
                            "declared_only": (rec.get("evidence") or {}).get("declared_only_skills"),
                            "history_decision": by_name["Demo stuffed"]["decision"],
                            "pdf_mentions_decision": st["decision"]["decision"] in stuffed_pdf}

    strong = evaluations["strong"]
    r = client.post("/api/v1/report/pdf", json={"result": strong["result"], "explanation": strong["explanation"],
                                                "recommendations": strong["recommendations"],
                                                "candidate_name": "Demo strong", "job_title": JOB["title"]}, headers=a)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    pdf_path = TMP / "demo_report.pdf"
    pdf_path.write_bytes(r.content)
    from PyPDF2 import PdfReader
    text = " ".join(" ".join((p.extract_text() or "").split()) for p in PdfReader(str(pdf_path)).pages)
    out["pdf"] = {"bytes": len(r.content), "path": str(pdf_path),
                  "mentions_calibration_version": strong["result"]["calibration_version"] in text,
                  "mentions_decision": strong["decision"]["decision"] in text}

    b = login("recruiter_b")
    out["isolation"] = {
        "b_evaluate_on_a_job": client.post("/api/v1/ui/evaluate", json={"cv_text": STRONG_CV, "job_offer_id": job_id},
                                           headers=b).status_code,
        "b_history_size": len(client.get("/api/v1/ui/matches", headers=b).json()),
        "b_detail_of_a_match": client.get(f"/api/v1/ui/matches/{rows[0]['id']}", headers=b).status_code,
    }
    assert out["isolation"] == {"b_evaluate_on_a_job": 404, "b_history_size": 0, "b_detail_of_a_match": 404}
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, default=str))
