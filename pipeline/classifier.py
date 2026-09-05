import os
import json
import abc
from typing import Dict, Any, List
from schemas.document import ClassificationResult, PageClassification

class BaseDocumentClassifier(abc.ABC):
    @abc.abstractmethod
    def classify(self, document: dict) -> ClassificationResult:
        """
        Classifies a parsed document dict containing pages.
        """
        pass

class RuleBasedDocumentClassifier(BaseDocumentClassifier):
    def __init__(self, config_path: str = None):
        if not config_path:
            # Look in standard config folder
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "classification", "document_types.json")
            
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.rules = json.load(f)
        else:
            self.rules = {}

    def classify(self, document: dict) -> ClassificationResult:
        pages_classifications = []
        overall_scores = {}
        
        for page_data in document.get("pages", []):
            page_num = page_data.get("page_number", 1)
            text_lower = page_data.get("text", "").lower()
            
            page_scores = {}
            for doc_type, info in self.rules.items():
                score = 0
                for keyword, weight in info.get("keywords", {}).items():
                    if keyword.lower() in text_lower:
                        score += weight
                page_scores[doc_type] = score
                
            # Determine best type for the page
            best_type = "UNKNOWN"
            best_score = 0
            for doc_type, score in page_scores.items():
                if score > best_score:
                    best_score = score
                    best_type = doc_type
            
            # Confidence calculation: deterministic based on raw score
            if best_score > 0:
                confidence = round(min(0.99, best_score / (best_score + 1.0)), 2)
            else:
                confidence = 0.0
                best_type = "UNKNOWN"
                
            pages_classifications.append(PageClassification(
                page=page_num,
                document_type=best_type,
                confidence=confidence
            ))
            
            # Accumulate overall scores
            for doc_type, score in page_scores.items():
                overall_scores[doc_type] = overall_scores.get(doc_type, 0) + score

        # Aggregate overall type
        unique_types = set(p.document_type for p in pages_classifications)
        
        # Default empty overall
        overall_type = "UNKNOWN"
        overall_conf = 0.0
        requires_review = False
        
        if not pages_classifications:
            overall_type = "UNKNOWN"
            overall_conf = 0.0
            requires_review = True
        elif len(unique_types) == 1:
            overall_type = list(unique_types)[0]
            overall_conf = round(sum(p.confidence for p in pages_classifications) / len(pages_classifications), 2)
            if overall_type == "UNKNOWN" or overall_conf < 0.70:
                requires_review = True
        else:
            # Mixed pages
            overall_type = "MIXED"
            overall_conf = round(sum(p.confidence for p in pages_classifications) / len(pages_classifications), 2)
            requires_review = True

        # Convert scores to float for Pydantic Dict[str, float]
        scores_out = {k: float(v) for k, v in overall_scores.items()}
        # If empty
        if not scores_out:
            scores_out = {k: 0.0 for k in self.rules.keys()}

        return ClassificationResult(
            document_type=overall_type,
            confidence=overall_conf,
            method="rule_based",
            scores=scores_out,
            requires_review=requires_review,
            pages=pages_classifications,
            overall_document_type=overall_type,
            overall_confidence=overall_conf
        )
