import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional

from services.table_detection_service import TableDetectionService
from services.field_extraction_service import FieldExtractionService

class ParserService:
    """
    Coordinator parser that utilizes TableDetectionService and FieldExtractionService
    to output structural records along with individual field extraction confidence metrics.
    """
    def __init__(self):
        self.table_detector = TableDetectionService()
        self.field_extractor = FieldExtractionService()

    def parse_structural_file(self, 
                             file_path: str, 
                             filename: str, 
                             document_type: str = "ERP Export") -> List[Dict[str, Any]]:
        """
        Parses structured files (Excel, CSV, JSON) directly into standardize records.
        """
        ext = os.path.splitext(filename)[1].lower()
        records = []
        
        if ext in [".xlsx", ".xls"]:
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name)
                # Parse df using field extractor (simulate table with high confidence)
                tbl = [{"headers": list(df.columns), "rows": df.values.tolist(), "page": 1, "confidence": 0.99}]
                sheet_records = self.field_extractor.extract_fields(document_type, "", tbl, filename)
                records.extend(sheet_records)
        elif ext == ".csv":
            df = pd.read_csv(file_path)
            tbl = [{"headers": list(df.columns), "rows": df.values.tolist(), "page": 1, "confidence": 0.99}]
            records = self.field_extractor.extract_fields(document_type, "", tbl, filename)
        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            for idx, item in enumerate(items, start=1):
                rec = self.field_extractor._standardize_and_score(item, document_type, filename, page_num=1, row_idx=idx, table_conf=0.99)
                records.append(rec)
                
        return records

    def parse_ocr_extract(self, 
                          ocr_result: Dict[str, Any], 
                          document_type: str, 
                          filename: str) -> List[Dict[str, Any]]:
        """
        Detects tables and extracts fields from OCR results using TableDetectionService and FieldExtractionService.
        """
        # Step 4: Table Detection
        detected_tables = self.table_detector.detect_tables(ocr_result)
        
        # Step 5: Field Extraction
        ocr_text = ocr_result.get("text", "")
        return self.field_extractor.extract_fields(document_type, ocr_text, detected_tables, filename)
