from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PodcastTone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    ENTERTAINING = "entertaining"
    INSPIRATIONAL = "inspirational"

class PodcastBrief(BaseModel):
    topic: str = Field(..., description="Main topic of the podcast")
    tone: PodcastTone = Field(..., description="Desired tone of the podcast")
    length_minutes: int = Field(..., ge=5, le=60, description="Target length in minutes")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    key_points: Optional[List[str]] = Field(None, description="Key points to cover")
    avoid_topics: Optional[List[str]] = Field(None, description="Topics to avoid")
    voice_preference: Optional[str] = Field(None, description="Voice preference for TTS")
    additional_context: Optional[str] = Field(None, description="Any additional context")

class PodcastJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    outline: Optional[Dict[str, Any]] = None
    script: Optional[str] = None
    audio_url: Optional[str] = None
    rss_feed_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ApprovalRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None

class OutlineStructure(BaseModel):
    title: str
    introduction: str
    sections: List[Dict[str, Any]]
    conclusion: str
    estimated_duration: int
