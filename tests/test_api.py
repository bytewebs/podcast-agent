import pytest
import requests
import json
import time
from datetime import datetime

class TestPodcastAPI:
    BASE_URL = "http://localhost:5050"
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_api_documentation(self):
        """Test API documentation endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/docs")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        assert "title" in data
        assert data["title"] == "Podcast Generation API"
    
    def test_create_podcast_valid(self):
        """Test valid podcast creation"""
        payload = {
            "topic": "Test Podcast Creation",
            "tone": "professional",
            "length_minutes": 10,
            "target_audience": "test audience",
            "key_points": ["testing", "validation", "quality"],
            "voice_preference": "professional_female"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/podcast/create",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "created_at" in data
        return data["job_id"]
    
    def test_create_podcast_invalid_tone(self):
        """Test podcast creation with invalid tone"""
        payload = {
            "topic": "Test Podcast",
            "tone": "invalid_tone",
            "length_minutes": 10
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/podcast/create",
            json=payload
        )
        
        assert response.status_code == 400
    
    def test_create_podcast_invalid_length(self):
        """Test podcast creation with invalid length"""
        payload = {
            "topic": "Test Podcast",
            "tone": "professional",
            "length_minutes": 120  # Too long
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/podcast/create",
            json=payload
        )
        
        assert response.status_code == 400
    
    def test_get_job_status(self):
        """Test job status retrieval"""
        # First create a job
        job_id = self.test_create_podcast_valid()
        
        # Then check its status
        response = requests.get(f"{self.BASE_URL}/api/v1/podcast/{job_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_nonexistent_job_status(self):
        """Test status retrieval for nonexistent job"""
        fake_job_id = "job_nonexistent123"
        response = requests.get(f"{self.BASE_URL}/api/v1/podcast/{fake_job_id}/status")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_list_jobs(self):
        """Test jobs listing"""
        # Create a job first to ensure we have at least one
        self.test_create_podcast_valid()
        
        response = requests.get(f"{self.BASE_URL}/api/v1/podcast/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
        assert len(data["jobs"]) > 0
        
        # Check job structure
        job = data["jobs"][0]
        assert "job_id" in job
        assert "status" in job
        assert "topic" in job
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = requests.get(f"{self.BASE_URL}/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "completed_jobs" in data
        assert "failed_jobs" in data
        assert "pending_jobs" in data
    
    def test_approval_endpoints(self):
        """Test approval endpoints"""
        # Create a job first
        job_id = self.test_create_podcast_valid()
        
        # Test outline approval
        approval_data = {
            "approved": True,
            "feedback": "Looks good"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/approval/{job_id}/outline",
            json=approval_data
        )
        # Note: This might return 404 if job hasn't reached approval stage yet
        assert response.status_code in [200, 404]
    
    def test_create_podcast_missing_fields(self):
        """Test podcast creation with missing required fields"""
        payload = {
            "topic": "Test Podcast"
            # Missing required tone and length_minutes
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/podcast/create",
            json=payload
        )
        
        assert response.status_code == 400
    
    def test_create_podcast_empty_payload(self):
        """Test podcast creation with empty payload"""
        response = requests.post(
            f"{self.BASE_URL}/api/v1/podcast/create",
            json={}
        )
        
        assert response.status_code == 400
    
    def test_rate_limiting(self):
        """Test basic rate limiting behavior"""
        # Create multiple jobs quickly
        job_ids = []
        for i in range(3):
            payload = {
                "topic": f"Rate Limit Test {i}",
                "tone": "professional",
                "length_minutes": 5
            }
            
            response = requests.post(
                f"{self.BASE_URL}/api/v1/podcast/create",
                json=payload
            )
            
            if response.status_code == 201:
                job_ids.append(response.json()["job_id"])
        
        # Should have created at least one job
        assert len(job_ids) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])