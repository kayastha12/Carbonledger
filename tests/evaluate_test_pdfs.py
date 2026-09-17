import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.universal_upload_service import UniversalUploadService

def run():
    service = UniversalUploadService()

    pdf1_candidates = [
        r"D:\internship\deepseek_html_20260731_54ad15 (1).pdf",
        r"tests\fixtures\deepseek_html_20260731_54ad15 (1).pdf",
        r"deepseek_html_20260731_54ad15 (1).pdf"
    ]
    pdf1_path = next((p for p in pdf1_candidates if os.path.exists(p)), None)
    pdf2_path = r"tests\fixtures\INV-005_TechManufacturing_50Materials_Invoice.pdf"

    print("=== PDF 1 EVALUATION ===")
    if pdf1_path:
        p1 = service.parse_uploaded_file(pdf1_path, os.path.basename(pdf1_path))
        recs1 = p1.get("records", [])
        calc1 = service.calculate_and_save(recs1, upload_id="test_p1")
        sum1 = calc1.get("summary", {})
        print(f"Extraction count: {len(recs1)}")
        print(f"Calculation count: {sum1.get('rows_calculated')}")
        print(f"Review count: {sum1.get('rows_manual_review')}")
        print(f"Total calculated CO2e: {sum1.get('total_co2e_kg')} kg")
        print(f"Scope 1: {sum1.get('scope_1_co2e_kg')} kg")
        print(f"Scope 2: {sum1.get('scope_2_co2e_kg')} kg")
        print(f"Scope 3: {sum1.get('scope_3_co2e_kg')} kg")
    else:
        print("PDF 1 path not found")

    print("\n=== PDF 2 EVALUATION ===")
    if os.path.exists(pdf2_path):
        p2 = service.parse_uploaded_file(pdf2_path, os.path.basename(pdf2_path))
        recs2 = p2.get("records", [])
        calc2 = service.calculate_and_save(recs2, upload_id="test_p2")
        sum2 = calc2.get("summary", {})
        print(f"Extraction count: {len(recs2)}")
        print(f"Calculation count: {sum2.get('rows_calculated')}")
        print(f"Review count: {sum2.get('rows_manual_review')}")
        print(f"Total calculated CO2e: {sum2.get('total_co2e_kg')} kg")
        print(f"Scope 1: {sum2.get('scope_1_co2e_kg')} kg")
        print(f"Scope 2: {sum2.get('scope_2_co2e_kg')} kg")
        print(f"Scope 3: {sum2.get('scope_3_co2e_kg')} kg")
    else:
        print("PDF 2 path not found")

if __name__ == "__main__":
    run()
