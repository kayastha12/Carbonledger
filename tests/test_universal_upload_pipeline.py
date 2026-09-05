import os
import json
import pytest
import pandas as pd
from fpdf import FPDF
from services.universal_upload_service import UniversalUploadService
from api.database import init_db

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

@pytest.fixture
def sample_pdf_path(tmp_path):
    pdf_file = os.path.join(tmp_path, "test_purchase_orders.pdf")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    pdf.cell(200, 10, text="PURCHASE ORDERS MANIFEST", new_x="LMARGIN", new_y="NEXT", align="C")
    
    orders = [
        ("PO-1001", "Steel Traders Ltd", "Steel Sheet", "1000.0", "kg", "5000.0", "DE"),
        ("PO-1002", "Alloy Dynamics", "Aluminium Bar", "500.0", "kg", "3500.0", "DE"),
        ("PO-1003", "MetalCorp Global", "Copper Wire", "250.0", "kg", "2800.0", "DE"),
    ]
    
    for po, sup, mat, qty, unit, cost, country in orders:
        text = f"PO Number: {po} | Supplier: {sup} | Material: {mat} | Quantity: {qty} | Unit: {unit} | Cost: {cost} | Country: {country}"
        pdf.cell(200, 10, text=text, new_x="LMARGIN", new_y="NEXT")
        
    pdf.output(pdf_file)
    return pdf_file

def test_pdf_upload_strict_parsing_and_cbam_cost(sample_pdf_path, tmp_path):
    service = UniversalUploadService(output_dir=str(tmp_path))
    
    # 1. Parse PDF
    parse_res = service.parse_uploaded_file(sample_pdf_path, "test_purchase_orders.pdf")
    extracted_records = parse_res.get("records", [])
    
    assert len(extracted_records) == 3
    assert extracted_records[0]["material"] in ["Steel Sheet", "Steel"]
    assert extracted_records[0]["quantity"] == 1000.0
    assert extracted_records[0]["unit"] == "kg"

    # 2. Calculate and build inventory.xlsx + CBAM cost
    calc_res = service.calculate_and_save(extracted_records, upload_id="test_strict_001")
    
    assert calc_res["status"] == "PASS"
    assert calc_res["total_records"] == 3
    
    inv_records = calc_res["inventory_records"]
    assert len(inv_records) == 3
    
    # Verify CBAM Cost Engine calculation
    first_row = inv_records[0]
    assert "cbam_cost_eur" in first_row
    assert first_row["cbam_cost_eur"] >= 0.0
    assert "co2e_kg" in first_row

def test_dynamic_validation_scores(sample_pdf_path, tmp_path):
    service = UniversalUploadService(output_dir=str(tmp_path))
    parse_res = service.parse_uploaded_file(sample_pdf_path, "test_purchase_orders.pdf")
    calc_res = service.calculate_and_save(parse_res["records"], upload_id="test_scores")
    
    scores = calc_res["validation_scores"]
    assert "ocr_confidence_pct" in scores
    assert "material_match_pct" in scores
    assert "factor_match_pct" in scores
    assert "overall_confidence_pct" in scores
    assert scores["overall_confidence_pct"] > 0.0

def test_5_fresh_reports_generation(sample_pdf_path, tmp_path):
    service = UniversalUploadService(output_dir=str(tmp_path))
    parse_res = service.parse_uploaded_file(sample_pdf_path, "test_purchase_orders.pdf")
    calc_res = service.calculate_and_save(parse_res["records"], upload_id="test_fresh_reports")
    
    reports = calc_res["reports"]
    expected_keys = [
        "carbon_report_pdf", "cbam_report_excel", "inventory_excel", "audit_json",
        "executive_esg_pdf"
    ]
    for key in expected_keys:
        assert key in reports

def test_processing_summary_cards(sample_pdf_path, tmp_path):
    service = UniversalUploadService(output_dir=str(tmp_path))
    parse_res = service.parse_uploaded_file(sample_pdf_path, "test_purchase_orders.pdf")
    calc_res = service.calculate_and_save(parse_res["records"], upload_id="test_summary_kpi")
    
    summary = calc_res["summary"]
    assert summary["documents_processed"] == 1
    assert summary["rows_extracted"] == 3
    assert summary["rows_validated"] == 3
    assert summary["rows_calculated"] + summary["rows_manual_review"] == 3
    assert summary["total_co2e_kg"] >= 0
    assert "total_cbam_cost_eur" in summary
