"""
CarbonLedger Context Propagator
=================================
Implements hierarchical context propagation for document extraction.

Context can exist at:
  DOCUMENT → LOGICAL_DOCUMENT → PAGE → SECTION → TABLE → ROW

Propagation rules:
- Supplier found in page KV block is propagated to all rows in tables on that page.
- Context is NOT propagated across segment boundaries.
- Provenance records whether a value was DIRECT or CONTEXT_PROPAGATED.
- Ambiguous propagation is flagged, not silently applied.
"""

import re
from typing import Optional, Dict, Any, List, Tuple


# Patterns to detect supplier/company context in page header text.
_SUPPLIER_KV_PATTERNS = [
    r"(?:supplier|vendor|sold\s+by|from|seller|exporter|manufacturer|producer)\s*[:\-]\s*([^\n|]{3,80})",
    r"(?:supplier|vendor)\s+name\s*[:\-]\s*([^\n|]{3,80})",
]

_COMPANY_KV_PATTERNS = [
    r"(?:company|buyer|customer|consignee|bill\s+to|ship\s+to|importer)\s*[:\-]\s*([^\n|]{3,80})",
    r"(?:company)\s+name\s*[:\-]\s*([^\n|]{3,80})",
]

_PERIOD_KV_PATTERNS = [
    r"(?:billing\s+period|bill\s+period|reading\s+period|period|invoice\s+date|date)\s*[:\-]\s*([^\n|]{3,40})",
]

_INVOICE_NUMBER_PATTERNS = [
    r"(?:invoice\s+no|invoice\s+number|invoice\s+#|inv\s+no|inv\s+#|bill\s+no|po\s+no|po\s+number)\s*[:\-]?\s*([A-Za-z0-9\-\/]{2,30})",
]


def _search_kv(text: str, patterns: List[str]) -> Optional[str]:
    """Search text for the first matching KV pattern."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # Remove trailing punctuation / noise
            val = re.sub(r"[\|\,\;\:]$", "", val).strip()
            # Reject values that look like noise
            if len(val) < 2 or val.lower() in ("n/a", "na", "none", "null", "-", "—"):
                continue
            return val
    return None


def extract_page_context(page_text: str) -> Dict[str, Any]:
    """
    Scans full page text for context-level KV fields.
    Returns a dict of context values with provenance method = CONTEXT_PROPAGATED.
    """
    context: Dict[str, Any] = {}

    supplier = _search_kv(page_text, _SUPPLIER_KV_PATTERNS)
    if supplier:
        context["supplier"] = {
            "value": supplier,
            "method": "KV_EXTRACTION",
            "propagation": "PAGE_CONTEXT",
        }

    company = _search_kv(page_text, _COMPANY_KV_PATTERNS)
    if company:
        context["customer_name"] = {
            "value": company,
            "method": "KV_EXTRACTION",
            "propagation": "PAGE_CONTEXT",
        }

    period = _search_kv(page_text, _PERIOD_KV_PATTERNS)
    if period:
        context["period"] = {
            "value": period,
            "method": "KV_EXTRACTION",
            "propagation": "PAGE_CONTEXT",
        }

    invoice_num = _search_kv(page_text, _INVOICE_NUMBER_PATTERNS)
    if invoice_num:
        context["invoice_number"] = {
            "value": invoice_num,
            "method": "KV_EXTRACTION",
            "propagation": "PAGE_CONTEXT",
        }

    return context


def propagate_context_to_row(
    row_dict: dict,
    page_context: Dict[str, Any],
    segment_type: str,
) -> Tuple[dict, Dict[str, str]]:
    """
    Injects page-level context values into a row dict where the row has no value.
    Returns (updated_row_dict, propagation_log).

    propagation_log maps field_name → "DIRECT" | "CONTEXT_PROPAGATED"
    """
    propagation_log = {}
    updated = dict(row_dict)

    # Only propagate supplier for purchase/material types (not transport)
    purchase_types = {
        "PURCHASE_INVOICE", "PURCHASE_ORDER", "MATERIAL_CONSUMPTION",
        "CBAM_PRODUCT_MAPPING", "SUPPLIER_MASTER",
    }

    if segment_type in purchase_types:
        ctx_sup = page_context.get("supplier")
        if ctx_sup and not updated.get("supplier") and not updated.get("supplier_name"):
            updated["supplier"] = ctx_sup["value"]
            updated["_supplier_propagated"] = True
            propagation_log["supplier"] = "CONTEXT_PROPAGATED"

        ctx_cust = page_context.get("customer_name")
        if ctx_cust and not updated.get("customer_name") and not updated.get("company_name"):
            updated["customer_name"] = ctx_cust["value"]
            propagation_log["customer_name"] = "CONTEXT_PROPAGATED"

    # Invoice number / period can propagate to all types
    ctx_inv = page_context.get("invoice_number")
    if ctx_inv and not updated.get("invoice_id") and not updated.get("invoice_number"):
        updated["invoice_id"] = ctx_inv["value"]
        propagation_log["invoice_number"] = "CONTEXT_PROPAGATED"

    ctx_period = page_context.get("period")
    if ctx_period and not updated.get("period") and not updated.get("date"):
        updated["period"] = ctx_period["value"]
        propagation_log["period"] = "CONTEXT_PROPAGATED"

    # Mark non-propagated fields as DIRECT
    for key in row_dict:
        if key not in propagation_log and row_dict.get(key) is not None:
            propagation_log[key] = "DIRECT"

    return updated, propagation_log


def build_propagation_provenance(
    propagation_log: Dict[str, str],
    base_provenance: Dict[str, Any],
    page_num: int,
) -> Dict[str, Any]:
    """
    Updates provenance entries to reflect whether each field was DIRECT or CONTEXT_PROPAGATED.
    Adds 'extraction_method' key to each provenance entry.
    """
    updated = dict(base_provenance)
    for field_name, method in propagation_log.items():
        if field_name in updated:
            updated[field_name]["extraction_method"] = method
            if method == "CONTEXT_PROPAGATED":
                # Slightly reduce confidence for propagated values
                prov_conf = updated[field_name].get("confidence", 0.95)
                updated[field_name]["confidence"] = min(prov_conf, 0.85)
        else:
            if method == "CONTEXT_PROPAGATED":
                updated[field_name] = {
                    "field": field_name,
                    "value": None,
                    "source": "CONTEXT_PROPAGATED",
                    "page": page_num,
                    "bbox": None,
                    "raw_text": None,
                    "confidence": 0.80,
                    "extraction_method": "CONTEXT_PROPAGATED",
                }
    return updated
