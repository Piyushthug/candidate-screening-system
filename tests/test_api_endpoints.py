"""Unit tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.database import Base, get_db


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session
    session.close()


@pytest.fixture
def client(test_db):
    """Create test client."""
    def override_get_db():
        return test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
        assert data.get('service') is not None


class TestJobEndpoints:
    """Tests for job-related endpoints."""

    def test_get_jobs(self, client):
        """Test getting all jobs."""
        response = client.get('/jobs')

        assert response.status_code == 200
        jobs = response.json()
        assert isinstance(jobs, list)


class TestCandidateEndpoints:
    """Tests for candidate-related endpoints."""

    def test_get_candidates(self, client):
        """Test getting candidates."""
        response = client.get('/candidates?job_id=job_001')

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            candidates = response.json()
            assert isinstance(candidates, list)


class TestScreeningBatchEndpoint:
    """Tests for screening batch creation."""

    def test_create_batch_missing_job_id(self, client):
        """Test batch creation without job ID."""
        response = client.post('/screen/batch?candidate_ids=cand_001')

        assert response.status_code == 400

    def test_create_batch_missing_candidates(self, client):
        """Test batch creation without candidates."""
        response = client.post('/screen/batch?job_id=job_001')

        assert response.status_code == 400

    def test_create_batch_invalid_job(self, client):
        """Test batch creation with invalid job."""
        response = client.post(
            '/screen/batch?job_id=invalid_job&candidate_ids=cand_001'
        )

        assert response.status_code in [400, 404]

    def test_create_batch_success(self, client, test_db):
        """Test successful batch creation."""
        from backend.db.database import Job, Candidate

        # Create test data
        job = Job(
            id='job_test',
            title='Test Job',
            description='Test',
            required_skills=['Python'],
            archived=False
        )
        candidate = Candidate(
            id='cand_test',
            name='Test',
            email='test@example.com',
            resume_text='Python',
            parsed_skills=['Python'],
            experience_years=5
        )
        test_db.add(job)
        test_db.add(candidate)
        test_db.commit()

        response = client.post(
            '/screen/batch?job_id=job_test&candidate_ids=cand_test'
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('screenings_created') > 0
        assert data.get('screening_ids') is not None


class TestScreeningApprovalEndpoint:
    """Tests for screening approval/rejection."""

    def test_approve_non_existent_screening(self, client):
        """Test approving non-existent screening."""
        response = client.post(
            '/screen/invalid_id/approve',
            json={'approval_status': 'approved', 'feedback': 'test'}
        )

        assert response.status_code == 404

    def test_reject_non_existent_screening(self, client):
        """Test rejecting non-existent screening."""
        response = client.post(
            '/screen/invalid_id/reject',
            json={'approval_status': 'rejected', 'feedback': 'test'}
        )

        assert response.status_code == 404


class TestScreeningDetailEndpoint:
    """Tests for getting screening details."""

    def test_get_screening_detail_not_found(self, client):
        """Test getting non-existent screening."""
        response = client.get('/screen/invalid_id/detail')

        assert response.status_code == 404

    def test_get_screening_detail_missing_job(self, client, test_db):
        """Test getting screening when job is deleted."""
        from backend.db.database import Screening

        # Create screening with non-existent job/candidate
        screening = Screening(
            id='screen_test',
            job_id='job_invalid',
            candidate_id='cand_invalid',
            status='pending',
            approval_status='pending'
        )
        test_db.add(screening)
        test_db.commit()

        response = client.get('/screen/screen_test/detail')

        assert response.status_code == 404


class TestScreeningListEndpoint:
    """Tests for listing screenings."""

    def test_list_screenings_for_job_not_found(self, client):
        """Test listing screenings for non-existent job."""
        response = client.get('/screen/job/invalid_job/screenings')

        assert response.status_code == 200  # Should return empty list
        data = response.json()
        assert data.get('screenings') is not None
