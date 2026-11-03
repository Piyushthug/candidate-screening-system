"""Unit tests for screening tools."""
import pytest
from backend.tools.screening_tools import (
    ResumeParsing, CandidateFitScoring, OutreachMessageGeneration, MessageValidation
)


class TestResumeParsing:
    """Tests for resume parsing."""

    def test_parse_good_resume(self, good_resume):
        """Test parsing a well-formed resume."""
        result = ResumeParsing.parse_resume(good_resume)

        assert result["experience_years"] >= 7
        assert len(result["skills"]) > 0
        assert "Python" in result["skills"]
        assert "Docker" in result["skills"]
        assert len(result["education"]) > 0

    def test_parse_malformed_resume(self, malformed_resume):
        """Test parsing a resume with missing information."""
        result = ResumeParsing.parse_resume(malformed_resume)

        assert result["experience_years"] == 0
        assert len(result["skills"]) == 0

    def test_parse_empty_resume(self, empty_resume):
        """Test parsing an empty resume."""
        result = ResumeParsing.parse_resume(empty_resume)

        assert result["experience_years"] == 0
        assert result["skills"] == []
        assert result["education"] == []

    def test_extract_skills(self, good_resume):
        """Test skill extraction."""
        result = ResumeParsing.parse_resume(good_resume)

        required_skills = ["Python", "FastAPI", "Docker", "PostgreSQL"]
        found_skills = [s for s in required_skills if s in result["skills"]]

        assert len(found_skills) >= 3


class TestCandidateFitScoring:
    """Tests for candidate fit scoring."""

    def test_perfect_fit(self, sample_job_requirements):
        """Test scoring when candidate has all required skills."""
        candidate_skills = ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"]
        candidate_experience = 5

        result = CandidateFitScoring.calculate_fit(
            candidate_skills,
            candidate_experience,
            sample_job_requirements
        )

        assert result["score"] >= 80
        assert "Python" in result["key_matches"]
        assert len(result["critical_gaps"]) == 0

    def test_partial_fit(self, sample_job_requirements):
        """Test scoring when candidate has some required skills."""
        candidate_skills = ["Python", "Docker"]
        candidate_experience = 3

        result = CandidateFitScoring.calculate_fit(
            candidate_skills,
            candidate_experience,
            sample_job_requirements
        )

        assert 50 < result["score"] < 80
        assert "FastAPI" in result["critical_gaps"]
        assert len(result["key_matches"]) > 0

    def test_low_fit(self, sample_job_requirements):
        """Test scoring when candidate lacks most skills."""
        candidate_skills = ["JavaScript", "Ruby"]
        candidate_experience = 1

        result = CandidateFitScoring.calculate_fit(
            candidate_skills,
            candidate_experience,
            sample_job_requirements
        )

        assert result["score"] < 50
        assert len(result["critical_gaps"]) >= 2

    def test_score_bounds(self, sample_job_requirements):
        """Test that score is always 0-100."""
        for candidate_skills in [[], ["Python"], ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"]]:
            result = CandidateFitScoring.calculate_fit(
                candidate_skills,
                10,
                sample_job_requirements
            )
            assert 0 <= result["score"] <= 100


class TestOutreachMessageGeneration:
    """Tests for message generation."""

    def test_generate_message_high_fit(self):
        """Test message generation for high fit candidate."""
        message = OutreachMessageGeneration.generate_message(
            "Alice",
            "Senior Python Engineer",
            score=90,
            key_matches=["Python", "FastAPI", "PostgreSQL"],
            critical_gaps=[]
        )

        assert "Alice" in message["content"]
        assert "Senior Python Engineer" in message["content"]
        assert "excited" in message["content"].lower() or "interested" in message["content"].lower()
        assert message["is_grounded"] is True

    def test_generate_message_medium_fit(self):
        """Test message generation for medium fit candidate."""
        message = OutreachMessageGeneration.generate_message(
            "Bob",
            "Backend Engineer",
            score=70,
            key_matches=["Python"],
            critical_gaps=["FastAPI", "PostgreSQL"]
        )

        assert "Bob" in message["content"]
        assert "Backend Engineer" in message["content"]

    def test_generate_message_low_fit(self):
        """Test message generation for low fit candidate."""
        message = OutreachMessageGeneration.generate_message(
            "Charlie",
            "DevOps Engineer",
            score=45,
            key_matches=[],
            critical_gaps=["Kubernetes", "Docker", "AWS"]
        )

        assert "Charlie" in message["content"]
        assert "DevOps Engineer" in message["content"]

    def test_personalization_points(self):
        """Test that personalization points are recorded."""
        message = OutreachMessageGeneration.generate_message(
            "Diana",
            "ML Engineer",
            score=85,
            key_matches=["Python", "TensorFlow"],
            critical_gaps=[]
        )

        assert len(message["personalization_points"]) > 0


class TestMessageValidation:
    """Tests for message validation."""

    def test_validate_good_message(self):
        """Test validation of a good message."""
        message = """Hi Alice,

We're excited about your profile for our Senior Python Engineer position.
Your experience with Python, FastAPI aligns well with our team's needs.

We'd love to learn more about your experience. Would you be open to a brief conversation?

Best regards,
The Recruiting Team"""

        is_valid, feedback = MessageValidation.validate_message(
            message,
            "Alice",
            "Senior Python Engineer",
            "7 years Python experience"
        )

        assert is_valid is True

    def test_validate_generic_message(self):
        """Test validation of a generic/too-short message."""
        message = "Hi there!"

        is_valid, feedback = MessageValidation.validate_message(
            message,
            "Alice",
            "Senior Python Engineer",
            "7 years Python experience"
        )

        assert is_valid is False
        assert "short" in feedback.lower()

    def test_validate_missing_candidate_name(self):
        """Test validation when candidate name not personalized."""
        message = """Hello there,

We have a Senior Python Engineer role that might interest you.
Please let us know if you're interested.

Best regards,
The Recruiting Team"""

        is_valid, feedback = MessageValidation.validate_message(
            message,
            "Alice",
            "Senior Python Engineer",
            "7 years Python experience"
        )

        assert is_valid is False
        assert "name" in feedback.lower()

    def test_validate_hallucinated_promises(self):
        """Test detection of hallucinated promises."""
        message = """Hi Alice,

We're excited about your profile for our Senior Python Engineer position.
We guarantee you'll get a $200k salary and start next Monday.

Best regards,
The Recruiting Team"""

        is_valid, feedback = MessageValidation.validate_message(
            message,
            "Alice",
            "Senior Python Engineer",
            "7 years Python experience"
        )

        assert is_valid is False
        assert "hallucination" in feedback.lower() or "salary" in feedback.lower()
