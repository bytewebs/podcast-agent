#!/usr/bin/env python3
"""
TTS Evaluation Worker
Consumes messages from Kafka and evaluates TTS output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from messaging.kafka_consumer import KafkaConsumerClient
from messaging.kafka_producer import KafkaProducerClient
from messaging.topics import KafkaTopics
from database.repositories import PodcastRepository
from utils.monitoring import monitor_performance
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    logger.info("Starting TTS Evaluation Worker")
    
    # Initialize consumer and producer
    consumer = KafkaConsumerClient([KafkaTopics.TTS_EVALUATION])
    producer = KafkaProducerClient()
    repo = PodcastRepository()
    
    # Register message handler
    @monitor_performance("tts_evaluation")
    def handle_evaluation_message(message):
        logger.info(f"Processing TTS evaluation message: {message}")
        try:
            job_id = message.get("job_id")
            audio_url = message.get("audio_url")
            script = message.get("script")
            
            logger.info(f"Evaluating TTS output for job {job_id}")
            
            # Simulate TTS evaluation (in production, implement actual audio quality checks)
            # Could check:
            # - Audio duration vs expected
            # - Audio quality metrics
            # - Speech clarity
            # - Proper pronunciation
            time.sleep(3)
            
            # For now, assume evaluation passes
            evaluation_passed = True
            evaluation_score = 0.85
            
            if evaluation_passed:
                logger.info(f"TTS evaluation passed for job {job_id}")
                
                # Send to audio approval
                producer.send_message(KafkaTopics.AUDIO_APPROVAL, {
                    "job_id": job_id,
                    "audio_url": audio_url,
                    "script": script,
                    "evaluation_score": evaluation_score
                })
                
                # Update job status
                repo.update_job(job_id, {
                    "status": "AUDIO_APPROVAL",
                    "tts_evaluation_score": evaluation_score
                })
            else:
                logger.warning(f"TTS evaluation failed for job {job_id}")
                
                # Send back to TTS generation for retry
                producer.send_message(KafkaTopics.TTS_GENERATION, {
                    "job_id": job_id,
                    "script": script,
                    "retry": True,
                    "feedback": "TTS quality below threshold"
                })
                
        except Exception as e:
            logger.error(f"Error processing TTS evaluation message: {str(e)}")
            
            # Update job status to failed
            try:
                repo.update_job(message.get("job_id"), {
                    "status": "FAILED",
                    "error_message": f"TTS evaluation failed: {str(e)}"
                })
            except Exception as db_error:
                logger.error(f"Failed to update job status: {str(db_error)}")
    
    consumer.register_handler(KafkaTopics.TTS_EVALUATION, handle_evaluation_message)
    
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