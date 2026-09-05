import json
from services.universal_upload_service import UniversalUploadService

TEST_PDF = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"

def dump_sample_records():
    service = UniversalUploadService()
    parsed_res = service.parse_uploaded_file(TEST_PDF, "deepseek_invoice_2026.pdf")
    records = parsed_res.get("records", [])
    print(f"Extracted {len(records)} records.")
    
    out_path = r"c:\Users\Aniket Singh\OneDrive\Documents\GitHub\Carbonledger\frontend\src\sample_records.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Saved sample records to {out_path}")

if __name__ == "__main__":
    dump_sample_records()
