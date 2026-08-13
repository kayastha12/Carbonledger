import pytest
import time
from services.emission_factor_service import EmissionFactorService
from services.calculation_engine import CalculationEngine

@pytest.fixture(autouse=True)
def reset_service():
    EmissionFactorService.reset_instance()
    yield

def test_exact_match():
    service = EmissionFactorService.get_instance()
    match = service.get_factor("Diesel Fuel", scope="Scope 1", unit="liters")
    assert match is not None
    assert match.emission_factor > 0
    assert match.confidence >= 0.95
    assert match.match_method in ["exact", "normalized"]
    assert match.execution_time_ms < 10.0

def test_rapidfuzz_match():
    service = EmissionFactorService.get_instance()
    match = service.get_factor("Steel Sheet Metal Heavy Use")
    assert match is not None
    assert match.emission_factor > 0
    assert match.confidence >= 0.65
    assert match.match_method in ["exact", "normalized", "rapidfuzz", "embedding"]

def test_unknown_material_fallback():
    service = EmissionFactorService.get_instance()
    match = service.get_factor("Unobtanium Exotic Superalloy 9999")
    assert match is not None
    assert match.match_method == "fallback"
    assert match.confidence <= 0.50
    assert match.emission_factor == 0.0

def test_unknown_unit_handling():
    service = EmissionFactorService.get_instance()
    engine = CalculationEngine()
    # Test conversion fallback for unknown unit
    val = engine.convert_units(100, "exotic_unit", "kg")
    assert val == 100

def test_cache_hit_performance():
    service = EmissionFactorService.get_instance()
    query = "Diesel Fuel"
    
    # First query (Cache Miss)
    t1_start = time.perf_counter()
    m1 = service.get_factor(query)
    t1 = (time.perf_counter() - t1_start) * 1000

    # Second query (Cache Hit)
    t2_start = time.perf_counter()
    m2 = service.get_factor(query)
    t2 = (time.perf_counter() - t2_start) * 1000

    assert m1.emission_factor == m2.emission_factor
    assert m2.execution_time_ms < 1.0
    assert service.get_metrics()["cache_hits"] >= 1

def test_calculation_engine_integration():
    engine = CalculationEngine()
    
    # Scope 1
    s1 = engine.calculate_scope_1("diesel", 100, "liters")
    assert "co2e_kg" in s1
    assert s1["co2e_kg"] > 0
    assert "factor_used" in s1
    assert "match_method" in s1

    # Scope 2
    s2 = engine.calculate_scope_2(1000, "UK")
    assert "location_based_co2e_kg" in s2
    assert s2["location_based_co2e_kg"] > 0

    # Scope 3 Category 1
    s3_1 = engine.calculate_scope_3_category_1("steel", 5, "t")
    assert "co2e_kg" in s3_1
    assert s3_1["co2e_kg"] > 0

    # Scope 3 Category 4
    s3_4 = engine.calculate_scope_3_category_4(15.4, 250.0, "road")
    assert "co2e_kg" in s3_4
    assert s3_4["co2e_kg"] > 0

def test_metrics_tracking():
    service = EmissionFactorService.get_instance()
    metrics = service.get_metrics()
    assert metrics["total_factors_loaded"] > 0
    assert "cache_size" in metrics
    assert "cache_hit_rate_pct" in metrics
    assert "avg_lookup_time_ms" in metrics
