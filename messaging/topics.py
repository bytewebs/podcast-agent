class KafkaTopics:
    # Generation topics
    OUTLINE_GENERATION = "podcast.outline.generation"
    SCRIPT_GENERATION = "podcast.script.generation"
    TTS_GENERATION = "podcast.tts.generation"
    PUBLISHING = "podcast.publishing"
    
    # Evaluation topics
    OUTLINE_EVALUATION = "podcast.outline.evaluation"
    SCRIPT_EVALUATION = "podcast.script.evaluation"
    TTS_EVALUATION = "podcast.tts.evaluation"
    
    # Guardrails topics
    OUTLINE_GUARDRAILS = "podcast.outline.guardrails"
    SCRIPT_GUARDRAILS = "podcast.script.guardrails"
    
    # Approval topics
    OUTLINE_APPROVAL = "podcast.outline.approval"
    SCRIPT_APPROVAL = "podcast.script.approval"
    AUDIO_APPROVAL = "podcast.audio.approval"
    
    # Control topics
    SUPERVISOR_CONTROL = "podcast.supervisor.control"
    JOB_STATUS = "podcast.job.status"
    
    # Error handling
    DLQ = "podcast.dlq"
    
    @classmethod
    def get_all_topics(cls) -> list:
        """Get list of all topics"""
        return [
            cls.OUTLINE_GENERATION,
            cls.SCRIPT_GENERATION,
            cls.TTS_GENERATION,
            cls.PUBLISHING,
            cls.OUTLINE_EVALUATION,
            cls.SCRIPT_EVALUATION,
            cls.TTS_EVALUATION,
            cls.OUTLINE_GUARDRAILS,
            cls.SCRIPT_GUARDRAILS,
            cls.OUTLINE_APPROVAL,
            cls.SCRIPT_APPROVAL,
            cls.AUDIO_APPROVAL,
            cls.SUPERVISOR_CONTROL,
            cls.JOB_STATUS,
            cls.DLQ
        ]