import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import engine, Base, SessionLocal
from src import models_db

def run_verification():
    print("Initializing Database...")
    # 1. Verify database creation & tables exist
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    db = SessionLocal()
    try:
        # 2. Insert candidate
        print("Inserting candidate...")
        new_candidate = models_db.Candidate(
            full_name="Jane Database",
            email=f"jane_{int(time.time())}@database.local"
        )
        db.add(new_candidate)
        db.commit()
        db.refresh(new_candidate)
        print(f"Candidate created with ID: {new_candidate.id}")

        # 3. Insert job offer
        print("Inserting job offer...")
        new_job = models_db.JobOffer(
            title="Database Engineer",
            description="Looking for SQL expertise.",
            required_skills_raw="SQL, Python, Database Design"
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        print(f"Job Offer created with ID: {new_job.id}")

        # 4. Insert match result
        print("Inserting match result...")
        new_match = models_db.MatchResult(
            candidate_id=new_candidate.id,
            job_offer_id=new_job.id,
            final_score=0.92,
            decision="HIRE",
            confidence="high"
        )
        db.add(new_match)
        db.commit()
        db.refresh(new_match)
        print(f"Match Result created with ID: {new_match.id}")

        # 5. Read data successfully
        print("\nReading data from database...")
        match_record = db.query(models_db.MatchResult).filter(models_db.MatchResult.id == new_match.id).first()
        if match_record:
            print(f"Found Match ID: {match_record.id}")
            print(f"  Candidate: {match_record.candidate.full_name}")
            print(f"  Job Title: {match_record.job_offer.title}")
            print(f"  Score: {match_record.final_score}")
            print(f"  Decision: {match_record.decision}")
            print("Database verification passed successfully!")
        else:
            print("Error: Could not read match result.")

    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
