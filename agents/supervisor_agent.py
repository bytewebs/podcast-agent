from agents.base_agent import BaseAgent
from messaging.topics import KafkaTopics
from database.models import JobStatus
from datetime import datetime, timezone
import logging
import os
import requests
import json
import traceback

logger = logging.getLogger(__name__)

class SupervisorAgent(BaseAgent):
    def __init__(self):
        super().__init__("supervisor")
        
        # Prefect configuration
        self.prefect_enabled = os.getenv('PREFECT_ENABLED', 'true').lower() == 'true'
        self.prefect_api_url = os.getenv('PREFECT_API_URL', 'http://prefect-server:4200/api')
        
        self.logger.info(f"Supervisor initialized - Prefect enabled: {self.prefect_enabled}")
        self.logger.info(f"Prefect API URL: {self.prefect_api_url}")

    def start_job(self, job_id: str, brief: dict):
        """Start a new podcast generation job"""
        self.logger.info(f"Starting job {job_id}")
        
        # Ensure user_email is included in the brief
        if 'user_email' not in brief:
            brief['user_email'] = os.getenv('DEFAULT_APPROVAL_EMAIL')
        
        # Update status
        self.update_job_status(job_id, JobStatus.OUTLINE_GENERATION.value)
        
        # Update job with user email
        self.repo.update_job(job_id, {"user_email": brief.get('user_email')})
        
        # Start Kafka workflow (immediate processing)
        kafka_success = self.send_to_next_stage(
            KafkaTopics.OUTLINE_GENERATION,
            {
                "job_id": job_id,
                "brief": brief
            }
        )
        
        if not kafka_success:
            self.logger.error(f"Failed to send job {job_id} to Kafka")
            return {"error": "Failed to start Kafka workflow"}
        
        # Trigger Prefect flow (for monitoring and orchestration)
        if self.prefect_enabled:
            prefect_result = self._trigger_prefect_flow_sync(job_id, brief)
            if prefect_result.get("success"):
                self.logger.info(f"Prefect flow triggered successfully for job {job_id}")
            else:
                self.logger.warning(f"Prefect trigger failed: {prefect_result.get('error')}")
                # Continue with Kafka-only workflow if Prefect fails
        else:
            self.logger.info("Prefect is disabled, using Kafka-only workflow")
        
        return {"success": True, "job_id": job_id}

    def _trigger_prefect_flow_sync(self, job_id: str, brief: dict):
        """Trigger Prefect flow using HTTP API - CORRECTED VERSION"""
        try:
            self.logger.info(f"🔧 Attempting to trigger Prefect flow for job {job_id}")
            
            # First, get all deployments to find ours
            deployments_url = f"{self.prefect_api_url}/deployments/"
            
            # Use POST with empty filter to get deployments (Prefect 2.x way)
            response = requests.post(
                deployments_url + "filter",
                json={},
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Failed to get deployments: {response.text}"}
            
            deployments = response.json()
            deployment_id = None
            
            self.logger.info(f"📋 Found {len(deployments)} deployments")
            
            # Find our deployment
            for deployment in deployments:
                if deployment.get("name") == "podcast-generation-deployment":
                    deployment_id = deployment.get("id")
                    self.logger.info(f"✅ Found deployment: {deployment_id}")
                    break
            
            if not deployment_id:
                available_deployments = [d.get("name") for d in deployments]
                return {"success": False, "error": f"Deployment 'podcast-generation-deployment' not found. Available: {available_deployments}"}
            
            # Create flow run using the correct endpoint
            flow_runs_url = f"{self.prefect_api_url}/deployments/{deployment_id}/create_flow_run"
            payload = {
                "parameters": {
                    "job_id": job_id,
                    "brief": brief,
                    "user_email": brief.get('user_email', '')
                },
                "tags": [f"job-{job_id}", "podcast-generation"]
            }
            
            self.logger.info(f"🚀 Creating flow run with payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                flow_runs_url, 
                json=payload, 
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                flow_run_data = response.json()
                flow_run_id = flow_run_data.get("id")
                self.logger.info(f"✅ Prefect flow triggered successfully: {flow_run_id}")
                return {"success": True, "flow_run_id": flow_run_id}
            else:
                self.logger.error(f"❌ HTTP API trigger failed ({response.status_code}): {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            self.logger.error(f"❌ Failed to trigger Prefect flow via HTTP: {str(e)}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def process(self, message: dict):
        """Process supervisor messages"""
        self.logger.info(f"Processing supervisor message: {message}")
        pass

