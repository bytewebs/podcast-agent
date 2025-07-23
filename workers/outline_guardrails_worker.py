#!/usr/bin/env python3
"""
Outline Guardrails Worker
Consumes messages from Kafka and checks guardrails for outlines
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.kafka_producer import KafkaProducerClient
from messaging.topics import KafkaTopics
from database.repositories import PodcastRepository
from guardrails.nsfw_filter import NSFWFilter
from guardrails.bias_detector import BiasDetector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Outline Guardrails Worker")
    
    # Initialize consumer and producer
    consumer = KafkaConsumerClient([KafkaTopics.OUTLINE_GUARDRAILS])
    producer = KafkaProducerClient()
    repo = PodcastRepository()
    
    # Initialize guardrails
    nsfw_filter = NSFWFilter()
    bias_detector = BiasDetector()
    
    # Register message handler
    def handle_guardrails_message(message):
        logger.info(f"Processing outline guardrails message: {message}")
        try:
            job_id = message.get("job_id")
            outline = message.get("outline")
            brief = message.get("brief")
            
            # Combine outline text
            content = f"{outline.get('title', '')} {outline.get('introduction', '')} {outline.get('conclusion', '')}"
            for section in outline.get('sections', []):
                content += f" {section.get('title', '')} {section.get('content', '')}"
            
            # Run guardrail checks
            nsfw_result = nsfw_filter.check_content(content)
            bias_result = bias_detector.check_content(content)
            
            passed = nsfw_result["passed"] and bias_result["passed"]
            
            if passed:
                logger.info(f"Outline guardrails passed for job {job_id}")
                
                # Send to approval
                producer.send_message(KafkaTopics.OUTLINE_APPROVAL, {
                    "job_id": job_id,
                    "outline": outline,
                    "brief": brief,
                    "guardrails_passed": True
                })
            else:
                logger.warning(f"Outline guardrails failed for job {job_id}")
                repo.update_job(job_id, {
                    "status": "FAILED",
                    "error_message": f"Guardrails failed: NSFW={nsfw_result['message']}, Bias={bias_result['message']}"
                })
                
        except Exception as e:
            logger.error(f"Error processing guardrails message: {str(e)}")
    
    consumer.register_handler(KafkaTopics.OUTLINE_GUARDRAILS, handle_guardrails_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    consumer.start_consuming()

if __name__ == "__main__":
    main()
