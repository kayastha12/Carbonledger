from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class HumanReviewItem(BaseModel):
    review_id: str
    document_id: str
    document_type: str
    field: str
    raw_value: Optional[str] = None
    current_value: Optional[Any] = None
    candidate_values: List[Any] = []
    reason: str
    severity: str  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    confidence: float
    page: int
    bbox: Optional[List[float]] = None
    suggested_correction: Optional[Any] = None
    status: str = "PENDING"  # PENDING, APPROVED, CORRECTED, REJECTED

class HumanCorrectionFeedback(BaseModel):
    field: str
    original_value: Optional[str] = None
    corrected_value: Any
    document_type: str
    reason: str
    timestamp: str
