# Anomaly Detection Service
import os
import joblib
import pandas as pd

class AnomalyService:
    def __init__(self, model_dir="d:/internship/carbonledger/models/saved_models/anomaly"):
        self.model_dir = model_dir
        self.iso_path = os.path.join(model_dir, "isolation_forest.pkl")
        self.clf_path = os.path.join(model_dir, "anomaly_classifier.pkl")
        
        self.iso_forest = None
        self.classifier = None
        
        if os.path.exists(self.iso_path) and os.path.exists(self.clf_path):
            try:
                self.iso_forest = joblib.load(self.iso_path)
                self.classifier = joblib.load(self.clf_path)
                print("Anomaly Detection models loaded successfully.")
            except Exception as e:
                print(f"Warning: Failed to load anomaly models ({e}). Using rule fallbacks.")
        else:
            print("Warning: Anomaly models not found. Using rule-based detection.")

    def detect_anomaly(self, expected_emission, actual_emission, record_id="N/A", extra_info=None):
        """
        Detect anomalies using isolation forest, random forest, and domain rules.
        """
        expected = float(expected_emission)
        actual = float(actual_emission)
        diff = actual - expected
        ratio = actual / (expected + 1e-5)
        
        is_anomaly = False
        confidence = 0.5
        method = "Rule-based Fallback"
        reason = "Emissions within normal variance."
        
        # 1. ML Model Predictions
        if self.iso_forest and self.classifier:
            try:
                X_features = pd.DataFrame([{
                    "ExpectedEmission": expected,
                    "ActualEmission": actual,
                    "diff_emission": diff,
                    "ratio_emission": ratio
                }])
                
                # Supervised classifier prediction
                pred_class = int(self.classifier.predict(X_features)[0])
                probs = self.classifier.predict_proba(X_features)[0]
                confidence = float(probs[pred_class])
                
                # Unsupervised isolation forest check
                iso_pred = int(self.iso_forest.predict(X_features)[0])
                
                if pred_class == 1 or iso_pred == -1:
                    is_anomaly = True
                    method = "Hybrid (RandomForest + Isolation Forest)"
                    reason = "Statistical anomaly detected in emissions value ratio/variance."
            except Exception as e:
                print(f"Anomaly model inference error: {e}")
                
        # 2. Domain Heuristics & Deterministic Rules (SRS requirements)
        # Check for wrong units (e.g. 1000x or 0.001x factor shift)
        if ratio > 900.0 or ratio < 0.0011:
            is_anomaly = True
            confidence = 0.99
            method = "Domain Rule (Wrong Units Check)"
            reason = "Suspicious scale shift detected. Unit of Measure (UoM) mismatch likely (e.g. kg vs tonnes)."
            
        # Check for duplicate invoices
        if extra_info and extra_info.get("is_duplicate_invoice"):
            is_anomaly = True
            confidence = 0.98
            method = "Domain Rule (Invoice Deduplication)"
            reason = "Duplicate invoice number or transaction pattern detected."
            
        # Check abnormal transport distance
        if extra_info and float(extra_info.get("distance", 0.0)) > 5000.0:
            is_anomaly = True
            confidence = 0.95
            method = "Domain Rule (Abnormal Transport)"
            reason = "Abnormally high logistics transport distance flagged (>5,000 km)."
            
        return {
            "record_id": record_id,
            "is_anomaly": is_anomaly,
            "confidence": round(confidence, 2),
            "method": method,
            "reason": reason,
            "expected_emission": round(expected, 1),
            "actual_emission": round(actual, 1),
            "difference": round(diff, 1),
            "ratio": round(ratio, 2)
        }

if __name__ == "__main__":
    detector = AnomalyService()
    res = detector.detect_anomaly(150.0, 150000.0, record_id="REC-908")
    print(res)
