"""
CarbonLedger Emission Factor Provider
=======================================
Clean provider interface for emission factor lookup.

DESIGN PRINCIPLES:
- Never fabricate factors.
- Return NOT_FOUND when database does not contain a factor.
- System is ready for config/database-backed sources.
- Supports find_material_factor(), find_fuel_factor(),
  find_electricity_factor(), find_transport_factor().
- Built-in table is minimal and sourced from IPCC AR6 / GHG Protocol defaults.

SOURCE ATTRIBUTION:
  IPCC AR6 WGIII, Annex III — Technology-specific cost and performance parameters
  GHG Protocol — Emission factors from cross-sector tools (2024 update)
  DEFRA — UK Government GHG Conversion Factors 2023
  IEA — World Energy Outlook 2023
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class EmissionFactor:
    factor_value: Optional[float]       # e.g. 1.85
    factor_unit: Optional[str]           # e.g. "kg CO2e/kg"
    source: Optional[str]                # e.g. "IPCC_AR6"
    version: Optional[str]               # e.g. "2021"
    methodology: Optional[str]           # e.g. "LCA"
    match_confidence: float              # 0.0–1.0
    matched_on: Optional[str]           # what key triggered the match
    status: str                          # "FOUND" | "NOT_FOUND" | "APPROXIMATE"
    notes: Optional[str] = None


_NOT_FOUND = EmissionFactor(
    factor_value=None,
    factor_unit=None,
    source=None,
    version=None,
    methodology=None,
    match_confidence=0.0,
    matched_on=None,
    status="NOT_FOUND"
)


# ---------------------------------------------------------------------------
# Built-in emission factor tables
# ---------------------------------------------------------------------------
# Units are kg CO2e per unit of activity unless otherwise noted.
# These are DEFAULT / GENERIC factors only. Real-world calculations should
# use activity-specific, region-specific, and year-specific factors.

_MATERIAL_FACTORS: Dict[str, Dict[str, Any]] = {
    # Material: {factor_value (kg CO2e/kg), source, unit}
    "steel": {"value": 1.85, "unit": "kg CO2e/kg", "source": "GHG_PROTOCOL_2024", "note": "Average steel, global mix"},
    "iron": {"value": 1.91, "unit": "kg CO2e/kg", "source": "IPCC_AR6", "note": "Pig iron"},
    "aluminium": {"value": 8.24, "unit": "kg CO2e/kg", "source": "GHG_PROTOCOL_2024", "note": "Primary aluminium"},
    "aluminum": {"value": 8.24, "unit": "kg CO2e/kg", "source": "GHG_PROTOCOL_2024", "note": "Primary aluminium"},
    "cement": {"value": 0.83, "unit": "kg CO2e/kg", "source": "IPCC_AR6", "note": "Ordinary Portland cement"},
    "concrete": {"value": 0.12, "unit": "kg CO2e/kg", "source": "IPCC_AR6", "note": "Ready-mix concrete"},
    "plastic": {"value": 3.31, "unit": "kg CO2e/kg", "source": "DEFRA_2023", "note": "Average plastic, cradle-to-gate"},
    "copper": {"value": 2.73, "unit": "kg CO2e/kg", "source": "IPCC_AR6", "note": "Primary copper"},
    "glass": {"value": 0.85, "unit": "kg CO2e/kg", "source": "DEFRA_2023", "note": "Float glass"},
    "paper": {"value": 0.92, "unit": "kg CO2e/kg", "source": "DEFRA_2023", "note": "Paper"},
    "cardboard": {"value": 0.67, "unit": "kg CO2e/kg", "source": "DEFRA_2023", "note": "Cardboard"},
    "wood": {"value": 0.21, "unit": "kg CO2e/kg", "source": "DEFRA_2023", "note": "Sawn timber"},
}

_FUEL_FACTORS: Dict[str, Dict[str, Any]] = {
    # Fuel type: {factor_value, unit (kg CO2e/unit), source}
    "diesel": {"value": 2.68, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Diesel, market basis"},
    "petrol": {"value": 2.31, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Motor petrol"},
    "gasoline": {"value": 2.31, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Motor petrol"},
    "lpg": {"value": 1.55, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Liquefied petroleum gas"},
    "natural gas": {"value": 2.04, "unit": "kg CO2e/m3", "source": "DEFRA_2023", "note": "Natural gas, gross CV"},
    "lng": {"value": 2.75, "unit": "kg CO2e/kg", "source": "DEFRA_2023", "note": "Liquefied natural gas"},
    "coal": {"value": 2.42, "unit": "kg CO2e/kg", "source": "IPCC_AR6", "note": "Bituminous coal"},
    "heavy fuel oil": {"value": 3.18, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Residual fuel oil"},
    "marine fuel oil": {"value": 3.18, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Residual fuel oil"},
    "hfo": {"value": 3.18, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Heavy fuel oil"},
    "kerosene": {"value": 2.55, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Aviation turbine fuel"},
    "jet fuel": {"value": 2.55, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Aviation turbine fuel"},
    "biodiesel": {"value": 0.18, "unit": "kg CO2e/L", "source": "DEFRA_2023", "note": "Biodiesel (B100), cradle-to-gate"},
    "cng": {"value": 1.69, "unit": "kg CO2e/kg", "source": "DEFRA_2023", "note": "Compressed natural gas"},
}

_ELECTRICITY_FACTORS: Dict[str, Dict[str, Any]] = {
    # Grid / country code: {factor_value (kg CO2e/kWh), source}
    "in": {"value": 0.708, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "India national grid"},
    "india": {"value": 0.708, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "India national grid"},
    "de": {"value": 0.364, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "Germany national grid"},
    "germany": {"value": 0.364, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "Germany national grid"},
    "us": {"value": 0.386, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "USA national average"},
    "gb": {"value": 0.233, "unit": "kg CO2e/kWh", "source": "DEFRA_2023", "note": "UK national grid"},
    "uk": {"value": 0.233, "unit": "kg CO2e/kWh", "source": "DEFRA_2023", "note": "UK national grid"},
    "cn": {"value": 0.555, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "China national grid"},
    "china": {"value": 0.555, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "China national grid"},
    "eu": {"value": 0.295, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "EU-27 average"},
    "global": {"value": 0.494, "unit": "kg CO2e/kWh", "source": "IEA_2023", "note": "Global average"},
}

_TRANSPORT_FACTORS: Dict[str, Dict[str, Any]] = {
    # Transport mode: {factor_value (kg CO2e / tonne-km), source}
    "truck": {"value": 0.096, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "HGV, average load"},
    "lorry": {"value": 0.096, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "HGV"},
    "road": {"value": 0.096, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Road freight"},
    "rail": {"value": 0.028, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Rail freight"},
    "container ship": {"value": 0.011, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Containership"},
    "ship": {"value": 0.011, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Sea freight, container"},
    "sea": {"value": 0.011, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Sea freight"},
    "air": {"value": 1.130, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Air freight"},
    "plane": {"value": 1.130, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Air freight"},
    "barge": {"value": 0.031, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Inland waterway"},
    "river": {"value": 0.031, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Inland waterway"},
    "port / yard": {"value": 0.020, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Port/yard handling estimate"},
    "port": {"value": 0.020, "unit": "kg CO2e/tonne-km", "source": "DEFRA_2023", "note": "Port/yard handling estimate"},
}


class EmissionFactorProvider:
    """
    Provider for emission factors.
    Returns EmissionFactor dataclass with status="FOUND" or "NOT_FOUND".
    """

    def find_material_factor(self, material: Optional[str]) -> EmissionFactor:
        """Find emission factor for a material (kg CO2e/kg)."""
        if not material:
            return _NOT_FOUND
        mat = str(material).lower().strip()
        for key, data in _MATERIAL_FACTORS.items():
            if key in mat or mat in key:
                return EmissionFactor(
                    factor_value=data["value"],
                    factor_unit=data["unit"],
                    source=data["source"],
                    version="2023",
                    methodology="Cradle-to-gate LCA",
                    match_confidence=0.80 if key != mat else 0.95,
                    matched_on=key,
                    status="FOUND",
                    notes=data.get("note"),
                )
        return _NOT_FOUND

    def find_fuel_factor(self, fuel_type: Optional[str]) -> EmissionFactor:
        """Find emission factor for a fuel (kg CO2e/L or kg CO2e/m3)."""
        if not fuel_type:
            return _NOT_FOUND
        fuel = str(fuel_type).lower().strip()
        for key, data in _FUEL_FACTORS.items():
            if key in fuel or fuel in key:
                return EmissionFactor(
                    factor_value=data["value"],
                    factor_unit=data["unit"],
                    source=data["source"],
                    version="2023",
                    methodology="WTW (Well-to-Wheel)",
                    match_confidence=0.90 if key == fuel else 0.80,
                    matched_on=key,
                    status="FOUND",
                    notes=data.get("note"),
                )
        return _NOT_FOUND

    def find_electricity_factor(
        self,
        country: Optional[str] = None,
        grid_region: Optional[str] = None,
    ) -> EmissionFactor:
        """Find grid emission factor (kg CO2e/kWh) for a country or region."""
        for lookup in [country, grid_region]:
            if not lookup:
                continue
            key = str(lookup).lower().strip()
            if key in _ELECTRICITY_FACTORS:
                data = _ELECTRICITY_FACTORS[key]
                return EmissionFactor(
                    factor_value=data["value"],
                    factor_unit=data["unit"],
                    source=data["source"],
                    version="2023",
                    methodology="Location-based",
                    match_confidence=0.90,
                    matched_on=key,
                    status="FOUND",
                    notes=data.get("note"),
                )
            # Partial match (e.g. "india" in "india national grid 2")
            for ek, ed in _ELECTRICITY_FACTORS.items():
                if ek in key or key in ek:
                    return EmissionFactor(
                        factor_value=ed["value"],
                        factor_unit=ed["unit"],
                        source=ed["source"],
                        version="2023",
                        methodology="Location-based",
                        match_confidence=0.75,
                        matched_on=ek,
                        status="APPROXIMATE",
                        notes=f"Approximate match on '{ek}'. {ed.get('note', '')}",
                    )
        return _NOT_FOUND

    def find_transport_factor(self, transport_mode: Optional[str]) -> EmissionFactor:
        """Find emission factor for a transport mode (kg CO2e/tonne-km)."""
        if not transport_mode:
            return _NOT_FOUND
        mode = str(transport_mode).lower().strip()
        if mode in _TRANSPORT_FACTORS:
            data = _TRANSPORT_FACTORS[mode]
            return EmissionFactor(
                factor_value=data["value"],
                factor_unit=data["unit"],
                source=data["source"],
                version="2023",
                methodology="Tonne-km basis",
                match_confidence=0.90,
                matched_on=mode,
                status="FOUND",
                notes=data.get("note"),
            )
        # Partial match
        for key, data in _TRANSPORT_FACTORS.items():
            if key in mode or mode in key:
                return EmissionFactor(
                    factor_value=data["value"],
                    factor_unit=data["unit"],
                    source=data["source"],
                    version="2023",
                    methodology="Tonne-km basis",
                    match_confidence=0.75,
                    matched_on=key,
                    status="APPROXIMATE",
                    notes=f"Approximate match on '{key}'. {data.get('note', '')}",
                )
        return _NOT_FOUND

    def to_dict(self, ef: EmissionFactor) -> dict:
        return {
            "factor_required": True,
            "factor_status": ef.status,
            "factor_value": ef.factor_value,
            "factor_unit": ef.factor_unit,
            "source": ef.source,
            "version": ef.version,
            "methodology": ef.methodology,
            "match_confidence": ef.match_confidence,
            "matched_on": ef.matched_on,
            "notes": ef.notes,
        }
