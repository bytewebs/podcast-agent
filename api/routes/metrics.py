from flask import Blueprint, jsonify
from utils.monitoring import metrics
from database.repositories import PodcastRepository
import logging

bp = Blueprint('metrics', __name__)
logger = logging.getLogger(__name__)

@bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    try:
        repo = PodcastRepository()
        jobs = repo.get_all_jobs()
        
        # Calculate statistics
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j.status.value == "COMPLETED"])
        failed_jobs = len([j for j in jobs if j.status.value == "FAILED"])
        pending_jobs = len([j for j in jobs if j.status.value in ["PENDING", "OUTLINE_GENERATION", "SCRIPT_GENERATION"]])
        
        system_metrics = {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "pending_jobs": pending_jobs,
            "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "performance_metrics": metrics.get_metrics()
        }
        
        return jsonify(system_metrics), 200
    
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500