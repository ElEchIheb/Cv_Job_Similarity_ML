"""
frontend/pages/analysis_history.py
NeuralHire — Analysis History Page
"""
from __future__ import annotations
import json
import streamlit as st
from sqlalchemy import func
from src.database import SessionLocal
from src import models_db
from frontend.components.ui import page_header, premium_table, empty_state, stat_row, badge_html, progress_mini
from frontend.styles.theme import ICONS

def render():
    page_header("EVALUATIONS", "Analysis", "History", "Review previous AI matching evaluations and reports.")

    db = SessionLocal()
    try:
        # Filters
        with st.expander("🔍 Filter Analyses"):
            col1, col2, col3 = st.columns(3)
            with col1:
                f_job_code = st.text_input("Job Offer Code", placeholder="e.g. JOB-2026-001").strip()
            with col2:
                f_job_name = st.text_input("Job Offer Title", placeholder="e.g. Engineer").strip()
            with col3:
                f_cand_email = st.text_input("Candidate Email", placeholder="e.g. alice@").strip()
                
        query = db.query(models_db.MatchResult).join(models_db.Candidate).join(models_db.JobOffer)
        if f_job_code:
            query = query.filter(models_db.JobOffer.job_code.ilike(f"%{f_job_code}%"))
        if f_job_name:
            query = query.filter(models_db.JobOffer.title.ilike(f"%{f_job_name}%"))
        if f_cand_email:
            query = query.filter(models_db.Candidate.email.ilike(f"%{f_cand_email}%"))
            
        matches = query.order_by(models_db.MatchResult.created_at.desc()).all()
        
        if not matches:
            empty_state("file-text", "No analyses found", "Adjust your filters or run a new evaluation.")
            return

        # KPI Summary
        total_analyses = len(matches)
        
        # Table
        headers = ["Candidate", "Email", "Job Offer", "Code", "Compatibility", "Decision", "Date"]
        rows = []
        
        for m in matches:
            candidate_name = m.candidate.full_name if m.candidate else f"Unknown (ID: {m.candidate_id})"
            cand_email = m.candidate.email if m.candidate and m.candidate.email else "N/A"
            job_title = m.job_offer.title if m.job_offer else f"Unknown (ID: {m.job_offer_id})"
            job_code = m.job_offer.job_code if m.job_offer and m.job_offer.job_code else "N/A"
            
            score_val = (m.final_score or 0.0)
            if score_val <= 1.0:
                score_val = score_val * 100
                
            score_col = progress_mini(score_val)
            
            dec = (m.decision or "N/A").upper()
            if dec == "HIRE": decision_badge = badge_html("HIRE", "hire")
            elif dec == "CONSIDER": decision_badge = badge_html("CONSIDER", "consider")
            elif dec == "REJECT": decision_badge = badge_html("REJECT", "reject")
            else: decision_badge = badge_html(dec, "draft")
            
            date = m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else "N/A"
            
            rows.append([
                candidate_name,
                f'<span class="secondary-text">{cand_email}</span>',
                job_title,
                f'<span class="secondary-text">{job_code}</span>',
                score_col,
                decision_badge,
                date
            ])
            
        premium_table(headers, rows, avatars_col=0)

        # Raw Details Expander
        st.markdown("### View Report Details")
        st.markdown('<div style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 12px;">Select an evaluation ID below to inspect the raw JSON explanation payload from the AI.</div>', unsafe_allow_html=True)
        selected_match_id = st.selectbox("Select Match ID:", [m.id for m in matches])
        
        if selected_match_id:
            match_record = db.query(models_db.MatchResult).filter(models_db.MatchResult.id == selected_match_id).first()
            if match_record and match_record.explanation_json:
                with st.expander(f"Raw Evaluation Data - Match #{selected_match_id}"):
                    st.json(json.loads(match_record.explanation_json))

    finally:
        db.close()

