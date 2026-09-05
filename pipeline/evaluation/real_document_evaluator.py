import os
import json
from typing import Dict, Any, List

class RealDocumentEvaluator:
    def __init__(self, ground_truth_dir: str, outputs_dir: str):
        self.ground_truth_dir = ground_truth_dir
        self.outputs_dir = outputs_dir

    def evaluate(self) -> Dict[str, Any]:
        """
        Runs evaluation of AI extraction against Human Ground Truth
        """
        metrics = {
            "evaluated_documents": 0,
            "evaluated_segments": 0,
            "total_fields": 0,
            "correct_fields": 0,
            "field_accuracy": 0.0,
            "unit_accuracy": 0.0,
            "material_accuracy": 0.0,
            "quantity_accuracy": 0.0,
            "supplier_accuracy": 0.0,
            "classification_accuracy": 0.0,
            "errors": []
        }

        if not os.path.exists(self.ground_truth_dir):
            return metrics

        # Discover parent documents in ground truth
        doc_dirs = [d for d in os.listdir(self.ground_truth_dir) if os.path.isdir(os.path.join(self.ground_truth_dir, d))]
        metrics["evaluated_documents"] = len(doc_dirs)

        total_units = 0
        correct_units = 0
        total_materials = 0
        correct_materials = 0
        total_quantities = 0
        correct_quantities = 0
        total_suppliers = 0
        correct_suppliers = 0
        total_classifications = 0
        correct_classifications = 0

        for doc_id in doc_dirs:
            gt_doc_dir = os.path.join(self.ground_truth_dir, doc_id)
            seg_files = [f for f in os.listdir(gt_doc_dir) if f.endswith(".json")]

            for seg_file in seg_files:
                seg_id_only = os.path.splitext(seg_file)[0] # e.g. SEG_001
                metrics["evaluated_segments"] += 1

                # Load Ground Truth
                with open(os.path.join(gt_doc_dir, seg_file), "r") as f:
                    gt_data = json.load(f)

                # Load AI Extraction
                ai_path = os.path.join(self.outputs_dir, doc_id, "segments", f"{doc_id}_{seg_id_only}", "activity_record.json")
                if not os.path.exists(ai_path):
                    continue

                with open(ai_path, "r") as f:
                    ai_data = json.load(f)

                # Compare fields
                gt_fields = gt_data.get("fields", {})
                ai_fields = ai_data.get("activity", {})

                # Check classification
                total_classifications += 1
                if gt_data.get("document_type") == ai_data.get("document_type"):
                    correct_classifications += 1
                    metrics["correct_fields"] += 1
                metrics["total_fields"] += 1

                for field, gt_val in gt_fields.items():
                    ai_val = ai_fields.get(field)
                    metrics["total_fields"] += 1

                    is_correct = str(gt_val).strip().lower() == str(ai_val).strip().lower()
                    if is_correct:
                        metrics["correct_fields"] += 1
                    else:
                        metrics["errors"].append({
                            "segment_id": f"{doc_id}_{seg_id_only}",
                            "field": field,
                            "ai_value": ai_val,
                            "gt_value": gt_val,
                            "error_type": "VALUE_MISMATCH"
                        })

                    # Track component metrics
                    if field == "unit":
                        total_units += 1
                        if is_correct: correct_units += 1
                    elif field == "material":
                        total_materials += 1
                        if is_correct: correct_materials += 1
                    elif field == "quantity":
                        total_quantities += 1
                        if is_correct: correct_quantities += 1
                    elif field == "supplier":
                        total_suppliers += 1
                        if is_correct: correct_suppliers += 1

        # Calculate percentages
        if metrics["total_fields"] > 0:
            metrics["field_accuracy"] = round((metrics["correct_fields"] / metrics["total_fields"]) * 100, 2)
        if total_units > 0:
            metrics["unit_accuracy"] = round((correct_units / total_units) * 100, 2)
        if total_materials > 0:
            metrics["material_accuracy"] = round((correct_materials / total_materials) * 100, 2)
        if total_quantities > 0:
            metrics["quantity_accuracy"] = round((correct_quantities / total_quantities) * 100, 2)
        if total_suppliers > 0:
            metrics["supplier_accuracy"] = round((correct_suppliers / total_suppliers) * 100, 2)
        if total_classifications > 0:
            metrics["classification_accuracy"] = round((correct_classifications / total_classifications) * 100, 2)

        return metrics
