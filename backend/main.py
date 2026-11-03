"""FastAPI application for candidate screening system."""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
from pathlib import Path

from backend.config import get_settings
from backend.db.database import init_db, get_db, SessionLocal
from backend.db.database import Job, Candidate
from backend.api.models import (
    JobCreate, JobResponse, CandidateCreate, CandidateResponse,
    ScreeningStartRequest, ScreeningApprovalRequest, ScreeningResponse
)
from backend.api import routes

settings = get_settings()
app = FastAPI(
    title="Candidate Screening System",
    description="AI-powered candidate screening with LLM agent",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include screening routes
app.include_router(routes.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    load_seed_data()


def load_seed_data():
    """Load sample jobs and candidates into database."""
    db = SessionLocal()
    try:
        # Load jobs if not already loaded
        if db.query(Job).count() == 0:
            jobs_file = Path(__file__).parent / "data" / "jobs.json"
            with open(jobs_file) as f:
                jobs_data = json.load(f)
            for job_data in jobs_data:
                job = Job(**job_data)
                db.add(job)
            db.commit()

        # Load candidates if not already loaded
        if db.query(Candidate).count() == 0:
            candidates_file = Path(__file__).parent / "data" / "candidates.json"
            with open(candidates_file) as f:
                candidates_data = json.load(f)
            for cand_data in candidates_data:
                candidate = Candidate(**cand_data)
                db.add(candidate)
            db.commit()
    finally:
        db.close()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "candidate-screening-system",
        "version": "1.0.0"
    }


@app.get("/jobs", response_model=list[JobResponse])
async def list_jobs(db: Session = Depends(get_db)):
    """Get all active jobs."""
    jobs = db.query(Job).filter(Job.archived == False).all()
    return jobs


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get specific job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/candidates", response_model=list[CandidateResponse])
async def list_candidates(db: Session = Depends(get_db)):
    """Get all candidates."""
    candidates = db.query(Candidate).all()
    return candidates


@app.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Get specific candidate by ID."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@app.get("/jobs/{job_id}/candidates", response_model=list[CandidateResponse])
async def list_candidates_for_job(job_id: str, db: Session = Depends(get_db)):
    """Get all candidates for a job (for screening batch)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = db.query(Candidate).all()
    return candidates




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port
    )
