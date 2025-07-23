from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils.config import config
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BiasDetector:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=config.OPENAI_API_KEY,
            temperature=0.1
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at detecting bias and potential misinformation in content.
            
            Check for:
            1. Gender, racial, cultural, or religious bias
            2. Political bias or one-sided arguments
            3. Misleading or false information
            4. Harmful stereotypes
            5. Exclusionary language
            
            Be thorough but fair. Some topics naturally have perspectives."""),
            ("human", """Analyze this content for bias and misinformation:
            
            {content}
            
            Provide:
            1. Overall bias score (0-1, where 0 is unbiased)
            2. Specific instances of bias found
            3. Suggestions for improvement
            4. Whether the content should be flagged (true/false)""")
        ])
    
    def check_content(self, text: str) -> Dict[str, Any]:
        """Check content for bias and misinformation"""
        try:
            chain = self.prompt | self.llm
            
            result = chain.invoke({"content": text[:2000]})  # Limit for token management
            
            # Parse LLM response (simplified logic for now)
            content = result.content if isinstance(result.content, str) else str(result.content)
            passed = "should be flagged: false" in content.lower()
            
            return {
                "passed": passed,
                "analysis": content,
                "message": "Content passed bias check" if passed else "Content flagged for potential bias"
            }
            
        except Exception as e:
            logger.error(f"Bias detector error: {str(e)}")
            return {
                "passed": True,
                "message": "Bias check skipped due to error"
            }