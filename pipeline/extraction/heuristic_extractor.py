from pipeline.extraction.invoice_extractor import PurchaseInvoiceExtractor
from pipeline.extraction.electricity_extractor import ElectricityBillExtractor
from pipeline.extraction.fuel_extractor import FuelInvoiceExtractor
from pipeline.extraction.transport_extractor import TransportationExtractor
from pipeline.extraction.shipping_extractor import ShippingExtractor
from schemas.extraction import ExtractionResult
from schemas.document import ClassificationResult, LayoutResult

class HeuristicExtractor:
    def __init__(self):
        self.extractors = {
            "PURCHASE_INVOICE": PurchaseInvoiceExtractor(),
            "ELECTRICITY_BILL": ElectricityBillExtractor(),
            "FUEL_INVOICE": FuelInvoiceExtractor(),
            "TRANSPORTATION_INVOICE": TransportationExtractor(),
            "SHIPPING_MANIFEST": ShippingExtractor(),
            "BILL_OF_LADING": ShippingExtractor()
        }

    def extract(
        self,
        document: dict,
        classification: ClassificationResult,
        layout: LayoutResult
    ) -> ExtractionResult:
        doc_type = classification.document_type
        # Default to Purchase Invoice if unknown/mixed for fallback robustness
        extractor = self.extractors.get(doc_type, self.extractors["PURCHASE_INVOICE"])
        return extractor.extract(document, classification, layout)

    def to_activity_data(self, result: ExtractionResult) -> dict:
        """
        Converts ExtractionResult into CarbonLedgerActivity standardized JSON.
        """
        activity = {}
        doc_type = result.document_type
        
        # Common supplier data
        supplier_name = result.supplier.name if result.supplier else None
        supplier_country = result.supplier.country if result.supplier and result.supplier.country else None
        
        if doc_type == "PURCHASE_INVOICE":
            activity["activity_type"] = "purchased_material"
            item = result.items[0] if result.items else {}
            activity["material"] = {
                "name": item.get("material", {}).get("normalized", None) if isinstance(item.get("material"), dict) else None,
                "category": item.get("material", {}).get("category", None) if isinstance(item.get("material"), dict) else None
            }
            activity["quantity"] = {
                "value": item.get("quantity", None),
                "unit": item.get("unit", None)
            }
            activity["supplier"] = {
                "name": supplier_name,
                "country": supplier_country
            }
            # Optional transport placeholders if relevant
            if "transport" in activity:
                pass # removed mock transport for purchase invoice
            
        elif doc_type == "ELECTRICITY_BILL":
            activity["activity_type"] = "purchased_electricity"
            energy = result.energy
            activity["energy"] = {
                "type": energy.type if energy else None,
                "quantity": {
                    "value": energy.quantity.value if energy and energy.quantity else None,
                    "unit": energy.quantity.unit if energy and energy.quantity else None
                }
            }
            
        elif doc_type == "FUEL_INVOICE":
            activity["activity_type"] = "fuel_consumption"
            fuel = result.fuel
            activity["fuel"] = {
                "type": fuel.type if fuel else None,
                "quantity": {
                    "value": fuel.quantity.value if fuel and fuel.quantity else None,
                    "unit": fuel.quantity.unit if fuel and fuel.quantity else None
                }
            }
            
        elif doc_type == "TRANSPORTATION_INVOICE":
            activity["activity_type"] = "logistics_transport"
            transport = result.transport
            qty_val = None
            unit_val = None
            
            # Map quantity from metadata
            qty_field = result.metadata.get("quantity")
            if qty_field and qty_field.normalized_value:
                if isinstance(qty_field.normalized_value, dict):
                    qty_val = qty_field.normalized_value.get("value", None)
                    unit_val = qty_field.normalized_value.get("unit", None)
            
            activity["transport"] = {
                "mode": transport.mode if transport else None,
                "origin": transport.origin if transport else None,
                "destination": transport.destination if transport else None,
                "distance": {
                    "value": transport.distance.value if transport and transport.distance else None,
                    "unit": transport.distance.unit if transport and transport.distance else None
                },
                "quantity": {
                    "value": qty_val,
                    "unit": unit_val
                }
            }
            
        elif doc_type in ["SHIPPING_MANIFEST", "BILL_OF_LADING"]:
            activity["activity_type"] = "logistics_transport"
            transport = result.transport
            item = result.items[0] if result.items else {}
            
            activity["transport"] = {
                "mode": transport.mode if transport else None,
                "origin": transport.origin if transport else None,
                "destination": transport.destination if transport else None,
                "distance": {
                    "value": None,
                    "unit": None
                },
                "quantity": {
                    "value": item.get("quantity", None) if item else None,
                    "unit": item.get("unit", None) if item else None
                }
            }
            
        return activity
