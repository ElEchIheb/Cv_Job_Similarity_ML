from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional

from src.database import Base

cv_skills = Table(
    'cv_skills',
    Base.metadata,
    Column('cv_id', Integer, ForeignKey('cvs.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)

job_skills = Table(
    'job_skills',
    Base.metadata,
    Column('job_offer_id', Integer, ForeignKey('job_offers.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="recruiter")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job_offers = relationship("JobOffer", back_populates="recruiter")
    candidates = relationship("Candidate", back_populates="recruiter")

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Recruitment (pipeline) status — distinct from evaluation/system status.
    # One of: NEW | UNDER_REVIEW | SHORTLISTED | INTERVIEW | REJECTED | HIRED
    status = Column(String, default="NEW", nullable=True)
    is_anonymous = Column(Integer, default=0, nullable=True)  # 1 when identity is auto-generated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recruiter = relationship("User", back_populates="candidates")
    cvs = relationship("CV", back_populates="candidate", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="candidate", cascade="all, delete-orphan")

class CV(Base):
    __tablename__ = "cvs"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    filename = Column(String, nullable=True)
    content_text = Column(Text, nullable=False)
    extracted_skills_raw = Column(Text, nullable=True) # JSON or comma separated backup
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="cvs")
    match_results = relationship("MatchResult", back_populates="cv")
    skills = relationship("Skill", secondary=cv_skills, back_populates="cvs")

class JobOffer(Base):
    __tablename__ = "job_offers"
    
    id = Column(Integer, primary_key=True, index=True)
    job_code = Column(String, unique=True, index=True, nullable=True) # Will be nullable during migration, then effectively required
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills_raw = Column(Text, nullable=True) # JSON or comma separated backup
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Position lifecycle status: OPEN | ON_HOLD | CLOSED
    status = Column(String, default="OPEN", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recruiter = relationship("User", back_populates="job_offers")
    match_results = relationship("MatchResult", back_populates="job_offer", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary=job_skills, back_populates="job_offers")

class MatchResult(Base):
    __tablename__ = "match_results"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=True)
    job_offer_id = Column(Integer, ForeignKey("job_offers.id"), nullable=True)
    
    final_score = Column(Float, nullable=True)
    score_hybrid = Column(Float, nullable=True)
    score_semantic = Column(Float, nullable=True)
    score_keyword = Column(Float, nullable=True)
    score_skill = Column(Float, nullable=True)
    
    confidence = Column(String, nullable=True)            # legacy string level (high/medium/low)
    decision = Column(String, nullable=True)              # HIRE | CONSIDER | REJECT (canonical)

    # ── Reproducibility metadata (so a persisted evaluation can be understood
    #    exactly as it was produced, even after settings change later) ──────────
    decision_confidence = Column(Float, nullable=True)    # uncalibrated [0,1] decision confidence
    strong_fit_threshold = Column(Float, nullable=True)   # active Strong Fit threshold at eval time
    potential_fit_threshold = Column(Float, nullable=True)# active Potential Fit threshold at eval time
    model_version = Column(String, nullable=True)         # e.g. hybrid-checkpoint / legacy-recompute
    evaluation_method = Column(String, nullable=True)     # hybrid | embedding | tfidf | skill
    weights_json = Column(Text, nullable=True)            # component weights used (JSON)

    model_used = Column(String, default="hybrid")
    explanation_json = Column(Text, nullable=True) # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="match_results")
    cv = relationship("CV", back_populates="match_results")
    job_offer = relationship("JobOffer", back_populates="match_results")

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=True)
    
    # Relationships
    cvs = relationship("CV", secondary=cv_skills, back_populates="skills")
    job_offers = relationship("JobOffer", secondary=job_skills, back_populates="skills")

# Database schema will be managed by Alembic in production.
# For local dev, you can still call Base.metadata.create_all(bind=engine) explicitly where needed.
