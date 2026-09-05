from pipeline.extraction.base import BaseExtractor
from pipeline.extraction.common import ExtractionHelper
from pipeline.extraction.entity_normalizer import EntityNormalizer
from pipeline.extraction.field_mapper import FieldMapper
from schemas.extraction import ExtractionResult, SupplierData, FinancialData
from schemas.document import ClassificationResult, LayoutResult

class PurchaseInvoiceExtractor(BaseExtractor):
    def extract(
        self,
        document: dict,
        classification: ClassificationResult,
        layout: LayoutResult
    ) -> ExtractionResult:
        page_layout = layout.pages[0]
        normalizer = EntityNormalizer()
        
        # 1. Metadata Fields
        inv_num_kv = ExtractionHelper.find_kv(page_layout, "invoice_number")
        date_kv = ExtractionHelper.find_kv(page_layout, "invoice_date")
        
        metadata = {
            "invoice_number": ExtractionHelper.build_field(inv_num_kv, None, "invoice_number"),
            "invoice_date": ExtractionHelper.build_field(date_kv, None, "invoice_date")
        }
        
        # 2. Supplier Data
        supplier_kv = ExtractionHelper.find_kv(page_layout, "supplier")
        supplier_header = ExtractionHelper.find_header_value(page_layout)
        supplier_name = None
        
        if supplier_kv:
            supplier_name = supplier_kv.value
        elif supplier_header:
            supplier_name = supplier_header.text
            
        country_kv = ExtractionHelper.find_kv(page_layout, "country")
        country_name = country_kv.value if country_kv else None

        supplier_data = None
        if supplier_name is not None:
            supplier_data = SupplierData(
                name=supplier_name,
                country=country_name
            )
        metadata["supplier"] = ExtractionHelper.build_field(supplier_kv, supplier_header, "supplier")
        metadata["country"] = ExtractionHelper.build_field(country_kv, None, "country")
        
        # 3. Items Extraction from Tables or Key-Values
        items = []
        financial_amount = None
        
        if page_layout.tables:
            table = page_layout.tables[0]
            # Map headers to list indices
            header_map = {}
            for idx, h in enumerate(table.headers):
                canonical = FieldMapper.get_canonical_field(h.text)
                header_map[canonical] = idx
                
            for row in table.rows:
                # Extract cells
                desc_idx = header_map.get("material", -1)
                qty_idx = header_map.get("quantity", -1)
                unit_idx = header_map.get("unit", -1)
                tot_idx = header_map.get("total_amount", -1)
                
                desc_val = row.cells[desc_idx].text if desc_idx != -1 else ""
                qty_str = row.cells[qty_idx].text if qty_idx != -1 else ""
                unit_str = row.cells[unit_idx].text if unit_idx != -1 else ""
                tot_str = row.cells[tot_idx].text if tot_idx != -1 else ""
                
                if desc_val:
                    qty_num, qty_unit = normalizer.normalize_value(f"{qty_str} {unit_str}")
                    qty_val = qty_num if qty_num is not None else None
                    unit_val = qty_unit or None
                    
                    # Convert to weight if unit is tonne/kg
                    weight_val = qty_val
                    weight_unit = unit_val
                    if unit_val == "tonne" and qty_val is not None:
                        weight_val = qty_val * 1000
                        weight_unit = "kg"
                        
                    amt_num, _ = normalizer.normalize_value(tot_str)
                    financial_amount = amt_num or financial_amount
                    
                    items.append({
                        "description": desc_val,
                        "material": normalizer.normalize_material(desc_val),
                        "quantity": qty_val,
                        "unit": unit_val,
                        "weight": weight_val,
                        "weight_unit": weight_unit,
                        "confidence": 0.95
                    })
                    
        # Fallback to key-values if no table items extracted
        if not items:
            mat_kv = ExtractionHelper.find_kv(page_layout, "material")
            qty_kv = ExtractionHelper.find_kv(page_layout, "quantity")
            unit_kv = ExtractionHelper.find_kv(page_layout, "unit")
            tot_kv = ExtractionHelper.find_kv(page_layout, "total_amount")
            
            if mat_kv and qty_kv:
                qty_num, qty_unit = normalizer.normalize_value(f"{qty_kv.value} {unit_kv.value if unit_kv else ''}")
                qty_val = qty_num if qty_num is not None else None
                unit_val = qty_unit or None
                
                weight_val = qty_val
                weight_unit = unit_val
                if unit_val == "tonne" and qty_val is not None:
                    weight_val = qty_val * 1000
                    weight_unit = "kg"
                    
                items.append({
                    "description": mat_kv.value,
                    "material": normalizer.normalize_material(mat_kv.value),
                    "quantity": qty_val,
                    "unit": unit_val,
                    "weight": weight_val,
                    "weight_unit": weight_unit,
                    "confidence": 0.95
                })
                
            if tot_kv:
                amt_num, _ = normalizer.normalize_value(tot_kv.value)
                financial_amount = amt_num or financial_amount

        # 4. Financial Data
        tot_kv = ExtractionHelper.find_kv(page_layout, "total_amount")
        metadata["total_amount"] = ExtractionHelper.build_field(tot_kv, None, "total_amount", fallback_val=str(financial_amount) if financial_amount else None)
        
        from pipeline.extraction.common import detect_currency_from_layout
        financial_data = FinancialData(
            currency=detect_currency_from_layout(page_layout),
            total_amount=financial_amount
        )
        
        return ExtractionResult(
            document_id=layout.document_id,
            document_type="PURCHASE_INVOICE",
            metadata=metadata,
            supplier=supplier_data,
            items=items,
            financial=financial_data,
            requires_review=False
        )
