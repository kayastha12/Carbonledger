import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import json
import pytest
from fastapi.testclient import TestClient

from api.main import app
from services.document_ai_service import DocumentAIService

client = TestClient(app)

def test_full_document_ai_upload_and_calculation_flow():
    pdf1_path = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"
    pdf2_path = r"D:\internship\reference_style_invoice_with_transport_distances.pdf"
    
    if not os.path.exists(pdf1_path) or not os.path.exists(pdf2_path):
        pytest.skip("Test PDFs not found in D:\\internship")

    # 1. Upload PDF A
    with open(pdf1_path, "rb") as f:
        resp1 = client.post(
            "/api/documents/upload",
            files={"file": (os.path.basename(pdf1_path), f, "application/pdf")}
        )
    assert resp1.status_code == 200, f"Upload PDF A failed: {resp1.text}"
    data1 = resp1.json()
    upload_id_1 = data1["upload_id"]
    records1 = data1["records"]
    assert upload_id_1.startswith("upload_")
    assert len(records1) > 0

    # Verify PDF A contains real data and NO fake fallbacks
    for r in records1:
        sup_name = r.get("supplier", {}).get("name") if isinstance(r.get("supplier"), dict) else r.get("supplier")
        mat_name = r.get("activity", {}).get("material") if isinstance(r.get("activity"), dict) else r.get("material")
        assert sup_name != "Unknown Supplier"
        assert mat_name != "Unspecified Material"
    
    # 2. Upload PDF B
    with open(pdf2_path, "rb") as f:
        resp2 = client.post(
            "/api/documents/upload",
            files={"file": (os.path.basename(pdf2_path), f, "application/pdf")}
        )
    assert resp2.status_code == 200, f"Upload PDF B failed: {resp2.text}"
    data2 = resp2.json()
    upload_id_2 = data2["upload_id"]
    records2 = data2["records"]
    assert upload_id_2.startswith("upload_")
    assert upload_id_2 != upload_id_1
    assert len(records2) > 0

    # 3. Verify Document Isolation via GET /api/documents/{document_id}/records
    iso_resp1 = client.get(f"/api/documents/{upload_id_1}/records")
    assert iso_resp1.status_code == 200
    iso_data1 = iso_resp1.json()
    assert iso_data1["document_id"] == upload_id_1
    assert len(iso_data1["records"]) == len(records1)

    iso_resp2 = client.get(f"/api/documents/{upload_id_2}/records")
    assert iso_resp2.status_code == 200
    iso_data2 = iso_resp2.json()
    assert iso_data2["document_id"] == upload_id_2
    assert len(iso_data2["records"]) == len(records2)

    # 4. Approve & Calculate PDF 1
    # Filter calculable records from PDF 1
    calculable_records = [
        r for r in records1 
        if r.get("carbon_calculation", {}).get("calculation_ready") is True
        or (r.get("activity", {}).get("material") and r.get("activity", {}).get("quantity"))
    ]
    if calculable_records:
        app_resp = client.post(
            "/api/upload/approve",
            json={"upload_id": upload_id_1, "records": calculable_records}
        )
        assert app_resp.status_code == 200, f"Approve failed: {app_resp.text}"
        calc_res = app_resp.json()
        assert calc_res.get("status") == "calculated" or "total_records" in calc_res

if __name__ == "__main__":
    test_full_document_ai_upload_and_calculation_flow()
    print("Full E2E Document AI Upload & Calculation Test Passed!")
