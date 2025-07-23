from agents.base_agent import BaseAgent
from google.cloud import texttospeech
from messaging.topics import KafkaTopics
from database.models import JobStatus
from storage.s3_client import S3Client
from utils.config import config
import tempfile
import os
import re

class TTSAgent(BaseAgent):
    """Agent responsible for converting scripts to audio using Google TTS"""
    
    def __init__(self):
        super().__init__("tts")
        self.tts_client = texttospeech.TextToSpeechClient()
        self.s3_client = S3Client()
        
        # Available voices mapping
        self.voice_map = {
            "professional_male": {
                "language_code": "en-US",
                "name": "en-US-Neural2-D",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            "professional_female": {
                "language_code": "en-US",
                "name": "en-US-Neural2-F",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
            },
            "casual_male": {
                "language_code": "en-US",
                "name": "en-US-Neural2-J",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            "casual_female": {
                "language_code": "en-US",
                "name": "en-US-Neural2-C",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
            }
        }
    
    def process(self, message: dict):
        """Convert script to audio"""
        job_id = message["job_id"]
        script = message["script"]
        voice_preference = message.get("voice_preference", "professional_female")
        
        try:
            self.logger.info(f"Generating audio for job {job_id}")
            self.update_job_status(job_id, JobStatus.TTS_GENERATION.value)
            
            # Prepare script for TTS (convert to SSML)
            ssml_script = self._prepare_ssml(script)
            
            # Select voice
            voice_config = self.voice_map.get(voice_preference, self.voice_map["professional_female"])
            
            # Configure TTS request
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_script)
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config["language_code"],
                name=voice_config["name"],
                ssml_gender=voice_config["ssml_gender"]
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0,
                volume_gain_db=0.0
            )
            
            # Generate audio
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(response.audio_content)
                tmp_path = tmp_file.name
            
            # Upload to S3
            s3_key = f"podcasts/{job_id}/audio.mp3"
            audio_url = self.s3_client.upload_file(tmp_path, s3_key)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            # Update database
            self.repo.update_job(job_id, {"audio_url": audio_url})
            
            # Send to evaluation
            self.send_to_next_stage(
                KafkaTopics.TTS_EVALUATION,
                {
                    "job_id": job_id,
                    "audio_url": audio_url,
                    "script": script
                }
            )
            
        except Exception as e:
            self.handle_error(job_id, f"TTS generation failed: {str(e)}")
    
    def _prepare_ssml(self, script: str) -> str:
        """Convert script to SSML format"""
        # Replace pause markers with SSML breaks
        ssml = script.replace("[pause]", '<break time="1s"/>')
        
        # Add emphasis markers
        ssml = re.sub(r'\*\*(.*?)\*\*', r'<emphasis level="strong">\1</emphasis>', ssml)
        
        # Wrap in SSML speak tag
        ssml = f'<speak>{ssml}</speak>'
        
        return ssml
