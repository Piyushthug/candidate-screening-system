"""API routes for screening endpoints."""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from backend.db.database import get_db, Screening
from backend.api.models import (
    ScreeningStartRequest, ScreeningApprovalRequest, ScreeningResponse, ScreeningDetailResponse
)
from backend.services.screening_service import ScreeningService
from backend.db.database import Job, Candidate

router = APIRouter(prefix="/screen", tags=["screening"])


@router.post("/batch")
async def start_screening_batch(
    job_id: str,
    candidate_ids: list[str] = None,
    db: Session = Depends(get_db)
):
    """Start screening batch for multiple candidates."""

    # Validate job exists and is not archived
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.archived:
        raise HTTPException(status_code=400, detail="Job is archived")

    # If no candidates specified, get all candidates
    if not candidate_ids:
        candidates = db.query(Candidate).all()
        candidate_ids = [c.id for c in candidates]

    # Create screening records for each candidate
    screenings = []
    for candidate_id in candidate_ids:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            continue

        screening_id = f"screening_{uuid.uuid4().hex[:8]}"
        screening = ScreeningService.create_screening(
            screening_id,
            job_id,
            candidate_id,
            db
        )
        screenings.append(screening)

    return {
        "job_id": job_id,
        "screenings_created": len(screenings),
        "screening_ids": [s.id for s in screenings]
    }


@router.post("/{screening_id}/start-workflow")
async def start_screening_workflow(
    screening_id: str,
    db: Session = Depends(get_db)
):
    """Start the screening workflow for a screening session."""

    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    try:
        state = ScreeningService.run_screening_workflow(
            screening_id,
            screening.job_id,
            screening.candidate_id,
            db
        )

        return {
            "screening_id": screening_id,
            "status": screening.status,
            "fit_score": screening.fit_score,
            "message_generated": screening.generated_message is not None,
            "approval_status": screening.approval_status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow error: {str(e)}")


@router.get("/{screening_id}", response_model=ScreeningResponse)
async def get_screening(screening_id: str, db: Session = Depends(get_db)):
    """Get screening state."""

    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    return screening


@router.get("/{screening_id}/detail", response_model=ScreeningDetailResponse)
async def get_screening_detail(screening_id: str, db: Session = Depends(get_db)):
    """Get complete screening details with job and candidate info."""

    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    job = db.query(Job).filter(Job.id == screening.job_id).first()
    candidate = db.query(Candidate).filter(Candidate.id == screening.candidate_id).first()

    if not job or not candidate:
        raise HTTPException(status_code=404, detail="Job or candidate not found")

    # Parse fit details if available
    fit_details = None
    if screening.fit_score is not None:
        fit_details = {
            "score": screening.fit_score,
            "reasoning": screening.fit_reasoning or "",
            "key_matches": [],
            "gaps": []
        }

    return {
        "screening": screening,
        "job": job,
        "candidate": candidate,
        "fit_details": fit_details
    }


@router.post("/{screening_id}/approve")
async def approve_screening(
    screening_id: str,
    request: ScreeningApprovalRequest,
    db: Session = Depends(get_db)
):
    """Approve a screening decision."""

    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    if screening.status not in ["pending_approval", "validation_failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve screening in status '{screening.status}'"
        )

    if request.approval_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Use /reject endpoint for rejecting"
        )

    screening = ScreeningService.approve_screening(
        screening_id,
        request.feedback,
        db
    )

    return {
        "screening_id": screening_id,
        "approval_status": screening.approval_status,
        "status": screening.status,
        "message": "Screening approved. In production, message would be sent now."
    }


@router.post("/{screening_id}/reject")
async def reject_screening(
    screening_id: str,
    request: ScreeningApprovalRequest,
    db: Session = Depends(get_db)
):
    """Reject a screening decision."""

    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    if screening.status not in ["pending_approval", "validation_failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject screening in status '{screening.status}'"
        )

    if request.approval_status != "rejected":
        raise HTTPException(
            status_code=400,
            detail="Use /approve endpoint for approving"
        )

    screening = ScreeningService.reject_screening(
        screening_id,
        request.feedback,
        db
    )

    return {
        "screening_id": screening_id,
        "approval_status": screening.approval_status,
        "status": screening.status,
        "message": "Screening rejected. Candidate will not be contacted."
    }


@router.get("/job/{job_id}/screenings")
async def list_screenings_for_job(job_id: str, db: Session = Depends(get_db)):
    """List all screenings for a job."""

    screenings = db.query(Screening).filter(Screening.job_id == job_id).all()

    screening_data = []
    for s in screenings:
        candidate = db.query(Candidate).filter(Candidate.id == s.candidate_id).first()

        # Handle parsed_skills - it's stored as JSON list
        skills = []
        if candidate and candidate.parsed_skills:
            if isinstance(candidate.parsed_skills, list):
                skills = candidate.parsed_skills
            elif isinstance(candidate.parsed_skills, str):
                skills = [s.strip() for s in candidate.parsed_skills.split(",") if s.strip()]

        screening_data.append({
            "id": s.id,
            "job_id": s.job_id,
            "candidate_id": s.candidate_id,
            "status": s.status,
            "fit_score": s.fit_score,
            "fit_reasoning": s.fit_reasoning or "",
            "generated_message": s.generated_message or "",
            "approval_status": s.approval_status,
            "candidate": {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "experience_years": candidate.experience_years,
                "parsed_skills": skills
            } if candidate else None
        })

    return {
        "job_id": job_id,
        "total": len(screening_data),
        "screenings": screening_data
    }
