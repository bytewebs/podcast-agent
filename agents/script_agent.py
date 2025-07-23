from agents.base_agent import BaseAgent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from messaging.topics import KafkaTopics
from database.models import JobStatus
from utils.config import config
from utils.fact_checker import FactChecker
import logging

logger = logging.getLogger(__name__)

class ScriptAgent(BaseAgent):
    """Agent responsible for generating full podcast scripts"""
    
    def __init__(self):
        super().__init__("script")
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=config.OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=4000
        )
        self.fact_checker = FactChecker()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert podcast script writer. Create an engaging, natural-sounding script based on the provided outline.
            
            Guidelines:
            - Write in a conversational tone appropriate for audio
            - Include natural transitions between sections
            - Add personality and engagement hooks
            - Ensure facts are accurate and well-presented
            - Match the requested tone and style
            - Include time markers for pacing
            
            Format the script with:
            - Clear speaker labels if multiple hosts
            - Natural pauses indicated with [pause]
            - Emphasis markers for important points
            - Smooth introductions and conclusions"""),
            ("human", """Create a detailed podcast script based on this outline:
            
            Title: {title}
            Tone: {tone}
            Target Duration: {duration} minutes
            
            Outline:
            {outline}
            
            Additional Context:
            {context}
            
            Remember to make it sound natural and engaging for listeners.""")
        ])
    
    def process(self, message: dict):
        """Generate podcast script from outline"""
        job_id = message["job_id"]
        outline = message["outline"]
        brief = message["brief"]
        
        try:
            self.logger.info(f"Generating script for job {job_id}")
            self.update_job_status(job_id, JobStatus.SCRIPT_GENERATION.value)
            
            # Generate script using updated langchain syntax
            script_response = self.llm.invoke(
                self.prompt.format_prompt(
                    title=outline["title"],
                    tone=brief["tone"],
                    duration=brief["length_minutes"],
                    outline=self._format_outline(outline),
                    context=brief.get("additional_context", "")
                ).to_messages()
            )
            
            script = script_response.content
            
            # Fact check the script
            if not message.get("skip_fact_check", False):
                fact_check_results = self.fact_checker.check_script(script)
                if fact_check_results["needs_correction"]:
                    script = self._regenerate_with_corrections(
                        script, 
                        fact_check_results["corrections"]
                    )
            
            # Save script to database
            self.repo.update_job(job_id, {"script": script})
            
            # Send to evaluation
            self.send_to_next_stage(
                KafkaTopics.SCRIPT_EVALUATION,
                {
                    "job_id": job_id,
                    "script": script,
                    "outline": outline,
                    "brief": brief
                }
            )
            
        except Exception as e:
            self.handle_error(job_id, f"Script generation failed: {str(e)}")
    
    def _format_outline(self, outline: dict) -> str:
        """Format outline for prompt"""
        formatted = f"Introduction:\n{outline['introduction']}\n\n"
        
        for i, section in enumerate(outline['sections'], 1):
            formatted += f"Section {i}: {section.get('title', '')}\n"
            formatted += f"{section.get('content', '')}\n\n"
        
        formatted += f"Conclusion:\n{outline['conclusion']}"
        return formatted
    
    def _regenerate_with_corrections(self, script: str, corrections: list) -> str:
        """Regenerate script with fact corrections"""
        correction_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a fact-checking editor. Revise the script with the provided corrections while maintaining the flow and style."),
            ("human", """Original script:
            {script}
            
            Required corrections:
            {corrections}
            
            Revise the script with these corrections integrated naturally.""")
        ])
        
        response = self.llm.invoke(
            correction_prompt.format_prompt(
                script=script, 
                corrections="\n".join(corrections)
            ).to_messages()
        )
        return response.content
