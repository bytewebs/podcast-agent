from agents.base_agent import BaseAgent
from google.cloud import texttospeech
from messaging.topics import KafkaTopics
from database.models import JobStatus
from storage.s3_client import S3Client
from utils.config import config
from pydub import AudioSegment
import tempfile
import os
import re
import logging

class TTSAgent(BaseAgent):
    """Agent responsible for converting scripts to audio using Google TTS"""
    
    # Google TTS has a 5000 byte limit, we use a slightly smaller limit for safety
    MAX_CHUNK_SIZE = 4800
    
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
            
            # Configure TTS settings
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
            
            # Generate audio (with chunking if necessary)
            final_audio_path = self._generate_chunked_audio(
                ssml_script, voice, audio_config, job_id
            )
            
            # Upload to S3
            s3_key = f"podcasts/{job_id}/audio.mp3"
            audio_url = self.s3_client.upload_file(final_audio_path, s3_key)
            
            # Clean up temp file
            os.unlink(final_audio_path)
            
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
    
    def _generate_chunked_audio(self, ssml_script: str, voice, audio_config, job_id: str) -> str:
        """Generate audio from SSML script, chunking if necessary"""
        # Check if chunking is needed
        script_bytes = ssml_script.encode('utf-8')
        
        if len(script_bytes) <= self.MAX_CHUNK_SIZE:
            # Single chunk - generate directly
            self.logger.info(f"Generating single audio chunk for job {job_id}")
            return self._generate_single_audio(ssml_script, voice, audio_config)
        
        # Multiple chunks needed
        self.logger.info(f"Script too long ({len(script_bytes)} bytes), chunking for job {job_id}")
        
        # Split into chunks
        chunks = self._split_ssml_into_chunks(ssml_script)
        self.logger.info(f"Split into {len(chunks)} chunks for job {job_id}")
        
        # Generate audio for each chunk
        audio_files = []
        try:
            for i, chunk in enumerate(chunks):
                self.logger.info(f"Generating chunk {i+1}/{len(chunks)} for job {job_id}")
                audio_file = self._generate_single_audio(chunk, voice, audio_config)
                audio_files.append(audio_file)
            
            # Merge all audio files
            merged_audio_path = self._merge_audio_files(audio_files, job_id)
            
            return merged_audio_path
            
        finally:
            # Clean up individual chunk files
            for audio_file in audio_files:
                try:
                    if os.path.exists(audio_file):
                        os.unlink(audio_file)
                except Exception as e:
                    self.logger.warning(f"Failed to clean up temp file {audio_file}: {e}")
    
    def _generate_single_audio(self, ssml_script: str, voice, audio_config) -> str:
        """Generate audio for a single SSML chunk"""
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_script)
        
        # Generate audio
        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(response.audio_content)
            return tmp_file.name
    
    def _split_ssml_into_chunks(self, ssml_script: str) -> list:
        """Split SSML script into chunks under the size limit"""
        chunks = []
        
        # Extract the content between <speak> tags
        speak_start = ssml_script.find('<speak>')
        speak_end = ssml_script.find('</speak>')
        
        if speak_start == -1 or speak_end == -1:
            # Fallback: treat as plain text
            return self._split_text_into_chunks(ssml_script)
        
        # Get the prefix, content, and suffix
        prefix = ssml_script[:speak_start + 7]  # Include <speak>
        content = ssml_script[speak_start + 7:speak_end]
        suffix = ssml_script[speak_end:]  # Include </speak>
        
        # Calculate overhead (prefix + suffix)
        overhead = len((prefix + suffix).encode('utf-8'))
        max_content_size = self.MAX_CHUNK_SIZE - overhead - 100  # Extra buffer
        
        if max_content_size <= 0:
            raise ValueError("SSML overhead too large for chunking")
        
        # Split content into chunks
        content_chunks = self._split_text_into_chunks(content, max_content_size)
        
        # Wrap each chunk with SSML tags
        for chunk in content_chunks:
            full_chunk = prefix + chunk + suffix
            chunk_bytes = full_chunk.encode('utf-8')
            
            if len(chunk_bytes) > self.MAX_CHUNK_SIZE:
                self.logger.warning(f"Chunk size {len(chunk_bytes)} exceeds limit {self.MAX_CHUNK_SIZE}")
            
            chunks.append(full_chunk)
        
        return chunks
    
    def _split_text_into_chunks(self, text: str, max_size: int = None) -> list:
        """Split text into chunks, preserving sentence boundaries"""
        if max_size is None:
            max_size = self.MAX_CHUNK_SIZE
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed the limit
            test_chunk = current_chunk + (" " if current_chunk else "") + sentence
            test_bytes = test_chunk.encode('utf-8')
            
            if len(test_bytes) <= max_size:
                # Sentence fits, add it
                current_chunk = test_chunk
            else:
                # Sentence doesn't fit
                if current_chunk:
                    # Save current chunk and start new one
                    chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split by words
                    word_chunks = self._split_sentence_by_words(sentence, max_size)
                    chunks.extend(word_chunks[:-1])  # Add all but last
                    current_chunk = word_chunks[-1] if word_chunks else ""
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_sentence_by_words(self, sentence: str, max_size: int) -> list:
        """Split a long sentence by words"""
        chunks = []
        current_chunk = ""
        words = sentence.split()
        
        for word in words:
            test_chunk = current_chunk + (" " if current_chunk else "") + word
            test_bytes = test_chunk.encode('utf-8')
            
            if len(test_bytes) <= max_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = word
                else:
                    # Single word is too long, split it (last resort)
                    chunks.extend(self._split_word_by_chars(word, max_size))
                    current_chunk = ""
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_word_by_chars(self, word: str, max_size: int) -> list:
        """Split a very long word by characters (last resort)"""
        chunks = []
        current_chunk = ""
        
        for char in word:
            test_chunk = current_chunk + char
            test_bytes = test_chunk.encode('utf-8')
            
            if len(test_bytes) <= max_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = char
                else:
                    # Even single character is too big (shouldn't happen with UTF-8)
                    raise ValueError(f"Single character too large for chunk size: {char}")
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _merge_audio_files(self, audio_files: list, job_id: str) -> str:
        """Merge multiple MP3 files into a single file"""
        if not audio_files:
            raise ValueError("No audio files to merge")
        
        if len(audio_files) == 1:
            # Only one file, just return it
            return audio_files[0]
        
        self.logger.info(f"Merging {len(audio_files)} audio files for job {job_id}")
        
        # Load first audio file
        merged_audio = AudioSegment.from_mp3(audio_files[0])
        
        # Append each subsequent file
        for audio_file in audio_files[1:]:
            audio_segment = AudioSegment.from_mp3(audio_file)
            merged_audio += audio_segment
        
        # Export merged audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            merged_audio.export(tmp_file.name, format="mp3")
            return tmp_file.name
    
    def _prepare_ssml(self, script: str) -> str:
        """Convert script to SSML format"""
        # Replace pause markers with SSML breaks
        ssml = script.replace("[pause]", '<break time="1s"/>')
        
        # Add emphasis markers
        ssml = re.sub(r'\*\*(.*?)\*\*', r'<emphasis level="strong">\1</emphasis>', ssml)
        
        # Wrap in SSML speak tag
        ssml = f'<speak>{ssml}</speak>'
        
        return ssml