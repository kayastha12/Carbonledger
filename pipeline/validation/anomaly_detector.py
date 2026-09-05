from schemas.validation import Anomaly
from typing import Dict, Any, List

class AnomalyDetector:
    @staticmethod
    def create_anomaly(code: str, severity: str, field: str, message: str, requires_review: bool = True) -> Anomaly:
        return Anomaly(
            code=code,
            severity=severity,
            field=field,
            message=message,
            requires_review=requires_review
        )

    def detect_unit_anomalies(self, field: str, unit: str, raw_unit: str) -> List[Anomaly]:
        anomalies = []
        if not unit:
            anomalies.append(self.create_anomaly(
                "UNIT_MISSING",
                "HIGH",
                field,
                f"Unit is missing for field '{field}'. Please verify."
            ))
        elif raw_unit and unit != raw_unit:
            # Check if merged value token detected
            if any(char.isdigit() for char in raw_unit):
                anomalies.append(self.create_anomaly(
                    "UNIT_MERGED_TOKEN",
                    "MEDIUM",
                    field,
                    f"Unit token '{raw_unit}' contains merged numeric values."
                ))
            else:
                anomalies.append(self.create_anomaly(
                    "UNIT_OCR_CORRECTED",
                    "INFO",
                    field,
                    f"Unit '{raw_unit}' corrected contextually to '{unit}'.",
                    requires_review=False
                ))
        return anomalies

    def detect_ocr_anomalies(self, field: str, raw: str, norm: str) -> List[Anomaly]:
        anomalies = []
        if raw and norm and raw != norm:
            if "I" in raw or "l" in raw or "0" in raw or "O" in raw:
                anomalies.append(self.create_anomaly(
                    "OCR_CHARACTER_SWAP",
                    "INFO",
                    field,
                    f"Suspicious character swaps detected in raw value '{raw}' -> normalized to '{norm}'.",
                    requires_review=False
                ))
        return anomalies
