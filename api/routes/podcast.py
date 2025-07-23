from flask import Blueprint, request, jsonify
from api.schemas import PodcastBrief, PodcastJobResponse, JobStatusResponse
from database.repositories import PodcastRepository
from agents.supervisor_agent import SupervisorAgent
import uuid
from datetime import datetime, timezone
import requests

bp = Blueprint('podcast', __name__)
repo = PodcastRepository()

@bp.route('/create', methods=['POST'])
def create_podcast():
    """Create a new podcast generation job"""
    try:
        # Validate request
        brief_data = request.get_json()
        if not brief_data:
            return jsonify({"error": "No data provided"}), 400
            
        brief = PodcastBrief(**brief_data)

        # Generate job ID
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        # Create job in the database
        job = repo.create_job(
            job_id=job_id,
            brief=brief.model_dump()
        )

        # Start the job using supervisor agent
        supervisor = SupervisorAgent()
        result = supervisor.start_job(job_id, brief.model_dump())
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        return jsonify(PodcastJobResponse(
            job_id=job_id,
            status="pending",
            created_at=datetime.now(timezone.utc),
            message="Podcast generation job created successfully"
        ).model_dump()), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a podcast generation job"""
    try:
        job = repo.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify(JobStatusResponse(
            job_id=job.job_id,
            status=job.status.value,
            outline=job.outline,
            script=job.script,
            audio_url=job.audio_url,
            rss_feed_url=job.rss_feed_url,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at
        ).model_dump()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all podcast generation jobs"""
    try:
        jobs = repo.get_all_jobs()
        return jsonify({
            "jobs": [
                {
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "topic": job.brief.get("topic", "Unknown"),
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                }
                for job in jobs
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400