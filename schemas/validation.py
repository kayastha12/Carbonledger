from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Anomaly(BaseModel):
    code: str  # e.g., VALUE_ANOMALY, UNIT_ANOMALY, FORMAT_ANOMALY, etc.
    severity: str  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    field: str
    message: str
    requires_review: bool = True

class FieldValidationResult(BaseModel):
    field: str
    raw_value: Optional[str] = None
    normalized_value: Optional[Any] = None
    validated_value: Optional[Any] = None
    unit: Optional[str] = None
    source: str
    confidence: float
    status: str  # VALID, VALID_WITH_WARNING, REVIEW_REQUIRED, INVALID

class ValidationResult(BaseModel):
    document_id: str
    document_type: str
    status: str  # VALID, VALID_WITH_WARNING, REVIEW_REQUIRED, INVALID
    overall_confidence: float
    confidence_level: str  # HIGH, MEDIUM, LOW
    confidence_components: Dict[str, float] = {}
    requires_review: bool = False
    field_results: List[FieldValidationResult] = []
    anomalies: List[Anomaly] = []
    warnings: List[str] = []
    errors: List[str] = []
    validated_at: str
