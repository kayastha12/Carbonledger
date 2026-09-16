# CarbonLedger AI Copilot — Comprehensive Architectural Audit & Upgrade Plan

**Document Version:** 2.0  
**Target System:** CarbonLedger Production (Render: `https://carbonledger-app-vxb3.onrender.com/`) & Local Core Engine  
**Author:** DeepMind / Antigravity AI Engineering  
**Date:** September 2026  

---

## 1. Executive Summary

A comprehensive audit of the CarbonLedger AI system (`services/copilot_engine.py`, `services/rag_service.py`, `services/report_generator_service.py`, `api/main.py`, and frontend components `AIIntelligenceTab.jsx`, `ReportsTab.jsx`) was conducted. 

While the existing system established foundational deterministic arithmetic and database connectivity, it suffers from several core architectural limitations:
1. **Keyword-Based Query Dispatch**: Relies primarily on English keyword substrings (e.g. `if "steel" in q_low:`), failing when queries are posed in Hindi, Hinglish, or natural variations (e.g., *"steel ka emission kitna hai"*, *"mera footprint batao"*, *"diesel Scope 1 kyun hai"*).
2. **Monolithic Response Templates**: Outputs repetitive markdown cards with fixed headers instead of dynamically adapting the explanation style based on intent (direct answer, calculation trace, conceptual explanation, comparison table, or troubleshooting).
3. **Absence of Structured Intent & Entity Detectors**: Does not formally parse user intents into structured types (`MATERIAL_LOOKUP`, `TRANSPORT_EMISSION`, `REPORT_CELL`, `DOUBLE_COUNTING_CHECK`, etc.) or extract composite entities (material, quantity, unit, geography, phase, supplier, PO).
4. **Missing Double-Counting Intelligence**: Fails to automatically recognize and explain overlaps across multiple business representations in uploaded documents (e.g., Invoices vs. Purchase Orders vs. Material Consumption, or Utility Electricity vs. Regional Grid Electricity).
5. **Lack of a Complete Deterministic Tool Registry**: Only 2 base tools (`lookup_emission_factor`, `calculate_emission`) were exposed, lacking dedicated tools for document search, invoice/PO lookups, logistics route calculations (e.g. Mumbai $\rightarrow$ Pune $\rightarrow$ Bangalore), regional electricity grid emissions (Maharashtra / Karnataka / Telangana), and dashboard-to-report reconciliation.
6. **No Native Multilingual Generation**: Lacks automatic language detection for English, Hindi (Devanagari), and natural conversational Hinglish.

---

## 2. Current Architecture & AI Flow

### Current Flow:
```
User Message → copilot_chat(query, user_id, context_data)
      ↓
English Keyword Checks (_dispatch_query with 'if "material" in q_low:')
      ↓
Hardcoded Branch Selection (e.g., _handle_dashboard_query, _handle_scope_1_query)
      ↓
Basic DB Aggregation (SUM co2e_kg from calculation_results)
      ↓
Static Markdown Card Assembly (Fixed template with rigid headers)
```

### Current Data Sources:
- SQLite Tables: `calculation_results`, `extracted_records`, `upload_sessions`, `reports`.
- Factor Service: `EmissionFactorService` with 8,740 master GHG factors (`master_factors_cleaned.csv`).
- Calculation Engine: `CarbonCalculationService` + `CalculationEngine`.
- Report Context: `ReportGeneratorService.get_report_context(upload_id)`.

---

## 3. Detailed Flaws & Gaps Identified

### A. Repetitive & Rigid Answer Behavior
- Every response for a material lookup or calculation uses an identical card structure (`### Calculation & Data Provenance`, `- Material / Activity`, `- Matched Emission Factor`, etc.).
- Follow-up questions like *"Why?"*, *"Explain it simply"*, or *"Show calculation"* do not smoothly adjust tone or depth; instead, they trigger static fallbacks.
- Asking the same factual question twice yielded verbatim identical strings rather than flexible, natural phrasing around deterministic facts.

### B. Language Blindness (English-Only Substring Checks)
- Queries in Hindi (*"मेरा कुल कार्बन फुटप्रिंट कितना है?"*, *"डीजल स्कोप 1 क्यों है?"*) or Hinglish (*"Steel ka emission kaise calculate hua?"*, *"Ye number kahan se aaya?"*) fail keyword filters and fall back to the generic error message.
- Over-formal translations were risking robotic Hindi phrasing (e.g., *"इस्पात पत्रक के उत्सर्जन की गणना हेतु..."*) instead of clean, natural conversational Hinglish (*"500 kg Steel Sheet ka emission calculate karne ke liye..."*).

### C. Missing Context & Entity Disambiguation
- Pronouns (*"it"*, *"this"*, *"that"*, *"the previous calculation"*, *"the supplier"*) are only partially handled in simple numeric what-if queries, but fail for entity switches or cross-sheet report references.
- Document phase references (e.g. *"Phase 4 logistics"*, *"Phase 9 electricity in Maharashtra"*, *"TechManufacturing India Ltd"*) were not mapped to structured document queries.

### D. Missing Double-Counting & Reconciliation Logic
- Uploaded enterprise documents (such as `deepseek_html_20260731_54ad15 (1).pdf` containing 30 transactions across 10 phases) contain multiple accounting views:
  - Invoices & POs for the same material.
  - Material purchases vs. Material shop-floor consumption.
  - Utility company bills vs. Grid power meter readings.
- The previous copilot simply summed all rows, failing to explain potential double counting to the user.

### E. Security & Multi-Tenant Authorization
- Context data passed from the frontend (such as `selected_record` or `selected_cell`) must be verified server-side against the authenticated `user_id` and active `upload_id` to prevent cross-tenant data leakage.

---

## 4. Upgraded Architecture Specification

```
USER MESSAGE (English / Hindi / Hinglish)
    ↓
1. LANGUAGE DETECTOR (Auto-detects EN / HI / HINGLISH)
    ↓
2. INTENT CLASSIFIER & ENTITY EXTRACTOR (Extracts Material, Qty, Unit, Geo, PO, Supplier, Phase, Sheet, Cell)
    ↓
3. CONVERSATION CONTEXT RESOLVER (Resolves 'it', 'this', 'previous calculation', 'same supplier', user/workspace session)
    ↓
4. USER & WORKSPACE AUTHORIZER (Enforces strict tenant isolation on user_id & upload_id)
    ↓
5. DATA SOURCE SELECTOR & RETRIEVAL ENGINE (Priority: Cell → Row → Sheet → Calc → Record → Document → Factors)
    ↓
6. DETERMINISTIC TOOLS SUITE (30+ domain tools for math, factors, freight routes, grids, reports, double-counting)
    ↓
7. EVIDENCE & PROVENANCE BUILDER (Constructs verifiable citation metadata: doc, page, PO, factor_id, formula)
    ↓
8. ADAPTIVE NATURAL ANSWER GENERATOR (Dynamic phrasing in user's detected language; zero mental arithmetic hallucination)
    ↓
9. GROUNDED ANSWER VALIDATOR (Ensures every fact and number matches deterministic tool output)
    ↓
STRUCTURED OUTPUT PAYLOAD:
{
  "answer": "...",
  "grounded": true,
  "language": "hinglish|hindi|english",
  "intent": "MATERIAL_EMISSION",
  "evidence": [ ... ],
  "suggestions": [ ... ]
}
```

---

## 5. Tool Suite Inventory (30+ Deterministic Tools)

| Tool Category | Tool Name | Function |
| :--- | :--- | :--- |
| **Documents** | `get_documents`, `search_documents`, `get_document_details` | Retrieves uploaded file metadata, pages, OCR confidence, and company info (e.g. TechManufacturing India Ltd). |
| **Activities & Materials** | `search_activity_records`, `get_material_records`, `calculate_material_emission` | Looks up materials, quantities, factors, and executes deterministic multiplication ($Q \times EF$). |
| **Suppliers & Invoices** | `get_supplier_records`, `get_invoice_records`, `get_purchase_order_records` | Maps vendor emissions, PO numbers, and line items. |
| **Logistics & Fuels** | `get_transport_records`, `calculate_transport_emission`, `get_fuel_records`, `calculate_fuel_emission` | Tonne-km freight calculations (Mumbai $\rightarrow$ Pune $\rightarrow$ Bangalore) and Scope 1 fuel combustion. |
| **Electricity & Utilities** | `get_electricity_records`, `calculate_electricity_emission`, `get_utility_records`, `get_facility_records` | Regional grid emissions (Maharashtra, Karnataka, Telangana, Germany DE). |
| **Emission Factors & Units** | `get_emission_factor`, `compare_emission_factors`, `convert_unit`, `validate_unit_compatibility` | Central factor library lookup, source provenance (DEFRA, EPA, Ecoinvent, CBAM), unit conversions. |
| **Scopes & Governance** | `get_scope_breakdown`, `get_validation_issues`, `get_calculation_provenance` | Scope 1/2/3 categorization rationale and audit trail validation. |
| **Dashboard & Trends** | `get_dashboard_metrics`, `get_dashboard_trends`, `get_top_emitters` | Live KPI totals, scope share, and emitter rankings. |
| **Reports & Cells** | `get_report_list`, `get_report_summary`, `get_report_sheet`, `get_report_rows`, `get_report_cell`, `trace_report_value` | Full multi-sheet inspector (Executive Summary, CBAM, Top Emitters, Audit Trail) and cell-level drilldown. |
| **Intelligence & Audit** | `find_possible_duplicates`, `reconcile_dashboard_and_report` | Double-counting detection (Invoice vs PO, Utility vs Grid) and reconciliation explanations. |

---

## 6. Implementation Action Plan

1. **Implement Core AI Engine (`services/copilot_engine.py`)**:
   - Language Detector (`detect_language` for EN, HI, Hinglish).
   - Intent Classifier (`classify_intent` across 40+ intent enums).
   - Entity Extractor (`extract_entities` supporting Hindi & Hinglish transliterations).
   - Context Memory & Pronoun Resolver (`resolve_context`).
   - Implement all 30+ deterministic tools.
   - Build dynamic, non-repetitive response synthesizers in English, Hindi, and natural Hinglish.
   - Attach structured evidence and dynamic follow-up suggestions.
2. **Expose API Endpoints (`api/main.py`)**:
   - Ensure `/api/rag`, `/api/v1/chat`, and `/api/v1/copilot/suggestions` return structured JSON payloads with language, groundedness, evidence, and suggestions.
3. **Frontend Copilot UI Enhancement (`frontend/src/components/AIIntelligenceTab.jsx`)**:
   - Render structured evidence badges, dynamic follow-up chips, copy-to-clipboard, retry, and clean table formatting.
4. **Comprehensive Automated Test Suite (`tests/test_ai_copilot.py`)**:
   - Expand to $\ge 40$ test cases covering English, Hindi, Hinglish, follow-ups, pronoun resolution, document phases (TechManufacturing India Ltd), logistics routes, double-counting detection, report cell inspection, and anti-hallucination.
5. **Documentation**:
   - Update `CARBONLEDGER_AI_COPILOT_DOCUMENTATION.md` and create `CARBONLEDGER_AI_TESTING_GUIDE.md` ($\ge 50$ test prompts).
