import re
from typing import Dict, Any

class SpeechPatternAnalyzer:
    def __init__(self):
        self.problematic_patterns = [
            r'\b(um|uh|er|ah)\b',  # Filler words
            r'([.!?])\1+',  # Multiple punctuation
            r'\b(\w+)\s+\1\b',  # Repeated words
            r'[^\w\s,.!?-]',  # Unusual characters
        ]
    
    def analyze_audio_script(self, script: str) -> Dict[str, Any]:
        """Analyze script for speech pattern issues"""
        issues = []
        
        # Check for filler words
        filler_matches = re.findall(self.problematic_patterns[0], script, re.IGNORECASE)
        if len(filler_matches) > 10:
            issues.append(f"High frequency of filler words: {len(filler_matches)} instances")
        
        # Check for repeated punctuation
        punct_matches = re.findall(self.problematic_patterns[1], script)
        if punct_matches:
            issues.append(f"Repeated punctuation found: {len(punct_matches)} instances")
        
        # Check for repeated words
        repeat_matches = re.findall(self.problematic_patterns[2], script, re.IGNORECASE)
        if repeat_matches:
            issues.append(f"Repeated words found: {len(repeat_matches)} instances")
        
        # Check script length vs expected duration
        words = len(script.split())
        expected_words = 150 * 10  # ~150 words per minute
        if abs(words - expected_words) > expected_words * 0.2:
            issues.append(f"Script length mismatch: {words} words vs {expected_words} expected")
        
        passed = len(issues) == 0
        
        return {
            "passed": passed,
            "issues": issues,
            "word_count": words,
            "message": "Speech patterns acceptable" if passed else "Speech pattern issues detected"
        }
