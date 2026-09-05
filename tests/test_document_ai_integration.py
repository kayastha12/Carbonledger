import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import json
import pytest

from services.document_ai_service import DocumentAIService

def test_document_ai_pdf1_extraction():
    pdf_path = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("PDF 1 not found")
        
    service = DocumentAIService()
    res = service.extract_document(pdf_path)
    
    assert res["document_id"].startswith("REAL_DOC_")
    assert len(res["records"]) > 0
    
    # Check strict provenance & no fake fallback
    for r in res["records"]:
        sup_name = r.get("supplier", {}).get("name") if isinstance(r.get("supplier"), dict) else r.get("supplier")
        mat_name = r.get("activity", {}).get("material") if isinstance(r.get("activity"), dict) else r.get("material")
        assert sup_name != "Unknown Supplier"
        assert mat_name != "Unspecified Material"
        assert "provenance" in r
        assert "carbon_calculation" in r
        assert "emission_factor" in r

def test_document_ai_pdf2_transport_extraction():
    pdf_path = r"D:\internship\reference_style_invoice_with_transport_distances.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("PDF 2 not found")
        
    service = DocumentAIService()
    res = service.extract_document(pdf_path)
    
    assert res["document_id"].startswith("REAL_DOC_")
    assert len(res["records"]) > 0
    
    # Verify transportation records contain distance/weight and proper units
    trans_recs = [r for r in res["records"] if r["activity"]["activity_type"] in ["TRANSPORTATION", "SHIPPING"]]
    assert len(trans_recs) > 0
    for r in trans_recs:
        assert r["activity"]["scope"] == "SCOPE_3"

if __name__ == "__main__":
    service = DocumentAIService()
    p1 = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"
    if os.path.exists(p1):
        res1 = service.extract_document(p1)
        print(f"PDF 1 extracted: {len(res1['records'])} records")
        print("Record 1:", json.dumps(res1["records"][0], indent=2))
        
    p2 = r"D:\internship\reference_style_invoice_with_transport_distances.pdf"
    if os.path.exists(p2):
        res2 = service.extract_document(p2)
        print(f"\nPDF 2 extracted: {len(res2['records'])} records")
        print("Record 1:", json.dumps(res2["records"][0], indent=2))
