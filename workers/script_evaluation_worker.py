#!/usr/bin/env python3
"""
Script Evaluation Worker
Consumes messages from Kafka and evaluates podcast scripts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.topics import KafkaTopics
from evaluation.script_evaluator import ScriptEvaluator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Script Evaluation Worker")
    
    # Initialize consumer
    consumer = KafkaConsumerClient([KafkaTopics.SCRIPT_EVALUATION])
    
    # Initialize evaluator
    evaluator = ScriptEvaluator()
    
    # Register message handler
    def handle_evaluation_message(message):
        logger.info(f"Processing script evaluation message: {message}")
        try:
            job_id = message.get("job_id")
            script = message.get("script")
            outline = message.get("outline")
            brief = message.get("brief")
            
            evaluator.evaluate(job_id, script, outline, brief)
        except Exception as e:
            logger.error(f"Error processing script evaluation message: {str(e)}")
    
    consumer.register_handler(KafkaTopics.SCRIPT_EVALUATION, handle_evaluation_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    consumer.start_consuming()

if __name__ == "__main__":
    main()