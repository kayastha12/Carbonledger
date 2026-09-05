import os
import json
import re
from typing import Dict, Any, Tuple, Optional, List
from difflib import SequenceMatcher

class NormalizationEngine:
    def __init__(self, taxonomy_dir: str = None, fuzzy_threshold: float = 0.90, review_threshold: float = 0.75):
        if not taxonomy_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            taxonomy_dir = os.path.join(base_dir, "config", "taxonomy")
            
        self.taxonomy_dir = taxonomy_dir
        self.fuzzy_threshold = fuzzy_threshold
        self.review_threshold = review_threshold
        
        self.materials = self._load_taxonomy("materials.json")
        self.fuels = self._load_taxonomy("fuels.json")
        self.energy = self._load_taxonomy("energy.json")
        self.transportation = self._load_taxonomy("transportation.json")
        self.units = self._load_taxonomy("units.json")
        self.countries = self._load_taxonomy("countries.json")
        self.currencies = self._load_taxonomy("currencies.json")

    def _load_taxonomy(self, filename: str) -> Dict[str, list]:
        path = os.path.join(self.taxonomy_dir, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def fuzzy_match(self, query: str, choices: Dict[str, List[str]]) -> Tuple[Optional[str], float]:
        """
        Performs fuzzy matching on choices. Returns (canonical_name, confidence).
        """
        query_clean = query.lower().strip()
        best_canonical = None
        best_ratio = 0.0
        
        # Exact match check first
        for canonical, aliases in choices.items():
            if query_clean == canonical.lower() or any(alias.lower() == query_clean for alias in aliases):
                return canonical, 1.0
                
        # Fuzzy match choices
        for canonical, aliases in choices.items():
            # Check canonical name
            ratio = SequenceMatcher(None, query_clean, canonical.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_canonical = canonical
                
            # Check aliases
            for alias in aliases:
                ratio = SequenceMatcher(None, query_clean, alias.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_canonical = canonical
                    
        return best_canonical, best_ratio

    def ocr_correct(self, text: str) -> str:
        """
        Performs conservative OCR typo corrections.
        """
        if not text:
            return text
        cleaned = text.strip()
        low = cleaned.lower()
        if low == "steei":
            return "Steel"
        if low in ["aluminlum", "aluminum"]:
            return "Aluminium"
        if low == "dieset":
            return "Diesel"
        if low == "natral gas":
            return "Natural Gas"
        if cleaned == "0":
            return "0"
        return cleaned

    def normalize_value(self, text: str, context_country: str = "IN") -> Tuple[Optional[float], Optional[str], Dict[str, Any]]:
        """
        Parses text like "25 MT" or "₹50,000" into (numeric_value, normalized_unit, audit_trail).
        """
        audit = {
            "original_value": text,
            "normalized_value": None,
            "normalization_type": "number_and_unit",
            "rule_used": "regex_numeric_extraction",
            "confidence": 1.0,
            "requires_review": False
        }
        
        if not text:
            audit["requires_review"] = True
            return None, None, audit
            
        cleaned = self.ocr_correct(text)
        
        # Parse currency symbols
        currency = None
        for curr, aliases in self.currencies.items():
            for alias in aliases:
                if alias in cleaned:
                    currency = curr
                    cleaned = cleaned.replace(alias, "")
                    break
            if currency:
                break
                
        # Handle international number formats
        # If comma is decimal separator (e.g. 5.420,50 in some European formats or 5,420.50 US/IN format)
        if "," in cleaned and "." in cleaned:
            # Check position of the last symbol
            comma_idx = cleaned.rfind(",")
            dot_idx = cleaned.rfind(".")
            if comma_idx > dot_idx:  # Comma is decimal separator (e.g. 5.420,50)
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:  # Dot is decimal separator (e.g. 5,420.50)
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            # Ambiguous single separator, e.g. "5,420"
            # In India/US, "5,420" means 5420. In Europe it could mean 5.420.
            if context_country in ["US", "IN"]:
                cleaned = cleaned.replace(",", "")
            else:
                # If it has 3 digits after comma, it's thousands separator
                parts = cleaned.split(",")
                if len(parts[-1]) == 3:
                    cleaned = cleaned.replace(",", "")
                else:
                    cleaned = cleaned.replace(",", ".")
                    
        match = re.search(r"([\d\.]+)\s*(.*)", cleaned)
        if not match:
            audit["requires_review"] = True
            return None, None, audit
            
        val_str = match.group(1)
        unit_str = match.group(2).strip()
        
        try:
            val = float(val_str)
        except ValueError:
            audit["requires_review"] = True
            return None, None, audit
            
        # Normalize unit
        norm_unit = self.normalize_unit(unit_str)
        
        audit["normalized_value"] = {"value": val, "unit": norm_unit}
        return val, norm_unit, audit

    def normalize_unit(self, unit_str: str) -> Optional[str]:
        if not unit_str:
            return None
        unit_str_lower = unit_str.lower().strip()
        for canonical, aliases in self.units.items():
            if unit_str_lower == canonical.lower() or any(alias.lower() == unit_str_lower for alias in aliases):
                return canonical
                
        # Token word fallback for merged columns (e.g. "mt 21250.00")
        words = re.findall(r"[a-zA-Z]+", unit_str_lower)
        for w in words:
            for canonical, aliases in self.units.items():
                if w == canonical.lower() or any(alias.lower() == w for alias in aliases):
                    return canonical
        return unit_str_lower

    def normalize_material(self, material_str: str) -> Dict[str, Any]:
        """Returns material audit trail"""
        corrected = self.ocr_correct(material_str)
        canonical, confidence = self.fuzzy_match(corrected, self.materials)
        
        # Refuse ambiguous metal mapping
        requires_review = False
        if corrected.lower() == "metal" and canonical == "Steel":
            requires_review = True
            confidence = 0.60
            
        if confidence < self.review_threshold:
            requires_review = True
            canonical = None
            
        category = "Metals" if canonical in ["Steel", "Aluminium", "Copper"] else "Other"
        if canonical in ["Plastic"]:
            category = "Plastics"
            
        return {
            "original_value": material_str,
            "normalized_value": canonical,
            "category": category,
            "subcategory": canonical,
            "normalization_type": "material_taxonomy",
            "rule_used": "fuzzy_match" if confidence < 1.0 else "exact_match",
            "confidence": round(confidence, 2),
            "requires_review": requires_review or (confidence < self.fuzzy_threshold)
        }

    def normalize_fuel(self, fuel_str: str) -> Dict[str, Any]:
        corrected = self.ocr_correct(fuel_str)
        canonical, confidence = self.fuzzy_match(corrected, self.fuels)
        
        requires_review = confidence < self.fuzzy_threshold
        if confidence < self.review_threshold:
            requires_review = True
            canonical = None
            
        category = "Liquid Fuel" if canonical in ["Diesel", "Petrol", "Biodiesel"] else "Gaseous Fuel"
        if canonical == "Coal":
            category = "Solid Fuel"
            
        return {
            "original_value": fuel_str,
            "normalized_value": canonical,
            "category": category,
            "normalization_type": "fuel_taxonomy",
            "rule_used": "fuzzy_match" if confidence < 1.0 else "exact_match",
            "confidence": round(confidence, 2),
            "requires_review": requires_review
        }

    def normalize_transport(self, transport_str: str) -> Dict[str, Any]:
        corrected = self.ocr_correct(transport_str)
        canonical, confidence = self.fuzzy_match(corrected, self.transportation)
        
        requires_review = confidence < self.fuzzy_threshold
        if confidence < self.review_threshold:
            requires_review = True
            canonical = "Unknown"
            
        return {
            "original_value": transport_str,
            "normalized_value": canonical,
            "normalization_type": "transportation_taxonomy",
            "rule_used": "fuzzy_match",
            "confidence": round(confidence, 2),
            "requires_review": requires_review
        }

    def normalize_country(self, country_str: str) -> Dict[str, Any]:
        corrected = self.ocr_correct(country_str)
        canonical, confidence = self.fuzzy_match(corrected, self.countries)
        
        requires_review = confidence < self.fuzzy_threshold
        code_map = {"India": "IN", "United States": "US", "United Kingdom": "GB", "Germany": "DE", "China": "CN", "Netherlands": "NL"}
        
        return {
            "original_value": country_str,
            "normalized_value": canonical,
            "country_code": code_map.get(canonical, "IN"),
            "normalization_type": "country_taxonomy",
            "rule_used": "fuzzy_match",
            "confidence": round(confidence, 2),
            "requires_review": requires_review
        }

    def normalize_currency(self, currency_str: str) -> Dict[str, Any]:
        corrected = self.ocr_correct(currency_str)
        canonical, confidence = self.fuzzy_match(corrected, self.currencies)
        return {
            "original_value": currency_str,
            "normalized_value": canonical,
            "normalization_type": "currency_taxonomy",
            "rule_used": "fuzzy_match",
            "confidence": round(confidence, 2),
            "requires_review": confidence < self.fuzzy_threshold
        }

    def normalize_date(self, date_str: str, context_country: str = "IN") -> Dict[str, Any]:
        """
        Parses date variations: 05/08/2026, 05-08-2026, 2026-08-05, 05 Aug 2026, etc.
        """
        audit = {
            "original_value": date_str,
            "normalized_value": None,
            "normalization_type": "date_formatting",
            "rule_used": "date_regex_parse",
            "confidence": 1.0,
            "requires_review": False
        }
        
        if not date_str:
            audit["requires_review"] = True
            return audit
            
        cleaned = date_str.strip()
        
        # Format 1: YYYY-MM-DD
        match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", cleaned)
        if match:
            audit["normalized_value"] = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
            return audit
            
        # Format 2: DD Aug YYYY or Aug DD, YYYY
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        month_pattern = r"(" + "|".join(months) + r")[a-z]*"
        
        match = re.search(r"(\d{1,2})\s+" + month_pattern + r"\s+(\d{4})", cleaned, re.IGNORECASE)
        if match:
            m_idx = months.index(match.group(2).lower()[:3]) + 1
            audit["normalized_value"] = f"{match.group(3)}-{m_idx:02d}-{int(match.group(1)):02d}"
            return audit
            
        match = re.search(month_pattern + r"\s+(\d{1,2}),?\s+(\d{4})", cleaned, re.IGNORECASE)
        if match:
            m_idx = months.index(match.group(1).lower()[:3]) + 1
            audit["normalized_value"] = f"{match.group(3)}-{m_idx:02d}-{int(match.group(2)):02d}"
            return audit
            
        # Format 3: DD/MM/YYYY or MM/DD/YYYY (ambiguous)
        match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", cleaned)
        if match:
            p1 = int(match.group(1))
            p2 = int(match.group(2))
            year = match.group(3)
            
            if p1 > 12:  # Must be DD/MM/YYYY
                audit["normalized_value"] = f"{year}-{p2:02d}-{p1:02d}"
            elif p2 > 12:  # Must be MM/DD/YYYY
                audit["normalized_value"] = f"{year}-{p1:02d}-{p2:02d}"
            else:
                # Ambiguous! Use context_country
                audit["requires_review"] = True
                if context_country == "US": # MM/DD/YYYY
                    audit["normalized_value"] = f"{year}-{p1:02d}-{p2:02d}"
                    audit["confidence"] = 0.70
                else: # DD/MM/YYYY
                    audit["normalized_value"] = f"{year}-{p2:02d}-{p1:02d}"
                    audit["confidence"] = 0.70
            return audit
            
        audit["requires_review"] = True
        return audit

    def convert_unit(self, val: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """
        Performs safe unit conversions.
        """
        fu = self.normalize_unit(from_unit)
        tu = self.normalize_unit(to_unit)
        
        if fu == tu:
            return {"status": "success", "value": val, "unit": tu}
            
        if fu == "tonne" and tu == "kg":
            return {"status": "success", "value": val * 1000.0, "unit": "kg"}
        if fu == "kg" and tu == "tonne":
            return {"status": "success", "value": val / 1000.0, "unit": "tonne"}
            
        return {"status": "conversion_not_available", "requires_review": True}
