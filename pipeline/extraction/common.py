from typing import Optional, List, Tuple
from schemas.document import PageLayout, KeyValueBlock, LayoutElement
from pipeline.extraction.field_mapper import FieldMapper
from pipeline.extraction.entity_normalizer import EntityNormalizer
from schemas.extraction import ExtractedField

class ExtractionHelper:
    @staticmethod
    def find_kv(page_layout: PageLayout, canonical_name: str) -> Optional[KeyValueBlock]:
        for kv in page_layout.key_values:
            if FieldMapper.get_canonical_field(kv.key) == canonical_name:
                return kv
        return None

    @staticmethod
    def find_header_value(page_layout: PageLayout) -> Optional[LayoutElement]:
        for elem in page_layout.elements:
            if elem.type == "HEADER":
                text = elem.text
                if text:
                    text_low = text.lower()
                    invalid_keywords = [
                        "sample", "dataset", "phase", "upload", "carbonledger", 
                        "invoice", "purchase order", "utility bill", "manifest", 
                        "loading", "page", "table", "document", "recipient", "billed to",
                        "shipped to", "consignee", "consignor"
                    ]
                    if not any(kw in text_low for kw in invalid_keywords) and len(text.strip()) >= 3 and len(text.strip()) <= 100 and any(c.isalpha() for c in text):
                        return elem
        return None

    @staticmethod
    def build_field(
        kv: Optional[KeyValueBlock], 
        elem: Optional[LayoutElement], 
        canonical_name: str, 
        fallback_val: Optional[str] = None
    ) -> ExtractedField:
        normalizer = EntityNormalizer()
        
        if kv:
            val = kv.value
            num_val, norm_unit = normalizer.normalize_value(val)
            norm_val = {"value": num_val, "unit": norm_unit} if num_val is not None else val
            
            return ExtractedField(
                value=val,
                original_value=val,
                normalized_value=norm_val,
                confidence=kv.confidence,
                source={"type": "REAL_DOCUMENT", "method": "key_value", "page": kv.page, "bbox": kv.bbox},
                status="extracted"
            )
        elif elem:
            val = elem.text
            return ExtractedField(
                value=val,
                original_value=val,
                normalized_value=val,
                confidence=elem.confidence,
                source={"type": "REAL_DOCUMENT", "method": "header", "page": elem.page, "bbox": element_bbox_or_fallback(elem)},
                status="extracted"
            )
        else:
            return ExtractedField(
                value=fallback_val,
                original_value=fallback_val,
                normalized_value=fallback_val,
                confidence=0.0,
                source={"type": "REAL_DOCUMENT" if fallback_val else "NOT_FOUND", "method": "derived" if fallback_val else None, "page": 1, "bbox": [0, 0, 0, 0]},
                status="extracted" if fallback_val else "not_found"
            )

def element_bbox_or_fallback(elem: LayoutElement) -> List[float]:
    return elem.bbox if elem.bbox else [0, 0, 0, 0]

def detect_currency_from_layout(page_layout: PageLayout, default_val: Optional[str] = None) -> Optional[str]:
    text_to_check = ""
    for elem in page_layout.elements:
        text_to_check += " " + elem.text
    for kv in page_layout.key_values:
        text_to_check += " " + kv.key + " " + kv.value
    
    text_to_check = text_to_check.lower()
    
    if "inr" in text_to_check or "₹" in text_to_check or "rupees" in text_to_check:
        return "INR"
    if "$" in text_to_check or "usd" in text_to_check or "dollar" in text_to_check:
        return "USD"
    if "€" in text_to_check or "eur" in text_to_check or "euro" in text_to_check:
        return "EUR"
    if "£" in text_to_check or "gbp" in text_to_check or "pound" in text_to_check:
        return "GBP"
    if "¥" in text_to_check or "jpy" in text_to_check or "yen" in text_to_check:
        return "JPY"
        
    return default_val

