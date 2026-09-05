import os
import json
import abc
from enum import Enum
from PIL import Image

class OCRMode(str, Enum):
    REAL = "REAL"
    ANNOTATION = "ANNOTATION"
    MOCK = "MOCK"

class BaseOCREngine(abc.ABC):
    @abc.abstractmethod
    def extract_text(self, image_path: str, page_number: int = 1) -> dict:
        """
        Extract text from an image.
        Returns:
            dict containing:
                "page": page_number,
                "words": [
                    {
                        "text": str,
                        "confidence": float,
                        "bbox": [x_min, y_min, x_max, y_max]
                    }
                ]
        """
        pass

class TesseractOCR(BaseOCREngine):
    def __init__(self, tesseract_cmd: str = None):
        import pytesseract
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # Common paths on Windows
            default_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            ]
            for path in default_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break

    def extract_text(self, image_path: str, page_number: int = 1) -> dict:
        import pytesseract
        try:
            img = Image.open(image_path)
            # Get word boxes
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            words = []
            n_boxes = len(data['level'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if not text:
                    continue
                # bbox is left, top, width, height -> convert to [x_min, y_min, x_max, y_max]
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                words.append({
                    "text": text,
                    "confidence": float(data['conf'][i]) / 100.0,
                    "bbox": [x, y, x + w, y + h],
                    "page": page_number
                })
            return {"page": page_number, "words": words, "source": "tesseract"}
        except Exception as e:
            # Prevent silent fallback to MockOCR in production
            raise RuntimeError(f"OCR_ENGINE_UNAVAILABLE: Tesseract OCR failed ({str(e)})")

class AnnotationOCR(BaseOCREngine):
    """
    Reads the corresponding generated sidecar annotation JSON.
    Perfect for test pipeline running where tesseract binary might not be available.
    """
    def __init__(self, annotations_dir: str):
        self.annotations_dir = annotations_dir

    def extract_text(self, image_path: str, page_number: int = 1) -> dict:
        # Resolve image filename to doc_id
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        # e.g. CL_PURCHASE_INVOICE_001_page1 -> CL_PURCHASE_INVOICE_001
        doc_id = base_name.rsplit("_page", 1)[0]
        
        annotation_file = os.path.join(self.annotations_dir, f"{doc_id}.json")
        if os.path.exists(annotation_file):
            with open(annotation_file, "r") as f:
                data = json.load(f)
            
            # Filter words for the correct page
            words = [
                {
                    "text": w["text"],
                    "confidence": 1.0,
                    "bbox": w["bbox"],
                    "page": page_number
                }
                for w in data.get("words", [])
                if w.get("page", 1) == page_number
            ]
            return {"page": page_number, "words": words, "source": "annotation"}
        
        # If no annotation file, raise error instead of silent mock fallback
        raise RuntimeError(f"OCR_ENGINE_UNAVAILABLE: Annotation not found for {doc_id}")

class MockOCR(BaseOCREngine):
    def extract_text(self, image_path: str, page_number: int = 1) -> dict:
        # Returns simple simulated words based on the filename/type
        base_name = os.path.basename(image_path).upper()
        words = []
        if "INVOICE" in base_name:
            words = [
                {"text": "ABC", "confidence": 0.99, "bbox": [50, 42, 100, 62], "page": page_number},
                {"text": "Steel", "confidence": 0.99, "bbox": [110, 42, 160, 62], "page": page_number},
                {"text": "Invoice", "confidence": 0.99, "bbox": [50, 82, 120, 102], "page": page_number},
                {"text": "Number:", "confidence": 0.99, "bbox": [130, 82, 200, 102], "page": page_number},
                {"text": "INV-2026-1001", "confidence": 0.99, "bbox": [210, 82, 300, 102], "page": page_number},
                {"text": "Quantity:", "confidence": 0.99, "bbox": [50, 150, 120, 170], "page": page_number},
                {"text": "25", "confidence": 0.99, "bbox": [130, 150, 160, 170], "page": page_number},
                {"text": "tonne", "confidence": 0.99, "bbox": [170, 150, 210, 170], "page": page_number}
            ]
        else:
            words = [
                {"text": "Electricity", "confidence": 0.99, "bbox": [50, 50, 150, 70], "page": page_number},
                {"text": "Bill", "confidence": 0.99, "bbox": [160, 50, 200, 70], "page": page_number},
                {"text": "15000", "confidence": 0.99, "bbox": [50, 100, 100, 120], "page": page_number},
                {"text": "kWh", "confidence": 0.99, "bbox": [110, 100, 150, 120], "page": page_number}
            ]
        return {"page": page_number, "words": words, "source": "mock"}
