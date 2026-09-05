import os
import sys

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.test_full_workflow_suite import (
    test_1_pdf_upload_receipt,
    test_2_and_4_real_pdf_extraction,
    test_5_and_7_approval_and_calculation,
    test_6_duplicate_approval_idempotency,
    test_8_and_9_carbon_ledger_and_dashboard_totals,
    test_10_new_document_clears_previous_state,
    test_11_invalid_approval_missing_material
)

def main():
    print("=== Running CarbonLedger Full Workflow Test Suite ===")
    
    tests = [
        ("TEST 1: PDF Upload Receipt", test_1_pdf_upload_receipt),
        ("TEST 2 & 4: Real PDF Extraction & Carbon Activity Detection", test_2_and_4_real_pdf_extraction),
        ("TEST 5 & 7: Document Approval & Carbon Calculation", test_5_and_7_approval_and_calculation),
        ("TEST 6: Duplicate Approval Idempotency", test_6_duplicate_approval_idempotency),
        ("TEST 8 & 9: Carbon Ledger & Dashboard Totals Persistence", test_8_and_9_carbon_ledger_and_dashboard_totals),
        ("TEST 10: New Document Clears Previous State", test_10_new_document_clears_previous_state),
        ("TEST 11: Invalid Approval Handling", test_11_invalid_approval_missing_material)
    ]
    
    passed = 0
    for name, fn in tests:
        try:
            print(f"\n[RUNNING] {name}...")
            fn()
            print(f"[PASSED] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAILED] {name}: {e}")
            import traceback
            traceback.print_exc()
            
    print(f"\n=== Summary: {passed}/{len(tests)} Tests Passed Successfully ===")
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
