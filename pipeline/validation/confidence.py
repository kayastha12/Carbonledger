import json
import os
from typing import Dict, Any, List

class ConfidenceScorer:
    def __init__(self, config_dir: str = None):
        if not config_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_dir = os.path.join(base_dir, "config", "validation")
            
        self.config_dir = config_dir
        config = self._load_config("confidence_weights.json")
        self.weights = config.get("weights", {
            "extraction": 0.30,
            "normalization": 0.15,
            "unit": 0.20,
            "consistency": 0.15,
            "validation": 0.15,
            "source": 0.05
        })
        self.thresholds = config.get("thresholds", {
            "high": 0.85,
            "medium": 0.65
        })

    def _load_config(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def calculate_confidence(
        self,
        extraction_score: float,
        normalization_score: float,
        unit_score: float,
        consistency_score: float,
        validation_score: float,
        source_score: float,
        penalties: List[float] = []
    ) -> Dict[str, Any]:
        """
        Calculates overall explainable confidence.
        """
        w = self.weights
        overall = (
            extraction_score * w.get("extraction", 0.30) +
            normalization_score * w.get("normalization", 0.15) +
            unit_score * w.get("unit", 0.20) +
            consistency_score * w.get("consistency", 0.15) +
            validation_score * w.get("validation", 0.15) +
            source_score * w.get("source", 0.05)
        )
        
        # Apply penalties (subtraction)
        for penalty in penalties:
            overall -= penalty
            
        overall = max(0.0, min(1.0, overall))
        overall = round(overall, 2)
        
        # Categorize
        if overall >= self.thresholds.get("high", 0.85):
            level = "HIGH"
        elif overall >= self.thresholds.get("medium", 0.65):
            level = "MEDIUM"
        else:
            level = "LOW"
            
        return {
            "overall_confidence": round(overall, 2),
            "confidence_level": level,
            "components": {
                "extraction": round(extraction_score, 2),
                "normalization": round(normalization_score, 2),
                "unit": round(unit_score, 2),
                "consistency": round(consistency_score, 2),
                "validation": round(validation_score, 2),
                "source": round(source_score, 2)
            }
        }
