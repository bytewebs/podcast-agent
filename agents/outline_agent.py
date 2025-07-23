from agents.base_agent import BaseAgent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from api.schemas import OutlineStructure
from messaging.topics import KafkaTopics
from database.models import JobStatus
from utils.config import config
import logging

logger = logging.getLogger(__name__)

class OutlineAgent(BaseAgent):
    """Agent responsible for generating podcast outlines"""

    def __init__(self):
        super().__init__("outline")
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=config.OPENAI_API_KEY,  
            temperature=0.7
        )
        self.parser = PydanticOutputParser(pydantic_object=OutlineStructure)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert podcast content creator. Generate a structured outline for a podcast based on the given brief.

Consider:
- The target audience and their interests
- The desired tone and style
- The time constraints
- Logical flow and engagement

{format_instructions}"""),
            ("human", """Create a podcast outline for:
Topic: {topic}
Tone: {tone}
Length: {length_minutes} minutes
Target Audience: {target_audience}
Key Points: {key_points}
Avoid Topics: {avoid_topics}
Additional Context: {additional_context}""")
        ])

    def process(self, message: dict):
        """Generate podcast outline"""
        job_id = message.get("job_id")
        brief = message.get("brief", {})

        if not isinstance(job_id, str):
            self.logger.error("Missing or invalid 'job_id' in message.")
            return

        try:
            self.logger.info(f"Generating outline for job {job_id}")
            self.update_job_status(job_id, JobStatus.OUTLINE_GENERATION.value)

            # Handle None values for key points and avoid topics
            key_points = brief.get("key_points") or []
            avoid_topics = brief.get("avoid_topics") or []

            # Ensure they are lists
            if not isinstance(key_points, list):
                key_points = []
            if not isinstance(avoid_topics, list):
                avoid_topics = []

            # Create the chain
            chain = self.prompt | self.llm | self.parser

            outline = chain.invoke({
                "topic": brief.get("topic", ""),
                "tone": brief.get("tone", ""),
                "length_minutes": brief.get("length_minutes", 10),
                "target_audience": brief.get("target_audience", "general audience"),
                "key_points": ", ".join(key_points),
                "avoid_topics": ", ".join(avoid_topics),
                "additional_context": brief.get("additional_context", "") or "",
                "format_instructions": self.parser.get_format_instructions()
            })

            # Save generated outline to DB
            self.repo.update_job(job_id, {"outline": outline.model_dump()})

            # Send to next stage
            self.send_to_next_stage(
                KafkaTopics.OUTLINE_EVALUATION,
                {
                    "job_id": job_id,
                    "outline": outline.model_dump(),
                    "brief": brief
                }
            )

        except Exception as e:
            self.logger.error(f"Outline generation failed for job {job_id}: {str(e)}")
            self.handle_error(job_id, f"Outline generation failed: {str(e)}")
