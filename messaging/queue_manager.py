import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from messaging.kafka_producer import KafkaProducerClient
from messaging.topics import KafkaTopics

logger = logging.getLogger(__name__)

class QueueManager:
    """Manage job queues and message routing"""
    
    def __init__(self):
        self.producer = KafkaProducerClient()
        self.topic_mapping = {
            "outline": KafkaTopics.OUTLINE_GENERATION,
            "script": KafkaTopics.SCRIPT_GENERATION,
            "tts": KafkaTopics.TTS_GENERATION,
            "publishing": KafkaTopics.PUBLISHING
        }
    
    def enqueue_job(self, stage: str, job_data: dict) -> bool:
        """Enqueue job for processing"""
        try:
            topic = self.topic_mapping.get(stage)
            if not topic:
                logger.error(f"Unknown stage: {stage}")
                return False
            
            # Add timestamp
            job_data["enqueued_at"] = datetime.now(timezone.utc).isoformat()
            
            return self.producer.send_message(topic, job_data)
        
        except Exception as e:
            logger.error(f"Failed to enqueue job: {str(e)}")
            return False
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics (simplified)"""
        # In a real implementation, this would query Kafka for queue depths
        return {
            "outline_queue": 0,
            "script_queue": 0,
            "tts_queue": 0,
            "publishing_queue": 0
        }
