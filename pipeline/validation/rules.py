import json
import os
from typing import Dict, Any, List, Optional

class RuleExecutor:
    def __init__(self, config_dir: str = None):
        if not config_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_dir = os.path.join(base_dir, "config", "validation")
            
        self.config_dir = config_dir
        self.required_fields = self._load_config("required_fields.json")
        self.plausibility_ranges = self._load_config("plausibility_ranges.json")

    def _load_config(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def check_required_fields(self, doc_type: str, extracted_metadata: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        missing = []
        required = self.required_fields.get(doc_type, [])
        
        for field in required:
            # Check metadata first
            meta_field = extracted_metadata.get(field)
            has_val = meta_field is not None and getattr(meta_field, "value", None) is not None
            
            # Check items list if not in metadata
            if not has_val and items:
                has_val = any(item.get(field) is not None for item in items)
                
            if not has_val:
                missing.append(field)
        return missing

    def check_range(self, field_name: str, val: float) -> str:
        """Returns NORMAL, UNUSUAL, or INVALID based on configured ranges"""
        rules = self.plausibility_ranges.get(field_name)
        if not rules:
            return "NORMAL"
            
        minimum = rules.get("minimum", 0.0)
        maximum = rules.get("maximum", 1000000.0)
        
        if val < minimum:
            return "INVALID"
            
        # If value is extremely large, treat as UNUSUAL
        if val > (maximum * 0.8):
            return "UNUSUAL"
            
        return "NORMAL"
