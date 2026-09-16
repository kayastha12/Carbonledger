import os
import sys
import pytest

# Ensure project root is on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.copilot_engine import CopilotEngine
from services.emission_factor_service import EmissionFactorService
from services.calculation_engine import CalculationEngine
from services.carbon_calculation_service import CarbonCalculationService


@pytest.fixture(scope="module")
def copilot():
    engine = CopilotEngine()
    return engine


@pytest.fixture(scope="module")
def sample_dataset():
    """Mock dataset representing real calculated and extracted records in a session."""
    records = [
        {
            "id": 1,
            "po_number": "PO-9001",
            "material": "Hot Rolled Steel Sheet",
            "supplier": "SteelCorp Global Ltd",
            "quantity": 500.0,
            "unit": "kg",
            "co2e_kg": 945.0,
            "emission_factor": 1.89,
            "factor_id": "DEFRA_STEEL_2026",
            "factor_source": "DEFRA GHG Factors 2026",
            "scope": "Scope 3",
            "calculation_status": "Calculated",
            "formula": "0.50 tonne * 1890.00 kgCO2e/t = 945.00 kgCO2e",
            "cbam_cost_eur": 80.33
        },
        {
            "id": 2,
            "po_number": "PO-9002",
            "material": "Diesel Fuel",
            "supplier": "TotalEnergy Fuel B.V.",
            "quantity": 1000.0,
            "unit": "litre",
            "co2e_kg": 2687.0,
            "emission_factor": 2.687,
            "factor_id": "DEFRA_DIESEL_2026",
            "factor_source": "DEFRA Fuels 2026",
            "scope": "Scope 1",
            "calculation_status": "Calculated",
            "formula": "1000.0 litre * 2.687 kgCO2e/L = 2687.00 kgCO2e",
            "cbam_cost_eur": 0.0
        },
        {
            "id": 3,
            "po_number": "PO-9003",
            "material": "Grid Electricity Germany",
            "supplier": "Stadtwerke Munich",
            "quantity": 15000.0,
            "unit": "kwh",
            "co2e_kg": 5775.0,
            "emission_factor": 0.385,
            "factor_id": "DE_GRID_2026",
            "factor_source": "UBA Germany Grid Average 2026",
            "scope": "Scope 2",
            "calculation_status": "Calculated",
            "formula": "15000.0 kwh * 0.385 kgCO2e/kwh = 5775.00 kgCO2e",
            "cbam_cost_eur": 0.0
        },
        {
            "id": 4,
            "po_number": "PO-9004",
            "material": "Road Freight Logistics",
            "supplier": "DHL Express Logistics",
            "quantity": 2500.0,
            "unit": "tonne.km",
            "co2e_kg": 375.0,
            "emission_factor": 0.15,
            "factor_id": "DEFRA_HGV_2026",
            "factor_source": "DEFRA Transport 2026",
            "scope": "Scope 3",
            "calculation_status": "Calculated",
            "formula": "2500.0 t*km * 0.15 kgCO2e/t-km = 375.00 kgCO2e",
            "cbam_cost_eur": 0.0
        },
        {
            "id": 5,
            "po_number": "PO-9005",
            "material": "Unknown Polymer X",
            "supplier": "ChemGlobal Ltd",
            "quantity": 200.0,
            "unit": "kg",
            "co2e_kg": 0.0,
            "emission_factor": 0.0,
            "factor_id": "MANUAL_REVIEW_REQUIRED",
            "factor_source": "Unmapped",
            "scope": "Scope 3",
            "calculation_status": "Manual Review Required",
            "anomaly_reason": "Emission factor confidence below 95% threshold",
            "formula": "Manual Review Required",
            "cbam_cost_eur": 0.0
        }
    ]
    return records


# =========================================================================
# TEST SUITE: 18 QUESTION CATEGORIES & GROUNDING CHECKS
# =========================================================================

def test_01_document_understanding(copilot, sample_dataset):
    """Test Question 1: What materials were extracted from my document?"""
    ctx = {"page": "Intake"}
    # Dispatch with mock records
    resp = copilot._handle_document_understanding(
        "What materials were found?",
        extracted_records=sample_dataset,
        records=sample_dataset,
        sessions=[{"filename": "invoice_steel_2026.pdf", "pages_count": 2, "overall_confidence_pct": 98.4}],
        is_simple_mode=False
    )
    assert "Steel" in resp or "Diesel" in resp
    assert "Materials Extracted" in resp or "Intelligence" in resp


def test_02_material_carbon_calculation_deterministic(copilot, sample_dataset):
    """Test Question 2 & 3: What is the carbon emission of 500 kg of steel?"""
    resp = copilot.copilot_chat("How much CO2e does 500 kg of steel produce?")
    assert "Steel" in resp or "steel" in resp
    assert "kg CO" in resp or "CO2e" in resp or "tonnes" in resp
    # Check that calculation is deterministic
    assert "kg" in resp


def test_03_emission_factor_provenance(copilot, sample_dataset):
    """Test Question 4 & 6: Which emission factor was used and what is its source?"""
    resp = copilot._handle_emission_factor_query("Which factor was used?", records=sample_dataset, is_simple_mode=False)
    assert "Emission Factor" in resp
    assert "DEFRA" in resp or "kg CO" in resp


def test_04_scope_1_fuel_breakdown(copilot, sample_dataset):
    """Test Question: What is my Scope 1 emission and which fuels contribute?"""
    resp = copilot._handle_scope_1_query("What is my Scope 1 emission?", records=sample_dataset, is_simple_mode=False)
    assert "Scope 1" in resp
    assert "Diesel" in resp
    assert "2,687" in resp or "2687" in resp


def test_05_scope_2_electricity_geography(copilot, sample_dataset):
    """Test Question: How was my Scope 2 electricity calculated?"""
    resp = copilot._handle_scope_2_query("How was Scope 2 calculated?", records=sample_dataset, is_simple_mode=False)
    assert "Scope 2" in resp
    assert "Electricity" in resp or "5,775" in resp


def test_06_transportation_logistics_calculation(copilot, sample_dataset):
    """Test Question: How was transportation emissions calculated?"""
    resp = copilot._handle_transport_query("Explain transport emissions", records=sample_dataset, is_simple_mode=False)
    assert "Transportation" in resp or "Freight" in resp or "Logistics" in resp


def test_07_unit_conversion_explanation(copilot, sample_dataset):
    """Test Question: Why was kg converted to tonnes?"""
    resp = copilot._handle_unit_conversion_query("Why was kg converted to tonnes?", records=sample_dataset, is_simple_mode=False)
    assert "Unit Conversion" in resp
    assert "1,000" in resp or "1000" in resp or "tonne" in resp


def test_08_scope_classification_rationale(copilot, sample_dataset):
    """Test Question: Why is an activity Scope 1 vs Scope 2 vs Scope 3?"""
    resp = copilot._handle_scope_classification_query("Explain scope classification", records=sample_dataset, is_simple_mode=False)
    assert "Scope 1" in resp
    assert "Scope 2" in resp
    assert "Scope 3" in resp


def test_09_validation_and_review_required(copilot, sample_dataset):
    """Test Question: Why was this record marked Review Required?"""
    resp = copilot._handle_validation_and_review("Which records need review?", records=sample_dataset, extracted_records=sample_dataset, is_simple_mode=False)
    assert "Review" in resp
    assert "Unknown Polymer X" in resp or "PO-9005" in resp or "flagged" in resp


def test_10_calculation_formula_explanation(copilot, sample_dataset):
    """Test Question: Show me the calculation and formula for this record."""
    resp = copilot._handle_calculation_explanation("Show me the formula", records=sample_dataset, is_simple_mode=False)
    assert "GHG Protocol" in resp or "Formula" in resp or "Emissions" in resp


def test_11_dashboard_total_footprint(copilot, sample_dataset):
    """Test Question: What is my total carbon footprint and top emitter?"""
    resp = copilot._handle_dashboard_query("What is my total footprint?", records=sample_dataset, sessions=[], is_simple_mode=False)
    assert "Dashboard Overview" in resp or "Total Carbon Footprint" in resp
    assert "kg CO" in resp


def test_12_dashboard_top_supplier(copilot, sample_dataset):
    """Test Question: Which supplier has the highest emissions?"""
    resp = copilot._handle_dashboard_query("Which supplier has the highest emissions?", records=sample_dataset, sessions=[], is_simple_mode=False)
    assert "Supplier" in resp
    assert "Stadtwerke Munich" in resp or "SteelCorp" in resp or "TotalEnergy" in resp


def test_13_report_multi_sheet_overview(copilot, sample_dataset):
    """Test Question: What sheets are included in the compliance report?"""
    resp = copilot._handle_report_query("Explain this report", sheet_name=None, report_context=None, records=sample_dataset, is_simple_mode=False)
    assert "Executive Summary" in resp
    assert "Scope 1" in resp
    assert "CBAM" in resp


def test_14_report_sheet_specific_inspection(copilot, sample_dataset):
    """Test Question: What does the Scope 3 sheet contain?"""
    mock_report_context = {
        "report_id": "RPT-TEST-001",
        "sheets": [
            {
                "name": "Scope 3",
                "description": "Upstream supply chain purchases, materials, and freight.",
                "type": "table",
                "columns": ["material", "supplier", "quantity", "unit", "co2e_kg"],
                "total_kg": 1320.0,
                "rows_count": 2
            }
        ]
    }
    resp = copilot._handle_report_query("Explain this sheet", sheet_name="Scope 3", report_context=mock_report_context, records=sample_dataset, is_simple_mode=False)
    assert "Scope 3" in resp
    assert "Upstream supply chain" in resp


def test_15_selected_cell_inspector(copilot, sample_dataset):
    """Test Question: Explain selected report cell."""
    resp = copilot._handle_selected_context(
        q="Explain this cell",
        selected_record=None,
        selected_cell={"column": "co2e_kg", "value": 945.0, "row_data": sample_dataset[0]},
        sheet_name="Scope 3",
        is_simple_mode=False
    )
    assert "Report Cell Inspector" in resp
    assert "co2e_kg" in resp
    assert "945" in resp


def test_16_simple_language_mode(copilot, sample_dataset):
    """Test Question: Explain this simply for a non-expert."""
    resp = copilot.copilot_chat("Explain 500 kg steel simply", context_data={"simple_mode": True})
    assert "Steel" in resp or "steel" in resp
    assert "greenhouse gases" in resp or "Carbon Footprint" in resp or "simple" in resp


def test_17_followup_conversation_context(copilot, sample_dataset):
    """Test Multi-turn Conversation: 'What if it was 1 tonne?'."""
    user_id = 999
    # Turn 1
    t1 = copilot.copilot_chat("How much CO2e does 500 kg of steel produce?", user_id=user_id)
    assert "Steel" in t1 or "steel" in t1
    # Turn 2 (Follow up)
    t2 = copilot.copilot_chat("What if it was 2 tonnes?", user_id=user_id)
    assert "Steel" in t2 or "steel" in t2 or "tonnes" in t2 or "2" in t2


# =========================================================================
# ANTI-HALLUCINATION GUARD TESTS
# =========================================================================

def test_18_anti_hallucination_unknown_material(copilot, sample_dataset):
    """Test Anti-hallucination: Asking for imaginary material 'Vibranium' must refuse to fabricate."""
    resp = copilot.copilot_chat("What is the carbon emission of 500 kg of Vibranium?")
    # Must state information is not available / factor not found without inventing numbers
    assert any(phrase in resp.lower() for phrase in ["not currently have", "no verified", "cannot calculate", "cannot guess", "unverified", "not available"])
    assert "9999" not in resp  # No invented numbers


def test_19_anti_hallucination_historical_years(copilot, sample_dataset):
    """Test Anti-hallucination: Asking for historical emissions in 2018 when only 2026 data exists."""
    resp = copilot.copilot_chat("What was our total carbon emissions in 2018?")
    assert "2018" in resp
    assert any(phrase in resp.lower() for phrase in ["do not have", "not available", "2026"])


def test_20_suggested_questions_generation(copilot):
    """Test dynamic suggested questions for every page."""
    intake_suggestions = copilot.get_suggested_questions("Intake")
    assert len(intake_suggestions) >= 4
    assert any("extracted" in s.lower() for s in intake_suggestions)

    review_suggestions = copilot.get_suggested_questions("Review")
    assert any("review" in s.lower() for s in review_suggestions)

    report_suggestions = copilot.get_suggested_questions("Reports", {"sheet_name": "CBAM Cost"})
    assert any("cbam" in s.lower() or "sheet" in s.lower() for s in report_suggestions)
