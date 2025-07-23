from transformers import pipeline
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Try importing torch, fallback to CPU if not available
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("torch is not installed. NSFWFilter will run on CPU only.")

class NSFWFilter:
    def __init__(self):
        # Use GPU if torch is available and CUDA is accessible
        device_id = 0 if HAS_TORCH and torch.cuda.is_available() else -1

        # Initialize pipeline
        try:
            self.classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=device_id
            )
            self.threshold = 0.7
        except Exception as e:
            logger.error(f"Failed to initialize NSFW filter: {str(e)}")
            self.classifier = None
            self.threshold = 0.7

    def check_content(self, text: str) -> Dict[str, Any]:
        """Check content for NSFW/inappropriate material"""
        if self.classifier is None:
            return {
                "passed": True,
                "score": 0,
                "message": "NSFW check skipped due to initialization error"
            }
            
        try:
            max_length = 512
            chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
            
            max_score = 0
            flagged_content = []

            for chunk in chunks:
                results = self.classifier(chunk)
                if results:
                    for result in results:
                        if result is not None and isinstance(result, dict):
                            if result.get('label') == 'TOXIC' and result.get('score', 0) > self.threshold:
                                max_score = max(max_score, result['score'])
                                flagged_content.append({
                                    "text": chunk[:100] + "...",
                                    "score": result['score']
                                })

            passed = max_score < self.threshold

            return {
                "passed": passed,
                "score": max_score,
                "flagged_content": flagged_content,
                "message": "Content passed NSFW check" if passed else "Content flagged for inappropriate material"
            }

        except Exception as e:
            logger.error(f"NSFW filter error: {str(e)}")
            return {
                "passed": True,
                "score": 0,
                "message": "NSFW check skipped due to error"
            }