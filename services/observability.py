import time
import json
import logging
from functools import wraps

logger = logging.getLogger("Observability")

class StructuredLogger:
    @staticmethod
    def log_event(event_name, status, duration_ms=0, metadata=None):
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_name,
            "status": status,
            "latency_ms": round(duration_ms, 2),
            "metadata": metadata or {}
        }
        logger.info(json.dumps(log_entry))

def track_latency(event_name):
    """
    Decorator to trace function/API execution time.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000.0
                StructuredLogger.log_event(event_name, "success", duration)
                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000.0
                StructuredLogger.log_event(event_name, f"failed: {str(e)}", duration)
                raise e
        return wrapper
    return decorator

# Setup basic Prometheus-like operational stats dictionary
metrics_registry = {
    "total_documents_processed": 0,
    "total_calculation_failures": 0,
    "average_inference_time_ms": 0.0
}

def increment_metric(name):
    if name in metrics_registry:
        metrics_registry[name] += 1

if __name__ == "__main__":
    @track_latency("test_calculation")
    def dummy_calc(x, y):
        time.sleep(0.05)
        return x + y
        
    dummy_calc(2, 3)
    increment_metric("total_documents_processed")
    print(metrics_registry)
