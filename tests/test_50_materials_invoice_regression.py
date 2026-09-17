import os
import sys
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.universal_upload_service import UniversalUploadService
from scripts.generate_inv_005 import generate_inv_005
from api.database import init_db

@pytest.fixture(scope="module")
def inv_005_pdf():
    fixture_dir = os.path.join(project_root, "tests", "fixtures")
    os.makedirs(fixture_dir, exist_ok=True)
    pdf_path = os.path.join(fixture_dir, "INV-005_TechManufacturing_50Materials_Invoice.pdf")
    generate_inv_005(pdf_path)
    return pdf_path

def test_inv_005_extraction_and_activity_detection(inv_005_pdf):
    """
    Primary regression test for INV-005_TechManufacturing_50Materials_Invoice.pdf:
    - Verifies that the document is accepted as containing carbon activity data (not rejected with 'No Carbon Activity Data Found').
    - Verifies that all 50 material line items are extracted into valid CarbonActivityRecord structures.
    - Verifies that the transport record (Section B) is extracted with distance, weight, mode, and fuel.
    - Verifies that summary/tax totals (Section C) are NOT counted as carbon activities.
    """
    init_db()
    service = UniversalUploadService()
    
    parsed = service.parse_uploaded_file(inv_005_pdf, "INV-005_TechManufacturing_50Materials_Invoice.pdf")
    records = parsed.get("records", [])
    
    assert len(records) > 0, "Document AI returned 0 records; 'No Carbon Activity Data Found' bug occurred"
    
    # 1. Check material line items
    material_records = [r for r in records if r.get("activity_type") in ["PURCHASED_GOODS", "PURCHASE_ORDER"]]
    assert len(material_records) == 50, f"Expected exactly 50 material line items, got {len(material_records)}"
    
    # Check specific material descriptions
    descriptions = [r.get("material") or r.get("activity", {}).get("material") for r in material_records]
    assert "Structural Steel Section (primary metal)" in descriptions
    assert "Tinplate Steel Sheet for Can Bodies (primary)" in descriptions
    assert "Aluminium Foil Stock 0.05 mm (primary)" in descriptions
    assert "HDPE Granules, injection grade (primary)" in descriptions
    assert "Corrugated Board Sheet (primary)" in descriptions
    assert "Refrigeration / Cooling Unit Assembly" in descriptions
    assert "Foundry Sand / Aggregate" in descriptions
    assert "Wooden Pallets / Timber Packing" in descriptions
    
    # Check quantities and units
    for r in material_records:
        assert r.get("quantity") is not None and r.get("quantity") > 0, f"Invalid quantity in record: {r}"
        assert str(r.get("unit")).lower() == "kg", f"Expected unit 'kg', got '{r.get('unit')}'"
        assert r.get("activity", {}).get("scope") == "SCOPE_3"
        
    # Check total net weight of materials equals 19,210 kg
    total_qty = sum(r["quantity"] for r in material_records)
    assert abs(total_qty - 19210.0) < 1e-4, f"Expected total material weight 19210.0 kg, got {total_qty}"
    
    # 2. Check transport record
    transport_records = [r for r in records if r.get("activity_type") in ["TRANSPORTATION", "LOGISTICS_SHIPPING"]]
    assert len(transport_records) == 1, f"Expected 1 transport record, got {len(transport_records)}"
    
    t_rec = transport_records[0]
    act = t_rec.get("activity", {})
    assert act.get("distance") == 180.0
    assert str(act.get("distance_unit")).lower() == "km"
    assert act.get("weight") == 19210.0
    assert str(act.get("weight_unit")).lower() == "kg"
    assert "Road - HGV" in str(act.get("transport_mode"))
    assert str(act.get("fuel_type")).lower() == "diesel"
    assert act.get("origin") == "Pune, Maharashtra"
    assert "Mumbai" in str(act.get("destination"))
    assert act.get("scope") == "SCOPE_3"
    
    # 3. Check summary/tax items are NOT in extracted records
    for desc in descriptions:
        desc_low = str(desc).lower()
        assert "subtotal" not in desc_low
        assert "taxable value" not in desc_low
        assert "cgst" not in desc_low
        assert "sgst" not in desc_low
        assert "grand total" not in desc_low
        assert "rounding" not in desc_low

def test_inv_005_approval_and_calculation_workflow(inv_005_pdf):
    """
    Tests approval and calculation on the 51 extracted records of INV-005.
    """
    init_db()
    service = UniversalUploadService()
    parsed = service.parse_uploaded_file(inv_005_pdf, "INV-005_TechManufacturing_50Materials_Invoice.pdf")
    records = parsed.get("records", [])
    
    calc_res = service.calculate_and_save(records, upload_id="test_inv_005_approval")
    assert calc_res["status"] == "PASS"
    assert calc_res["total_records"] == 51
    
    summary = calc_res["summary"]
    assert summary["rows_extracted"] == 51
    assert summary["rows_validated"] == 51
    assert summary["suppliers_count"] == 1
    assert summary["materials_count"] == 51

def test_generic_unknown_material_creates_activity_record():
    """
    TEST 1 & 3: Unknown material description with valid quantity/unit is accepted
    as candidate activity data and marked as needing factor review rather than rejected.
    """
    from services.document_ai_service import DocumentAIService
    from services.workbook_factor_engine import WorkbookFactorEngine
    
    doc_service = DocumentAIService()
    factor_engine = WorkbookFactorEngine.get_instance()
    
    rec = {
        "activity_type": "PURCHASED_GOODS",
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "scope": "SCOPE_3",
            "material": "High-Performance Carbon Composite Section ZX-900",
            "quantity": 2500.0,
            "unit": "kg"
        },
        "material": "High-Performance Carbon Composite Section ZX-900",
        "quantity": 2500.0,
        "unit": "kg"
    }
    
    # 1. Must be recognized as a valid carbon record
    assert doc_service.is_valid_carbon_record(rec) is True
    
    # 2. Factor engine evaluates without failing or inventing fake factors
    eval_res = factor_engine.evaluate_activity(rec)
    assert eval_res["calculation_status"] in ["FACTOR_NOT_FOUND", "REVIEW_REQUIRED"]
    assert eval_res["emission_kgco2e"] == 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
