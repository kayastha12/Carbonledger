"""
CarbonLedger Table Detector
=============================
Semantic table validation that replaces the fragile `is_valid_data_table()` function.

DESIGN PRINCIPLES:
- Do NOT require exact header strings.
- Use a confidence score for table validity.
- Consider: column count, row count, header similarity, numeric density, doc type.
- Return a (is_valid: bool, confidence: float, reason: str) tuple.
"""

import re
from typing import Optional, Tuple, List


# ---------------------------------------------------------------------------
# Semantic header groups — keywords that indicate different table types
# ---------------------------------------------------------------------------

_TRANSPORT_HEADER_KEYWORDS = {
    "stage", "leg", "from", "origin", "loading", "pol", "ship from", "place of dispatch",
    "to", "destination", "discharge", "pod", "ship to", "delivery location",
    "mode", "transport", "vehicle", "carrier", "shipping", "method",
    "distance", "km", "kms", "dist",
    "weight", "cargo", "gross", "net", "mass", "tonne", "ton", "kg",
    "via", "route",
}

_INVOICE_HEADER_KEYWORDS = {
    "s.no", "s no", "sr no", "sr.no", "serial", "no.", "item no", "line",
    "item", "description", "desc", "particulars", "goods", "material", "product",
    "article", "commodity",
    "qty", "quantity", "volume",
    "unit", "uom", "units",
    "rate", "price", "cost", "amount", "value", "total",
    "hsn", "hs", "cn code", "sac",
    "gst", "tax", "vat",
    "supplier", "vendor", "manufacturer",
}

_UTILITY_HEADER_KEYWORDS = {
    "utility", "consumption", "kwh", "mwh", "units consumed", "meter",
    "billing", "period", "reading", "electricity", "gas", "fuel",
    "cost", "amount", "tariff",
}

_SHIPPING_HEADER_KEYWORDS = {
    "package", "pkg", "container", "seal", "bl", "b/l",
    "description", "commodity",
    "net weight", "gross weight", "net wt", "gross wt",
    "hs code", "hs", "cn code", "origin", "country",
    "marks", "shipper", "consignee",
}

_CBAM_HEADER_KEYWORDS = {
    "cn code", "hs code", "hsn", "commodity",
    "country of origin", "country",
    "embedded emissions", "direct emissions", "indirect emissions",
    "production facility", "producer",
    "net mass", "quantity",
}

_MASTER_DATA_HEADER_KEYWORDS = {
    "supplier id", "supplier name", "plant id", "plant name",
    "facility id", "product id", "grid id",
    "country", "city", "location", "esg", "certification",
}

# ---------------------------------------------------------------------------
# Structural rejection patterns — headers that indicate non-data tables
# ---------------------------------------------------------------------------
_REJECT_HEADER_PATTERNS = [
    r"\b\d{2}[\/\-]\d{2}[\/\-]\d{4}\b",      # Date-as-header
    r"\b(inv|po|lr|util|bl|bol)-\d+\b",        # ID-as-header
    r"^nim/pi",
]

_METADATA_LABELS = {
    "invoice no", "invoice date", "po no", "vehicle no",
    "place of supply", "transporter", "billed to", "shipped to",
    "gstin", "pan", "cin",
}


def _headers_from_row(row: list) -> List[str]:
    """Extract cleaned header strings from a table's first row."""
    headers = []
    for h in row:
        if h is None:
            headers.append("")
        else:
            cleaned = str(h).replace("\n", " ").lower().strip()
            headers.append(cleaned)
    return headers


def _count_keyword_hits(headers: List[str], keyword_set) -> int:
    count = 0
    for h in headers:
        for kw in keyword_set:
            if kw in h:
                count += 1
                break  # only count each header once
    return count


def _has_reject_pattern(header: str) -> bool:
    for pat in _REJECT_HEADER_PATTERNS:
        if re.search(pat, header, re.IGNORECASE):
            return True
    return False


def _is_metadata_heavy(headers: List[str]) -> bool:
    meta_hits = sum(1 for h in headers if any(lbl in h for lbl in _METADATA_LABELS))
    return meta_hits >= 2


def _numeric_density(table: list) -> float:
    """Fraction of non-header cells that contain numbers."""
    total = 0
    numeric = 0
    for row in table[1:]:  # skip header
        for cell in row:
            if cell is not None and str(cell).strip():
                total += 1
                if re.search(r"\d", str(cell)):
                    numeric += 1
    return (numeric / total) if total > 0 else 0.0


def _data_row_count(table: list) -> int:
    """Count rows with at least 2 non-None, non-empty cells."""
    count = 0
    for row in table[1:]:
        non_empty = sum(1 for c in row if c is not None and str(c).strip())
        if non_empty >= 2:
            count += 1
    return count


def validate_table(
    table: list,
    doc_type: str,
    page_text: str = "",
    min_columns: int = 2,
    min_data_rows: int = 1,
) -> Tuple[bool, float, str]:
    """
    Validates whether a table is a meaningful data table for the given document type.

    Returns:
        (is_valid: bool, confidence: float, reason: str)

    Confidence > 0.5 → accept; < 0.5 → reject.
    """
    if not table or len(table) < 2:
        return False, 0.0, "Table is empty or has only a header row"

    if len(table[0]) < min_columns:
        return False, 0.0, f"Table has fewer than {min_columns} columns"

    headers = _headers_from_row(table[0])

    # Structural rejection: headers that look like IDs or dates
    for h in headers:
        if _has_reject_pattern(h):
            return False, 0.1, f"Header '{h}' matches rejection pattern (looks like ID/date)"

    # Metadata table rejection
    if _is_metadata_heavy(headers):
        return False, 0.15, "Table appears to be a metadata block, not a data table"

    # Data row count
    data_rows = _data_row_count(table)
    if data_rows < min_data_rows:
        return False, 0.2, f"Table has fewer than {min_data_rows} data rows ({data_rows} found)"

    # Master data types: always accept if min structure is met
    if doc_type in {
        "SUPPLIER_MASTER", "FACILITY_PLANT", "MATERIAL_CONSUMPTION",
        "FUEL_CONSUMPTION", "ELECTRICITY_GRID", "CBAM_PRODUCT_MAPPING",
        "PURCHASE_ORDER",
    }:
        return True, 0.90, f"Master/reference data table accepted for {doc_type}"

    # Numeric density check
    num_density = _numeric_density(table)

    # Build semantic score based on doc_type
    confidence = 0.0

    if doc_type in {"TRANSPORTATION_INVOICE", "SHIPPING_MANIFEST", "BILL_OF_LADING", "LOGISTICS_SHIPPING"}:
        hits = _count_keyword_hits(headers, _TRANSPORT_HEADER_KEYWORDS)
        shipping_hits = _count_keyword_hits(headers, _SHIPPING_HEADER_KEYWORDS)
        best_hits = max(hits, shipping_hits)
        n_cols = len(headers)

        if best_hits >= 3:
            confidence = 0.85 + min(0.10, (best_hits - 3) * 0.02)
        elif best_hits == 2:
            confidence = 0.70
        elif best_hits == 1:
            confidence = 0.55
        else:
            # No keyword hits but check numeric density — a distance/weight table
            if num_density > 0.4 and n_cols >= 4:
                confidence = 0.55
            else:
                return False, 0.25, f"Transport table has no recognizable transport headers ({best_hits} hits)"

    elif doc_type in {"PURCHASE_INVOICE", "MATERIAL_CONSUMPTION"}:
        hits = _count_keyword_hits(headers, _INVOICE_HEADER_KEYWORDS)
        if hits >= 3:
            confidence = 0.85 + min(0.10, (hits - 3) * 0.02)
        elif hits == 2:
            confidence = 0.70
        elif hits == 1:
            # Accept if numeric density is significant
            confidence = 0.55 if num_density > 0.3 else 0.35

    elif doc_type in {"ELECTRICITY_BILL", "UTILITY_BILL"}:
        hits = _count_keyword_hits(headers, _UTILITY_HEADER_KEYWORDS)
        if hits >= 2:
            confidence = 0.80
        elif hits >= 1:
            confidence = 0.60

    elif doc_type in {"FUEL_INVOICE"}:
        fuel_terms = {"fuel", "diesel", "petrol", "lpg", "litre", "liter", "gallon", "quantity", "consumption"}
        hits = _count_keyword_hits(headers, fuel_terms | _INVOICE_HEADER_KEYWORDS)
        confidence = min(0.90, 0.55 + hits * 0.10)

    elif doc_type in {"CBAM_PRODUCT_MAPPING"}:
        hits = _count_keyword_hits(headers, _CBAM_HEADER_KEYWORDS)
        confidence = min(0.90, 0.55 + hits * 0.10)

    else:
        # Generic: any table with reasonable structure
        hits = _count_keyword_hits(headers, _INVOICE_HEADER_KEYWORDS | _UTILITY_HEADER_KEYWORDS)
        if hits >= 2:
            confidence = 0.65
        elif hits == 1 or num_density > 0.3:
            confidence = 0.55

    # Numeric density bonus
    if num_density > 0.5 and confidence > 0.40:
        confidence = min(0.95, confidence + 0.05)

    is_valid = confidence >= 0.50
    reason = (
        f"{'Accepted' if is_valid else 'Rejected'}: "
        f"doc_type={doc_type}, columns={len(headers)}, data_rows={data_rows}, "
        f"num_density={num_density:.2f}, confidence={confidence:.2f}"
    )
    return is_valid, confidence, reason
