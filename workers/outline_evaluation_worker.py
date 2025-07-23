#!/usr/bin/env python3
"""
Outline Evaluation Worker
Consumes messages from Kafka and evaluates podcast outlines
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.topics import KafkaTopics
from evaluation.outline_evaluator import OutlineEvaluator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Outline Evaluation Worker")
    
    # Initialize consumer
    consumer = KafkaConsumerClient([KafkaTopics.OUTLINE_EVALUATION])
    
    # Initialize evaluator
    evaluator = OutlineEvaluator()
    
    # Register message handler
    def handle_evaluation_message(message):
        logger.info(f"Processing outline evaluation message: {message}")
        try:
            job_id = message.get("job_id")
            outline = message.get("outline")
            brief = message.get("brief")
            
            evaluator.evaluate(job_id, outline, brief)
        except Exception as e:
            logger.error(f"Error processing evaluation message: {str(e)}")
    
    consumer.register_handler(KafkaTopics.OUTLINE_EVALUATION, handle_evaluation_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    consumer.start_consuming()

if __name__ == "__main__":
    main()