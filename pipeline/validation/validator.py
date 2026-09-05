import time
import re
from typing import Dict, Any, List
from schemas.extraction import ExtractionResult
from schemas.validation import ValidationResult, FieldValidationResult, Anomaly
from pipeline.validation.rules import RuleExecutor
from pipeline.validation.anomaly_detector import AnomalyDetector
from pipeline.validation.consistency import ConsistencyChecker
from pipeline.validation.confidence import ConfidenceScorer
from pipeline.validation.review import ReviewQueue
from pipeline.validation.audit import ValidationAuditor

class DocumentValidator:
    def __init__(self):
        self.rules = RuleExecutor()
        self.anomaly_detector = AnomalyDetector()
        self.consistency = ConsistencyChecker()
        self.scorer = ConfidenceScorer()
        self.review_queue = ReviewQueue()
        self.auditor = ValidationAuditor()
        
        # Unit Intelligence integration
        from pipeline.units.validator import UnitValidator as SystemUnitValidator
        from pipeline.units.detector import UnitDetector
        self.unit_val_eng = SystemUnitValidator()
        self.unit_det_eng = UnitDetector()

    def validate(self, ext_res: ExtractionResult) -> ValidationResult:
        anomalies = []
        warnings = []
        errors = []
        field_results = []
        
        doc_type = ext_res.document_type
        doc_id = ext_res.document_id
        
        # 1. Required Fields Check
        missing_fields = self.rules.check_required_fields(doc_type, ext_res.metadata, ext_res.items)
        for field in missing_fields:
            anomalies.append(self.anomaly_detector.create_anomaly(
                "MISSING_REQUIRED_FIELD",
                "CRITICAL",
                field,
                f"Required field '{field}' is missing for document type '{doc_type}'."
            ))
            errors.append(f"Missing required field: {field}")
            
        # 2. Field-Level Validation and Value Check
        qty_val = None
        qty_unit = None
        raw_qty = None
        
        qty_field = ext_res.metadata.get("quantity")
        if qty_field and qty_field.value is not None:
            raw_qty = str(qty_field.value)
            if isinstance(qty_field.normalized_value, dict):
                qty_val = float(qty_field.normalized_value.get("value", 0.0))
                qty_unit = qty_field.normalized_value.get("unit", "")
            else:
                from pipeline.normalization import NormalizationEngine
                qty_val, qty_unit, _ = NormalizationEngine().normalize_value(raw_qty)
                qty_val = float(qty_val) if qty_val is not None else 0.0
        elif ext_res.items:
            item_qty = ext_res.items[0].get("quantity")
            qty_val = float(item_qty) if item_qty is not None else None
            qty_unit = ext_res.items[0].get("unit") or ""
            raw_qty = str(qty_val) if qty_val is not None else None
            
        # Detect and handle merged tokens (e.g. "mt21250" or "kg 25000")
        if raw_qty:
            split_val, split_unit = self.unit_det_eng.split_merged_token(raw_qty)
            if split_val is not None:
                qty_val = split_val
                qty_unit = split_unit
                    
        # Plausibility range check
        if qty_val is not None:
            # Check ranges
            range_status = self.rules.check_range("quantity", qty_val)
            if range_status == "INVALID":
                anomalies.append(self.anomaly_detector.create_anomaly(
                    "VALUE_ANOMALY",
                    "CRITICAL",
                    "quantity",
                    f"Quantity value {qty_val} is physically invalid."
                ))
                errors.append("Invalid range: quantity")
            elif range_status == "UNUSUAL":
                anomalies.append(self.anomaly_detector.create_anomaly(
                    "RANGE_WARNING",
                    "LOW",
                    "quantity",
                    f"Quantity value {qty_val} is unusually large.",
                    requires_review=False
                ))
                warnings.append("Unusual quantity detected")

        # 3. Unit Validation (highest priority)
        if qty_unit:
            unit_anoms = self.anomaly_detector.detect_unit_anomalies("quantity", qty_unit, qty_unit)
            anomalies.extend(unit_anoms)
            
            # Check document unit compatibility
            if not self.unit_val_eng.is_compatible(doc_type, "quantity", qty_unit):
                anomalies.append(self.anomaly_detector.create_anomaly(
                    "INCOMPATIBLE_UNIT",
                    "CRITICAL",
                    "quantity",
                    f"Unit '{qty_unit}' is incompatible with document type '{doc_type}'."
                ))
                errors.append("Incompatible unit detected")
        else:
            anomalies.append(self.anomaly_detector.create_anomaly(
                "UNIT_MISSING",
                "HIGH",
                "quantity",
                "Unit is missing for quantity. Human review recommended."
            ))
            
        # 4. Cross-Field Consistency Check
        if doc_type == "PURCHASE_INVOICE":
            # Math subtotal check
            subtotal = ext_res.financial.subtotal if ext_res.financial else None
            tax = ext_res.financial.tax if ext_res.financial else None
            total = ext_res.financial.total_amount if ext_res.financial else None
            math_anoms = self.consistency.check_invoice_math(subtotal, tax, total, ext_res.items)
            anomalies.extend(math_anoms)
            
        # 5. Scorer and Confidence Level Mapping
        # Build score metrics based on anomalies
        ext_score = 0.95
        norm_score = 0.95
        unit_score = 0.95 if qty_unit else 0.50
        const_score = 0.95
        val_score = 0.95
        src_score = 0.95
        
        penalties = []
        if any(a.code == "MISSING_REQUIRED_FIELD" for a in anomalies):
            penalties.append(0.30)
        if any(a.code == "UNIT_MISSING" for a in anomalies):
            penalties.append(0.25)
            unit_score = 0.30
        if any(a.code == "MATHEMATICAL_MISMATCH" for a in anomalies):
            penalties.append(0.20)
            const_score = 0.40
            
        conf_res = self.scorer.calculate_confidence(
            ext_score, norm_score, unit_score, const_score, val_score, src_score, penalties
        )
        
        # Build validation decision routing
        overall_status = "VALID"
        requires_review = False
        
        if any(a.requires_review for a in anomalies):
            requires_review = True
            
        if errors or any(a.severity == "CRITICAL" for a in anomalies):
            overall_status = "INVALID"
        elif any(a.severity in ["HIGH", "MEDIUM"] for a in anomalies) or conf_res["confidence_level"] in ["MEDIUM", "LOW"] or requires_review:
            overall_status = "REVIEW_REQUIRED"
            requires_review = True
        elif warnings or any(a.severity == "LOW" for a in anomalies):
            overall_status = "VALID_WITH_WARNING"
            
        val_result = ValidationResult(
            document_id=doc_id,
            document_type=doc_type,
            status=overall_status,
            overall_confidence=conf_res["overall_confidence"],
            confidence_level=conf_res["confidence_level"],
            confidence_components=conf_res["components"],
            requires_review=requires_review,
            field_results=field_results,
            anomalies=anomalies,
            warnings=warnings,
            errors=errors,
            validated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        
        # Log audit trail
        self.auditor.log_decision(
            doc_id,
            "quantity",
            raw_qty,
            qty_val,
            qty_val,
            "RANGE_AND_UNIT_CHECK",
            0.95,
            conf_res["overall_confidence"],
            anomalies[0].code if anomalies else None,
            overall_status
        )
        
        return val_result
