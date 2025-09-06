#!/usr/bin/env python3
"""
Audio Approval Worker
Consumes messages from Kafka and handles audio approvals
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.kafka_producer import KafkaProducerClient
from messaging.topics import KafkaTopics
from database.repositories import PodcastRepository
from services.approval_mixin import ApprovalMixin
from utils.config import config
from utils.monitoring import monitor_performance
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioApprovalWorker(ApprovalMixin):
    def __init__(self):
        super().__init__()
        self.consumer = KafkaConsumerClient([KafkaTopics.AUDIO_APPROVAL])
        self.producer = KafkaProducerClient()
        self.repo = PodcastRepository()
        # Get approval setting from config
        self.auto_approve = getattr(config, 'AUTO_APPROVE_AUDIO', False)  # Changed default to False

def main():
    """Main worker function"""
    logger.info("Starting Audio Approval Worker")
    
    worker = AudioApprovalWorker()
    
    # Register message handler
    @monitor_performance("audio_approval")
    def handle_approval_message(message):
        logger.info(f"Processing audio approval message: {message}")
        try:
            job_id = message.get("job_id")
            audio_url = message.get("audio_url")
            evaluation_score = message.get("evaluation_score", 0.8)
            
            logger.info(f"Processing audio approval for job {job_id}")
            
            if worker.auto_approve:
                # Auto-approve logic
                time.sleep(2)
                
                logger.info(f"Auto-approving audio for job {job_id}")
                
                # Send to publishing
                worker.producer.send_message(KafkaTopics.PUBLISHING, {
                    "job_id": job_id,
                    "audio_url": audio_url,
                    "approved": True
                })
                
                # Update status
                worker.repo.update_job(job_id, {
                    "status": "PUBLISHING",
                    "audio_approved": True  # NEW: Mark as approved
                })
            else:
                # Email approval logic
                content_data = {"audio_url": audio_url, "evaluation_score": evaluation_score}
                next_message = {
                    "job_id": job_id,
                    "audio_url": audio_url,
                    "approved": True
                }
                status_update = {
                    "status": "PUBLISHING",
                    "audio_approved": True  # NEW: Mark as approved
                }
                
                worker.handle_with_email_approval(
                    job_id=job_id,
                    stage="audio",
                    content_data=content_data,
                    next_topic=KafkaTopics.PUBLISHING,
                    next_message=next_message,
                    status_update=status_update
                )
                
        except Exception as e:
            logger.error(f"Error processing approval message: {str(e)}")
            
            # Update job status to failed
            try:
                worker.repo.update_job(message.get("job_id"), {
                    "status": "FAILED",
                    "error_message": f"Audio approval failed: {str(e)}"
                })
            except Exception as db_error:
                logger.error(f"Failed to update job status: {str(db_error)}")
    
    worker.consumer.register_handler(KafkaTopics.AUDIO_APPROVAL, handle_approval_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    try:
        worker.consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
