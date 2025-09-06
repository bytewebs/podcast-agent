#!/usr/bin/env python3
"""
Script Approval Worker
Consumes messages from Kafka and handles script approvals
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
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScriptApprovalWorker(ApprovalMixin):
    def __init__(self):
        super().__init__()
        self.consumer = KafkaConsumerClient([KafkaTopics.SCRIPT_APPROVAL])
        self.producer = KafkaProducerClient()
        self.repo = PodcastRepository()
        # Get approval setting from config
        self.auto_approve = getattr(config, 'AUTO_APPROVE_SCRIPT', False)  # Changed default to False

def main():
    """Main worker function"""
    logger.info("Starting Script Approval Worker")
    
    worker = ScriptApprovalWorker()
    
    # Register message handler
    def handle_approval_message(message):
        logger.info(f"Processing script approval message: {message}")
        try:
            job_id = message.get("job_id")
            script = message.get("script")
            brief = message.get("brief")
            
            logger.info(f"Processing script approval for job {job_id}")
            
            if worker.auto_approve:
                # Auto-approve logic
                time.sleep(2)
                
                logger.info(f"Auto-approving script for job {job_id}")
                
                # Send to TTS generation
                worker.producer.send_message(KafkaTopics.TTS_GENERATION, {
                    "job_id": job_id,
                    "script": script,
                    "voice_preference": brief.get("voice_preference", "professional_female")
                })
                
                # Update status
                worker.repo.update_job(job_id, {
                    "status": "TTS_GENERATION",
                    "script_approved": True  # NEW: Mark as approved
                })
            else:
                # Email approval logic
                content_data = {"script": script, "brief": brief}
                next_message = {
                    "job_id": job_id,
                    "script": script,
                    "voice_preference": brief.get("voice_preference", "professional_female")
                }
                status_update = {
                    "status": "TTS_GENERATION",
                    "script_approved": True  # NEW: Mark as approved
                }
                
                worker.handle_with_email_approval(
                    job_id=job_id,
                    stage="script",
                    content_data=content_data,
                    next_topic=KafkaTopics.TTS_GENERATION,
                    next_message=next_message,
                    status_update=status_update
                )
                
        except Exception as e:
            logger.error(f"Error processing approval message: {str(e)}")
            # Update job status to failed
            try:
                worker.repo.update_job(job_id, {
                    "status": "FAILED",
                    "error_message": f"Script approval failed: {str(e)}"
                })
            except Exception as db_error:
                logger.error(f"Failed to update job status: {str(db_error)}")
    
    worker.consumer.register_handler(KafkaTopics.SCRIPT_APPROVAL, handle_approval_message)
    
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
