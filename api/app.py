# api/app.py (UPDATED VERSION)
from flask import Flask, jsonify
from flask_cors import CORS
from api.routes import podcast, approval, metrics, admin
from api.docs import docs_bp
from database.connection import init_db
from utils.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    # Register all blueprints
    app.register_blueprint(podcast.bp, url_prefix='/api/v1/podcast')
    app.register_blueprint(approval.bp, url_prefix='/api/v1/approval')
    app.register_blueprint(metrics.bp, url_prefix='/api/v1')
    app.register_blueprint(admin.bp, url_prefix='/api/v1/admin')
    app.register_blueprint(docs_bp, url_prefix='/')

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "podcast-generation-api",
            "version": "1.0.0"
        }), 200

    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            "service": "Podcast Generation API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "docs": "/api/docs",
                "create_podcast": "/api/v1/podcast/create",
                "job_status": "/api/v1/podcast/{job_id}/status",
                "list_jobs": "/api/v1/podcast/jobs"
            }
        }), 200

    # Global error handler
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG)
