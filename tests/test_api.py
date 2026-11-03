"""API endpoint tests."""
import pytest
import uuid
from backend.db.database import Job, Candidate, Screening
from backend.services.screening_service import ScreeningService


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestJobEndpoints:
    """Tests for job endpoints."""

    def test_list_jobs(self, client, db_session):
        """Test listing all jobs."""
        response = client.get("/jobs")

        assert response.status_code == 200
        jobs = response.json()
        assert len(jobs) >= 5  # We loaded sample data

    def test_get_specific_job(self, client, db_session):
        """Test getting a specific job."""
        response = client.get("/jobs/job_001")

        assert response.status_code == 200
        job = response.json()
        assert job["id"] == "job_001"
        assert "Senior" in job["title"]

    def test_get_nonexistent_job(self, client):
        """Test getting a job that doesn't exist."""
        response = client.get("/jobs/nonexistent")

        assert response.status_code == 404


class TestCandidateEndpoints:
    """Tests for candidate endpoints."""

    def test_list_candidates(self, client, db_session):
        """Test listing all candidates."""
        response = client.get("/candidates")

        assert response.status_code == 200
        candidates = response.json()
        assert len(candidates) >= 10  # We loaded sample data

    def test_get_specific_candidate(self, client, db_session):
        """Test getting a specific candidate."""
        response = client.get("/candidates/cand_001")

        assert response.status_code == 200
        candidate = response.json()
        assert candidate["id"] == "cand_001"
        assert candidate["name"] == "Alice Johnson"

    def test_get_candidates_for_job(self, client, db_session):
        """Test getting candidates for a specific job."""
        response = client.get("/jobs/job_001/candidates")

        assert response.status_code == 200
        candidates = response.json()
        assert len(candidates) >= 10


class TestScreeningBatch:
    """Tests for screening batch endpoints."""

    def test_start_batch_screening(self, client, db_session):
        """Test starting a screening batch."""
        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001", "candidate_ids": ["cand_001", "cand_002"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job_001"
        assert data["screenings_created"] == 2

    def test_batch_screening_all_candidates(self, client, db_session):
        """Test starting batch with all candidates."""
        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["screenings_created"] >= 10

    def test_batch_screening_invalid_job(self, client):
        """Test batch screening with invalid job."""
        response = client.post(
            "/screen/batch",
            params={"job_id": "nonexistent"}
        )

        assert response.status_code == 404

    def test_batch_screening_archived_job(self, client, db_session):
        """Test batch screening with archived job."""
        # Archive a job
        job = db_session.query(Job).filter(Job.id == "job_001").first()
        job.archived = True
        db_session.commit()

        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001"}
        )

        assert response.status_code == 400


class TestScreeningWorkflow:
    """Tests for screening workflow."""

    def test_start_workflow(self, client, db_session):
        """Test starting a screening workflow."""
        # Create a screening
        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001", "candidate_ids": ["cand_001"]}
        )
        screening_id = response.json()["screening_ids"][0]

        # Start workflow
        response = client.post(f"/screen/{screening_id}/start-workflow")

        assert response.status_code == 200
        data = response.json()
        assert data["screening_id"] == screening_id
        assert data["fit_score"] is not None
        assert data["approval_status"] in ["pending", "escalated"]

    def test_get_screening(self, client, db_session):
        """Test getting screening details."""
        # Create screening
        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001", "candidate_ids": ["cand_001"]}
        )
        screening_id = response.json()["screening_ids"][0]

        # Get screening
        response = client.get(f"/screen/{screening_id}")

        assert response.status_code == 200
        screening = response.json()
        assert screening["id"] == screening_id
        assert screening["job_id"] == "job_001"

    def test_get_screening_detail(self, client, db_session):
        """Test getting detailed screening info."""
        # Create and run screening
        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001", "candidate_ids": ["cand_001"]}
        )
        screening_id = response.json()["screening_ids"][0]

        client.post(f"/screen/{screening_id}/start-workflow")

        # Get detail
        response = client.get(f"/screen/{screening_id}/detail")

        assert response.status_code == 200
        detail = response.json()
        assert "screening" in detail
        assert "job" in detail
        assert "candidate" in detail


class TestScreeningApproval:
    """Tests for screening approval/rejection."""

    def test_approve_screening(self, client, db_session):
        """Test approving a screening."""
        # Create and run screening
        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001", "candidate_ids": ["cand_001"]}
        )
        screening_id = response.json()["screening_ids"][0]

        client.post(f"/screen/{screening_id}/start-workflow")

        # Approve
        response = client.post(
            f"/screen/{screening_id}/approve",
            json={"approval_status": "approved", "feedback": "Great candidate"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"

    def test_reject_screening(self, client, db_session):
        """Test rejecting a screening."""
        # Create and run screening
        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001", "candidate_ids": ["cand_001"]}
        )
        screening_id = response.json()["screening_ids"][0]

        client.post(f"/screen/{screening_id}/start-workflow")

        # Reject
        response = client.post(
            f"/screen/{screening_id}/reject",
            json={"approval_status": "rejected", "feedback": "Skills don't match"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "rejected"

    def test_approve_with_wrong_endpoint(self, client, db_session):
        """Test that approve endpoint rejects wrong approval_status."""
        response = client.post(
            "/screen/batch",
            params={"job_id": "job_001", "candidate_ids": ["cand_001"]}
        )
        screening_id = response.json()["screening_ids"][0]

        client.post(f"/screen/{screening_id}/start-workflow")

        # Try to reject using approve endpoint
        response = client.post(
            f"/screen/{screening_id}/approve",
            json={"approval_status": "rejected"}
        )

        assert response.status_code == 400


class TestScreeningErrors:
    """Tests for screening error handling."""

    def test_workflow_on_invalid_screening(self, client):
        """Test workflow on non-existent screening."""
        response = client.post("/screen/nonexistent/start-workflow")

        assert response.status_code == 404

    def test_approve_nonexistent_screening(self, client):
        """Test approving non-existent screening."""
        response = client.post(
            "/screen/nonexistent/approve",
            json={"approval_status": "approved"}
        )

        assert response.status_code == 404

    def test_reject_nonexistent_screening(self, client):
        """Test rejecting non-existent screening."""
        response = client.post(
            "/screen/nonexistent/reject",
            json={"approval_status": "rejected"}
        )

        assert response.status_code == 404

    def test_list_screenings_for_job(self, client, db_session):
        """Test listing screenings for a job."""
        # Create screening
        client.post(
            "/screen/batch",
            params={"job_id": "job_001", "candidate_ids": ["cand_001", "cand_002"]}
        )

        # List screenings
        response = client.get("/screen/job/job_001/screenings")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["screenings"]) == 2
