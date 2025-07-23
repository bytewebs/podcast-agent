#!/usr/bin/env python3
"""
Main startup script for the podcast generation system
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_db
from utils.config import config
from utils.logger import setup_logger

# Setup logging
logger = setup_logger("startup", logging.INFO)

def check_environment():
    """Check required environment variables"""
    required_vars = [
        'OPENAI_API_KEY',
        'DATABASE_URL',
        'KAFKA_BOOTSTRAP_SERVERS'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def initialize_database():
    """Initialize database tables"""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False

def start_api_server():
    """Start the API server"""
    try:
        logger.info("Starting API server...")
        from api.app import create_app
        
        app = create_app()
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.DEBUG
        )
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        raise

def main():
    """Main startup function"""
    logger.info("🚀 Starting Podcast Generation System")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        logger.error("❌ Database initialization failed")
        sys.exit(1)
    
    # Start API server
    logger.info("✅ System startup complete")
    start_api_server()

if __name__ == "__main__":
    main()
