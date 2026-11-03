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
        candidate = {
            'skills': ['Python', 'FastAPI', 'PostgreSQL'],
            'experience_years': 7
        }
        job_requirements = {
            'required_skills': ['Python', 'FastAPI'],
            'preferred_skills': [],
            'min_experience': 5
        }
        
        result = CandidateFitScoring.calculate_fit(candidate, job_requirements)
        
        assert result is not None
        assert 'fit_score' in result
        assert 0 <= result['fit_score'] <= 100


class TestMessageGeneration:
    """Tests for message generation."""
    
    def test_generate_message(self):
        """Test generating outreach message."""
        candidate = {'name': 'John Doe', 'skills': ['Python']}
        job = {'title': 'Python Engineer'}
        fit_analysis = {'fit_score': 85}
        
        result = OutreachMessageGeneration.generate_message(candidate, job, fit_analysis)
        
        assert result is not None
        assert isinstance(result, dict)


class TestMessageValidation:
    """Tests for message validation."""
    
    def test_validate_message(self):
        """Test message validation."""
        message = "Hello, we are interested in your profile"
        
        result = MessageValidation.validate_message(message, "Python Engineer", ["Python"])
        
        assert result is not None
        assert isinstance(result, dict)
