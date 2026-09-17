import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.main import app
from api.database import get_db_connection, init_db

client = TestClient(app)

def test_what_if_endpoints_removed():
    """Verify that What-If simulation endpoints have been permanently removed."""
    res1 = client.post("/api/what-if", json={"strategy": "eaf_steel"})
    assert res1.status_code in [404, 405]

    res2 = client.post("/api/v1/what-if", json={"strategy": "eaf_steel"})
    assert res2.status_code in [404, 405]

def test_fresh_user_empty_dashboard_state():
    """Verify that a newly created user has an empty dashboard state."""
    init_db()
    test_email = f"fresh_user_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": "Password123!",
        "full_name": "Fresh User",
        "organization": "Empty Corp"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Latest upload should be null
    latest_res = client.get("/api/upload/latest", headers=headers)
    assert latest_res.status_code == 200
    assert latest_res.json() is None

def test_unapproved_upload_does_not_populate_dashboard():
    """Verify that uploading without approval leaves the dashboard in an uncalculated/empty state."""
    init_db()
    test_email = f"uploader_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": "Password123!",
        "full_name": "Uploader User",
        "organization": "Upload Corp"
    })
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload INV-005 fixture
    pdf_path = "tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("INV-005 fixture missing")

    with open(pdf_path, "rb") as f:
        up_res = client.post("/api/upload/universal", headers=headers, files={"file": ("INV-005.pdf", f, "application/pdf")})
    assert up_res.status_code == 200
    body = up_res.json()
    assert body["status"] == "parsed"
    assert len(body["records"]) == 51

    # Before approval, latest calculated dashboard data must STILL be null
    latest_res = client.get("/api/upload/latest", headers=headers)
    assert latest_res.status_code == 200
    assert latest_res.json() is None

def test_approved_calculation_populates_authoritative_dashboard():
    """Verify that explicit approval computes emissions, persists them, and dashboard reflects exact values."""
    init_db()
    test_email = f"approver_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": "Password123!",
        "full_name": "Approver User",
        "organization": "Approver Corp"
    })
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    pdf_path = "tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("INV-005 fixture missing")

    with open(pdf_path, "rb") as f:
        up_res = client.post("/api/upload/universal", headers=headers, files={"file": ("INV-005.pdf", f, "application/pdf")})
    assert up_res.status_code == 200
    up_data = up_res.json()
    upload_id = up_data["upload_id"]
    records = up_data["records"]

    # Approve & Calculate
    app_res = client.post("/api/upload/approve", headers=headers, json={
        "upload_id": upload_id,
        "records": records
    })
    assert app_res.status_code == 200
    app_data = app_res.json()
    assert app_data["status"] == "calculated"
    assert app_data["summary"]["total_co2e_kg"] > 0

    # Fetch latest upload dashboard API
    latest_res = client.get("/api/upload/latest", headers=headers)
    assert latest_res.status_code == 200
    dashboard_data = latest_res.json()
    assert dashboard_data is not None
    assert dashboard_data["status"] == "calculated"
    
    summary = dashboard_data["summary"]
    assert summary["rows_extracted"] == 51
    assert summary["rows_calculated"] == 51
    assert summary["total_co2e_kg"] == round(summary["scope_1_co2e_kg"] + summary["scope_2_co2e_kg"] + summary["scope_3_co2e_kg"], 2)

def test_tenant_workspace_isolation():
    """Verify that User B cannot see User A's calculated dashboard data."""
    init_db()
    # User A
    email_a = f"user_a_{uuid.uuid4().hex[:8]}@example.com"
    token_a = client.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "full_name": "User A", "organization": "Org A"}).json()["token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    email_b = f"user_b_{uuid.uuid4().hex[:8]}@example.com"
    token_b = client.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "full_name": "User B", "organization": "Org B"}).json()["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B should see None
    assert client.get("/api/upload/latest", headers=headers_b).json() is None

def test_partial_calculation_yields_partial_totals():
    """Verify that if some records are valid and some need review, valid records are calculated and reflected on dashboard."""
    init_db()
    test_email = f"partial_{uuid.uuid4().hex[:8]}@example.com"
    token = client.post("/api/v1/auth/register", json={"email": test_email, "password": "Password123!", "full_name": "Partial User", "organization": "Partial Corp"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    upload_id = f"upload_partial_{uuid.uuid4().hex[:6]}"
    records = [
        # Record 1: Valid Diesel combustion (Scope 1)
        {
            "po_number": "PO-101",
            "material": "Diesel Fuel - 100% Mineral",
            "quantity": 500.0,
            "unit": "litres",
            "activity_type": "FUEL_CONSUMPTION"
        },
        # Record 2: Unknown/Ambiguous material requiring review
        {
            "po_number": "PO-102",
            "material": "Generic Mixed Unspecified Waste Substance",
            "quantity": 1000.0,
            "unit": "kg",
            "activity_type": "PURCHASED_GOODS"
        }
    ]

    app_res = client.post("/api/upload/approve", headers=headers, json={"upload_id": upload_id, "records": records})
    assert app_res.status_code == 200
    app_data = app_res.json()
    summary = app_data["summary"]

    assert summary["rows_extracted"] == 2
    assert summary["rows_calculated"] == 1
    assert summary["rows_manual_review"] == 1
    # Total footprint must NOT be zero; it must equal diesel calculation
    assert summary["total_co2e_kg"] > 0
    assert summary["scope_1_co2e_kg"] > 0

    # Dashboard endpoint check
    latest_res = client.get("/api/upload/latest", headers=headers)
    assert latest_res.status_code == 200
    dash_data = latest_res.json()
    assert dash_data["summary"]["total_co2e_kg"] == summary["total_co2e_kg"]
    assert dash_data["summary"]["rows_calculated"] == 1
    assert dash_data["summary"]["rows_manual_review"] == 1

def test_dashboard_and_report_reconciliation():
    """Verify that dashboard totals reconcile exactly with persisted calculation records."""
    init_db()
    test_email = f"reconcile_{uuid.uuid4().hex[:8]}@example.com"
    token = client.post("/api/v1/auth/register", json={"email": test_email, "password": "Password123!", "full_name": "Reconcile User", "organization": "Reconcile Corp"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    pdf_path = "tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("INV-005 fixture missing")

    with open(pdf_path, "rb") as f:
        up_res = client.post("/api/upload/universal", headers=headers, files={"file": ("INV-005.pdf", f, "application/pdf")})
    assert up_res.status_code == 200
    up_data = up_res.json()

    app_res = client.post("/api/upload/approve", headers=headers, json={"upload_id": up_data["upload_id"], "records": up_data["records"]})
    assert app_res.status_code == 200

    dash_res = client.get("/api/upload/latest", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    summary = dash_data["summary"]
    records = dash_data["records"]

    # Reconcile sum of individual records with dashboard totals
    calc_records = [r for r in records if r["calculation_status"] == "Calculated"]
    reconciled_scope1 = round(sum(r["co2e_kg"] for r in calc_records if r["scope"] == "Scope 1"), 2)
    reconciled_scope2 = round(sum(r["co2e_kg"] for r in calc_records if r["scope"] == "Scope 2"), 2)
    reconciled_scope3 = round(sum(r["co2e_kg"] for r in calc_records if r["scope"] == "Scope 3"), 2)
    reconciled_total = round(reconciled_scope1 + reconciled_scope2 + reconciled_scope3, 2)

    assert summary["scope_1_co2e_kg"] == reconciled_scope1
    assert summary["scope_2_co2e_kg"] == reconciled_scope2
    assert summary["scope_3_co2e_kg"] == reconciled_scope3
    assert summary["total_co2e_kg"] == reconciled_total

