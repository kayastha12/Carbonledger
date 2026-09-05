import time
import requests
import json

PROD_API_URL = "https://carbonledger-api-8bl2.onrender.com"
TEST_PDF_PATH = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"

def test_prod_health():
    try:
        r = requests.get(f"{PROD_API_URL}/", timeout=15)
        print("Health response:", r.status_code, r.text)
        return r.status_code == 200
    except Exception as e:
        print("Health check failed:", e)
        return False

def test_prod_upload():
    print(f"Testing upload of {TEST_PDF_PATH} to {PROD_API_URL}/api/upload/universal...")
    with open(TEST_PDF_PATH, "rb") as f:
        files = {"file": ("deepseek_html_20260731_54ad15 (1).pdf", f, "application/pdf")}
        r = requests.post(f"{PROD_API_URL}/api/upload/universal", files=files, timeout=60)
    
    print("Status code:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        status = data.get("status")
        records = data.get("records", [])
        total_carbon = data.get("total_carbon_emissions")
        print(f"Upload Result: status={status}, record_count={len(records)}, total_carbon={total_carbon}")
        print("Records summary:")
        for idx, rec in enumerate(records[:10]):
            print(f"  [{idx+1}] {rec.get('material', rec.get('category'))} | {rec.get('quantity')} {rec.get('unit')} | factor={rec.get('emission_factor')} | carbon={rec.get('carbon_footprint') or rec.get('emissions')}")
        if len(records) > 10:
            print(f"  ... and {len(records)-10} more records.")
        return len(records) > 0
    else:
        print("Error text:", r.text)
        return False

if __name__ == "__main__":
    test_prod_health()
    test_prod_upload()
