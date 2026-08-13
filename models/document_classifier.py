import os
import torch
import json
import time
from typing import Dict, Any
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class DocumentClassifier:
    """
    Fine-tuned Sequence Classifier for Sustainability & ERP Documents.
    Uses dynamic path resolution with high-precision keyword overrides when un-fine-tuned.
    """
    def __init__(self, model_dir: str = None):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_dir = model_dir or os.path.join(project_root, "models", "fine_tuned", "document_classifier")
        self.fallback_dir = os.path.join(project_root, "models", "saved_models", "distilbert")
        self.pretrained_cache_dir = os.path.join(project_root, "models", "pretrained", "distilbert-base-uncased")
        
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.tokenizer = None
        self.model = None
        self.label_map = {}
        self.inv_label_map = {}
        self.is_fine_tuned = False
        
        target_path = None
        if os.path.exists(os.path.join(self.model_dir, "model.safetensors")) or os.path.exists(os.path.join(self.model_dir, "pytorch_model.bin")):
            target_path = self.model_dir
            self.is_fine_tuned = True
        elif os.path.exists(os.path.join(self.fallback_dir, "model.safetensors")) or os.path.exists(os.path.join(self.fallback_dir, "pytorch_model.bin")):
            target_path = self.fallback_dir
            self.is_fine_tuned = True
            
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

    def classify_with_details(self, ocr_text: str) -> Dict[str, Any]:
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
            
        mapping = {
            "Invoice": "Invoice",
            "Purchase Order": "Purchase Order",
            "Packing List": "Shipping Manifest",
            "Bill of Lading": "Shipping Manifest",
            "Electricity Bill": "Electricity Bill",
            "Water Bill": "Utility Bill",
            "Fuel Receipt": "Fuel Log",
            "ERP Export": "ERP Export",
            "Supplier Sheet": "Supplier List"
        }
        
        mapped_pred = mapping.get(raw_pred, "Other")
        
        # Keyword override when fine-tuned checkpoint is missing or model confidence is uncalibrated
        text_lower = ocr_text.lower()
        if not self.is_fine_tuned or confidence < 0.8:
            if "cbam" in text_lower or "embedded emissions" in text_lower:
                mapped_pred = "CBAM Data"
                confidence = 0.99
            elif "employee travel" in text_lower or "business trip" in text_lower or "flight booking" in text_lower or "travel expense" in text_lower:
                mapped_pred = "Employee Travel"
                confidence = 0.99
            elif "fuel log" in text_lower or "diesel log" in text_lower or "petrol log" in text_lower or "fuel receipt" in text_lower:
                mapped_pred = "Fuel Log"
                confidence = 0.99
            elif "electricity bill" in text_lower or "electric bill" in text_lower or "power bill" in text_lower:
                mapped_pred = "Electricity Bill"
                confidence = 0.99
            elif "gas bill" in text_lower or "natural gas" in text_lower or "gas invoice" in text_lower:
                mapped_pred = "Gas Bill"
                confidence = 0.99
            elif "utility bill" in text_lower or "utility receipt" in text_lower:
                mapped_pred = "Utility Bill"
                confidence = 0.99
            elif "supplier list" in text_lower or "supplier sheet" in text_lower or "vendor list" in text_lower:
                mapped_pred = "Supplier List"
                confidence = 0.99
            elif "erp export" in text_lower or "sap export" in text_lower or "erp log" in text_lower:
                mapped_pred = "ERP Export"
                confidence = 0.99
            elif "shipping manifest" in text_lower or "packing list" in text_lower or "bill of lading" in text_lower or "shipment manifest" in text_lower:
                mapped_pred = "Shipping Manifest"
                confidence = 0.99
            elif "invoice" in text_lower or "inv-" in text_lower or "inv_" in text_lower:
                mapped_pred = "Invoice"
                confidence = 0.99
            elif "purchase order" in text_lower or "po-" in text_lower or "po_" in text_lower or "order no" in text_lower:
                mapped_pred = "Purchase Order"
                confidence = 0.99

        latency = (time.perf_counter() - t_start) * 1000.0
        
        return {
            "document_type": mapped_pred,
            "confidence": confidence,
            "inference_time_ms": round(latency, 2)
        }

    def classify(self, ocr_text: str) -> str:
        res = self.classify_with_details(ocr_text)
        return res["document_type"]

if __name__ == "__main__":
    classifier = DocumentClassifier()
    sample_text = "INVOICE #INV-2026-9872. Supplier: SteelCorp. Item: Steel Sheet. Quantity: 50 tonnes."
    res = classifier.classify_with_details(sample_text)
    print("Classified:", res)
