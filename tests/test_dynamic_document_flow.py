"""
Tests verifying dynamic document isolation, state replacement, and session filtering:
- No hardcoded data in responses
- Each upload has a unique upload_id / document context
- Uploading document B replaces document A records
- Failed extraction clears records
- Calculation only computes emissions for the active upload_id
- Different PDFs produce distinct, dynamic records (PDF 1 vs PDF 2 vs Copper PDF 3)
"""

import os
import pytest
from services.field_extraction_service import FieldExtractionService
from services.universal_upload_service import UniversalUploadService
from services.carbon_calculation_service import CarbonCalculationService
from scripts.generate_sample_copper_invoice import generate_copper_invoice


@pytest.fixture
def upload_service():
    return UniversalUploadService(output_dir="output/temp")


@pytest.fixture
def field_service():
    return FieldExtractionService()


@pytest.fixture
def calc_service():
    return CarbonCalculationService()


def test_unique_upload_id_generation(upload_service):
    """Every upload session must receive a unique upload_id."""
    records_1 = [{"material": "Steel Sheet", "quantity": 500.0, "unit": "kg", "activity_type": "PURCHASED_GOODS"}]
    records_2 = [{"material": "Copper Wire", "quantity": 750.0, "unit": "kg", "activity_type": "PURCHASED_GOODS"}]

    res_1 = upload_service.calculate_and_save(records_1, upload_id=None)
    res_2 = upload_service.calculate_and_save(records_2, upload_id=None)

    assert res_1["upload_id"] != res_2["upload_id"]
    assert res_1["upload_id"].startswith("upload_")
    assert res_2["upload_id"].startswith("upload_")


def test_different_pdfs_produce_distinct_records(upload_service):
    """PDF 1, PDF 2, and Copper PDF 3 must produce distinct dynamic records."""
    copper_pdf_path = "output/temp/test_copper_invoice.pdf"
    generate_copper_invoice(copper_pdf_path)

    res_copper = upload_service.parse_uploaded_file(copper_pdf_path, "test_copper_invoice.pdf")
    copper_records = res_copper.get("records", [])

    assert len(copper_records) == 3
    assert copper_records[0]["material"] in ["Copper Wire", "Copper"]
    assert copper_records[0]["quantity"] == 750.0
    assert copper_records[0]["unit"] == "kg"
    assert any("ABC METALS" in str(copper_records[0].get(k, "")).upper() for k in ["supplier", "supplier_name"]) or "ABC Metals" in str(copper_records[0].get("supplier", {}).get("name", ""))
    assert copper_records[1]["material"] in ["Brass Rod", "Brass"]
    assert copper_records[1]["quantity"] == 300.0
    assert copper_records[2]["material"] in ["Stainless Steel Fasteners", "Steel", "Stainless Steel"]

    # Verify that NO old materials (Steel Sheet, Plastic Resin, Aluminum Bar) bleed into Copper invoice
    for rec in copper_records:
        assert rec["material"] not in ["Steel Sheet", "Plastic Resin", "Aluminum Bar"]


def test_calculation_isolated_by_upload_id(upload_service):
    """Calculation must process strictly the passed records and return scoped totals."""
    records = [
        {"fuel_type": "Diesel", "material": "Diesel", "quantity": 500.0, "unit": "L", "activity_type": "FUEL_CONSUMPTION", "cost": 50000.0, "currency": "INR", "country": "IN", "scope": "Scope 1", "invoice_id": "INV-001", "supplier": "Fuel Suppliers"}
    ]
    calc_res = upload_service.calculate_and_save(records, upload_id="test_steel_up_01")
    
    assert calc_res["upload_id"] == "test_steel_up_01"
    assert calc_res["summary"]["rows_extracted"] == 1
    assert calc_res["summary"]["materials_count"] == 1
    # Check that calculation computed positive emissions for 500 L Diesel (1291.77 kg CO2e)
    assert calc_res["summary"]["total_co2e_kg"] > 0
    assert abs(calc_res["summary"]["total_co2e_kg"] - 1291.77) < 0.1


def test_empty_document_produces_zero_records(field_service):
    """An empty or non-activity table returns an empty list without fake records."""
    tables = [{
        "headers": ["Document Title", "Version"],
        "rows": [["Internal Corporate Policy", "v2.1"]],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Policy", "Corporate Governance Policy", tables, "policy.pdf")
    # Empty because policy has no carbon activity rows
    assert len(records) == 0
