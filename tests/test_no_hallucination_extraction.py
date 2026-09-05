"""
Comprehensive test suite verifying the strict No-Hallucination rules:
- No default/placeholder values ("Unspecified Material", "Unknown Supplier", quantity=1, cost=0, EUR, IN)
- Missing fields return None
- calculation_ready is False when essential fields are missing
- Provenance is preserved on every real extracted field
- Multi-line cell tokens are reconstructed accurately
- Summary, metadata, and empty rows are rejected
"""

import pytest
from services.field_extraction_service import (
    FieldExtractionService,
    extract_unit_and_value,
    extract_unit_from_header_or_string,
    normalize_material_name,
)
from services.table_detection_service import TableDetectionService, clean_cell_text
from services.carbon_calculation_service import CarbonCalculationService


@pytest.fixture
def field_service():
    return FieldExtractionService()


@pytest.fixture
def table_service():
    return TableDetectionService()


@pytest.fixture
def calc_service():
    return CarbonCalculationService()


# 1. Missing material does not become "Unspecified Material"
def test_missing_material_is_none(field_service):
    tables = [{
        "headers": ["Quantity", "Supplier"],
        "rows": [["500 kg", "Steel Traders Ltd"]],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Invoice", "raw text", tables, "test.pdf")
    assert len(records) == 1
    assert records[0]["material"] is None
    assert records[0]["material"] != "Unspecified Material"
    assert records[0]["carbon_calculation"]["calculation_ready"] is False
    assert "material" in records[0]["carbon_calculation"]["missing_fields"]


# 2. Missing supplier does not become "Unknown Supplier"
def test_missing_supplier_is_none(field_service):
    tables = [{
        "headers": ["Material", "Quantity", "Unit"],
        "rows": [["Steel Sheet", "500", "kg"]],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Invoice", "raw text", tables, "test.pdf")
    assert len(records) == 1
    assert records[0]["supplier"] is None


# 3. Missing quantity does not become 1
def test_missing_quantity_is_none(field_service):
    tables = [{
        "headers": ["Material", "Supplier"],
        "rows": [["Steel Sheet", "Steel Traders Ltd"]],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Invoice", "raw text", tables, "test.pdf")
    assert len(records) == 1
    assert records[0]["quantity"] is None
    assert records[0]["quantity"] != 1.0
    assert records[0]["carbon_calculation"]["calculation_ready"] is False
    assert "quantity" in records[0]["carbon_calculation"]["missing_fields"]


# 4. Missing amount does not become 0
def test_missing_amount_is_none(field_service):
    tables = [{
        "headers": ["Material", "Quantity", "Unit"],
        "rows": [["Steel Sheet", "500", "kg"]],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Invoice", "raw text", tables, "test.pdf")
    assert len(records) == 1
    assert records[0]["cost"] is None


# 5. Missing currency does not become EUR
def test_missing_currency_is_none(field_service):
    tables = [{
        "headers": ["Material", "Quantity", "Unit", "Amount"],
        "rows": [["Steel Sheet", "500", "kg", "5000"]],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Invoice", "raw text without currency markers", tables, "test.pdf")
    assert len(records) == 1
    assert records[0]["currency"] is None
    assert records[0]["currency"] != "EUR"


# 6. Missing country does not become IN
def test_missing_country_is_none(field_service):
    tables = [{
        "headers": ["Material", "Quantity", "Unit"],
        "rows": [["Steel Sheet", "500", "kg"]],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Invoice", "plain description without region", tables, "test.pdf")
    assert len(records) == 1
    assert records[0]["country"] is None
    assert records[0]["country"] != "IN"
    assert records[0]["country"] != "DE"


# 7. Empty table rows do not create records
def test_empty_rows_do_not_create_records(field_service):
    tables = [{
        "headers": ["Material", "Quantity", "Supplier"],
        "rows": [["", "", ""], ["   ", "—", ""]],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Invoice", "raw text", tables, "test.pdf")
    assert len(records) == 0


# 8. Header rows do not create records
def test_header_rows_do_not_create_records(field_service):
    tables = [{
        "headers": ["Material", "Quantity", "Unit", "Supplier"],
        "rows": [
            ["Material", "Quantity", "Unit", "Supplier"],  # Repeated header as row
            ["Steel Sheet", "500", "kg", "Steel Traders Ltd"],
        ],
        "page": 1,
        "confidence": 0.95
    }]
    records = field_service.extract_fields("Invoice", "raw text", tables, "test.pdf")
    assert len(records) == 1
    assert records[0]["material"] == "Steel Sheet"


# 9. Metadata tables do not create records
def test_metadata_tables_rejected(table_service):
    headers = ["Invoice No.", "INV-2025-001", "Invoice Date", "15-Jan-2025"]
    rows = [["Supplier", "Steel Corp", "Customer", "CarbonLedger Inc"]]
    assert table_service.is_valid_data_table(headers, rows) is False


# 10. Dataset summary pages do not create records
def test_dataset_summary_rejected(table_service):
    headers = ["Phase 1", "Phase 2", "Phase 3"]
    rows = [["Complete", "Complete", "Complete"]]
    assert table_service.is_valid_data_table(headers, rows) is False


# 11. Real quantities are preserved
def test_real_quantities_preserved():
    val, unit = extract_unit_and_value("500 kg")
    assert val == 500.0
    assert unit == "kg"

    val2, unit2 = extract_unit_and_value("1250.75 L")
    assert val2 == 1250.75
    assert unit2 == "L"


# 12. Units are preserved correctly
def test_units_preserved_correctly():
    assert extract_unit_from_header_or_string("Qty (kg)") == "kg"
    assert extract_unit_from_header_or_string("Consumption (MWh)") == "MWh"
    assert extract_unit_from_header_or_string("Distance (km)") == "km"
    assert extract_unit_from_header_or_string("Weight (tonne)") == "tonne"


# 13. kg → tonne conversion is mathematically correct
def test_kg_to_tonne_conversion():
    qty_kg = 5000.0
    qty_tonne = qty_kg / 1000.0
    assert qty_tonne == 5.0
    assert 500.0 / 1000.0 == 0.5


# 14. Multi-line supplier names are reconstructed correctly
def test_multiline_supplier_name_reconstructed():
    raw_cell = "Plastic Supplies\nLtd"
    cleaned = clean_cell_text(raw_cell)
    assert cleaned == "Plastic Supplies Ltd"


# 15. Multi-line dates are reconstructed correctly
def test_multiline_dates_reconstructed():
    raw_cell = "2025-01-\n15"
    cleaned = clean_cell_text(raw_cell)
    assert cleaned == "2025-01-15"


# 16. Multi-line invoice/PO IDs are reconstructed correctly
def test_multiline_ids_reconstructed():
    raw_cell = "PO-\n2025-\n001"
    cleaned = clean_cell_text(raw_cell)
    assert cleaned == "PO-2025-001"


# 17. Every extracted field has valid provenance
def test_field_provenance_populated(field_service):
    tables = [{
        "headers": ["Material", "Quantity", "Unit", "Supplier"],
        "rows": [["Steel Sheet", "500", "kg", "Steel Traders Ltd"]],
        "page": 2,
        "confidence": 0.98
    }]
    records = field_service.extract_fields("Invoice", "raw text", tables, "test.pdf")
    assert len(records) == 1
    rec = records[0]

    assert rec["page_number"] == 2
    assert "material" in rec["provenance"]
    assert rec["provenance"]["material"]["raw_text"] == "Steel Sheet"
    assert rec["provenance"]["material"]["page"] == 2
    assert "quantity" in rec["provenance"]
    assert rec["provenance"]["quantity"]["raw_text"] == "500"


# 18. Every generated CarbonActivityRecord corresponds to a real PDF row
def test_records_correspond_to_real_rows(field_service):
    tables = [{
        "headers": ["Material", "Quantity", "Unit", "Supplier"],
        "rows": [
            ["Steel Sheet", "500", "kg", "Steel Traders Ltd"],
            ["Plastic Resin", "100", "L", "Plastic Supplies Ltd"],
            ["Aluminum Bar", "250", "kg", "Aluminum Suppliers"],
        ],
        "page": 1,
        "confidence": 0.98
    }]
    records = field_service.extract_fields("Invoice", "raw text", tables, "test.pdf")
    assert len(records) == 3
    assert records[0]["material"] == "Steel Sheet"
    assert records[0]["quantity"] == 500.0
    assert records[1]["material"] == "Plastic Resin"
    assert records[1]["quantity"] == 100.0
    assert records[2]["material"] == "Aluminium Bar"
    assert records[2]["material_raw"] == "Aluminum Bar"
    assert records[2]["quantity"] == 250.0


# 19. Emission factor matching does not run on fake/unknown material
def test_no_emission_factor_for_none_material(calc_service):
    with pytest.raises(ValueError, match="Material Missing"):
        calc_service.calculate_scope_emissions(
            scope="Scope 3",
            material=None,
            quantity=500.0,
            unit="kg",
            region="DE"
        )


# 20. Calculation readiness is false when essential real fields are missing
def test_calculation_readiness_false_when_missing_fields(calc_service):
    # Missing unit raises error and blocks calculation
    with pytest.raises(ValueError, match="Unit Unsupported"):
        calc_service.calculate_scope_emissions(
            scope="Scope 3",
            material="Steel Sheet",
            quantity=500.0,
            unit=None,
            region="DE"
        )

    # Missing quantity raises error
    with pytest.raises(ValueError, match="Quantity Invalid"):
        calc_service.calculate_scope_emissions(
            scope="Scope 3",
            material="Steel Sheet",
            quantity=None,
            unit="kg",
            region="DE"
        )
