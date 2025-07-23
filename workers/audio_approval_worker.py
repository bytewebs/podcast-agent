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
from utils.monitoring import monitor_performance
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Audio Approval Worker")
    
    # Initialize consumer and producer
    consumer = KafkaConsumerClient([KafkaTopics.AUDIO_APPROVAL])
    producer = KafkaProducerClient()
    repo = PodcastRepository()
    
    # Auto-approve setting (change to False for manual approval)
    auto_approve = True
    
    # Register message handler
    @monitor_performance("audio_approval")
    def handle_approval_message(message):
        logger.info(f"Processing audio approval message: {message}")
        try:
            job_id = message.get("job_id")
            audio_url = message.get("audio_url")
            evaluation_score = message.get("evaluation_score", 0.8)
            
            logger.info(f"Processing audio approval for job {job_id}")
            
            if auto_approve:
                # Simulate approval time
                time.sleep(2)
                
                logger.info(f"Auto-approving audio for job {job_id}")
                
                # Send to publishing
                producer.send_message(KafkaTopics.PUBLISHING, {
                    "job_id": job_id,
                    "audio_url": audio_url,
                    "approved": True
                })
                
                # Update status
                repo.update_job(job_id, {
                    "status": "PUBLISHING",
                    "audio_approved": True
                })
            else:
                # Manual approval needed
                logger.info(f"Manual approval required for job {job_id}")
                repo.update_job(job_id, {
                    "status": "PENDING_APPROVAL",
                    "audio_approved": False
                })
                
        except Exception as e:
            logger.error(f"Error processing approval message: {str(e)}")
            
            # Update job status to failed
            try:
                repo.update_job(message.get("job_id"), {
                    "status": "FAILED",
                    "error_message": f"Audio approval failed: {str(e)}"
                })
            except Exception as db_error:
                logger.error(f"Failed to update job status: {str(db_error)}")
    
    consumer.register_handler(KafkaTopics.AUDIO_APPROVAL, handle_approval_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
