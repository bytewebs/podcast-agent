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
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Outline Approval Worker")
    
    # Initialize consumer and producer
    consumer = KafkaConsumerClient([KafkaTopics.OUTLINE_APPROVAL])
    producer = KafkaProducerClient()
    repo = PodcastRepository()
    
    # Auto-approve setting (change to False for manual approval)
    auto_approve = True
    
    # Register message handler
    def handle_approval_message(message):
        logger.info(f"Processing outline approval message: {message}")
        try:
            job_id = message.get("job_id")
            outline = message.get("outline")
            brief = message.get("brief")
            
            logger.info(f"Processing outline approval for job {job_id}")
            
            if auto_approve:
                # Simulate approval time
                time.sleep(2)
                
                logger.info(f"Auto-approving outline for job {job_id}")
                
                # Send to script generation
                producer.send_message(KafkaTopics.SCRIPT_GENERATION, {
                    "job_id": job_id,
                    "outline": outline,
                    "brief": brief,
                    "approved": True
                })
                
                # Update status
                repo.update_job(job_id, {"status": "SCRIPT_GENERATION"})
            else:
                # Manual approval needed
                logger.info(f"Manual approval required for job {job_id}")
                repo.update_job(job_id, {"status": "PENDING_APPROVAL"})
                
        except Exception as e:
            logger.error(f"Error processing approval message: {str(e)}")
    
    consumer.register_handler(KafkaTopics.OUTLINE_APPROVAL, handle_approval_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    consumer.start_consuming()

if __name__ == "__main__":
    main()
