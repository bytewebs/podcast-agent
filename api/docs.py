from flask import Blueprint, jsonify

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/api/docs', methods=['GET'])
def api_documentation():
    """API documentation endpoint"""
    docs = {
        "title": "Podcast Generation API",
        "version": "1.0.0",
        "description": "AI-powered podcast generation system",
        "base_url": "/api/v1",
        "endpoints": {
            "POST /api/v1/podcast/create": {
                "description": "Create a new podcast generation job",
                "parameters": {
                    "topic": "string (required) - Main topic of the podcast",
                    "tone": "string (required) - professional, casual, educational, entertaining, inspirational",
                    "length_minutes": "integer (required) - Target length in minutes (5-60)",
                    "target_audience": "string (optional) - Target audience description",
                    "key_points": "array (optional) - Key points to cover",
                    "avoid_topics": "array (optional) - Topics to avoid",
                    "voice_preference": "string (optional) - Voice preference for TTS",
                    "additional_context": "string (optional) - Any additional context"
                },
                "response": {
                    "job_id": "string - Unique job identifier",
                    "status": "string - Job status",
                    "created_at": "datetime - Creation timestamp",
                    "message": "string - Status message"
                },
                "example": {
                    "topic": "The Future of Artificial Intelligence",
                    "tone": "professional",
                    "length_minutes": 15,
                    "target_audience": "technology enthusiasts",
                    "key_points": ["machine learning", "neural networks", "AI ethics"],
                    "voice_preference": "professional_female"
                }
            },
            "GET /api/v1/podcast/{job_id}/status": {
                "description": "Get the status of a podcast generation job",
                "parameters": {
                    "job_id": "string (required) - Job identifier"
                },
                "response": {
                    "job_id": "string - Job identifier",
                    "status": "string - Current status",
                    "outline": "object - Generated outline (if available)",
                    "script": "string - Generated script (if available)",
                    "audio_url": "string - Audio file URL (if available)",
                    "rss_feed_url": "string - RSS feed URL (if available)",
                    "error_message": "string - Error message (if failed)",
                    "created_at": "datetime - Creation timestamp",
                    "updated_at": "datetime - Last update timestamp"
                }
            },
            "GET /api/v1/podcast/jobs": {
                "description": "List all podcast generation jobs",
                "response": {
                    "jobs": "array - List of jobs with basic information"
                }
            },
            "POST /api/v1/approval/{job_id}/outline": {
                "description": "Approve or reject generated outline",
                "parameters": {
                    "approved": "boolean (required) - Approval decision",
                    "feedback": "string (optional) - Feedback for improvement",
                    "modifications": "object (optional) - Requested modifications"
                }
            },
            "POST /api/v1/approval/{job_id}/script": {
                "description": "Approve or reject generated script",
                "parameters": {
                    "approved": "boolean (required) - Approval decision",
                    "feedback": "string (optional) - Feedback for improvement",
                    "modifications": "object (optional) - Requested modifications"
                }
            },
            "GET /api/v1/metrics": {
                "description": "Get system metrics and statistics",
                "response": {
                    "total_jobs": "integer - Total number of jobs",
                    "completed_jobs": "integer - Number of completed jobs",
                    "failed_jobs": "integer - Number of failed jobs",
                    "pending_jobs": "integer - Number of pending jobs",
                    "success_rate": "float - Success rate percentage"
                }
            },
            "GET /health": {
                "description": "System health check",
                "response": {
                    "status": "string - System status (healthy/unhealthy)",
                    "service": "string - Service name",
                    "version": "string - API version"
                }
            }
        },
        "status_codes": {
            "PENDING": "Job created and waiting to start",
            "OUTLINE_GENERATION": "Generating podcast outline",
            "OUTLINE_EVALUATION": "Evaluating outline quality",
            "OUTLINE_APPROVAL": "Waiting for outline approval",
            "SCRIPT_GENERATION": "Generating podcast script",
            "SCRIPT_EVALUATION": "Evaluating script quality",
            "SCRIPT_APPROVAL": "Waiting for script approval",
            "TTS_GENERATION": "Converting script to audio",
            "TTS_EVALUATION": "Evaluating audio quality",
            "AUDIO_APPROVAL": "Waiting for audio approval",
            "PUBLISHING": "Publishing podcast and creating RSS feed",
            "COMPLETED": "Job completed successfully",
            "FAILED": "Job failed with errors"
        },
        "error_codes": {
            "400": "Bad Request - Invalid parameters",
            "404": "Not Found - Job or resource not found",
            "500": "Internal Server Error - System error"
        }
    }
    return jsonify(docs)