"""Screening business logic service."""
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from backend.db.database import Job, Candidate, Screening, AuditLog
from backend.agent.state import ScreeningState, JobRequirements
from backend.tools.screening_tools import (
    ResumeParsing, CandidateFitScoring, OutreachMessageGeneration, MessageValidation
)

logger = logging.getLogger(__name__)


class ScreeningService:
    """Service for candidate screening workflows."""

    @staticmethod
    def create_screening(
        screening_id: str,
        job_id: str,
        candidate_id: str,
        db: Session
    ) -> Screening:
        """Create a new screening record."""

        screening = Screening(
            id=screening_id,
            job_id=job_id,
            candidate_id=candidate_id,
            approval_status="pending",
            status="pending"
        )

        db.add(screening)
        db.commit()
        db.refresh(screening)

        # Log audit trail
        ScreeningService.log_action(
            db,
            screening_id,
            "created",
            {"job_id": job_id, "candidate_id": candidate_id}
        )

        return screening

    @staticmethod
    def update_screening_status(
        screening_id: str,
        status: str,
        db: Session
    ) -> Screening:
        """Update screening status."""

        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise ValueError(f"Screening {screening_id} not found")

        old_status = screening.status
        screening.status = status
        screening.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(screening)

        ScreeningService.log_action(
            db,
            screening_id,
            f"status_changed",
            {"from": old_status, "to": status}
        )

        return screening

    @staticmethod
    def update_fit_score(
        screening_id: str,
        fit_score: float,
        fit_reasoning: str,
        db: Session
    ) -> Screening:
        """Update fit score and reasoning."""

        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise ValueError(f"Screening {screening_id} not found")

        screening.fit_score = fit_score
        screening.fit_reasoning = fit_reasoning
        screening.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(screening)

        ScreeningService.log_action(
            db,
            screening_id,
            "fit_score_calculated",
            {"score": fit_score}
        )

        return screening

    @staticmethod
    def update_generated_message(
        screening_id: str,
        message: str,
        db: Session
    ) -> Screening:
        """Store generated message."""

        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise ValueError(f"Screening {screening_id} not found")

        screening.generated_message = message
        screening.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(screening)

        ScreeningService.log_action(
            db,
            screening_id,
            "message_generated",
            {"message_length": len(message)}
        )

        return screening

    @staticmethod
    def approve_screening(
        screening_id: str,
        feedback: str = None,
        db: Session = None
    ) -> Screening:
        """Approve a screening and mark for sending."""

        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise ValueError(f"Screening {screening_id} not found")

        screening.approval_status = "approved"
        screening.approval_feedback = feedback
        screening.status = "approved"
        screening.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(screening)

        ScreeningService.log_action(
            db,
            screening_id,
            "approved",
            {"feedback": feedback}
        )

        return screening

    @staticmethod
    def reject_screening(
        screening_id: str,
        feedback: str = None,
        db: Session = None
    ) -> Screening:
        """Reject a screening."""

        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise ValueError(f"Screening {screening_id} not found")

        screening.approval_status = "rejected"
        screening.approval_feedback = feedback
        screening.status = "rejected"
        screening.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(screening)

        ScreeningService.log_action(
            db,
            screening_id,
            "rejected",
            {"feedback": feedback}
        )

        return screening

    @staticmethod
    def log_action(db: Session, screening_id: str, action: str, details: dict):
        """Log an action in the audit trail."""
        log = AuditLog(
            screening_id=screening_id,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()

    @staticmethod
    def get_screening_state(
        job_id: str,
        candidate_id: str,
        db: Session
    ) -> ScreeningState:
        """Build screening state from database."""

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.archived:
            raise ValueError(f"Job {job_id} is archived - cannot screen")

        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        # Extract job requirements from requirements JSON
        job_requirements: JobRequirements = {
            "required_skills": job.requirements if isinstance(job.requirements, list) else [],
            "preferred_skills": [],
            "min_experience_years": 0,
            "level": job.level or "mid"
        }

        # Parse candidate resume
        parsed_resume = ResumeParsing.parse_resume(candidate.resume_text)

        # Calculate fit
        fit_analysis = CandidateFitScoring.calculate_fit(
            parsed_resume["skills"],
            parsed_resume["experience_years"],
            job_requirements
        )

        # Build state
        state: ScreeningState = {
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "resume_text": candidate.resume_text,
            "job_id": job.id,
            "job_title": job.title,
            "job_description": job.description,
            "parsed_resume": parsed_resume,
            "job_requirements": job_requirements,
            "fit_analysis": fit_analysis,
            "approval_status": "pending",
            "step": "initialized",
            "retry_count": 0
        }

        return state

    @staticmethod
    def run_screening_workflow(
        screening_id: str,
        job_id: str,
        candidate_id: str,
        db: Session
    ):
        """Run the complete screening workflow."""

        try:
            logger.info(f"Starting screening {screening_id} for candidate {candidate_id}, job {job_id}")

            # Get screening state
            state = ScreeningService.get_screening_state(job_id, candidate_id, db)
            state["screening_id"] = screening_id

            # Update status
            ScreeningService.update_screening_status(screening_id, "analyzing", db)
            state["step"] = "fit_analysis"

            # Calculate fit (already done in state)
            fit_score = state["fit_analysis"]["score"]
            fit_reasoning = state["fit_analysis"]["reasoning"]

            ScreeningService.update_fit_score(
                screening_id,
                fit_score,
                fit_reasoning,
                db
            )

            # Generate outreach message
            state["step"] = "message_generation"
            message_data = OutreachMessageGeneration.generate_message(
                state["candidate_name"],
                state["job_title"],
                fit_score,
                state["fit_analysis"]["key_matches"],
                state["fit_analysis"]["critical_gaps"]
            )
            state["generated_message"] = message_data

            # Validate message
            is_valid, validation_feedback = MessageValidation.validate_message(
                message_data["content"],
                state["candidate_name"],
                state["job_title"],
                state["resume_text"]
            )

            if not is_valid:
                state["step"] = "validation_failed"
                ScreeningService.update_screening_status(
                    screening_id,
                    "validation_failed",
                    db
                )
                ScreeningService.log_action(
                    db,
                    screening_id,
                    "validation_failed",
                    {"reason": validation_feedback}
                )
                logger.warning(f"Validation failed for screening {screening_id}: {validation_feedback}")
                return state

            # Store message
            ScreeningService.update_generated_message(
                screening_id,
                message_data["content"],
                db
            )

            # Mark as ready for approval
            state["step"] = "pending_approval"
            ScreeningService.update_screening_status(
                screening_id,
                "pending_approval",
                db
            )

            logger.info(f"Screening {screening_id} completed, awaiting approval")

            return state

        except Exception as e:
            logger.error(f"Error in screening workflow {screening_id}: {str(e)}", exc_info=True)
            try:
                ScreeningService.update_screening_status(
                    screening_id,
                    "escalated",
                    db
                )
            except:
                pass
            raise
