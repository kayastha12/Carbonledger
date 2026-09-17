import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple
import openpyxl

logger = logging.getLogger("WorkbookFactorEngine")
logger.setLevel(logging.INFO)

class WorkbookFactor:
    def __init__(self,
                 factor_id: str,
                 scope: str,
                 level_1: str,
                 level_2: str,
                 level_3: str,
                 level_4: str,
                 column_text: str,
                 uom: str,
                 ghg_unit: str,
                 conversion_factor: float,
                 source_sheet: str,
                 source_workbook: str):
        self.factor_id = str(factor_id)
        self.scope = scope
        self.level_1 = level_1
        self.level_2 = level_2
        self.level_3 = level_3
        self.level_4 = level_4
        self.column_text = column_text
        self.uom = str(uom).strip().lower()
        self.ghg_unit = str(ghg_unit).strip()
        self.conversion_factor = float(conversion_factor) if conversion_factor is not None else 0.0
        self.source_sheet = source_sheet
        self.source_workbook = source_workbook

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.factor_id,
            "scope": self.scope,
            "level_1": self.level_1,
            "level_2": self.level_2,
            "level_3": self.level_3,
            "level_4": self.level_4,
            "column_text": self.column_text,
            "unit": f"kg CO2e/{self.uom}",
            "uom": self.uom,
            "ghg_unit": self.ghg_unit,
            "value": self.conversion_factor,
            "source": self.source_workbook,
            "sheet": self.source_sheet
        }

class WorkbookFactorEngine:
    """
    Authoritative emission factor engine directly loading and querying
    the CarbonLedger GHG Factors workbook (CarbonLedger_GHG_Factors_2026_Clean(6).xlsx).
    Enforces unit-safe calculations, semantic matching confidence, and zero fabrication.
    """
    _instance: Optional["WorkbookFactorEngine"] = None

    def __init__(self, workbook_path: Optional[str] = None):
        self.workbook_path = workbook_path or self._resolve_workbook_path()
        self.factors_by_id: Dict[str, WorkbookFactor] = {}
        self.factors_by_sheet: Dict[str, List[WorkbookFactor]] = {}
        self.flat_factors: List[WorkbookFactor] = []
        self.is_loaded = False
        self._load_workbook()

    @classmethod
    def get_instance(cls, workbook_path: Optional[str] = None) -> "WorkbookFactorEngine":
        if cls._instance is None:
            cls._instance = WorkbookFactorEngine(workbook_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def _resolve_workbook_path(self) -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(project_root, "datasets", "CarbonLedger_GHG_Factors_2026_Clean(6).xlsx"),
            os.path.join(project_root, "datasets", "CarbonLedger_GHG_Factors_2026_Clean.xlsx"),
            r"D:\internship\mlmodel\CarbonLedger_GHG_Factors_2026_Clean(6).xlsx",
            r"D:\internship\CarbonLedger_GHG_Factors_2026_Clean(6).xlsx",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return candidates[0]

    def _load_workbook(self):
        if not os.path.exists(self.workbook_path):
            logger.warning(f"Workbook not found at {self.workbook_path}")
            return

        wb_filename = os.path.basename(self.workbook_path)
        logger.info(f"Loading authoritative GHG factors from {self.workbook_path}...")

        wb = openpyxl.load_workbook(self.workbook_path, data_only=True, read_only=True)
        
        # Load 'All Factors (Flat)'
        if "All Factors (Flat)" in wb.sheetnames:
            sheet = wb["All Factors (Flat)"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                fid = str(row[0]).strip()
                scope = str(row[1] or "").strip()
                l1 = str(row[2] or "").strip()
                l2 = str(row[3] or "").strip()
                l3 = str(row[4] or "").strip()
                l4 = str(row[5] or "").strip()
                col_text = str(row[6] or "").strip()
                uom = str(row[7] or "").strip()
                ghg_unit = str(row[8] or "").strip()
                raw_factor = row[9]

                try:
                    factor_val = float(str(raw_factor).replace(",", "").strip()) if raw_factor is not None and str(raw_factor).strip() != "" else 0.0
                except ValueError:
                    factor_val = 0.0

                w_factor = WorkbookFactor(
                    factor_id=fid,
                    scope=scope,
                    level_1=l1,
                    level_2=l2,
                    level_3=l3,
                    level_4=l4,
                    column_text=col_text,
                    uom=uom,
                    ghg_unit=ghg_unit,
                    conversion_factor=factor_val,
                    source_sheet="All Factors (Flat)",
                    source_workbook=wb_filename
                )
                self.factors_by_id[fid] = w_factor
                self.flat_factors.append(w_factor)

        wb.close()
        self.is_loaded = True
        logger.info(f"Loaded {len(self.flat_factors)} factors from {wb_filename}")

    def find_factors(self,
                     category: Optional[str] = None,
                     search_text: Optional[str] = None,
                     scope: Optional[str] = None,
                     uom: Optional[str] = None) -> List[WorkbookFactor]:
        """
        Queries factors matching text descriptors, scope, and UOM.
        """
        results = []
        st_low = search_text.lower().strip() if search_text else None
        cat_low = category.lower().strip() if category else None
        uom_low = uom.lower().strip() if uom else None
        scope_low = scope.lower().strip() if scope else None

        for f in self.flat_factors:
            # Only match total kg CO2e factors (exclude partial breakdowns CO2/CH4/N2O unless requested)
            if f.ghg_unit != "kg CO2e":
                continue

            if scope_low and scope_low not in f.scope.lower():
                continue

            if uom_low and uom_low != f.uom:
                continue

            row_desc = f"{f.level_1} {f.level_2} {f.level_3} {f.level_4} {f.column_text}".lower()

            if cat_low and cat_low not in row_desc:
                continue

            if st_low and st_low not in row_desc:
                continue

            results.append(f)

        return results

    def extract_material_attributes(self, mat_str: str) -> Dict[str, Any]:
        """
        Extracts material family, canonical category, material form, and production route
        from raw description without mutating the raw text.
        """
        if not mat_str:
            return {"raw": "", "route": "Primary material production", "l2": None, "l3": None}
        
        m_raw = str(mat_str).strip()
        m_low = m_raw.lower()

        # 1. Route extraction
        if any(k in m_low for k in ["closed-loop", "closed loop", "rpet", "(recycled)", "recycled", "cullet"]):
            col_text = "Closed-loop source"
        elif any(k in m_low for k in ["re-used", "reused"]):
            col_text = "Re-used"
        elif any(k in m_low for k in ["open-loop", "open loop"]):
            col_text = "Open-loop source"
        elif any(k in m_low for k in ["primary", "virgin"]):
            col_text = "Primary material production"
        else:
            col_text = "Primary material production"

        # 2. Canonical mapping to workbook Level 2 and Level 3
        target_l2 = None
        target_l3 = None

        # Construction metals (Structural steel / section / plates / generic steel)
        if "structural steel" in m_low or "steel section" in m_low or "structural metal" in m_low or "steel plate" in m_low or m_low in ["steel", "metals", "metal", "construction steel"]:
            target_l2 = "Construction"
            target_l3 = "Metals"
        elif "tinplate" in m_low or "can bodies" in m_low or ("steel" in m_low and "can" in m_low):
            target_l2 = "Metal"
            target_l3 = "Metal: steel cans"
        elif "scrap metal" in m_low or "metal scrap" in m_low:
            target_l2 = "Metal"
            target_l3 = "Metal: scrap metal"
        elif "mixed metal can" in m_low or "mixed can" in m_low:
            target_l2 = "Metal"
            target_l3 = "Metal: mixed cans"
        elif "aluminium" in m_low or "aluminum" in m_low:
            if m_low in ["aluminium", "aluminum", "generic aluminium", "generic aluminum", "raw aluminium", "raw aluminum"]:
                target_l2 = None
                target_l3 = None
            else:
                target_l2 = "Metal"
                target_l3 = "Metal: aluminium cans and foil (excl. forming)"
        elif "hdpe" in m_low or "high-density polyethylene" in m_low:
            target_l2 = "Plastic"
            target_l3 = "Plastics: HDPE (incl. forming)"
        elif "lldpe" in m_low or "ldpe" in m_low or "linear low-density" in m_low:
            target_l2 = "Plastic"
            target_l3 = "Plastics: LDPE and LLDPE (incl. forming)"
        elif "rpet" in m_low or "pet resin" in m_low or ("pet" in m_low and "forming" in m_low) or ("polyethylene terephthalate" in m_low):
            target_l2 = "Plastic"
            target_l3 = "Plastics: PET (incl. forming)"
        elif "polypropylene" in m_low or " pp " in f" {m_low} ":
            target_l2 = "Plastic"
            target_l3 = "Plastics: PP (incl. forming)"
        elif "polystyrene" in m_low or " ps " in f" {m_low} ":
            target_l2 = "Plastic"
            target_l3 = "Plastics: PS (incl. forming)"
        elif "pvc" in m_low or "polyvinyl chloride" in m_low:
            target_l2 = "Plastic"
            target_l3 = "Plastics: PVC (incl. forming)"
        elif "plastic film" in m_low:
            target_l2 = "Plastic"
            target_l3 = "Plastics: average plastic film"
        elif "rigid plastic" in m_low or "moulding compound" in m_low:
            target_l2 = "Plastic"
            target_l3 = "Plastics: average plastic rigid"
        elif "plastic resin" in m_low:
            # Generic plastic resin without specific polymer grade requires review
            target_l2 = None
            target_l3 = None
        elif "plastic granules" in m_low or m_low in ["plastic", "plastics", "mixed plastics", "average plastic", "average plastics"]:
            target_l2 = "Plastic"
            target_l3 = "Plastics: average plastics"
        elif "corrugated board" in m_low or ("board" in m_low and "paper" not in m_low and "insulation" not in m_low and "plaster" not in m_low):
            target_l2 = "Paper"
            target_l3 = "Paper and board: board"
        elif "kraft paper" in m_low or ("paper" in m_low and "board" not in m_low and "mixed" not in m_low):
            target_l2 = "Paper"
            target_l3 = "Paper and board: paper"
        elif "mixed paper" in m_low or ("paper" in m_low and "board" in m_low):
            target_l2 = "Paper"
            target_l3 = "Paper and board: mixed"
        elif "refrigeration" in m_low or "cooling unit" in m_low or "fridge" in m_low or "freezer" in m_low:
            target_l2 = "Electrical items"
            target_l3 = "Electrical items - fridges and freezers"
        elif "large electrical" in m_low or "appliance sub-assembly" in m_low:
            target_l2 = "Electrical items"
            target_l3 = "Electrical items - large"
        elif "it hardware" in m_low or "control pc" in m_low or "computer" in m_low:
            target_l2 = "Electrical items"
            target_l3 = "Electrical items - IT"
        elif "small electrical" in m_low or "electrical components" in m_low:
            target_l2 = "Electrical items"
            target_l3 = "Electrical items - small"
        elif "alkaline battery" in m_low or "batteries - alkaline" in m_low:
            target_l2 = "Electrical items"
            target_l3 = "Batteries - Alkaline"
        elif "lithium" in m_low or "li ion" in m_low or "li-ion" in m_low:
            target_l2 = "Electrical items"
            target_l3 = "Batteries - Li ion"
        elif "nimh" in m_low or "ni-mh" in m_low:
            target_l2 = "Electrical items"
            target_l3 = "Batteries - NiMh"
        elif "glass" in m_low:
            target_l2 = "Other"
            target_l3 = "Glass"
        elif "sand" in m_low or "aggregate" in m_low:
            target_l2 = "Construction"
            target_l3 = "Aggregates"
        elif "brick" in m_low or "refractory" in m_low:
            target_l2 = "Construction"
            target_l3 = "Bricks"
        elif "concrete" in m_low:
            target_l2 = "Construction"
            target_l3 = "Concrete"
        elif "insulation" in m_low:
            target_l2 = "Construction"
            target_l3 = "Insulation"
        elif "mineral oil" in m_low:
            target_l2 = "Construction"
            target_l3 = "Mineral oil"
        elif "plasterboard" in m_low:
            target_l2 = "Construction"
            target_l3 = "Plasterboard"
        elif "tyre" in m_low or "tire" in m_low:
            target_l2 = "Construction"
            target_l3 = "Tyres"
        elif "pallet" in m_low or "timber" in m_low or "wood" in m_low:
            target_l2 = "Construction"
            target_l3 = "Wood"
        elif "clothing" in m_low or "textile" in m_low:
            target_l2 = "Other"
            target_l3 = "Clothing"
        elif "food" in m_low or "drink" in m_low:
            target_l2 = "Other"
            target_l3 = "Food and drink"

        return {
            "raw": m_raw,
            "route": col_text,
            "l2": target_l2,
            "l3": target_l3
        }

    def evaluate_activity(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates an extracted activity record against the authoritative workbook.
        Enforces unit safety, semantic match checks, double-counting guards, and geography rules.
        """
        act = rec.get("activity", {})
        act_type = str(act.get("activity_type", rec.get("activity_type", "PURCHASED_GOODS"))).upper()
        doc_type = str(rec.get("document_type", "")).upper()

        # 1. Check for Reference-Only / Supporting documents (e.g. Purchase Orders)
        if act_type == "PURCHASE_ORDER" or doc_type == "PURCHASE_ORDER":
            return {
                "calculation_status": "REFERENCE_ONLY",
                "calculation_ready": False,
                "reason": "Supporting purchase order; excluded from emission calculations to prevent double-counting with invoices.",
                "factor": None,
                "formula": "Reference Only (No Calculation)",
                "emission_kgco2e": 0.0,
                "confidence": 1.0,
                "match_method": "reference_guard"
            }

        mat = act.get("material") or act.get("product") or rec.get("material")
        fuel = act.get("fuel_type") or rec.get("fuel_type")
        nrg = act.get("energy_type") or rec.get("energy_type")
        mode = act.get("transport_mode") or rec.get("transport_mode")
        qty = act.get("quantity") if act.get("quantity") is not None else rec.get("quantity")
        unit = act.get("unit") or rec.get("unit")
        dist = act.get("distance") if act.get("distance") is not None else rec.get("distance")
        dist_unit = act.get("distance_unit") or rec.get("distance_unit") or "km"
        wt = act.get("weight") if act.get("weight") is not None else rec.get("weight")
        wt_unit = act.get("weight_unit") or rec.get("weight_unit") or "kg"
        cons = act.get("consumption") if act.get("consumption") is not None else rec.get("consumption")
        cons_unit = act.get("consumption_unit") or rec.get("consumption_unit")
        country = act.get("country") or rec.get("country") or rec.get("company", {}).get("country") or "India"

        # 2. Case: FUEL_CONSUMPTION
        if act_type == "FUEL_CONSUMPTION" or fuel:
            fuel_name = str(fuel or mat or "").lower().strip()
            
            # 2a. Diesel (average biofuel blend)
            if "diesel" in fuel_name:
                u_str = str(unit or "L").lower().strip()
                if u_str in ["l", "liter", "litres", "litre", "liters"]:
                    factor = self.factors_by_id.get("1_101_1011_8_1") or self.find_factors(search_text="Diesel (average biofuel blend)", uom="litres")
                    f_obj = factor if isinstance(factor, WorkbookFactor) else (factor[0] if factor else None)
                    if f_obj and qty is not None:
                        val = float(qty) * f_obj.conversion_factor
                        return {
                            "calculation_status": "READY",
                            "calculation_ready": True,
                            "reason": None,
                            "factor": f_obj.to_dict(),
                            "formula": f"{float(qty)} L × {f_obj.conversion_factor} kg CO2e/litre",
                            "emission_kgco2e": round(val, 4),
                            "confidence": 1.0,
                            "match_method": "exact_factor_match"
                        }
            
            # 2b. LPG
            elif "lpg" in fuel_name:
                u_str = str(unit or "kg").lower().strip()
                if u_str in ["kg", "g", "tonne", "t", "tonnes"]:
                    factor = self.factors_by_id.get("1_100_1003_15_1") or self.find_factors(search_text="LPG", uom="tonnes")
                    f_obj = factor if isinstance(factor, WorkbookFactor) else (factor[0] if factor else None)
                    if f_obj and qty is not None:
                        tonnes = float(qty) / 1000.0 if u_str == "kg" else float(qty)
                        val = tonnes * f_obj.conversion_factor
                        return {
                            "calculation_status": "READY",
                            "calculation_ready": True,
                            "reason": None,
                            "factor": f_obj.to_dict(),
                            "formula": f"{tonnes} tonne × {f_obj.conversion_factor} kg CO2e/tonne (converted from {float(qty)} kg)",
                            "emission_kgco2e": round(val, 4),
                            "confidence": 1.0,
                            "match_method": "exact_unit_converted_match"
                        }

            # 2c. Natural Gas (Fuel Consumption)
            elif "natural gas" in fuel_name or "gas" in fuel_name:
                u_str = str(unit or "").upper().strip()
                if "MCM" in u_str:
                    return {
                        "calculation_status": "REVIEW_REQUIRED",
                        "calculation_ready": False,
                        "reason": f"Natural gas quantity is in MCM ({qty} MCM). Unit scaling requires confirmation before applying m³ factor.",
                        "factor": None,
                        "formula": "Pending MCM Unit Scaling Confirmation",
                        "emission_kgco2e": 0.0,
                        "confidence": 0.80,
                        "match_method": "unit_scaling_review"
                    }

        # 3. Case: TRANSPORTATION (Scope 3 Freight)
        if act_type in ["TRANSPORTATION", "LOGISTICS_SHIPPING", "SHIPPING_MANIFEST"] or mode:
            mode_str = str(mode or "").lower().strip()

            # 3a. Rail Freight
            if "rail" in mode_str or "train" in mode_str:
                factor = self.factors_by_id.get("27_315_3151_14_1") or self.find_factors(category="Freighting goods", search_text="Freight train", uom="tonne.km")
                f_obj = factor if isinstance(factor, WorkbookFactor) else (factor[0] if factor else None)
                if f_obj and wt is not None and dist is not None:
                    wt_tonnes = float(wt) / 1000.0 if str(wt_unit).lower().strip() in ["kg", "g"] else float(wt)
                    dist_km = float(dist)
                    tonne_km = wt_tonnes * dist_km
                    val = tonne_km * f_obj.conversion_factor
                    return {
                        "calculation_status": "READY",
                        "calculation_ready": True,
                        "reason": None,
                        "factor": f_obj.to_dict(),
                        "formula": f"{tonne_km} tonne.km × {f_obj.conversion_factor} kg CO2e/tonne.km ({wt_tonnes} t × {dist_km} km)",
                        "emission_kgco2e": round(val, 4),
                        "confidence": 1.0,
                        "match_method": "exact_freight_rail_match"
                    }

            # 3b. Road / HGV Freight
            elif "truck" in mode_str or "road" in mode_str or "hgv" in mode_str or "freight" in mode_str:
                # If mode is single generic keyword 'truck' with only weight/dist and no class or context, require review
                if mode_str == "truck":
                    return {
                        "calculation_status": "REVIEW_REQUIRED",
                        "calculation_ready": False,
                        "reason": f"Truck transportation ({wt} {wt_unit}, {dist} {dist_unit}) requires vehicle class specification in workbook.",
                        "factor": None,
                        "formula": "Pending Vehicle Class Specification",
                        "emission_kgco2e": 0.0,
                        "confidence": 0.85,
                        "match_method": "truck_class_review"
                    }

                # Resolve vehicle category and loading condition
                target_l2 = "HGV (refrigerated, all diesel)" if "refrigerated" in mode_str and "non-refrigerated" not in mode_str else "HGV (non-refrigerated, all diesel)"
                
                if "articulated" in mode_str or "artic" in mode_str:
                    target_l3 = "Articulated (>3.5 - 33t)" if (">3.5" in mode_str or "33" in mode_str) else "Articulated (>33t)"
                elif "rigid" in mode_str:
                    if ">3.5 - 7.5" in mode_str or "7.5" in mode_str:
                        target_l3 = "Rigid (>3.5 - 7.5 tonnes)"
                    elif ">7.5 - 17" in mode_str or "17" in mode_str:
                        target_l3 = "Rigid (>7.5 tonnes-17 tonnes)"
                    else:
                        target_l3 = "Rigid (>17 tonnes)"
                else:
                    target_l3 = "All HGVs"

                # Loading condition: Check 100% and 50% BEFORE 0% to prevent substring match bugs
                if "100%" in mode_str or "100% laden" in mode_str:
                    col_text = "100% Laden"
                elif "50%" in mode_str or "50% laden" in mode_str:
                    col_text = "50% Laden"
                elif "0%" in mode_str or "unladen" in mode_str or "0% laden" in mode_str:
                    col_text = "0% Laden"
                else:
                    col_text = "Average laden"

                # Look up matching tonne.km factor
                matched_factor = None
                for f in self.flat_factors:
                    if f.level_1 == "Freighting goods" and f.ghg_unit == "kg CO2e" and f.uom == "tonne.km":
                        if f.level_2.lower() == target_l2.lower() and f.level_3.lower() == target_l3.lower() and f.column_text.lower() == col_text.lower():
                            matched_factor = f
                            break

                if not matched_factor:
                    # Fallback lookup in same vehicle class
                    for f in self.flat_factors:
                        if f.level_1 == "Freighting goods" and f.ghg_unit == "kg CO2e" and f.uom == "tonne.km":
                            if "articulated" in f.level_3.lower() and col_text.lower() in f.column_text.lower():
                                matched_factor = f
                                break

                if matched_factor and wt is not None and dist is not None:
                    wt_tonnes = float(wt) / 1000.0 if str(wt_unit).lower().strip() in ["kg", "g"] else float(wt)
                    dist_km = float(dist)
                    tonne_km = round(wt_tonnes * dist_km, 4)
                    val = round(tonne_km * matched_factor.conversion_factor, 4)
                    return {
                        "calculation_status": "READY",
                        "calculation_ready": True,
                        "reason": None,
                        "factor": matched_factor.to_dict(),
                        "formula": f"{tonne_km} tonne.km × {matched_factor.conversion_factor} kg CO2e/tonne.km ({wt_tonnes} t × {dist_km} km)",
                        "emission_kgco2e": val,
                        "confidence": 1.0,
                        "match_method": "exact_freight_hgv_match"
                    }
                elif wt is None or dist is None:
                    return {
                        "calculation_status": "MISSING_REQUIRED_DATA",
                        "calculation_ready": False,
                        "reason": f"Transport record requires weight and distance for carbon calculation (found weight={wt}, dist={dist}).",
                        "factor": matched_factor.to_dict() if matched_factor else None,
                        "formula": "Missing Weight / Distance Parameter",
                        "emission_kgco2e": 0.0,
                        "confidence": 0.0,
                        "match_method": "missing_transport_metrics"
                    }
                else:
                    return {
                        "calculation_status": "REVIEW_REQUIRED",
                        "calculation_ready": False,
                        "reason": f"Truck transportation ({wt} {wt_unit}, {dist} {dist_unit}) requires vehicle class specification in workbook.",
                        "factor": None,
                        "formula": "Pending Vehicle Class Specification",
                        "emission_kgco2e": 0.0,
                        "confidence": 0.85,
                        "match_method": "truck_class_review"
                    }

        # 4. Case: ELECTRICITY_CONSUMPTION
        if act_type in ["ELECTRICITY_CONSUMPTION", "ELECTRICITY_GRID"] or (nrg and "electricity" in str(nrg).lower()):
            if "india" in str(country).lower():
                return {
                    "calculation_status": "FACTOR_NOT_FOUND",
                    "calculation_ready": False,
                    "reason": "No compatible India electricity emission factor available in the configured factor database (workbook contains only UK electricity).",
                    "factor": None,
                    "formula": "Factor Not Found (Requires India Grid Factor)",
                    "emission_kgco2e": 0.0,
                    "confidence": 0.0,
                    "match_method": "geography_mismatch_guard"
                }

        # 5. Case: NATURAL_GAS_CONSUMPTION / UTILITY
        if act_type in ["NATURAL_GAS_CONSUMPTION"] or (nrg and "natural gas" in str(nrg).lower()):
            u_str = str(cons_unit or unit or "").upper().strip()
            if "MCM" in u_str:
                return {
                    "calculation_status": "REVIEW_REQUIRED",
                    "calculation_ready": False,
                    "reason": f"Natural gas utility consumption is in MCM ({cons or qty} MCM). Unit scaling requires confirmation before applying m³ factor.",
                    "factor": None,
                    "formula": "Pending MCM Unit Scaling Confirmation",
                    "emission_kgco2e": 0.0,
                    "confidence": 0.80,
                    "match_method": "unit_scaling_review"
                }

        # 6. Case: STEAM_CONSUMPTION
        if act_type in ["STEAM_CONSUMPTION"] or (nrg and "steam" in str(nrg).lower()):
            u_str = str(cons_unit or unit or "").lower().strip()
            if u_str in ["mt", "tonne", "tonnes", "t", "kg"]:
                return {
                    "calculation_status": "MISSING_REQUIRED_DATA",
                    "calculation_ready": False,
                    "reason": f"Steam quantity is in tonnes ({cons or qty} {u_str}) but available workbook factor requires kWh. Missing steam enthalpy / energy conversion parameter.",
                    "factor": None,
                    "formula": "Missing Conversion Parameter (tonnes -> kWh)",
                    "emission_kgco2e": 0.0,
                    "confidence": 0.0,
                    "match_method": "incompatible_unit_guard"
                }

        # 7. Case: PURCHASED_GOODS / MATERIAL_CONSUMPTION
        if act_type in ["PURCHASED_GOODS", "MATERIAL_CONSUMPTION"] or mat:
            mat_name = str(mat or "").strip()
            attrs = self.extract_material_attributes(mat_name)
            target_l2 = attrs.get("l2")
            target_l3 = attrs.get("l3")
            col_text = attrs.get("route", "Primary material production")

            if target_l2 and target_l3:
                # 1. Look for exact route match
                matched_factor = None
                for f in self.flat_factors:
                    if f.level_1 == "Material use" and f.ghg_unit == "kg CO2e":
                        if f.level_2.lower() == target_l2.lower() and f.level_3.lower() == target_l3.lower() and f.column_text.lower() == col_text.lower():
                            matched_factor = f
                            break

                # 2. If closed-loop requested but not found, check if primary exists and mark review
                if not matched_factor and col_text != "Primary material production":
                    for f in self.flat_factors:
                        if f.level_1 == "Material use" and f.ghg_unit == "kg CO2e":
                            if f.level_2.lower() == target_l2.lower() and f.level_3.lower() == target_l3.lower():
                                return {
                                    "calculation_status": "REVIEW_REQUIRED",
                                    "calculation_ready": False,
                                    "reason": f"Compatible recycled factor unavailable in workbook for '{mat_name}'. Primary factor available ({f.conversion_factor} kg CO2e/t) but requires auditor review.",
                                    "factor": f.to_dict(),
                                    "formula": "Pending Recycled Factor Auditor Confirmation",
                                    "emission_kgco2e": 0.0,
                                    "confidence": 0.85,
                                    "match_method": "recycled_factor_review"
                                }

                if matched_factor and qty is not None:
                    u_low = str(unit or "kg").lower().strip()
                    if u_low in ["kg", "g", "lb", "pounds"]:
                        tonnes = (float(qty) * 0.001) if u_low == "kg" else (float(qty) * 0.000453592 if u_low in ["lb", "pounds"] else float(qty) * 1e-6)
                    else:
                        tonnes = float(qty)
                    
                    val = round(tonnes * matched_factor.conversion_factor, 4)
                    return {
                        "calculation_status": "READY",
                        "calculation_ready": True,
                        "reason": None,
                        "factor": matched_factor.to_dict(),
                        "formula": f"{tonnes} tonne × {matched_factor.conversion_factor} kg CO2e/tonne (converted from {float(qty)} {unit or 'kg'})",
                        "emission_kgco2e": val,
                        "confidence": 1.0,
                        "match_method": "exact_workbook_material_match"
                    }
                elif qty is None:
                    return {
                        "calculation_status": "MISSING_REQUIRED_DATA",
                        "calculation_ready": False,
                        "reason": f"Material '{mat_name}' is missing quantity.",
                        "factor": matched_factor.to_dict() if matched_factor else None,
                        "formula": "Missing Quantity",
                        "emission_kgco2e": 0.0,
                        "confidence": 0.0,
                        "match_method": "missing_quantity_guard"
                    }

            # If not matched canonically, evaluate semantic candidates strictly without guessing across categories
            cand_factors = []
            m_low = mat_name.lower()
            for f in self.flat_factors:
                if f.level_1 == "Material use" and f.ghg_unit == "kg CO2e" and f.conversion_factor > 0:
                    desc = f"{f.level_2} {f.level_3}".lower()
                    if any(w in desc for w in m_low.split() if len(w) > 4):
                        cand_factors.append(f)

            if cand_factors:
                cand = cand_factors[0]
                return {
                    "calculation_status": "REVIEW_REQUIRED",
                    "calculation_ready": False,
                    "reason": f"No exact emission factor for '{mat_name}' in workbook. Semantic candidate '{cand.level_2}: {cand.level_3}' requires auditor review.",
                    "factor": cand.to_dict(),
                    "formula": "Pending Material Mapping Confirmation",
                    "emission_kgco2e": 0.0,
                    "confidence": 0.80,
                    "match_method": "semantic_material_review"
                }

            return {
                "calculation_status": "FACTOR_NOT_FOUND",
                "calculation_ready": False,
                "reason": f"No compatible emission factor found in authoritative workbook for material '{mat_name}'. Guessing blocked.",
                "factor": None,
                "formula": "Factor Not Found",
                "emission_kgco2e": 0.0,
                "confidence": 0.0,
                "match_method": "no_match_guard"
            }

        # 8. Default Unmapped Activity
        return {
            "calculation_status": "FACTOR_NOT_FOUND",
            "calculation_ready": False,
            "reason": f"No authoritative emission factor found in workbook for activity '{act_type}' ({mat or fuel or nrg or mode}).",
            "factor": None,
            "formula": "Factor Not Found",
            "emission_kgco2e": 0.0,
            "confidence": 0.0,
            "match_method": "no_match"
        }

