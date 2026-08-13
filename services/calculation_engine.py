import pandas as pd
from typing import Dict, Any, Optional
from services.emission_factor_service import EmissionFactorService, EmissionFactorMatch

class CalculationEngine:
    """
    CarbonLedger Calculation Engine.
    All factor retrieval is centralized strictly through EmissionFactorService.
    """
    def __init__(self, cleaned_factors_csv: Optional[str] = None):
        # Delegate factor storage & retrieval to EmissionFactorService
        self.factor_service = EmissionFactorService.get_instance(data_path=cleaned_factors_csv)

    def get_factor_record(self, factor_id: str) -> Optional[Dict[str, Any]]:
        match = self.factor_service.get_factor_by_id(factor_id)
        if match:
            return {
                "id": match.factor_id,
                "activity": match.material,
                "scope": match.scope,
                "region": match.region,
                "year": match.year,
                "category": match.activity_type,
                "factor": match.emission_factor,
                "uom": match.unit,
                "ghg_unit": match.ghg_unit,
                "source_sheet": match.factor_source,
                "factor_version": match.factor_version
            }
        return None

    def get_factor(self, factor_id: str) -> float:
        rec = self.get_factor_record(factor_id)
        if rec:
            return float(rec["factor"])
        return 0.0

    def convert_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Converts activity values between incompatible units.
        Supports: kg, g, tonne / t, lb, m³ / cubic meters / cubic metres, litre / l / liters, kWh / kwh, km, mile / miles.
        """
        if value is None:
            return 0.0
        
        from_u = str(from_unit).lower().strip()
        to_u = str(to_unit).lower().strip()
        
        # Standardize aliases
        aliases = {
            "t": "tonne",
            "tonnes": "tonne",
            "l": "liters",
            "litre": "liters",
            "liter": "liters",
            "cubic meters": "cubic meters",
            "cubic metres": "cubic meters",
            "m3": "cubic meters",
            "m³": "cubic meters",
            "kwh": "kwh",
            "kwh (net cv)": "kwh",
            "kwh (gross cv)": "kwh",
            "km": "km",
            "miles": "miles",
            "mile": "miles",
            "g": "g",
            "kg": "kg",
            "lb": "lb",
            "pounds": "lb"
        }
        
        from_u = aliases.get(from_u, from_u)
        to_u = aliases.get(to_u, to_u)
        
        if from_u == to_u:
            return float(value)
            
        # Conversion rates to base units (Mass: kg, Volume: liters, Energy: kwh, Distance: km)
        mass_to_kg = {
            "kg": 1.0,
            "g": 0.001,
            "tonne": 1000.0,
            "lb": 0.45359237
        }
        
        volume_to_liters = {
            "liters": 1.0,
            "cubic meters": 1000.0
        }
        
        distance_to_km = {
            "km": 1.0,
            "miles": 1.609344
        }
        
        # Mass conversions
        if from_u in mass_to_kg and to_u in mass_to_kg:
            val_kg = value * mass_to_kg[from_u]
            return val_kg / mass_to_kg[to_u]
            
        # Volume conversions
        if from_u in volume_to_liters and to_u in volume_to_liters:
            val_l = value * volume_to_liters[from_u]
            return val_l / volume_to_liters[to_u]
            
        # Distance conversions
        if from_u in distance_to_km and to_u in distance_to_km:
            val_km = value * distance_to_km[from_u]
            return val_km / distance_to_km[to_u]
            
        # Energy conversions
        conversions = {
            ("kwh", "mj"): 3.6,
            ("mj", "kwh"): 0.277778,
            ("kwh", "gj"): 0.0036,
            ("gj", "kwh"): 277.778,
        }
        
        rate = conversions.get((from_u, to_u))
        if rate:
            return value * rate
            
        # Fallback
        return float(value)

    def calculate_scope_1(self, fuel_type: str, quantity: float, unit: str, factor_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Direct emissions from fuel combustion.
        Formula: Fuel Quantity * Fuel Emission Factor
        """
        if factor_id:
            match = self.factor_service.get_factor_by_id(factor_id)
        else:
            match = None

        if not match:
            match = self.factor_service.get_factor(fuel_type, scope="Scope 1", unit=unit)

        factor_u = match.unit
        factor_source = match.factor_source
        factor_version = match.factor_version
        
        # Enforce confidence check (Never guess factor values below 95% confidence)
        if match.confidence < 0.95:
            factor = 0.0
            co2e = 0.0
            converted_qty = quantity
            factor_source = "Unmapped (Requires Auditor Assignment)"
        else:
            factor = match.emission_factor
            # Convert quantity to the factor's UOM
            converted_qty = self.convert_units(quantity, unit, factor_u)
            co2e = converted_qty * factor
        
        return {
            "co2e_kg": round(co2e, 4),
            "ch4_kg": round(co2e * 0.0008, 4),
            "n2o_kg": round(co2e * 0.0022, 4),
            "factor_used": factor,
            "factor_unit": f"kg CO2e/{factor_u}",
            "factor_source": factor_source,
            "factor_version": factor_version,
            "confidence": match.confidence,
            "match_method": match.match_method,
            "activity_value_converted": converted_qty,
            "converted_unit": factor_u
        }

    def calculate_scope_2(self, consumption_kwh: float, country: str, market_factor: Optional[float] = None, factor_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Indirect emissions from electricity consumption.
        Hierarchy: Supplier-specific contractual factor -> Residual Mix -> Grid Average Factor
        """
        if factor_id:
            loc_match = self.factor_service.get_factor_by_id(factor_id)
        else:
            loc_match = None

        if not loc_match:
            loc_match = self.factor_service.get_factor(f"Electricity {country}", scope="Scope 2", unit="kwh", region=country)

        loc_u = loc_match.unit
        loc_version = loc_match.factor_version
        
        # Enforce confidence check
        if loc_match.confidence < 0.95:
            loc_factor = 0.0
            loc_co2e = 0.0
            mkt_factor = 0.0
            mkt_co2e = 0.0
            loc_source = "Unmapped (Requires Auditor Assignment)"
            mkt_source = "Unmapped"
            mkt_version = loc_version
            converted_qty = consumption_kwh
            warnings = ["Confidence < 95% - Manual Review Required."]
        else:
            loc_factor = loc_match.emission_factor
            loc_source = loc_match.factor_source
            converted_qty = self.convert_units(consumption_kwh, "kwh", loc_u)
            loc_co2e = converted_qty * loc_factor
            
            # Calculate Market-Based Hierarchy
            warnings = []
            if market_factor is not None:
                mkt_factor = float(market_factor)
                mkt_source = "Supplier-specific Contractual"
                mkt_version = "2026.1"
            else:
                res_match = self.factor_service.get_factor(f"Residual Mix {country}", scope="Scope 2", unit="kwh", region=country)
                if res_match and res_match.match_method != "fallback" and res_match.confidence >= 0.95:
                    mkt_factor = res_match.emission_factor
                    mkt_source = res_match.factor_source
                    mkt_version = res_match.factor_version
                else:
                    mkt_factor = loc_factor
                    mkt_source = loc_source
                    mkt_version = loc_version
                    warnings.append("Supplier-specific contractual factor and Residual Mix unavailable. Falling back to Grid Average Factor.")
            mkt_co2e = converted_qty * mkt_factor
        
        return {
            "location_based_co2e_kg": round(loc_co2e, 4),
            "market_based_co2e_kg": round(mkt_co2e, 4),
            "location_factor": loc_factor,
            "market_factor": mkt_factor,
            "factor_used": loc_factor,
            "factor_unit": f"kg CO2e/{loc_u}",
            "factor_source": loc_source,
            "factor_version": loc_version,
            "market_source": mkt_source,
            "market_version": mkt_version,
            "confidence": loc_match.confidence,
            "match_method": loc_match.match_method,
            "activity_value_converted": converted_qty,
            "converted_unit": loc_u,
            "warnings": warnings
        }

    def calculate_scope_3_category_1(self, material: str, quantity: float, unit: str, factor_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Scope 3 Category 1: Purchased Goods and Services.
        Formula: Activity Quantity * Activity Emission Factor
        """
        if factor_id:
            match = self.factor_service.get_factor_by_id(factor_id)
        else:
            match = None

        if not match:
            match = self.factor_service.get_factor(material, scope="Scope 3", unit=unit)

        factor_u = match.unit
        factor_version = match.factor_version
        
        # Enforce confidence check
        if match.confidence < 0.95:
            factor = 0.0
            co2e = 0.0
            converted_qty = quantity
            factor_source = "Unmapped (Requires Auditor Assignment)"
        else:
            factor = match.emission_factor
            factor_source = match.factor_source
            # Unit mismatch protection: convert quantity to factor's UOM
            converted_qty = self.convert_units(quantity, unit, factor_u)
            co2e = converted_qty * factor
        
        return {
            "co2e_kg": round(co2e, 4),
            "factor_used": factor,
            "factor_unit": f"kg CO2e/{factor_u}",
            "factor_source": factor_source,
            "factor_version": factor_version,
            "confidence": match.confidence,
            "match_method": match.match_method,
            "activity_value_converted": converted_qty,
            "converted_unit": factor_u
        }

    def calculate_scope_3_category_4(self, weight_tonnes: float, distance_km: float, mode: str, factor_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Scope 3 Category 4: Upstream Transportation.
        """
        if factor_id:
            match = self.factor_service.get_factor_by_id(factor_id)
        else:
            match = None

        if not match:
            match = self.factor_service.get_factor(f"Freight Transport {mode}", scope="Scope 3", unit="tonne.km")

        factor_u = match.unit
        factor_version = match.factor_version
        
        # Enforce confidence check
        if match.confidence < 0.95:
            factor = 0.0
            co2e = 0.0
            activity_value = weight_tonnes * distance_km
            factor_source = "Unmapped (Requires Auditor Assignment)"
        else:
            factor = match.emission_factor
            factor_source = match.factor_source
            activity_value = weight_tonnes * distance_km
            co2e = activity_value * factor
        
        return {
            "co2e_kg": round(co2e, 4),
            "factor_used": factor,
            "factor_unit": f"kg CO2e/{factor_u}",
            "factor_source": factor_source,
            "factor_version": factor_version,
            "confidence": match.confidence,
            "match_method": match.match_method,
            "activity_value_converted": activity_value,
            "converted_unit": factor_u
        }

    def calculate_cbam_embedded_emissions(self, production_weight_tonnes: float, direct_emissions_kg: float, indirect_emissions_kg: float) -> Dict[str, Any]:
        """
        Calculates specific embedded emissions per tonne of product.
        """
        if production_weight_tonnes <= 0:
            return {"specific_direct_t_per_t": 0.0, "specific_indirect_t_per_t": 0.0, "total_specific_t_per_t": 0.0}
            
        direct_t = direct_emissions_kg / 1000.0
        indirect_t = indirect_emissions_kg / 1000.0
        
        specific_direct = direct_t / production_weight_tonnes
        specific_indirect = indirect_t / production_weight_tonnes
        
        return {
            "specific_direct_t_per_t": round(specific_direct, 6),
            "specific_indirect_t_per_t": round(specific_indirect, 6),
            "total_specific_t_per_t": round(specific_direct + specific_indirect, 6)
        }

    def calculate_footprints(self, scope_1_list: list, scope_2_list: list, scope_3_list: list) -> Dict[str, Any]:
        """
        Aggregates emissions to compute multiple footprints.
        """
        s1 = sum(item.get("co2e_kg", 0.0) for item in scope_1_list)
        s2_loc = sum(item.get("location_based_co2e_kg", 0.0) for item in scope_2_list)
        s2_mkt = sum(item.get("market_based_co2e_kg", 0.0) for item in scope_2_list)
        s3 = sum(item.get("co2e_kg", 0.0) for item in scope_3_list)
        
        total_loc = s1 + s2_loc + s3
        total_mkt = s1 + s2_mkt + s3
        
        return {
            "scope_1_co2e_kg": round(s1, 2),
            "scope_2_location_co2e_kg": round(s2_loc, 2),
            "scope_2_market_co2e_kg": round(s2_mkt, 2),
            "scope_3_co2e_kg": round(s3, 2),
            "organization_footprint_location_co2e_kg": round(total_loc, 2),
            "organization_footprint_market_co2e_kg": round(total_mkt, 2)
        }

if __name__ == "__main__":
    engine = CalculationEngine()
    print("Scope 1:", engine.calculate_scope_1("diesel", 100, "liters"))
    print("Scope 2:", engine.calculate_scope_2(1000, "DE"))
    print("Scope 3 Category 1:", engine.calculate_scope_3_category_1("steel", 5, "t"))
    print("Scope 3 Category 4:", engine.calculate_scope_3_category_4(15.4, 250.0, "road"))
    print("CBAM Embedded:", engine.calculate_cbam_embedded_emissions(15.4, 3000, 1500))
