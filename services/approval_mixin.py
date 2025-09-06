from services.email_service import EmailApprovalService
from database.repositories import PodcastRepository
from utils.config import config
import logging
import time
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ApprovalMixin:
    """Mixin to add email approval functionality to existing workers"""
    
    def __init__(self):
        self.email_service = EmailApprovalService()
        self.approval_repo = PodcastRepository()
        self.approval_enabled = getattr(config, 'EMAIL_APPROVAL_ENABLED', True)
        self.approval_timeout = getattr(config, 'APPROVAL_TIMEOUT_HOURS', 168)  # 7 days default
        self.check_interval = getattr(config, 'APPROVAL_CHECK_INTERVAL', 30)  # 30 seconds
        
        # NEW: Prefect integration
        self.prefect_enabled = getattr(config, 'PREFECT_ENABLED', True)
    
    def handle_with_email_approval(self, job_id: str, stage: str, content_data: dict, 
                                     next_topic, next_message: dict, status_update: dict,
                                     user_email: str = None) -> bool:
        """
        Handle approval with email notification
        
        Args:
            job_id: The job ID
            stage: The approval stage ('outline', 'script', 'audio')
            content_data: The data to include in the email
            next_topic: Kafka topic to send to after approval
            next_message: Message to send to next topic
            status_update: Status update for database
            user_email: User email (optional)
            
        Returns:
            bool: True if processed successfully
        """
        if not self.approval_enabled:
            logger.info(f"Email approval disabled, auto-approving {stage} for job {job_id}")
            return self._auto_approve_and_continue(job_id, next_topic, next_message, status_update)
        
        try:
            # Get user email if not provided
            if not user_email:
                user_email = self._get_user_email(job_id)
                
            if not user_email:
                logger.warning(f"No user email found for job {job_id}, auto-approving")
                return self._auto_approve_and_continue(job_id, next_topic, next_message, status_update)
            
            # Send approval email
            success = self._send_stage_email(job_id, stage, content_data, user_email)
            
            if not success:
                logger.error(f"Failed to send approval email for job {job_id}, auto-approving")
                return self._auto_approve_and_continue(job_id, next_topic, next_message, status_update)
            
            # Mark as pending approval in database
            self._mark_pending_approval(job_id, stage, next_topic, next_message, status_update)
            
            logger.info(f"Email approval requested for job {job_id}, stage {stage}")
            return True
            
        except Exception as e:
            logger.error(f"Error in approval process for job {job_id}, stage {stage}: {e}")
            # Auto-approve on error to prevent pipeline blockage
            return self._auto_approve_and_continue(job_id, next_topic, next_message, status_update)
    
    def _get_user_email(self, job_id: str) -> str:
        """Get user email from job data"""
        try:
            job_data = self.approval_repo.get_job(job_id)
            if hasattr(job_data, 'user_email'):
                return job_data.user_email
            elif hasattr(job_data, 'brief') and isinstance(job_data.brief, dict):
                return job_data.brief.get('user_email')
            return getattr(config, 'DEFAULT_APPROVAL_EMAIL', None)
        except Exception as e:
            logger.error(f"Error getting user email for job {job_id}: {e}")
            return None
    
    def _send_stage_email(self, job_id: str, stage: str, content_data: dict, user_email: str) -> bool:
        """Send email for specific stage"""
        try:
            if stage == 'outline':
                return self.email_service.send_outline_approval_email(job_id, user_email, content_data)
            elif stage == 'script':
                return self.email_service.send_script_approval_email(job_id, user_email, content_data)
            elif stage == 'audio':
                return self.email_service.send_audio_approval_email(job_id, user_email, content_data)
            else:
                logger.error(f"Unknown approval stage: {stage}")
                return False
        except Exception as e:
            logger.error(f"Error sending {stage} approval email: {e}")
            return False
    
    def _mark_pending_approval(self, job_id: str, stage: str, next_topic, next_message: dict, status_update: dict):
        """Mark job as pending approval and store continuation data"""
        try:
            # NEW: Enhanced approval data with Prefect integration
            approval_data = {
                "status": f"{stage.upper()}_APPROVAL",  # More specific status
                f"{stage}_approval_requested": True,
                f"{stage}_approval_requested_at": datetime.utcnow(),
                "approval_stage": stage,
                "approval_timeout": datetime.utcnow() + timedelta(hours=self.approval_timeout),
                "continuation_data": json.dumps({  # Ensure JSON serialization
                    "next_topic": next_topic.value if hasattr(next_topic, 'value') else str(next_topic),
                    "next_message": next_message,
                    "status_update": status_update
                }),
                "updated_at": datetime.utcnow()
            }
            
            self.approval_repo.update_job(job_id, approval_data)
            logger.info(f"Job {job_id} marked as pending {stage} approval")
            
        except Exception as e:
            logger.error(f"Error marking job {job_id} as pending approval: {e}")
            raise
    
    def _auto_approve_and_continue(self, job_id: str, next_topic, next_message: dict, status_update: dict) -> bool:
        """Auto-approve and continue pipeline"""
        try:
            from messaging.kafka_producer import KafkaProducerClient
            
            producer = KafkaProducerClient()
            
            # Send to next stage
            success = producer.send_message(next_topic, next_message)
            if not success:
                logger.error(f"Failed to send message to next stage for job {job_id}")
                return False
            
            # Update status
            self.approval_repo.update_job(job_id, status_update)
            
            logger.info(f"Auto-approved and continued pipeline for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in auto-approve for job {job_id}: {e}")
            return False
