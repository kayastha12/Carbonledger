import time
import requests

PROD_API_URL = "https://carbonledger-api-8bl2.onrender.com"
TEST_PDF_PATH = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"

def poll_for_deployment(max_attempts=20, interval=15):
    print("Waiting for Render deployment of main branch...")
    for i in range(1, max_attempts + 1):
        print(f"\n[Attempt {i}/{max_attempts}] Testing production upload...")
        try:
            with open(TEST_PDF_PATH, "rb") as f:
                files = {"file": ("deepseek_html_20260731_54ad15 (1).pdf", f, "application/pdf")}
                r = requests.post(f"{PROD_API_URL}/api/upload/universal", files=files, timeout=60)
            
            if r.status_code == 200:
                data = r.json()
                records = data.get("records", [])
                total_carbon = data.get("total_carbon_emissions")
                print(f"Status 200: record_count={len(records)}, total_carbon={total_carbon}")
                if len(records) > 0:
                    print(f"\n SUCCESS! Render has deployed the new build!")
                    print(f"Extracted {len(records)} records in Production:")
                    for idx, rec in enumerate(records):
                        print(f"  [{idx+1}] {rec.get('material', rec.get('category'))} | {rec.get('quantity')} {rec.get('unit')} | factor={rec.get('emission_factor')} | carbon={rec.get('carbon_footprint') or rec.get('emissions')}")
                    return True
            else:
                print(f"Status code: {r.status_code}, response: {r.text[:200]}")
        except Exception as e:
            print(f"Error connecting: {e}")
        
        time.sleep(interval)
    
    print("\nDeployment poll timed out.")
    return False

if __name__ == "__main__":
    poll_for_deployment()
