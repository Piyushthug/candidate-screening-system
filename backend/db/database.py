"""Database models and initialization."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from backend.config import get_settings

settings = get_settings()

# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Job(Base):
    """Job posting model."""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    requirements = Column(JSON)  # List of required skills/qualifications
    level = Column(String)  # e.g., "junior", "mid", "senior"
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Candidate(Base):
    """Candidate model."""
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    resume_text = Column(Text)
    parsed_skills = Column(JSON)  # Extracted skills
    experience_years = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class Screening(Base):
    """Screening session model."""
    __tablename__ = "screenings"

    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), index=True)
    candidate_id = Column(String, ForeignKey("candidates.id"), index=True)
    fit_score = Column(Float, nullable=True)
    fit_reasoning = Column(Text, nullable=True)
    generated_message = Column(Text, nullable=True)
    approval_status = Column(String)  # "pending", "approved", "rejected"
    approval_feedback = Column(Text, nullable=True)
    status = Column(String, default="pending")  # "pending", "screened", "approved", "rejected", "sent", "escalated"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for all screening decisions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    screening_id = Column(String, ForeignKey("screenings.id"), index=True)
    action = Column(String)  # "created", "scored", "message_generated", "approved", "rejected", "escalated"
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database schema."""
    Base.metadata.create_all(bind=engine)
