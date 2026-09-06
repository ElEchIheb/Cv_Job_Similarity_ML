import sqlite3
import pandas as pd
from src.database import SessionLocal, Base, engine
from src.db_maintenance import run_data_redesign_migration
from src.matching.service import _resolve_candidate, evaluate_and_persist
from src.decisioning import DecisionConfig, DecisionResult
import src.models_db as models_db
import shutil
import pytest
import time

def print_header(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

# 1. DATABASE FORENSICS
print_header("1. DATABASE FORENSICS (SQLite Direct)")
conn = sqlite3.connect("d:/education/pfe/pfe_ai/data/neuralhire.db")
c = conn.cursor()

# Job Offers
c.execute("SELECT COUNT(*) FROM job_offers")
total_jobs = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT job_code) FROM job_offers WHERE job_code IS NOT NULL")
unique_job_codes = c.fetchone()[0]
c.execute("SELECT job_code, COUNT(*) FROM job_offers GROUP BY job_code HAVING COUNT(*) > 1")
duplicate_job_codes = c.fetchall()
c.execute("SELECT title, COUNT(*) FROM job_offers GROUP BY LOWER(TRIM(title)) HAVING COUNT(*) > 1")
duplicate_titles = c.fetchall()

print(f"Total JobOffers: {total_jobs}")
print(f"Unique job_codes: {unique_job_codes}")
print(f"Duplicate job_codes: {len(duplicate_job_codes)}")
print(f"Duplicate titles: {len(duplicate_titles)} {duplicate_titles}")

# Candidates
c.execute("SELECT COUNT(*) FROM candidates")
total_cands = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT email) FROM candidates WHERE email IS NOT NULL AND TRIM(email) != ''")
unique_emails = c.fetchone()[0]
c.execute("SELECT email, COUNT(*) FROM candidates WHERE email IS NOT NULL AND TRIM(email) != '' GROUP BY LOWER(TRIM(email)) HAVING COUNT(*) > 1")
duplicate_emails = c.fetchall()
c.execute("SELECT COUNT(*) FROM candidates WHERE email IS NULL OR TRIM(email) = ''")
empty_emails = c.fetchone()[0]

print(f"\nTotal Candidates: {total_cands}")
print(f"Unique emails: {unique_emails}")
print(f"Duplicate emails: {len(duplicate_emails)} {duplicate_emails}")
print(f"Empty/null emails: {empty_emails}")

# MatchResults
c.execute("SELECT COUNT(*) FROM match_results")
total_apps = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM match_results WHERE candidate_id NOT IN (SELECT id FROM candidates)")
invalid_cands = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM match_results WHERE job_offer_id NOT IN (SELECT id FROM job_offers)")
invalid_jobs = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM match_results WHERE final_score IS NULL")
no_score = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM match_results WHERE decision IS NULL")
no_decision = c.fetchone()[0]

print(f"\nTotal applications: {total_apps}")
print(f"Applications with invalid candidate_id: {invalid_cands}")
print(f"Applications with invalid job_offer_id: {invalid_jobs}")
print(f"Applications without compatibility score: {no_score}")
print(f"Applications without status (decision): {no_decision}")

# Foreign keys pragma
c.execute("PRAGMA foreign_keys")
fk_enabled = c.fetchone()[0]
print(f"\nForeign Keys enabled in SQLite PRAGMA: {fk_enabled}")

conn.close()

# 2. CONSTRAINTS CHECK
print_header("2. DATABASE CONSTRAINTS")
# We can check SQLite sqlite_master for table definitions
conn = sqlite3.connect("d:/education/pfe/pfe_ai/data/neuralhire.db")
df_jo = pd.read_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='job_offers'", conn)
df_cand = pd.read_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='candidates'", conn)
print("Job Offers Table SQL:")
print(df_jo.iloc[0]['sql'])
print("\nCandidates Table SQL:")
print(df_cand.iloc[0]['sql'])
conn.close()

# 3. MIGRATION SAFETY
print_header("3. MIGRATION SAFETY (Idempotency)")
# Make a copy of the DB
shutil.copy2("d:/education/pfe/pfe_ai/data/neuralhire.db", "d:/education/pfe/pfe_ai/data/neuralhire_copy.db")
from sqlalchemy import create_engine
engine_copy = create_engine("sqlite:///d:/education/pfe/pfe_ai/data/neuralhire_copy.db")
print("Running migration again on copy...")
stats = run_data_redesign_migration(engine_copy)
print("Migration Stats (should be all 0):", stats)

# 4. END-TO-END TEST
print_header("4. END-TO-END & NEGATIVE TESTS")
engine_test = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine_test)
TestingSession = SessionLocal
TestingSession.configure(bind=engine_test)
db = TestingSession()

try:
    # Set up models dict mock
    class MockModel:
        def predict(self, cv, job):
            return {"final_score": 0.85, "component_scores": {}, "percentage": 85.0, "label": 1, "confidence": "high", "skill_details": {}}
    models_mock = {"hybrid": MockModel(), "explainer": MockModel(), "recommender": MockModel()}
    def explain_mock(cv, job, res, config=None, **kwargs):
        return {"gap_analysis": {}, "hiring_recommendation": {"decision": "HIRE", "confidence": "high", "confidence_level": 0.9}, "decision_config": {}}
    def generate_mock(gap):
        return []
    models_mock["explainer"].explain = explain_mock
    models_mock["recommender"].generate = generate_mock
    
    # Step 1: Create Job Offer A
    job_a = models_db.JobOffer(job_code="JOB-A", title="Data Scientist", description="Must know Python")
    db.add(job_a)
    db.commit()
    db.refresh(job_a)
    print(f"Step 1: Created JobOffer A. Total jobs: {db.query(models_db.JobOffer).count()}")

    # Step 2: Create Candidate A via evaluation flow later, but let's check evaluation
    
    # Step 3: Evaluate Cand A against Job A
    payload1 = evaluate_and_persist(
        db, models_mock, "I am a Data Scientist in python", "Must know Python",
        candidate_name="John Doe", candidate_email="john@example.com",
        job_offer_id=job_a.id, recruiter_id=1, config=DecisionConfig.default()
    )
    cands_count = db.query(models_db.Candidate).count()
    apps_count = db.query(models_db.MatchResult).count()
    print(f"Step 3: Evaluated Cand A against Job A. Candidates: {cands_count}, Applications: {apps_count}")

    # Step 4: Evaluate Cand A against Job A AGAIN
    payload2 = evaluate_and_persist(
        db, models_mock, "I am a Data Scientist in python updated", "Must know Python",
        candidate_name="JOHN DOE", candidate_email="JOHN@EXAMPLE.COM", # Case insensitive check
        job_offer_id=job_a.id, recruiter_id=1, config=DecisionConfig.default()
    )
    cands_count = db.query(models_db.Candidate).count()
    jobs_count = db.query(models_db.JobOffer).count()
    apps_count = db.query(models_db.MatchResult).count()
    print(f"Step 4: Evaluated Cand A (case changes) against Job A again. Candidates: {cands_count}, Jobs: {jobs_count}, Applications: {apps_count}")
    
    # Step 5: Create Job Offer B, Evaluate Cand A against Job B
    job_b = models_db.JobOffer(job_code="JOB-B", title="Backend Engineer", description="Python backend")
    db.add(job_b)
    db.commit()
    db.refresh(job_b)
    
    payload3 = evaluate_and_persist(
        db, models_mock, "I am a Data Scientist in python", "Python backend",
        candidate_name="John Doe", candidate_email="John@example.com",
        job_offer_id=job_b.id, recruiter_id=1, config=DecisionConfig.default()
    )
    cands_count = db.query(models_db.Candidate).count()
    jobs_count = db.query(models_db.JobOffer).count()
    apps_count = db.query(models_db.MatchResult).count()
    print(f"Step 5: Evaluated Cand A against Job B. Candidates: {cands_count}, Jobs: {jobs_count}, Applications: {apps_count}")

    # Step 6 & 7 & 8: Verify links, scores, status
    apps = db.query(models_db.MatchResult).order_by(models_db.MatchResult.id).all()
    print("Step 6-8: Applications:")
    for app in apps:
        print(f"  App {app.id} -> Cand: {app.candidate.email}, Job: {app.job_offer.job_code}, Score: {app.final_score}, Decision: {app.decision}")

    # NEGATIVE TESTS
    print("\nNEGATIVE TESTS:")
    try:
        evaluate_and_persist(db, models_mock, "CV", "Job", candidate_email="new@t.com", job_offer_id=None)
        print("Test A (Missing Job Offer): FAILED (No exception raised)")
    except ValueError as e:
        print(f"Test A (Missing Job Offer): PASSED ({e})")
        
    try:
        evaluate_and_persist(db, models_mock, "CV", "Job", candidate_email="new@t.com", job_offer_id=999)
        print("Test B (Invalid Job Offer ID): FAILED (No exception raised)")
    except ValueError as e:
        print(f"Test B (Invalid Job Offer ID): PASSED ({e})")

finally:
    db.close()
