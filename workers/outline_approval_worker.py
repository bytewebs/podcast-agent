#!/usr/bin/env python3
"""
Outline Approval Worker
Consumes messages from Kafka and handles outline approvals
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

class OutlineApprovalWorker(ApprovalMixin):
    def __init__(self):
        super().__init__()
        self.consumer = KafkaConsumerClient([KafkaTopics.OUTLINE_APPROVAL])
        self.producer = KafkaProducerClient()
        self.repo = PodcastRepository()
        # Get approval setting from config
        self.auto_approve = getattr(config, 'AUTO_APPROVE_OUTLINE', False)  # Changed default to False
        
        # NEW: Prefect integration
        self.prefect_enabled = getattr(config, 'PREFECT_ENABLED', True)

def main():
    """Main worker function"""
    logger.info("Starting Outline Approval Worker")
    
    worker = OutlineApprovalWorker()
    
    # Register message handler
    def handle_approval_message(message):
        logger.info(f"Processing outline approval message: {message}")
        try:
            job_id = message.get("job_id")
            outline = message.get("outline")
            brief = message.get("brief")
            
            logger.info(f"Processing outline approval for job {job_id}")
            
            if worker.auto_approve:
                # Auto-approve logic
                time.sleep(2)
                
                logger.info(f"Auto-approving outline for job {job_id}")
                
                # Send to script generation
                worker.producer.send_message(KafkaTopics.SCRIPT_GENERATION, {
                    "job_id": job_id,
                    "outline": outline,
                    "brief": brief,
                    "approved": True
                })
                
                # Update status
                worker.repo.update_job(job_id, {
                    "status": "SCRIPT_GENERATION",
                    "outline_approved": True  # NEW: Mark as approved
                })
            else:
                # Email approval logic
                content_data = {"outline": outline, "brief": brief}
                next_message = {
                    "job_id": job_id,
                    "outline": outline,
                    "brief": brief,
                    "approved": True
                }
                status_update = {
                    "status": "SCRIPT_GENERATION",
                    "outline_approved": True  # NEW: Mark as approved
                }
                
                worker.handle_with_email_approval(
                    job_id=job_id,
                    stage="outline",
                    content_data=content_data,
                    next_topic=KafkaTopics.SCRIPT_GENERATION,
                    next_message=next_message,
                    status_update=status_update
                )
                
        except Exception as e:
            logger.error(f"Error processing approval message: {str(e)}")
            # Update job status to failed
            try:
                worker.repo.update_job(job_id, {
                    "status": "FAILED",
                    "error_message": f"Outline approval failed: {str(e)}"
                })
            except Exception as db_error:
                logger.error(f"Failed to update job status: {str(db_error)}")
    
    worker.consumer.register_handler(KafkaTopics.OUTLINE_APPROVAL, handle_approval_message)
    
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
