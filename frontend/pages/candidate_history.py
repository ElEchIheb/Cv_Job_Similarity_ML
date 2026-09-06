"""
frontend/pages/candidate_history.py
NeuralHire — Candidate History Page
"""
from __future__ import annotations
import streamlit as st
from sqlalchemy import func
from src.database import SessionLocal
from src import models_db
from frontend.components.ui import page_header, premium_table, empty_state, stat_row, progress_mini
from frontend.styles.theme import ICONS

def render():
    page_header("CANDIDATES", "Candidate", "History", "Review candidates, parsed profiles and their evaluation activity.")

    db = SessionLocal()
    try:
        candidates = db.query(models_db.Candidate).order_by(models_db.Candidate.created_at.desc()).all()
        
        if not candidates:
            empty_state("users", "No candidates yet", "Upload a CV to begin evaluating candidates.")
            return

        # KPI Summary
        eval_total = db.query(models_db.MatchResult).count()
        avg_score = db.query(func.avg(models_db.MatchResult.final_score)).scalar()
        avg_score_val = f"{avg_score * 100:.1f}%" if avg_score else "N/A"
        
        recent = db.query(models_db.Candidate).order_by(models_db.Candidate.created_at.desc()).first()
        recent_date = recent.created_at.strftime("%b %d, %Y") if recent and recent.created_at else "N/A"

        stat_row([
            {"icon_key": "users", "value": str(len(candidates)), "label": "Total Candidates", "variant": "brand"},
            {"icon_key": "activity", "value": str(eval_total), "label": "Total Evaluations", "variant": "purple"},
            {"icon_key": "trending-up", "value": avg_score_val, "label": "Avg Compatibility", "variant": "cyan"},
            {"icon_key": "clock", "value": recent_date, "label": "Most Recent", "variant": "brand"}
        ])

        @st.dialog("✏️ Edit Candidate")
        def edit_candidate_dialog(cand_id):
            edit_cand = db.query(models_db.Candidate).filter(models_db.Candidate.id == cand_id).first()
            if not edit_cand:
                st.error("Candidate not found.")
                return
            
            with st.form("edit_candidate_form"):
                name = st.text_input("Candidate Name *", value=edit_cand.full_name)
                email = st.text_input("Candidate Email", value=edit_cand.email if edit_cand.email else "")
                phone = st.text_input("Phone", value=edit_cand.phone if edit_cand.phone else "")
                
                status_options = ["NEW", "UNDER_REVIEW", "SHORTLISTED", "INTERVIEW", "HIRED", "REJECTED"]
                current_status = edit_cand.status if edit_cand.status else "NEW"
                status_index = status_options.index(current_status) if current_status in status_options else 0
                status = st.selectbox("Pipeline Status", status_options, index=status_index)
                
                if st.form_submit_button("Save Changes", type="primary"):
                    if not name.strip():
                        st.error("Candidate Name is required.")
                        return
                    
                    clean_email = email.strip().lower() if email.strip() else None
                    if clean_email and clean_email != edit_cand.email:
                        # Check for duplicates
                        existing = db.query(models_db.Candidate).filter(models_db.Candidate.email == clean_email).first()
                        if existing:
                            st.error(f"Cannot use email '{clean_email}'. It is already in use by another candidate.")
                            return

                    edit_cand.full_name = name.strip()
                    edit_cand.email = clean_email
                    edit_cand.phone = phone.strip()
                    edit_cand.status = status
                    db.commit()
                    st.success("Candidate updated.")
                    st.rerun()

        @st.dialog("⚠️ Delete Candidate")
        def delete_candidate_dialog(cand_id):
            cand = db.query(models_db.Candidate).filter(models_db.Candidate.id == cand_id).first()
            if not cand:
                st.error("Candidate not found.")
                return
            
            eval_count = db.query(models_db.MatchResult).filter(models_db.MatchResult.candidate_id == cand_id).count()
            
            st.markdown(f"**{cand.full_name}**")
            st.markdown(f"*{cand.email or 'No email'}*")
            
            if eval_count > 0:
                st.warning(f"Cannot permanently delete this candidate because they have {eval_count} existing application(s).")
                st.info("You can archive/deactivate the candidate instead by changing their Pipeline Status to REJECTED or moving them out of active consideration.")
                if st.button("Cancel"):
                    st.rerun()
            else:
                st.markdown("This candidate has 0 applications. Are you sure you want to delete them?")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Cancel", width="stretch"):
                        st.rerun()
                with col2:
                    if st.button("Delete", type="primary", width="stretch"):
                        db.delete(cand)
                        db.commit()
                        st.success("Candidate deleted.")
                        st.rerun()

        st.markdown("### Manage Candidates")
        manage_col1, manage_col2, manage_col3 = st.columns([2, 1, 1])
        cand_options = {c.id: f"{c.full_name} ({c.email or 'No email'})" for c in candidates}
        with manage_col1:
            selected_cand_id = st.selectbox("Select Candidate", options=list(cand_options.keys()), format_func=lambda x: cand_options[x], label_visibility="collapsed")
        with manage_col2:
            if st.button("Edit", width="stretch", icon=":material/edit:") and selected_cand_id:
                edit_candidate_dialog(selected_cand_id)
        with manage_col3:
            if st.button("Delete", width="stretch", icon=":material/delete:") and selected_cand_id:
                delete_candidate_dialog(selected_cand_id)

        # Table
        headers = ["Candidate", "Email", "Evaluations", "Best Match", "Created", "Status"]
        rows = []
        
        for c in candidates:
            eval_count = db.query(models_db.MatchResult).filter(models_db.MatchResult.candidate_id == c.id).count()
            best_score = db.query(func.max(models_db.MatchResult.final_score)).filter(models_db.MatchResult.candidate_id == c.id).scalar()
            
            # Formatting
            email = c.email if c.email else '<span class="secondary-text">N/A</span>'
            date = c.created_at.strftime("%Y-%m-%d") if c.created_at else "N/A"
            
            if best_score is not None:
                match_col = progress_mini(best_score * 100)
            else:
                match_col = '<span class="secondary-text">Not evaluated</span>'
                
            _cstatus = (c.status or "NEW").upper()
            _cls = {"HIRED": "hire", "SHORTLISTED": "consider", "INTERVIEW": "consider",
                    "UNDER_REVIEW": "active", "REJECTED": "reject", "NEW": "draft"}.get(_cstatus, "draft")
            status_badge = f'<span class="nh-badge-inline {_cls}">{_cstatus.replace("_", " ")}</span>'
            
            rows.append([
                c.full_name,
                email,
                str(eval_count),
                match_col,
                date,
                status_badge
            ])
            
        premium_table(headers, rows, avatars_col=0)

    finally:
        db.close()

