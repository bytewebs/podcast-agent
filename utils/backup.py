import json
import logging
from datetime import datetime
from database.repositories import PodcastRepository
from storage.s3_client import S3Client

logger = logging.getLogger(__name__)

class BackupManager:
    """Manage system backups"""
    
    def __init__(self):
        self.repo = PodcastRepository()
        self.s3_client = S3Client()
    
    def backup_jobs(self) -> bool:
        """Backup all jobs to S3"""
        try:
            jobs = self.repo.get_all_jobs()
            
            backup_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "job_count": len(jobs),
                "jobs": []
            }
            
            for job in jobs:
                job_data = {
                    "job_id": job.job_id,
                    "brief": job.brief,
                    "status": job.status.value,
                    "outline": job.outline,
                    "script": job.script,
                    "audio_url": job.audio_url,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                }
                backup_data["jobs"].append(job_data)
            
            # Upload backup
            backup_key = f"backups/jobs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            self.s3_client.upload_json(backup_data, backup_key)
            
            logger.info(f"Backup completed: {len(jobs)} jobs backed up")
            return True
        
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return False