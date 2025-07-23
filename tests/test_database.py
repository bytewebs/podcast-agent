import pytest
from database.connection import init_db, get_db
from database.repositories import PodcastRepository
from database.models import JobStatus
import uuid

class TestDatabase:
    
    def setup_method(self):
        """Setup test database"""
        init_db()
        self.repo = PodcastRepository()
    
    def test_create_job(self):
        """Test job creation"""
        job_id = f"test_{uuid.uuid4().hex[:8]}"
        brief = {
            "topic": "Test Topic",
            "tone": "professional",
            "length_minutes": 10
        }
        
        job = self.repo.create_job(job_id, brief)
        
        assert job.job_id == job_id
        assert job.brief == brief
        assert job.status == JobStatus.PENDING
    
    def test_get_job(self):
        """Test job retrieval"""
        job_id = f"test_{uuid.uuid4().hex[:8]}"
        brief = {"topic": "Test"}
        
        # Create job
        created_job = self.repo.create_job(job_id, brief)
        
        # Retrieve job
        retrieved_job = self.repo.get_job(job_id)
        
        assert retrieved_job is not None
        assert retrieved_job.job_id == job_id
    
    def test_update_job(self):
        """Test job update"""
        job_id = f"test_{uuid.uuid4().hex[:8]}"
        brief = {"topic": "Test"}
        
        # Create job
        self.repo.create_job(job_id, brief)
        
        # Update job
        updates = {"status": JobStatus.OUTLINE_GENERATION.value}
        updated_job = self.repo.update_job(job_id, updates)
        
        assert updated_job is not None
        assert updated_job.status == JobStatus.OUTLINE_GENERATION
    
    def test_list_jobs(self):
        """Test jobs listing"""
        # Create multiple jobs
        for i in range(3):
            job_id = f"test_{uuid.uuid4().hex[:8]}"
            brief = {"topic": f"Test Topic {i}"}
            self.repo.create_job(job_id, brief)
        
        jobs = self.repo.get_all_jobs()
        assert len(jobs) >= 3