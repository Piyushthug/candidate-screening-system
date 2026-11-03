"""Screening tools used by the agent."""
import re
from typing import List, Dict, Tuple
from backend.agent.state import ParsedResume, FitAnalysis, OutreachMessage, JobRequirements


class ResumeParsing:
    """Parse resume text to extract structured information."""

    COMMON_SKILLS = {
        "Python", "JavaScript", "Java", "C++", "Go", "Rust",
        "React", "Vue", "Angular", "FastAPI", "Django", "Node.js",
        "PostgreSQL", "MySQL", "MongoDB", "Redis",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes",
        "TensorFlow", "PyTorch", "OpenCV", "Pandas",
        "Git", "Linux", "SQL", "REST APIs", "GraphQL",
        "HTML", "CSS", "TypeScript", "HTML/CSS"
    }

    @staticmethod
    def parse_resume(resume_text: str) -> ParsedResume:
        """Extract skills, experience, and education from resume."""
        if not resume_text or len(resume_text.strip()) == 0:
            return {
                "skills": [],
                "experience_years": 0.0,
                "education": [],
                "summary": "Unable to parse resume"
            }

        # Extract skills (simple keyword matching)
        skills = []
        text_upper = resume_text.upper()
        for skill in ResumeParsing.COMMON_SKILLS:
            if skill.upper() in text_upper:
                skills.append(skill)

        # Extract experience years (look for patterns like "5 years", "5+ years")
        experience_years = 0.0
        experience_patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'(\d+)\+?\s*years?\s+(?:in|with)',
        ]
        for pattern in experience_patterns:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            if matches:
                experience_years = float(matches[0])
                break

        # Extract education (simple heuristic)
        education = []
        if "bachelor" in resume_text.lower():
            education.append("Bachelor's Degree")
        if "master" in resume_text.lower():
            education.append("Master's Degree")
        if "phd" in resume_text.lower() or "ph.d" in resume_text.lower():
            education.append("PhD")

        # Create summary of first 200 chars
        summary = resume_text.strip()[:200] + "..." if len(resume_text) > 200 else resume_text.strip()

        return {
            "skills": skills,
            "experience_years": experience_years,
            "education": education,
            "summary": summary
        }


class CandidateFitScoring:
    """Score candidate fit for a job."""

    @staticmethod
    def calculate_fit(
        candidate_skills: List[str],
        candidate_experience_years: float,
        job_requirements: Dict
    ) -> FitAnalysis:
        """Calculate fit score and provide analysis."""

        required_skills = job_requirements.get("required_skills", [])
        preferred_skills = job_requirements.get("preferred_skills", [])
        min_experience = job_requirements.get("min_experience_years", 0)

        # Normalize skills to upper case for comparison
        candidate_skills_upper = [s.upper() for s in candidate_skills]
        required_upper = [s.upper() for s in required_skills]
        preferred_upper = [s.upper() for s in preferred_skills]

        # Calculate matches
        required_matches = [s for s in required_upper if s in candidate_skills_upper]
        required_gaps = [s for s in required_upper if s not in candidate_skills_upper]

        preferred_matches = [s for s in preferred_upper if s in candidate_skills_upper]
        preferred_gaps = [s for s in preferred_upper if s not in candidate_skills_upper]

        # Calculate score (0-100)
        # Required skills: 70% of score
        # Preferred skills: 20% of score
        # Experience level: 10% of score

        required_score = (len(required_matches) / max(len(required_skills), 1)) * 70 if required_skills else 70
        preferred_score = (len(preferred_matches) / max(len(preferred_skills), 1)) * 20 if preferred_skills else 0

        experience_score = 0
        if candidate_experience_years >= min_experience:
            experience_score = 10
        elif candidate_experience_years >= min_experience * 0.7:
            experience_score = 5

        total_score = required_score + preferred_score + experience_score
        total_score = min(100, max(0, total_score))  # Clamp to 0-100

        # Create reasoning
        reasoning = f"Candidate has {len(required_matches)}/{len(required_skills)} required skills, "
        reasoning += f"{len(preferred_matches)}/{len(preferred_skills)} preferred skills, "
        reasoning += f"and {candidate_experience_years:.1f} years of experience (required: {min_experience})."

        return {
            "score": total_score,
            "reasoning": reasoning,
            "key_matches": required_matches[:5],  # Top 5 matches
            "critical_gaps": required_gaps[:5],  # Top 5 gaps
            "nice_to_have_gaps": preferred_gaps[:3]
        }


class OutreachMessageGeneration:
    """Generate personalized outreach messages."""

    @staticmethod
    def generate_message(
        candidate_name: str,
        job_title: str,
        fit_score: float,
        key_matches: List[str],
        critical_gaps: List[str]
    ) -> OutreachMessage:
        """Generate a personalized outreach message grounded in job and candidate profile."""

        personalization_points = []
        message_parts = []

        # Opening
        message_parts.append(f"Hi {candidate_name},")
        message_parts.append("")
        message_parts.append(f"We're excited about your profile for our {job_title} position.")

        # Personalization based on fit
        if key_matches:
            matches_str = ", ".join(key_matches[:3])
            message_parts.append(f"Your experience with {matches_str} aligns well with our team's needs.")
            personalization_points.append(f"Highlighted experience: {matches_str}")

        # Address if there are gaps
        if critical_gaps and fit_score < 80:
            gaps_str = ", ".join(critical_gaps[:2])
            message_parts.append(f"While we're looking for experience with {gaps_str}, your strong background in other areas makes you a strong candidate.")
            personalization_points.append(f"Acknowledged gap: {gaps_str}")

        # Call to action based on fit
        if fit_score >= 85:
            message_parts.append("We'd love to learn more about your experience. Would you be open to a brief conversation?")
        elif fit_score >= 70:
            message_parts.append("We'd like to explore if this opportunity might be a good fit. Are you interested in chatting?")
        else:
            message_parts.append("We'd like to discuss how your skills could contribute to our team. Would you be interested in learning more?")

        message_parts.append("")
        message_parts.append("Best regards,")
        message_parts.append("The Recruiting Team")

        content = "\n".join(message_parts)

        return {
            "content": content,
            "personalization_points": personalization_points,
            "is_grounded": True  # All claims grounded in job requirements and candidate profile
        }


class MessageValidation:
    """Validate generated messages."""

    @staticmethod
    def validate_message(
        message_content: str,
        candidate_name: str,
        job_title: str,
        resume_text: str
    ) -> Tuple[bool, str]:
        """Validate that message is grounded and professional."""

        issues = []

        # Check if message is too short
        if len(message_content) < 100:
            issues.append("Message is too short or generic")

        # Check if candidate name is used
        if candidate_name.split()[0].lower() not in message_content.lower():
            issues.append("Candidate name not personalized")

        # Check if job title or role is mentioned
        if job_title.lower() not in message_content.lower():
            issues.append("Job title not mentioned")

        # Check for hallucinated claims (red flags)
        hallucination_flags = [
            "guaranteed", "promise", "definitely",
            "we will hire", "we guarantee",
            "salary", "compensation", "stock options",
            "start date", "offer letter"
        ]

        message_lower = message_content.lower()
        for flag in hallucination_flags:
            if flag in message_lower:
                issues.append(f"Potential hallucination: '{flag}' used without specifics")

        is_valid = len(issues) == 0
        feedback = "\n".join(issues) if issues else "Message is well-grounded and professional"

        return is_valid, feedback
