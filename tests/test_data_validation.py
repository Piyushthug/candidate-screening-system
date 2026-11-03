"""Data validation tests."""
import pytest
import json
from pathlib import Path
from backend.db.database import Job, Candidate


class TestJobData:
    """Tests for job data validation."""

    def test_jobs_fixture_valid(self):
        """Test that jobs.json is valid."""
        jobs_file = Path(__file__).parent.parent / "backend" / "data" / "jobs.json"

        with open(jobs_file) as f:
            jobs = json.load(f)

        assert isinstance(jobs, list)
        assert len(jobs) >= 5

        for job in jobs:
            assert "id" in job
            assert "title" in job
            assert "description" in job
            assert "requirements" in job
            assert "level" in job

            # Validate IDs
            assert job["id"].startswith("job_")

            # Validate levels
            assert job["level"] in ["junior", "mid", "senior"]

            # Validate requirements is a list
            assert isinstance(job["requirements"], list)
            assert len(job["requirements"]) > 0

    def test_job_model_from_fixture(self, db_session):
        """Test creating Job models from fixture data."""
        jobs = db_session.query(Job).all()

        assert len(jobs) >= 5

        job = jobs[0]
        assert job.id
        assert job.title
        assert job.archived is False
        assert job.created_at is not None

    def test_archived_job_excluded_from_list(self, db_session):
        """Test that archived jobs are excluded from active list."""
        # Get all jobs
        all_jobs = db_session.query(Job).all()
        assert len(all_jobs) >= 5

        # Archive one job
        job = db_session.query(Job).first()
        job.archived = True
        db_session.commit()

        # Check active jobs count
        active_jobs = db_session.query(Job).filter(Job.archived == False).all()
        assert len(active_jobs) == len(all_jobs) - 1


class TestCandidateData:
    """Tests for candidate data validation."""

    def test_candidates_fixture_valid(self):
        """Test that candidates.json is valid."""
        candidates_file = Path(__file__).parent.parent / "backend" / "data" / "candidates.json"

        with open(candidates_file) as f:
            candidates = json.load(f)

        assert isinstance(candidates, list)
        assert len(candidates) >= 10

        for candidate in candidates:
            assert "id" in candidate
            assert "name" in candidate
            assert "email" in candidate
            assert "resume_text" in candidate

            # Validate IDs
            assert candidate["id"].startswith("cand_")

            # Validate email format (simple check)
            assert "@" in candidate["email"]

            # Validate resume is not empty
            assert len(candidate["resume_text"]) > 0

    def test_candidate_model_from_fixture(self, db_session):
        """Test creating Candidate models from fixture data."""
        candidates = db_session.query(Candidate).all()

        assert len(candidates) >= 10

        candidate = candidates[0]
        assert candidate.id
        assert candidate.name
        assert candidate.email
        assert candidate.resume_text
        assert candidate.created_at is not None

    def test_candidate_skills_extraction(self, db_session):
        """Test that candidate skills can be extracted."""
        from backend.tools.screening_tools import ResumeParsing

        candidate = db_session.query(Candidate).first()

        parsed = ResumeParsing.parse_resume(candidate.resume_text)

        assert parsed["experience_years"] >= 0
        assert isinstance(parsed["skills"], list)
        assert isinstance(parsed["education"], list)


class TestDataConsistency:
    """Tests for data consistency."""

    def test_no_duplicate_job_ids(self, db_session):
        """Test that job IDs are unique."""
        jobs = db_session.query(Job).all()
        ids = [j.id for j in jobs]

        assert len(ids) == len(set(ids))

    def test_no_duplicate_candidate_ids(self, db_session):
        """Test that candidate IDs are unique."""
        candidates = db_session.query(Candidate).all()
        ids = [c.id for c in candidates]

        assert len(ids) == len(set(ids))

    def test_job_requirements_have_multiple_skills(self, db_session):
        """Test that each job has multiple required skills."""
        jobs = db_session.query(Job).all()

        for job in jobs:
            assert len(job.requirements) >= 3


class TestDataTransformation:
    """Tests for data transformation during screening."""

    def test_candidate_resume_parsing_preserves_info(self, db_session):
        """Test that resume parsing preserves important information."""
        from backend.tools.screening_tools import ResumeParsing

        candidate = db_session.query(Candidate).filter(
            Candidate.id == "cand_001"
        ).first()

        parsed = ResumeParsing.parse_resume(candidate.resume_text)

        # Alice has 7 years of experience in her resume
        assert parsed["experience_years"] >= 6
        assert "Python" in parsed["skills"]
        assert "FastAPI" in parsed["skills"] or "Django" in parsed["skills"]

    def test_fit_scoring_returns_valid_score(self, db_session):
        """Test that fit scoring returns valid 0-100 score."""
        from backend.tools.screening_tools import CandidateFitScoring

        candidate = db_session.query(Candidate).filter(
            Candidate.id == "cand_001"
        ).first()

        job = db_session.query(Job).filter(
            Job.id == "job_001"
        ).first()

        parsed = ResumeParsing.parse_resume(candidate.resume_text)

        fit = CandidateFitScoring.calculate_fit(
            parsed["skills"],
            parsed["experience_years"],
            {
                "required_skills": job.requirements,
                "preferred_skills": [],
                "min_experience_years": 3
            }
        )

        assert 0 <= fit["score"] <= 100
        assert "reasoning" in fit
        assert "key_matches" in fit
        assert "critical_gaps" in fit


class TestFixtureDataQuality:
    """Tests for overall quality of fixture data."""

    def test_jobs_and_candidates_mismatch(self, db_session):
        """Test that we have meaningful variation between jobs and candidates."""
        from backend.tools.screening_tools import ResumeParsing, CandidateFitScoring

        jobs = db_session.query(Job).all()
        candidates = db_session.query(Candidate).all()

        # Get fit scores for all combinations
        fit_scores = []

        for job in jobs[:3]:  # Check first 3 jobs
            for candidate in candidates[:3]:  # Check first 3 candidates
                parsed = ResumeParsing.parse_resume(candidate.resume_text)

                fit = CandidateFitScoring.calculate_fit(
                    parsed["skills"],
                    parsed["experience_years"],
                    {
                        "required_skills": job.requirements,
                        "preferred_skills": [],
                        "min_experience_years": 3
                    }
                )

                fit_scores.append(fit["score"])

        # Ensure we have variation in scores (not all perfect matches)
        assert min(fit_scores) < 100
        assert max(fit_scores) > 50

        # Ensure average is reasonable
        avg_score = sum(fit_scores) / len(fit_scores)
        assert 40 < avg_score < 90
