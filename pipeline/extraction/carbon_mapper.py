import re
import json
from typing import Dict, Any, List, Tuple, Optional
from pipeline.normalization import NormalizationEngine
from pipeline.extraction.cbam_mapper import (
    assess_cbam_status,
    build_cbam_record,
    check_cbam_readiness,
    is_cbam_applicable,
)
from pipeline.extraction.emission_factor_provider import EmissionFactorProvider

class CarbonMapper:
    def __init__(self):
        self.normalizer = NormalizationEngine()
        self.ef_provider = EmissionFactorProvider()
        self.supplier_dir = {}   # supplier_name.lower() -> {supplier_id, country, city}
        self.facility_dir = {}   # plant_name.lower() -> {facility_id, location}
        self.product_dir = {}    # product_name.lower() -> {product_id, hs_code, cn_code, category}

    def build_lookups_from_pdf(self, pdf_obj, parsed_doc) -> None:
        """
        Parses all tables across all pages in the PDF to populate lookup directories for data consistency.
        """
        if not pdf_obj:
            return
            
        # We scan all pages to find tables that belong to master data:
        # Phase 3 (Supplier Master), Phase 6 (Facility & Plant), Phase 10 (CBAM Product Mapping)
        for page_idx, page in enumerate(pdf_obj.pages):
            page_text = page.extract_text() or ""
            text_low = page_text.lower()
            
            tables = page.extract_tables() or []
            for t in tables:
                if len(t) < 2 or len(t[0]) < 3:
                    continue
                    
                headers = [str(h).lower().strip() for h in t[0] if h is not None]
                
                # Check if it's Supplier Master
                if "supplier id" in headers or "supplier name" in headers or "supplier master" in text_low:
                    # Map columns
                    name_idx = -1
                    id_idx = -1
                    country_idx = -1
                    city_idx = -1
                    for col_idx, h in enumerate(t[0]):
                        if not h:
                            continue
                        h_clean = str(h).lower().strip()
                        if "supplier name" in h_clean or h_clean == "supplier":
                            name_idx = col_idx
                        elif "supplier id" in h_clean:
                            id_idx = col_idx
                        elif "country" in h_clean:
                            country_idx = col_idx
                        elif "city" in h_clean:
                            city_idx = col_idx
                            
                    for row in t[1:]:
                        if name_idx < len(row) and row[name_idx]:
                            s_name = str(row[name_idx]).strip()
                            s_id = str(row[id_idx]).strip() if (id_idx < len(row) and row[id_idx]) else None
                            s_country = str(row[country_idx]).strip() if (country_idx < len(row) and row[country_idx]) else None
                            s_city = str(row[city_idx]).strip() if (city_idx < len(row) and row[city_idx]) else None
                            self.supplier_dir[s_name.lower()] = {
                                "supplier_id": s_id,
                                "country": s_country,
                                "city": s_city
                            }
                            
                # Check if Facility & Plant
                elif "plant id" in headers or "plant name" in headers or "facility & plant" in text_low:
                    name_idx = -1
                    id_idx = -1
                    loc_idx = -1
                    for col_idx, h in enumerate(t[0]):
                        if not h:
                            continue
                        h_clean = str(h).lower().strip()
                        if "plant name" in h_clean or "facility" in h_clean:
                            name_idx = col_idx
                        elif "plant id" in h_clean or "facility id" in h_clean:
                            id_idx = col_idx
                        elif "location" in h_clean or "city" in h_clean:
                            loc_idx = col_idx
                            
                    for row in t[1:]:
                        if name_idx < len(row) and row[name_idx]:
                            f_name = str(row[name_idx]).strip()
                            f_id = str(row[id_idx]).strip() if (id_idx < len(row) and row[id_idx]) else None
                            f_loc = str(row[loc_idx]).strip() if (loc_idx < len(row) and row[loc_idx]) else None
                            self.facility_dir[f_name.lower()] = {
                                "facility_id": f_id,
                                "location": f_loc
                            }
                            
                # Check if CBAM Product Mapping
                elif "product id" in headers or "hs code" in headers or "cbam product" in text_low:
                    id_idx = -1
                    hs_idx = -1
                    cn_idx = -1
                    name_idx = -1
                    cat_idx = -1
                    for col_idx, h in enumerate(t[0]):
                        if not h:
                            continue
                        h_clean = str(h).lower().strip()
                        if "product id" in h_clean:
                            id_idx = col_idx
                        elif "hs code" in h_clean:
                            hs_idx = col_idx
                        elif "cn code" in h_clean:
                            cn_idx = col_idx
                        elif "product name" in h_clean or "product" in h_clean:
                            name_idx = col_idx
                        elif "category" in h_clean:
                            cat_idx = col_idx
                            
                    for row in t[1:]:
                        if name_idx < len(row) and row[name_idx]:
                            p_name = str(row[name_idx]).strip()
                            p_id = str(row[id_idx]).strip() if (id_idx < len(row) and row[id_idx]) else None
                            hs = str(row[hs_idx]).strip() if (hs_idx < len(row) and row[hs_idx]) else None
                            cn = str(row[cn_idx]).strip() if (cn_idx < len(row) and row[cn_idx]) else None
                            cat = str(row[cat_idx]).strip() if (cat_idx < len(row) and row[cat_idx]) else None
                            self.product_dir[p_name.lower()] = {
                                "product_id": p_id,
                                "hs_code": hs,
                                "cn_code": cn,
                                "category": cat
                            }

    def normalize_unit_canonical(self, unit_str: str) -> Optional[str]:
        if not unit_str:
            return None
        norm = self.normalizer.normalize_unit(unit_str)
        if norm:
            if norm == "liter":
                return "L"
            return norm
        return unit_str

    def normalize_value_and_unit(self, val: Any, unit_str: Any) -> dict:
        raw_val = None
        if val is not None:
            try:
                raw_val = float(str(val).replace(",", "").strip())
            except ValueError:
                pass
                
        raw_unit = str(unit_str).strip() if unit_str else None
        norm_unit = self.normalize_unit_canonical(raw_unit) if raw_unit else None
        norm_val = raw_val
        
        conversion_applied = False
        conversion_reason = None
        
        if norm_unit and raw_unit and norm_unit.lower() != raw_unit.lower():
            conversion_applied = True
            conversion_reason = f"Normalized unit from '{raw_unit}' to canonical '{norm_unit}'"
            
        return {
            "raw_value": raw_val,
            "raw_unit": raw_unit,
            "normalized_value": norm_val,
            "normalized_unit": norm_unit,
            "conversion_applied": conversion_applied,
            "conversion_reason": conversion_reason
        }

    def check_cbam_readiness(self, cbam: dict) -> Tuple[float, List[str], Dict[str, str]]:
        # Delegate to centralized cbam_mapper module
        return check_cbam_readiness(cbam)

    def normalize_date_enhanced(self, date_str: str) -> Optional[str]:
        if not date_str:
            return None
        cleaned = date_str.replace("-\n", "-").replace("\n", " ").strip()
        
        # Format 1: YYYY-MM-DD
        match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", cleaned)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
            
        # Format 2: YYYY-MM (e.g. 2025-01)
        match = re.search(r"(\d{4})[-/](\d{1,2})", cleaned)
        if match:
            # check that it's not part of YYYY-MM-DD
            if not re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", cleaned):
                return f"{match.group(1)}-{int(match.group(2)):02d}"
                
        # Format 3: Month YYYY (e.g. Jan 2025, January 2025)
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        month_pattern = r"\b(" + "|".join(months) + r")[a-z]*"
        
        match = re.search(month_pattern + r"\s*[-/]?\s*(\d{4})", cleaned, re.IGNORECASE)
        if match:
            m_idx = months.index(match.group(1).lower()[:3]) + 1
            return f"{match.group(2)}-{m_idx:02d}"
            
        match = re.search(r"(\d{4})\s*[-/]?\s*" + month_pattern, cleaned, re.IGNORECASE)
        if match:
            m_idx = months.index(match.group(2).lower()[:3]) + 1
            return f"{match.group(1)}-{m_idx:02d}"
            
        # Fallback to standard
        audit = self.normalizer.normalize_date(cleaned)
        if audit.get("normalized_value"):
            return audit["normalized_value"]
            
        return cleaned

    def extract_company_info(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        company_name = None
        company_id = None
        
        # Search for Company Name
        match = re.search(r"Company\s*:\s*([^\n|]+)", text, re.IGNORECASE)
        if match:
            company_name = match.group(1).strip()
            
        # Search for Company ID
        match_id = re.search(r"Company\s+ID\s*:\s*([^\n|]+)", text, re.IGNORECASE)
        if not match_id:
            match_id = re.search(r"\bID\s*:\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if match_id:
            company_id = match_id.group(1).strip()
            
        return company_name, company_id

    def classify_activity(self, doc_type: str, raw_record: dict, text: str) -> Tuple[str, str, str]:
        # returns (activity_type, scope, category)
        val_str = json.dumps(raw_record).lower() + " " + text.lower()
        
        # 1. Document type direct matching
        if doc_type in ["TRANSPORTATION_INVOICE", "SHIPPING_MANIFEST", "BILL_OF_LADING", "LOGISTICS_SHIPPING"]:
            return "TRANSPORTATION", "SCOPE_3", "TRANSPORT"
        elif doc_type in ["ELECTRICITY_BILL", "ELECTRICITY_GRID", "UTILITY_BILL"]:
            ut = str(raw_record.get("utility_type") or "").lower()
            if "gas" in ut or "natural gas" in ut:
                return "NATURAL_GAS_CONSUMPTION", "SCOPE_1", "ENERGY"
            elif "steam" in ut:
                return "STEAM_CONSUMPTION", "SCOPE_2", "ENERGY"
            return "ELECTRICITY_CONSUMPTION", "SCOPE_2", "ENERGY"
        elif doc_type in ["FUEL_INVOICE", "FUEL_CONSUMPTION"]:
            return "FUEL_CONSUMPTION", "SCOPE_1", "FUEL"
        elif doc_type == "FACILITY_PLANT":
            return "FACILITY_ACTIVITY", "SCOPE_1", "FACILITY"
        elif doc_type == "CBAM_PRODUCT_MAPPING":
            return "CBAM_PRODUCT", "SCOPE_3", "MATERIAL"
        elif doc_type == "PURCHASE_ORDER":
            return "PURCHASE_ORDER", "SCOPE_3", "MATERIAL"
            
        # 2. Text keyword matching for other/mixed cases
        if any(f in val_str for f in ["diesel", "petrol", "lpg", "fuel id", "fuel type", "fuel_type"]) and "distance" not in val_str:
            return "FUEL_CONSUMPTION", "SCOPE_1", "FUEL"
        if any(e in val_str for e in ["electricity", "kwh", "grid id", "electricity grid"]):
            return "ELECTRICITY_CONSUMPTION", "SCOPE_2", "ENERGY"
        if "natural gas" in val_str:
            return "NATURAL_GAS_CONSUMPTION", "SCOPE_1", "ENERGY"
        if "steam" in val_str:
            return "STEAM_CONSUMPTION", "SCOPE_2", "ENERGY"
        if any(t in val_str for t in ["truck", "rail", "distance", "origin", "destination", "transport"]):
            return "TRANSPORTATION", "SCOPE_3", "TRANSPORT"
        if any(m in val_str for m in ["steel", "aluminium", "aluminum", "plastic", "purchase invoice", "purchase order", "material id", "hs code"]):
            if "purchase order" in val_str or doc_type == "PURCHASE_ORDER":
                return "PURCHASE_ORDER", "SCOPE_3", "MATERIAL"
            return "PURCHASED_GOODS", "SCOPE_3", "MATERIAL"
            
        # 3. Fallbacks
        if doc_type in ["PURCHASE_INVOICE", "MATERIAL_CONSUMPTION"]:
            return "PURCHASED_GOODS", "SCOPE_3", "MATERIAL"
            
        return "OTHER", "UNKNOWN", "OTHER"

    def check_calculation_ready(self, activity_type: str, act: dict) -> Tuple[bool, List[str]]:
        missing = []
        if activity_type in ["PURCHASED_GOODS", "PURCHASE_ORDER", "MATERIAL_CONSUMPTION", "CBAM_PRODUCT"]:
            if not act.get("material"):
                missing.append("material")
            if act.get("quantity") is None:
                missing.append("quantity")
            if not act.get("unit"):
                missing.append("unit")
        elif activity_type == "FUEL_CONSUMPTION":
            if not act.get("fuel_type"):
                missing.append("fuel_type")
            if act.get("quantity") is None:
                missing.append("quantity")
            if not act.get("unit"):
                missing.append("unit")
        elif activity_type == "ELECTRICITY_CONSUMPTION":
            if act.get("consumption") is None:
                missing.append("consumption")
            c_unit = act.get("consumption_unit")
            if not c_unit:
                missing.append("consumption_unit")
            elif str(c_unit).lower().strip() not in ["kwh", "mwh", "gwh", "wh"]:
                missing.append("valid_consumption_unit (must be kWh/MWh/GWh)")
        elif activity_type in ["NATURAL_GAS_CONSUMPTION", "STEAM_CONSUMPTION"]:
            if act.get("consumption") is None:
                missing.append("consumption")
            c_unit = act.get("consumption_unit")
            if not c_unit:
                missing.append("consumption_unit")
            elif str(c_unit).lower().strip() not in ["m3", "mcm", "scf", "gal", "gallon", "liter", "litre", "l", "kg", "tonne", "ton", "t", "kwh", "mwh", "gwh"]:
                missing.append("valid_consumption_unit")
        elif activity_type in ["TRANSPORTATION", "SHIPPING"]:
            if not act.get("transport_mode"):
                missing.append("transport_mode")
            if act.get("distance") is None:
                missing.append("distance")
            if not act.get("distance_unit"):
                missing.append("distance_unit")
            if act.get("weight") is None:
                missing.append("weight")
            if not act.get("weight_unit"):
                missing.append("weight_unit")
        else:
            if act.get("quantity") is None:
                missing.append("quantity")
            if not act.get("unit"):
                missing.append("unit")
                
        return len(missing) == 0, missing

    def map_to_carbon_record(
        self,
        raw_record: dict,
        doc_id: str,
        doc_type: str,
        page_num: int,
        page_text: str,
        provenance_dict: dict
    ) -> dict:
        """
        Maps a raw extracted record to the standardized CarbonActivityRecord structure.
        """
        # Determine activity category and GHG scope
        act_type, scope, category = self.classify_activity(doc_type, raw_record, page_text)

        # Normalize quantity and units
        raw_qty = raw_record.get("quantity") or raw_record.get("qty") or raw_record.get("consumption")
        raw_unit = raw_record.get("unit") or raw_record.get("consumption_unit")
        
        # Parse quantity numeric value safely
        qty = None
        if raw_qty is not None:
            try:
                qty = float(str(raw_qty).replace(",", "").strip())
            except ValueError:
                pass

        # Clean unit
        unit = self.normalize_unit_canonical(raw_unit) if raw_unit else None

        # RC-07: Do NOT auto-convert kg → tonne.
        # The source document is authoritative. If 1000 kg is stated, store 1000 kg.
        # Downstream calculations must handle unit conversions explicitly.
        # (Conversion audit trail is preserved in unit_normalization_audit)

        # Resolve supplier details
        sup_name = raw_record.get("supplier") or raw_record.get("supplier_name") or raw_record.get("vendor") or raw_record.get("vendor_name")
        sup_id = raw_record.get("supplier_id") or (f"SPL-{hash(sup_name) % 10000:04d}" if sup_name else None)
        sup_country = raw_record.get("supplier_country") or raw_record.get("country") or None
        sup_state = raw_record.get("supplier_state") or raw_record.get("state") or None
        sup_city = raw_record.get("supplier_city") or raw_record.get("city") or None

        # Resolve company details
        c_name = raw_record.get("customer") or raw_record.get("customer_name") or raw_record.get("company_name")
        c_id = raw_record.get("customer_id") or raw_record.get("company_id")

        # Material details mapping
        material_raw = raw_record.get("material") or raw_record.get("product") or raw_record.get("description")
        material_norm = None
        if material_raw:
            material_norm = self.normalizer.normalize_material(material_raw)["normalized_value"]

        # Fuel details mapping
        fuel_raw = raw_record.get("fuel_type") or raw_record.get("fuel")
        fuel_norm = None
        if fuel_raw:
            fuel_norm = self.normalizer.normalize_fuel(fuel_raw)["normalized_value"]

        # Construct activity block
        activity = {
            "activity_type": act_type,
            "scope": scope,
            "category": category,
            "material": material_norm,
            "product": material_raw,
            "quantity": qty if act_type not in ["ELECTRICITY_CONSUMPTION", "NATURAL_GAS_CONSUMPTION", "STEAM_CONSUMPTION"] else None,
            "unit": unit if act_type not in ["ELECTRICITY_CONSUMPTION", "NATURAL_GAS_CONSUMPTION", "STEAM_CONSUMPTION"] else None,
            "fuel_type": fuel_norm,
            "energy_type": "electricity" if act_type == "ELECTRICITY_CONSUMPTION" else (raw_record.get("utility_type") or None),
            "distance": None,
            "distance_unit": None,
            "weight": None,
            "weight_unit": None,
            "origin": raw_record.get("origin") or None,
            "destination": raw_record.get("destination") or None,
            "transport_mode": raw_record.get("transport_mode") or None,
            "consumption": None,
            "consumption_unit": None,
            "period_start": None,
            "period_end": None,
            "country": raw_record.get("country") or None,
            "state": raw_record.get("state") or None,
            "grid_region": raw_record.get("grid_region") or None
        }

        # Date normalization
        date_raw = raw_record.get("date") or raw_record.get("delivery_date") or raw_record.get("period") or raw_record.get("invoice_date")
        date_norm = self.normalize_date_enhanced(date_raw) if date_raw else None
        
        # Populate specific activity structures based on type
        if act_type in ["ELECTRICITY_CONSUMPTION", "NATURAL_GAS_CONSUMPTION", "STEAM_CONSUMPTION"]:
            activity["consumption"] = qty
            activity["consumption_unit"] = unit
            activity["period_start"] = date_norm
            activity["period_end"] = date_norm
        else:
            activity["period_start"] = date_norm
            activity["period_end"] = date_norm

        if act_type in ["TRANSPORTATION", "SHIPPING"]:
            # Parse distance value safely
            dist_val = raw_record.get("distance")
            if dist_val is not None:
                try:
                    activity["distance"] = float(str(dist_val).replace(",", "").strip())
                except ValueError:
                    pass
            activity["distance_unit"] = self.normalize_unit_canonical(raw_record.get("distance_unit")) or "km"
            
            # Parse weight value safely
            w_val = raw_record.get("weight") or qty
            if w_val is not None:
                try:
                    activity["weight"] = float(str(w_val).replace(",", "").strip())
                except ValueError:
                    pass
            activity["weight_unit"] = self.normalize_unit_canonical(raw_record.get("weight_unit")) or unit or "kg"
            activity["transport_mode"] = raw_record.get("transport_mode") or raw_record.get("mode") or raw_record.get("transport mode") or raw_record.get("mode_of_transport") or raw_record.get("shipping_mode")

        # Company record — RC-06: NEVER substitute a hardcoded default company name.
        # If company information does not exist in the document, company.name = null.
        company = {
            "name": c_name or None,
            "company_id": c_id or None,
            "country": raw_record.get("company_country") or None,
            "state": raw_record.get("state") or None,
            "facility": raw_record.get("plant_name") or raw_record.get("facility_id") or None
        }

        # Supplier record
        supplier = {
            "name": sup_name,
            "supplier_id": sup_id,
            "country": sup_country,
            "state": sup_state,
            "city": sup_city
        }

        # Financial details
        amount = raw_record.get("amount") or raw_record.get("total") or raw_record.get("cost")
        if amount is not None:
            if not isinstance(amount, (int, float)):
                try:
                    amount_clean = str(amount).replace(",", "").strip()
                    match = re.search(r"([\d\.]+)", amount_clean)
                    if match:
                        amount = float(match.group(1))
                    else:
                        amount = None
                except Exception:
                    amount = None
                
        financial = {
            "amount": amount,
            "currency": raw_record.get("currency") or None
        }

        # Emission Factor — RC-12: Look up actual emission factor; never fabricate.
        ef = self._lookup_emission_factor(act_type, activity)
        emission_factor = self.ef_provider.to_dict(ef)

        # Activity data readiness (can we describe the activity?)
        activity_data_ready, missing = self.check_calculation_ready(act_type, activity)

        # Emission calculation readiness (do we also have an emission factor?)
        emission_calc_ready = activity_data_ready and ef.status in ("FOUND", "APPROXIMATE")

        carbon_calc = {
            "activity_data_ready": activity_data_ready,
            "calculation_ready": emission_calc_ready,
            "emission_factor_status": ef.status,
            "missing_fields": missing,
        }

        # Validation status
        val_status = "VALID"
        anomalies = []
        if not activity_data_ready:
            val_status = "REVIEW_REQUIRED"
            anomalies.append({
                "type": "MISSING_REQUIRED_FIELDS",
                "field": "multiple",
                "message": f"Required activity fields for {act_type} are missing: {missing}"
            })
        if ef.status == "NOT_FOUND":
            anomalies.append({
                "type": "MISSING_EMISSION_FACTOR",
                "field": "emission_factor",
                "message": f"No emission factor found for {act_type}. Carbon calculation requires manual factor assignment."
            })

        validation = {
            "status": val_status,
            "anomalies": anomalies
        }

        # RC-05: Compute confidence from actual field completeness, not hardcoded 0.98.
        confidence = self._compute_confidence(activity_data_ready, missing, ef, provenance_dict)

        # ── CBAM ── RC-08: Use centralized CBAM mapper; NOT_APPLICABLE for transport/fuel/electricity
        cbam_data = build_cbam_record(raw_record, material=material_norm or raw_record.get("material"))
        # Set quantity/unit from activity (may be used for net_mass in CBAM)
        if act_type not in ["ELECTRICITY_CONSUMPTION", "NATURAL_GAS_CONSUMPTION", "STEAM_CONSUMPTION"]:
            if cbam_data.get("net_mass") is None and cbam_data.get("quantity") is None:
                cbam_data["quantity"] = qty
                cbam_data["unit"] = unit

        cbam_status, missing_cbam = assess_cbam_status(act_type, cbam_data, material=material_norm)
        cbam_data["cbam_status"] = cbam_status

        if cbam_status == "NOT_APPLICABLE":
            # RC-08: Do not run completeness scoring for non-applicable records
            cbam_data["cbam_ready"] = False
            cbam_data["missing_fields"] = []
            cbam_data["cbam_completeness"] = 0.0
            cbam_data["cbam_not_applicable_reason"] = f"Activity type '{act_type}' is not CBAM-applicable."
        else:
            cbam_completeness, missing_cbam_fields, category_status = check_cbam_readiness(cbam_data)
            cbam_data["cbam_ready"] = cbam_completeness >= 40.0
            cbam_data["missing_fields"] = missing_cbam_fields
            cbam_data["cbam_completeness"] = cbam_completeness

        # RC-09: Check if this record has sufficient evidence to emit.
        skip_record, suppression_reason = self._check_minimum_evidence(act_type, activity, cbam_data)
        if skip_record:
            # Return a suppression marker instead of a useless record
            return {
                "_suppressed": True,
                "_suppression_reason": suppression_reason,
                "document_id": doc_id,
                "activity": {"activity_type": act_type, "scope": scope, "category": category},
                "carbon_calculation": {"activity_data_ready": False, "calculation_ready": False,
                                       "emission_factor_status": "NOT_FOUND", "missing_fields": list(missing)},
                "validation": {"status": "SUPPRESSED", "anomalies": [{"type": "INSUFFICIENT_EVIDENCE", "field": "record", "message": suppression_reason}]},
                "cbam": cbam_data,
            }

        dummy_v = None  # placeholder needed to preserve structure below; actual float parsing was already done above
        # Construct unit normalization audit record
        # RC-07: raw values are PRESERVED. Audit records show what the document says.
        unit_normalization_audit = {}
        if raw_qty is not None:
            unit_normalization_audit["quantity"] = self.normalize_value_and_unit(raw_qty, raw_unit)
            # Note: No auto-conversion is applied. raw = normalized.
        if raw_record.get("weight") is not None:
            unit_normalization_audit["weight"] = self.normalize_value_and_unit(raw_record.get("weight"), raw_record.get("weight_unit") or raw_unit)
        if raw_record.get("distance") is not None:
            unit_normalization_audit["distance"] = self.normalize_value_and_unit(raw_record.get("distance"), raw_record.get("distance_unit"))
        if raw_record.get("consumption") is not None:
            unit_normalization_audit["consumption"] = self.normalize_value_and_unit(raw_record.get("consumption"), raw_record.get("consumption_unit"))

        # Build provenance object
        allowed_paths = [
            "company.name",
            "company.company_id",
            "supplier.name",
            "supplier.supplier_id",
            "activity.material",
            "activity.quantity",
            "activity.unit",
            "activity.distance",
            "activity.origin",
            "activity.destination",
            "activity.transport_mode",
            "activity.weight",
            "activity.weight_unit",
            "activity.fuel_type",
            "activity.energy_type",
            "activity.consumption",
            "activity.consumption_unit",
            "activity.period_start",
            "activity.period_end",
            "financial.amount",
            "financial.currency",
            "cbam.cn_code",
            "cbam.hs_code",
            "cbam.hsn_code",
            "cbam.country_of_origin",
            "cbam.embedded_emissions"
        ]

        record_provenance = {}
        for key, prov_val in provenance_dict.items():
            schema_path = None
            key_clean = key.lower().strip()
            if key_clean in allowed_paths:
                schema_path = key_clean
            elif key_clean in ["supplier", "supplier_name", "supplier.name"]:
                schema_path = "supplier.name"
            elif key_clean in ["supplier_id", "supplier.supplier_id"]:
                schema_path = "supplier.supplier_id"
            elif key_clean in ["company", "company_name", "company.name"]:
                schema_path = "company.name"
            elif key_clean in ["company_id", "company.company_id"]:
                schema_path = "company.company_id"
            elif key_clean in ["material", "product", "activity.material"]:
                schema_path = "activity.material"
            elif key_clean in ["quantity", "qty", "activity.quantity"]:
                schema_path = "activity.quantity"
            elif key_clean in ["unit", "activity.unit"]:
                schema_path = "activity.unit"
            elif key_clean in ["distance", "activity.distance"]:
                schema_path = "activity.distance"
            elif key_clean in ["origin", "from", "activity.origin"]:
                schema_path = "activity.origin"
            elif key_clean in ["destination", "to", "activity.destination"]:
                schema_path = "activity.destination"
            elif key_clean in ["transport_mode", "mode", "activity.transport_mode"]:
                schema_path = "activity.transport_mode"
            elif key_clean in ["weight", "activity.weight"]:
                schema_path = "activity.weight"
            elif key_clean in ["weight_unit", "activity.weight_unit"]:
                schema_path = "activity.weight_unit"
            elif key_clean in ["fuel_type", "fuel", "activity.fuel_type"]:
                schema_path = "activity.fuel_type"
            elif key_clean in ["energy_type", "energy", "activity.energy_type"]:
                schema_path = "activity.energy_type"
            elif key_clean in ["consumption", "activity.consumption"]:
                schema_path = "activity.consumption"
            elif key_clean in ["consumption_unit", "activity.consumption_unit"]:
                schema_path = "activity.consumption_unit"
            elif key_clean in ["period_start", "date", "period", "invoice_date", "activity.period_start"]:
                schema_path = "activity.period_start"
            elif key_clean in ["period_end", "activity.period_end"]:
                schema_path = "activity.period_end"
            elif key_clean in ["amount", "total", "cost", "financial.amount"]:
                schema_path = "financial.amount"
            elif key_clean in ["currency", "financial.currency"]:
                schema_path = "financial.currency"
            elif key_clean in ["cn_code", "cn code", "cbam.cn_code"]:
                schema_path = "cbam.cn_code"
            elif key_clean in ["hs_code", "hs code", "cbam.hs_code"]:
                schema_path = "cbam.hs_code"
            elif key_clean in ["hsn_code", "hsn code", "cbam.hsn_code"]:
                schema_path = "cbam.hsn_code"
            elif key_clean in ["country_of_origin", "country of origin", "cbam.country_of_origin"]:
                schema_path = "cbam.country_of_origin"
            elif key_clean in ["embedded_emissions", "embedded emissions", "cbam.embedded_emissions"]:
                schema_path = "cbam.embedded_emissions"
                
            if schema_path and schema_path in allowed_paths:
                conv_applied = False
                audit_ref = unit_normalization_audit.get("quantity") or unit_normalization_audit.get("weight") or unit_normalization_audit.get("distance") or unit_normalization_audit.get("consumption")
                if audit_ref:
                    conv_applied = audit_ref.get("conversion_applied", False)
                    
                record_provenance[schema_path] = {
                    "page": prov_val.get("page", page_num),
                    "raw_text": prov_val.get("raw_text") or str(prov_val.get("value")),
                    "bbox": prov_val.get("bbox") or [0, 0, 0, 0],
                    "source": prov_val.get("source", "PDF_TEXT"),
                    "confidence": prov_val.get("confidence", 0.95),
                    "ocr_confidence": prov_val.get("ocr_confidence") or prov_val.get("confidence", 0.95),
                    "extraction_confidence": prov_val.get("extraction_confidence") or prov_val.get("confidence", 0.95),
                    "mapping_confidence": 0.95,
                    "normalization_confidence": 0.95 if not conv_applied else 0.90,
                    "validation_status": val_status,
                    "calculation_readiness": "READY" if activity_data_ready else "NOT_READY"
                }

        record = {
            "document_id": doc_id,
            "company": company,
            "supplier": supplier,
            "activity": activity,
            "financial": financial,
            "emission_factor": emission_factor,
            "carbon_calculation": carbon_calc,
            "provenance": record_provenance,
            "confidence": confidence,
            "validation": validation,
            "cbam": cbam_data,
            "unit_normalization_audit": unit_normalization_audit
        }

        return record

    def verify_real_provenance(self, record: dict, page_text: str) -> dict:
        """
        Verifies that every non-null value in the record has a matching raw text or string representation
        in the document text. Nullifies the value if it cannot be verified.
        """
        if not page_text:
            return record
            
        text_lower = page_text.lower()
        
        def get_nested(d, path):
            parts = path.split(".")
            curr = d
            for p in parts:
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    return None
            return curr
            
        def set_nested(d, path, val):
            parts = path.split(".")
            curr = d
            for p in parts[:-1]:
                if p not in curr:
                    curr[p] = {}
                curr = curr[p]
            curr[parts[-1]] = val

        paths_to_verify = [
            "company.name",
            "company.company_id",
            "supplier.name",
            "supplier.supplier_id",
            "activity.material",
            "activity.quantity",
            "activity.unit",
            "activity.distance",
            "activity.origin",
            "activity.destination",
            "activity.transport_mode",
            "activity.weight",
            "activity.weight_unit",
            "activity.fuel_type",
            "activity.energy_type",
            "activity.consumption",
            "activity.consumption_unit",
            "activity.period_start",
            "activity.period_end",
            "financial.amount",
            "financial.currency"
        ]
        
        provenance = record.get("provenance", {})
        
        for path in paths_to_verify:
            val = get_nested(record, path)
            if val is None:
                continue
                
            if isinstance(val, str) and not val.strip():
                set_nested(record, path, None)
                continue
                
            prov_entry = provenance.get(path)
            verified = False
            
            if prov_entry and prov_entry.get("raw_text"):
                raw_txt = str(prov_entry["raw_text"]).strip()
                if raw_txt.lower() in text_lower:
                    verified = True
                else:
                    words = [w.lower().strip() for w in re.split(r'\s+', raw_txt) if len(w) >= 2]
                    if words and all(w in text_lower for w in words):
                        verified = True
                    
            if not verified:
                # Special checks for normalized values
                if path in ["activity.unit", "activity.consumption_unit"]:
                    raw_unit = record["activity"].get("consumption_unit") or record["activity"].get("unit")
                    val_str = str(raw_unit or val).strip()
                    equivalents = [val_str]
                    if val_str.lower() in ["tonne", "ton", "t"]:
                        equivalents.extend(["tonne", "ton", "t", "kg", "kilogram"])
                    elif val_str.lower() in ["kg", "kilogram"]:
                        equivalents.extend(["kg", "kilogram", "tonne", "ton", "t"])
                    elif val_str.lower() in ["liter", "l", "litre"]:
                        equivalents.extend(["liter", "l", "litre"])
                    elif val_str.lower() in ["kwh", "mwh"]:
                        equivalents.extend(["kwh", "mwh"])
                    if any(eq.lower() in text_lower for eq in equivalents):
                        verified = True
                elif path == "activity.material":
                    product = record["activity"].get("product")
                    if product and str(product).lower() in text_lower:
                        verified = True
                elif path in ["activity.quantity", "activity.consumption", "activity.weight", "activity.distance", "financial.amount"]:
                    try:
                        f_val = float(val)
                        candidates = [
                            str(val),
                            str(int(f_val)) if f_val.is_integer() else str(f_val),
                            str(int(f_val * 1000)) if (f_val * 1000).is_integer() else str(f_val * 1000),
                            str(int(f_val / 1000)) if (f_val / 1000).is_integer() else str(f_val / 1000)
                        ]
                        if any(c in text_lower for c in candidates):
                            verified = True
                    except Exception:
                        pass
                        
            if not verified:
                val_str = str(val).strip()
                if val_str.lower() in text_lower:
                    verified = True
                else:
                    if isinstance(val, str) and val.strip():
                        words = [w.lower().strip() for w in re.split(r'\s+', val) if len(w) >= 2]
                        if words and all(w in text_lower for w in words):
                            verified = True
                    elif isinstance(val, float) and val_str.endswith(".0"):
                        val_str_alt = val_str[:-2]
                        if val_str_alt in text_lower:
                            verified = True
                            
            if not verified:
                set_nested(record, path, None)
                if path in provenance:
                    del provenance[path]
                    
        return record

    # New Helper Methods (RC-05, RC-09, RC-12)

    def _lookup_emission_factor(self, act_type, activity):
        """Looks up emission factor. Delegates to EmissionFactorProvider -- never fabricates."""
        act_upper = str(act_type).upper()
        if act_upper in ('TRANSPORTATION', 'SHIPPING'):
            return self.ef_provider.find_transport_factor(activity.get('transport_mode'))
        elif act_upper == 'FUEL_CONSUMPTION':
            return self.ef_provider.find_fuel_factor(activity.get('fuel_type'))
        elif act_upper in ('ELECTRICITY_CONSUMPTION', 'ELECTRICITY_BILL'):
            return self.ef_provider.find_electricity_factor(
                country=activity.get('country'),
                grid_region=activity.get('grid_region')
            )
        elif act_upper in ('PURCHASED_GOODS', 'PURCHASE_INVOICE', 'PURCHASE_ORDER', 'MATERIAL_CONSUMPTION'):
            return self.ef_provider.find_material_factor(
                activity.get('material') or activity.get('product')
            )
        else:
            from pipeline.extraction.emission_factor_provider import _NOT_FOUND
            return _NOT_FOUND

    def _compute_confidence(self, activity_data_ready, missing, ef, provenance):
        """RC-05: Compute confidence from field completeness + EF availability + provenance quality."""
        base = 0.95 if activity_data_ready else max(0.40, 0.95 - len(missing) * 0.10)
        if ef.status == 'NOT_FOUND':
            base -= 0.05
        elif ef.status == 'APPROXIMATE':
            base -= 0.02
        if provenance:
            found_bbox = sum(
                1 for v in provenance.values()
                if isinstance(v, dict) and v.get('bbox') and v.get('bbox') != [0.0, 0.0, 0.0, 0.0]
            )
            total = len(provenance)
            prov_ratio = found_bbox / total if total > 0 else 0.0
            base = base * (0.90 + 0.10 * prov_ratio)
        overall = round(max(0.0, min(1.0, base)), 3)
        level = 'HIGH' if overall >= 0.85 else ('MEDIUM' if overall >= 0.60 else 'LOW')
        return {'overall': overall, 'level': level}

    def _check_minimum_evidence(self, act_type, activity, cbam):
        """RC-09: Returns (should_suppress, reason). Suppresses all-null records."""
        act_upper = str(act_type).upper()
        if act_upper in ('TRANSPORTATION', 'SHIPPING'):
            has_any = any([
                activity.get('origin'),
                activity.get('destination'),
                activity.get('transport_mode'),
                activity.get('distance'),
                activity.get('weight'),
            ])
            if not has_any:
                return True, 'Transport record has no usable fields (all null).'
        elif act_upper in ('PURCHASED_GOODS', 'PURCHASE_INVOICE', 'PURCHASE_ORDER', 'MATERIAL_CONSUMPTION'):
            has_any = any([
                activity.get('material'),
                activity.get('product'),
                activity.get('quantity'),
            ])
            if not has_any:
                return True, 'Purchase record has no usable activity data (all null).'
        elif act_upper in ('FUEL_CONSUMPTION', 'ELECTRICITY_CONSUMPTION'):
            has_any = any([
                activity.get('quantity'),
                activity.get('consumption'),
                activity.get('fuel_type'),
                activity.get('energy_type'),
            ])
            if not has_any:
                return True, 'Energy record has no usable fields (all null).'
        else:
            non_null = sum(1 for v in activity.values() if v is not None and str(v).strip())
            if non_null == 0:
                return True, 'Record has no usable fields (completely empty).'
        return False, ''
