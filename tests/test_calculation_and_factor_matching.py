import os
import pytest
from services.workbook_factor_engine import WorkbookFactorEngine
from services.emission_factor_service import EmissionFactorService
from services.universal_upload_service import UniversalUploadService
from services.document_ai_service import DocumentAIService

@pytest.fixture
def factor_engine():
    return WorkbookFactorEngine.get_instance()

@pytest.fixture
def factor_service():
    return EmissionFactorService.get_instance()

def test_1_structural_steel_primary_selected_no_steel_cans(factor_engine):
    """
    TEST 1: Structural Steel Section (primary)
    Expected: Material recognized as Construction Metals (Primary), NOT steel cans.
    """
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "Structural Steel Section (primary metal)",
            "quantity": 1500.0,
            "unit": "kg"
        }
    }
    eval_res = factor_engine.evaluate_activity(rec)
    assert eval_res["calculation_status"] == "READY"
    assert eval_res["calculation_ready"] is True
    assert eval_res["factor"] is not None
    assert eval_res["factor"]["id"] == "19_500_5028_15_1"
    assert "steel cans" not in eval_res["factor"]["level_3"].lower()
    assert eval_res["factor"]["level_2"] == "Construction"
    assert eval_res["factor"]["level_3"] == "Metals"
    assert eval_res["factor"]["column_text"] == "Primary material production"
    assert pytest.approx(eval_res["emission_kgco2e"], 0.01) == 1.5 * 3821.94858

def test_2_structural_steel_closed_loop_recycled(factor_engine):
    """
    TEST 2: Structural Steel Section (closed-loop recycled)
    Expected: Recycled/closed-loop attribute preserved, matches Construction Metals (Closed-loop source).
    """
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "Structural Steel Section (closed-loop recycled)",
            "quantity": 1200.0,
            "unit": "kg"
        }
    }
    eval_res = factor_engine.evaluate_activity(rec)
    assert eval_res["calculation_status"] == "READY"
    assert eval_res["factor"]["id"] == "19_500_5031_15_1"
    assert eval_res["factor"]["column_text"] == "Closed-loop source"
    assert pytest.approx(eval_res["emission_kgco2e"], 0.01) == 1.2 * 1636.68994

def test_3_aluminium_foil_stock_recognized(factor_engine):
    """
    TEST 3: Aluminium Foil Stock
    Expected: Aluminium family recognized, matched to aluminium cans & foil, no steel factor.
    """
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "Aluminium Foil Stock 0.05 mm (primary)",
            "quantity": 300.0,
            "unit": "kg"
        }
    }
    eval_res = factor_engine.evaluate_activity(rec)
    assert eval_res["calculation_status"] == "READY"
    assert eval_res["factor"]["id"] == "19_504_5104_15_1"
    assert "aluminium" in eval_res["factor"]["level_3"].lower()
    assert "steel" not in eval_res["factor"]["level_3"].lower()
    assert pytest.approx(eval_res["emission_kgco2e"], 0.01) == 0.3 * 9113.58251

def test_4_hdpe_granules_classified(factor_engine):
    """
    TEST 4: HDPE Granules
    Expected: HDPE classification, matched to Plastics: HDPE (incl. forming), no generic steel/plastic mismatch.
    """
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "HDPE Granules, injection grade (primary)",
            "quantity": 450.0,
            "unit": "kg"
        }
    }
    eval_res = factor_engine.evaluate_activity(rec)
    assert eval_res["calculation_status"] == "READY"
    assert eval_res["factor"]["id"] == "19_505_5132_15_1"
    assert "HDPE" in eval_res["factor"]["level_3"]
    assert pytest.approx(eval_res["emission_kgco2e"], 0.01) == 0.45 * 3092.8927

def test_5_pet_vs_rpet_distinction(factor_engine):
    """
    TEST 5: PET / rPET
    Expected: Primary and recycled distinctions preserved with different factors.
    """
    rec_primary = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "PET Resin, bottle grade (primary)",
            "quantity": 250.0,
            "unit": "kg"
        }
    }
    eval_primary = factor_engine.evaluate_activity(rec_primary)
    assert eval_primary["calculation_status"] == "READY"
    assert eval_primary["factor"]["id"] == "19_505_5140_15_1"
    assert eval_primary["factor"]["column_text"] == "Primary material production"
    assert pytest.approx(eval_primary["factor"]["value"], 0.01) == 3861.58251

    rec_recycled = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "rPET Resin (closed-loop recycled)",
            "quantity": 220.0,
            "unit": "kg"
        }
    }
    eval_recycled = factor_engine.evaluate_activity(rec_recycled)
    assert eval_recycled["calculation_status"] == "READY"
    assert eval_recycled["factor"]["id"] == "19_505_5143_15_1"
    assert eval_recycled["factor"]["column_text"] == "Closed-loop source"
    assert pytest.approx(eval_recycled["factor"]["value"], 0.01) == 2211.58251
    assert eval_primary["factor"]["value"] > eval_recycled["factor"]["value"]

def test_6_quantity_conversion_kg_to_tonne(factor_engine):
    """
    TEST 6: Quantity conversion: 1500 kg -> 1.5 tonne when factor unit is kg CO2e/tonne.
    """
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "Precast Concrete Machine Base",
            "quantity": 1500.0,
            "unit": "kg"
        }
    }
    eval_res = factor_engine.evaluate_activity(rec)
    assert eval_res["calculation_status"] == "READY"
    assert "1.5 tonne" in eval_res["formula"]
    assert "1500.0 kg" in eval_res["formula"]
    # 1.5 tonnes * 118.80307 kg CO2e/tonne = 178.2046 kg CO2e
    assert pytest.approx(eval_res["emission_kgco2e"], 0.01) == 178.2046

def test_7_transport_matching(factor_engine):
    """
    TEST 7: Transport matching
    19,210 kg (19.21 t) + 180 km + Diesel + Road HGV articulated (>3.5-33 t) + 50% laden
    Expected: Matches 27_304_3126_14_1 (0.1209 kg CO2e/tonne.km), no passenger car factor.
    """
    rec = {
        "activity_type": "TRANSPORTATION",
        "activity": {
            "activity_type": "TRANSPORTATION",
            "transport_mode": "Road - HGV articulated (>3.5-33 t), non-refrigerated diesel, 50% laden",
            "fuel_type": "Diesel",
            "weight": 19210.0,
            "weight_unit": "kg",
            "distance": 180.0,
            "distance_unit": "km"
        }
    }
    eval_res = factor_engine.evaluate_activity(rec)
    assert eval_res["calculation_status"] == "READY"
    assert eval_res["factor"]["id"] == "27_304_3126_14_1"
    assert eval_res["factor"]["uom"] == "tonne.km"
    assert eval_res["factor"]["value"] == 0.1209
    # 19.21 t * 180 km = 3457.8 tonne.km * 0.1209 = 418.04802 kg CO2e
    assert pytest.approx(eval_res["emission_kgco2e"], 0.01) == 418.048

def test_8_unknown_material_not_found_zero_hallucination(factor_engine):
    """
    TEST 8: Completely unknown material
    Expected: FACTOR_NOT_FOUND, 0 emission, never invent a factor.
    """
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "Unobtanium Hyper-Alloy Matrix X-99",
            "quantity": 100.0,
            "unit": "kg"
        }
    }
    eval_res = factor_engine.evaluate_activity(rec)
    assert eval_res["calculation_status"] == "FACTOR_NOT_FOUND"
    assert eval_res["calculation_ready"] is False
    assert eval_res["emission_kgco2e"] == 0.0
    assert eval_res["factor"] is None

def test_9_inv_005_e2e_full_calculation_workflow():
    """
    TEST 9 & 10: Complete PDF extraction -> factor matching -> calculation -> persistence -> dashboard reconciliation.
    """
    pdf_path = "tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf"
    if not os.path.exists(pdf_path):
        from scripts.generate_inv_005 import generate_pdf
        os.makedirs("tests/fixtures", exist_ok=True)
        generate_pdf(pdf_path)

    service = UniversalUploadService()
    parsed_res = service.parse_uploaded_file(pdf_path, "INV-005_TechManufacturing_50Materials_Invoice.pdf")
    records = parsed_res.get("records", [])
    
    assert len(records) == 51, f"Expected 51 extracted records, got {len(records)}"

    # Check calculation readiness
    ready_count = sum(1 for r in records if r.get("carbon_calculation", {}).get("calculation_ready") is True)
    assert ready_count == 51, f"Expected all 51 valid records to be READY, got {ready_count}"

    # Calculate and save
    calc_res = service.calculate_and_save(records, upload_id="test_calc_inv_005")
    summary = calc_res.get("summary", {})
    
    total_co2e = summary.get("total_co2e_kg", 0.0)
    scope1 = summary.get("scope_1_co2e_kg", 0.0)
    scope2 = summary.get("scope_2_co2e_kg", 0.0)
    scope3 = summary.get("scope_3_co2e_kg", 0.0)

    # Reconciliation check
    assert total_co2e > 0.0, "Total footprint must be calculated and > 0"
    assert pytest.approx(total_co2e, 0.01) == (scope1 + scope2 + scope3)
    assert pytest.approx(total_co2e, 1.0) == 40710.49
