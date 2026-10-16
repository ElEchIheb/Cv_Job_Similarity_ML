"""Seed a running JobTest API with fictitious demo data for the thesis screenshots.

Run it against a server started on a THROWAWAY database (never the development
database, which holds the student's own test CVs):

    DATABASE_URL=sqlite:///<scratch>/jobtest_demo.db python -m uvicorn src.api.main:app --port 8000
    python scripts/seed_demo_screens.py [--api http://127.0.0.1:8000/api/v1]

Everything below is invented for the demonstration: recruiter account, offers,
candidate names (example.com addresses) and CV texts. The credentials are
test values for a local instance only.
"""
from __future__ import annotations

import argparse
import json
import sys

import requests

DEMO_EMAIL = "demo.recruiter@jobtest.test"
DEMO_PASSWORD = "Demo-Screens-2026!"
DEMO_NAME = "Demo Recruiter"

OFFERS = [
    {"title": "Full Stack Web Developer", "status": "OPEN",
     "description": ("We are looking for a Full Stack Web Developer to design, develop, and maintain modern web "
                     "applications. The candidate will work on both frontend and backend development, build REST "
                     "APIs, manage relational databases, and collaborate with the development team to deliver "
                     "scalable and high-quality software solutions."),
     "required_skills": "JavaScript, TypeScript, React, Node.js, Express.js, REST API, SQL, Git, Docker, HTML, CSS"},
    {"title": "Data Engineer", "status": "OPEN",
     "description": ("We are hiring a data engineer to build batch and streaming pipelines. "
                     "Required: Python, SQL, Apache Airflow, Apache Spark, Docker. "
                     "Nice to have: Kafka, AWS, dbt. Team work and communication matter."),
     "required_skills": "python, sql, airflow, spark, docker"},
    {"title": "Mobile Developer (Flutter)", "status": "ON_HOLD",
     "description": ("Build and maintain cross-platform mobile applications with Flutter and Dart, integrate REST "
                     "APIs and Firebase, write tests and publish releases to the stores."),
     "required_skills": "flutter, dart, firebase, rest api, git"},
    {"title": "DevOps Engineer", "status": "CLOSED",
     "description": ("Operate CI/CD pipelines and Kubernetes clusters on Azure, automate infrastructure with "
                     "Terraform and monitor services with Prometheus and Grafana."),
     "required_skills": "kubernetes, docker, terraform, azure, ci/cd, linux"},
]

# (offer index, candidate name, e-mail, CV text) — all fictitious.
EVALUATIONS = [
    (1, "Sara Lopez", "sara.lopez@example.com",
     "PROFILE\nData engineer with 5 years of experience building ETL pipelines.\n\n"
     "EXPERIENCE\n2021-2026 Data Engineer: designed Airflow DAGs and Spark jobs in Python, modelled data in SQL "
     "and dbt, packaged services with Docker, streamed events with Kafka on AWS.\n\n"
     "SKILLS\nPython, SQL, Apache Airflow, Apache Spark, Docker, Kafka, AWS, dbt\n\nSOFT SKILLS\nteamwork, communication"),
    (1, "Omar Haddad", "omar.haddad@example.com",
     "PROFILE\nBackend developer with 4 years of experience.\n\n"
     "EXPERIENCE\n2022-2026 Backend developer: REST APIs in Python with Django and PostgreSQL, SQL optimisation, "
     "Docker deployments.\n\nSKILLS\nPython, Django, PostgreSQL, SQL, Docker, Git"),
    (1, "Julia Novak", "julia.novak@example.com",
     "PROFILE\nGraphic designer with 3 years of experience in branding.\n\n"
     "EXPERIENCE\n2022-2025 Designer: produced visual identities and print layouts.\n\n"
     "SKILLS\nAdobe Illustrator, Photoshop, InDesign, typography, colour theory"),
    (1, "Leo Martin", "leo.martin@example.com",
     "PROFILE\nGraphic designer with 3 years of experience in branding.\n\n"
     "EXPERIENCE\n2022-2025 Designer: produced visual identities and print layouts.\n\n"
     "SKILLS\nPython, SQL, Apache Airflow, Apache Spark, Docker, Kafka, AWS, dbt, Adobe Illustrator"),
    (0, "Nina Rossi", "nina.rossi@example.com",
     "PROFILE\nFull stack developer with 4 years of experience building web applications.\n\n"
     "EXPERIENCE\n2022-2026 Full Stack Developer: built React and TypeScript front ends, Node.js and Express.js "
     "REST APIs backed by PostgreSQL (SQL), versioned with Git and shipped in Docker containers; "
     "responsive pages in HTML and CSS.\n\nSKILLS\nJavaScript, TypeScript, React, Node.js, Express.js, SQL, Git, Docker"),
    (0, "Adam Weber", "adam.weber@example.com",
     "PROFILE\nJunior frontend developer, 1 year of experience.\n\n"
     "EXPERIENCE\n2025-2026 Frontend intern: built pages in HTML, CSS and JavaScript, small React components.\n\n"
     "SKILLS\nHTML, CSS, JavaScript, React, Figma"),
]


def main(api: str) -> dict:
    s = requests.Session()
    r = s.post(f"{api}/auth/register", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": DEMO_NAME})
    if r.status_code not in (200, 201, 400, 409):
        r.raise_for_status()
    tok = s.post(f"{api}/auth/login", data={"username": DEMO_EMAIL, "password": DEMO_PASSWORD})
    tok.raise_for_status()
    s.headers["Authorization"] = f"Bearer {tok.json()['access_token']}"

    existing = {o["title"]: o["id"] for o in s.get(f"{api}/ui/job-offers").json()}
    ids = []
    for offer in OFFERS:
        if offer["title"] in existing:
            ids.append(existing[offer["title"]])
            continue
        resp = s.post(f"{api}/ui/job-offers", json=offer)
        resp.raise_for_status()
        ids.append(resp.json()["id"])

    out = []
    if not s.get(f"{api}/ui/matches").json():
        for idx, name, email, cv in EVALUATIONS:
            resp = s.post(f"{api}/ui/evaluate", json={"cv_text": cv, "job_offer_id": ids[idx],
                                                      "candidate_name": name, "candidate_email": email})
            resp.raise_for_status()
            b = resp.json()
            out.append({"candidate": name, "offer": OFFERS[idx]["title"], "score": b["result"]["percentage"],
                        "decision": b["decision"]["decision"]})
    return {"offers": dict(zip([o["title"] for o in OFFERS], ids)), "evaluations": out}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8000/api/v1")
    print(json.dumps(main(ap.parse_args().api), indent=2))
    sys.exit(0)
