import logging
import time
from functools import wraps
from typing import Callable, Any, Dict
from datetime import datetime, timezone
import threading
from collections import defaultdict

class MetricsCollector:
    """Simple metrics collection for monitoring"""
    
    def __init__(self):
        self.metrics = defaultdict(int)
        self.durations = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
    
    def increment_counter(self, metric_name: str, labels: dict = None):
        """Increment a counter metric"""
        key = f"{metric_name}_{str(labels or {})}"
        with self._lock:
            self.metrics[key] += 1
        self.logger.info(f"Metric {metric_name}: {self.metrics[key]}")
    
    def record_duration(self, metric_name: str, duration: float, labels: dict = None):
        """Record a duration metric"""
        key = f"{metric_name}_duration_{str(labels or {})}"
        with self._lock:
            self.durations[key].append(duration)
            # Keep only last 100 measurements
            if len(self.durations[key]) > 100:
                self.durations[key] = self.durations[key][-100:]
        self.logger.info(f"Duration {metric_name}: {duration:.2f}s")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        with self._lock:
            result = dict(self.metrics)
            # Add duration statistics
            for key, values in self.durations.items():
                if values:
                    result[f"{key}_avg"] = sum(values) / len(values)
                    result[f"{key}_max"] = max(values)
                    result[f"{key}_min"] = min(values)
            return result

    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self.metrics.clear()
            self.durations.clear()

# Global metrics collector
metrics = MetricsCollector()

def monitor_performance(metric_name: str):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                metrics.increment_counter(f"{metric_name}_success")
                return result
            except Exception as e:
                metrics.increment_counter(f"{metric_name}_error")
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_duration(metric_name, duration)
        return wrapper
    return decorator

class SystemMonitor:
    """System monitoring utilities"""
    
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get basic system statistics"""
        return {
            "uptime_seconds": self.get_uptime(),
            "metrics": metrics.get_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global system monitor
system_monitor = SystemMonitor()