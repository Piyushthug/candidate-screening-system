"""Test configuration and fixtures."""
import pytest
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.database import Base, get_db
from backend.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    app.dependency_overrides.clear()


@pytest.fixture
def client(temp_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def db_session(temp_db):
    """Provide database session for tests."""
    from backend.db.database import Job, Candidate
    import json

    # Load sample data
    jobs_file = Path(__file__).parent.parent / "backend" / "data" / "jobs.json"
    with open(jobs_file) as f:
        jobs_data = json.load(f)

    for job_data in jobs_data:
        job = Job(**job_data)
        temp_db.add(job)

    candidates_file = Path(__file__).parent.parent / "backend" / "data" / "candidates.json"
    with open(candidates_file) as f:
        candidates_data = json.load(f)

    for cand_data in candidates_data:
        candidate = Candidate(**cand_data)
        temp_db.add(candidate)

    temp_db.commit()

    return temp_db


# Test data fixtures
@pytest.fixture
def sample_job():
    """Sample job data."""
    return {
        "id": "job_test_001",
        "title": "Test Developer",
        "description": "A test job",
        "requirements": ["Python", "Testing"],
        "level": "mid"
    }


@pytest.fixture
def sample_candidate():
    """Sample candidate data."""
    return {
        "id": "cand_test_001",
        "name": "Test Candidate",
        "email": "test@example.com",
        "resume_text": "5 years of Python and Testing experience. Strong backend skills."
    }


@pytest.fixture
def good_resume():
    """Well-formed resume."""
    return """John Doe
Software Engineer
7 years of experience

Skills:
- Python, JavaScript, FastAPI
- PostgreSQL, AWS, Docker
- Kubernetes, REST APIs

Experience:
- Senior Engineer at TechCorp (3 years)
- Mid-level at StartupXYZ (2 years)
- Junior at WebDev Inc (2 years)

Education:
- Bachelor's Degree in Computer Science
"""


@pytest.fixture
def malformed_resume():
    """Resume with missing information."""
    return "Developer. Some experience."


@pytest.fixture
def empty_resume():
    """Empty resume."""
    return ""


@pytest.fixture
def sample_job_requirements():
    """Sample job requirements."""
    return {
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "preferred_skills": ["AWS", "Docker"],
        "min_experience_years": 3,
        "level": "senior"
    }
