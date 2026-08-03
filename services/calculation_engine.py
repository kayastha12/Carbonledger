import pandas as pd

class CalculationEngine:
    def __init__(self, cleaned_factors_csv="d:/internship/carbonledger/preprocessing/master_factors_cleaned.csv"):
        self.factors_df = None
        if pd.io.common.file_exists(cleaned_factors_csv):
            self.factors_df = pd.read_csv(cleaned_factors_csv)

    def get_factor_record(self, factor_id):
        if self.factors_df is not None:
            matches = self.factors_df[self.factors_df["id"] == factor_id]
            if not matches.empty:
                return matches.iloc[0].to_dict()
        return None

    def get_factor(self, factor_id):
        rec = self.get_factor_record(factor_id)
        if rec:
            return float(rec["factor"])
        return 0.0

    def convert_units(self, value, from_unit, to_unit):
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
            return value
            
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
        return value

    def calculate_scope_1(self, fuel_type, quantity, unit, factor_id=None):
        """
        Direct emissions from fuel combustion.
        Formula: Fuel Quantity * Fuel Emission Factor
        """
        factor_rec = None
        if factor_id:
            factor_rec = self.get_factor_record(factor_id)
            
        if factor_rec:
            factor = float(factor_rec["factor"])
            factor_u = str(factor_rec.get("uom", "liters"))
            factor_source = factor_rec.get("source_sheet", "GHG Protocol")
            factor_version = factor_rec.get("factor_version", "2026.1")
        else:
            # Look up factor dynamically from self.factors_df based on fuel_type and unit
            factor = 2.68
            factor_u = "liters"
            factor_source = "Default Fallback"
            factor_version = "2026.1"
            if self.factors_df is not None:
                matches = self.factors_df[
                    (self.factors_df["scope"] == "Scope 1") & 
                    (self.factors_df["activity"].str.lower().str.contains(str(fuel_type).lower(), na=False))
                ]
                if not matches.empty:
                    # Prefer matching UOM
                    uom_matches = matches[matches["uom"].str.lower().str.strip() == str(unit).lower().strip()]
                    best_match = uom_matches.iloc[0] if not uom_matches.empty else matches.iloc[0]
                    factor = float(best_match["factor"])
                    factor_u = str(best_match["uom"])
                    factor_source = best_match["source_sheet"]
                    factor_version = best_match["factor_version"]

        # Convert quantity to the factor's UOM
        converted_qty = self.convert_units(quantity, unit, factor_u)
        co2e = converted_qty * factor
        
        return {
            "co2e_kg": co2e,
            "ch4_kg": co2e * 0.0008,
            "n2o_kg": co2e * 0.0022,
            "factor_used": factor,
            "factor_unit": f"kg CO2e/{factor_u}",
            "factor_source": factor_source,
            "factor_version": factor_version,
            "activity_value_converted": converted_qty,
            "converted_unit": factor_u
        }

    def calculate_scope_2(self, consumption_kwh, country, market_factor=None, factor_id=None):
        """
        Indirect emissions from electricity consumption.
        Hierarchy: Supplier-specific contractual factor -> Residual Mix -> Grid Average Factor
        """
        loc_factor = 0.38  # Default average
        loc_source = "Default Fallback"
        loc_version = "2026.1"
        loc_u = "kwh"
        
        # Grid average lookup
        if factor_id:
            factor_rec = self.get_factor_record(factor_id)
            if factor_rec:
                loc_factor = float(factor_rec["factor"])
                loc_u = str(factor_rec.get("uom", "kwh"))
                loc_source = factor_rec.get("source_sheet", "Grid Average")
                loc_version = factor_rec.get("factor_version", "2026.1")
        else:
            if self.factors_df is not None:
                matches = self.factors_df[
                    (self.factors_df["scope"] == "Scope 2") & 
                    (self.factors_df["category"].str.lower().str.contains("electricity", na=False)) &
                    (self.factors_df["uom"].str.lower().str.strip() == "kwh")
                ]
                if not matches.empty:
                    # Attempt country match
                    country_matches = matches[matches["activity"].str.lower().str.contains(str(country).lower(), na=False)]
                    best_match = country_matches.iloc[0] if not country_matches.empty else matches.iloc[0]
                    loc_factor = float(best_match["factor"])
                    loc_u = str(best_match["uom"])
                    loc_source = best_match["source_sheet"]
                    loc_version = best_match["factor_version"]

        # Calculate Location-Based
        converted_qty = self.convert_units(consumption_kwh, "kwh", loc_u)
        loc_co2e = converted_qty * loc_factor
        
        # Calculate Market-Based Hierarchy
        warnings = []
        if market_factor is not None:
            mkt_factor = market_factor
            mkt_source = "Supplier-specific Contractual"
            mkt_version = "2026.1"
        else:
            # Attempt lookup of Residual Mix from database (e.g. EU residual mix or country specific residual mix)
            # If not found, fallback to location factor with a warning
            mkt_factor = None
            mkt_source = None
            mkt_version = None
            
            if self.factors_df is not None:
                residual_matches = self.factors_df[
                    (self.factors_df["scope"] == "Scope 2") & 
                    (self.factors_df["activity"].str.lower().str.contains("residual mix", na=False))
                ]
                if not residual_matches.empty:
                    country_res = residual_matches[residual_matches["activity"].str.lower().str.contains(str(country).lower(), na=False)]
                    best_res = country_res.iloc[0] if not country_res.empty else residual_matches.iloc[0]
                    mkt_factor = float(best_res["factor"])
                    mkt_source = best_res["source_sheet"]
                    mkt_version = best_res["factor_version"]
            
            if mkt_factor is None:
                # Fallback to location based grid factor and raise warning
                mkt_factor = loc_factor
                mkt_source = loc_source
                mkt_version = loc_version
                warnings.append("Supplier-specific contractual factor and Residual Mix unavailable. Falling back to Grid Average Factor.")

        mkt_co2e = converted_qty * mkt_factor
        
        return {
            "location_based_co2e_kg": loc_co2e,
            "market_based_co2e_kg": mkt_co2e,
            "location_factor": loc_factor,
            "market_factor": mkt_factor,
            "factor_used": loc_factor,
            "factor_unit": f"kg CO2e/{loc_u}",
            "factor_source": loc_source,
            "factor_version": loc_version,
            "market_source": mkt_source,
            "market_version": mkt_version,
            "activity_value_converted": converted_qty,
            "converted_unit": loc_u,
            "warnings": warnings
        }

    def calculate_scope_3_category_1(self, material, quantity, unit, factor_id=None):
        """
        Scope 3 Category 1: Purchased Goods and Services.
        Formula: Activity Quantity * Activity Emission Factor
        """
        factor_rec = None
        if factor_id:
            factor_rec = self.get_factor_record(factor_id)
            
        if factor_rec:
            factor = float(factor_rec["factor"])
            factor_u = str(factor_rec.get("uom", "kg"))
            factor_source = factor_rec.get("source_sheet", "GHG Protocol")
            factor_version = factor_rec.get("factor_version", "2026.1")
        else:
            factor = 2.0
            factor_u = "kg"
            factor_source = "Default Fallback"
            factor_version = "2026.1"
            if self.factors_df is not None:
                matches = self.factors_df[
                    (self.factors_df["scope"] == "Scope 3") & 
                    (self.factors_df["activity"].str.lower().str.contains(str(material).lower(), na=False))
                ]
                if not matches.empty:
                    uom_matches = matches[matches["uom"].str.lower().str.strip() == str(unit).lower().strip()]
                    best_match = uom_matches.iloc[0] if not uom_matches.empty else matches.iloc[0]
                    factor = float(best_match["factor"])
                    factor_u = str(best_match["uom"])
                    factor_source = best_match["source_sheet"]
                    factor_version = best_match["factor_version"]

        # Unit mismatch protection: convert quantity to factor's UOM
        converted_qty = self.convert_units(quantity, unit, factor_u)
        co2e = converted_qty * factor
        
        return {
            "co2e_kg": co2e,
            "factor_used": factor,
            "factor_unit": f"kg CO2e/{factor_u}",
            "factor_source": factor_source,
            "factor_version": factor_version,
            "activity_value_converted": converted_qty,
            "converted_unit": factor_u
        }

    def calculate_scope_3_category_4(self, weight_tonnes, distance_km, mode, factor_id=None):
        """
        Scope 3 Category 4: Upstream Transportation.
        """
        factor_rec = None
        if factor_id:
            factor_rec = self.get_factor_record(factor_id)
            
        if factor_rec:
            factor = float(factor_rec["factor"])
            factor_u = str(factor_rec.get("uom", "tonne.km"))
            factor_source = factor_rec.get("source_sheet", "GHG Protocol")
            factor_version = factor_rec.get("factor_version", "2026.1")
        else:
            mode_factors = {
                "road": 0.15,
                "rail": 0.03,
                "sea": 0.015,
                "air": 0.60,
                "hgv": 0.15,
                "container ship": 0.015,
                "cargo plane": 0.60,
                "freight train": 0.03
            }
            factor = mode_factors.get(str(mode).lower(), 0.15)
            factor_u = "tonne.km"
            factor_source = "Default Fallback"
            factor_version = "2026.1"
            if self.factors_df is not None:
                matches = self.factors_df[
                    (self.factors_df["scope"] == "Scope 3") & 
                    (self.factors_df["activity"].str.lower().str.contains(str(mode).lower(), na=False))
                ]
                if not matches.empty:
                    best_match = matches.iloc[0]
                    factor = float(best_match["factor"])
                    factor_u = str(best_match["uom"])
                    factor_source = best_match["source_sheet"]
                    factor_version = best_match["factor_version"]

        activity_value = weight_tonnes * distance_km
        co2e = activity_value * factor
        
        return {
            "co2e_kg": co2e,
            "factor_used": factor,
            "factor_unit": f"kg CO2e/{factor_u}",
            "factor_source": factor_source,
            "factor_version": factor_version,
            "activity_value_converted": activity_value,
            "converted_unit": factor_u
        }

    def calculate_cbam_embedded_emissions(self, production_weight_tonnes, direct_emissions_kg, indirect_emissions_kg):
        """
        Calculates specific embedded emissions per tonne of product.
        """
        if production_weight_tonnes <= 0:
            return {"specific_direct_t": 0.0, "specific_indirect_t": 0.0, "total_specific_t": 0.0}
            
        direct_t = direct_emissions_kg / 1000.0
        indirect_t = indirect_emissions_kg / 1000.0
        
        specific_direct = direct_t / production_weight_tonnes
        specific_indirect = indirect_t / production_weight_tonnes
        
        return {
            "specific_direct_t_per_t": specific_direct,
            "specific_indirect_t_per_t": specific_indirect,
            "total_specific_t_per_t": specific_direct + specific_indirect
        }

    def calculate_footprints(self, scope_1_list, scope_2_list, scope_3_list):
        """
        Aggregates emissions to compute multiple footprints.
        """
        s1 = sum(item["co2e_kg"] for item in scope_1_list)
        s2_loc = sum(item["location_based_co2e_kg"] for item in scope_2_list)
        s2_mkt = sum(item["market_based_co2e_kg"] for item in scope_2_list)
        s3 = sum(item["co2e_kg"] for item in scope_3_list)
        
        total_loc = s1 + s2_loc + s3
        total_mkt = s1 + s2_mkt + s3
        
        return {
            "scope_1_co2e_kg": s1,
            "scope_2_location_co2e_kg": s2_loc,
            "scope_2_market_co2e_kg": s2_mkt,
            "scope_3_co2e_kg": s3,
            "organization_footprint_location_co2e_kg": total_loc,
            "organization_footprint_market_co2e_kg": total_mkt
        }

if __name__ == "__main__":
    engine = CalculationEngine()
    print("Scope 1:", engine.calculate_scope_1("diesel", 100, "liters"))
    print("Scope 2:", engine.calculate_scope_2(1000, "DE"))
    print("Scope 3 Category 1:", engine.calculate_scope_3_category_1("steel", 5, "t"))
    print("Scope 3 Category 4:", engine.calculate_scope_3_category_4(15.4, 250.0, "road"))
    print("CBAM Embedded:", engine.calculate_cbam_embedded_emissions(15.4, 3000, 1500))
