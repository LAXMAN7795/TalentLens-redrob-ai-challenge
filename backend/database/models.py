from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from backend.database.postgres import Base

class JobDescriptionModel(Base):
    """
    SQLAlchemy model representing the parsed criteria of a Job Description.
    """
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    skills_required = Column(JSON, nullable=True)  # List[str]
    experience_required_years = Column(Float, nullable=True)
    education_required = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CandidateModel(Base):
    """
    SQLAlchemy model representing the parsed Candidate profile.
    """
    __tablename__ = "candidates"

    candidate_id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)            # List[str]
    experience = Column(JSON, nullable=True)        # List[Dict]
    education = Column(JSON, nullable=True)         # List[Dict]
    certifications = Column(JSON, nullable=True)    # List[Dict]
    languages = Column(JSON, nullable=True)         # List[str]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RankingModel(Base):
    """
    SQLAlchemy model representing a candidate's calculated scores, disqualification status,
    and LLM recruiter feedback for a specific Job Description.
    """
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String(255), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    
    # Dynamic weight sub-scores
    final_score = Column(Float, nullable=False)
    semantic_score = Column(Float, nullable=False)
    skill_score = Column(Float, nullable=False)
    career_score = Column(Float, nullable=False)
    behavioral_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    honeypot_penalty = Column(Float, nullable=False)
    is_disqualified = Column(Boolean, default=False)
    
    # Recruiter explanation card
    fit_summary = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)           # List[str]
    concerns = Column(JSON, nullable=True)            # List[str]
    interview_questions = Column(JSON, nullable=True) # List[str]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
