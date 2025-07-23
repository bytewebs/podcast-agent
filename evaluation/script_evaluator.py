from pydantic import BaseModel, Field
from typing import List
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from messaging.topics import KafkaTopics
from utils.config import config
from messaging.kafka_producer import KafkaProducerClient
from database.repositories import PodcastRepository
import logging

logger = logging.getLogger(__name__)

class ScriptEvaluation(BaseModel):
    fluency_score: float = Field(..., ge=0, le=1, description="Score for language fluency")
    accuracy_score: float = Field(..., ge=0, le=1, description="Score for factual accuracy")
    engagement_score: float = Field(..., ge=0, le=1, description="Score for engagement level")
    tone_score: float = Field(..., ge=0, le=1, description="Score for tone consistency")
    pacing_score: float = Field(..., ge=0, le=1, description="Score for pacing")
    overall_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    feedback: str = Field(..., description="Detailed feedback")
    corrections_needed: List[str] = Field(default_factory=list, description="Required corrections")

class ScriptEvaluator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=config.OPENAI_API_KEY,
            temperature=0.3
        )
        self.parser = PydanticOutputParser(pydantic_object=ScriptEvaluation)
        self.producer = KafkaProducerClient()
        self.repo = PodcastRepository()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert podcast script evaluator. Evaluate scripts for:
            
            1. Fluency: Natural, conversational language suitable for audio
            2. Accuracy: Factual correctness and clarity
            3. Engagement: Hooks, storytelling, audience retention
            4. Tone: Consistency with the requested tone
            5. Pacing: Appropriate speed and rhythm for the duration
            
            Identify specific areas that need improvement.
            
            {format_instructions}"""),
            ("human", """Evaluate this podcast script:
            
            Target Tone: {tone}
            Target Duration: {duration} minutes
            
            Script:
            {script}
            
            Provide detailed evaluation and specific corrections if needed.""")
        ])
    
    def evaluate(self, job_id: str, script: str, outline: dict, brief: dict):
        """Evaluate script quality"""
        try:
            logger.info(f"Evaluating script for job {job_id}")
            
            # Run evaluation
            chain = self.prompt | self.llm | self.parser
            
            evaluation = chain.invoke({
                "tone": brief["tone"],
                "duration": brief["length_minutes"],
                "script": script[:3000],  # Limit for token management
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Save evaluation result
            self.repo.save_evaluation_result_to_db(
                job_id=job_id,
                stage="script",
                score=evaluation.model_dump(),
                passed=evaluation.overall_score >= 0.75,
                feedback=evaluation.feedback
            )
            
            # Determine next step
            if evaluation.overall_score >= 0.75:
                # Send to guardrails
                self.producer.send_message(
                    KafkaTopics.SCRIPT_APPROVAL,
                    {
                        "job_id": job_id,
                        "script": script,
                        "outline": outline,
                        "brief": brief,
                        "evaluation": evaluation.model_dump()
                    }
                )
            else:
                # Send back for improvement
                self.producer.send_message(
                    KafkaTopics.SCRIPT_GENERATION,
                    {
                        "job_id": job_id,
                        "outline": outline,
                        "brief": brief,
                        "feedback": evaluation.feedback,
                        "corrections": evaluation.corrections_needed,
                        "retry": True
                    }
                )
            
        except Exception as e:
            logger.error(f"Script evaluation failed: {str(e)}")