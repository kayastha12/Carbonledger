from typing import List, Dict, Any

class ValidationService:
    """
    ValidationService handles business schema verification and input-versus-output
    data fidelity compliance checks.
    """
    def __init__(self):
        pass

    def validate_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates individual records for essential carbon accounting fields.
        """
        report = []
        for r in records:
            errors = []
            if not r.get("material") or r.get("material") == "Unspecified Material":
                errors.append("Missing Material")
            if r.get("quantity") is None or float(r.get("quantity", 0)) <= 0:
                errors.append("Invalid Quantity")
            if not r.get("unit"):
                errors.append("Missing Unit")
            if errors:
                report.append({"id": r.get("id"), "record": r, "errors": errors})
        return report

    def validate_and_compare(self, 
                             extracted_records: List[Dict[str, Any]], 
                             inventory_records: List[Dict[str, Any]],
                             comparison_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compares input extracted records with output inventory records for high fidelity.
        """
        ext_count = len(extracted_records)
        inv_count = len(inventory_records)

        if ext_count != inv_count:
            return {
                "validation_status": "FAIL",
                "error": f"Record count mismatch: Extracted {ext_count} vs Inventory {inv_count}",
                "total_records_extracted": ext_count,
                "total_records_inventory": inv_count,
                "comparison_entries": comparison_entries
            }

        mismatches = []
        for idx in range(ext_count):
            ext = extracted_records[idx]
            inv = inventory_records[idx]

            if str(ext.get("material")).strip() != str(inv.get("material")).strip():
                mismatches.append(f"Row {idx+1} Material mismatch: Extracted '{ext.get('material')}' vs Inventory '{inv.get('material')}'")

            if float(ext.get("quantity", 0)) != float(inv.get("quantity", 0)):
                mismatches.append(f"Row {idx+1} Quantity mismatch: Extracted {ext.get('quantity')} vs Inventory {inv.get('quantity')}")

            if str(ext.get("unit")).strip() != str(inv.get("unit")).strip():
                mismatches.append(f"Row {idx+1} Unit mismatch: Extracted '{ext.get('unit')}' vs Inventory '{inv.get('unit')}'")

        status = "PASS" if not mismatches else "FAIL"

        return {
            "validation_status": status,
            "total_records_extracted": ext_count,
            "total_records_inventory": inv_count,
            "fidelity_accuracy_pct": 100.0 if status == "PASS" else round((1 - len(mismatches)/ext_count) * 100, 2),
            "mismatches": mismatches,
            "comparison_entries": comparison_entries
        }
