# CarbonLedger — Live Presentation & Demo Script

> **Purpose:** Step-by-step walkthrough script for live client demonstrations, investor pitches, technical interviews, and stakeholder audits.  
> **Source Fidelity:** Built strictly from verified repository UI components, endpoints, and test fixtures.

---

## Demo Preparation Checklist
- [ ] Backend running: `http://localhost:8000` (or production: `https://carbonledger-app-vxb3.onrender.com`)
- [ ] Frontend running: `http://localhost:5173` (or production static site)
- [ ] Sample Test PDF ready: `tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf`
- [ ] Browser window opened to the CarbonLedger Dashboard.

---

## Step 1: Initial Dashboard & Zero-Baseline Gating

### What the Presenter Does
1. Navigate to the **Dashboard** tab (`http://localhost:5173`).
2. Show the clean executive KPI cards:
   - **Total Carbon Footprint:** `0.00 kg CO2e` (or clean baseline)
   - **Scope 1 (Direct):** `0.00 kg CO2e`
   - **Scope 2 (Electricity):** `0.00 kg CO2e`
   - **Scope 3 (Value Chain):** `0.00 kg CO2e`
   - **Status Banner:** *"Document Uploaded — Awaiting Approval & Calculation"* (or prompt to upload).

### What to Explain to the Audience
> "Notice that the CarbonLedger dashboard enforces strict zero-baseline data integrity. Unlike systems that populate mock numbers or prematurely guess footprint values before human review, CarbonLedger guarantees that no unverified or phantom emissions ever reach corporate ESG reports."

### Technical Details (Behind the Scenes)
- **Frontend Component:** `frontend/src/components/DashboardTab.jsx`
- **Backend API:** `GET /api/v1/dashboard/summary`
- **Database Table:** Queries `calculation_results` in SQLite. When zero approved records exist, it returns exact zero metrics.

---

## Step 2: Uploading a Commercial PDF Invoice

### What the Presenter Does
1. Click on the **Upload & Review** tab in the main navigation.
2. Drag and drop (or browse and select) the test file:  
   `tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf`.
3. Observe the loading progress indicator during extraction.

### What to Explain to the Audience
> "We are now uploading a real, 50-line commercial manufacturing invoice containing diverse raw materials (hot rolled steel, aluminum extrusions, polymers) and freight transport. 
> 
> In less than 2 seconds, our asynchronous backend pipeline parses the PDF layout, extracts table grids, identifies units, and links bounding-box coordinates for each line item."

### Technical Details (Behind the Scenes)
- **Frontend Component:** `frontend/src/components/UploadReviewTab.jsx`
- **Backend Endpoint:** `POST /api/v1/extract` (multipart/form-data)
- **Engine:** `services/document_ai_service.py` using `pdfplumber` for memory-efficient layout analysis and `pytesseract` for OCR fallback if needed.
- **Database Write:** Generates a new `session_id` in `upload_sessions` and saves raw extracted rows to `extracted_records`.

---

## Step 3: Human-in-the-Loop Review & Factor Matching

### What the Presenter Does
1. Review the generated **Line Items Review & Audit Parity Grid**:
   - Total Extracted Records: **51 records** (50 materials + 1 freight transport).
   - Show the columns: `Line #`, `Raw Description`, `Normalized Material`, `Extracted Qty`, `Unit`, `Confidence`, `Matched Factor`, `Status`.
2. Highlight the confidence badges (e.g. `98% Confidence`, `Ready to Calculate`).
3. Show how a compliance officer can edit an item or verify the matched factor.

### What to Explain to the Audience
> "Here is our Human-in-the-Loop validation table. The system has automatically normalized units—converting tonnes to kilograms and gallons to litres—and matched each item against our database of 8,740 authoritative 2026 GHG factors. 
> 
> Notice that the compliance officer retains full audit control. Items with lower confidence can be inspected or edited before calculation."

### Technical Details (Behind the Scenes)
- **Factor Engine:** `services/workbook_factor_engine.py` indexing `datasets/CarbonLedger_GHG_Factors_2026_Clean(6).xlsx`.
- **Normalization:** `services/document_ai_service.py` converting raw inputs into ISO metric standards.
- **Audit Provenance:** Bounding box coordinates saved for every extracted token.

---

## Step 4: Calculation Execution

### What the Presenter Does
1. Click the primary action button: **"Approve & Calculate Carbon Footprint"**.
2. Watch the confirmation notification confirm successful computation.

### What to Explain to the Audience
> "Upon clicking calculate, the system executes deterministic GHG Protocol formulas across all 51 line items, partitions direct vs. indirect emissions, and writes the immutable calculation records to our database."

### Technical Details (Behind the Scenes)
- **Backend Endpoint:** `POST /api/v1/calculate` with `{ session_id: "..." }`
- **Calculation Service:** `services/carbon_calculation_service.py`
- **Database Write:** Inserts 51 records into `calculation_results` and updates `upload_sessions` status to `calculated`.

---

## Step 5: Executive Dashboard & Scope Breakdown

### What the Presenter Does
1. Click back to the **Dashboard** tab.
2. Present the live updated metrics:
   - **Total Carbon Footprint:** **`40,717.46 kg CO2e`** (`40.72 Tonnes CO2e`)
   - **Scope 1:** `0.00 kg CO2e`
   - **Scope 2:** `0.00 kg CO2e`
   - **Scope 3:** `40,717.46 kg CO2e` (Purchased Goods & Freight)
   - **Documents Processed:** `1`
   - **Extracted Line Items:** `51`
   - **Calculation Status:** `COMPLETED`

### What to Explain to the Audience
> "The dashboard is now populated dynamically with the verified footprint. In this manufacturing invoice, all emissions fall under Scope 3 Category 1 (Purchased Goods) and Category 4 (Upstream Freight), giving sustainability managers an instant breakdown of their supply chain impact."

### Technical Details (Behind the Scenes)
- **Backend Endpoint:** `GET /api/v1/dashboard/summary`
- **Verification Rule:** The total footprint ($40,717.46\ kg\ CO_2e$) is the exact mathematical sum of all 51 row calculations in `calculation_results`.

---

## Step 6: Multi-Format Audit Download (CSV & Excel)

### What the Presenter Does
1. Click on the **Download Audit Ledger** button (or navigate to **Reports & Analytics**).
2. Download both the **CSV Export** and the **Excel (.xlsx) Workbook**.
3. Open the downloaded CSV/Excel file and show the 25 comprehensive audit columns:
   - `Calculation ID`, `Invoice Name`, `Raw Material`, `Normalized Unit`, `Emission Factor Code`, `Factor Source`, `Scope`, `Calculated CO2e (kg)`, `Confidence Score`.

### What to Explain to the Audience
> "For regulatory assurance and external audits (such as KPMG, PwC, or EU CBAM verifiers), CarbonLedger provides a complete 25-column audit ledger. Every single kilogram of CO2e can be traced back to the specific invoice row, bounding box, and emission factor source."

### Technical Details (Behind the Scenes)
- **Backend Endpoints:**
  - `GET /api/calculations/download?session_id=...&format=csv`
  - `GET /api/calculations/download?session_id=...&format=xlsx`
- **Data Source:** Streams directly from `calculation_results` and `upload_sessions`.

---

## Step 7: AI Copilot Natural Language Query

### What the Presenter Does
1. Open the **AI Copilot** tab.
2. Ask: *"What are the top 3 highest emission materials in the uploaded invoice?"*
3. Review the Copilot's response showing exact material names, quantities, and calculated $kg\ CO_2e$.

### What to Explain to the Audience
> "Our AI Copilot uses Retrieval-Augmented Generation (RAG) backed by ChromaDB. Instead of hallucinating numbers, it retrieves the actual calculation results from our database and answers natural-language inquiries with verifiable figures."

### Technical Details (Behind the Scenes)
- **Component:** `frontend/src/components/AICopilotTab.jsx`
- **Backend Endpoint:** `POST /api/v1/copilot/chat`
- **Vector DB:** ChromaDB with `sentence-transformers/all-MiniLM-L6-v2` dense embeddings.

---

## Step 8: Demo Conclusion & Summary

### Presenter Wrap-Up Statement
> "In summary, CarbonLedger transforms complex, unstructured procurement PDFs into compliant, auditable, and actionable carbon intelligence in seconds. It combines high-speed PDF extraction, 8,740 authoritative 2026 GHG factors, strict human-in-the-loop validation, and full audit parity across dashboards and reports."
