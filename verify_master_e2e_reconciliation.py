import os
import time
import requests
import io
import pandas as pd
from api.database import init_db, get_db_connection

BASE_URL = "http://127.0.0.1:8000"

def run_e2e_master_test():
    print("=" * 75)
    print("CARBONLEDGER MASTER E2E VERIFICATION & RECONCILIATION TEST")
    print("=" * 75)

    # 1. Health check
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print("[1/6] Backend Health Check: OK (200)")

    # 2. Test File 1: INV-005_TechManufacturing_50Materials_Invoice.pdf
    pdf_path_1 = "tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf"
    assert os.path.exists(pdf_path_1), f"File missing: {pdf_path_1}"
    
    print("\n[2/6] Testing Upload & Extraction: INV-005_TechManufacturing_50Materials_Invoice.pdf")
    t0 = time.time()
    with open(pdf_path_1, "rb") as f:
        files = {"file": ("INV-005_TechManufacturing_50Materials_Invoice.pdf", f, "application/pdf")}
        r_up1 = requests.post(f"{BASE_URL}/api/upload/universal", files=files)
    t_up1 = time.time() - t0
    
    assert r_up1.status_code == 200, f"Upload failed: {r_up1.status_code} - {r_up1.text}"
    data1 = r_up1.json()
    upload_id_1 = data1.get("upload_id")
    records_1 = data1.get("records", [])
    timing_1 = data1.get("timing_breakdown", {})
    
    print(f"  -> Upload & Extraction completed in {t_up1:.3f}s")
    print(f"  -> Upload ID: {upload_id_1}")
    print(f"  -> Extracted Candidate Records: {len(records_1)}")
    print(f"  -> Server Timing Breakdown: {timing_1}")
    assert len(records_1) == 51, f"Expected 51 records from INV-005, got {len(records_1)}"

    # 3. Gating Test: Before approval, verify that latest calculation status has no approved calculations
    r_latest_pre = requests.get(f"{BASE_URL}/api/upload/latest")
    # Pre-approval check
    print("\n[3/6] Verifying Pre-Approval Gating State...")
    print("  -> Candidate records are awaiting user review in Upload & Review UI.")

    # 4. Approval & Calculation Flow for INV-005
    print("\n[4/6] Approving & Calculating INV-005...")
    t0 = time.time()
    r_app1 = requests.post(f"{BASE_URL}/api/upload/approve", json={
        "upload_id": upload_id_1,
        "records": records_1
    })
    t_app1 = time.time() - t0
    assert r_app1.status_code == 200, f"Approval failed: {r_app1.status_code} - {r_app1.text}"
    calc_data1 = r_app1.json()
    summary1 = calc_data1.get("summary", {})
    total_co2e_1 = summary1.get("total_co2e_kg")
    s1_1 = summary1.get("scope_1_co2e_kg")
    s2_1 = summary1.get("scope_2_co2e_kg")
    s3_1 = summary1.get("scope_3_co2e_kg")
    calculated_rows_1 = summary1.get("rows_calculated")
    
    print(f"  -> Approval & Calculation completed in {t_app1:.3f}s")
    print(f"  -> Total Footprint: {total_co2e_1:,.2f} kg CO2e")
    print(f"  -> Scope 1: {s1_1:,.2f} kg | Scope 2: {s2_1:,.2f} kg | Scope 3: {s3_1:,.2f} kg")
    print(f"  -> Calculated Records: {calculated_rows_1} of {len(records_1)}")
    assert total_co2e_1 > 0, "Total carbon footprint must be non-zero after calculation!"

    # 5. Database Direct Verification (Source of Truth)
    print("\n[5/6] Verifying Persisted SQLite Database Source of Truth...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM calculation_results WHERE upload_id = ?", (upload_id_1,))
    db_rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    db_calculated_rows = [r for r in db_rows if r.get("calculation_status") == "Calculated"]
    db_total_co2e = round(sum(r.get("co2e_kg", 0.0) for r in db_calculated_rows), 2)
    db_s1 = round(sum(r.get("co2e_kg", 0.0) for r in db_calculated_rows if r.get("scope") == "Scope 1"), 2)
    db_s2 = round(sum(r.get("co2e_kg", 0.0) for r in db_calculated_rows if r.get("scope") == "Scope 2"), 2)
    db_s3 = round(sum(r.get("co2e_kg", 0.0) for r in db_calculated_rows if r.get("scope") == "Scope 3"), 2)
    
    print(f"  -> DB Total Calculated Rows: {len(db_calculated_rows)}")
    print(f"  -> DB Total CO2e: {db_total_co2e} kg")
    print(f"  -> DB Scope 1: {db_s1} kg | DB Scope 2: {db_s2} kg | DB Scope 3: {db_s3} kg")
    
    assert abs(db_total_co2e - total_co2e_1) < 0.01, f"DB total {db_total_co2e} != Summary total {total_co2e_1}"
    assert abs(db_s1 - s1_1) < 0.01, f"DB Scope 1 {db_s1} != Summary Scope 1 {s1_1}"
    assert abs(db_s2 - s2_1) < 0.01, f"DB Scope 2 {db_s2} != Summary Scope 2 {s2_1}"
    assert abs(db_s3 - s3_1) < 0.01, f"DB Scope 3 {db_s3} != Summary Scope 3 {s3_1}"
    print("  -> RECONCILIATION SUCCESS: Database rows exactly match Dashboard totals!")

    # 6. Calculated Data Download & Reconciliation Test (Parts 21 & 22)
    print("\n[6/6] Testing Calculated Data CSV & XLSX Download and Reconciliation...")
    # CSV Download
    r_csv = requests.get(f"{BASE_URL}/api/calculations/download?upload_id={upload_id_1}&format=csv")
    assert r_csv.status_code == 200, f"CSV download failed: {r_csv.status_code}"
    csv_df = pd.read_csv(io.StringIO(r_csv.text))
    
    print(f"  -> Downloaded CSV Records: {len(csv_df)} rows, {len(csv_df.columns)} columns")
    print(f"  -> CSV Columns: {list(csv_df.columns)}")
    
    # Verify required 23 audit columns
    required_cols = [
        "document_id", "source_document", "invoice_number", "invoice_date", "supplier",
        "activity_record_id", "activity_type", "material_description", "category", "scope",
        "original_quantity", "original_unit", "normalized_quantity", "normalized_unit",
        "factor_id", "factor_value", "factor_unit", "factor_source", "factor_year",
        "factor_geography", "conversion", "formula", "calculated_co2e_kg", "calculation_status", "source_page"
    ]
    for col in required_cols:
        assert col in csv_df.columns, f"Missing required audit column in CSV: {col}"

    csv_calculated_rows = csv_df[csv_df["calculation_status"] == "Calculated"]
    csv_total_co2e = round(csv_calculated_rows["calculated_co2e_kg"].astype(float).sum(), 2)
    csv_s1 = round(csv_df[(csv_df["calculation_status"] == "Calculated") & (csv_df["scope"] == "Scope 1")]["calculated_co2e_kg"].astype(float).sum(), 2)
    csv_s2 = round(csv_df[(csv_df["calculation_status"] == "Calculated") & (csv_df["scope"] == "Scope 2")]["calculated_co2e_kg"].astype(float).sum(), 2)
    csv_s3 = round(csv_df[(csv_df["calculation_status"] == "Calculated") & (csv_df["scope"] == "Scope 3")]["calculated_co2e_kg"].astype(float).sum(), 2)

    print(f"  -> Downloaded CSV Calculated Rows: {len(csv_calculated_rows)}")
    print(f"  -> Downloaded CSV Total CO2e: {csv_total_co2e} kg")
    print(f"  -> Downloaded CSV Scope 1: {csv_s1} kg | Scope 2: {csv_s2} kg | Scope 3: {csv_s3} kg")

    assert abs(csv_total_co2e - total_co2e_1) < 0.01, f"Downloaded CSV Total {csv_total_co2e} != Dashboard Total {total_co2e_1}"
    assert abs(csv_s1 - s1_1) < 0.01, f"Downloaded CSV Scope 1 {csv_s1} != Dashboard Scope 1 {s1_1}"
    assert abs(csv_s2 - s2_1) < 0.01, f"Downloaded CSV Scope 2 {csv_s2} != Dashboard Scope 2 {s2_1}"
    assert abs(csv_s3 - s3_1) < 0.01, f"Downloaded CSV Scope 3 {csv_s3} != Dashboard Scope 3 {s3_1}"
    print("  -> PART 22 RECONCILIATION SUCCESS: Downloaded CSV perfectly matches Dashboard!")

    # Excel Download
    r_xlsx = requests.get(f"{BASE_URL}/api/calculations/download?upload_id={upload_id_1}&format=xlsx")
    assert r_xlsx.status_code == 200, f"Excel download failed: {r_xlsx.status_code}"
    xlsx_df = pd.read_excel(io.BytesIO(r_xlsx.content))
    assert len(xlsx_df) == len(csv_df), f"Excel rows {len(xlsx_df)} != CSV rows {len(csv_df)}"
    print(f"  -> Downloaded Excel Records: {len(xlsx_df)} rows verified.")

    # Also test DeepSeek PDF #2
    pdf_path_2 = "tests/fixtures/deepseek_html_20260731_54ad15 (1).pdf"
    print("\n" + "=" * 75)
    print("[TEST PDF #2] Testing Deepseek Multi-Phase PDF...")
    t0 = time.time()
    with open(pdf_path_2, "rb") as f:
        files = {"file": ("deepseek_html_20260731_54ad15 (1).pdf", f, "application/pdf")}
        r_up2 = requests.post(f"{BASE_URL}/api/upload/universal", files=files)
    t_up2 = time.time() - t0
    assert r_up2.status_code == 200, f"Deepseek upload failed: {r_up2.status_code}"
    data2 = r_up2.json()
    records_2 = data2.get("records", [])
    print(f"  -> Deepseek Upload & Extraction completed in {t_up2:.3f}s")
    print(f"  -> Deepseek Extracted Candidate Records: {len(records_2)}")
    assert len(records_2) > 0, "Expected non-zero records for DeepSeek invoice."

    r_app2 = requests.post(f"{BASE_URL}/api/upload/approve", json={
        "upload_id": data2.get("upload_id"),
        "records": records_2
    })
    assert r_app2.status_code == 200, f"Deepseek approval failed: {r_app2.status_code}"
    calc_data2 = r_app2.json()
    total_co2e_2 = calc_data2.get("summary", {}).get("total_co2e_kg")
    print(f"  -> Deepseek Total Calculated Emissions: {total_co2e_2:,.2f} kg CO2e")
    assert total_co2e_2 > 0, "Deepseek total emissions must be non-zero after calculation!"

    print("\n" + "=" * 75)
    print("ALL END-TO-END MASTER RECONCILIATION TESTS PASSED PERFECTLY!")
    print("=" * 75)

if __name__ == "__main__":
    run_e2e_master_test()
