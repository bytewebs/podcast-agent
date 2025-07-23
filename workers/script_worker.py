#!/usr/bin/env python3
"""
Script Generation Worker
Consumes messages from Kafka and generates podcast scripts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.topics import KafkaTopics
from agents.script_agent import ScriptAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Script Generation Worker")
    
    # Initialize consumer
    consumer = KafkaConsumerClient([KafkaTopics.SCRIPT_GENERATION])
    
    # Initialize agent
    agent = ScriptAgent()
    
    # Register message handler
    def handle_script_message(message):
        logger.info(f"Processing script generation message: {message}")
        try:
            agent.process(message)
        except Exception as e:
            logger.error(f"Error processing script message: {str(e)}")
    
    consumer.register_handler(KafkaTopics.SCRIPT_GENERATION, handle_script_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    consumer.start_consuming()

if __name__ == "__main__":
    main()
