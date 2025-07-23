from abc import ABC, abstractmethod
from messaging.kafka_producer import KafkaProducerClient
from database.repositories import PodcastRepository
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.producer = KafkaProducerClient()
        self.repo = PodcastRepository()
        self.logger = logging.getLogger(f"agent.{name}")
    
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
        except Exception as e:
            self.logger.error(f"Failed to update job status: {str(e)}")
    
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
        except Exception as e:
            self.logger.error(f"Failed to handle error properly: {str(e)}")
