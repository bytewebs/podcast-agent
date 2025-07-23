import logging
import sys
from typing import Optional

def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """Set up logger with consistent formatting"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

logger = setup_logger(__name__)