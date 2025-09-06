from abc import ABC, abstractmethod
from messaging.kafka_producer import KafkaProducerClient
from database.repositories import PodcastRepository
import logging
import os

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.producer = KafkaProducerClient()
        self.repo = PodcastRepository()
        self.logger = logging.getLogger(f"agent.{name}")
        
        # NEW: Add Prefect integration flag
        self.prefect_enabled = os.getenv('PREFECT_ENABLED', 'true').lower() == 'true'
    
    @abstractmethod
    def process(self, message: dict):
        """Process incoming message"""
        pass
    
    def send_to_next_stage(self, topic: str, message: dict) -> bool:
        """Send message to next stage"""
        return self.producer.send_message(topic, message)
    
    def update_job_status(self, job_id: str, status: str):
        """Update job status in database"""
        try:
            self.repo.update_job(job_id, {"status": status})
            
            # NEW: Optional Prefect state update
            if self.prefect_enabled:
                self._update_prefect_state(job_id, status)
                
        except Exception as e:
            self.logger.error(f"Failed to update job status: {str(e)}")
    
    def _update_prefect_state(self, job_id: str, status: str):
        """Update Prefect flow state (optional)"""
        try:
            # This is optional - you can implement if you want Prefect visibility
            # For now, we'll just log it
            self.logger.info(f"Prefect integration: Job {job_id} status updated to {status}")
        except Exception as e:
            self.logger.warning(f"Failed to update Prefect state: {str(e)}")
    
    def handle_error(self, job_id: str, error: str):
        """Handle processing errors"""
        self.logger.error(f"Error in {self.name} for job {job_id}: {error}")
        try:
            self.repo.update_job(job_id, {
                "status": "FAILED",
                "error_message": error
            })
            
            # Send to DLQ
            self.producer.send_message("podcast.dlq", {
                "job_id": job_id,
                "agent": self.name,
                "error": error
            })
            
            # NEW: Optional Prefect error notification
            if self.prefect_enabled:
                self._notify_prefect_error(job_id, error)
                
        except Exception as e:
            self.logger.error(f"Failed to handle error properly: {str(e)}")
    
    def _notify_prefect_error(self, job_id: str, error: str):
        """Notify Prefect of error (optional)"""
        try:
            # This could trigger Prefect flow failure if needed
            self.logger.info(f"Prefect integration: Job {job_id} failed with error: {error}")
        except Exception as e:
            self.logger.warning(f"Failed to notify Prefect of error: {str(e)}")
