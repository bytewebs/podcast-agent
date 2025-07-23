from flask import Blueprint, jsonify, request
from database.repositories import PodcastRepository
from messaging.kafka_producer import KafkaProducerClient
from messaging.topics import KafkaTopics
import logging

bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@bp.route('/jobs/<job_id>/retry', methods=['POST'])
def retry_job(job_id):
    """Retry a failed job"""
    try:
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if job.status.value != "FAILED":
            return jsonify({"error": "Job is not in failed state"}), 400
        
        # Reset job status and retry
        repo.update_job(job_id, {
            "status": "PENDING",
            "error_message": None,
            "retry_count": job.retry_count + 1
        })
        
        # Send to outline generation to restart
        producer = KafkaProducerClient()
        producer.send_message(KafkaTopics.OUTLINE_GENERATION, {
            "job_id": job_id,
            "brief": job.brief,
            "retry": True
        })
        
        return jsonify({"message": "Job retry initiated"}), 200
    
    except Exception as e:
        logger.error(f"Error retrying job: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a job"""
    try:
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if job.status.value in ["COMPLETED", "FAILED"]:
            return jsonify({"error": "Job cannot be cancelled"}), 400
        
        # Update job status to failed
        repo.update_job(job_id, {
            "status": "FAILED",
            "error_message": "Job cancelled by user"
        })
        
        return jsonify({"message": "Job cancelled successfully"}), 200
    
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/system/status', methods=['GET'])
def system_status():
    """Get system status"""
    try:
        # Check database connection
        repo = PodcastRepository()
        try:
            repo.get_all_jobs()
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"
        
        # Check Kafka connection
        try:
            producer = KafkaProducerClient()
            kafka_status = "healthy"
        except Exception:
            kafka_status = "unhealthy"
        
        return jsonify({
            "database": db_status,
            "kafka": kafka_status,
            "overall": "healthy" if db_status == "healthy" and kafka_status == "healthy" else "degraded"
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({"error": str(e)}), 500