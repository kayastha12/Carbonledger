from pipeline.extraction.base import BaseExtractor
from pipeline.extraction.common import ExtractionHelper
from pipeline.extraction.entity_normalizer import EntityNormalizer
from schemas.extraction import ExtractionResult, SupplierData, FuelData, QuantityData, FinancialData
from schemas.document import ClassificationResult, LayoutResult

class FuelInvoiceExtractor(BaseExtractor):
    def extract(
        self,
        document: dict,
        classification: ClassificationResult,
        layout: LayoutResult
    ) -> ExtractionResult:
        page_layout = layout.pages[0]
        normalizer = EntityNormalizer()
        
        # 1. Metadata Fields
        fuel_type_kv = ExtractionHelper.find_kv(page_layout, "fuel_type")
        metadata = {
            "fuel_type": ExtractionHelper.build_field(fuel_type_kv, None, "fuel_type")
        }
        
        # 2. Supplier Data
        supplier_kv = ExtractionHelper.find_kv(page_layout, "supplier")
        supplier_header = ExtractionHelper.find_header_value(page_layout)
        supplier_name = None
        
        if supplier_kv:
            supplier_name = supplier_kv.value
        elif supplier_header:
            supplier_name = supplier_header.text
            
        supplier_data = None
        if supplier_name is not None:
            supplier_data = SupplierData(
                name=supplier_name
            )
        metadata["supplier"] = ExtractionHelper.build_field(supplier_kv, supplier_header, "supplier")
        
        # 3. Fuel Quantity & Normalization
        qty_kv = ExtractionHelper.find_kv(page_layout, "quantity")
        unit_kv = ExtractionHelper.find_kv(page_layout, "unit")
        
        qty_val = None
        unit_val = None
        
        if qty_kv:
            qty_num, qty_unit = normalizer.normalize_value(f"{qty_kv.value} {unit_kv.value if unit_kv else ''}")
            qty_val = qty_num if qty_num is not None else None
            unit_val = qty_unit or None
            
        # Normalize fuel type string using taxonomy
        fuel_type_str = fuel_type_kv.value if fuel_type_kv else None
        fuel_data = None
        if fuel_type_str or qty_val is not None:
            norm_fuel = normalizer.normalize_fuel(fuel_type_str) if fuel_type_str else None
            fuel_type_normalized = norm_fuel["normalized"] if (fuel_type_str and norm_fuel) else None
            fuel_data = FuelData(
                type=fuel_type_normalized,
                quantity=QuantityData(value=qty_val if qty_val is not None else 0.0, unit=unit_val or "liter")
            )
        metadata["quantity"] = ExtractionHelper.build_field(qty_kv, None, "quantity")
        
        # 4. Financial Data
        tot_kv = ExtractionHelper.find_kv(page_layout, "total_amount")
        amount_val = None
        if tot_kv:
            amt_num, _ = normalizer.normalize_value(tot_kv.value)
            amount_val = amt_num
            
        from pipeline.extraction.common import detect_currency_from_layout
        financial_data = FinancialData(
            currency=detect_currency_from_layout(page_layout),
            total_amount=amount_val
        )
        metadata["total_amount"] = ExtractionHelper.build_field(tot_kv, None, "total_amount")
        
        return ExtractionResult(
            document_id=layout.document_id,
            document_type="FUEL_INVOICE",
            metadata=metadata,
            supplier=supplier_data,
            fuel=fuel_data,
            financial=financial_data,
            requires_review=False
        )
