"""Unit tests for screening service business logic."""
import pytest
from backend.services.screening_service import ScreeningService
from backend.db.database import Screening, Job, Candidate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    from backend.db.database import Base
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test data
    job = Job(
        id='job_test',
        title='Test Engineer',
        description='Test job',
        required_skills=['Python', 'Testing'],
        preferred_skills=['FastAPI'],
        level='mid',
        archived=False
    )
    session.add(job)

    candidate = Candidate(
        id='cand_test',
        name='Test Candidate',
        email='test@example.com',
        resume_text='Python developer with 5 years experience',
        parsed_skills=['Python', 'Testing', 'FastAPI'],
        experience_years=5
    )
    session.add(candidate)
    session.commit()

    yield session

    session.close()


class TestScreeningService:
    """Tests for ScreeningService methods."""

    def test_create_screening(self, db_session):
        """Test screening creation."""
        screening = ScreeningService.create_screening(
            'screening_test',
            'job_test',
            'cand_test',
            db_session
        )

        assert screening.id == 'screening_test'
        assert screening.job_id == 'job_test'
        assert screening.candidate_id == 'cand_test'
        assert screening.status == 'pending_workflow'
        assert screening.approval_status == 'pending'

    def test_approve_screening(self, db_session):
        """Test screening approval."""
        screening = ScreeningService.create_screening(
            'screening_test',
            'job_test',
            'cand_test',
            db_session
        )
        screening.status = 'pending_approval'
        screening.fit_score = 85
        db_session.commit()

        result = ScreeningService.approve_screening(
            'screening_test',
            'Approved by recruiter',
            db_session
        )

        assert result.approval_status == 'approved'
        assert result.status == 'approved'

    def test_reject_screening(self, db_session):
        """Test screening rejection."""
        screening = ScreeningService.create_screening(
            'screening_test',
            'job_test',
            'cand_test',
            db_session
        )
        screening.status = 'pending_approval'
        screening.fit_score = 25
        db_session.commit()

        result = ScreeningService.reject_screening(
            'screening_test',
            'Rejected by recruiter',
            db_session
        )

        assert result.approval_status == 'rejected'
        assert result.status == 'rejected'

    def test_cannot_approve_non_pending_screening(self, db_session):
        """Test that approved screenings cannot be approved again."""
        screening = ScreeningService.create_screening(
            'screening_test',
            'job_test',
            'cand_test',
            db_session
        )
        screening.status = 'pending_approval'
        screening.approval_status = 'approved'
        db_session.commit()

        with pytest.raises(ValueError):
            ScreeningService.approve_screening(
                'screening_test',
                'Feedback',
                db_session
            )

    def test_screening_state_transitions(self, db_session):
        """Test valid state transitions for screening."""
        screening = ScreeningService.create_screening(
            'screening_test',
            'job_test',
            'cand_test',
            db_session
        )

        # Initial state
        assert screening.status == 'pending_workflow'
        assert screening.approval_status == 'pending'

        # Move to pending_approval (after workflow)
        screening.status = 'pending_approval'
        screening.fit_score = 75
        db_session.commit()

        # Approve
        approved = ScreeningService.approve_screening(
            'screening_test',
            'Good fit',
            db_session
        )
        assert approved.status == 'approved'
        assert approved.approval_status == 'approved'
