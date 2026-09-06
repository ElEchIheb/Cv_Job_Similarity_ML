"""
frontend/pages/job_offers.py
NeuralHire — Job Offers Page
"""
from __future__ import annotations
import streamlit as st
from datetime import datetime
from sqlalchemy import func
from src.database import SessionLocal
from src import models_db
from frontend.components.ui import page_header, premium_table, empty_state, stat_row, badge_html
from frontend.styles.theme import ICONS

def _next_job_code(db) -> str:
    year = datetime.utcnow().year
    max_job = db.query(models_db.JobOffer.job_code).filter(models_db.JobOffer.job_code.like(f"JOB-{year}-%")).order_by(models_db.JobOffer.job_code.desc()).first()
    seq = 1
    if max_job and max_job[0]:
        try:
            seq = int(max_job[0].split("-")[-1]) + 1
        except ValueError:
            pass
    return f"JOB-{year}-{seq:03d}"

def render():
    page_header("POSITIONS", "Active", "Job Offers", "Manage open positions and view their requirements.")

    db = SessionLocal()
    try:
        @st.dialog("➕ Add / Edit Job Offer", width="large")
        def edit_job_dialog(job_id=None):
            edit_job = None
            if job_id:
                edit_job = db.query(models_db.JobOffer).filter(models_db.JobOffer.id == job_id).first()
                if not edit_job:
                    st.error("Job offer not found.")
                    return
            
            with st.form("job_form"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    title = st.text_input("Job Title *", value=edit_job.title if edit_job else "")
                with col2:
                    status = st.selectbox("Status", ["OPEN", "ON_HOLD", "CLOSED"], index=["OPEN", "ON_HOLD", "CLOSED"].index(edit_job.status if edit_job and edit_job.status else "OPEN"))
                
                desc = st.text_area("Job Description *", value=edit_job.description if edit_job else "", height=150)
                skills = st.text_input("Required Skills (comma separated)", value=edit_job.required_skills_raw if edit_job else "")
                
                submit_label = "Update Job Offer" if edit_job else "Create Job Offer"
                if st.form_submit_button(submit_label, type="primary"):
                    if not title.strip() or not desc.strip():
                        st.error("Title and Description are required.")
                    else:
                        if edit_job:
                            edit_job.title = title.strip()
                            edit_job.description = desc.strip()
                            edit_job.required_skills_raw = skills.strip()
                            edit_job.status = status
                            db.commit()
                            st.success("Job Offer updated.")
                            st.rerun()
                        else:
                            recruiter_id = st.session_state.get("user_id")
                            new_job = models_db.JobOffer(
                                job_code=_next_job_code(db),
                                title=title.strip(),
                                description=desc.strip(),
                                required_skills_raw=skills.strip(),
                                status=status,
                                recruiter_id=recruiter_id
                            )
                            db.add(new_job)
                            db.commit()
                            st.success(f"Job Offer created: {new_job.job_code}")
                            st.rerun()

        @st.dialog("⚠️ Delete Job Offer")
        def delete_job_dialog(job_id):
            job = db.query(models_db.JobOffer).filter(models_db.JobOffer.id == job_id).first()
            if not job:
                st.error("Job offer not found.")
                return
            
            count = db.query(models_db.MatchResult).filter(models_db.MatchResult.job_offer_id == job_id).count()
            st.markdown(f"**{job.job_code}: {job.title}**")
            
            if count > 0:
                st.warning(f"This Job Offer cannot be permanently deleted because it has {count} associated evaluation(s).")
                st.info("You can deactivate it instead by changing its Status to CLOSED.")
                if st.button("Cancel"):
                    st.rerun()
            else:
                st.markdown("This job offer has 0 applications. Are you sure you want to delete it?")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Cancel", width="stretch"):
                        st.rerun()
                with col2:
                    if st.button("Delete", type="primary", width="stretch"):
                        db.delete(job)
                        db.commit()
                        st.success("Job offer deleted.")
                        st.rerun()

        def toggle_job_status(job_id):
            job = db.query(models_db.JobOffer).filter(models_db.JobOffer.id == job_id).first()
            if job:
                job.status = "CLOSED" if job.status == "OPEN" else "OPEN"
                db.commit()
                st.success(f"Job status changed to {job.status}.")

        offers = db.query(models_db.JobOffer).order_by(models_db.JobOffer.created_at.desc()).all()

        st.markdown("### Manage Job Offers")
        manage_col1, manage_col2, manage_col3, manage_col4, manage_col5 = st.columns([2, 1, 1, 1, 1])
        job_options = {o.id: f"{o.job_code}: {o.title} ({o.status})" for o in offers}
        with manage_col1:
            selected_job_id = st.selectbox("Select Job Offer", options=list(job_options.keys()), format_func=lambda x: job_options[x], label_visibility="collapsed") if offers else None
        with manage_col2:
            if st.button("Edit", width="stretch", icon=":material/edit:", disabled=not offers) and selected_job_id:
                edit_job_dialog(selected_job_id)
        with manage_col3:
            if st.button("Toggle Status", width="stretch", icon=":material/swap_horiz:", disabled=not offers) and selected_job_id:
                toggle_job_status(selected_job_id)
                st.rerun()
        with manage_col4:
            if st.button("Delete", width="stretch", icon=":material/delete:", disabled=not offers) and selected_job_id:
                delete_job_dialog(selected_job_id)
        with manage_col5:
            if st.button("Add New Job", width="stretch", icon=":material/add:", type="primary"):
                edit_job_dialog()

        # KPI Summary
        active_positions = len(offers)
        open_roles = sum(1 for o in offers if (o.status or "OPEN").upper() == "OPEN")
        total_evals = db.query(models_db.MatchResult).count()
        recent_offer = offers[0].created_at.strftime("%b %d, %Y") if offers and offers[0].created_at else "N/A"

        stat_row([
            {"icon_key": "briefcase", "value": str(active_positions), "label": "Total Positions", "variant": "brand"},
            {"icon_key": "target", "value": str(open_roles), "label": "Open Roles", "variant": "cyan"},
            {"icon_key": "users", "value": str(total_evals), "label": "Total Candidates Evaluated", "variant": "purple"},
            {"icon_key": "clock", "value": recent_offer, "label": "Latest Position", "variant": "brand"}
        ])
        
        if not offers:
            empty_state("briefcase", "No job offers", "Add a new job offer to begin evaluating candidates.")
            return

        headers = ["Code", "Title", "Evaluations", "Created", "Status"]
        rows = []
        
        for o in offers:
            candidate_count = db.query(models_db.MatchResult).filter(models_db.MatchResult.job_offer_id == o.id).count()
            
            code = o.job_code or "N/A"
            title = o.title
            date = o.created_at.strftime("%Y-%m-%d") if o.created_at else "N/A"
            _jstatus = (o.status or "OPEN").upper()
            _jcls = {"OPEN": "active", "CLOSED": "closed", "ON_HOLD": "draft"}.get(_jstatus, "active")
            status_badge = badge_html(_jstatus.replace("_", " "), _jcls)
            
            rows.append([
                code,
                title,
                str(candidate_count),
                date,
                status_badge
            ])
            
        premium_table(headers, rows, avatars_col=0)

    finally:
        db.close()

