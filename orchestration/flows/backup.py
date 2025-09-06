# # from prefect import flow, task, get_run_logger
# from prefect.task_runners import ConcurrentTaskRunner
# from prefect.blocks.system import Secret
# from prefect import task, flow, get_run_logger
# from datetime import timedelta, datetime, timezone
# import asyncio
# import sys
# import os
# import time

# # Add project root to path
# sys.path.insert(0, '/app')

# @task(
#     name="generate-outline",
#     description="Generate podcast outline using AI",
#     retries=2,
#     retry_delay_seconds=60,
#     timeout_seconds=300
# )
# async def generate_outline_task(job_id: str, brief: dict):
#     """Generate podcast outline"""
#     logger = get_run_logger()
#     logger.info(f"Generating outline for job {job_id}")
    
#     try:
#         from agents.outline_agent import OutlineAgent
        
#         agent = OutlineAgent()
#         result = await asyncio.to_thread(
#             agent.process, 
#             {"job_id": job_id, "brief": brief}
#         )
        
#         logger.info(f"Outline generated successfully for job {job_id}")
#         return {"status": "success", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Outline generation failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="evaluate-outline",
#     description="Evaluate outline quality",
#     retries=1,
#     retry_delay_seconds=30
# )
# async def evaluate_outline_task(job_id: str, brief: dict):
#     """Evaluate outline quality"""
#     logger = get_run_logger()
#     logger.info(f"Evaluating outline for job {job_id}")
    
#     try:
#         from evaluation.outline_evaluator import OutlineEvaluator
#         from database.repositories import PodcastRepository
        
#         repo = PodcastRepository()
#         job = repo.get_job(job_id)
        
#         if not job or not job.outline:
#             raise ValueError(f"No outline found for job {job_id}")
        
#         evaluator = OutlineEvaluator()
#         await asyncio.to_thread(
#             evaluator.evaluate, 
#             job_id, job.outline, brief
#         )
        
#         logger.info(f"Outline evaluation completed for job {job_id}")
#         return {"status": "success", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Outline evaluation failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="request-outline-approval",
#     description="Request outline approval via email",
#     retries=1
# )
# async def request_outline_approval_task(job_id: str, brief: dict, user_email: str = None):
#     """Request outline approval via email"""
#     logger = get_run_logger()
#     logger.info(f"Requesting outline approval for job {job_id}")
    
#     try:
#         from database.repositories import PodcastRepository
#         from services.email_service import EmailApprovalService
#         from messaging.topics import KafkaTopics
        
#         repo = PodcastRepository()
#         job = repo.get_job(job_id)
        
#         if not job or not job.outline:
#             raise ValueError(f"No outline found for job {job_id}")
        
#         # Get user email
#         user_email = (user_email or 
#                       brief.get('user_email') or 
#                       job.user_email or 
#                       os.getenv('DEFAULT_APPROVAL_EMAIL'))
        
#         if not user_email:
#             raise ValueError(f"No user email found for job {job_id}")
        
#         # Send approval email
#         email_service = EmailApprovalService()
#         success = await asyncio.to_thread(
#             email_service.send_outline_approval_email,
#             job_id, user_email, {"outline": job.outline, "brief": brief}
#         )
        
#         if not success:
#             raise Exception("Failed to send approval email")
        
#         # Update job status to pending approval
#         repo.update_job(job_id, {
#             "status": "OUTLINE_APPROVAL",
#             "outline_approval_requested": True,
#             "outline_approval_requested_at": datetime.now(timezone.utc),
#             "approval_stage": "outline",
#             "user_email": user_email
#         })
        
#         # Store continuation data for later
#         continuation_data = {
#             "next_topic": KafkaTopics.SCRIPT_GENERATION,
#             "next_message": {
#                 "job_id": job_id,
#                 "outline": job.outline,
#                 "brief": brief
#             },
#             "status_update": {
#                 "status": "SCRIPT_GENERATION",
#                 "outline_approved": True
#             }
#         }
        
#         repo.update_job(job_id, {"continuation_data": continuation_data})
        
#         logger.info(f"Outline approval email sent for job {job_id}")
#         return {"status": "approval_requested", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Failed to request outline approval for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="wait-for-outline-approval",
#     description="Wait for outline approval with polling",
#     timeout_seconds=604800,  # 7 days
#     retries=0
# )
# async def wait_for_outline_approval_task(job_id: str):
#     """Wait for outline approval with async polling"""
#     logger = get_run_logger()
#     logger.info(f"Waiting for outline approval for job {job_id}")
    
#     from database.repositories import PodcastRepository
    
#     repo = PodcastRepository()
#     timeout_hours = int(os.getenv('APPROVAL_TIMEOUT_HOURS', 168))  # 7 days
#     poll_interval = 30  # seconds
#     max_polls = (timeout_hours * 3600) // poll_interval
    
#     for poll_count in range(max_polls):
#         job = repo.get_job(job_id)
        
#         if not job:
#             raise ValueError(f"Job {job_id} not found")
        
#         # Check if approved
#         if job.outline_approved:
#             logger.info(f"Outline approved for job {job_id}")
#             return {"status": "approved", "job_id": job_id}
        
#         # Check if rejected
#         if job.status in ["FAILED", "REJECTED"]:
#             raise ValueError(f"Outline rejected for job {job_id}")
        
#         # Check for timeout
#         if job.outline_approval_requested_at:
#             elapsed = datetime.now(timezone.utc) - job.outline_approval_requested_at
#             if elapsed.total_seconds() > timeout_hours * 3600:
#                 repo.update_job(job_id, {
#                     "status": "FAILED",
#                     "error_message": "Outline approval timeout"
#                 })
#                 raise ValueError(f"Outline approval timeout for job {job_id}")
        
#         # Wait before next poll
#         await asyncio.sleep(poll_interval)
        
#         if poll_count % 120 == 0:  # Log every hour
#             logger.info(f"Still waiting for outline approval for job {job_id} (poll {poll_count})")
    
#     # Timeout reached
#     repo.update_job(job_id, {
#         "status": "FAILED",
#         "error_message": "Outline approval timeout"
#     })
#     raise ValueError(f"Outline approval timeout for job {job_id}")

# @task(
#     name="generate-script",
#     description="Generate podcast script",
#     retries=2,
#     retry_delay_seconds=60
# )
# async def generate_script_task(job_id: str, brief: dict):
#     """Generate script"""
#     logger = get_run_logger()
#     logger.info(f"Generating script for job {job_id}")
    
#     try:
#         from agents.script_agent import ScriptAgent
#         from database.repositories import PodcastRepository
        
#         # Get outline from database
#         repo = PodcastRepository()
#         job = repo.get_job(job_id)
        
#         if not job or not job.outline:
#             raise ValueError(f"No outline found for job {job_id}")
        
#         agent = ScriptAgent()
#         await asyncio.to_thread(
#             agent.process,
#             {
#                 "job_id": job_id,
#                 "outline": job.outline,
#                 "brief": brief
#             }
#         )
        
#         logger.info(f"Script generated successfully for job {job_id}")
#         return {"status": "success", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Script generation failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="evaluate-script",
#     description="Evaluate script quality",
#     retries=1
# )
# async def evaluate_script_task(job_id: str, brief: dict):
#     """Evaluate script"""
#     logger = get_run_logger()
#     logger.info(f"Evaluating script for job {job_id}")
    
#     try:
#         from evaluation.script_evaluator import ScriptEvaluator
#         from database.repositories import PodcastRepository
        
#         # Get script and outline from database
#         repo = PodcastRepository()
#         job = repo.get_job(job_id)
        
#         if not job or not job.script or not job.outline:
#             raise ValueError(f"No script or outline found for job {job_id}")
        
#         evaluator = ScriptEvaluator()
#         await asyncio.to_thread(
#             evaluator.evaluate,
#             job_id, job.script, job.outline, brief
#         )
        
#         logger.info(f"Script evaluation completed for job {job_id}")
#         return {"status": "success", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Script evaluation failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="request-script-approval",
#     description="Request script approval via email",
#     retries=1
# )
# async def request_script_approval_task(job_id: str, brief: dict, user_email: str = None):
#     """Request script approval via email"""
#     logger = get_run_logger()
#     logger.info(f"Requesting script approval for job {job_id}")
    
#     try:
#         from database.repositories import PodcastRepository
#         from services.email_service import EmailApprovalService
#         from messaging.topics import KafkaTopics
        
#         repo = PodcastRepository()
#         job = repo.get_job(job_id)
        
#         if not job or not job.script:
#             raise ValueError(f"No script found for job {job_id}")
        
#         # Get user email
#         user_email = job.user_email or os.getenv('DEFAULT_APPROVAL_EMAIL')
        
#         if not user_email:
#             raise ValueError(f"No user email found for job {job_id}")
        
#         # Send approval email
#         email_service = EmailApprovalService()
#         success = await asyncio.to_thread(
#             email_service.send_script_approval_email,
#             job_id, user_email, {"script": job.script, "brief": brief}
#         )
        
#         if not success:
#             raise Exception("Failed to send approval email")
        
#         # Update job status to pending approval
#         repo.update_job(job_id, {
#             "status": "SCRIPT_APPROVAL",
#             "script_approval_requested": True,
#             "script_approval_requested_at": datetime.now(timezone.utc),
#             "approval_stage": "script"
#         })
        
#         # Store continuation data
#         continuation_data = {
#             "next_topic": KafkaTopics.TTS_GENERATION,
#             "next_message": {
#                 "job_id": job_id,
#                 "script": job.script,
#                 "voice_preference": brief.get("voice_preference", "professional_female")
#             },
#             "status_update": {
#                 "status": "TTS_GENERATION",
#                 "script_approved": True
#             }
#         }
        
#         repo.update_job(job_id, {"continuation_data": continuation_data})
        
#         return {"status": "approval_requested", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Script approval request failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="wait-for-script-approval",
#     description="Wait for script approval",
#     timeout_seconds=604800,
#     retries=0
# )
# async def wait_for_script_approval_task(job_id: str):
#     """Wait for script approval"""
#     logger = get_run_logger()
#     logger.info(f"Waiting for script approval for job {job_id}")
    
#     from database.repositories import PodcastRepository
    
#     repo = PodcastRepository()
#     timeout_hours = int(os.getenv('APPROVAL_TIMEOUT_HOURS', 168))
#     poll_interval = 30
#     max_polls = (timeout_hours * 3600) // poll_interval
    
#     for poll_count in range(max_polls):
#         job = repo.get_job(job_id)
        
#         if not job:
#             raise ValueError(f"Job {job_id} not found")
        
#         # Check if approved
#         if job.script_approved:
#             logger.info(f"Script approved for job {job_id}")
#             return {"status": "approved", "job_id": job_id}
        
#         # Check if rejected
#         if job.status in ["FAILED", "REJECTED"]:
#             raise ValueError(f"Script rejected for job {job_id}")
        
#         # Check for timeout
#         if job.script_approval_requested_at:
#             elapsed = datetime.now(timezone.utc) - job.script_approval_requested_at
#             if elapsed.total_seconds() > timeout_hours * 3600:
#                 repo.update_job(job_id, {
#                     "status": "FAILED",
#                     "error_message": "Script approval timeout"
#                 })
#                 raise ValueError(f"Script approval timeout for job {job_id}")
        
#         await asyncio.sleep(poll_interval)
        
#         if poll_count % 120 == 0:
#             logger.info(f"Still waiting for script approval for job {job_id} (poll {poll_count})")
    
#     repo.update_job(job_id, {
#         "status": "FAILED",
#         "error_message": "Script approval timeout"
#     })
#     raise ValueError(f"Script approval timeout for job {job_id}")

# @task(
#     name="generate-audio",
#     description="Generate audio from script",
#     retries=2,
#     retry_delay_seconds=60
# )
# async def generate_audio_task(job_id: str, brief: dict):
#     """Generate audio"""
#     logger = get_run_logger()
#     logger.info(f"Generating audio for job {job_id}")
    
#     try:
#         from agents.tts_agent import TTSAgent
#         from database.repositories import PodcastRepository
        
#         # Get script from database
#         repo = PodcastRepository()
#         job = repo.get_job(job_id)
        
#         if not job or not job.script:
#             raise ValueError(f"No script found for job {job_id}")
        
#         agent = TTSAgent()
#         await asyncio.to_thread(
#             agent.process,
#             {
#                 "job_id": job_id,
#                 "script": job.script,
#                 "voice_preference": brief.get("voice_preference", "professional_female")
#             }
#         )
        
#         logger.info(f"Audio generated successfully for job {job_id}")
#         return {"status": "success", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Audio generation failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="evaluate-audio",
#     description="Evaluate audio quality",
#     retries=1
# )
# async def evaluate_audio_task(job_id: str):
#     """Evaluate audio quality"""
#     logger = get_run_logger()
#     logger.info(f"Evaluating audio quality for job {job_id}")
    
#     try:
#         from database.repositories import PodcastRepository
        
#         # Get audio URL from database
#         repo = PodcastRepository()
#         job = repo.get_job(job_id)
        
#         if not job or not job.audio_url:
#             raise ValueError(f"No audio found for job {job_id}")
        
#         # Simulate audio evaluation (in production, implement actual checks)
#         await asyncio.sleep(2)
        
#         # For demo purposes, assume evaluation passes
#         evaluation_score = 0.85
        
#         # Save evaluation result
#         repo.save_evaluation_result_to_db(
#             job_id=job_id,
#             stage="audio",
#             score={"quality_score": evaluation_score},
#             passed=evaluation_score >= 0.8,
#             feedback="Audio quality acceptable"
#         )
        
#         logger.info(f"Audio evaluation completed for job {job_id}")
#         return {"status": "success", "job_id": job_id, "score": evaluation_score}
        
#     except Exception as e:
#         logger.error(f"Audio evaluation failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="request-audio-approval",
#     description="Request audio approval via email",
#     retries=1
# )
# async def request_audio_approval_task(job_id: str, user_email: str = None):
#     """Request audio approval via email"""
#     logger = get_run_logger()
#     logger.info(f"Requesting audio approval for job {job_id}")
    
#     try:
#         from database.repositories import PodcastRepository
#         from services.email_service import EmailApprovalService
#         from messaging.topics import KafkaTopics
        
#         repo = PodcastRepository()
#         job = repo.get_job(job_id)
        
#         if not job or not job.audio_url:
#             raise ValueError(f"No audio found for job {job_id}")
        
#         # Get user email
#         user_email = job.user_email or os.getenv('DEFAULT_APPROVAL_EMAIL')
        
#         if not user_email:
#             raise ValueError(f"No user email found for job {job_id}")
        
#         # Send approval email
#         email_service = EmailApprovalService()
#         success = await asyncio.to_thread(
#             email_service.send_audio_approval_email,
#             job_id, user_email, {"audio_url": job.audio_url}
#         )
        
#         if not success:
#             raise Exception("Failed to send approval email")
        
#         # Update job status to pending approval
#         repo.update_job(job_id, {
#             "status": "AUDIO_APPROVAL",
#             "audio_approval_requested": True,
#             "audio_approval_requested_at": datetime.now(timezone.utc),
#             "approval_stage": "audio"
#         })
        
#         # Store continuation data
#         continuation_data = {
#             "next_topic": KafkaTopics.PUBLISHING,
#             "next_message": {
#                 "job_id": job_id,
#                 "audio_url": job.audio_url,
#                 "approved": True
#             },
#             "status_update": {
#                 "status": "PUBLISHING",
#                 "audio_approved": True
#             }
#         }
        
#         repo.update_job(job_id, {"continuation_data": continuation_data})
        
#         return {"status": "approval_requested", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Audio approval request failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="wait-for-audio-approval",
#     description="Wait for audio approval",
#     timeout_seconds=604800,
#     retries=0
# )
# async def wait_for_audio_approval_task(job_id: str):
#     """Wait for audio approval"""
#     logger = get_run_logger()
#     logger.info(f"Waiting for audio approval for job {job_id}")
    
#     from database.repositories import PodcastRepository
    
#     repo = PodcastRepository()
#     timeout_hours = int(os.getenv('APPROVAL_TIMEOUT_HOURS', 168))
#     poll_interval = 30
#     max_polls = (timeout_hours * 3600) // poll_interval
    
#     for poll_count in range(max_polls):
#         job = repo.get_job(job_id)
        
#         if not job:
#             raise ValueError(f"Job {job_id} not found")
        
#         # Check if approved
#         if job.audio_approved:
#             logger.info(f"Audio approved for job {job_id}")
#             return {"status": "approved", "job_id": job_id}
        
#         # Check if rejected
#         if job.status in ["FAILED", "REJECTED"]:
#             raise ValueError(f"Audio rejected for job {job_id}")
        
#         # Check for timeout
#         if job.audio_approval_requested_at:
#             elapsed = datetime.now(timezone.utc) - job.audio_approval_requested_at
#             if elapsed.total_seconds() > timeout_hours * 3600:
#                 repo.update_job(job_id, {
#                     "status": "FAILED",
#                     "error_message": "Audio approval timeout"
#                 })
#                 raise ValueError(f"Audio approval timeout for job {job_id}")
        
#         await asyncio.sleep(poll_interval)
        
#         if poll_count % 120 == 0:
#             logger.info(f"Still waiting for audio approval for job {job_id} (poll {poll_count})")
    
#     repo.update_job(job_id, {
#         "status": "FAILED",
#         "error_message": "Audio approval timeout"
#     })
#     raise ValueError(f"Audio approval timeout for job {job_id}")

# @task(
#     name="publish-podcast",
#     description="Publish podcast and create RSS feed",
#     retries=2,
#     retry_delay_seconds=60
# )
# async def publish_task(job_id: str):
#     """Publish podcast"""
#     logger = get_run_logger()
#     logger.info(f"Publishing podcast for job {job_id}")
    
#     try:
#         from agents.publishing_agent import PublishingAgent
        
#         agent = PublishingAgent()
#         await asyncio.to_thread(
#             agent.process,
#             {"job_id": job_id}
#         )
        
#         logger.info(f"Podcast published successfully for job {job_id}")
#         return {"status": "success", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Publishing failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="complete-job",
#     description="Mark job as completed",
#     retries=1
# )
# async def completion_task(job_id: str):
#     """Final task to mark job as completed"""
#     logger = get_run_logger()
#     logger.info(f"Marking job {job_id} as completed")
    
#     try:
#         from database.repositories import PodcastRepository
        
#         repo = PodcastRepository()
#         repo.update_job(job_id, {
#             "status": "COMPLETED",
#             "completed_at": datetime.now(timezone.utc)
#         })
        
#         logger.info(f"Job {job_id} marked as completed")
#         return {"status": "completed", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Job completion failed for job {job_id}: {str(e)}")
#         raise

# @task(
#     name="handle-flow-failure",
#     description="Handle flow failure",
#     retries=0
# )
# async def handle_flow_failure(job_id: str, error_message: str):
#     """Handle flow failure"""
#     logger = get_run_logger()
#     logger.error(f"Handling flow failure for job {job_id}: {error_message}")
    
#     try:
#         from database.repositories import PodcastRepository
        
#         repo = PodcastRepository()
#         repo.update_job(job_id, {
#             "status": "FAILED",
#             "error_message": f"Prefect flow failed: {error_message}",
#             "updated_at": datetime.now(timezone.utc)
#         })
        
#         logger.info(f"Job {job_id} marked as failed")
        
#     except Exception as e:
#         logger.error(f"Failed to handle flow failure for job {job_id}: {str(e)}")

# @flow(
#     name="podcast-generation-pipeline",
#     description="Complete end-to-end podcast generation pipeline with email approvals",
#     task_runner=ConcurrentTaskRunner(),
#     retries=1,
#     retry_delay_seconds=300,
#     timeout_seconds=86400  # 24 hours
# )
# async def podcast_generation_flow(job_id: str, brief: dict, user_email: str = None):
#     """Main Prefect flow for podcast generation"""
#     logger = get_run_logger()
#     logger.info(f"Starting podcast generation flow for job {job_id}")
    
#     try:
#         # Stage 1: Outline Generation and Approval
#         await generate_outline_task(job_id, brief)
#         await evaluate_outline_task(job_id, brief)
#         await request_outline_approval_task(job_id, brief, user_email)
#         await wait_for_outline_approval_task(job_id)
        
#         # Stage 2: Script Generation and Approval  
#         await generate_script_task(job_id, brief)
#         await evaluate_script_task(job_id, brief)
#         await request_script_approval_task(job_id, brief, user_email)
#         await wait_for_script_approval_task(job_id)
        
#         # Stage 3: Audio Generation and Approval
#         await generate_audio_task(job_id, brief)
#         await evaluate_audio_task(job_id)
#         await request_audio_approval_task(job_id, user_email)
#         await wait_for_audio_approval_task(job_id)
        
#         # Stage 4: Publishing
#         await publish_task(job_id)
#         await completion_task(job_id)
        
#         logger.info(f"Podcast generation completed successfully for job {job_id}")
#         return {"status": "completed", "job_id": job_id}
        
#     except Exception as e:
#         logger.error(f"Flow failed for job {job_id}: {str(e)}")
#         await handle_flow_failure(job_id, str(e))
#         raise

# if __name__ == "__main__":
#     # For local testing
#     import asyncio
    
#     test_brief = {
#         "topic": "The Future of AI",
#         "tone": "professional",
#         "length_minutes": 15,
#         "target_audience": "tech enthusiasts",
#         "user_email": "test@example.com"
#     }
    
#     asyncio.run(podcast_generation_flow("test-job-123", test_brief, "test@example.com"))