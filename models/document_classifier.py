import os
import torch
import json
import time
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class DocumentClassifier:
    def __init__(self, model_dir="d:/internship/carbonledger/models/fine_tuned/document_classifier"):
        self.model_dir = model_dir
        self.fallback_dir = "d:/internship/carbonledger/models/saved_models/distilbert"
        self.pretrained_cache_dir = "d:/internship/carbonledger/models/pretrained/distilbert-base-uncased"
        
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.tokenizer = None
        self.model = None
        self.label_map = {}
        self.inv_label_map = {}
        
        # Determine which path to load from
        target_path = None
        if os.path.exists(os.path.join(self.model_dir, "model.safetensors")) or os.path.exists(os.path.join(self.model_dir, "pytorch_model.bin")):
            target_path = self.model_dir
        elif os.path.exists(os.path.join(self.fallback_dir, "model.safetensors")) or os.path.exists(os.path.join(self.fallback_dir, "pytorch_model.bin")):
            target_path = self.fallback_dir
            
        if target_path:
            label_map_path = os.path.join(target_path, "label_map.json")
            if os.path.exists(label_map_path):
                with open(label_map_path, "r") as f:
                    self.label_map = json.load(f)
                self.inv_label_map = {v: k for k, v in self.label_map.items()}
            
            print(f"Loading DocumentClassifier from: {target_path} on {self.device}")
            self.tokenizer = AutoTokenizer.from_pretrained(target_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(target_path)
            self.model.to(self.device)
            self.model.eval()
        else:
            print("Fine-tuned or saved classifier models not found. Auto-downloading/caching distilbert-base-uncased...")
            os.makedirs(self.pretrained_cache_dir, exist_ok=True)
            self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased", cache_dir=self.pretrained_cache_dir)
            # We map some default categories for initialization
            self.label_map = {
                "Invoice": 0, "Purchase Order": 1, "Packing List": 2, "Bill of Lading": 3,
                "Electricity Bill": 4, "Water Bill": 5, "Fuel Receipt": 6, "ERP Export": 7, "Supplier Sheet": 8
            }
            self.inv_label_map = {v: k for k, v in self.label_map.items()}
            self.model = AutoModelForSequenceClassification.from_pretrained(
                "distilbert-base-uncased", 
                num_labels=len(self.label_map),
                cache_dir=self.pretrained_cache_dir
            )
            self.model.to(self.device)
            self.model.eval()

    def classify_with_details(self, ocr_text):
        if not self.tokenizer or not self.model:
            return {"document_type": "Other", "confidence": 0.5, "inference_time_ms": 0.0}
            
        t_start = time.perf_counter()
        with torch.no_grad():
            inputs = self.tokenizer(ocr_text, truncation=True, padding=True, max_length=128, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            pred_idx = torch.argmax(probs, dim=1).item()
            confidence = float(probs[0][pred_idx].item())
            raw_pred = self.inv_label_map.get(pred_idx, "Other")
            
        # Map raw generator categories to the target SRS classes
        mapping = {
            "Invoice": "Invoice",
            "Purchase Order": "Purchase Order",
            "Packing List": "Shipping Manifest",
            "Bill of Lading": "Shipping Manifest",
            "Electricity Bill": "Utility Bill",
            "Water Bill": "Utility Bill",
            "Fuel Receipt": "Utility Bill",
            "ERP Export": "ERP Export",
            "Supplier Sheet": "Supplier Sheet"
        }
        
        mapped_pred = mapping.get(raw_pred, "Other")
        latency = (time.perf_counter() - t_start) * 1000.0
        
        return {
            "document_type": mapped_pred,
            "confidence": confidence,
            "inference_time_ms": round(latency, 2)
        }

    def classify(self, ocr_text):
        res = self.classify_with_details(ocr_text)
        return res["document_type"]

if __name__ == "__main__":
    classifier = DocumentClassifier()
    sample_text = "INVOICE #INV-2026-9872. Supplier: SteelCorp. Item: Steel Sheet. Quantity: 50 tonnes."
    res = classifier.classify_with_details(sample_text)
    print(f"Classification result: {res}")

