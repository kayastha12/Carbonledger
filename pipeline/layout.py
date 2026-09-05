import os
import re
from typing import List, Dict, Any, Tuple
from schemas.document import (
    LayoutResult, PageLayout, LayoutElement, KeyValueBlock,
    Table, TableRow, TableCell, TableHeader
)

class LayoutAnalyzer:
    def __init__(self):
        # Target keys to extract as key-values
        self.target_keys = [
            "invoice number", "invoice date", "date", "bill no", "account no", "account number",
            "quantity", "qty", "unit", "total amount", "total paid", "total bill amount",
            "distance", "customer", "fuel type", "port of loading", "port of discharge",
            "route", "gross weight", "weight", "description of goods", "description", "material", 
            "product", "electricity consumption", "supplier"
        ]

    def analyze(self, document: dict) -> LayoutResult:
        doc_id = document.get("file_name", "unknown_doc")
        page_layouts = []

        for page_data in document.get("pages", []):
            page_num = page_data.get("page_number", 1)
            words = page_data.get("words", [])
            
            # Reconstruct lines of text (Reading Order)
            lines = self._reconstruct_lines(words)
            
            # Detect Layout elements
            elements = []
            key_values = []
            tables = []
            
            # Detect Headers and Footers
            header_lines, footer_lines, body_lines = self._split_regions(lines)
            
            for line_text, bbox in header_lines:
                elements.append(LayoutElement(
                    type="HEADER",
                    text=line_text,
                    bbox=bbox,
                    page=page_num,
                    confidence=0.95
                ))
                
            for line_text, bbox in footer_lines:
                elements.append(LayoutElement(
                    type="FOOTER",
                    text=line_text,
                    bbox=bbox,
                    page=page_num,
                    confidence=0.95
                ))
                
            # Extract key-values and tables from body lines
            extracted_kvs, table_lines = self._extract_key_values_and_tables(body_lines, words)
            key_values.extend(extracted_kvs)
            
            # Detect and build tables
            detected_tables = self._detect_tables(table_lines, page_num)
            tables.extend(detected_tables)
            
            # Add general elements for KEY_VALUE and TABLE
            for kv in key_values:
                elements.append(LayoutElement(
                    type="KEY_VALUE",
                    text=f"{kv.key}: {kv.value}",
                    bbox=kv.bbox,
                    page=page_num,
                    confidence=kv.confidence
                ))
                
            for tbl in tables:
                elements.append(LayoutElement(
                    type="TABLE",
                    text=f"Table with {len(tbl.rows)} rows",
                    bbox=tbl.bbox,
                    page=page_num,
                    confidence=1.0
                ))
                
            page_layouts.append(PageLayout(
                page=page_num,
                elements=elements,
                key_values=key_values,
                tables=tables
            ))
            
        return LayoutResult(
            document_id=doc_id,
            pages=page_layouts
        )

    def _reconstruct_lines(self, words: List[dict], y_tolerance: float = 6.0) -> List[Tuple[str, List[float], List[dict]]]:
        """
        Groups words into lines based on vertical overlap and sorts them by reading order.
        Returns a list of (line_text, bbox, words_in_line).
        """
        if not words:
            return []
            
        # Sort words primarily by y_min (top) and then by x_min (left)
        # BBox format: [x0, y0, x1, y1]
        sorted_words = sorted(words, key=lambda w: (w["bbox"][1], w["bbox"][0]))
        
        lines = []
        current_line_words = []
        
        for w in sorted_words:
            if not current_line_words:
                current_line_words.append(w)
            else:
                # Check if this word's top coordinate is close to the current line's average top/bottom
                avg_y = sum(x["bbox"][1] for x in current_line_words) / len(current_line_words)
                if abs(w["bbox"][1] - avg_y) <= y_tolerance:
                    current_line_words.append(w)
                else:
                    # Sort current line words by left-to-right (x0)
                    current_line_words.sort(key=lambda x: x["bbox"][0])
                    lines.append(current_line_words)
                    current_line_words = [w]
                    
        if current_line_words:
            current_line_words.sort(key=lambda x: x["bbox"][0])
            lines.append(current_line_words)
            
        # Sort lines by top coordinate
        lines.sort(key=lambda l: sum(w["bbox"][1] for w in l)/len(l))
        
        formatted_lines = []
        for line in lines:
            line_text = " ".join(w["text"] for w in line)
            
            x0 = min(w["bbox"][0] for w in line)
            y0 = min(w["bbox"][1] for w in line)
            x1 = max(w["bbox"][2] for w in line)
            y1 = max(w["bbox"][3] for w in line)
            
            formatted_lines.append((line_text, [x0, y0, x1, y1], line))
            
        return formatted_lines

    def _split_regions(self, lines: List[Tuple[str, List[float], List[dict]]]) -> Tuple[List[Any], List[Any], List[Any]]:
        """
        Split lines into Header, Footer, and Body based on vertical coordinates.
        Page height assumed to be around 792 points.
        """
        headers = []
        footers = []
        body = []
        
        for text, bbox, line_words in lines:
            y_center = (bbox[1] + bbox[3]) / 2
            
            # Check if it looks like a key-value pair first
            is_kv_candidate = ":" in text or " - " in text or any(k in text.lower() for k in ["invoice number", "invoice date", "bill no", "date"])
            
            # Header zone: top 15% (y_center < 120) and not a key-value candidate
            if y_center < 120 and not is_kv_candidate:
                headers.append((text, bbox))
            # Footer zone: bottom 15% (y_center > 680) or contains page/T&C keyword
            elif y_center > 680 or "page" in text.lower() or "terms" in text.lower():
                footers.append((text, bbox))
            else:
                body.append((text, bbox, line_words))
                
        return headers, footers, body

    def _extract_key_values_and_tables(self, body_lines: List[Tuple[str, List[float], List[dict]]], all_words: List[dict]) -> Tuple[List[KeyValueBlock], List[Tuple[str, List[float], List[dict]]]]:
        """
        Finds key-value matches and returns them along with the remaining lines (which are table candidates).
        """
        kvs = []
        table_lines = []
        
        # Regex patterns for key-value extraction
        # e.g. "Invoice Number: INV-1001" or "Qty: 25"
        for text, bbox, line_words in body_lines:
            matched_kv = False
            
            # Check if this line looks like a table header or table row
            # If the line contains a colon, it is a KV candidate, do not skip as table line
            if ":" in text:
                pass
            elif any(h in text.lower() for h in ["description", "quantity", "unit", "price", "amount", "goods", "port"]):
                table_lines.append((text, bbox, line_words))
                continue
                
            # If it's a short text line or row below header with column separation
            elif len(line_words) > 3 and any(w["bbox"][0] > 200 for w in line_words) and ":" not in text:
                # High probability of being a table row
                table_lines.append((text, bbox, line_words))
                continue

            for target in self.target_keys:
                pattern = rf"(?i)\b({target})\b\s*[:\-]\s*(.*)"
                match = re.search(pattern, text)
                if match:
                    key_part = match.group(1).strip()
                    val_part = match.group(2).strip()
                    
                    # Truncate val_part if it contains another target key pattern
                    for other_target in self.target_keys:
                        if other_target != target:
                            other_pattern = rf"(?i)\b{other_target}\b\s*[:\-]"
                            other_match = re.search(other_pattern, val_part)
                            if other_match:
                                val_part = val_part[:other_match.start()].strip()
                                break
                                
                    # Find matching words for key and value by text matching
                    key_words = []
                    val_words = []
                    
                    key_terms = [t.lower().replace(":", "").replace("-", "").strip() for t in key_part.split() if t]
                    val_terms = [t.lower().replace(":", "").replace("-", "").strip() for t in val_part.split() if t]
                    
                    for w in line_words:
                        w_clean = w["text"].lower().replace(":", "").replace("-", "").strip()
                        if any(term == w_clean or w_clean in term for term in key_terms):
                            key_words.append(w)
                        elif any(term == w_clean or w_clean in term for term in val_terms):
                            val_words.append(w)
                            
                    if key_words and val_words:
                        k_bbox = [
                            min(w["bbox"][0] for w in key_words),
                            min(w["bbox"][1] for w in key_words),
                            max(w["bbox"][2] for w in key_words),
                            max(w["bbox"][3] for w in key_words)
                        ]
                        v_bbox = [
                            min(w["bbox"][0] for w in val_words),
                            min(w["bbox"][1] for w in val_words),
                            max(w["bbox"][2] for w in val_words),
                            max(w["bbox"][3] for w in val_words)
                        ]
                        
                        kvs.append(KeyValueBlock(
                            key=key_part,
                            value=val_part,
                            key_bbox=k_bbox,
                            value_bbox=v_bbox,
                            bbox=bbox,
                            page=line_words[0]["page"]
                        ))
                        matched_kv = True
            
            if not matched_kv:
                # If not matched as KV, group under table lines candidate
                table_lines.append((text, bbox, line_words))
                
        return kvs, table_lines

    def _detect_tables(self, table_lines: List[Tuple[str, List[float], List[dict]]], page_num: int) -> List[Table]:
        if not table_lines:
            return []
            
        # Find header line (first line containing descriptive headers)
        header_index = -1
        header_words = []
        
        for idx, (text, bbox, line_words) in enumerate(table_lines):
            text_lower = text.lower()
            if any(h in text_lower for h in ["description", "quantity", "unit", "price", "amount", "goods", "gross weight"]):
                header_index = idx
                header_words = line_words
                break
                
        if header_index == -1:
            return []
            
        # Parse headers
        headers = []
        # Group adjacent words in header line into distinct headers based on horizontal spacing
        current_h_words = []
        for w in sorted(header_words, key=lambda x: x["bbox"][0]):
            if not current_h_words:
                current_h_words.append(w)
            else:
                if w["bbox"][0] - current_h_words[-1]["bbox"][2] < 25:
                    current_h_words.append(w)
                else:
                    h_text = " ".join(x["text"] for x in current_h_words)
                    h_bbox = [
                        min(x["bbox"][0] for x in current_h_words),
                        min(x["bbox"][1] for x in current_h_words),
                        max(x["bbox"][2] for x in current_h_words),
                        max(x["bbox"][3] for x in current_h_words)
                    ]
                    headers.append(TableHeader(text=h_text, bbox=h_bbox))
                    current_h_words = [w]
        if current_h_words:
            h_text = " ".join(x["text"] for x in current_h_words)
            h_bbox = [
                min(x["bbox"][0] for x in current_h_words),
                min(x["bbox"][1] for x in current_h_words),
                max(x["bbox"][2] for x in current_h_words),
                max(x["bbox"][3] for x in current_h_words)
            ]
            headers.append(TableHeader(text=h_text, bbox=h_bbox))

        # Parse rows below header
        rows = []
        table_bbox_y1 = table_lines[header_index][1][3]
        
        for text, bbox, line_words in table_lines[header_index + 1:]:
            cells = []
            # Map each word to the closest header column based on overlap or alignment
            row_cells_data = {i: [] for i in range(len(headers))}
            
            for w in line_words:
                # Find best matching header by horizontal center distance
                w_center_x = (w["bbox"][0] + w["bbox"][2]) / 2
                best_hdr_idx = 0
                best_dist = float('inf')
                
                for h_idx, h in enumerate(headers):
                    h_center_x = (h.bbox[0] + h.bbox[2]) / 2
                    dist = abs(w_center_x - h_center_x)
                    if dist < best_dist:
                        best_dist = dist
                        best_hdr_idx = h_idx
                
                row_cells_data[best_hdr_idx].append(w)
                
            # Create cells
            for h_idx in range(len(headers)):
                cell_words = sorted(row_cells_data[h_idx], key=lambda x: x["bbox"][0])
                if cell_words:
                    cell_text = " ".join(x["text"] for x in cell_words)
                    c_bbox = [
                        min(x["bbox"][0] for x in cell_words),
                        min(x["bbox"][1] for x in cell_words),
                        max(x["bbox"][2] for x in cell_words),
                        max(x["bbox"][3] for x in cell_words)
                    ]
                    cells.append(TableCell(text=cell_text, bbox=c_bbox))
                else:
                    cells.append(TableCell(text="", bbox=[0, 0, 0, 0]))
                    
            rows.append(TableRow(cells=cells))
            table_bbox_y1 = max(table_bbox_y1, bbox[3])

        # Overall Table Bounding Box
        t_x0 = min(h.bbox[0] for h in headers)
        t_y0 = min(h.bbox[1] for h in headers)
        t_x1 = max(h.bbox[2] for h in headers)
        t_y1 = table_bbox_y1
        
        tbl = Table(
            table_id="table_1",
            bbox=[t_x0, t_y0, t_x1, t_y1],
            headers=headers,
            rows=rows,
            page=page_num
        )
        return [tbl]
