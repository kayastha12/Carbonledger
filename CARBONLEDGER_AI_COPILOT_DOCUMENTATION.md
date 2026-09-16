# CarbonLedger AI Copilot — Technical Architecture & Integration Guide

**System Version:** 3.0 Enterprise  
**Core Service:** `services/copilot_engine.py`  
**API Endpoints:** `/api/rag`, `/api/v1/chat`, `/api/v1/copilot/suggestions`, `/api/v1/reports/context`  
**Frontend Modules:** `frontend/src/components/AIIntelligenceTab.jsx`, `frontend/src/components/ReportsTab.jsx`  
**Target Platform:** Local Development & Render Production (`https://carbonledger-app-vxb3.onrender.com/`)  

---

## 1. Executive Overview

The **CarbonLedger AI Copilot** is a context-aware, deterministic, multilingual carbon accounting assistant. It bridges raw corporate documents (PDF invoices, purchase orders, freight manifests, utility bills) and regulatory GHG Protocol / EU CBAM compliance reports.

### Key Capabilities:
- **Automatic Multilingual Switching**: Seamlessly supports English, Hindi (Devanagari script), and natural conversational Hinglish.
- **30+ Deterministic Domain Tools**: All numerical operations ($Q \times EF$, unit normalization, tonne-km freight logistics, regional grid emissions, CBAM certificate exposure) are executed via mathematical engines rather than LLM guesswork.
- **Zero Mock / Fake Data Fallback**: Answers are strictly grounded in verified database records. When data or emission factors do not exist, the Copilot explicitly clarifies the gap.
- **Double-Counting Intelligence**: Detects and explains transaction overlaps across Invoices vs. Purchase Orders, Utility Bills vs. Regional Grid Meters, and Purchases vs. Shop-Floor Consumption.
- **Full Report & Cell Traceability**: Inspects generated compliance sheets, tables, and individual cells, mapping every cell back to its underlying activity record, emission factor, formula, and source document.
- **Dynamic Conversational Memory**: Resolves multi-turn references and pronouns (*"it"*, *"this"*, *"that"*, *"the previous calculation"*, *"iska"*, *"ye"*) with what-if scenario re-computation.

---

## 2. Core Architectural Flow

```
USER MESSAGE (English / Hindi / Hinglish)
    ↓
1. LANGUAGE DETECTOR (Auto-detects EN / HI / HINGLISH)
    ↓
2. INTENT CLASSIFIER & ENTITY EXTRACTOR (Maps 40+ intent enums; extracts material, quantity, unit, geo, PO, phase, cell)
    ↓
3. CONVERSATION CONTEXT RESOLVER (Resolves multi-turn pronouns & what-if variations)
    ↓
4. MULTI-TENANT AUTHORIZER (Enforces strict tenant isolation on user_id & upload_id)
    ↓
5. DATA SOURCE RETRIEVER (Priority: Cell → Row → Sheet → Calc → Record → Document → Factor)
    ↓
6. DETERMINISTIC TOOL EXECUTION (Math engine, factor library, freight logistics, regional grid factors)
    ↓
7. EVIDENCE & PROVENANCE BUILDER (Constructs verifiable audit payload)
    ↓
8. ADAPTIVE NATURAL ANSWER GENERATOR (Dynamic phrasing in user's detected language)
    ↓
STRUCTURED RESPONSE PAYLOAD:
{
  "answer": "...",
  "grounded": true,
  "language": "hinglish",
  "intent": "MATERIAL_EMISSION",
  "evidence": [...],
  "suggestions": [...]
}
```

---

## 3. Central Context Object (`CopilotContext`)

Every user interaction is resolved against a structured context object:

```python
class CopilotContext:
    user_id: Optional[int]
    workspace_id: str
    conversation_id: str
    upload_id: Optional[str]
    language: str  # "english" | "hindi" | "hinglish"
    previous_messages: List[Dict[str, Any]]
    current_document_id: Optional[str]
    current_document_name: Optional[str]
    current_record_id: Optional[str]
    current_report_id: Optional[str]
    current_report_name: Optional[str]
    current_sheet_name: Optional[str]
    selected_cell: Optional[Dict[str, Any]]
    selected_row: Optional[Dict[str, Any]]
    selected_column: Optional[str]
    dashboard_context: Dict[str, Any]
    active_filters: Dict[str, Any]
    simple_mode: bool
```

---

## 4. Multilingual & Natural Phrasing Engine

The copilot respects the user's natural conversational style:

### English:
- **Query:** *"How much carbon does 500 kg of steel produce?"*
- **Response:** Direct calculation trace with factor ID, source database, formula, and deterministic CO₂e result.

### Hindi (Devanagari):
- **Query:** *"मेरा कुल कार्बन फुटप्रिंट कितना है?"*
- **Response:** *"डैशबोर्ड के अनुसार आपका कुल कार्बन फुटप्रिंट 31,461.77 kg CO₂e (31.462 tonnes) है..."*

### Hinglish (Conversational Romanized Hindi):
- **Query:** *"Steel sheet ka emission kaise calculate hua?"*
- **Response:** *"500 kg Steel Sheet ka emission calculate karne ke liye quantity ko compatible factor se multiply kiya gaya hai. Formula: 500 kg × 2.861 = 1,430.79 kg CO₂e."*

---

## 5. Complete Deterministic Tool Registry (30+ Tools)

| Category | Function | Description |
| :--- | :--- | :--- |
| **Documents** | `get_documents`, `search_documents`, `get_document_details` | Retrieves upload sessions, pages, composite OCR confidence, and company identifiers (`TechManufacturing India Ltd`, `CL-TCH-001`). |
| **Materials** | `search_activity_records`, `get_material_records`, `calculate_material_emission` | Looks up materials, quantities, factors, and executes deterministic multiplication ($Q \times EF$). |
| **Vendors & POs** | `get_supplier_records`, `get_invoice_records`, `get_purchase_order_records` | Maps vendor emissions, PO numbers, and line items. |
| **Freight** | `get_transport_records`, `calculate_transport_emission` | Tonne-km freight calculations (Mumbai $\rightarrow$ Pune $\rightarrow$ Bangalore) with heavy-goods vehicle or electric truck factors. |
| **Scope 1 Fuels** | `get_fuel_records`, `calculate_fuel_emission` | Stationary diesel generator, natural gas, and boiler combustion calculations. |
| **Scope 2 Grids** | `get_electricity_records`, `calculate_electricity_emission` | Regional grid calculations (Maharashtra, Karnataka, Telangana, Germany grid factors). |
| **Factors & Units** | `get_emission_factor`, `compare_emission_factors`, `convert_unit`, `validate_unit_compatibility` | Central factor library lookup, source provenance (DEFRA, EPA, Ecoinvent, CBAM), unit conversions. |
| **Scopes** | `get_scope_breakdown`, `get_validation_issues`, `get_calculation_provenance` | Scope 1/2/3 categorization rationale and audit trail validation. |
| **Dashboard** | `get_dashboard_metrics`, `get_top_emitters` | Live KPI totals, scope distribution, and emitter rankings. |
| **Reports** | `get_report_list`, `get_report_summary`, `get_report_sheet`, `get_report_cell`, `trace_report_value` | Full multi-sheet inspector (Executive Summary, CBAM, Top Emitters, Audit Trail) and cell-level drilldown. |
| **Intelligence** | `find_possible_duplicates`, `reconcile_dashboard_and_report` | Double-counting detection (Invoice vs PO, Utility vs Grid) and dashboard-to-report reconciliation. |

---

## 6. Double-Counting Prevention Engine

When analyzing multi-phase documents (e.g. `deepseek_html_20260731_54ad15 (1).pdf` with 30 transactions across 10 phases), the Copilot identifies potential duplicate activities:
1. **Invoice vs. Purchase Order**: Highlights identical material-quantity pairs across purchase orders and payment invoices.
2. **Utility Bills vs. Grid Meters**: Identifies overlapping Scope 2 kWh electricity records between facility utility invoices and state-level grid logs.
3. **Stationary Fuel vs. Transport Freight**: Distinguishes on-site generator diesel from logistics fleet transport fuel.
4. **Purchased Materials vs. Shop-Floor Consumption**: Reconciles raw material intake with manufacturing batch logs.

---

## 7. Report Cell Inspector Specification

When a user clicks any cell in the Reports tab, the frontend dispatches a structured inspection payload:

```json
{
  "report_id": "RPT-upload_b8fb83eb-2026",
  "sheet_name": "Executive Summary",
  "cell_reference": "B12",
  "column": "total_co2e_kg",
  "display_value": "1,430.79 kg CO2e",
  "row_data": {
    "material": "Steel Sheet",
    "po_number": "PO-2025-001",
    "quantity": 500.0,
    "unit": "kg",
    "emission_factor": 2.861,
    "factor_id": "DEFRA_STEEL_2026",
    "formula": "500 kg * 2.861 kgCO2e/kg = 1430.79 kgCO2e"
  }
}
```

The Copilot instantly explains the exact provenance, formula, and source document transaction behind that cell.

---

## 8. Anti-Hallucination Policy

1. **Unknown Materials**: Refuses to estimate emissions for imaginary materials (*"Vibranium"*, *"Unobtainium"*); returns a clear explanation that an approved factor is required.
2. **Missing Historical Years**: When queried for years not in the active ledger (e.g. *2018*), explains that the active inventory reflects reporting year *2026*.
3. **Deterministic Arithmetic**: Never delegates calculations to the LLM; all arithmetic is performed by `CalculationEngine` and `CarbonCalculationService`.
