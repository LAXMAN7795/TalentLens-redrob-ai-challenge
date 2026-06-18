from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

class Education(BaseModel):
    institution: str = Field(..., description="Name of the school, college, or university")
    degree: Optional[str] = Field(None, description="Degree obtained (e.g., Bachelor, Master, PhD)")
    field_of_study: Optional[str] = Field(None, description="Field of study (e.g., Computer Science)")
    start_date: Optional[str] = Field(None, description="Start date of education")
    end_date: Optional[str] = Field(None, description="End date of education or 'Present'")
    gpa: Optional[float] = Field(None, description="GPA or grade percentage")

class Experience(BaseModel):
    company: str = Field(..., description="Name of the company or organization")
    title: str = Field(..., description="Job title / role")
    start_date: Optional[str] = Field(None, description="Start date of employment")
    end_date: Optional[str] = Field(None, description="End date of employment or 'Present'")
    description: Optional[str] = Field(None, description="Detailed description of responsibilities and achievements")
    skills: List[str] = Field(default_factory=list, description="Skills used or learned in this role")
    location: Optional[str] = Field(None, description="Geographic location of the company")

class Certification(BaseModel):
    name: str = Field(..., description="Name of the certification")
    issuing_organization: Optional[str] = Field(None, description="Organization that issued the certification")
    issue_date: Optional[str] = Field(None, description="Date when the certification was issued")

class CandidateProfile(BaseModel):
    candidate_id: str = Field(..., description="Unique identifier for the candidate (UUID, email, or sequential ID)")
    name: str = Field(..., description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address of the candidate")
    phone: Optional[str] = Field(None, description="Contact phone number")
    summary: Optional[str] = Field(None, description="Professional summary or bio")
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills")
    experience: List[Experience] = Field(default_factory=list, description="List of professional experiences")
    education: List[Education] = Field(default_factory=list, description="List of educational background")
    certifications: List[Certification] = Field(default_factory=list, description="List of certifications")
    languages: List[str] = Field(default_factory=list, description="Languages spoken by the candidate")

class JobDescription(BaseModel):
    title: str = Field(..., description="Target role title")
    department: Optional[str] = Field(None, description="Department or business unit")
    description: str = Field(..., description="Full text description of the role")
    skills_required: List[str] = Field(default_factory=list, description="List of mandatory and preferred skills")
    experience_required_years: Optional[float] = Field(None, description="Minimum years of experience required")
    education_required: Optional[str] = Field(None, description="Minimum education level required")
    location: Optional[str] = Field(None, description="Role location (e.g. Remote, On-site, Hybrid)")

class CandidateScoreBreakdown(BaseModel):
    candidate_id: str
    name: str
    final_score: float
    semantic_score: float
    skill_score: float
    career_score: float
    behavioral_score: float
    education_score: float
    honeypot_penalty: float
    is_disqualified: bool = False

class CandidateExplanation(BaseModel):
    candidate_id: str
    fit_summary: str = Field(..., description="2-3 sentence overview of candidate's suitability for this role")
    strengths: List[str] = Field(default_factory=list, description="Key professional and technical strengths")
    concerns: List[str] = Field(default_factory=list, description="Gaps, missing skills, or candidate career flags")
    interview_questions: List[str] = Field(default_factory=list, description="Tailored screening questions for the recruiter to ask")
