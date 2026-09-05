import re
from typing import Dict, Any, List

def clean_cell_text(val: Any) -> str:
    """
    Cleans cell text by intelligently reconstructing broken tokens across newlines
    without joining unrelated tokens.
    """
    if val is None:
        return ""
    text = str(val).strip()
    if not text:
        return ""
    
    # Reconstruct hyphenated tokens across lines (e.g. "PO-\n2025-\n001" -> "PO-2025-001")
    text = re.sub(r'(\w+)-\s*\n\s*', r'\1-', text)
    # Reconstruct standard multi-line words with a single space (e.g. "Steel\nTraders" -> "Steel Traders")
    text = re.sub(r'\s*\n\s*', ' ', text)
    # Normalize multiple whitespace to single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class TableDetectionService:
    """
    Service for identifying and validating structured data tables from document OCR extracts.
    Filters out document cover cards, metadata boxes, summary matrices, and headers.
    """
    def __init__(self):
        pass

    def is_valid_data_table(self, headers: List[str], rows: List[List[str]]) -> bool:
        """
        Determines if a candidate table represents actual transactional activity rows
        rather than metadata blocks, title banners, or documentation grids.
        """
        if not rows:
            return False
            
        # Must have at least 2 columns to be a tabular data structure
        max_cols = max(len(headers), max((len(r) for r in rows), default=0))
        if max_cols < 2:
            return False
            
        # Check for documentation / metadata table signatures
        h_lower = [str(h).lower().strip() for h in headers]
        h_str = " ".join(h_lower)
        
        # Filter schema documentation tables (e.g. Table / Purpose)
        if h_lower == ["table", "purpose"] or "stores original uploaded files" in " ".join(" ".join(str(c) for c in r) for r in rows).lower():
            return False
            
        # Filter matrix overview tables (e.g. Element / Phase 1 / Phase 2 ...)
        if "phase 1" in h_str and "phase 2" in h_str:
            return False
            
        # Filter checkmark matrix grids (where cells are mostly checkmarks or dashes)
        total_cells = 0
        symbol_cells = 0
        for r in rows:
            for c in r:
                c_str = str(c).strip()
                total_cells += 1
                if c_str in ["✓", "—", "-", "x", "X", "yes", "no", ""]:
                    symbol_cells += 1
        if total_cells > 0 and (symbol_cells / total_cells) > 0.45:
            return False
            
        # Filter address / recipient header blocks (e.g. Name & Address of Recipient)
        if any("name & address" in h or "billed to" in h or "shipped to" in h for h in h_lower):
            return False
            
        # Filter commercial / summary cards (e.g. Material Weight, Commercial Data)
        if any("commercial data" in h or "material weight" in h or "import & manufacturing" in h for h in h_lower):
            return False
            
        # Filter invoice metadata key-value header grid (e.g. Invoice No., L.R. No., Place of Supply, etc.)
        if any("invoice no" in h or "invoice date" in h or "l.r. no" in h or "place of supply" in h or "po no" in h or "e-way bill" in h for h in h_lower) and not any(k in h_str for k in ["material description", "item description", "item code", "hsn", "packages", "qty", "quantity", "unit cost", "rate"]):
            return False
            
        return True

    def detect_tables(self, ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses OCR results, cleans table cells, and returns validated data tables.
        """
        extracted_tables = ocr_result.get("tables", [])
        detected = []
        
        for idx, tbl in enumerate(extracted_tables):
            raw_headers = tbl.get("headers", [])
            raw_rows = tbl.get("rows", [])
            page = tbl.get("page", 1)
            
            # Clean headers
            clean_headers = [clean_cell_text(h) for h in raw_headers]
            
            # Clean data rows
            clean_rows = []
            for row in raw_rows:
                cleaned_row = [clean_cell_text(cell) for cell in row]
                # Filter out completely empty rows
                if any(c != "" for c in cleaned_row):
                    clean_rows.append(cleaned_row)
                    
            if self.is_valid_data_table(clean_headers, clean_rows):
                detected.append({
                    "table_id": len(detected) + 1,
                    "page": page,
                    "headers": clean_headers,
                    "rows": clean_rows,
                    "confidence": tbl.get("confidence", 0.98)
                })
                
        return detected
