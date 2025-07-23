import time
import logging
from functools import wraps
from typing import Callable, Any
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self._cache = {}
        self._cache_ttl = {}
    
    def cache_result(self, ttl: int = 300):
        """Cache function results with TTL"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
                current_time = time.time()
                
                # Check cache
                if (cache_key in self._cache and 
                    cache_key in self._cache_ttl and
                    current_time < self._cache_ttl[cache_key]):
                    return self._cache[cache_key]
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                self._cache[cache_key] = result
                self._cache_ttl[cache_key] = current_time + ttl
                
                return result
            return wrapper
        return decorator
    
    def async_execute(self, func: Callable, *args, **kwargs):
        """Execute function asynchronously"""
        return self.thread_pool.submit(func, *args, **kwargs)
    
    def batch_process(self, items: list, func: Callable, batch_size: int = 10):
        """Process items in batches"""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = [func(item) for item in batch]
            results.extend(batch_results)
        return results

# Global performance optimizer
performance = PerformanceOptimizer()