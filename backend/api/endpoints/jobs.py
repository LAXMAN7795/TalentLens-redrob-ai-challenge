import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.api.deps import get_database_session
from backend.database.models import JobDescriptionModel
from backend.jd_analysis.jd_extractor import JobDescriptionExtractor
from backend.llm.groq_client import GroqClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class JobCreate(BaseModel):
    title: str = Field(..., example="Senior Python Engineer")
    description: str = Field(..., example="We are looking for a Python dev with 5 years experience using FastAPI...")

class JobResponse(BaseModel):
    id: int
    title: str
    department: Optional[str]
    description: str
    skills_required: List[str]
    experience_required_years: Optional[float]
    education_required: Optional[str]
    location: Optional[str]

    class Config:
        from_attributes = True


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_database_session)):
    """
    Submits a raw job title and description text.
    Extracts structured requirements using Groq LLM (or fallback) and commits it to the database.
    """
    logger.info(f"Received job creation request: '{payload.title}'")
    try:
        # Initialize extractor. It automatically loads credentials from config
        extractor = JobDescriptionExtractor()
        extracted_jd = extractor.extract_job_details(payload.title, payload.description)
        
        # Commit to SQL Database
        db_model = JobDescriptionModel(
            title=extracted_jd.title,
            department=extracted_jd.department,
            description=extracted_jd.description,
            skills_required=extracted_jd.skills_required,
            experience_required_years=extracted_jd.experience_required_years,
            education_required=extracted_jd.education_required,
            location=extracted_jd.location
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        logger.info(f"Job Description successfully processed and saved. ID: {db_model.id}")
        return db_model
    except Exception as exc:
        logger.error(f"Error creating job description: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze and save Job Description: {str(exc)}"
        )

@router.get("", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_database_session)):
    """
    Lists all Job Descriptions in the system.
    """
    return db.query(JobDescriptionModel).order_by(JobDescriptionModel.created_at.desc()).all()

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_database_session)):
    """
    Retrieves the detailed criteria for a specific job ID.
    """
    job = db.query(JobDescriptionModel).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with ID {job_id} not found."
        )
    return job
