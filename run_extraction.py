import sys
import os
import io
import argparse
import json

# Ensure stdout uses utf-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.universal_upload_service import UniversalUploadService

def run(pdf_path: str, debug: bool = False):
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
        
    filename = os.path.basename(pdf_path)
    print("=" * 80)
    print(f"CARBONLEDGER EXTRACTION RUNNER: {filename}")
    print("=" * 80)
    
    service = UniversalUploadService()
    result = service.parse_uploaded_file(pdf_path, filename)
    
    records = result.get("records", [])
    pages_count = result.get("pages_count", 0)
    tables_count = result.get("tables_count", 0)
    proc_time = result.get("processing_time_ms", 0)
    
    print(f"\nDocument Ingestion Summary:")
    print(f"  • File: {filename}")
    print(f"  • Pages: {pages_count}")
    print(f"  • Tables Processed: {tables_count}")
    print(f"  • Processing Time: {proc_time} ms")
    print(f"  • Total Real Records Extracted: {len(records)}")
    
    ready_count = sum(1 for r in records if r.get("carbon_calculation", {}).get("calculation_ready") is True)
    review_count = len(records) - ready_count
    
    print(f"  • Calculation Ready Records: {ready_count}")
    print(f"  • Review Required Records: {review_count}")
    
    print("\n" + "-" * 80)
    print(f"{'#':<3} | {'Material / Activity':<30} | {'Qty':<10} | {'Unit':<8} | {'Supplier':<25} | {'Cost':<12} | {'Country':<8} | {'Ready'}")
    print("-" * 80)
    
    for idx, r in enumerate(records, start=1):
        mat = str(r.get("material") or r.get("activity", {}).get("material") or r.get("activity", {}).get("product") or r.get("transport_mode") or r.get("fuel_type") or "-")[:28]
        qty_val = r.get("quantity") if r.get("quantity") is not None else r.get("activity", {}).get("quantity")
        qty_str = str(qty_val) if qty_val is not None else "-"
        unit_str = str(r.get("unit") or r.get("activity", {}).get("unit") or "-")[:7]
        sup = r.get("supplier")
        sup_str = str(sup.get("name") if isinstance(sup, dict) else (sup or "-"))[:23]
        cost_val = r.get("cost") if r.get("cost") is not None else r.get("financial", {}).get("amount")
        curr = r.get("currency") or r.get("financial", {}).get("currency") or ""
        cost_str = f"{curr}{cost_val:,.2f}" if cost_val is not None else "-"
        country_str = str(r.get("country") or r.get("company", {}).get("country") or "-")[:7]
        is_ready = "✓" if r.get("carbon_calculation", {}).get("calculation_ready") is True else "✗"
        
        print(f"{idx:<3} | {mat:<30} | {qty_str:<10} | {unit_str:<8} | {sup_str:<25} | {cost_str:<12} | {country_str:<8} | {is_ready}")

    if debug:
        print("\n" + "=" * 80)
        print("DEBUG RECORD DETAILS (JSON):")
        print("=" * 80)
        print(json.dumps(records, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CarbonLedger strict extraction on a PDF.")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--debug", action="store_true", help="Print debug JSON payload")
    
    args = parser.parse_args()
    run(args.pdf_path, debug=args.debug)
