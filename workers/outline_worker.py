#!/usr/bin/env python3
"""
Outline Generation Worker
Consumes messages from Kafka and generates podcast outlines
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.topics import KafkaTopics
from agents.outline_agent import OutlineAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Outline Generation Worker")
    
    # Initialize consumer
    consumer = KafkaConsumerClient([KafkaTopics.OUTLINE_GENERATION])
    
    # Initialize agent
    agent = OutlineAgent()
    
    # Register message handler
    def handle_outline_message(message):
        logger.info(f"Processing outline generation message: {message}")
        try:
            agent.process(message)
        except Exception as e:
            logger.error(f"Error processing outline message: {str(e)}")
    
    consumer.register_handler(KafkaTopics.OUTLINE_GENERATION, handle_outline_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    consumer.start_consuming()

if __name__ == "__main__":
    main()
