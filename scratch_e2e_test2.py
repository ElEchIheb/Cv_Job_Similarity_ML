import sys
import os
from pathlib import Path

# Fix python path for local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.api.main import _model_result, _build_services
from src.reporting.pdf_generator import MatchReportPDF
from src.parsing import extract_text_from_pdf
import src.api.main as main_api

def run_test():
    # Pre-build services manually since we are bypassing FastAPI initialization
    main_api._services_cache = _build_services()
    
    cv_text = "I am a software engineer with 5 years of experience in Python and React. I have a Master's degree in Computer Science."
    job_text = "We are looking for a software engineer with Python and React experience."
    
    # 0. Fit TFIDF since the checkpoint isn't present
    main_api._services_cache["hybrid"].models["tfidf"].fit_pairs([cv_text], [job_text])
    
    # 1. Match
    print("Matching...")
    result = _model_result("hybrid", cv_text, job_text)
    
    print("Score:", result["score"])
    print("Decision:", result["label"], result["explanation"].get("hiring_recommendation", {}).get("decision"))
    print("Confidence:", result["confidence"])
    
    # 2. PDF
    print("Generating PDF...")
    gen = MatchReportPDF()
    pdf_bytes = gen.generate(
        result=result,
        explanation=result["explanation"],
        recommendations=result["recommendations"],
        candidate_name="John Doe",
        job_title="Software Engineer"
    )
    if pdf_bytes:
        print(f"PDF generated: {len(pdf_bytes)} bytes")
    
if __name__ == "__main__":
    run_test()
