import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.api.deps import get_database_session
from backend.database.models import RankingModel, CandidateModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rankings", tags=["Rankings"])

class LeaderboardResponse(BaseModel):
    id: int
    candidate_id: str
    name: str
    final_score: float
    semantic_score: float
    skill_score: float
    career_score: float
    behavioral_score: float
    education_score: float
    honeypot_penalty: float
    is_disqualified: bool

    class Config:
        from_attributes = True

class ScoreDetailsResponse(BaseModel):
    candidate_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    summary: Optional[str]
    skills: List[str]
    experience: List[dict]
    education: List[dict]
    certifications: List[dict]
    languages: List[str]
    
    # Ranking metrics
    final_score: float
    semantic_score: float
    skill_score: float
    career_score: float
    behavioral_score: float
    education_score: float
    honeypot_penalty: float
    is_disqualified: bool
    
    # Recruiter explanation card
    fit_summary: Optional[str]
    strengths: List[str]
    concerns: List[str]
    interview_questions: List[str]

    class Config:
        from_attributes = True

@router.get("/{job_id}", response_model=List[LeaderboardResponse])
def get_leaderboard(
    job_id: int,
    filter_disqualified: bool = True,
    db: Session = Depends(get_database_session)
):
    """
    Fetches the sorted leaderboard of candidates evaluated against a specific Job Description.
    Supports filtering out disqualified profiles.
    """
    query = db.query(
        RankingModel.id,
        RankingModel.candidate_id,
        CandidateModel.name,
        RankingModel.final_score,
        RankingModel.semantic_score,
        RankingModel.skill_score,
        RankingModel.career_score,
        RankingModel.behavioral_score,
        RankingModel.education_score,
        RankingModel.honeypot_penalty,
        RankingModel.is_disqualified
    ).join(
        CandidateModel, RankingModel.candidate_id == CandidateModel.candidate_id
    ).filter(
        RankingModel.job_description_id == job_id
    )

    if filter_disqualified:
        query = query.filter(RankingModel.is_disqualified == False)

    # Sort by score descending
    rankings = query.order_by(RankingModel.final_score.desc()).all()
    
    # Format SQLAlchemy row tuples into models
    results = []
    for r in rankings:
        results.append(
            LeaderboardResponse(
                id=r.id,
                candidate_id=r.candidate_id,
                name=r.name,
                final_score=r.final_score,
                semantic_score=r.semantic_score,
                skill_score=r.skill_score,
                career_score=r.career_score,
                behavioral_score=r.behavioral_score,
                education_score=r.education_score,
                honeypot_penalty=r.honeypot_penalty,
                is_disqualified=r.is_disqualified
            )
        )
    return results

@router.get("/{job_id}/candidate/{candidate_id}", response_model=ScoreDetailsResponse)
def get_candidate_score_details(
    job_id: int,
    candidate_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Retrieves the complete profile data and detailed scoring breakdown (strengths,
    concerns, and interview questions) for a candidate evaluated against a job description.
    """
    # 1. Fetch ranking record
    ranking = db.query(RankingModel).filter_by(
        job_description_id=job_id,
        candidate_id=candidate_id
    ).first()
    
    if not ranking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ranking record not found for Candidate {candidate_id} matching Job {job_id}."
        )
        
    # 2. Fetch profile details
    candidate = db.query(CandidateModel).filter_by(candidate_id=candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile {candidate_id} not found."
        )

    # Construct joint response
    return ScoreDetailsResponse(
        candidate_id=candidate.candidate_id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        summary=candidate.summary,
        skills=candidate.skills or [],
        experience=candidate.experience or [],
        education=candidate.education or [],
        certifications=candidate.certifications or [],
        languages=candidate.languages or [],
        
        final_score=ranking.final_score,
        semantic_score=ranking.semantic_score,
        skill_score=ranking.skill_score,
        career_score=ranking.career_score,
        behavioral_score=ranking.behavioral_score,
        education_score=ranking.education_score,
        honeypot_penalty=ranking.honeypot_penalty,
        is_disqualified=ranking.is_disqualified,
        
        fit_summary=ranking.fit_summary,
        strengths=ranking.strengths or [],
        concerns=ranking.concerns or [],
        interview_questions=ranking.interview_questions or []
    )
