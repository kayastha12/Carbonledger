import re
from typing import Dict, Any, Optional

class UnitNormalizer:
    # Dimensions Mapping
    DIMENSIONS = {
        "tonne": "MASS",
        "kg": "MASS",
        "g": "MASS",
        "mg": "MASS",
        "liter": "VOLUME",
        "m3": "VOLUME",
        "kWh": "ENERGY",
        "MWh": "ENERGY",
        "MJ": "ENERGY",
        "GJ": "ENERGY",
        "km": "DISTANCE",
        "mile": "DISTANCE",
        "tCO2e": "EMISSION",
        "kgCO2e": "EMISSION"
    }
    
    # Conversions relative to canonical base
    CONVERSIONS = {
        # MASS base: kg
        "kg": {"base": "kg", "factor": 1.0},
        "tonne": {"base": "kg", "factor": 1000.0},
        "g": {"base": "kg", "factor": 0.001},
        "mg": {"base": "kg", "factor": 0.000001},
        
        # VOLUME base: liter
        "liter": {"base": "liter", "factor": 1.0},
        "m3": {"base": "liter", "factor": 1000.0},
        
        # ENERGY base: kWh
        "kWh": {"base": "kWh", "factor": 1.0},
        "MWh": {"base": "kWh", "factor": 1000.0},
        "MJ": {"base": "kWh", "factor": 0.277778},
        "GJ": {"base": "kWh", "factor": 277.778},
        
        # DISTANCE base: km
        "km": {"base": "km", "factor": 1.0},
        "mile": {"base": "km", "factor": 1.60934}
    }
    
    # Mapping raw variations to canonical unit
    ALIASES = {
        "kg": ["kg", "kgs", "kilogram", "kilograms", "kilo", "kilos"],
        "tonne": ["mt", "ton", "tonne", "tonnes", "metric ton", "metric tons"],
        "g": ["g", "gram", "grams"],
        "mg": ["mg", "milligram", "milligrams"],
        "liter": ["l", "liter", "liters", "litre", "litres", "ltr", "ltrs"],
        "m3": ["m3", "m³", "cubic meter", "cubic metre"],
        "kWh": ["kwh", "kw-h", "kilowatt hour", "kilowatt-hour", "kilowatt hours", "kilowatt-hours", "unit", "units"],
        "MWh": ["mwh", "megawatt hour", "megawatt hours"],
        "km": ["km", "kms", "kilometer", "kilometre", "kilometers", "kilometres"],
        "mile": ["mile", "miles", "mi"]
    }

    def normalize(self, raw_token: str) -> Optional[str]:
        if not raw_token:
            return None
        lbl = raw_token.lower().strip().replace(".", "")
        for canonical, aliases in self.ALIASES.items():
            if lbl == canonical.lower() or any(alias.lower() == lbl for alias in aliases):
                return canonical
        return None

    def get_dimension(self, unit: str) -> Optional[str]:
        return self.DIMENSIONS.get(unit)

    def convert(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        norm_from = self.normalize(from_unit)
        norm_to = self.normalize(to_unit)
        
        if not norm_from or not norm_to:
            return {"status": "error", "message": "Unknown units"}
            
        dim_from = self.get_dimension(norm_from)
        dim_to = self.get_dimension(norm_to)
        
        if dim_from != dim_to:
            return {"status": "error", "message": f"Incompatible dimensions: {dim_from} vs {dim_to}"}
            
        cfg_from = self.CONVERSIONS.get(norm_from)
        cfg_to = self.CONVERSIONS.get(norm_to)
        
        if not cfg_from or not cfg_to or cfg_from["base"] != cfg_to["base"]:
            return {"status": "error", "message": "Unconvertible dimension bases"}
            
        # Convert to base, then to target
        value_in_base = value * cfg_from["factor"]
        target_value = value_in_base / cfg_to["factor"]
        
        return {
            "status": "success",
            "value": round(target_value, 4),
            "unit": norm_to
        }
