class PodcastGenerationError(Exception):
    """Base exception for podcast generation system"""
    pass

class OutlineGenerationError(PodcastGenerationError):
    """Error during outline generation"""
    pass

class ScriptGenerationError(PodcastGenerationError):
    """Error during script generation"""
    pass

class TTSGenerationError(PodcastGenerationError):
    """Error during TTS generation"""
    pass

class PublishingError(PodcastGenerationError):
    """Error during publishing"""
    pass

class EvaluationError(PodcastGenerationError):
    """Error during evaluation"""
    pass

class GuardrailError(PodcastGenerationError):
    """Error during guardrail checks"""
    pass

class JobNotFoundError(PodcastGenerationError):
    """Job not found in database"""
    pass

class InvalidJobStateError(PodcastGenerationError):
    """Job is in invalid state for operation"""
    pass