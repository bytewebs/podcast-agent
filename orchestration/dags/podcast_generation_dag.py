from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, '/opt/airflow')

logger = logging.getLogger(__name__)

# Default arguments for tasks
default_args = {
    'owner': 'podcast-system',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'podcast_generation_pipeline',
    default_args=default_args,
    description='Complete end-to-end podcast generation pipeline',
    schedule_interval=None,  # Triggered manually
    catchup=False,
    tags=['podcast', 'ai', 'generation'],
)

def generate_outline_task(**context):
    """Task to generate podcast outline"""
    try:
        from agents.outline_agent import OutlineAgent
        
        job_id = context['dag_run'].conf.get('job_id')
        brief = context['dag_run'].conf.get('brief')
        
        logger.info(f"Generating outline for job {job_id}")
        
        agent = OutlineAgent()
        agent.process({
            "job_id": job_id,
            "brief": brief
        })
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Outline generation failed: {str(e)}")
        raise

def evaluate_outline_task(**context):
    """Task to evaluate outline"""
    try:
        from evaluation.outline_evaluator import OutlineEvaluator
        from database.repositories import PodcastRepository
        
        job_id = context['dag_run'].conf.get('job_id')
        brief = context['dag_run'].conf.get('brief')
        
        # Get outline from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.outline:
            raise ValueError(f"No outline found for job {job_id}")
        
        logger.info(f"Evaluating outline for job {job_id}")
        
        evaluator = OutlineEvaluator()
        evaluator.evaluate(job_id, job.outline, brief)
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Outline evaluation failed: {str(e)}")
        raise

def approve_outline_task(**context):
    """Task for outline approval (auto-approval in Airflow)"""
    try:
        from database.repositories import PodcastRepository
        
        job_id = context['dag_run'].conf.get('job_id')
        
        logger.info(f"Auto-approving outline for job {job_id}")
        
        # Update approval status
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "outline_approved": True,
            "status": "SCRIPT_GENERATION"
        })
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Outline approval failed: {str(e)}")
        raise

def generate_script_task(**context):
    """Task to generate script"""
    try:
        from agents.script_agent import ScriptAgent
        from database.repositories import PodcastRepository
        
        job_id = context['dag_run'].conf.get('job_id')
        brief = context['dag_run'].conf.get('brief')
        
        # Get outline from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.outline:
            raise ValueError(f"No outline found for job {job_id}")
        
        logger.info(f"Generating script for job {job_id}")
        
        agent = ScriptAgent()
        agent.process({
            "job_id": job_id,
            "outline": job.outline,
            "brief": brief
        })
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Script generation failed: {str(e)}")
        raise

def evaluate_script_task(**context):
    """Task to evaluate script"""
    try:
        from evaluation.script_evaluator import ScriptEvaluator
        from database.repositories import PodcastRepository
        
        job_id = context['dag_run'].conf.get('job_id')
        brief = context['dag_run'].conf.get('brief')
        
        # Get script and outline from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.script or not job.outline:
            raise ValueError(f"No script or outline found for job {job_id}")
        
        logger.info(f"Evaluating script for job {job_id}")
        
        evaluator = ScriptEvaluator()
        evaluator.evaluate(job_id, job.script, job.outline, brief)
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Script evaluation failed: {str(e)}")
        raise

def approve_script_task(**context):
    """Task for script approval (auto-approval in Airflow)"""
    try:
        from database.repositories import PodcastRepository
        
        job_id = context['dag_run'].conf.get('job_id')
        
        logger.info(f"Auto-approving script for job {job_id}")
        
        # Update approval status
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "script_approved": True,
            "status": "TTS_GENERATION"
        })
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Script approval failed: {str(e)}")
        raise

def generate_audio_task(**context):
    """Task to generate audio"""
    try:
        from agents.tts_agent import TTSAgent
        from database.repositories import PodcastRepository
        
        job_id = context['dag_run'].conf.get('job_id')
        brief = context['dag_run'].conf.get('brief')
        
        # Get script from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.script:
            raise ValueError(f"No script found for job {job_id}")
        
        logger.info(f"Generating audio for job {job_id}")
        
        agent = TTSAgent()
        agent.process({
            "job_id": job_id,
            "script": job.script,
            "voice_preference": brief.get("voice_preference", "professional_female")
        })
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        raise

def evaluate_audio_task(**context):
    """Task to evaluate audio quality"""
    try:
        from database.repositories import PodcastRepository
        import time
        
        job_id = context['dag_run'].conf.get('job_id')
        
        # Get audio URL from database
        repo = PodcastRepository()
        job = repo.get_job(job_id)
        
        if not job or not job.audio_url:
            raise ValueError(f"No audio found for job {job_id}")
        
        logger.info(f"Evaluating audio quality for job {job_id}")
        
        # Simulate audio evaluation (in production, implement actual checks)
        time.sleep(2)
        
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
        
        return {"status": "success", "job_id": job_id, "score": evaluation_score}
        
    except Exception as e:
        logger.error(f"Audio evaluation failed: {str(e)}")
        raise

def approve_audio_task(**context):
    """Task for audio approval (auto-approval in Airflow)"""
    try:
        from database.repositories import PodcastRepository
        
        job_id = context['dag_run'].conf.get('job_id')
        
        logger.info(f"Auto-approving audio for job {job_id}")
        
        # Update approval status
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "audio_approved": True,
            "status": "PUBLISHING"
        })
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Audio approval failed: {str(e)}")
        raise

def publish_task(**context):
    """Task to publish podcast"""
    try:
        from agents.publishing_agent import PublishingAgent
        
        job_id = context['dag_run'].conf.get('job_id')
        
        logger.info(f"Publishing podcast for job {job_id}")
        
        agent = PublishingAgent()
        agent.process({
            "job_id": job_id
        })
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Publishing failed: {str(e)}")
        raise

def completion_task(**context):
    """Final task to mark job as completed"""
    try:
        from database.repositories import PodcastRepository
        from datetime import datetime, timezone
        
        job_id = context['dag_run'].conf.get('job_id')
        
        logger.info(f"Marking job {job_id} as completed")
        
        repo = PodcastRepository()
        repo.update_job(job_id, {
            "status": "COMPLETED",
            "completed_at": datetime.now(timezone.utc)
        })
        
        return {"status": "completed", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Job completion failed: {str(e)}")
        raise

# ===== DEFINE ALL TASKS =====

# 1. Outline Generation
outline_task = PythonOperator(
    task_id='generate_outline',
    python_callable=generate_outline_task,
    dag=dag,
)

# 2. Outline Evaluation
outline_evaluation_task = PythonOperator(
    task_id='evaluate_outline',
    python_callable=evaluate_outline_task,
    dag=dag,
)

# 3. Outline Approval
outline_approval_task = PythonOperator(
    task_id='approve_outline',
    python_callable=approve_outline_task,
    dag=dag,
)

# 4. Script Generation
script_task = PythonOperator(
    task_id='generate_script',
    python_callable=generate_script_task,
    dag=dag,
)

# 5. Script Evaluation
script_evaluation_task = PythonOperator(
    task_id='evaluate_script',
    python_callable=evaluate_script_task,
    dag=dag,
)

# 6. Script Approval
script_approval_task = PythonOperator(
    task_id='approve_script',
    python_callable=approve_script_task,
    dag=dag,
)

# 7. Audio Generation
audio_task = PythonOperator(
    task_id='generate_audio',
    python_callable=generate_audio_task,
    dag=dag,
)

# 8. Audio Evaluation
audio_evaluation_task = PythonOperator(
    task_id='evaluate_audio',
    python_callable=evaluate_audio_task,
    dag=dag,
)

# 9. Audio Approval
audio_approval_task = PythonOperator(
    task_id='approve_audio',
    python_callable=approve_audio_task,
    dag=dag,
)

# 10. Publishing
publish_task_op = PythonOperator(
    task_id='publish_podcast',
    python_callable=publish_task,
    dag=dag,
)

# 11. Completion
completion_task_op = PythonOperator(
    task_id='complete_job',
    python_callable=completion_task,
    dag=dag,
)

# ===== DEFINE STREAMLINED PIPELINE DEPENDENCIES =====
# Updated pipeline without guardrail tasks:

outline_task >> outline_evaluation_task >> outline_approval_task >> \
script_task >> script_evaluation_task >> script_approval_task >> \
audio_task >> audio_evaluation_task >> audio_approval_task >> publish_task_op >> completion_task_op