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
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Script Approval Worker")
    
    # Initialize consumer and producer
    consumer = KafkaConsumerClient([KafkaTopics.SCRIPT_APPROVAL])
    producer = KafkaProducerClient()
    repo = PodcastRepository()
    
    # Auto-approve setting
    auto_approve = True
    
    # Register message handler
    def handle_approval_message(message):
        logger.info(f"Processing script approval message: {message}")
        try:
            job_id = message.get("job_id")
            script = message.get("script")
            brief = message.get("brief")
            
            logger.info(f"Processing script approval for job {job_id}")
            
            if auto_approve:
                time.sleep(2)
                
                logger.info(f"Auto-approving script for job {job_id}")
                
                # Send to TTS generation
                producer.send_message(KafkaTopics.TTS_GENERATION, {
                    "job_id": job_id,
                    "script": script,
                    "voice_preference": brief.get("voice_preference", "professional_female")
                })
                
                # Update status
                repo.update_job(job_id, {"status": "TTS_GENERATION"})
            else:
                logger.info(f"Manual approval required for job {job_id}")
                repo.update_job(job_id, {"status": "PENDING_APPROVAL"})
                
        except Exception as e:
            logger.error(f"Error processing approval message: {str(e)}")
    
    consumer.register_handler(KafkaTopics.SCRIPT_APPROVAL, handle_approval_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    consumer.start_consuming()

if __name__ == "__main__":
    main()
