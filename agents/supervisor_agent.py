from agents.base_agent import BaseAgent
from messaging.topics import KafkaTopics
from database.models import JobStatus
import requests
import os
import time
from datetime import datetime, timezone

class SupervisorAgent(BaseAgent):
    """Supervisor agent that orchestrates the entire workflow"""
    
    def __init__(self):
        super().__init__("supervisor")
        
        # Read environment variables with defaults
        self.airflow_enabled = os.getenv('AIRFLOW_ENABLED', 'false').lower() == 'true'
        self.airflow_base_url = os.getenv('AIRFLOW_BASE_URL', 'http://airflow-webserver:8080')
        self.airflow_username = os.getenv('AIRFLOW_USERNAME', 'admin')
        self.airflow_password = os.getenv('AIRFLOW_PASSWORD', 'admin')
        
        self.logger.info(f"Supervisor initialized - Airflow enabled: {self.airflow_enabled}")
        self.logger.info(f"Airflow URL: {self.airflow_base_url}")
    
    def start_job(self, job_id: str, brief: dict):
        """Start a new podcast generation job"""
        self.logger.info(f"Starting job {job_id}")
        
        # Update status
        self.update_job_status(job_id, JobStatus.OUTLINE_GENERATION.value)
        
        # Send to outline generation (Kafka workflow)
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
        
        # Try Airflow DAG trigger (optional)
        if self.airflow_enabled:
            airflow_result = self._trigger_airflow_dag(job_id, brief)
            if airflow_result.get("success"):
                self.logger.info(f"Airflow DAG triggered successfully for job {job_id}")
            else:
                self.logger.warning(f"Airflow trigger failed: {airflow_result.get('error')}")
        else:
            self.logger.info("Airflow is disabled, using Kafka-only workflow")
        
        return {"success": True, "job_id": job_id}
    
    def _trigger_airflow_dag(self, job_id: str, brief: dict):
        """Trigger Airflow DAG for the job"""
        try:
            self.logger.info(f"Triggering Airflow DAG for job {job_id}")
            
            # Create unique DAG run ID
            dag_run_id = f"podcast_job_{job_id}_{int(time.time())}"
            
            # DAG configuration
            dag_config = {
                "job_id": job_id,
                "brief": brief,
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "triggered_by": "supervisor_agent"
            }
            
            # API request to trigger DAG
            url = f"{self.airflow_base_url}/api/v1/dags/podcast_generation_pipeline/dagRuns"
            
            payload = {
                "conf": dag_config,
                "dag_run_id": dag_run_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Use basic authentication
            auth = (self.airflow_username, self.airflow_password)
            
            # Make the request
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                auth=auth,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Successfully triggered Airflow DAG: {dag_run_id}")
                return {"success": True, "dag_run_id": dag_run_id}
            else:
                error_msg = f"Airflow API error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Cannot connect to Airflow: {str(e)}"
            self.logger.warning(error_msg)
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Failed to trigger Airflow DAG: {str(e)}"
            self.logger.warning(error_msg)
            return {"success": False, "error": error_msg}
    
    def process(self, message: dict):
        """Process supervisor messages"""
        self.logger.info(f"Processing supervisor message: {message}")
        pass