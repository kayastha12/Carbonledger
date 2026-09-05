import json
import os
import time
from typing import Dict, Any, List, Optional

class ValidationAuditor:
    def __init__(self, log_path: str = None):
        if not log_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            log_path = os.path.join(base_dir, "dataset", "validation_audit.jsonl")
            
        self.log_path = log_path

    def log_decision(
        self,
        document_id: str,
        field: str,
        raw_value: Optional[str],
        normalized_value: Any,
        validated_value: Any,
        rule: str,
        conf_before: float,
        conf_after: float,
        anomaly: Optional[str],
        decision: str,
        page: int = 1,
        bbox: Optional[List[float]] = None
    ):
        record = {
            "document_id": document_id,
            "page": page,
            "bbox": bbox or [0, 0, 0, 0],
            "field": field,
            "raw_value": raw_value,
            "normalized_value": normalized_value,
            "validated_value": validated_value,
            "validation_rule": rule,
            "confidence_before": conf_before,
            "confidence_after": conf_after,
            "anomaly": anomaly,
            "decision": decision,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Append-only log file write
        with open(self.log_path, "a") as f:
            f.write(json.dumps(record) + "\n")
