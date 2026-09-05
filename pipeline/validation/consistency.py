import json
import os
from typing import Dict, Any, List, Optional
from schemas.validation import Anomaly
from pipeline.validation.anomaly_detector import AnomalyDetector

class ConsistencyChecker:
    def __init__(self, config_dir: str = None):
        if not config_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_dir = os.path.join(base_dir, "config", "validation")
            
        self.config_dir = config_dir
        self.tolerances = self._load_config("tolerances.json")

    def _load_config(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def check_invoice_math(self, subtotal: Optional[float], tax: Optional[float], total: Optional[float], items: Optional[List[Dict[str, Any]]] = None) -> List[Anomaly]:
        anomalies = []
        tol = self.tolerances.get("mathematical", {}).get("absolute_difference", 0.05)
        
        # Check subtotal + tax = total
        if subtotal is not None and tax is not None and total is not None:
            diff = abs((subtotal + tax) - total)
            if diff > tol:
                anomalies.append(AnomalyDetector.create_anomaly(
                    "MATHEMATICAL_MISMATCH",
                    "HIGH" if diff > 10.0 else "MEDIUM",
                    "total_amount",
                    f"Invoice math mismatch: Subtotal ({subtotal}) + Tax ({tax}) = {subtotal + tax}, but Total is {total}."
                ))
                
        # Check items total match subtotal/total
        if items and total is not None:
            items_sum = sum(item.get("quantity", 0.0) * item.get("unit_price", 0.0) for item in items if "unit_price" in item)
            # Only check if items actually had prices
            if items_sum > 0.0 and abs(items_sum - total) > tol:
                # Check subtotal instead of total
                if subtotal is not None and abs(items_sum - subtotal) > tol:
                    anomalies.append(AnomalyDetector.create_anomaly(
                        "MATHEMATICAL_MISMATCH",
                        "HIGH",
                        "subtotal",
                        f"Items total sum ({items_sum}) does not match subtotal ({subtotal})."
                    ))
        return anomalies

    def check_electricity_meter(self, prev_reading: Optional[float], curr_reading: Optional[float], consumption: Optional[float]) -> List[Anomaly]:
        anomalies = []
        if prev_reading is not None and curr_reading is not None:
            if curr_reading < prev_reading:
                anomalies.append(AnomalyDetector.create_anomaly(
                    "METER_CONSUMPTION_MISMATCH",
                    "CRITICAL",
                    "quantity",
                    f"Current meter reading ({curr_reading}) is less than previous reading ({prev_reading})."
                ))
            elif consumption is not None:
                expected = curr_reading - prev_reading
                if abs(expected - consumption) > 1.0:
                    anomalies.append(AnomalyDetector.create_anomaly(
                        "METER_CONSUMPTION_MISMATCH",
                        "HIGH",
                        "quantity",
                        f"Calculated consumption ({expected}) does not match billed consumption ({consumption})."
                    ))
        return anomalies

    def check_weight_quantity_consistency(self, qty: float, unit: str, weight: Optional[float], w_unit: Optional[str]) -> List[Anomaly]:
        anomalies = []
        if weight is not None and w_unit is not None:
            # Try to normalize/convert
            from pipeline.normalization import NormalizationEngine
            engine = NormalizationEngine()
            conv = engine.convert_unit(qty, unit, w_unit)
            if conv["status"] == "success":
                expected = conv["value"]
                if abs(expected - weight) > 0.1:
                    anomalies.append(AnomalyDetector.create_anomaly(
                        "WEIGHT_QUANTITY_MISMATCH",
                        "HIGH",
                        "quantity",
                        f"Quantity ({qty} {unit}) represents {expected} {w_unit}, but weight is declared as {weight} {w_unit}."
                    ))
        return anomalies
