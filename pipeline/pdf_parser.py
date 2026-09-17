import os
import pdfplumber
from pipeline.ocr_engine import BaseOCREngine, TesseractOCR

class PDFParser:
    def __init__(self, ocr_engine: BaseOCREngine = None):
        self.ocr_engine = ocr_engine

    def parse_pdf(self, pdf_path: str, temp_image_dir: str = None, pdf_obj = None) -> dict:
        """
        Parses a PDF file. Extracts embedded text if available, 
        otherwise falls back to OCR on rendered pages.
        """
        result = {
            "file_name": os.path.basename(pdf_path),
            "pages": []
        }
        
        has_embedded_text = False
        collected_pages = []
        total_words = 0

        # Helper to process an open pdfplumber object
        def _process_pages(pdf):
            nonlocal total_words, has_embedded_text, collected_pages
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                words = page.extract_words() or []
                total_words += len(words)
                page_words = []
                for w in words:
                    page_words.append({
                        "text": w["text"],
                        "confidence": 1.0,
                        "bbox": [float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"])],
                        "page": page_num
                    })
                full_text = " ".join([w["text"] for w in words])
                collected_pages.append({
                    "page_number": page_num,
                    "text": full_text,
                    "words": page_words,
                    "source": "PDF_EMBEDDED_TEXT"
                })
            
            if total_words > 3 * len(pdf.pages):
                has_embedded_text = True

        if pdf_obj is not None:
            _process_pages(pdf_obj)
        else:
            with pdfplumber.open(pdf_path) as pdf:
                _process_pages(pdf)
                
        if has_embedded_text:
            result["pages"] = collected_pages
        
        # If no embedded text, fallback to OCR
        if not has_embedded_text:
            print(f"No embedded text found in {pdf_path}. Falling back to OCR.")
            if not temp_image_dir:
                temp_image_dir = "temp_uploads"
            os.makedirs(temp_image_dir, exist_ok=True)
            
            if not self.ocr_engine:
                try:
                    self.ocr_engine = TesseractOCR()
                except Exception as e:
                    raise RuntimeError(f"OCR_ENGINE_UNAVAILABLE: Real OCR is required but Tesseract is not installed. {str(e)}")
            
            # Check if engine is actually TesseractOCR or REAL mode
            if not isinstance(self.ocr_engine, TesseractOCR):
                raise RuntimeError("OCR_ENGINE_UNAVAILABLE: Real OCR engine (Tesseract) must be used in REAL mode.")
                
            with pdfplumber.open(pdf_path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    page_num = page_idx + 1
                    im = page.to_image(resolution=150)
                    img_path = os.path.join(temp_image_dir, f"page_{page_num:03d}.png")
                    im.save(img_path, format="PNG")
                    
                    ocr_result = self.ocr_engine.extract_text(img_path, page_number=page_num)
                    full_text = " ".join([w["text"] for w in ocr_result["words"]])
                    
                    result["pages"].append({
                        "page_number": page_num,
                        "text": full_text,
                        "words": ocr_result["words"],
                        "source": "REAL_OCR"
                    })
                
        return result
