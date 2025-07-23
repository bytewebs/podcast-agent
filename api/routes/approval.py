from flask import Blueprint, request, jsonify
from api.schemas import ApprovalRequest
from database.repositories import PodcastRepository
from messaging.kafka_producer import KafkaProducerClient
from messaging.topics import KafkaTopics

bp = Blueprint('approval', __name__)
repo = PodcastRepository()
producer = KafkaProducerClient()

@bp.route('/<job_id>/outline', methods=['POST'])
def approve_outline(job_id):
    """Approve or reject generated outline"""
    try:
        approval_data = request.get_json()
        approval = ApprovalRequest(**approval_data)
        
        job = repo.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if approval.approved:
            repo.update_job(job_id, {"outline_approved": True})
            # Send to script generation
            producer.send_message(
                KafkaTopics.SCRIPT_GENERATION,
                {
                    "job_id": job_id,
                    "outline": job.outline,
                    "brief": job.brief
                }
            )
        else:
            # Send back for regeneration with feedback
            producer.send_message(
                KafkaTopics.OUTLINE_GENERATION,
                {
                    "job_id": job_id,
                    "brief": job.brief,
                    "feedback": approval.feedback,
                    "retry": True
                }
            )
        
        return jsonify({"message": "Approval processed"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<job_id>/script', methods=['POST'])
def approve_script(job_id):
    """Approve or reject generated script"""
    try:
        approval_data = request.get_json()
        approval = ApprovalRequest(**approval_data)
        
        job = repo.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if approval.approved:
            repo.update_job(job_id, {"script_approved": True})
            # Send to TTS generation
            producer.send_message(
                KafkaTopics.TTS_GENERATION,
                {
                    "job_id": job_id,
                    "script": job.script,
                    "voice_preference": job.brief.get("voice_preference")
                }
            )
        else:
            # Send back for regeneration
            producer.send_message(
                KafkaTopics.SCRIPT_GENERATION,
                {
                    "job_id": job_id,
                    "outline": job.outline,
                    "brief": job.brief,
                    "feedback": approval.feedback,
                    "retry": True
                }
            )
        
        return jsonify({"message": "Approval processed"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400