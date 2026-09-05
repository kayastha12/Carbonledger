"""
CarbonLedger Duplicate Detector
================================
Semantically-aware duplicate detection for CarbonActivityRecord objects.

DESIGN PRINCIPLES:
- A record must NOT be considered a duplicate merely because several fields are null.
- Records are deduplicated only when strong identity fields match.
- Transportation records: origin + destination + distance + weight + mode must all match.
- Purchased goods: invoice_number + supplier + material + quantity + unit must all match.
- If identity confidence is too low, record is flagged as UNCERTAIN (not deleted).
- Raw counts are reported: exact, near, uncertain, legitimate_similar.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any


# Minimum number of non-None identity fields required to make an exact-duplicate claim.
MIN_IDENTITY_FIELDS_FOR_EXACT = 3


@dataclass
class DeduplicationResult:
    unique_records: List[dict] = field(default_factory=list)
    exact_duplicates_removed: int = 0
    near_duplicates: int = 0
    uncertain_duplicates: int = 0
    legitimate_similar_records: int = 0
    suppressed_reasons: List[dict] = field(default_factory=list)


def _safe_str(val: Any) -> str:
    """Convert a value to a canonical string for fingerprinting."""
    if val is None:
        return "__NULL__"
    if isinstance(val, float):
        # Normalise floats: 7242.5 and 7242.500 must be the same
        return f"{val:.6f}"
    return str(val).strip().lower()


def _count_non_null(parts: List[str]) -> int:
    return sum(1 for p in parts if p != "__NULL__")


def _make_fingerprint(parts: List[str]) -> str:
    m = hashlib.sha256()
    m.update("|".join(parts).encode("utf-8"))
    return m.hexdigest()


def _build_fingerprint_purchased(r: dict) -> Tuple[str, int, List[str]]:
    """
    Identity fields for PURCHASED_GOODS / PURCHASE_ORDER / MATERIAL_CONSUMPTION / CBAM_PRODUCT.
    Priority: invoice_number > supplier > date > material > quantity > unit > amount
    """
    act = r.get("activity", {})
    sup = r.get("supplier", {})
    fin = r.get("financial", {})

    parts = [
        _safe_str(r.get("_invoice_number")),
        _safe_str(sup.get("name")),
        _safe_str(r.get("_invoice_date") or act.get("period_start")),
        _safe_str(act.get("material") or act.get("product") or r.get("_material")),
        _safe_str(act.get("quantity") or r.get("_quantity")),
        _safe_str(act.get("unit") or r.get("_unit")),
        _safe_str(fin.get("amount")),
    ]
    return _make_fingerprint(parts), _count_non_null(parts), parts


def _build_fingerprint_fuel(r: dict) -> Tuple[str, int, List[str]]:
    """
    Identity for FUEL_CONSUMPTION: fuel_type + quantity + unit + date + facility
    """
    act = r.get("activity", {})
    company = r.get("company", {})

    parts = [
        _safe_str(act.get("fuel_type")),
        _safe_str(act.get("quantity") or act.get("consumption")),
        _safe_str(act.get("unit") or act.get("consumption_unit")),
        _safe_str(act.get("period_start")),
        _safe_str(company.get("facility") or act.get("grid_region")),
    ]
    return _make_fingerprint(parts), _count_non_null(parts), parts


def _build_fingerprint_electricity(r: dict) -> Tuple[str, int, List[str]]:
    """
    Identity for ELECTRICITY_CONSUMPTION: consumption + unit + period + grid_region
    """
    act = r.get("activity", {})
    company = r.get("company", {})

    parts = [
        _safe_str(act.get("consumption")),
        _safe_str(act.get("consumption_unit")),
        _safe_str(act.get("period_start")),
        _safe_str(act.get("period_end")),
        _safe_str(company.get("facility") or act.get("grid_region") or act.get("country")),
    ]
    return _make_fingerprint(parts), _count_non_null(parts), parts


def _build_fingerprint_transport(r: dict) -> Tuple[str, int, List[str]]:
    """
    Identity for TRANSPORTATION / SHIPPING:
    origin + destination + mode + distance + weight MUST all match for exact duplicate.
    Different quantities (weight) must remain separate transactions.
    """
    act = r.get("activity", {})

    parts = [
        _safe_str(act.get("origin")),
        _safe_str(act.get("destination")),
        _safe_str(act.get("transport_mode")),
        _safe_str(act.get("distance")),
        _safe_str(act.get("weight")),
        _safe_str(act.get("period_start")),
    ]
    return _make_fingerprint(parts), _count_non_null(parts), parts


def _build_fingerprint_generic(r: dict) -> Tuple[str, int, List[str]]:
    """Fallback fingerprint for OTHER activity types."""
    act = r.get("activity", {})
    sup = r.get("supplier", {})

    parts = [
        _safe_str(act.get("activity_type")),
        _safe_str(sup.get("name")),
        _safe_str(act.get("quantity") or act.get("consumption")),
        _safe_str(act.get("unit") or act.get("consumption_unit")),
        _safe_str(act.get("period_start")),
    ]
    return _make_fingerprint(parts), _count_non_null(parts), parts


def _get_fingerprint(r: dict) -> Tuple[str, int, str, List[str]]:
    """
    Returns (fingerprint_hex, non_null_count, category, parts_list).
    category is used to decide what threshold to apply.
    """
    act = r.get("activity", {})
    act_type = str(act.get("activity_type", "")).upper()

    if act_type in ("PURCHASED_GOODS", "PURCHASE_ORDER", "MATERIAL_CONSUMPTION", "CBAM_PRODUCT"):
        fp, count, parts = _build_fingerprint_purchased(r)
        return fp, count, "PURCHASED", parts
    elif act_type == "FUEL_CONSUMPTION":
        fp, count, parts = _build_fingerprint_fuel(r)
        return fp, count, "FUEL", parts
    elif act_type in ("ELECTRICITY_CONSUMPTION", "NATURAL_GAS_CONSUMPTION", "STEAM_CONSUMPTION"):
        fp, count, parts = _build_fingerprint_electricity(r)
        return fp, count, "ENERGY", parts
    elif act_type in ("TRANSPORTATION", "SHIPPING"):
        fp, count, parts = _build_fingerprint_transport(r)
        return fp, count, "TRANSPORT", parts
    else:
        fp, count, parts = _build_fingerprint_generic(r)
        return fp, count, "GENERIC", parts


def deduplicate_records(records: List[dict]) -> DeduplicationResult:
    """
    Deduplicates a list of CarbonActivityRecord dicts.

    Logic:
    1. Compute fingerprint for each record using strong identity fields.
    2. If fingerprint is seen AND non-null field count >= MIN_IDENTITY_FIELDS_FOR_EXACT → exact duplicate.
    3. If fingerprint is seen AND non-null count < MIN_IDENTITY_FIELDS_FOR_EXACT → uncertain (retain, flag).
    4. Never remove a record that has unique identity information.
    5. Record all decisions for audit transparency.
    """
    result = DeduplicationResult()
    seen_fingerprints: Dict[str, dict] = {}  # fingerprint → first record meta

    for idx, r in enumerate(records):
        fp, non_null_count, category, parts = _get_fingerprint(r)

        r_annotated = dict(r)
        r_annotated["_duplicate_status"] = "UNIQUE"
        r_annotated["_duplicate_fingerprint"] = fp
        r_annotated["_duplicate_identity_fields"] = non_null_count
        r_annotated["_duplicate_category"] = category

        if fp not in seen_fingerprints:
            seen_fingerprints[fp] = {
                "record_index": idx,
                "non_null_count": non_null_count,
                "category": category
            }
            result.unique_records.append(r_annotated)
        else:
            first = seen_fingerprints[fp]
            if non_null_count >= MIN_IDENTITY_FIELDS_FOR_EXACT:
                # Strong evidence this is a true duplicate
                result.exact_duplicates_removed += 1
                r_annotated["_duplicate_status"] = "EXACT_DUPLICATE"
                result.suppressed_reasons.append({
                    "record_index": idx,
                    "status": "EXACT_DUPLICATE",
                    "fingerprint": fp,
                    "identity_fields_matched": non_null_count,
                    "reason": f"Exact match on {non_null_count} identity fields with record index {first['record_index']}",
                    "parts": parts
                })
            else:
                # Too few non-null fields to be confident — retain but flag
                result.uncertain_duplicates += 1
                r_annotated["_duplicate_status"] = "UNCERTAIN"
                result.unique_records.append(r_annotated)
                result.suppressed_reasons.append({
                    "record_index": idx,
                    "status": "UNCERTAIN",
                    "fingerprint": fp,
                    "identity_fields_matched": non_null_count,
                    "reason": f"Fingerprint collision with only {non_null_count} non-null fields — retained",
                    "parts": parts
                })

    return result
