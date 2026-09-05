import time
import requests
import json

PROD_API_URL = "https://carbonledger-api-8bl2.onrender.com"
TEST_PDF_PATH = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"

def monitor(max_minutes=6):
    start = time.time()
    print(f"Monitoring Render deployment for version 7.1 (max {max_minutes} mins)...")
    
    while time.time() - start < max_minutes * 60:
        try:
            r = requests.get(f"{PROD_API_URL}/health", timeout=10)
            if r.status_code == 200:
                data = r.json()
                version = data.get("version")
                print(f"[{int(time.time() - start)}s] Live API version: {version}")
                if version == "7.1":
                    print("\n Version 7.1 is LIVE! Checking Document AI status...")
                    dbg_resp = requests.get(f"{PROD_API_URL}/api/debug/doc-ai", timeout=15)
                    print("Debug Endpoint Response:", json.dumps(dbg_resp.json(), indent=2))
                    
                    print(f"\n Testing universal PDF upload on {PROD_API_URL}/api/upload/universal...")
                    with open(TEST_PDF_PATH, "rb") as f:
                        files = {"file": ("deepseek_html_20260731_54ad15 (1).pdf", f, "application/pdf")}
                        upload_resp = requests.post(f"{PROD_API_URL}/api/upload/universal", files=files, timeout=90)
                    
                    if upload_resp.status_code == 200:
                        up_data = upload_resp.json()
                        records = up_data.get("records", [])
                        print(f"\n SUCCESS! Upload returned status {upload_resp.status_code}")
                        print(f"Total Extracted Records: {len(records)}")
                        print(f"Document ID: {up_data.get('upload_id')}")
                        for idx, rec in enumerate(records):
                            mat = rec.get("material") or rec.get("category") or rec.get("fuel_type")
                            qty = rec.get("quantity")
                            unit = rec.get("unit")
                            ef = rec.get("emission_factor")
                            co2 = rec.get("carbon_footprint") or rec.get("emissions") or rec.get("co2e_kg")
                            scope = rec.get("scope")
                            print(f"  [{idx+1:02d}] {mat:<22} | {qty} {unit:<5} | EF: {ef} | Scope: {scope} | Carbon: {co2}")
                        return True
                    else:
                        print("Upload failed:", upload_resp.status_code, upload_resp.text)
                        return False
            else:
                print(f"[{int(time.time() - start)}s] Status code {r.status_code}")
        except Exception as e:
            print(f"[{int(time.time() - start)}s] Ping error: {e}")
            
        time.sleep(15)
        
    print("Monitoring timed out.")
    return False

if __name__ == "__main__":
    monitor()
