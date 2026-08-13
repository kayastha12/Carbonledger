import pytest
from services.field_extraction_service import parse_numeric_value, extract_unit_and_value, detect_region_from_fields, FieldExtractionService
from services.universal_upload_service import UniversalUploadService

def test_number_and_quantity_parsing():
    # 1. 1,000 kg -> 1000
    qty, unit = extract_unit_and_value("1,000 kg")
    assert qty == 1000.0
    assert unit == "kg"

    # 2. 200 L -> 200 L
    qty, unit = extract_unit_and_value("200 L")
    assert qty == 200.0
    assert unit == "L"

    # 3. Currency and Indian formatting
    cost = parse_numeric_value("₹1,72,500")
    assert cost == 172500.0

    # 4. Decimals and Scientific Notation
    assert parse_numeric_value("1,250.50") == 1250.50
    assert parse_numeric_value("0.25") == 0.25
    assert parse_numeric_value("1.23e3") == 1230.0
    assert parse_numeric_value("-500.25") == -500.25

def test_material_matching_no_rename():
    service = FieldExtractionService()
    raw_record = {
        "material": "Steel Sheet",
        "quantity": "1,000 kg",
        "unit": "kg",
        "supplier": "Steel Traders Ltd"
    }
    parsed = service._standardize_and_score(raw_record, "ERP Export", "test.pdf", 1, 1, 0.99)
    # Parser should NEVER rename materials
    assert parsed["material"] == "Steel Sheet"

def test_region_detection_without_guessing():
    # Detect from GST/VAT or explicit text
    assert detect_region_from_fields("TechManufacturing India Ltd.", {}) == "IN"
    assert detect_region_from_fields("VAT DE123456789", {}) == "DE"
    assert detect_region_from_fields("GmbH Munich", {}) == "DE"
    assert detect_region_from_fields("Pincode 400001", {}) == "IN"

def test_automatic_validation_mismatch():
    service = UniversalUploadService(output_dir="D:\\CarbanLedger\\output\\temp")
    
    # Valid record
    valid_record = {
        "po_number": "PO-0001",
        "supplier": "Steel Traders Ltd",
        "material": "Steel Sheet",
        "quantity": 1000.0,
        "quantity_raw": "1,000",
        "unit": "kg",
        "unit_raw": "kg",
        "cost": 50000.0,
        "cost_raw": "50,000",
        "country": "IN",
        "country_raw": "India"
    }
    
    # Should not raise exception
    service._validate_required_fields([valid_record])
    
    # Manual edits (Quantity edited from 1,000 to 2000) should NOT raise any exception
    edited_record = valid_record.copy()
    edited_record["quantity"] = 2000.0
    service._validate_required_fields([edited_record])
    
    # Material Missing check
    invalid_mat_record = valid_record.copy()
    invalid_mat_record["material"] = ""
    with pytest.raises(ValueError, match="Material Missing"):
        service._validate_required_fields([invalid_mat_record])

    # Country Missing check
    invalid_country_record = valid_record.copy()
    invalid_country_record["country"] = ""
    with pytest.raises(ValueError, match="Country Missing"):
        service._validate_required_fields([invalid_country_record])

    # Quantity Invalid check
    invalid_qty_record = valid_record.copy()
    invalid_qty_record["quantity"] = -5.0
    with pytest.raises(ValueError, match="Quantity Invalid"):
        service._validate_required_fields([invalid_qty_record])

    # Unit Unsupported check
    invalid_unit_record = valid_record.copy()
    invalid_unit_record["unit"] = "invalid_unit"
    with pytest.raises(ValueError, match="Unit Unsupported"):
        service._validate_required_fields([invalid_unit_record])
