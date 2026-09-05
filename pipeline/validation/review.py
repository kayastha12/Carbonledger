from schemas.validation import ValidationResult
from schemas.review import HumanReviewItem, HumanCorrectionFeedback
from typing import List, Dict, Any, Optional

class ReviewQueue:
    def __init__(self):
        self.queue: List[HumanReviewItem] = []
        self.feedback_log: List[HumanCorrectionFeedback] = []

    def route_decision(self, validation_res: ValidationResult) -> str:
        """
        Determines the review status decision based on confidence and anomalies.
        """
        if any(a.severity == "CRITICAL" for a in validation_res.anomalies) or validation_res.status == "INVALID":
            return "INVALID"
            
        if validation_res.overall_confidence < 0.65 or validation_res.requires_review:
            return "REVIEW_REQUIRED"
            
        if any(a.severity in ["HIGH", "MEDIUM"] for a in validation_res.anomalies):
            return "REVIEW_REQUIRED"
            
        if any(a.severity == "LOW" for a in validation_res.anomalies):
            return "VALID_WITH_WARNING"
            
        return "VALID"

    def add_to_queue(self, review_item: HumanReviewItem):
        self.queue.append(review_item)

    def process_correction(self, review_id: str, corrected_value: Any, reviewer_reason: str, timestamp: str):
        for item in self.queue:
            if item.review_id == review_id:
                item.status = "CORRECTED"
                item.suggested_correction = corrected_value
                
                # Log feedback
                feedback = HumanCorrectionFeedback(
                    field=item.field,
                    original_value=item.raw_value,
                    corrected_value=corrected_value,
                    document_type=item.document_type,
                    reason=reviewer_reason,
                    timestamp=timestamp
                )
                self.feedback_log.append(feedback)
                break
