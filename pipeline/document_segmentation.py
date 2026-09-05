"""
CarbonLedger Document Segmenter
=================================
Groups PDF pages into logical document segments and classifies each segment type.

DESIGN PRINCIPLES:
- Support real-world document types, not just structured dataset pages.
- Use keyword scoring rather than single-trigger matching for robustness.
- UNKNOWN pages with tables/KVs are attached to the previous segment rather than dropped.
- No page-number-specific or filename-specific logic.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


# ---------------------------------------------------------------------------
# Document type keyword signals (all lowercase)
# Each entry: (doc_type, keywords_that_trigger_high_confidence, keywords_for_scoring)
# ---------------------------------------------------------------------------

_DOC_TYPE_SIGNALS = {
    # ─── Structured dataset phases (legacy compatibility) ─────────────────────
    "PURCHASE_INVOICE_PHASE": {
        "exclusive": ["phase 1:", "invoice upload"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "PURCHASE_INVOICE",
    },
    "PURCHASE_ORDER_PHASE": {
        "exclusive": ["phase 2:", "purchase order upload"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "PURCHASE_ORDER",
    },
    "SUPPLIER_MASTER_PHASE": {
        "exclusive": ["phase 3:", "supplier master upload"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "SUPPLIER_MASTER",
    },
    "LOGISTICS_PHASE": {
        "exclusive": ["phase 4:", "logistics & shipping"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "LOGISTICS_SHIPPING",
    },
    "UTILITY_PHASE": {
        "exclusive": ["phase 5:", "utility bills upload"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "UTILITY_BILL",
    },
    "FACILITY_PHASE": {
        "exclusive": ["phase 6:", "facility & plant upload"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "FACILITY_PLANT",
    },
    "MATERIAL_CONSUMPTION_PHASE": {
        "exclusive": ["phase 7:", "material consumption upload"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "MATERIAL_CONSUMPTION",
    },
    "FUEL_CONSUMPTION_PHASE": {
        "exclusive": ["phase 8:", "fuel consumption upload"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "FUEL_CONSUMPTION",
    },
    "ELECTRICITY_GRID_PHASE": {
        "exclusive": ["phase 9:", "electricity grid upload"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "ELECTRICITY_GRID",
    },
    "CBAM_MAPPING_PHASE": {
        "exclusive": ["phase 10:", "cbam product mapping"],
        "keywords": [],
        "min_score": 1,
        "doc_type": "CBAM_PRODUCT_MAPPING",
    },
}

# Keyword-score based classification for real-world documents
_SCORED_TYPES = [
    # ─── Transportation / Logistics ────────────────────────────────────────────
    {
        "doc_type": "TRANSPORTATION_INVOICE",
        "high_confidence_triggers": [
            "freight invoice", "transport invoice", "freight bill", "transport receipt",
            "logistics invoice", "delivery note", "dispatch note",
            "transportation charges", "freight charges",
        ],
        "scoring_keywords": [
            "origin", "destination", "transport mode", "mode of transport",
            "distance", "weight", "carrier", "freight", "logistics",
            "truck", "lorry", "rail", "ship", "sea freight", "air freight",
            "dispatch", "shipment", "transport",
        ],
        "required_min": 2,
    },
    # ─── Shipping / Bill of Lading ─────────────────────────────────────────────
    {
        "doc_type": "SHIPPING_MANIFEST",
        "high_confidence_triggers": [
            "bill of lading", "b/l number", "shipping manifest", "packing list",
            "delivery challan", "consignment note",
        ],
        "scoring_keywords": [
            "consignee", "shipper", "vessel", "port of loading", "port of discharge",
            "seal no", "container no", "bl no", "bl number", "hs code",
            "net weight", "gross weight", "package", "cargo",
        ],
        "required_min": 2,
    },
    # ─── Electricity / Utility ─────────────────────────────────────────────────
    {
        "doc_type": "ELECTRICITY_BILL",
        "high_confidence_triggers": [
            "electricity bill", "power bill", "electricity invoice",
            "electric bill", "energy bill", "utility bill",
        ],
        "scoring_keywords": [
            "kwh", "mwh", "electricity", "units consumed", "meter reading",
            "billing period", "tariff", "grid", "electricity consumption",
            "power consumption",
        ],
        "required_min": 2,
    },
    # ─── Fuel ──────────────────────────────────────────────────────────────────
    {
        "doc_type": "FUEL_INVOICE",
        "high_confidence_triggers": [
            "fuel invoice", "diesel invoice", "fuel receipt", "petroleum invoice",
            "fuel bill", "bunker invoice",
        ],
        "scoring_keywords": [
            "fuel type", "diesel", "petrol", "gasoline", "lpg", "cng",
            "natural gas", "litre", "liter", "gallon", "fuel consumption",
            "bunker", "petroleum",
        ],
        "required_min": 2,
    },
    # ─── Natural gas (often utility) ───────────────────────────────────────────
    {
        "doc_type": "FUEL_INVOICE",
        "high_confidence_triggers": [
            "gas bill", "natural gas invoice", "gas invoice",
        ],
        "scoring_keywords": [
            "natural gas", "gas consumption", "mcm", "m3", "cubic metre",
        ],
        "required_min": 1,
    },
    # ─── CBAM / Supplier Declaration ──────────────────────────────────────────
    {
        "doc_type": "SUPPLIER_DECLARATION",
        "high_confidence_triggers": [
            "cbam declaration", "emission declaration", "supplier declaration",
            "embedded emissions", "cbam regulation", "carbon border",
        ],
        "scoring_keywords": [
            "cn code", "country of origin", "net mass", "production facility",
            "direct emissions", "indirect emissions", "verification",
            "production route", "emission factor",
        ],
        "required_min": 2,
    },
    # ─── Purchase Invoice (general) ────────────────────────────────────────────
    {
        "doc_type": "PURCHASE_INVOICE",
        "high_confidence_triggers": [
            "tax invoice", "commercial invoice", "purchase invoice",
            "proforma invoice", "invoice", "sales invoice",
        ],
        "scoring_keywords": [
            "invoice no", "invoice date", "supplier", "vendor", "material",
            "quantity", "unit", "total", "gst", "vat", "tax",
            "hs code", "hsn", "description",
        ],
        "required_min": 3,
    },
    # ─── Purchase Order ────────────────────────────────────────────────────────
    {
        "doc_type": "PURCHASE_ORDER",
        "high_confidence_triggers": [
            "purchase order", "po document",
        ],
        "scoring_keywords": [
            "po no", "po number", "order date", "delivery date",
            "supplier", "material", "quantity", "unit",
        ],
        "required_min": 2,
    },
    # ─── Material Consumption ──────────────────────────────────────────────────
    {
        "doc_type": "MATERIAL_CONSUMPTION",
        "high_confidence_triggers": [
            "material consumption", "consumption report", "material usage",
        ],
        "scoring_keywords": [
            "material", "quantity", "consumption", "production line", "supplier",
        ],
        "required_min": 2,
    },
]


def _score_page(text_lower: str) -> Tuple[str, float]:
    """
    Scores the page text against all document type signals.
    Returns (doc_type, confidence).
    """
    # 1. Check exclusive structured-dataset phase markers first (highest priority)
    for _, signal in _DOC_TYPE_SIGNALS.items():
        for trigger in signal.get("exclusive", []):
            if trigger in text_lower:
                return signal["doc_type"], 0.95

    # 2. Score-based classification for real-world docs
    best_type = "UNKNOWN"
    best_confidence = 0.0

    for sig in _SCORED_TYPES:
        # High confidence triggers
        for trigger in sig["high_confidence_triggers"]:
            if trigger in text_lower:
                confidence = 0.92
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_type = sig["doc_type"]
                break

        # Scoring keywords
        score = sum(1 for kw in sig["scoring_keywords"] if kw in text_lower)
        required = sig.get("required_min", 2)
        if score >= required:
            raw_conf = min(0.90, 0.55 + score * 0.05)
            if raw_conf > best_confidence:
                best_confidence = raw_conf
                best_type = sig["doc_type"]

    # 3. Legacy single-keyword fallbacks for backwards compatibility
    if best_type == "UNKNOWN":
        if "kwh" in text_lower or "electricity consumption" in text_lower:
            return "ELECTRICITY_BILL", 0.75
        if "fuel type" in text_lower and "diesel" in text_lower:
            return "FUEL_INVOICE", 0.75
        if "ship id" in text_lower or ("carrier" in text_lower and "distance" in text_lower):
            return "TRANSPORTATION_INVOICE", 0.75

    if best_confidence < 0.50:
        return "UNKNOWN", best_confidence

    return best_type, best_confidence


# Pages with these keywords are clearly non-actionable cover/summary pages
_SUMMARY_PAGE_MARKERS = {
    "dataset summary", "purpose & usage", "sample dataset",
    "data coverage", "data dictionary", "table of contents",
    "index", "instructions", "how to use",
}


class DocumentSegmenter:
    def __init__(self):
        pass

    def classify_page(self, page_text: str) -> Tuple[str, float]:
        """
        Classifies page text and returns (doc_type, confidence).
        """
        if not page_text or not page_text.strip():
            return "UNKNOWN", 0.0

        low = page_text.lower()

        # Reject summary/cover pages
        if any(marker in low for marker in _SUMMARY_PAGE_MARKERS):
            return "UNKNOWN", 0.50

        return _score_page(low)

    def segment_document(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Groups pages of a document into logical segments.

        Improvement over previous version:
        - UNKNOWN pages with non-trivial content are attached to the previous segment
          rather than starting a fresh boundary (avoids losing multi-page tables).
        - Only truly empty or summary pages are dropped.
        """
        segments = []
        pages = parsed_doc.get("pages", [])
        if not pages:
            return segments

        current_segment_pages: List[int] = []
        current_type: Optional[str] = None

        for idx, page in enumerate(pages):
            page_num = page.get("page_number")
            page_text = page.get("text", "")

            p_type, p_conf = self.classify_page(page_text)

            if p_type == "UNKNOWN":
                if current_segment_pages:
                    # Attach this page to the current segment if it has content
                    # (multi-page continuation of the same document)
                    has_content = bool(page_text and len(page_text.strip()) > 50)
                    if has_content:
                        current_segment_pages.append(page_num)
                    else:
                        # Truly empty / summary page — close current segment
                        segments.append(self._make_segment(segments, current_segment_pages, current_type))
                        current_segment_pages = []
                        current_type = None
                # If no current segment, skip this page
                continue

            if current_type is None:
                current_type = p_type
                current_segment_pages.append(page_num)
            elif p_type == current_type:
                current_segment_pages.append(page_num)
            else:
                # Doc type changed — close current segment and start new
                segments.append(self._make_segment(segments, current_segment_pages, current_type))
                current_type = p_type
                current_segment_pages = [page_num]

        # Append remaining
        if current_segment_pages:
            segments.append(self._make_segment(segments, current_segment_pages, current_type))

        return segments

    def _make_segment(
        self,
        existing_segments: List[dict],
        pages: List[int],
        doc_type: Optional[str],
    ) -> dict:
        return {
            "segment_id": f"SEG_{len(existing_segments) + 1:03d}",
            "pages": pages,
            "type": doc_type or "UNKNOWN",
            "confidence": 0.95,
        }
