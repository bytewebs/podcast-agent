from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
from messaging.kafka_producer import KafkaProducerClient
from messaging.topics import KafkaTopics
from database.repositories import PodcastRepository
from utils.config import config
import logging

logger = logging.getLogger(__name__)

class OutlineEvaluation(BaseModel):
    structure_score: float = Field(..., ge=0, le=1, description="Score for outline structure")
    relevance_score: float = Field(..., ge=0, le=1, description="Score for topic relevance")
    completeness_score: float = Field(..., ge=0, le=1, description="Score for completeness")
    flow_score: float = Field(..., ge=0, le=1, description="Score for logical flow")
    overall_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    feedback: str = Field(..., description="Detailed feedback")
    issues: List[str] = Field(default_factory=list, description="List of issues found")

class OutlineEvaluator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=config.OPENAI_API_KEY,
            temperature=0.3
        )
        self.parser = PydanticOutputParser(pydantic_object=OutlineEvaluation)
        self.producer = KafkaProducerClient()
        self.repo = PodcastRepository()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert podcast content evaluator. Evaluate the quality of podcast outlines based on:
            
            1. Structure: Clear introduction, logical sections, strong conclusion
            2. Relevance: Alignment with the brief and topic
            3. Completeness: Coverage of key points without gaps
            4. Flow: Natural progression and transitions
            
            Be critical but constructive. Identify specific issues that need improvement.
            
            {format_instructions}"""),
            ("human", """Evaluate this podcast outline:
            
            Brief:
            Topic: {topic}
            Tone: {tone}
            Target Audience: {audience}
            Key Points: {key_points}
            
            Outline:
            {outline}
            
            Provide detailed evaluation scores and feedback.""")
        ])
    
    def evaluate(self, job_id: str, outline: dict, brief: dict):
        """Evaluate outline quality"""
        try:
            logger.info(f"Evaluating outline for job {job_id}")
            
            # Create chain
            chain = self.prompt | self.llm | self.parser
            
            # Fix the bug: ensure key_points is always a list
            key_points = brief.get("key_points") or []
            if not isinstance(key_points, list):
                key_points = []
            
            evaluation = chain.invoke({
                "topic": brief["topic"],
                "tone": brief["tone"],
                "audience": brief.get("target_audience", "general"),
                "key_points": ", ".join(key_points),  # Now safe to join
                "outline": self._format_outline(outline),
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Save evaluation result
            self.repo.save_evaluation_result_to_db(
                job_id=job_id,
                stage="outline",
                score=evaluation.model_dump(),
                passed=evaluation.overall_score >= 0.7,
                feedback=evaluation.feedback
            )
            
            # Determine next step
            if evaluation.overall_score >= 0.7:
                # Send to guardrails
                self.producer.send_message(
                    KafkaTopics.OUTLINE_APPROVAL,
                    {
                        "job_id": job_id,
                        "outline": outline,
                        "brief": brief,
                        "evaluation": evaluation.model_dump()
                    }
                )
            else:
                # Send back for regeneration
                self.producer.send_message(
                    KafkaTopics.OUTLINE_GENERATION,
                    {
                        "job_id": job_id,
                        "brief": brief,
                        "feedback": evaluation.feedback,
                        "issues": evaluation.issues,
                        "retry": True
                    }
                )
            
        except Exception as e:
            logger.error(f"Outline evaluation failed: {str(e)}")
            self.producer.send_message(KafkaTopics.DLQ, {
                "job_id": job_id,
                "error": str(e),
                "stage": "outline_evaluation"
            })
    
    def _format_outline(self, outline: dict) -> str:
        """Format outline for evaluation"""
        return f"""
Title: {outline.get('title', '')}

Introduction:
{outline.get('introduction', '')}

Sections:
{self._format_sections(outline.get('sections', []))}

Conclusion:
{outline.get('conclusion', '')}

Estimated Duration: {outline.get('estimated_duration', 0)} minutes
"""
    
    def _format_sections(self, sections: List[dict]) -> str:
        formatted = []
        for i, section in enumerate(sections, 1):
            formatted.append(f"{i}. {section.get('title', '')}")
            formatted.append(f"   {section.get('content', '')}")
        return "\n".join(formatted)