import os
import requests
from services.universal_upload_service import UniversalUploadService

TEST_PDF = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"

def test_download_flow():
    print("Testing calculation and report generation...")
    service = UniversalUploadService()
    parsed_res = service.parse_uploaded_file(TEST_PDF, "deepseek_invoice.pdf")
    records = parsed_res.get("records", [])
    
    upload_id = "test_download_flow_123"
    calc_res = service.calculate_and_save(records, upload_id=upload_id)
    reports = calc_res.get("reports", {})
    
    print("Generated Reports Map:")
    for k, v in reports.items():
        print(f"  {k}: {v}")
        
    project_root = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(project_root, "output", "reports", "uploads", upload_id)
    
    expected_files = ["carbon_report.pdf", "cbam_report.xlsx", "inventory.xlsx", "audit.json", "executive_esg_report.pdf"]
    for f in expected_files:
        f_path = os.path.join(upload_dir, f)
        exists = os.path.exists(f_path)
        size = os.path.getsize(f_path) if exists else 0
        print(f"  File: {f} | Exists: {exists} | Size: {size} bytes")
        assert exists, f"Missing report file {f}"

    print("\nReport generation and download paths verified successfully!")

if __name__ == "__main__":
    test_download_flow()
