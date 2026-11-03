"""Pytest configuration and shared fixtures."""
import pytest
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def sample_candidate():
    """Sample candidate data."""
    return {
        'id': 'cand_001',
        'name': 'Alice Johnson',
        'email': 'alice@example.com',
        'resume_text': 'Senior Python Engineer with 7 years experience',
        'parsed_skills': ['Python', 'FastAPI', 'PostgreSQL', 'AWS'],
        'experience_years': 7
    }


@pytest.fixture
def sample_job():
    """Sample job data."""
    return {
        'id': 'job_001',
        'title': 'Senior Python Engineer',
        'description': 'Experienced Python engineer needed',
        'required_skills': ['Python', 'FastAPI', 'PostgreSQL'],
        'preferred_skills': ['AWS', 'Docker'],
        'experience_years': 5,
        'level': 'senior'
    }


@pytest.fixture
def sample_screening():
    """Sample screening data."""
    return {
        'id': 'screening_001',
        'job_id': 'job_001',
        'candidate_id': 'cand_001',
        'status': 'pending_approval',
        'approval_status': 'pending',
        'fit_score': 85,
        'fit_reasoning': 'Strong match',
        'generated_message': 'Dear Alice, interested'
    }
