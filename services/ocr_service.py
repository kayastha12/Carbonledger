import os
from typing import Dict, Any
from services.document_understanding import DocumentUnderstandingService

class OCRService:
    """
    OCR and document layout analysis service.
    Natively parses PDF layouts/tables and extracts text using pdfplumber, pypdf, and PaddleOCR.
    """
    def __init__(self, doc_understanding: DocumentUnderstandingService = None):
        self.doc_understanding = doc_understanding or DocumentUnderstandingService()

    def extract_document(self, file_path: str) -> Dict[str, Any]:
        """
        Natively extracts text, words, tables, and pages metadata from the document.
        """
        return self.doc_understanding.ocr_document(file_path)
