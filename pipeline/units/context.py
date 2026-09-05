import re
from typing import Dict, Any, Optional, List
from pipeline.units.normalizer import UnitNormalizer

class UnitContextManager:
    def __init__(self):
        self.normalizer = UnitNormalizer()

    def extract_header_unit(self, header_text: str) -> Optional[str]:
        """
        Parses column headers like "Quantity (MT)" or "Weight (kg)"
        """
        if not header_text:
            return None
        # Look for parentheses content
        match = re.search(r"\(([^)]+)\)", header_text)
        if match:
            unit_candidate = match.group(1).strip()
            norm = self.normalizer.normalize(unit_candidate)
            if norm:
                return norm
        return None

    def find_nearby_unit(self, words: List[Dict[str, Any]], target_bbox: List[float], max_distance: float = 50.0) -> Optional[str]:
        """
        Finds raw unit tokens in surrounding word coordinates
        """
        tx_min, ty_min, tx_max, ty_max = target_bbox
        for word in words:
            text = word.get("text", "")
            bbox = word.get("boundingBox", [0, 0, 0, 0])
            wx_min, wy_min, wx_max, wy_max = bbox
            
            # Check spatial distance (horizontal or vertical separation)
            dist_x = min(abs(tx_min - wx_max), abs(wx_min - tx_max))
            dist_y = min(abs(ty_min - wy_max), abs(wy_min - ty_max))
            
            if dist_x < max_distance and dist_y < 15.0:
                norm = self.normalizer.normalize(text)
                if norm:
                    return norm
        return None
