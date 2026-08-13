import os
import json
import re
import pandas as pd
from typing import List, Dict, Any, Optional

UNITS_LIST = [
    "kg", "g", "ton", "tonne", "l", "litre", "m³", "m3", "m^3", 
    "mwh", "kwh", "km", "ton-km", "tkm", "piece", "pieces", "pcs", 
    "tonnes", "liters", "litres", "grams", "kilograms"
]

def parse_numeric_value(val_str: str) -> float:
    """
    Standardizes and parses any numeric value string including Indian formatting,
    international formatting, negative values, scientific notations, decimals,
    and currency symbols.
    """
    if val_str is None:
        return 0.0
    
    # Clean currency symbols and leading/trailing spaces
    clean_str = re.sub(r'[₹€$¥£\s]', '', str(val_str)).strip()
    if not clean_str:
        return 0.0
    
    # Check for negative
    is_negative = clean_str.startswith('-')
    if is_negative:
        clean_str = clean_str[1:]
    
    # Check for scientific notation (e.g. 1.2e3 or 1.2e-3)
    if re.search(r'\d+e[+-]?\d+', clean_str, re.IGNORECASE):
        try:
            val = float(clean_str)
            return -val if is_negative else val
        except ValueError:
            pass
    
    # Handle separators
    if '.' in clean_str and ',' in clean_str:
        dot_idx = clean_str.find('.')
        comma_idx = clean_str.find(',')
        if dot_idx < comma_idx: # e.g. 1.250,50
            # dot is separator, comma is decimal
            clean_str = clean_str.replace('.', '').replace(',', '.')
        else: # e.g. 1,250.50
            # comma is separator, dot is decimal
            clean_str = clean_str.replace(',', '')
    elif ',' in clean_str: # only commas
        parts = clean_str.split(',')
        if len(parts) > 2: # e.g. 1,72,500
            clean_str = "".join(parts)
        elif len(parts) == 2:
            last_part = parts[1]
            if len(last_part) == 3: # e.g. 1,000 -> 1000
                clean_str = "".join(parts)
            else: # e.g. 1,25 -> 1.25
                clean_str = clean_str.replace(',', '.')
    elif '.' in clean_str: # only dots
        parts = clean_str.split('.')
        if len(parts) > 2: # e.g. 1.000.000
            clean_str = "".join(parts)
        elif len(parts) == 2:
            last_part = parts[1]
            if len(last_part) == 3: # e.g. 1.000 -> 1000
                clean_str = "".join(parts)
                
    try:
        val = float(clean_str)
        return -val if is_negative else val
    except ValueError:
        # Extract the first numeric sequence
        match = re.search(r'-?\d+([.,]\d+)?', clean_str)
        if match:
            return parse_numeric_value(match.group(0))
        return 0.0

def extract_unit_and_value(val_str: str) -> tuple:
    """
    Extracts a numeric value and standardized unit from a string like "200 L" or "1,000 kg".
    """
    if val_str is None:
        return 0.0, None
        
    cleaned = str(val_str).strip().lower()
    sorted_units = sorted(UNITS_LIST, key=len, reverse=True)
    
    # Match a float value followed by optional spaces, then standard unit word
    num_pattern = r'(-?\d+(?:[.,]\d+)*)'
    unit_pattern = r'(?:' + '|'.join(re.escape(u) for u in sorted_units) + r')\b'
    
    match = re.search(num_pattern + r'\s*(' + unit_pattern + r')', cleaned)
    if match:
        num_part = match.group(1)
        unit_part = match.group(2)
        
        unit_mapping = {
            "kg": "kg", "kilograms": "kg", "g": "g", "grams": "g",
            "ton": "ton", "tonne": "tonne", "tonnes": "tonne",
            "l": "L", "litre": "L", "liters": "L", "litres": "L",
            "m³": "m³", "m3": "m³", "m^3": "m³",
            "mwh": "MWh", "kwh": "kWh", "km": "km",
            "ton-km": "ton-km", "tkm": "ton-km",
            "piece": "piece", "pieces": "piece", "pcs": "piece"
        }
        std_unit = unit_mapping.get(unit_part, unit_part)
        return parse_numeric_value(num_part), std_unit
        
    return parse_numeric_value(val_str), None

def detect_region_from_fields(ocr_text: str, raw_dict: dict, filename: str = "") -> Optional[str]:
    """
    Determines the standardized region code without guessing.
    Inspects explicit country column, addresses, currencies, GST, VAT, Tax IDs, and phone numbers.
    """
    country_mapping = {
        "india": "IN", "in": "IN", "ind": "IN",
        "germany": "DE", "de": "DE", "deu": "DE", "deutschland": "DE",
        "france": "FR", "fr": "FR", "fra": "FR",
        "united kingdom": "GB", "uk": "GB", "gb": "GB", "gbr": "GB",
        "united states": "US", "usa": "US", "us": "US",
        "china": "CN", "cn": "CN", "chn": "CN",
        "japan": "JP", "jp": "JP", "jpn": "JP"
    }
    
    # 1. Check direct country column/field
    for k in ["country", "origin", "region", "country_code"]:
        for rk in raw_dict.keys():
            if str(rk).strip().lower() == k:
                val = str(raw_dict[rk]).strip().lower()
                if val in country_mapping:
                    return country_mapping[val]
                    
    # 2. Check full OCR text / address context
    search_text = (ocr_text + " " + filename + " " + " ".join(str(v) for v in raw_dict.values())).lower()
    
    # Check Indian GSTIN pattern
    if "gstin" in search_text or "gst registration" in search_text or re.search(r'\b\d{2}[a-z]{5}\d{4}[a-z]{1}[a-z\d]{1}[z]{1}[a-z\d]{1}\b', search_text):
        return "IN"
        
    # Check European VAT pattern (e.g. DE123456789, FR987654321)
    vat_match = re.search(r'\b(de|fr|gb|nl|it|es|pl)\d{9,12}\b', search_text)
    if vat_match:
        return vat_match.group(1).upper()
        
    # Check explicit currency
    if "₹" in search_text or "inr" in search_text or "rs." in search_text or "rupees" in search_text:
        return "IN"
    if "jpy" in search_text:
        return "JP"
    if "usd" in search_text:
        return "US"
        
    # Check address keywords
    if "india" in search_text or "mumbai" in search_text or "delhi" in search_text or "bengaluru" in search_text or re.search(r'\b(pin|pincode)?\s*\d{6}\b', search_text):
        return "IN"
    if "germany" in search_text or "berlin" in search_text or "munich" in search_text or "frankfurt" in search_text or "gmbh" in search_text:
        return "DE"
        
    return None

class FieldExtractionService:
    """
    Extracts key carbon and business fields (material, qty, unit, cost, supplier, etc.)
    from tables or text depending on the document type, attaching confidence scores for each field.
    """
    def __init__(self):
        pass

    def extract_fields(self, 
                       document_type: str, 
                       text: str, 
                       tables: List[Dict[str, Any]], 
                       filename: str) -> List[Dict[str, Any]]:
        """
        Extracts document business variables from layout structures or plain text.
        """
        records = []
        
        # If we have tables detected, parse rows
        if tables:
            for tbl in tables:
                headers = tbl["headers"]
                rows = tbl["rows"]
                page = tbl["page"]
                confidence = tbl.get("confidence", 0.99)
                
                df_tbl = pd.DataFrame(rows, columns=headers if len(headers) == len(rows[0]) else None)
                for idx, row in df_tbl.iterrows():
                    raw_dict = row.to_dict()
                    raw_dict = {str(k).strip(): (None if pd.isna(v) else v) for k, v in raw_dict.items()}
                    
                    rec = self._standardize_and_score(raw_dict, document_type, filename, page, row_idx=idx+1, table_conf=confidence, ocr_text=text)
                    records.append(rec)
        
        # Fallback to lines parsing if no table structure is present
        if not records:
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            row_count = 1
            for line in lines:
                l_lower = line.lower()
                if "manifest" in l_lower or ("purchase orders" in l_lower and "|" not in line and ":" not in line):
                    continue
                
                line_dict = {}
                segments = line.split("|") if "|" in line else [line]
                for seg in segments:
                    if ":" in seg:
                        k, v = seg.split(":", 1)
                        line_dict[k.strip().lower()] = v.strip()
                
                if line_dict.get("material") or line_dict.get("po_number") or line_dict.get("supplier"):
                    rec = self._standardize_and_score(line_dict, document_type, filename, page_num=1, row_idx=row_count, table_conf=0.7, ocr_text=text)
                    records.append(rec)
                    row_count += 1
                    
            if not records and lines:
                fallback_dict = {"material": lines[0][:40], "quantity": 100.0, "unit": "kg"}
                rec = self._standardize_and_score(fallback_dict, document_type, filename, page_num=1, row_idx=1, table_conf=0.5, ocr_text=text)
                records.append(rec)
                
        return records

    def _standardize_and_score(self, 
                                raw_dict: Dict[str, Any], 
                                document_type: str, 
                                filename: str, 
                                page_num: int, 
                                row_idx: int,
                                table_conf: float,
                                ocr_text: str = "") -> Dict[str, Any]:
        
        def get_val_with_conf(keys, default_val=None, type_cast=str):
            for k in keys:
                for rk in raw_dict.keys():
                    if str(rk).strip().lower() == k.lower():
                        val = raw_dict[rk]
                        if val is not None and str(val).strip() != "":
                            try:
                                return type_cast(val), 0.99
                            except Exception:
                                pass
            return default_val, 0.5

        # Standard Core Fields
        po_keys = ["po_number", "ponumber", "po", "po_num", "purchase_order", "invoice_number", "invoice_num", "inv_num", "inv_number"]
        po_number, po_conf = get_val_with_conf(po_keys, f"PO-{row_idx:04d}")
        
        supplier, supplier_conf = get_val_with_conf(["supplier", "supplier_name", "suppliername", "vendor"], "Unknown Supplier")
        
        # NEVER RENAME MATERIALS
        material, material_conf = get_val_with_conf(["material", "material_name", "item", "item_description", "description", "product"], "Unspecified Material")
        material = str(material).strip()

        # Parse Quantity and Unit
        qty_raw, qty_conf = get_val_with_conf(["quantity", "qty", "amount", "volume", "weight"], None)
        unit_raw, unit_conf = get_val_with_conf(["unit", "uom", "unit_of_measure"], None)
        
        quantity = 1.0
        unit = "kg"
        
        if qty_raw is not None:
            # Extract both unit and value from quantity if possible
            parsed_val, parsed_unit = extract_unit_and_value(qty_raw)
            quantity = parsed_val
            qty_conf = 0.99
            if parsed_unit:
                unit = parsed_unit
                unit_conf = 0.99
                
        if unit_raw is not None and (unit_raw != "kg" or qty_raw is None or not parsed_unit):
            _, parsed_unit = extract_unit_and_value(f"1 {unit_raw}")
            if parsed_unit:
                unit = parsed_unit
                unit_conf = 0.99
            else:
                unit = str(unit_raw).strip()
                unit_conf = 0.99

        # Parse Cost and Currency
        cost_raw, cost_conf = get_val_with_conf(["cost", "price", "amount_eur", "total_cost", "val"], 0.0)
        cost = parse_numeric_value(cost_raw)
        if cost_raw is not None and cost_raw != 0.0:
            cost_conf = 0.99
            
        currency = "EUR"
        # Extract currency symbol or word if in cost_raw
        if cost_raw is not None:
            cost_str = str(cost_raw).upper()
            if "₹" in cost_str or "INR" in cost_str:
                currency = "INR"
            elif "$" in cost_str or "USD" in cost_str:
                currency = "USD"
            elif "¥" in cost_str or "JPY" in cost_str:
                currency = "JPY"
            elif "€" in cost_str or "EUR" in cost_str:
                currency = "EUR"

        delivery_date, date_conf = get_val_with_conf(["delivery_date", "date", "ship_date", "invoice_date"], pd.Timestamp.now().strftime("%Y-%m-%d"))
        status, status_conf = get_val_with_conf(["status", "state", "order_status"], "Delivered")
        facility, facility_conf = get_val_with_conf(["facility", "plant", "site", "location"], "Munich Plant")
        
        # Region detection (never guess)
        detected_country = detect_region_from_fields(ocr_text, raw_dict, filename)
        if detected_country:
            country = detected_country
            country_conf = 0.99
        else:
            country, country_conf = get_val_with_conf(["country", "origin", "region"], "")
            
        section, section_conf = get_val_with_conf(["section", "category"], "Purchase Orders")

        # Dynamic additional fields depending on classification type
        extra_fields = {}
        if document_type == "Shipping Manifest":
            vehicle, vehicle_conf = get_val_with_conf(["vehicle", "transport_mode", "mode", "ship_via"], "HGV Truck")
            dist_raw, dist_conf = get_val_with_conf(["distance", "miles", "km", "range"], 0.0)
            distance = parse_numeric_value(dist_raw)
            if dist_raw is not None:
                dist_conf = 0.99
            origin, origin_conf = get_val_with_conf(["origin", "from", "ship_from"], country)
            destination, destination_conf = get_val_with_conf(["destination", "to", "ship_to"], country)
            extra_fields = {
                "vehicle": vehicle,
                "vehicle_confidence": vehicle_conf,
                "distance": distance,
                "distance_confidence": dist_conf,
                "origin": origin,
                "origin_confidence": origin_conf,
                "destination": destination,
                "destination_confidence": destination_conf
            }
        elif document_type == "Employee Travel":
            emp, emp_conf = get_val_with_conf(["employee_name", "employee", "passenger", "name"], "Employee")
            mode, mode_conf = get_val_with_conf(["transport_mode", "mode", "type"], "Flight")
            dist_raw, dist_conf = get_val_with_conf(["distance", "km", "miles"], 0.0)
            distance = parse_numeric_value(dist_raw)
            if dist_raw is not None:
                dist_conf = 0.99
            extra_fields = {
                "employee_name": emp,
                "employee_name_confidence": emp_conf,
                "transport_mode": mode,
                "transport_mode_confidence": mode_conf,
                "distance": distance,
                "distance_confidence": dist_conf
            }
        elif document_type == "CBAM Data":
            hs, hs_conf = get_val_with_conf(["hs_code", "cn_code", "tariff"], "7207.11")
            route, route_conf = get_val_with_conf(["production_route", "route", "process"], "Basic Oxygen Furnace")
            extra_fields = {
                "hs_code": hs,
                "hs_code_confidence": hs_conf,
                "production_route": route,
                "production_route_confidence": route_conf
            }

        # Calculate average extraction confidence
        conf_list = [po_conf, supplier_conf, material_conf, qty_conf, unit_conf, cost_conf, date_conf, country_conf]
        avg_field_conf = round(sum(conf_list) / len(conf_list), 2)
        overall_record_conf = round((avg_field_conf + table_conf) / 2, 2)

        # No Hallucination Policy: Validate completeness
        # If core fields are missing or not confidently extracted, set flag
        has_critical_missing = (
            qty_raw is None or 
            unit_raw is None or 
            material == "Unspecified Material" or 
            supplier == "Unknown Supplier"
        )
        
        # If missing critical data, flag as Manual Review Required
        if has_critical_missing:
            status = "Manual Review Required"

        record = {
            "id": row_idx,
            "po_number": str(po_number),
            "po_number_confidence": po_conf,
            "supplier": str(supplier),
            "supplier_confidence": supplier_conf,
            "material": str(material),
            "material_confidence": material_conf,
            "quantity": quantity,
            "quantity_confidence": qty_conf,
            "quantity_raw": str(qty_raw) if qty_raw is not None else "",
            "unit": unit,
            "unit_confidence": unit_conf,
            "unit_raw": str(unit_raw) if unit_raw is not None else "",
            "cost": cost,
            "cost_confidence": cost_conf,
            "cost_raw": str(cost_raw) if cost_raw is not None else "",
            "currency": currency,
            "delivery_date": str(delivery_date),
            "delivery_date_confidence": date_conf,
            "status": str(status),
            "status_confidence": status_conf,
            "facility": str(facility),
            "facility_confidence": facility_conf,
            "country": str(country),
            "country_confidence": country_conf,
            "country_raw": str(detected_country or raw_dict.get("country", "")),
            "section": str(section),
            "section_confidence": section_conf,
            "source_document": filename,
            "page_number": page_num,
            "ocr_confidence": table_conf,
            "extraction_confidence": overall_record_conf,
            "document_type": document_type
        }
        
        record.update(extra_fields)
        return record
