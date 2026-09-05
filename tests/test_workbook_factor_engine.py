import os
import pytest
from services.workbook_factor_engine import WorkbookFactorEngine

@pytest.fixture(scope="module")
def engine():
    return WorkbookFactorEngine.get_instance()

def test_diesel_500l_exact_match(engine):
    rec = {
        "activity": {
            "activity_type": "FUEL_CONSUMPTION",
            "fuel_type": "Diesel",
            "quantity": 500.0,
            "unit": "L"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "READY"
    assert res["calculation_ready"] is True
    assert abs(res["emission_kgco2e"] - 1291.77) < 0.01
    assert "2.58354" in res["formula"]
    assert res["factor"]["uom"] == "litres"
    assert res["factor"]["id"] == "1_101_1011_8_1"

def test_natural_gas_mcm_scaling_review(engine):
    rec = {
        "activity": {
            "activity_type": "NATURAL_GAS_CONSUMPTION",
            "energy_type": "Natural Gas",
            "consumption": 500.0,
            "consumption_unit": "MCM"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "REVIEW_REQUIRED"
    assert res["calculation_ready"] is False
    assert "MCM" in res["reason"]
    assert res["emission_kgco2e"] == 0.0

def test_lpg_100kg_unit_conversion(engine):
    rec = {
        "activity": {
            "activity_type": "FUEL_CONSUMPTION",
            "fuel_type": "LPG",
            "quantity": 100.0,
            "unit": "kg"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "READY"
    assert res["calculation_ready"] is True
    # 100 kg = 0.1 tonne * 2939.36095 kg CO2e/tonne = 293.9361 kg CO2e
    assert abs(res["emission_kgco2e"] - 293.9361) < 0.01
    assert "2939.36095" in res["formula"]
    assert res["factor"]["id"] == "1_100_1003_15_1"

def test_rail_freight_tonne_km_calculation(engine):
    rec = {
        "activity": {
            "activity_type": "TRANSPORTATION",
            "transport_mode": "Rail",
            "weight": 5000.0,
            "weight_unit": "kg",
            "distance": 700.0,
            "distance_unit": "km"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "READY"
    assert res["calculation_ready"] is True
    # 5 tonnes * 700 km = 3500 tonne.km * 0.02583 = 90.405 kg CO2e
    assert abs(res["emission_kgco2e"] - 90.405) < 0.001
    assert res["factor"]["uom"] == "tonne.km"
    assert res["factor"]["id"] == "27_315_3151_14_1"

def test_truck_freight_class_review(engine):
    rec = {
        "activity": {
            "activity_type": "TRANSPORTATION",
            "transport_mode": "Truck",
            "weight": 2000.0,
            "weight_unit": "kg",
            "distance": 180.0,
            "distance_unit": "km"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "REVIEW_REQUIRED"
    assert res["calculation_ready"] is False
    assert "vehicle class" in res["reason"].lower()
    assert res["emission_kgco2e"] == 0.0

def test_electricity_india_factor_not_found(engine):
    rec = {
        "company": {"country": "India"},
        "activity": {
            "activity_type": "ELECTRICITY_CONSUMPTION",
            "energy_type": "electricity",
            "consumption": 15000.0,
            "consumption_unit": "kWh"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "FACTOR_NOT_FOUND"
    assert res["calculation_ready"] is False
    assert "India electricity emission factor" in res["reason"]
    assert res["emission_kgco2e"] == 0.0

def test_steel_sheet_semantic_review(engine):
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "Steel Sheet",
            "quantity": 500.0,
            "unit": "kg"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "REVIEW_REQUIRED"
    assert res["calculation_ready"] is False
    assert "Steel Sheet" in res["reason"]
    assert "steel cans" in res["reason"]
    assert res["emission_kgco2e"] == 0.0

def test_plastic_resin_semantic_review(engine):
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "Plastic Resin",
            "quantity": 100.0,
            "unit": "L"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "REVIEW_REQUIRED"
    assert res["calculation_ready"] is False
    assert "Plastic Resin" in res["reason"]
    assert res["emission_kgco2e"] == 0.0

def test_aluminium_semantic_review(engine):
    rec = {
        "activity": {
            "activity_type": "PURCHASED_GOODS",
            "material": "Aluminium",
            "quantity": 250.0,
            "unit": "kg"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "REVIEW_REQUIRED"
    assert res["calculation_ready"] is False
    assert "Aluminium" in res["reason"]
    assert res["emission_kgco2e"] == 0.0

def test_steam_tonne_missing_required_data(engine):
    rec = {
        "activity": {
            "activity_type": "STEAM_CONSUMPTION",
            "energy_type": "Steam",
            "consumption": 1000.0,
            "consumption_unit": "tonne"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "MISSING_REQUIRED_DATA"
    assert res["calculation_ready"] is False
    assert "tonnes" in res["reason"] and "requires kWh" in res["reason"]
    assert res["emission_kgco2e"] == 0.0

def test_purchase_order_reference_only_guard(engine):
    rec = {
        "document_type": "PURCHASE_ORDER",
        "activity": {
            "activity_type": "PURCHASE_ORDER",
            "material": "Steel Sheet",
            "quantity": 1000.0,
            "unit": "kg"
        }
    }
    res = engine.evaluate_activity(rec)
    assert res["calculation_status"] == "REFERENCE_ONLY"
    assert res["calculation_ready"] is False
    assert res["emission_kgco2e"] == 0.0
    assert "double-counting" in res["reason"]

def test_factor_serialization_safety(engine):
    factor = engine.factors_by_id.get("1_101_1011_8_1")
    assert factor is not None
    d = factor.to_dict()
    assert isinstance(d["value"], float)
    assert isinstance(d["unit"], str)
    assert isinstance(d["source"], str)
    assert "id" in d and d["id"] == "1_101_1011_8_1"
