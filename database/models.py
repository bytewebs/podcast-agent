from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = "PENDING"
    OUTLINE_GENERATION = "OUTLINE_GENERATION"
    OUTLINE_EVALUATION = "OUTLINE_EVALUATION"
    OUTLINE_APPROVAL = "OUTLINE_APPROVAL"
    SCRIPT_GENERATION = "SCRIPT_GENERATION"
    SCRIPT_EVALUATION = "SCRIPT_EVALUATION"
    SCRIPT_APPROVAL = "SCRIPT_APPROVAL"
    TTS_GENERATION = "TTS_GENERATION"
    TTS_EVALUATION = "TTS_EVALUATION"
    AUDIO_APPROVAL = "AUDIO_APPROVAL"
    PUBLISHING = "PUBLISHING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class PodcastJob(Base):
    __tablename__ = "podcast_jobs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), unique=True, nullable=False)
    brief = Column(JSON, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    
    # Generated content
    outline = Column(JSON)
    script = Column(Text)
    audio_url = Column(String(500))
    rss_feed_url = Column(String(500))
    
    # Metadata
    podcast_metadata = Column(JSON, default={})
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Approvals
    outline_approved = Column(Boolean, default=False)
    script_approved = Column(Boolean, default=False)
    audio_approved = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), nullable=False)
    stage = Column(String(50), nullable=False)
    score = Column(JSON)
    passed = Column(Boolean, default=False)
    feedback = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class GuardrailResult(Base):
    __tablename__ = "guardrail_results"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), nullable=False)
    guardrail_type = Column(String(50), nullable=False)
    passed = Column(Boolean, default=True)
    details = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
