import os
import sys
import time
import requests

API_URL = "http://127.0.0.1:8000"
PDF_PATH = os.path.abspath("tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf")

def run_benchmark():
    print("=" * 60)
    print("CARBONLEDGER SINGLE PDF INVOICE BENCHMARK (LOCAL)")
    print("=" * 60)

    # 1. Login
    login_res = requests.post(f"{API_URL}/api/auth/login", json={
        "email": "demo@carbonledger.io",
        "password": "demopassword123"
    })
    if login_res.status_code != 200:
        # Create user or try register
        reg_res = requests.post(f"{API_URL}/api/auth/register", json={
            "email": "demo@carbonledger.io",
            "password": "demopassword123",
            "full_name": "Demo User"
        })
        token = reg_res.json().get("access_token")
    else:
        token = login_res.json().get("access_token")

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 2. Measure PDF Upload & Extraction
    print(f"\n[1] Uploading single PDF invoice: {os.path.basename(PDF_PATH)}")
    t0 = time.perf_counter()
    with open(PDF_PATH, "rb") as f:
        files = {"file": (os.path.basename(PDF_PATH), f, "application/pdf")}
        up_res = requests.post(f"{API_URL}/api/upload/universal", headers=headers, files=files)
    t1 = time.perf_counter()

    upload_duration = round(t1 - t0, 3)
    print(f"Status Code: {up_res.status_code}")
    assert up_res.status_code == 200, f"Upload failed: {up_res.text}"

    data = up_res.json()
    upload_id = data.get("upload_id")
    records = data.get("records", [])
    timings = data.get("timings", {})

    print(f"\n--- LOCAL UPLOAD & EXTRACTION TIMINGS ---")
    print(f"Total Client-Perceived Upload Time: {upload_duration}s")
    print(f"Backend File Save: {timings.get('file_save_sec', 0)}s")
    print(f"Backend PDF Extraction & Factor Evaluation: {timings.get('extraction_sec', 0)}s")
    print(f"Backend Database Record Save: {timings.get('database_sec', 0)}s")
    print(f"Extracted Records: {len(records)} line items")
    print(f"Upload ID: {upload_id}")

    # 3. Check Dashboard BEFORE Approval (Must be None or no approved session)
    latest_pre = requests.get(f"{API_URL}/api/upload/latest", headers=headers).json()
    print(f"\n[2] Pre-Approval Dashboard Upload Session: {latest_pre} (Expected: None)")
    assert latest_pre is None or latest_pre.get("total_co2e_kg", 0) == 0, "Dashboard was unexpectedly populated before approval!"

    # 4. Approve & Calculate
    print(f"\n[3] Approving and calculating emissions for {len(records)} records...")
    t_calc0 = time.perf_counter()
    appr_res = requests.post(f"{API_URL}/api/upload/approve", headers=headers, json={
        "upload_id": upload_id,
        "records": records
    })
    t_calc1 = time.perf_counter()
    calc_duration = round(t_calc1 - t_calc0, 3)
    assert appr_res.status_code == 200, f"Approval failed: {appr_res.text}"
    calc_data = appr_res.json()
    summary = calc_data.get("summary", {})
    total_co2e = summary.get("total_co2e_kg", 0)
    print(f"Calculation Time: {calc_duration}s")
    print(f"Calculated Total Footprint: {total_co2e} kg CO2e")

    # 5. Check Dashboard AFTER Approval (Must be > 0.0 kg CO2e)
    latest_post = requests.get(f"{API_URL}/api/upload/latest", headers=headers).json()
    assert latest_post is not None, "Dashboard upload session not found after approval!"
    total_footprint = latest_post.get("summary", {}).get("total_co2e_kg", 0) or latest_post.get("total_co2e_kg", 0)
    print(f"\n[4] Post-Approval Dashboard Total Footprint: {total_footprint} kg CO2e")
    print(f"Post-Approval Calculated Items: {len(latest_post.get('records', []))} records")
    assert total_footprint > 0, "Dashboard is still 0 after calculation approval!"

    print("\n" + "=" * 60)
    print("LOCAL BENCHMARK AND FIDELITY CHECK: ALL PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_benchmark()
