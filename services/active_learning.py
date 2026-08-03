import os
import json
import time

class ActiveLearningService:
    def __init__(self, feedback_dir="d:/internship/carbonledger/services/active_learning"):
        self.feedback_dir = feedback_dir
        self.feedback_file = os.path.join(self.feedback_dir, "user_feedback_log.json")
        os.makedirs(self.feedback_dir, exist_ok=True)

    def log_feedback(self, raw_input, original_prediction, user_correction, field_type):
        """
        Logs user corrections for active learning pipelines.
        Field Types: 'document_class', 'supplier_match', 'emission_factor', 'calculation'
        """
        log_entry = {
            "timestamp": time.time(),
            "field_type": field_type,
            "raw_input": raw_input,
            "system_prediction": original_prediction,
            "user_correction": user_correction
        }
        
        logs = []
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, "r") as f:
                    logs = json.load(f)
            except Exception:
                pass
                
        logs.append(log_entry)
        
        with open(self.feedback_file, "w") as f:
            json.dump(logs, f, indent=2)
            
        print(f"Logged active learning correction for field '{field_type}'.")
        return {"status": "success", "logged_entry": log_entry}

    def compile_retraining_dataset(self, field_type):
        """
        Aggregates logged overrides and exports them as training pairs.
        """
        if not os.path.exists(self.feedback_file):
            return []
            
        with open(self.feedback_file, "r") as f:
            logs = json.load(f)
            
        filtered_logs = [l for l in logs if l["field_type"] == field_type]
        
        training_pairs = []
        for l in filtered_logs:
            training_pairs.append({
                "text": l["raw_input"],
                "label": l["user_correction"]
            })
            
        # Export file
        retrain_path = os.path.join(self.feedback_dir, f"retrain_{field_type}.json")
        with open(retrain_path, "w") as f:
            json.dump(training_pairs, f, indent=2)
            
        print(f"Compiled retraining dataset for {field_type} with {len(training_pairs)} pairs.")
        return training_pairs

if __name__ == "__main__":
    al = ActiveLearningService()
    al.log_feedback("INV-9872", "Utility Bill", "Invoice", "document_class")
    al.compile_retraining_dataset("document_class")
