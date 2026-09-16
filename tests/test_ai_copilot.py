"""
CarbonLedger AI Copilot Comprehensive Test Suite (Version 3.0)

Testing:
- Multilingual Natural Language Understanding (English, Hindi Devanagari, Natural Hinglish)
- Real Sample Document Facts (TechManufacturing India Ltd, CL-TCH-001, Phases 1-10)
- Tonne-km Freight Route Calculations (Mumbai -> Pune -> Bangalore -> Hyderabad)
- Regional Electricity Grid Calculations (Maharashtra, Karnataka, Telangana, Germany)
- Scope 1 Fuel Combustion & Scope 2/3 Classification Rationales
- Double-Counting Detection (Invoice vs PO, Utility vs Grid)
- Dashboard to Compliance Report Reconciliation
- Cell-level Inspection & Calculation Provenance Tracing
- Multi-turn Follow-up Context & Pronoun Resolution ("it", "this", "what if", "iska")
- Strict Anti-Hallucination on Imaginary Materials & Historical Years
"""

import os
import sys
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.copilot_engine import CopilotEngine, LanguageDetector, IntentClassifier, EntityExtractor
from services.emission_factor_service import EmissionFactorService
from services.calculation_engine import CalculationEngine
from services.carbon_calculation_service import CarbonCalculationService


@pytest.fixture(scope="module")
def copilot():
    return CopilotEngine()


@pytest.fixture(scope="module")
def sample_dataset():
    """Dataset representing real calculated records in a tenant session."""
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


# =============================================================================
# PART 1: MULTILINGUAL & LANGUAGE DETECTION TESTS
# =============================================================================

def test_01_language_detection():
    assert LanguageDetector.detect("What is my total carbon footprint?") == "english"
    assert LanguageDetector.detect("How much CO2e does 500 kg of steel produce?") == "english"
    assert LanguageDetector.detect("मेरा कुल कार्बन फुटप्रिंट कितना है?") == "hindi"
    assert LanguageDetector.detect("डीजल स्कोप 1 क्यों है?") == "hindi"
    assert LanguageDetector.detect("Mera total carbon footprint kitna hai?") == "hinglish"
    assert LanguageDetector.detect("Steel ka emission kaise calculate hua?") == "hinglish"
    assert LanguageDetector.detect("Ye number kahan se aaya?") == "hinglish"
    assert LanguageDetector.detect("Diesel ko Scope 1 kyun classify kiya hai?") == "hinglish"


def test_02_hindi_devanagari_query(copilot):
    """User asks in Hindi: 'मेरा कुल कार्बन फुटप्रिंट कितना है?'."""
    resp = copilot.copilot_chat("मेरा कुल कार्बन फुटप्रिंट कितना है?")
    assert "कार्बन" in resp or "उत्सर्जन" in resp or "CO₂e" in resp
    # Should not be empty
    assert len(resp) > 20


def test_03_hinglish_material_query(copilot):
    """User asks in Hinglish: '500 kg steel sheet ka emission kitna hai?'."""
    resp = copilot.copilot_chat("500 kg steel sheet ka emission kitna hai?")
    assert "Steel" in resp or "steel" in resp
    assert "CO₂e" in resp or "kg" in resp
    assert "calculate" in resp or "factor" in resp or "emission" in resp


def test_04_hinglish_scope_query(copilot):
    """User asks in Hinglish: 'Diesel ko Scope 1 kyun classify kiya hai?'."""
    resp = copilot.copilot_chat("Diesel ko Scope 1 kyun classify kiya hai?")
    assert "Scope 1" in resp
    assert "Direct" in resp or "direct" in resp or "combustion" in resp or "दहन" in resp


# =============================================================================
# PART 2: REAL DOCUMENT EXTRACTION & MULTI-PHASE FACTS (TechManufacturing India Ltd)
# =============================================================================

def test_05_document_overview_techmanufacturing(copilot):
    """Document overview for TechManufacturing India Ltd."""
    resp = copilot.copilot_chat("What company data was extracted from my uploaded document?")
    assert "TechManufacturing India Ltd" in resp or "CL-TCH-001" in resp or "Document" in resp


def test_06_document_phase_1_materials(copilot):
    """Verify Phase 1 materials: Steel Sheet (500 kg), Plastic Resin (100 L), Aluminum Bar (250 kg)."""
    resp = copilot.copilot_chat("What is in Phase 1 of the document?")
    assert "Phase 1" in resp
    assert "Steel Sheet" in resp
    assert "Plastic Resin" in resp
    assert "Aluminum Bar" in resp


def test_07_document_phase_4_transport_routes(copilot):
    """Verify Phase 4 logistics routes: Mumbai -> Pune (180 km), Pune -> Bangalore (700 km)."""
    resp = copilot.copilot_chat("Show Phase 4 logistics freight routes")
    assert "Phase 4" in resp
    assert "Mumbai" in resp and "Pune" in resp
    assert "180 km" in resp or "700 km" in resp


def test_08_document_phase_5_utilities(copilot):
    """Verify Phase 5 utilities: Electricity (15,000 kWh), Natural Gas (500 MCM), Steam (1,000 MT)."""
    resp = copilot.copilot_chat("What utilities were extracted in Phase 5?")
    assert "Phase 5" in resp
    assert "Electricity" in resp
    assert "Natural Gas" in resp
    assert "Steam" in resp


def test_09_document_phase_9_regional_electricity(copilot):
    """Verify Phase 9 regional electricity: Maharashtra, Karnataka, Telangana."""
    resp = copilot.copilot_chat("Show Phase 9 regional electricity consumption")
    assert "Phase 9" in resp
    assert "Maharashtra" in resp
    assert "Karnataka" in resp
    assert "Telangana" in resp


def test_10_document_phase_10_finished_goods(copilot):
    """Verify Phase 10 finished goods: Steel Coils, Aluminium Sheets, Plastic Granules."""
    resp = copilot.copilot_chat("What products are listed in Phase 10?")
    assert "Phase 10" in resp
    assert "Steel Coils" in resp
    assert "Aluminium Sheets" in resp
    assert "Plastic Granules" in resp


# =============================================================================
# PART 3: TONNE-KM FREIGHT CALCULATIONS & ROUTE LOGISTICS
# =============================================================================

def test_11_transport_route_mumbai_to_pune(copilot):
    """Calculate Mumbai -> Pune: 180 km, 2 tonnes, Diesel Truck."""
    res = copilot.calculate_transport_emission(distance_km=180.0, weight_tonnes=2.0, vehicle_type="Diesel Truck")
    assert res["tonne_km"] == 360.0
    assert res["co2e_kg"] > 0.0
    assert "180.0 km" in res["formula"]


def test_12_transport_route_pune_to_bangalore(copilot):
    """Calculate Pune -> Bangalore: 700 km, 5 tonnes, Electric Truck."""
    res = copilot.calculate_transport_emission(distance_km=700.0, weight_tonnes=5.0, vehicle_type="Electric Truck")
    assert res["tonne_km"] == 3500.0
    assert res["emission_factor"] == 0.025  # Electric truck factor


# =============================================================================
# PART 4: REGIONAL ELECTRICITY GRID CALCULATIONS
# =============================================================================

def test_13_electricity_maharashtra_grid(copilot):
    """15,000 kWh on Maharashtra Grid."""
    res = copilot.calculate_electricity_emission(kwh=15000.0, region_or_state="Maharashtra")
    assert res["quantity_kwh"] == 15000.0
    assert res["co2e_kg"] == 15000.0 * 0.79


def test_14_electricity_karnataka_grid(copilot):
    """8,000 kWh on Karnataka Grid."""
    res = copilot.calculate_electricity_emission(kwh=8000.0, region_or_state="Karnataka")
    assert res["co2e_kg"] == 8000.0 * 0.68


# =============================================================================
# PART 5: DOUBLE-COUNTING INTELLIGENCE & RECONCILIATION
# =============================================================================

def test_15_double_counting_detection(copilot):
    """Check duplicate detection for duplicate transactions and utility vs grid overlap."""
    dups = copilot.find_possible_duplicates()
    assert isinstance(dups, list)
    resp = copilot.copilot_chat("Check for potential double counting in my data")
    assert "Double" in resp or "double" in resp or "Clean" in resp or "दोहराव" in resp


def test_16_dashboard_and_report_reconciliation(copilot):
    """Test reconciliation between live database calculations and compliance report totals."""
    rec = copilot.reconcile_dashboard_and_report()
    assert "database_total_co2e_kg" in rec
    assert "report_total_co2e_kg" in rec
    assert "is_reconciled" in rec
    resp = copilot.copilot_chat("Reconcile dashboard and report totals")
    assert "Reconciliation" in resp or "Total" in resp or "मिलान" in resp


# =============================================================================
# PART 6: MULTI-TURN CONVERSATION & PRONOUN RESOLUTION
# =============================================================================

def test_17_multi_turn_pronoun_resolution(copilot):
    """Test conversational pronoun resolution: 'What is steel emission?' -> 'Why?' -> 'What if 2 tonnes?'."""
    user_id = 8888
    # Turn 1
    t1 = copilot.copilot_chat("How much carbon does 500 kg of steel sheet produce?", user_id=user_id)
    assert "Steel" in t1 or "steel" in t1

    # Turn 2: 'Why?'
    t2 = copilot.copilot_chat("Why?", user_id=user_id)
    assert len(t2) > 10

    # Turn 3: 'What if it was 2 tonnes?'
    t3 = copilot.copilot_chat("What if it was 2 tonnes?", user_id=user_id)
    assert "Steel" in t3 or "steel" in t3 or "tonnes" in t3 or "2" in t3


# =============================================================================
# PART 7: DETERMINISTIC MATH & FACTOR PROVENANCE
# =============================================================================

def test_18_material_calculation_deterministic_parity(copilot):
    calc = copilot.calculate_material_emission("Steel Sheet", 500.0, "kg")
    assert calc["status"] == "Calculated"
    assert calc["co2e_kg"] > 0.0
    assert "factor_id" in calc
    assert "formula" in calc


def test_19_emission_factor_provenance(copilot):
    f_info = copilot.get_emission_factor("Steel Sheet")
    assert f_info["status"] == "found"
    assert "emission_factor" in f_info
    assert "factor_source" in f_info
    assert "confidence" in f_info


# =============================================================================
# PART 8: REPORT CELL INSPECTION & AUDIT TRACE
# =============================================================================

def test_20_report_cell_inspector(copilot, sample_dataset):
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


def test_21_report_multi_sheet_index(copilot):
    sheets = copilot.get_report_list()
    assert len(sheets) == 11
    assert "Executive Summary" in sheets
    assert "CBAM Cost Analysis" in sheets
    assert "Audit Trail" in sheets


# =============================================================================
# PART 9: ANTI-HALLUCINATION & SECURITY CHECKS
# =============================================================================

def test_22_anti_hallucination_unknown_material(copilot):
    """Refuse to fabricate emissions for imaginary materials like Vibranium."""
    resp = copilot.copilot_chat("What is the carbon emission of 500 kg of Vibranium?")
    assert any(phrase in resp.lower() for phrase in ["not currently have", "no verified", "cannot calculate", "cannot guess", "unverified", "not available"])
    assert "99999" not in resp


def test_23_anti_hallucination_historical_year(copilot):
    """Refuse to fabricate historical data for year 2018."""
    resp = copilot.copilot_chat("What was our total carbon emissions in 2018?")
    assert "2018" in resp
    assert any(phrase in resp.lower() for phrase in ["do not have", "not available", "2026", "उपलब्ध नहीं"])


def test_24_structured_chat_output_payload(copilot):
    """Verify copilot_chat_structured returns all required contract fields."""
    res_dict = copilot.copilot_chat_structured("What is my total footprint?")
    assert "answer" in res_dict
    assert "grounded" in res_dict
    assert "language" in res_dict
    assert "intent" in res_dict
    assert "evidence" in res_dict
    assert "suggestions" in res_dict
    assert len(res_dict["suggestions"]) >= 2
