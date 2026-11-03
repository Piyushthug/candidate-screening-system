"""Agent state definition for screening workflow."""
from typing import TypedDict, Optional, List


class ParsedResume(TypedDict, total=False):
    """Parsed resume information."""
    skills: List[str]
    experience_years: float
    education: List[str]
    summary: str


class JobRequirements(TypedDict, total=False):
    """Job requirements."""
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience_years: float
    level: str


class FitAnalysis(TypedDict, total=False):
    """Fit analysis results."""
    score: float  # 0-100
    reasoning: str
    key_matches: List[str]
    critical_gaps: List[str]
    nice_to_have_gaps: List[str]


class OutreachMessage(TypedDict, total=False):
    """Generated outreach message."""
    content: str
    personalization_points: List[str]
    is_grounded: bool


class ScreeningState(TypedDict, total=False):
    """Shared state across screening workflow."""

    # Input
    candidate_id: str
    candidate_name: str
    resume_text: str
    job_id: str
    job_title: str
    job_description: str

    # Processing steps
    parsed_resume: ParsedResume
    job_requirements: JobRequirements
    fit_analysis: FitAnalysis
    generated_message: Optional[OutreachMessage]

    # Approval
    approval_status: str  # "pending", "approved", "rejected"
    approval_feedback: Optional[str]

    # Metadata
    screening_id: str
    step: str  # Current step in workflow
    error: Optional[str]
    retry_count: int
