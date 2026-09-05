"""
CarbonLedger Field Mapper
==========================
Maps raw PDF/table header labels to canonical CarbonActivityRecord field names.

DESIGN PRINCIPLES:
- Support all common real-world header variations for invoice, transport, shipping,
  electricity, fuel, CBAM, and supplier documents.
- Explicit exclusions prevent noise fields from being mapped.
- Context-aware disambiguation for ambiguous labels like "Amount".
- Returns "unknown" for fields that cannot be reliably mapped.
"""

import re
from typing import Optional


class FieldMapper:
    """Maps layout keys to canonical activity field names."""

    # Primary exact-match mapping (all lowercase, stripped)
    MAP = {
        # ─── Invoice / Document Identity ────────────────────────────────────────
        "invoice number": "invoice_number",
        "invoice no": "invoice_number",
        "invoice no.": "invoice_number",
        "invoice #": "invoice_number",
        "inv no": "invoice_number",
        "inv no.": "invoice_number",
        "inv #": "invoice_number",
        "bill no": "invoice_number",
        "bill no.": "invoice_number",
        "receipt no": "invoice_number",
        "receipt number": "invoice_number",
        "invoice date": "invoice_date",
        "bill date": "invoice_date",
        "date": "invoice_date",
        "invoice dt": "invoice_date",

        # ─── Purchase Order ──────────────────────────────────────────────────────
        "purchase order number": "purchase_order_number",
        "po number": "purchase_order_number",
        "po no": "purchase_order_number",
        "po no.": "purchase_order_number",
        "po #": "purchase_order_number",
        "p.o. number": "purchase_order_number",
        "order number": "purchase_order_number",
        "order no": "purchase_order_number",
        "lr no": "lr_number",
        "lr number": "lr_number",
        "waybill no": "lr_number",

        # ─── Supplier / Vendor ────────────────────────────────────────────────────
        "supplier": "supplier",
        "supplier name": "supplier",
        "supplier id": "supplier_id",
        "supplier code": "supplier_id",
        "vendor": "supplier",
        "vendor name": "supplier",
        "vendor id": "supplier_id",
        "vendor code": "supplier_id",
        "seller": "supplier",
        "sold by": "supplier",
        "sold by:": "supplier",
        "manufacturer": "supplier",
        "producer": "supplier",
        "exporter": "supplier",
        "shipper": "supplier",
        "from": "origin",  # will be overridden by transport context

        # ─── Customer / Buyer ─────────────────────────────────────────────────────
        "customer": "customer_name",
        "customer name": "customer_name",
        "customer id": "company_id",
        "buyer": "customer_name",
        "consignee": "customer_name",
        "bill to": "customer_name",
        "billed to": "customer_name",
        "ship to": "destination",
        "account no": "account_number",
        "account number": "account_number",

        # ─── Material / Product ───────────────────────────────────────────────────
        "material": "material",
        "material type": "material",
        "material description": "material",
        "material id": "material_id",
        "product": "material",
        "product name": "material",
        "product description": "material",
        "description": "material",
        "item description": "material",
        "item": "material",
        "goods": "material",
        "goods description": "material",
        "particulars": "material",
        "article": "material",
        "commodity": "material",
        "description of goods": "material",
        "nature of goods": "material",
        "description of supply": "material",

        # ─── Quantity ─────────────────────────────────────────────────────────────
        "quantity": "quantity",
        "qty": "quantity",
        "no. of units": "quantity",
        "no of units": "quantity",
        "number of units": "quantity",
        "volume": "quantity",
        "pcs": "quantity",
        "nos": "quantity",
        "no.": "quantity",
        "nos.": "quantity",

        # ─── Unit of Measure ─────────────────────────────────────────────────────
        "unit": "unit",
        "uom": "unit",
        "unit of measure": "unit",
        "unit of measurement": "unit",
        "u/m": "unit",

        # ─── Weight ───────────────────────────────────────────────────────────────
        "weight": "weight",
        "gross weight": "weight",
        "net weight": "weight",
        "net wt": "weight",
        "net wt.": "weight",
        "gross wt": "weight",
        "gross wt.": "weight",
        "net mass": "weight",
        "gross mass": "weight",
        "cargo weight": "weight",
        "cargo wt": "weight",
        "cargo wt.": "weight",
        "total weight": "weight",
        "chargeable weight": "weight",

        # ─── Financial ───────────────────────────────────────────────────────────
        "total": "total_amount",
        "total amount": "total_amount",
        "invoice value": "total_amount",
        "invoice total": "total_amount",
        "total value": "total_amount",
        "amount payable": "total_amount",
        "payable amount": "total_amount",
        "grand total": "total_amount",
        "net amount": "total_amount",
        "basic amount": "total_amount",
        "taxable amount": "total_amount",
        "total paid": "total_amount",
        "total bill amount": "total_amount",
        "cost": "total_amount",
        "price": "total_amount",
        "rate": "unit_rate",
        "unit rate": "unit_rate",
        "unit cost": "unit_rate",
        "unit price": "unit_rate",
        "amount": "total_amount",  # context-dependent; may be overridden

        # ─── Currency ─────────────────────────────────────────────────────────────
        "currency": "currency",

        # ─── HS / CN / Commodity Codes ────────────────────────────────────────────
        "hs code": "hs_code",
        "hs": "hs_code",
        "hsn code": "hsn_code",
        "hsn": "hsn_code",
        "hsn/sac": "hsn_code",
        "hsn sac": "hsn_code",
        "sac": "hsn_code",
        "cn code": "cn_code",
        "cn": "cn_code",
        "combined nomenclature": "cn_code",
        "commodity code": "commodity_code",
        "tariff code": "commodity_code",
        "tariff heading": "commodity_code",
        "customs code": "commodity_code",

        # ─── Transport ────────────────────────────────────────────────────────────
        "origin": "origin",
        "loading location": "origin",
        "port of loading": "origin",
        "port of load": "origin",
        "loading port": "origin",
        "pol": "origin",
        "place of dispatch": "origin",
        "place of receipt": "origin",
        "departure": "origin",
        "destination": "destination",
        "delivery location": "destination",
        "port of discharge": "destination",
        "discharge port": "destination",
        "pod": "destination",
        "delivery address": "destination",
        "arrival": "destination",
        "transport mode": "transport_mode",
        "mode": "transport_mode",
        "mode of transport": "transport_mode",
        "transport_mode": "transport_mode",
        "mode_of_transport": "transport_mode",
        "shipping mode": "transport_mode",
        "shipping_mode": "transport_mode",
        "shipping method": "transport_mode",
        "transport type": "transport_mode",
        "vehicle type": "transport_mode",
        "mode of shipment": "transport_mode",
        "carrier": "transport_mode",
        "vehicle": "transport_mode",
        "distance": "distance",
        "distance (km)": "distance",
        "dist (km)": "distance",
        "km": "distance",
        "kms": "distance",
        "dist": "distance",
        "route": "route",
        "stage": "stage",
        "leg": "stage",

        # ─── Fuel ─────────────────────────────────────────────────────────────────
        "fuel type": "fuel_type",
        "fuel": "fuel_type",
        "fuel id": "fuel_id",

        # ─── Electricity / Energy ─────────────────────────────────────────────────
        "electricity consumption": "consumption",
        "consumption": "consumption",
        "units consumed": "consumption",
        "energy consumed": "consumption",
        "kwh": "consumption",
        "mwh": "consumption",
        "energy": "energy_type",
        "utility type": "utility_type",
        "utility": "utility_type",
        "meter number": "meter_number",
        "meter reading": "meter_reading",
        "billing period": "billing_period",
        "bill period": "billing_period",
        "reading period": "billing_period",
        "billing cycle": "billing_period",
        "period": "billing_period",
        "consumption (kwh)": "consumption",
        "consumption (mwh)": "consumption",
        "tariff": "tariff",

        # ─── Facility / Plant ─────────────────────────────────────────────────────
        "plant id": "facility_id",
        "plant name": "plant_name",
        "facility id": "facility_id",
        "facility": "plant_name",
        "location": "location",
        "capacity": "capacity",
        "machines": "machines",
        "fuel used": "fuel_used",
        "working hours": "working_hours",
        "working hours/day": "working_hours",

        # ─── Supplier Master ──────────────────────────────────────────────────────
        "country": "country",
        "city": "city",
        "state": "state",
        "industry": "industry",
        "esg rating": "esg_rating",
        "certification": "certification",

        # ─── Other IDs ────────────────────────────────────────────────────────────
        "bill id": "bill_id",
        "ship id": "shipment_id",
        "shipment id": "shipment_id",
        "grid id": "grid_id",
        "grid region": "grid_region",
        "material id": "material_id",
        "product id": "product_id",
        "delivery date": "delivery_date",
        "status": "status",
        "notes": "notes",
        "production line": "production_line",
        "equipment": "equipment",
        "vehicle/equipment": "equipment",
    }

    # Fields that should never be mapped — they add noise without carbon relevance
    _EXPLICIT_EXCLUSIONS = {
        "date & time of supply",
        "time of supply",
        "vehicle no",
        "vehicle number",
        "packages",
        "item code",
        "grade",
        "specification",
        "remarks",
        "authorized signatory",
        "e & o.e",
        "certified that",
        "irn",
        "ack no",
        "ack date",
        "registered office",
        "corporate identity",
        "bank details",
        "account name",
        "sort code",
        "iban",
        "swift",
        "payment terms",
        "terms & conditions",
        "terms of payment",
        "warranty",
    }

    @classmethod
    def get_canonical_field(cls, raw_label: str) -> str:
        """
        Maps a raw label to its canonical field name.
        Returns 'unknown' if no reliable mapping exists.
        """
        if not raw_label:
            return "unknown"

        # Normalize: lowercase, strip punctuation/whitespace
        lbl = raw_label.lower().strip()
        lbl = re.sub(r"[:\-]+$", "", lbl).strip()
        lbl_nopunct = re.sub(r"[^a-z0-9 /().]", " ", lbl).strip()
        lbl_nopunct = re.sub(r"\s+", " ", lbl_nopunct).strip()

        # Explicit exclusions
        if any(ex in lbl for ex in cls._EXPLICIT_EXCLUSIONS):
            return "unknown"

        # Exact match (primary)
        if lbl in cls.MAP:
            return cls.MAP[lbl]

        # Exact match without punctuation
        if lbl_nopunct in cls.MAP:
            return cls.MAP[lbl_nopunct]

        # Normalized token match (remove spaces/underscores/hyphens)
        lbl_tok = re.sub(r"[\s_\-/]", "", lbl)
        for k, v in cls.MAP.items():
            k_tok = re.sub(r"[\s_\-/]", "", k)
            if k_tok == lbl_tok:
                return v

        # ─── Semantic keyword-based fallback ────────────────────────────────────

        # Invoice / PO number
        if re.search(r"invoice\s*(no|num|number|#)", lbl):
            return "invoice_number"
        if re.search(r"\bpo\s*(no|num|number|#)\b", lbl):
            return "purchase_order_number"
        if re.search(r"\blr\s*(no|num|number)\b", lbl):
            return "lr_number"

        # Supplier / Vendor
        if re.search(r"\b(supplier|vendor|seller|exporter|manufacturer|producer)\b", lbl):
            if re.search(r"\b(id|code)\b", lbl):
                return "supplier_id"
            return "supplier"

        # Customer / Buyer / Company
        if re.search(r"\b(customer|buyer|consignee|company)\b", lbl):
            if re.search(r"\b(id|code)\b", lbl):
                return "company_id"
            return "customer_name"

        # Material / Product
        if re.search(r"\b(material|product|goods|item|article|commodity|particulars|description)\b", lbl):
            if re.search(r"\b(code|no|num|id)\b", lbl):
                return "commodity_code"
            return "material"

        # HS / CN codes
        if re.search(r"\bhs\b|\bhsn\b|\bcn\b", lbl):
            if "hsn" in lbl or "sac" in lbl:
                return "hsn_code"
            if "cn" in lbl:
                return "cn_code"
            return "hs_code"
        if re.search(r"\b(tariff|commodity\s*code|customs\s*code)\b", lbl):
            return "commodity_code"

        # Quantity
        if re.search(r"\b(qty|quantity|volume|pcs|nos|units)\b", lbl):
            return "quantity"

        # Weight
        if re.search(r"\b(weight|mass|wt)\b", lbl):
            if re.search(r"\b(gross|total|chargeable)\b", lbl):
                return "weight"
            if re.search(r"\b(net|cargo)\b", lbl):
                return "weight"
            return "weight"

        # Distance / Transport
        if re.search(r"\b(distance|km|kms|dist)\b", lbl):
            return "distance"
        if re.search(r"\b(mode|transport|vehicle|carrier|shipping\s*method)\b", lbl):
            if not re.search(r"\b(charge|cost|rate)\b", lbl):
                return "transport_mode"

        # Origin / Destination
        if re.search(r"\b(origin|loading|departure|pol|from)\b", lbl):
            if not re.search(r"\b(country\s*of\s*origin)\b", lbl):
                return "origin"
        if re.search(r"\b(destination|discharge|arrival|pod)\b", lbl):
            return "destination"
        if re.search(r"country\s*of\s*origin", lbl):
            return "country_of_origin"

        # Fuel
        if re.search(r"\b(fuel\s*type|fuel)\b", lbl):
            return "fuel_type"

        # Energy / Electricity
        if re.search(r"\b(consumption|kwh|mwh|units\s*consumed|energy\s*consumed)\b", lbl):
            return "consumption"
        if re.search(r"\b(billing\s*period|reading\s*period|bill\s*period)\b", lbl):
            return "billing_period"
        if re.search(r"\b(utility\s*type|utility)\b", lbl):
            return "utility_type"

        # Financial amounts — context-aware
        if re.search(r"\b(total\s*amount|invoice\s*value|invoice\s*total|grand\s*total|amount\s*payable|payable\s*amount|net\s*amount|basic\s*amount)\b", lbl):
            return "total_amount"
        if re.search(r"\b(rate|unit\s*rate|unit\s*cost|unit\s*price)\b", lbl):
            return "unit_rate"

        # Country / Location
        if re.search(r"\bcountry\b", lbl):
            return "country"

        return "unknown"

    @classmethod
    def is_excluded(cls, raw_label: str) -> bool:
        """Returns True if the field should be explicitly excluded."""
        if not raw_label:
            return False
        lbl = raw_label.lower().strip()
        return any(ex in lbl for ex in cls._EXPLICIT_EXCLUSIONS)
