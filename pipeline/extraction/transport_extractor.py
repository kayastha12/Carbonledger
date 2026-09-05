from pipeline.extraction.base import BaseExtractor
from pipeline.extraction.common import ExtractionHelper
from pipeline.extraction.entity_normalizer import EntityNormalizer
from schemas.extraction import ExtractionResult, SupplierData, TransportData, QuantityData
from schemas.document import ClassificationResult, LayoutResult

class TransportationExtractor(BaseExtractor):
    def extract(
        self,
        document: dict,
        classification: ClassificationResult,
        layout: LayoutResult
    ) -> ExtractionResult:
        page_layout = layout.pages[0]
        normalizer = EntityNormalizer()
        
        # 1. Metadata Fields
        route_kv = ExtractionHelper.find_kv(page_layout, "route")
        origin_kv = ExtractionHelper.find_kv(page_layout, "origin")
        dest_kv = ExtractionHelper.find_kv(page_layout, "destination")
        
        metadata = {
            "route": ExtractionHelper.build_field(route_kv, None, "route"),
            "origin": ExtractionHelper.build_field(origin_kv, None, "origin"),
            "destination": ExtractionHelper.build_field(dest_kv, None, "destination")
        }
        
        # 2. Supplier Data (Carrier)
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
        
        # 3. Distance Data
        dist_kv = ExtractionHelper.find_kv(page_layout, "distance")
        dist_val = None
        if dist_kv:
            dist_num, dist_unit = normalizer.normalize_value(f"{dist_kv.value}")
            if dist_num is not None:
                dist_val = QuantityData(value=dist_num, unit=dist_unit or "km")
            
        metadata["distance"] = ExtractionHelper.build_field(dist_kv, None, "distance")
        
        # 4. Weight/Quantity Data
        qty_kv = ExtractionHelper.find_kv(page_layout, "quantity") or ExtractionHelper.find_kv(page_layout, "weight")
        unit_kv = ExtractionHelper.find_kv(page_layout, "unit")
        qty_val = None
        unit_val = None
        
        if qty_kv:
            qty_num, qty_unit = normalizer.normalize_value(f"{qty_kv.value} {unit_kv.value if unit_kv else ''}")
            qty_val = qty_num if qty_num is not None else None
            unit_val = qty_unit or None
            
        metadata["quantity"] = ExtractionHelper.build_field(qty_kv, None, "quantity")
        if metadata["quantity"] and isinstance(metadata["quantity"].normalized_value, dict):
            metadata["quantity"].normalized_value["unit"] = unit_val
        
        # Determine transport mode (heuristics / default to Road)
        transport_mode = "Road"
        if supplier_kv and "freight" in supplier_kv.value.lower():
            transport_mode = "Road"
            
        transport_data = TransportData(
            mode=normalizer.normalize_transport(transport_mode),
            origin=origin_kv.value if origin_kv else None,
            destination=dest_kv.value if dest_kv else None,
            distance=dist_val
        )
        
        return ExtractionResult(
            document_id=layout.document_id,
            document_type="TRANSPORTATION_INVOICE",
            metadata=metadata,
            supplier=supplier_data,
            transport=transport_data,
            requires_review=False
        )
