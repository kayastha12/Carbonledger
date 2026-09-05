import re
from typing import Dict, Any, Optional, Tuple

class UnitDetector:
    # OCR Correction matches
    OCR_MAP = {
        "kwh": "kWh",
        "iiter": "liter",
        "mt": "tonne",
        "kgs": "kg"
    }

    def detect_raw_unit(self, text: str) -> Optional[str]:
        if not text:
            return None
        # Clean spacing
        clean = text.strip()
        # Look for standard patterns
        match = re.search(r"\b([a-zA-Z³]+)\b", clean)
        if match:
            return match.group(1)
        return None

    def split_merged_token(self, token: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Splits merged tokens like "25MT" or "mt21250" into (value, raw_unit)
        """
        if not token:
            return None, None
        token = token.strip()
        
        # Pattern 1: Number followed by unit (e.g., 25MT, 25-MT)
        match1 = re.match(r"^([\d\.,\-]+)\s*([a-zA-Z³]+)$", token)
        if match1:
            val_str = match1.group(1).replace("-", "").strip()
            try:
                return float(val_str), match1.group(2)
            except ValueError:
                pass
                
        # Pattern 2: Unit followed by number (e.g., MT25)
        match2 = re.match(r"^([a-zA-Z³]+)\s*([\d\.,\-]+)$", token)
        if match2:
            val_str = match2.group(2).replace("-", "").strip()
            try:
                return float(val_str), match2.group(1)
            except ValueError:
                pass
                
        return None, None

    def apply_ocr_correction(self, raw_unit: str) -> Tuple[str, Optional[str]]:
        """
        Returns (corrected_unit, rule_name_if_applied)
        """
        low = raw_unit.lower()
        if low in self.OCR_MAP:
            return self.OCR_MAP[low], f"ocr.{low}"
        return raw_unit, None
