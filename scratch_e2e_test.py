import sys
import asyncio
import os
from pathlib import Path

# Fix python path for local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.api.services.cv_service import process_cv
from src.database.models import CV, JobOffer, MatchingResult, Base
from src.database.core import get_db, engine
from fastapi import UploadFile
import io

async def run_e2e():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    # Find a test CV and Job
    cv_path = Path("data/samples/cv_sample.pdf")
    if not cv_path.exists():
        pdfs = list(Path("data").rglob("*.pdf"))
        if not pdfs:
            print("No PDFs found to test.")
            return
        cv_path = pdfs[0]
        
    print(f"Using CV: {cv_path}")
    
    # create a dummy job offer in DB
    job = JobOffer(
        title="Software Engineer",
        description="We are looking for a software engineer with Python and React experience.",
        domain="Software Engineering",
        requirements={"skills": ["Python", "React", "SQL"]},
        recruiter_id=1
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    with open(cv_path, "rb") as f:
        file_content = f.read()
        
    upload_file = UploadFile(filename=cv_path.name, file=io.BytesIO(file_content))
    
    print("Processing CV...")
    result = await process_cv(upload_file, job.id, db)
    
    print(f"Match Result ID: {result.id}")
    print(f"Global Score: {result.global_score}")
    print(f"Decision: {result.decision}")
    print(f"Confidence: {result.confidence_score}")
    
    # Check PDF
    print(f"Report Path: {result.report_path}")
    if result.report_path and Path(result.report_path).exists():
        print("PDF generated successfully.")
    else:
        print("PDF generation failed or path incorrect.")

if __name__ == "__main__":
    asyncio.run(run_e2e())
