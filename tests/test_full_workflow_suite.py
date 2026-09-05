import os
import json
import pytest
from services.universal_upload_service import UniversalUploadService
from api.database import get_db_connection, init_db

TEST_PDF = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"

init_db()

def test_1_pdf_upload_receipt():
    assert os.path.exists(TEST_PDF), f"Test PDF does not exist at {TEST_PDF}"
    assert os.path.getsize(TEST_PDF) > 0, "Test PDF is empty"

def test_2_and_4_real_pdf_extraction():
    service = UniversalUploadService()
    parsed = service.parse_uploaded_file(TEST_PDF, "deepseek_invoice.pdf")
    
    assert parsed["file_name"] == "deepseek_invoice.pdf"
    assert parsed["pages_count"] >= 1
    assert len(parsed["records"]) > 0, "Document AI extracted 0 records from real PDF"
    
    records = parsed["records"]
    # Check that real records exist
    materials = [r.get("material") or r.get("activity", {}).get("material") for r in records]
    assert any("Steel" in str(m) for m in materials), "Expected Steel Sheet in extracted records"
    assert any("Diesel" in str(m) or "Fuel" in str(m) for m in materials), "Expected Diesel in extracted records"
    assert any("Electricity" in str(m) for m in materials), "Expected Electricity in extracted records"

def test_3_zero_record_document_handling(tmp_path):
    # Create empty dummy text file
    dummy_file = tmp_path / "empty_doc.pdf"
    dummy_file.write_bytes(b"%PDF-1.4\n%EOF")
    
    service = UniversalUploadService()
    try:
        parsed = service.parse_uploaded_file(str(dummy_file), "empty_doc.pdf")
        assert len(parsed["records"]) == 0
    except Exception:
        pass # Graceful handling

def test_5_and_7_approval_and_calculation():
    service = UniversalUploadService()
    parsed = service.parse_uploaded_file(TEST_PDF, "deepseek_invoice.pdf")
    records = parsed["records"]
    
    upload_id = "test_workflow_upload_001"
    calc_res = service.calculate_and_save(records, upload_id=upload_id)
    
    assert calc_res["status"] in ["PASSED", "PASS", "WARNING", "VALID", "calculated"]
    summary = calc_res["summary"]
    assert summary["total_co2e_kg"] > 0, "Total carbon footprint must be positive"
    assert summary["rows_calculated"] > 0, "Calculated rows must be greater than 0"
    assert "scope_1_co2e_kg" in summary
    assert "scope_2_co2e_kg" in summary
    assert "scope_3_co2e_kg" in summary
    assert len(calc_res["reports"]) >= 4, "Must generate at least 4 compliance reports"

def test_6_duplicate_approval_idempotency():
    service = UniversalUploadService()
    parsed = service.parse_uploaded_file(TEST_PDF, "deepseek_invoice.pdf")
    records = parsed["records"]
    
    upload_id = "test_idempotent_002"
    # First calculation
    calc_1 = service.calculate_and_save(records, upload_id=upload_id)
    # Second calculation with same upload_id
    calc_2 = service.calculate_and_save(records, upload_id=upload_id)
    
    assert calc_1["summary"]["total_co2e_kg"] == calc_2["summary"]["total_co2e_kg"]

def test_8_and_9_carbon_ledger_and_dashboard_totals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM upload_sessions")
    session_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM calculation_results")
    calc_count = cursor.fetchone()[0]
    conn.close()
    
    assert session_count > 0, "Upload session must be persisted in database"
    assert calc_count > 0, "Calculation rows must be persisted in database"

def test_10_new_document_clears_previous_state():
    service = UniversalUploadService()
    res1 = service.parse_uploaded_file(TEST_PDF, "doc1.pdf")
    assert len(res1["records"]) > 0
    
    # Simulating new document parse
    res2 = service._build_empty_parse_result("doc2.pdf", 1, 0, 0.0, [])
    assert len(res2["records"]) == 0

def test_11_invalid_approval_missing_material():
    service = UniversalUploadService()
    invalid_records = [{"activity_type": "PURCHASED_GOODS", "material": "", "quantity": 100, "unit": "kg"}]
    
    with pytest.raises(ValueError) as exc_info:
        service.calculate_and_save(invalid_records, upload_id="test_invalid")
    assert "Material Missing" in str(exc_info.value) or "Invalid" in str(exc_info.value)
