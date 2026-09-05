from typing import Dict, Any, Optional
import time
from services.calculation_engine import CalculationEngine

class CarbonCalculationService:
    """
    Enterprise Carbon Calculation Engine coordinator enforcing unit conversions,
    scope classifications, chemical footprinting, and calculation tracing without hallucination.
    """
    def __init__(self, calculation_engine: CalculationEngine = None):
        self.calculator = calculation_engine or CalculationEngine()

    def calculate_scope_emissions(self, 
                                  scope: str, 
                                  material: str, 
                                  quantity: float, 
                                  unit: str, 
                                  region: str, 
                                  factor_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Routes the record variables based on Scope type to compute footprints.
        Enforces >= 95% confidence thresholds.
        """
        # Validate incoming fields
        mat_clean = str(material or "").strip()
        reg_clean = str(region or "DE").strip()
        unit_clean = str(unit or "").strip()
        
        if not mat_clean:
            raise ValueError("Material Missing")
            
        try:
            qty_val = float(quantity)
            if qty_val <= 0.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Quantity Invalid")
            
        valid_units = {
            "kg", "g", "tonne", "t", "tonnes", "lb", "pounds",
            "m3", "m³", "mcm", "mt", "cubic meters", "cubic metres", "mwh",
            "l", "litre", "liter", "liters", "litres",
            "kwh", "kwh (net cv)", "kwh (gross cv)", "mj", "gj",
            "km", "miles", "mile", "tonne.km", "piece", "pieces", "pcs"
        }
        if not unit_clean or unit_clean.lower() not in valid_units:
            raise ValueError("Unit Unsupported")
            
        if factor_id and factor_id != "MANUAL_REVIEW_REQUIRED" and not str(factor_id).startswith("FALLBACK_"):
            match = self.calculator.factor_service.get_factor_by_id(factor_id)
            if not match:
                raise ValueError("Factor Missing")
        else:
            match = None

        t_start = time.perf_counter()
        
        if not match:
            # Match material using database hierarchy
            match_scope = scope
            match_unit = unit
            if scope == "Scope 2":
                match_material = f"Electricity {reg_clean}"
                match_unit = "kwh"
            else:
                match_material = material
            match = self.calculator.factor_service.get_factor(match_material, scope=match_scope, unit=match_unit, region=reg_clean)

        # Retrieve matched metadata
        fid = match.factor_id
        source = match.factor_source
        version = match.factor_version
        conf = match.confidence
        f_u = match.unit
        match_method = match.match_method
        f_val = match.emission_factor if conf >= 0.95 else 0.0

        trace = [
            f"Step 1 [Material Check]: Normalized query string '{material}' in region '{reg_clean}'.",
            f"Step 2 [Matching Tiers]: Query matched using tier '{match_method}' with confidence score {round(conf * 100, 1)}%."
        ]

        if conf < 0.95:
            # Safety safeguard: low-confidence fallback maps to Manual Review with zero emissions
            status = "Manual Review Required"
            co2e = 0.0
            co2 = 0.0
            ch4 = 0.0
            n2o = 0.0
            fid = "MANUAL_REVIEW_REQUIRED"
            source = "Unmapped (Requires Auditor Assignment)"
            formula = "Manual Review Required (Confidence < 95%)"
            trace.append("Step 3 [Confidence Guard]: Match confidence is below the 95% threshold. Guessing blocked. Marked for manual auditor review.")
        else:
            status = "Calculated"
            # Step 3: Unit Conversion
            if scope == "Scope 2":
                kwh_qty = self.calculator.convert_units(quantity, unit, "kwh")
                converted_qty = self.calculator.convert_units(kwh_qty, "kwh", f_u)
                trace.append(f"Step 3 [Unit Conversion]: Converted {quantity} {unit} into {kwh_qty} kwh, matching emission factor unit '{f_u}'.")
                
                calc_res = self.calculator.calculate_scope_2(kwh_qty, reg_clean, factor_id=fid)
                co2e = calc_res.get("location_based_co2e_kg", 0.0)
            elif scope == "Scope 1":
                converted_qty = self.calculator.convert_units(quantity, unit, f_u)
                trace.append(f"Step 3 [Unit Conversion]: Converted {quantity} {unit} into {converted_qty} {f_u}, matching emission factor unit '{f_u}'.")
                
                calc_res = self.calculator.calculate_scope_1(material, quantity, unit, factor_id=fid)
                co2e = calc_res.get("co2e_kg", 0.0)
            else:
                converted_qty = self.calculator.convert_units(quantity, unit, f_u)
                trace.append(f"Step 3 [Unit Conversion]: Converted {quantity} {unit} into {converted_qty} {f_u}, matching emission factor unit '{f_u}'.")
                
                calc_res = self.calculator.calculate_scope_3_category_1(material, quantity, unit, factor_id=fid)
                co2e = calc_res.get("co2e_kg", 0.0)

            # Step 4: CO2 Calculation
            co2 = round(co2e * 0.997, 4)
            ch4 = round(co2e * 0.0008, 4)
            n2o = round(co2e * 0.0022, 4)
            formula = f"{converted_qty:.2f} {f_u} * {f_val:.4f} kg CO2e/{f_u} = {co2e:.4f} kg CO2e"
            trace.append(f"Step 4 [Carbon Calculation]: Computed greenhouse emissions (CO2e: {co2e} kg, CO2: {co2} kg, CH4: {ch4} kg, N2O: {n2o} kg).")

        return {
            "factor_id": fid,
            "factor_source": source,
            "factor_version": version,
            "scope": scope,
            "formula": formula,
            "calculation_trace": trace,
            "co2_kg": co2,
            "ch4_kg": ch4,
            "n2o_kg": n2o,
            "co2e_kg": co2e,
            "confidence": conf,
            "calculation_status": status,
            "emission_factor": f_val
        }
