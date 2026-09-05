import json
import os
from typing import Dict, Any, List, Optional
from pipeline.units.normalizer import UnitNormalizer
from schemas.validation import Anomaly

class UnitValidator:
    def __init__(self, config_dir: str = None):
        if not config_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_dir = os.path.join(base_dir, "config", "validation")
            
        self.config_dir = config_dir
        self.expectations = self._load_config("unit_expectations.json")
        self.normalizer = UnitNormalizer()

    def _load_config(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def is_compatible(self, doc_type: str, field_name: str, unit: str) -> bool:
        expected = self.expectations.get(doc_type, {}).get(field_name, [])
        if not expected:
            return True
            
        norm = self.normalizer.normalize(unit)
        if not norm:
            return False
            
        # Check compatibility via dimension matching
        for exp in expected:
            norm_exp = self.normalizer.normalize(exp)
            if norm_exp and self.normalizer.get_dimension(norm) == self.normalizer.get_dimension(norm_exp):
                return True
        return False

    def detect_conflicts(self, units_list: List[Dict[str, Any]]) -> List[Anomaly]:
        """
        Detects conflicting unit definitions across raw fields.
        """
        anomalies = []
        if len(units_list) < 2:
            return anomalies
            
        base_unit = units_list[0].get("unit")
        base_val = units_list[0].get("value")
        
        for item in units_list[1:]:
            curr_unit = item.get("unit")
            curr_val = item.get("value")
            
            # Check dimension mapping compatibility
            conv = self.normalizer.convert(curr_val, curr_unit, base_unit)
            if conv["status"] == "error":
                anomalies.append(Anomaly(
                    code="UNIT_CONFLICT",
                    severity="HIGH",
                    field=item.get("field", "quantity"),
                    message=f"Unit conflict detected: incompatible units {curr_unit} vs {base_unit}."
                ))
            elif abs(conv["value"] - base_val) > 1.0:
                anomalies.append(Anomaly(
                    code="UNIT_VALUE_CONFLICT",
                    severity="HIGH",
                    field=item.get("field", "quantity"),
                    message=f"Value conflict under unit normalization: {curr_val} {curr_unit} converts to {conv['value']} {base_unit}, but base value is {base_val}."
                ))
        return anomalies
