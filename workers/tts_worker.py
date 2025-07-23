#!/usr/bin/env python3
"""
TTS Generation Worker
Consumes messages from Kafka and generates audio from scripts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.topics import KafkaTopics
from agents.tts_agent import TTSAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting TTS Generation Worker")
    
    # Initialize consumer
    consumer = KafkaConsumerClient([KafkaTopics.TTS_GENERATION])
    
    # Initialize agent
    agent = TTSAgent()
    
    # Register message handler
    def handle_tts_message(message):
        logger.info(f"Processing TTS generation message: {message}")
        try:
            agent.process(message)
        except Exception as e:
            logger.error(f"Error processing TTS message: {str(e)}")
    
    consumer.register_handler(KafkaTopics.TTS_GENERATION, handle_tts_message)
    
    # Start consuming
    logger.info("Starting to consume messages...")
    consumer.start_consuming()

if __name__ == "__main__":
    main()
