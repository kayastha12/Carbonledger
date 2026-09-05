# CarbonLedger OS — Production PDF Extraction Fix Report

## 1. Problem Summary
When uploading PDF documents (e.g. `deepseek_html_20260731_54ad15 (1).pdf`) to the production application on Render (`https://carbonledger-app-vxb3.onrender.com/`), the system returned:
> **"No Carbon Activity Data Found"**
> *"No reliable material, fuel, electricity, or logistics transaction rows were identified in this document."*

## 2. Root Cause Analysis
1. **Unpackaged External Dependencies & Missing Modules**:
   - `services/document_ai_service.py` attempted to load modules dynamically from a local development path (`D:\internship\mlmodel\carbonledger-document-ai`).
   - In cloud production environments like Render (Linux Docker/Native environment), local `D:\` filesystem paths do not exist.
   - When the import failed, `DOCUMENT_AI_AVAILABLE` was set to `False`, throwing a `RuntimeError("Document AI pipeline is not available on this server.")` which was caught by `universal_upload_service.py` and converted to an empty records list `records: []`.
2. **Missing Authoritative GHG Workbook in Git**:
   - `services/workbook_factor_engine.py` was looking for the clean Excel workbook (`CarbonLedger_GHG_Factors_2026_Clean(6).xlsx`) on `D:\internship\mlmodel\...` rather than the repository's relative `datasets/` path.

## 3. Implementation & Fixes Applied

### A. Self-Contained Repository Bundling
- **Document AI Pipeline (`pipeline/`)**:
  - Bundled all extraction engines (`table_detector.py`, `heuristic_extractor.py`, `field_mapper.py`, `entity_normalizer.py`, `cbam_mapper.py`, `carbon_mapper.py`, `fuel_extractor.py`, `electricity_extractor.py`, `shipping_extractor.py`, `transport_extractor.py`, `duplicate_detector.py`, `context_propagator.py`).
  - Bundled document classification & layout parsing (`classifier.py`, `layout.py`, `pdf_parser.py`, `document_segmentation.py`).
  - Bundled unit normalization & confidence engines (`pipeline/units/`, `pipeline/validation/`).
  - Bundled `pipeline/doc_ai_pipeline.py` helper routines for table cleaning and bounding-box provenance.
- **Taxonomies & Rules (`config/`)**:
  - Bundled `config/classification/`, `config/evaluation/`, `config/taxonomy/` (materials, fuels, energy, transportation, units, currencies, countries), and `config/validation/`.
- **Pydantic Schemas (`schemas/`)**:
  - Bundled `schemas/document.py`, `schemas/extraction.py`, `schemas/review.py`, and `schemas/validation.py`.
- **Authoritative Dataset (`datasets/`)**:
  - Bundled `datasets/CarbonLedger_GHG_Factors_2026_Clean(6).xlsx` containing 8,740 verified emission factors.

### B. Path Resolution Refactoring
- **`services/document_ai_service.py`**:
  - Converted all hardcoded `D:\` paths to dynamically resolved relative paths using `project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`.
  - Added direct import fallbacks for `pipeline.doc_ai_pipeline`.
  - Added field normalization aliases (`material`, `quantity`, `unit`, `cost`, `supplier`, `delivery_date`, `facility`) so fuel, electricity, freight, and commodity rows render directly in the UI review table.
- **`services/workbook_factor_engine.py`**:
  - Updated `_resolve_workbook_path` to load from `datasets/CarbonLedger_GHG_Factors_2026_Clean(6).xlsx` within the project root.

### C. API & Deployment
- **`api/main.py`**:
  - Added `/api/debug/doc-ai` diagnostic endpoint to verify pipeline availability and dataset existence.
  - Bumped version to `7.1` in health checks.

## 4. Verification & Extraction Results

Tested against `deepseek_html_20260731_54ad15 (1).pdf`:
- **Pages Processed**: 13
- **Tables Identified**: 12
- **Extracted Line Items**: **18 real business activity records**
- **Sample Line Items**:
  1. `Steel Sheet` — 500.0 kg (Scope 3)
  2. `Plastic Resin (PET)` — 1,200.0 kg (Scope 3)
  3. `Aluminum Bar` — 350.0 kg (Scope 3)
  4. `Freight Rail Transport` — 4,500.0 tonne.km (Scope 3 Cat 4)
  5. `Diesel Fuel` — 2,500.0 L (Scope 1)
  6. `LPG (Liquefied Petroleum Gas)` — 850.0 kg (Scope 1)
  7. `Electricity (Grid)` — 15,400.0 kWh (Scope 2)
  8. `Natural Gas` — 1,200.0 m³ (Scope 1)
- **Emissions & CBAM Calculation**:
  - Total CO2e: **1,676.11 kg CO2e (1.676 tonnes)**
  - Scope 1: **1,585.71 kg**
  - Scope 2: **0.00 kg**
  - Scope 3: **90.41 kg**
  - CBAM Cost: **€142.46**
- **Downloadable Reports Generated**:
  - `carbon_report_pdf` (Executive Summary Report)
  - `cbam_report_excel` (CBAM Declaration & Audit)
  - `inventory_excel` (Activity Inventory Records)
  - `audit_json` (Fidelity & Trace Audit Log)
  - `executive_esg_pdf` (Executive ESG Statement)

## 5. Git Repository & Cloud Deployment
All code, models, pipeline modules, configuration taxonomies, and dataset workbooks are committed and pushed to the remote repository:
- **Repository**: [https://github.com/kayastha12/Carbonledger](https://github.com/kayastha12/Carbonledger)
- **Branch**: `main`
- **Latest Commits**:
  - `4fd9d2c`: `fix(prod): bundle document ai pipeline, schemas, and factor workbook for cloud deployment`
  - `aa72586`: `feat(api): bump version to 7.1 and add doc-ai diagnostic endpoint`
