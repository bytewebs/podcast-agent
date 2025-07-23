#!/usr/bin/env python3
"""
Publishing Worker
Consumes messages from Kafka and publishes podcasts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.topics import KafkaTopics
from agents.publishing_agent import PublishingAgent
from utils.monitoring import monitor_performance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting Publishing Worker")
    
    # Initialize consumer
    consumer = KafkaConsumerClient([KafkaTopics.PUBLISHING])
    
    # Initialize agent
    agent = PublishingAgent()
    
    # Register message handler
    @monitor_performance("publishing")
    def handle_publishing_message(message):
        logger.info(f"Processing publishing message: {message}")
        try:
            agent.process(message)
        except Exception as e:
            logger.error(f"Error processing publishing message: {str(e)}")
            
            # The agent handles error reporting, but we can add additional logging
            job_id = message.get("job_id", "unknown")
            logger.error(f"Publishing failed for job {job_id}: {str(e)}")
    
    consumer.register_handler(KafkaTopics.PUBLISHING, handle_publishing_message)
    
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
