from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json
import logging
from typing import Callable
from utils.config import config

logger = logging.getLogger(__name__)

class KafkaConsumerClient:
    def __init__(self, topics: list, group_id: str = ""):
        self.consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id or config.KAFKA_GROUP_ID,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            enable_auto_commit=False,
            auto_offset_reset='earliest'
        )
        self.handlers = {}
    
    def register_handler(self, topic: str, handler: Callable):
        """Register a message handler for a topic"""
        self.handlers[topic] = handler
    
    def start_consuming(self):
        """Start consuming messages"""
        logger.info(f"Starting consumer for topics: {self.consumer.subscription()}")
        
        try:
            for message in self.consumer:
                topic = message.topic
                if topic in self.handlers:
                    try:
                        self.handlers[topic](message.value)
                        self.consumer.commit()
                    except Exception as e:
                        logger.error(f"Error processing message from {topic}: {str(e)}")
                else:
                    logger.warning(f"No handler registered for topic: {topic}")
        except KafkaError as e:
            logger.error(f"Kafka consumer error: {str(e)}")
        finally:
            self.close()
    
    def close(self):
        if hasattr(self, 'consumer'):
            self.consumer.close()
