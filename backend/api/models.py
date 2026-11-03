"""API request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JobCreate(BaseModel):
    """Create job request."""
    id: str
    title: str
    description: str
    requirements: List[str]  # List of skills/qualifications
    level: str


class JobResponse(BaseModel):
    """Job response."""
    id: str
    title: str
    description: str
    requirements: List[str]
    level: str
    archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    """Create candidate request."""
    id: str
    name: str
    email: str
    resume_text: str


class CandidateResponse(BaseModel):
    """Candidate response."""
    id: str
    name: str
    email: str
    resume_text: str
    parsed_skills: Optional[List[str]] = None
    experience_years: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScreeningStartRequest(BaseModel):
    """Start screening request."""
    job_id: str
    candidate_id: str


class ScreeningApprovalRequest(BaseModel):
    """Approve/reject screening request."""
    approval_status: str = Field(..., description="'approved' or 'rejected'")
    feedback: Optional[str] = None


class FitScoreDetail(BaseModel):
    """Fit score with reasoning."""
    score: float = Field(..., description="0-100 score")
    reasoning: str
    key_matches: List[str]
    gaps: List[str]


class ScreeningResponse(BaseModel):
    """Screening response."""
    id: str
    job_id: str
    candidate_id: str
    fit_score: Optional[float] = None
    fit_reasoning: Optional[str] = None
    generated_message: Optional[str] = None
    approval_status: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScreeningDetailResponse(BaseModel):
    """Detailed screening response with all info."""
    screening: ScreeningResponse
    job: JobResponse
    candidate: CandidateResponse
    fit_details: Optional[FitScoreDetail] = None
