from prefect.task_runners import ConcurrentTaskRunner
from prefect import task, flow, get_run_logger
from datetime import datetime, timezone
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/app')

@task(
    name="generate-outline",
    description="Generate podcast outline using AI",
    retries=2,
    retry_delay_seconds=60,
    timeout_seconds=300
)
async def generate_outline_task(job_id: str, brief: dict):
    """Generate podcast outline"""
    logger = get_run_logger()
    logger.info(f"Generating outline for job {job_id}")
    
    try:
        from agents.outline_agent import OutlineAgent
        
        agent = OutlineAgent()
        result = await asyncio.to_thread(
            agent.process, 
            {"job_id": job_id, "brief": brief}
        )
        
        logger.info(f"Outline generated successfully for job {job_id}")
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Outline generation failed for job {job_id}: {str(e)}")
        raise

@task(
    name="evaluate-outline",
    description="Evaluate outline quality",
    retries=1,
    retry_delay_seconds=30
)
async def evaluate_outline_task(job_id: str, brief: dict):
    """Evaluate outline quality"""
    logger = get_run_logger()
    logger.info(f"Evaluating outline for job {job_id}")
    
    try:
        from evaluation.outline_evaluator import OutlineEvaluator
        from database.repositories import PodcastRepository
        
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.outline:
            raise ValueError(f"No outline found for job {job_id}")
        
        evaluator = OutlineEvaluator()
        await asyncio.to_thread(
            evaluator.evaluate, 
            job_id, job.outline, brief
        )
        
        logger.info(f"Outline evaluation completed for job {job_id}")
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Outline evaluation failed for job {job_id}: {str(e)}")
        raise

@task(
    name="auto-approve-outline",
    description="Auto-approve outline (no email required)",
    retries=1
)
async def auto_approve_outline_task(job_id: str):
    """Auto-approve outline"""
    logger = get_run_logger()
    logger.info(f"Auto-approving outline for job {job_id}")
    
    try:
        from database.repositories import PodcastRepository
        
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "outline_approved": True,
            "status": "SCRIPT_GENERATION"
        })
        
        logger.info(f"Outline auto-approved for job {job_id}")
        return {"status": "approved", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Outline auto-approval failed for job {job_id}: {str(e)}")
        raise

@task(
    name="generate-script",
    description="Generate podcast script",
    retries=2,
    retry_delay_seconds=60
)
async def generate_script_task(job_id: str, brief: dict):
    """Generate script"""
    logger = get_run_logger()
    logger.info(f"Generating script for job {job_id}")
    
    try:
        from agents.script_agent import ScriptAgent
        from database.repositories import PodcastRepository
        
        # Get outline from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.outline:
            raise ValueError(f"No outline found for job {job_id}")
        
        agent = ScriptAgent()
        await asyncio.to_thread(
            agent.process,
            {
                "job_id": job_id,
                "outline": job.outline,
                "brief": brief
            }
        )
        
        logger.info(f"Script generated successfully for job {job_id}")
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Script generation failed for job {job_id}: {str(e)}")
        raise

@task(
    name="evaluate-script",
    description="Evaluate script quality",
    retries=1
)
async def evaluate_script_task(job_id: str, brief: dict):
    """Evaluate script"""
    logger = get_run_logger()
    logger.info(f"Evaluating script for job {job_id}")
    
    try:
        from evaluation.script_evaluator import ScriptEvaluator
        from database.repositories import PodcastRepository
        
        # Get script and outline from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.script or not job.outline:
            raise ValueError(f"No script or outline found for job {job_id}")
        
        evaluator = ScriptEvaluator()
        await asyncio.to_thread(
            evaluator.evaluate,
            job_id, job.script, job.outline, brief
        )
        
        logger.info(f"Script evaluation completed for job {job_id}")
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Script evaluation failed for job {job_id}: {str(e)}")
        raise

@task(
    name="auto-approve-script",
    description="Auto-approve script (no email required)",
    retries=1
)
async def auto_approve_script_task(job_id: str):
    """Auto-approve script"""
    logger = get_run_logger()
    logger.info(f"Auto-approving script for job {job_id}")
    
    try:
        from database.repositories import PodcastRepository
        
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "script_approved": True,
            "status": "TTS_GENERATION"
        })
        
        logger.info(f"Script auto-approved for job {job_id}")
        return {"status": "approved", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Script auto-approval failed for job {job_id}: {str(e)}")
        raise

@task(
    name="generate-audio",
    description="Generate audio from script",
    retries=2,
    retry_delay_seconds=60
)
async def generate_audio_task(job_id: str, brief: dict):
    """Generate audio"""
    logger = get_run_logger()
    logger.info(f"Generating audio for job {job_id}")
    
    try:
        from agents.tts_agent import TTSAgent
        from database.repositories import PodcastRepository
        
        # Get script from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.script:
            raise ValueError(f"No script found for job {job_id}")
        
        agent = TTSAgent()
        await asyncio.to_thread(
            agent.process,
            {
                "job_id": job_id,
                "script": job.script,
                "voice_preference": brief.get("voice_preference", "professional_female")
            }
        )
        
        logger.info(f"Audio generated successfully for job {job_id}")
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Audio generation failed for job {job_id}: {str(e)}")
        raise

@task(
    name="evaluate-audio",
    description="Evaluate audio quality",
    retries=1
)
async def evaluate_audio_task(job_id: str):
    """Evaluate audio quality"""
    logger = get_run_logger()
    logger.info(f"Evaluating audio quality for job {job_id}")
    
    try:
        from database.repositories import PodcastRepository
        
        # Get audio URL from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.audio_url:
            raise ValueError(f"No audio found for job {job_id}")
        
        # Simulate audio evaluation (in production, implement actual checks)
        await asyncio.sleep(2)
        
        # For demo purposes, assume evaluation passes
        evaluation_score = 0.85
        
        # Save evaluation result
        repo.save_evaluation_result_to_db(
            job_id=job_id,
            stage="audio",
            score={"quality_score": evaluation_score},
            passed=evaluation_score >= 0.8,
            feedback="Audio quality acceptable"
        )
        
        logger.info(f"Audio evaluation completed for job {job_id}")
        return {"status": "success", "job_id": job_id, "score": evaluation_score}
        
    except Exception as e:
        logger.error(f"Audio evaluation failed for job {job_id}: {str(e)}")
        raise

@task(
    name="auto-approve-audio",
    description="Auto-approve audio (no email required)",
    retries=1
)
async def auto_approve_audio_task(job_id: str):
    """Auto-approve audio"""
    logger = get_run_logger()
    logger.info(f"Auto-approving audio for job {job_id}")
    
    try:
        from database.repositories import PodcastRepository
        
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "audio_approved": True,
            "status": "PUBLISHING"
        })
        
        logger.info(f"Audio auto-approved for job {job_id}")
        return {"status": "approved", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Audio auto-approval failed for job {job_id}: {str(e)}")
        raise

@task(
    name="publish-podcast",
    description="Publish podcast and create RSS feed",
    retries=2,
    retry_delay_seconds=60
)
async def publish_task(job_id: str):
    """Publish podcast"""
    logger = get_run_logger()
    logger.info(f"Publishing podcast for job {job_id}")
    
    try:
        from agents.publishing_agent import PublishingAgent
        
        agent = PublishingAgent()
        await asyncio.to_thread(
            agent.process,
            {"job_id": job_id}
        )
        
        logger.info(f"Podcast published successfully for job {job_id}")
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Publishing failed for job {job_id}: {str(e)}")
        raise

@task(
    name="complete-job",
    description="Mark job as completed",
    retries=1
)
async def completion_task(job_id: str):
    """Final task to mark job as completed"""
    logger = get_run_logger()
    logger.info(f"Marking job {job_id} as completed")
    
    try:
        from database.repositories import PodcastRepository
        
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "status": "COMPLETED",
            "completed_at": datetime.now(timezone.utc)
        })
        
        logger.info(f"Job {job_id} marked as completed")
        return {"status": "completed", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Job completion failed for job {job_id}: {str(e)}")
        raise

@task(
    name="handle-flow-failure",
    description="Handle flow failure",
    retries=0
)
async def handle_flow_failure(job_id: str, error_message: str):
    """Handle flow failure"""
    logger = get_run_logger()
    logger.error(f"Handling flow failure for job {job_id}: {error_message}")
    
    try:
        from database.repositories import PodcastRepository
        
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "status": "FAILED",
            "error_message": f"Prefect flow failed: {error_message}",
            "updated_at": datetime.now(timezone.utc)
        })
        
        logger.info(f"Job {job_id} marked as failed")
        
    except Exception as e:
        logger.error(f"Failed to handle flow failure for job {job_id}: {str(e)}")

@flow(
    name="podcast-generation-pipeline",
    description="Complete end-to-end podcast generation pipeline (auto-approval)",
    task_runner=ConcurrentTaskRunner(),
    retries=1,
    retry_delay_seconds=300,
    timeout_seconds=86400  # 24 hours
)
async def podcast_generation_flow(job_id: str, brief: dict, user_email: str = None):
    """Main Prefect flow for podcast generation - SIMPLIFIED WITHOUT EMAIL APPROVALS"""
    logger = get_run_logger()
    logger.info(f"Starting podcast generation flow for job {job_id}")
    
    try:
        # Stage 1: Outline Generation and Auto-Approval
        await generate_outline_task(job_id, brief)
        await evaluate_outline_task(job_id, brief)
        await auto_approve_outline_task(job_id)
        
        # Stage 2: Script Generation and Auto-Approval  
        await generate_script_task(job_id, brief)
        await evaluate_script_task(job_id, brief)
        await auto_approve_script_task(job_id)
        
        # Stage 3: Audio Generation and Auto-Approval
        await generate_audio_task(job_id, brief)
        await evaluate_audio_task(job_id)
        await auto_approve_audio_task(job_id)
        
        # Stage 4: Publishing
        await publish_task(job_id)
        await completion_task(job_id)
        
        logger.info(f"Podcast generation completed successfully for job {job_id}")
        return {"status": "completed", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Flow failed for job {job_id}: {str(e)}")
        await handle_flow_failure(job_id, str(e))
        raise

if __name__ == "__main__":
    # For local testing
    import asyncio
    
    test_brief = {
        "topic": "The Future of AI",
        "tone": "professional",
        "length_minutes": 15,
        "target_audience": "tech enthusiasts",
        "user_email": "test@example.com"
    }
    
    asyncio.run(podcast_generation_flow("test-job-123", test_brief, "test@example.com"))
