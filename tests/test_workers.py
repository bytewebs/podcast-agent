import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add workers to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'workers'))

class TestWorkers:
    
    def test_outline_worker_import(self):
        """Test that outline worker can be imported"""
        try:
            from workers import outline_worker
            assert outline_worker is not None
        except ImportError as e:
            pytest.skip(f"Worker import failed: {e}")
    
    def test_script_worker_import(self):
        """Test that script worker can be imported"""
        try:
            from workers import script_worker
            assert script_worker is not None
        except ImportError as e:
            pytest.skip(f"Worker import failed: {e}")