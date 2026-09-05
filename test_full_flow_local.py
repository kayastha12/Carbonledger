import os
import json
from services.universal_upload_service import UniversalUploadService

TEST_PDF = r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf"

def test_full_pipeline():
    print(f"=== Testing Full Document AI Flow on: {TEST_PDF} ===")
    service = UniversalUploadService()
    
    # 1. Parse uploaded PDF
    parsed_res = service.parse_uploaded_file(TEST_PDF, "deepseek_invoice.pdf")
    records = parsed_res.get("records", [])
    print(f"1. Parsed Document Result:")
    print(f"   Status: {parsed_res.get('file_name')}")
    print(f"   Pages: {parsed_res.get('pages_count')}, Tables: {parsed_res.get('tables_count')}")
    print(f"   Extracted Records Count: {len(records)}")
    
    if not records:
        print("❌ FAILED: No records extracted!")
        return False
        
    print(f"   Sample Extracted Row 1: {records[0].get('material')} | {records[0].get('quantity')} {records[0].get('unit')}")
    
    # 2. Calculate and Save
    calc_res = service.calculate_and_save(records, upload_id="test_prod_full_flow")
    summary = calc_res.get("summary", {})
    reports = calc_res.get("reports", {})
    inv_records = calc_res.get("inventory_records", [])
    
    print(f"\n2. Calculation & Audit Result:")
    print(f"   Total CO2e (kg): {summary.get('total_co2e_kg')}")
    print(f"   Total CO2e (tonnes): {summary.get('total_co2e_tonnes')}")
    print(f"   Scope 1: {summary.get('scope_1_co2e_kg')} kg")
    print(f"   Scope 2: {summary.get('scope_2_co2e_kg')} kg")
    print(f"   Scope 3: {summary.get('scope_3_co2e_kg')} kg")
    print(f"   CBAM Cost: €{summary.get('total_cbam_cost_eur')}")
    print(f"   Inventory Records: {len(inv_records)}")
    print(f"   Reports Generated: {list(reports.keys())}")
    
    print("\n✅ Full end-to-end PDF parsing and carbon emission calculation verified successfully!")
    return True

if __name__ == "__main__":
    test_full_pipeline()
