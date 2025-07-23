#!/usr/bin/env python3
"""
System validation script to check all components
"""

import requests
import time
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemValidator:
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        full_message = f"{status} {test_name}"
        if message:
            full_message += f" - {message}"
        
        print(full_message)
        logger.info(full_message)
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        return passed
    
    def test_health_endpoint(self) -> bool:
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return self.log_test("Health Endpoint", True, f"Service: {data.get('service', 'unknown')}")
                else:
                    return self.log_test("Health Endpoint", False, f"Unhealthy status: {data.get('status')}")
            else:
                return self.log_test("Health Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("Health Endpoint", False, str(e))
    
    def test_api_documentation(self) -> bool:
        """Test API documentation endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/docs", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "endpoints" in data and "title" in data:
                    return self.log_test("API Documentation", True, f"Found {len(data['endpoints'])} endpoints")
                else:
                    return self.log_test("API Documentation", False, "Invalid documentation format")
            else:
                return self.log_test("API Documentation", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("API Documentation", False, str(e))
    
    def test_podcast_creation(self) -> Optional[str]:
        """Test podcast creation endpoint"""
        try:
            payload = {
                "topic": "System Validation Test Podcast",
                "tone": "professional",
                "length_minutes": 5,
                "target_audience": "system administrators",
                "key_points": ["validation", "testing", "quality"],
                "voice_preference": "professional_female"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/podcast/create",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                job_id = data.get("job_id")
                if job_id:
                    self.log_test("Podcast Creation", True, f"Created job: {job_id}")
                    return job_id
                else:
                    self.log_test("Podcast Creation", False, "No job_id in response")
                    return None
            else:
                self.log_test("Podcast Creation", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Podcast Creation", False, str(e))
            return None

    def test_job_status(self, job_id: str) -> bool:
        """Test job status endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/podcast/{job_id}/status",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                if status:
                    return self.log_test("Job Status", True, f"Status: {status}")
                else:
                    return self.log_test("Job Status", False, "No status in response")
            else:
                return self.log_test("Job Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("Job Status", False, str(e))

    def test_list_jobs(self) -> bool:
        """Test list jobs endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/podcast/jobs",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                return self.log_test("List Jobs", True, f"Found {len(jobs)} jobs")
            else:
                return self.log_test("List Jobs", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("List Jobs", False, str(e))

    def test_metrics(self) -> bool:
        """Test system metrics endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/metrics",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if "uptime" in data:
                    return self.log_test("System Metrics", True, f"Uptime: {data.get('uptime')}")
                else:
                    return self.log_test("System Metrics", False, "No uptime in response")
            else:
                return self.log_test("System Metrics", False, f"HTTP {response.status_code}")
        except Exception as e:
            return self.log_test("System Metrics", False, str(e))

    def test_invalid_requests(self) -> None:
        """Test invalid requests and error handling"""
        # Invalid payload
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/podcast/create",
                json={"invalid": "data"},
                timeout=10
            )
            if response.status_code == 400:
                self.log_test("Invalid Payload", True, "Properly rejected invalid payload")
            else:
                self.log_test("Invalid Payload", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Payload", False, str(e))

        # Missing required fields
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/podcast/create",
                json={"topic": "Test"},
                timeout=10
            )
            if response.status_code == 400:
                self.log_test("Missing Fields", True, "Properly rejected missing fields")
            else:
                self.log_test("Missing Fields", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Missing Fields", False, str(e))

        # Non-existent job status
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/podcast/fake_job_id/status",
                timeout=10
            )
            if response.status_code == 404:
                self.log_test("Non-existent Job Status", True, "Properly returned 404")
            else:
                self.log_test("Non-existent Job Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Job Status", False, str(e))

    def summary(self):
        """Print summary of all tests"""
        print("\n==== System Validation Summary ====")
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        for result in self.test_results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{result['timestamp']} - {result['test']}: {status} - {result['message']}")
        print(f"\nTotal: {total} | Passed: {passed} | Failed: {total - passed}")
        if passed == total:
            print("🎉 All system validation tests passed!")
        else:
            print("❌ Some system validation tests failed.")

def main():
    validator = SystemValidator()
    print("🔎 Running system validation tests...\n")

    # 1. Health endpoint
    validator.test_health_endpoint()

    # 2. API documentation
    validator.test_api_documentation()

    # 3. Podcast creation
    job_id = validator.test_podcast_creation()

    # 4. Job status (if job created)
    if job_id:
        # Wait a few seconds for job to register
        time.sleep(2)
        validator.test_job_status(job_id)
    else:
        print("Skipping job status test due to podcast creation failure.")

    # 5. List jobs
    validator.test_list_jobs()

    # 6. System metrics
    validator.test_metrics()

    # 7. Invalid requests
    validator.test_invalid_requests()

    # 8. Summary
    validator.summary()

if __name__ == "__main__":
    main()
                    
