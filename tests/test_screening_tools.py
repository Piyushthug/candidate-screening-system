"""Unit tests for screening tools."""
import pytest
from backend.tools.screening_tools import (
    ResumeParsing,
    CandidateFitScoring,
    OutreachMessageGeneration,
    MessageValidation
)


class TestResumeParser:
    """Tests for resume parsing."""
    
    def test_parse_basic_resume(self):
        """Test parsing a basic resume."""
        resume_text = "Senior Python Engineer with 5 years experience. Skills: Python, FastAPI, PostgreSQL"
        result = ResumeParsing.parse_resume(resume_text)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'experience_years' in result
    
    def test_parse_empty_resume(self):
        """Test parsing empty resume."""
        result = ResumeParsing.parse_resume("")
        
        assert result is not None
        assert result.get('experience_years') == 0.0


class TestFitScoring:
    """Tests for fit score calculation."""

    def test_calculate_fit(self):
        """Test calculating fit score."""
        candidate_skills = ['Python', 'FastAPI', 'PostgreSQL']
        candidate_experience_years = 7
        job_requirements = {
            'required_skills': ['Python', 'FastAPI'],
            'preferred_skills': [],
            'min_experience_years': 5
        }

        result = CandidateFitScoring.calculate_fit(
            candidate_skills, candidate_experience_years, job_requirements
        )

        assert result is not None
        assert 'score' in result
        assert 0 <= result['score'] <= 100


class TestMessageGeneration:
    """Tests for message generation."""

    def test_generate_message(self):
        """Test generating outreach message."""
        candidate_name = 'John Doe'
        job_title = 'Python Engineer'
        fit_score = 85
        key_matches = ['Python', 'FastAPI']
        critical_gaps = []

        result = OutreachMessageGeneration.generate_message(
            candidate_name, job_title, fit_score, key_matches, critical_gaps
        )

        assert result is not None
        assert isinstance(result, dict)
        assert 'content' in result
        assert 'John' in result['content']


class TestMessageValidation:
    """Tests for message validation."""

    def test_validate_message(self):
        """Test message validation."""
        message_content = "Hi John Doe, we are interested in your profile for the Python Engineer position. Your Python skills align well with our team."
        candidate_name = "John Doe"
        job_title = "Python Engineer"
        resume_text = "John Doe, 5 years Python experience with FastAPI"

        is_valid, feedback = MessageValidation.validate_message(
            message_content, candidate_name, job_title, resume_text
        )

        assert isinstance(is_valid, bool)
        assert isinstance(feedback, str)
