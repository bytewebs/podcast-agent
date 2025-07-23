from typing import Dict, Any
import os
import json
from utils.config import config

class Settings:
    """Dynamic settings management"""
    
    def __init__(self):
        self._settings = self._load_default_settings()
        self._load_environment_overrides()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default settings"""
        return {
            "auto_approval": {
                "outline": True,
                "script": True,
                "audio": True
            },
            "quality_thresholds": {
                "outline_score": 0.7,
                "script_score": 0.75,
                "audio_score": 0.8
            },
            "retry_settings": {
                "max_retries": 3,
                "retry_delay": 60
            },
            "worker_settings": {
                "batch_size": 1,
                "timeout": 300
            }
        }
    
    def _load_environment_overrides(self):
        """Load settings from environment variables"""
        if os.getenv('SETTINGS_OVERRIDE'):
            try:
                overrides = json.loads(os.getenv('SETTINGS_OVERRIDE'))
                self._settings.update(overrides)
            except json.JSONDecodeError:
                pass
    
    def get(self, key: str, default=None):
        """Get setting value"""
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set setting value"""
        keys = key.split('.')
        setting = self._settings
        
        for k in keys[:-1]:
            if k not in setting:
                setting[k] = {}
            setting = setting[k]
        
        setting[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Get all settings as dictionary"""
        return self._settings.copy()

# Global settings instance
settings = Settings()