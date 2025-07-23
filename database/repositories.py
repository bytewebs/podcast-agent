from database.models import PodcastJob, EvaluationResult, GuardrailResult, JobStatus
from database.connection import SessionLocal
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class PodcastRepository:
    def __init__(self):
        self.session_factory = SessionLocal
    
    def _get_session(self):
        """Get a new database session"""
        return self.session_factory()
    
    def create_job(self, job_id: str, brief: dict) -> PodcastJob:
        """Create a new podcast job"""
        session = self._get_session()
        try:
            job = PodcastJob()
            job.job_id = job_id
            job.brief = brief
            job.status = JobStatus.PENDING

            session.add(job)
            session.commit()
            session.refresh(job)
            return job
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating job: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_job(self, job_id: str) -> Optional[PodcastJob]:
        """Get job by ID"""
        session = self._get_session()
        try:
            return session.query(PodcastJob).filter(PodcastJob.job_id == job_id).first()
        finally:
            session.close()
    
    def get_all_jobs(self) -> List[PodcastJob]:
        """Get all jobs ordered by creation date"""
        session = self._get_session()
        try:
            return session.query(PodcastJob).order_by(PodcastJob.created_at.desc()).all()
        finally:
            session.close()
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> Optional[PodcastJob]:
        """Update job fields"""
        session = self._get_session()
        try:
            job = session.query(PodcastJob).filter(PodcastJob.job_id == job_id).first()
            if job:
                for key, value in updates.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
                session.commit()
                session.refresh(job)
            return job
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error updating job: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_evaluation_result_to_db(self, job_id: str, stage: str, score: Dict[str, Any], passed: bool, feedback: str) -> None:
        """Save evaluation result"""
        session = self._get_session()
        try:
            result = EvaluationResult()
            result.job_id = job_id
            result.stage = stage
            result.score = score
            result.passed = passed
            result.feedback = feedback

            session.add(result)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving evaluation result: {str(e)}")
            raise
        finally:
            session.close()

    def save_guardrail_result(self, job_id: str, guardrail_type: str, passed: bool, details: dict):
        """Save guardrail check result"""
        session = self._get_session()
        try:
            result = GuardrailResult()
            result.job_id = job_id
            result.guardrail_type = guardrail_type
            result.passed = passed
            result.details = details

            session.add(result)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving guardrail result: {str(e)}")
            raise
        finally:
            session.close()

    def save_evaluation_result_to_job(self, job_id: str, stage: str, score: dict, passed: bool, feedback: str):
        """Update job with evaluation results"""
        evaluation_data = {
            f"{stage}_evaluation": {
                "score": score,
                "passed": passed,
                "feedback": feedback,
                "evaluated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        return self.update_job(job_id, evaluation_data)
