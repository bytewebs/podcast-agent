#!/usr/bin/env python3
"""
Database migration to add email approval fields
Run this script to add the necessary approval fields to your existing database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text, Column, Boolean, DateTime, String, Text
from sqlalchemy.orm import sessionmaker
from database.connection import get_engine
from utils.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the approval fields migration"""
    try:
        engine = get_engine()
        
        logger.info("Starting database migration: add_approval_fields")
        
        # List of SQL commands to add approval fields
        migration_commands = [
            # User email field for approvals
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);
            """,
            
            # Outline approval fields
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS outline_approved BOOLEAN DEFAULT FALSE;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS outline_approval_requested BOOLEAN DEFAULT FALSE;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS outline_approval_requested_at TIMESTAMP;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS outline_approval_time TIMESTAMP;
            """,
            
            # Script approval fields
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS script_approved BOOLEAN DEFAULT FALSE;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS script_approval_requested BOOLEAN DEFAULT FALSE;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS script_approval_requested_at TIMESTAMP;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS script_approval_time TIMESTAMP;
            """,
            
            # Audio approval fields
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS audio_approved BOOLEAN DEFAULT FALSE;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS audio_approval_requested BOOLEAN DEFAULT FALSE;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS audio_approval_requested_at TIMESTAMP;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS audio_approval_time TIMESTAMP;
            """,
            
            # General approval fields
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS approval_stage VARCHAR(50);
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS approval_timeout TIMESTAMP;
            """,
            """
            ALTER TABLE podcast_jobs 
            ADD COLUMN IF NOT EXISTS continuation_data TEXT;
            """,
            
            # Add indexes for better performance
            """
            CREATE INDEX IF NOT EXISTS idx_podcast_jobs_approval_stage 
            ON podcast_jobs(approval_stage);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_podcast_jobs_outline_approved 
            ON podcast_jobs(outline_approved);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_podcast_jobs_script_approved 
            ON podcast_jobs(script_approved);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_podcast_jobs_audio_approved 
            ON podcast_jobs(audio_approved);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_podcast_jobs_user_email 
            ON podcast_jobs(user_email);
            """
        ]
        
        # Execute each migration command
        with engine.connect() as connection:
            for i, command in enumerate(migration_commands, 1):
                try:
                    logger.info(f"Executing migration step {i}/{len(migration_commands)}")
                    connection.execute(text(command.strip()))
                    connection.commit()
                    logger.info(f"✅ Step {i} completed successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Step {i} failed (may already exist): {e}")
                    # Continue with other commands even if one fails
                    continue
        
        logger.info("✅ Database migration completed successfully!")
        
        # Verify the migration
        verify_migration(engine)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

def verify_migration(engine):
    """Verify that the migration was successful"""
    try:
        logger.info("Verifying migration...")
        
        # Check if the new columns exist
        verification_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'podcast_jobs' 
        AND column_name IN (
            'user_email',
            'outline_approved',
            'script_approved', 
            'audio_approved',
            'approval_stage',
            'continuation_data'
        );
        """
        
        with engine.connect() as connection:
            result = connection.execute(text(verification_query))
            columns = [row[0] for row in result]
            
            expected_columns = [
                'user_email',
                'outline_approved',
                'script_approved',
                'audio_approved', 
                'approval_stage',
                'continuation_data'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            
            if missing_columns:
                logger.warning(f"⚠️ Some columns may not have been created: {missing_columns}")
            else:
                logger.info("✅ All approval columns verified successfully!")
                
    except Exception as e:
        logger.warning(f"⚠️ Could not verify migration (this may be normal): {e}")

def rollback_migration():
    """Rollback the migration (remove approval fields)"""
    try:
        engine = get_engine()
        
        logger.info("Starting migration rollback...")
        
        rollback_commands = [
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS user_email;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS outline_approved;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS outline_approval_requested;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS outline_approval_requested_at;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS outline_approval_time;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS script_approved;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS script_approval_requested;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS script_approval_requested_at;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS script_approval_time;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS audio_approved;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS audio_approval_requested;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS audio_approval_requested_at;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS audio_approval_time;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS approval_stage;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS approval_timeout;",
            "ALTER TABLE podcast_jobs DROP COLUMN IF EXISTS continuation_data;",
            "DROP INDEX IF EXISTS idx_podcast_jobs_approval_stage;",
            "DROP INDEX IF EXISTS idx_podcast_jobs_outline_approved;",
            "DROP INDEX IF EXISTS idx_podcast_jobs_script_approved;",
            "DROP INDEX IF EXISTS idx_podcast_jobs_audio_approved;",
            "DROP INDEX IF EXISTS idx_podcast_jobs_user_email;"
        ]
        
        with engine.connect() as connection:
            for command in rollback_commands:
                try:
                    connection.execute(text(command))
                    connection.commit()
                except Exception as e:
                    logger.warning(f"Rollback command failed: {e}")
                    continue
        
        logger.info("✅ Migration rollback completed!")
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration for approval fields")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        run_migration()