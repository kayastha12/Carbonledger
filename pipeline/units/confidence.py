from typing import Dict, Any

class UnitConfidenceScorer:
    CONFIDENCE_WEIGHTS = {
        "direct_text_match": 0.95,
        "table_header_match": 0.90,
        "key_value_match": 0.90,
        "nearby_context": 0.80,
        "document_expectation": 0.60,
        "inferred": 0.50
    }

    def calculate_score(self, source_type: str, matches_expectations: bool = True) -> float:
        score = self.CONFIDENCE_WEIGHTS.get(source_type, 0.50)
        if not matches_expectations:
            score -= 0.15
        return round(max(0.0, min(1.0, score)), 2)
