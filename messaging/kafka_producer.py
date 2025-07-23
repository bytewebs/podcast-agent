from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable
import json
import logging
from utils.config import config
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class KafkaProducerClient:
    def __init__(self, retries=5, delay=5):
        self.producer = None
        attempt = 0
        
        while attempt < retries:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    retries=3,
                    acks='all'
                )
                logger.info("KafkaProducer initialized successfully")
                break
            except NoBrokersAvailable as e:
                attempt += 1
                logger.warning(f"Kafka not available (attempt {attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(delay)
        
        if self.producer is None:
            logger.error("Failed to connect to Kafka after multiple retries")
            raise ConnectionError("Could not connect to Kafka")

    def send_message(self, topic: str, message: dict, key: str = "") -> bool:
        """Send message to Kafka topic"""
        try:
            key = key or ""
            future = self.producer.send(topic, value=message, key=key)
            record_metadata = future.get(timeout=10)
            logger.info(f"Message sent to {topic} at offset {record_metadata.offset}")
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message to {topic}: {str(e)}")
            self._send_to_dlq(topic, message, str(e))
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to {topic}: {str(e)}")
            return False

    def _send_to_dlq(self, original_topic: str, message: dict, error: str):
        """Send failed messages to Dead Letter Queue"""
        dlq_message = {
            "original_topic": original_topic,
            "message": message,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        try:
            if self.producer:
                self.producer.send("podcast.dlq", value=dlq_message)
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {str(e)}")
    
    def close(self):
        if self.producer:
            self.producer.close()