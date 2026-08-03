# Script to rebuild the ChromaDB Vector Index for CarbonLedger
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from preprocessing.clean_factors import clean_and_build_master
from vector_db.chroma_service import ChromaService

def rebuild_db():
    print("=" * 60)
    print("CarbonLedger Vector Database Rebuilder")
    print("=" * 60)
    
    excel_path = os.path.join(ROOT, "datasets/CarbonLedger_GHG_Factors_2026_Clean.xlsx")
    out_csv = os.path.join(ROOT, "preprocessing/master_factors_cleaned.csv")
    out_json = os.path.join(ROOT, "preprocessing/master_factors_cleaned.json")
    
    if not os.path.exists(excel_path):
        print(f"Error: GHG Factor Excel sheet not found at: {excel_path}")
        sys.exit(1)
        
    # Step 1: Run cleaner to generate CSV and JSON factors
    print("\n[+] Step 1: Cleaning raw emission factors from Excel...")
    try:
        clean_and_build_master(excel_path, out_csv, out_json)
        print("[-] Step 1 completed successfully.")
    except Exception as e:
        print(f"[!] Error in factor cleaning: {e}")
        sys.exit(1)
        
    # Step 2: Index factors into ChromaDB
    print("\n[+] Step 2: Embedding and indexing factors into ChromaDB...")
    try:
        service = ChromaService()
        if os.path.exists(out_json):
            service.index_factors(out_json, refresh_embeddings=True)
            print("[-] Step 2 completed successfully.")
            
            # Step 3: Run validation query
            print("\n[+] Step 3: Testing vector search query...")
            test_query = "Steel Sheet Metal"
            results = service.query_factors(test_query, top_n=2)
            if results:
                print(f"[-] Query Test SUCCESS: Found matches for '{test_query}':")
                for r in results:
                    print(f"  - [{r.get('id')}] {r.get('activity')} (Confidence: {r.get('confidence'):.2%}, Factor: {r.get('factor')} {r.get('ghg_unit')})")
            else:
                print("[!] Query Test FAILED: No matches found.")
        else:
            print(f"[!] Error: Cleaned JSON factors not found at: {out_json}")
            sys.exit(1)
    except Exception as e:
        print(f"[!] Error in vector database indexing: {e}")
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("Vector database rebuild completed successfully.")
    print("=" * 60)

if __name__ == "__main__":
    rebuild_db()
