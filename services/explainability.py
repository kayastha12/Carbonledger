class ExplainabilityService:
    @staticmethod
    def explain_matching(query_text, matched_candidate, alternative_candidates):
        """
        Explains semantic emission factor matching scores and ranking.
        """
        explanation = {
            "query": query_text,
            "selected_factor": {
                "id": matched_candidate.get("id"),
                "scope": matched_candidate.get("scope"),
                "category": matched_candidate.get("category"),
                "subcategory": matched_candidate.get("subcategory"),
                "activity": matched_candidate.get("activity"),
                "text": matched_candidate.get("text"),
                "factor_value": matched_candidate.get("factor"),
                "confidence_score": matched_candidate.get("confidence")
            },
            "embedding_similarity": f"{matched_candidate.get('confidence', 0.0):.2%}",
            "reasoning": f"Standardized activity '{matched_candidate.get('activity')}' matches input description '{query_text}' with high semantic similarity. Chosen factor value is {matched_candidate.get('factor')} per {matched_candidate.get('uom')}.",
            "alternatives": [
                {
                    "id": c.get("id"),
                    "category": c.get("category"),
                    "activity": c.get("activity"),
                    "factor": c.get("factor"),
                    "similarity": f"{c.get('confidence', 0.0):.2%}"
                } for c in alternative_candidates if c.get("id") != matched_candidate.get("id")
            ],
            "audit_trail": {
                "source_sheet": matched_candidate.get("source_sheet"),
                "factor_version": matched_candidate.get("factor_version"),
                "formula": "emissions_kg = activity_value * conversion_factor"
            }
        }
        return explanation

    @staticmethod
    def explain_anomaly(record_id, is_anomaly, score, expected, actual, root_cause="N/A"):
        """
        Explains outputs from isolation forest or supervised classifiers.
        """
        diff = actual - expected
        ratio = actual / (expected + 1e-5)
        return {
            "record_id": record_id,
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": float(score),
            "features": {
                "expected_emission": expected,
                "actual_emission": actual,
                "emission_difference": diff,
                "emission_ratio": ratio
            },
            "explanation": f"Isolation Forest flagged this transaction as anomalous due to the actual emissions ({actual:.1f} kg) violating normal variance thresholds (Ratio: {ratio:.1f}x higher than expected). Cause: {root_cause}."
        }
