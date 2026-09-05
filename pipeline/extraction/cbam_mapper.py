"""
CarbonLedger CBAM Mapper
=========================
Centralized CBAM applicability logic and record construction.

CBAM applicability is product/import/category dependent — NOT scope-based.
A transportation record should be NOT_APPLICABLE unless it carries CBAM product data.
"""

from typing import Dict, Any, Optional, Tuple, List


# CBAM sectors per EU Regulation 2023/956 (iron/steel, aluminium, cement, fertilisers,
# electricity, hydrogen). We tag known activity types as their default CBAM stance.
_CBAM_APPLICABLE_ACTIVITY_TYPES = {
    "PURCHASED_GOODS",
    "PURCHASE_ORDER",
    "MATERIAL_CONSUMPTION",
    "CBAM_PRODUCT",
}

_CBAM_NOT_APPLICABLE_ACTIVITY_TYPES = {
    "TRANSPORTATION",
    "SHIPPING",
    "FUEL_CONSUMPTION",
    "FACILITY_ACTIVITY",
    # electricity is CBAM-applicable but only when imported from non-EEA;
    # domestic grid electricity is NOT_APPLICABLE. Default to NOT_APPLICABLE for now.
    "ELECTRICITY_CONSUMPTION",
    "NATURAL_GAS_CONSUMPTION",
    "STEAM_CONSUMPTION",
    "OTHER",
}

# CBAM product categories — materials that are typically CBAM-relevant
_CBAM_RELEVANT_MATERIALS = {
    "steel", "iron", "stainless steel", "alloy steel", "galvanised steel",
    "aluminium", "aluminum", "aluminium alloy",
    "cement", "clinker", "concrete",
    "fertiliser", "fertilizer", "ammonia", "urea", "nitric acid",
    "hydrogen",
    "electricity",  # when imported cross-border
    "cast iron", "pig iron", "sponge iron", "dri", "hot briquetted iron",
}


def is_cbam_applicable(activity_type: str) -> bool:
    """
    Returns True if the activity type is in a CBAM-applicable category by default.
    This is a coarse check — further product-level check is done in assess_cbam_status().
    """
    return activity_type.upper() in _CBAM_APPLICABLE_ACTIVITY_TYPES


def _has_meaningful_cbam_field(cbam: dict) -> bool:
    """Returns True if at least one CBAM data field has a real value."""
    meaningful_fields = [
        "cn_code", "hs_code", "hsn_code", "commodity_code",
        "country_of_origin", "country_of_production",
        "net_mass", "gross_mass",
        "direct_emissions", "indirect_emissions", "embedded_emissions",
        "production_facility", "installation",
        "supplier_declared_emissions",
        "production_route", "manufacturing_process",
    ]
    for f in meaningful_fields:
        v = cbam.get(f)
        if v is not None and str(v).strip().lower() not in ("", "none", "null"):
            return True
    return False


def _material_is_cbam_relevant(material: Optional[str]) -> bool:
    """Check if extracted material is in CBAM-relevant categories."""
    if not material:
        return False
    mat_lower = str(material).lower().strip()
    for kw in _CBAM_RELEVANT_MATERIALS:
        if kw in mat_lower:
            return True
    return False


def assess_cbam_status(
    activity_type: str,
    cbam: dict,
    material: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """
    Determines CBAM status and returns (cbam_status, missing_cbam_fields).

    CBAM Status values:
      NOT_APPLICABLE        — activity type is not CBAM-relevant
      POTENTIALLY_APPLICABLE — material is CBAM-relevant but no CBAM data present
      DATA_INCOMPLETE       — CBAM is applicable, some fields present, some missing
      READY                 — minimum CBAM fields are present
      REVIEW_REQUIRED       — CBAM applicable but key fields are missing
    """
    act_upper = activity_type.upper()

    # Hard NOT_APPLICABLE
    if act_upper in _CBAM_NOT_APPLICABLE_ACTIVITY_TYPES:
        # Exception: even a transport record could carry product CBAM data
        if _has_meaningful_cbam_field(cbam):
            # Has CBAM data attached (e.g. B/L with HS code) — review rather than ignore
            return "REVIEW_REQUIRED", []
        return "NOT_APPLICABLE", []

    # For PURCHASED_GOODS / PURCHASE_ORDER etc.
    if act_upper in _CBAM_APPLICABLE_ACTIVITY_TYPES:
        has_data = _has_meaningful_cbam_field(cbam)
        mat_relevant = _material_is_cbam_relevant(material)

        if not has_data and not mat_relevant:
            # No evidence either way — potentially applicable but unclear
            return "POTENTIALLY_APPLICABLE", []

        if not has_data and mat_relevant:
            # Material is CBAM-relevant but no CBAM data was extracted
            return "DATA_INCOMPLETE", ["cn_code", "country_of_origin", "net_mass", "embedded_emissions"]

        # Has some CBAM data — assess completeness
        required_fields = ["cn_code", "country_of_origin", "net_mass"]
        missing = []
        for f in required_fields:
            v = cbam.get(f)
            if v is None or str(v).strip().lower() in ("", "none", "null"):
                missing.append(f)

        if not missing:
            return "READY", []
        elif len(missing) == len(required_fields):
            return "REVIEW_REQUIRED", missing
        else:
            return "DATA_INCOMPLETE", missing

    # Unknown activity type — check if CBAM data present
    if _has_meaningful_cbam_field(cbam):
        return "REVIEW_REQUIRED", []
    return "POTENTIALLY_APPLICABLE", []


def build_cbam_record(raw_record: dict, material: Optional[str] = None) -> dict:
    """
    Extracts all CBAM-relevant fields from a raw record dict into a clean CBAM sub-record.
    Returns None values for fields not found in the document.
    """
    def _get(*keys):
        for k in keys:
            v = raw_record.get(k)
            if v is not None and str(v).strip().lower() not in ("", "none", "null"):
                return v
        return None

    cbam = {
        # Codes
        "cn_code": _get("cn_code", "cn code", "combined_nomenclature"),
        "hs_code": _get("hs_code", "hs code"),
        "hsn_code": _get("hsn_code", "hsn code", "hsn sac", "hsn/sac"),
        "commodity_code": _get("commodity_code", "tariff_heading", "tariff code", "customs code"),

        # Product
        "product_description": _get("product_description", "description", "goods", "material", "product"),
        "material": material or _get("material", "product_name", "goods"),
        "product_category": _get("product_category", "category"),

        # Origin / trade
        "country_of_origin": _get("country_of_origin", "origin_country", "country of origin"),
        "country_of_production": _get("country_of_production"),
        "country_of_dispatch": _get("country_of_dispatch"),
        "country_of_destination": _get("country_of_destination", "destination_country"),
        "export_country": _get("export_country"),
        "import_country": _get("import_country"),

        # Parties
        "supplier": _get("supplier", "supplier_name", "vendor", "seller", "exporter"),
        "producer": _get("producer", "manufacturer"),
        "installation": _get("installation"),
        "production_facility": _get("production_facility", "facility", "plant_name", "manufacturing_facility"),

        # Mass
        "net_mass": _parse_float(_get("net_mass", "net_weight", "net wt", "net_wt")),
        "gross_mass": _parse_float(_get("gross_mass", "gross_weight", "gross wt", "gross_wt")),
        "quantity": None,  # populated by caller
        "unit": None,      # populated by caller

        # Emissions
        "direct_emissions": _parse_float(_get("direct_emissions", "direct emissions")),
        "indirect_emissions": _parse_float(_get("indirect_emissions", "indirect emissions")),
        "embedded_emissions": _parse_float(_get("embedded_emissions", "embedded emissions", "total_embedded_emissions")),
        "specific_embedded_emissions": _parse_float(_get("specific_embedded_emissions")),
        "total_embedded_emissions": _parse_float(_get("total_embedded_emissions")),
        "co2": _parse_float(_get("co2")),
        "co2e": _parse_float(_get("co2e")),
        "ghg": _parse_float(_get("ghg")),

        # Emission factors
        "emission_factor": _parse_float(_get("emission_factor", "ef")),
        "emission_factor_source": _get("emission_factor_source"),

        # Production
        "production_route": _get("production_route", "manufacturing process", "process type"),
        "manufacturing_process": _get("manufacturing_process", "manufacturing process"),
        "process_type": _get("process_type", "process type"),
        "precursor_material": _get("precursor_material"),
        "precursor_quantity": _parse_float(_get("precursor_quantity")),

        # Electricity
        "electricity_consumed": _parse_float(_get("electricity_consumed")),
        "electricity_source": _get("electricity_source"),
        "electricity_mix": _get("electricity_mix"),
        "grid_factor": _parse_float(_get("grid_factor")),
        "renewable_electricity": _parse_float(_get("renewable_electricity")),

        # Declarations
        "supplier_declared_emissions": _parse_float(_get("supplier_declared_emissions", "supplier declared emissions")),
        "methodology": _get("methodology"),
        "reporting_period": _get("reporting_period", "period"),
        "verification_status": _get("verification_status", "verification status"),
        "verification_body": _get("verification_body", "verification body"),
        "calculation_method": _get("calculation_method"),
        "declaration_date": _get("declaration_date"),
    }

    return cbam


def _parse_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def check_cbam_readiness(cbam: dict) -> Tuple[float, List[str], Dict[str, str]]:
    """
    Checks the completeness of a CBAM record across standard category groups.
    Returns (completeness_pct, missing_field_list, category_status_dict).
    """
    categories = {
        "Product identification": ["cn_code", "hs_code", "hsn_code", "commodity_code", "product_description", "material"],
        "Origin and trade": ["country_of_origin", "supplier", "producer"],
        "Quantity": ["net_mass", "gross_mass", "quantity"],
        "Embedded emissions": ["embedded_emissions", "direct_emissions", "indirect_emissions", "co2e", "co2"],
        "Production information": ["production_facility", "installation", "production_route", "manufacturing_process"],
        "Electricity": ["electricity_consumed", "electricity_source"],
        "Supplier declarations": ["supplier_declared_emissions", "verification_status"],
    }

    status = {}
    missing_fields = []
    complete_count = 0

    for cat, fields in categories.items():
        is_complete = False
        for f in fields:
            val = cbam.get(f)
            if val is not None and str(val).strip().lower() not in ("", "none", "null"):
                is_complete = True
                break
        if is_complete:
            status[cat] = "COMPLETE"
            complete_count += 1
        else:
            status[cat] = "MISSING"
            missing_fields.append(fields[0])

    completeness = round((complete_count / len(categories)) * 100.0, 1)
    return completeness, missing_fields, status
