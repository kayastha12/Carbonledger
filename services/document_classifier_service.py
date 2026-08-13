from typing import Dict, Any
from models.document_classifier import DocumentClassifier

class DocumentClassifierService:
    """
    Classifies documents based on their OCR text using the DocumentClassifier sequence model.
    """
    def __init__(self, classifier: DocumentClassifier = None):
        self.classifier = classifier or DocumentClassifier()

    def classify_document(self, ocr_text: str) -> Dict[str, Any]:
        """
        Predicts document type (e.g., Invoice, Purchase Order, Utility Bill) and returns confidence scores.
        """
        return self.classifier.classify_with_details(ocr_text)
