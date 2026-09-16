# CarbonLedger AI Copilot — Comprehensive Testing & Validation Guide

**Version:** 3.0 Enterprise  
**Coverage:** 50+ Verified Test Cases across 14 Domain Categories  
**Languages:** English, Hindi (Devanagari), Natural Hinglish  

---

## Category 1: Multilingual Language Understanding & Natural Phrasing

| # | Question / Prompt | Expected Language | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 1 | `What is my total carbon footprint?` | English | Returns total enterprise footprint in kg and metric tonnes CO₂e with Scope 1/2/3 breakdown. |
| 2 | `मेरा कुल कार्बन फुटप्रिंट कितना है?` | Hindi | Returns total carbon footprint in Devanagari Hindi with accurate numerical values. |
| 3 | `Mera total carbon footprint kitna hai?` | Hinglish | Returns conversational Hinglish summary with total footprint and leading emitter. |
| 4 | `500 kg Steel Sheet ka carbon kitna hai?` | Hinglish | Multiplies 500 kg by verified steel factor; shows step-by-step formula. |
| 5 | `डीजल को स्कोप 1 में क्यों वर्गीकृत किया गया है?` | Hindi | Explains Scope 1 direct combustion definition in Hindi. |
| 6 | `Diesel ko Scope 1 kyun classify kiya hai?` | Hinglish | Explains company-owned direct combustion rationale in natural Hinglish. |
| 7 | `Ye value kahan se aayi?` | Hinglish | Explains source document extraction and factor matching trace. |
| 8 | `Iska calculation formula dikhao.` | Hinglish | Shows exact multiplication formula ($Q \times EF = \text{CO}_2\text{e}$). |

---

## Category 2: Document Extraction & Multi-Phase Understanding (`TechManufacturing India Ltd`)

| # | Question / Prompt | Target Domain | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 9 | `What company data was extracted from my uploaded document?` | Document Overview | Identifies `TechManufacturing India Ltd`, ID `CL-TCH-001`, reporting year 2025-2026. |
| 10 | `What is in Phase 1 of the document?` | Phase 1 Intake | Extracts Steel Sheet (500 kg), Plastic Resin (100 L), and Aluminum Bar (250 kg). |
| 11 | `Show Phase 4 logistics freight routes` | Phase 4 Transport | Shows Mumbai $\rightarrow$ Pune (180 km Diesel), Pune $\rightarrow$ Bangalore (700 km Electric), Bangalore $\rightarrow$ Hyderabad (575 km Diesel). |
| 12 | `What utilities were extracted in Phase 5?` | Phase 5 Utilities | Identifies Electricity (15,000 kWh), Natural Gas (500 MCM), and Steam (1,000 MT). |
| 13 | `What materials are in Phase 7?` | Phase 7 Materials | Identifies Steel (200 kg), Aluminium (150 kg), and Plastic (50 L). |
| 14 | `What fuel records are in Phase 8?` | Phase 8 Fuels | Identifies Diesel (500 L), Natural Gas (200 MCM), and LPG (100 kg). |
| 15 | `Show Phase 9 regional electricity consumption` | Phase 9 Grids | Identifies Maharashtra (15,000 kWh), Karnataka (8,000 kWh), Telangana (5,000 kWh). |
| 16 | `What products are listed in Phase 10?` | Phase 10 Finished Goods | Identifies Steel Coils, Aluminium Sheets, and Plastic Granules. |

---

## Category 3: Deterministic Calculations & Material Provenance

| # | Question / Prompt | Target Material | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 17 | `How much CO2e does 500 kg of steel sheet produce?` | Steel Sheet | Calculates $500 \times EF$, shows factor ID and database source. |
| 18 | `Calculate carbon footprint for 250 kg of Aluminum Bar` | Aluminum Bar | Returns deterministic CO₂e with cradle-to-gate factor provenance. |
| 19 | `Calculate emissions for 100 L of Plastic Resin` | Plastic Resin | Normalizes volume units and applies verified resin factor. |
| 20 | `Show calculation trace for 1000 kg Copper Wire` | Copper Wire | Shows exact formula and verified DEFRA factor. |

---

## Category 4: Transportation & Freight Tonne-Km Logistics

| # | Question / Prompt | Route / Mode | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 21 | `Calculate transport emission for Mumbai to Pune truck route` | Mumbai $\rightarrow$ Pune | $180\text{ km} \times 2\text{ tonnes} \times 0.089\text{ kg CO}_2\text{e/t-km} = 32.04\text{ kg CO}_2\text{e}$. |
| 22 | `Calculate Pune to Bangalore electric truck logistics` | Pune $\rightarrow$ Bangalore | $700\text{ km} \times 5\text{ tonnes} \times 0.025\text{ kg CO}_2\text{e/t-km} = 87.50\text{ kg CO}_2\text{e}$. |
| 23 | `Calculate Bangalore to Hyderabad diesel freight shipment` | Bangalore $\rightarrow$ Hyderabad | $575\text{ km} \times 3.5\text{ tonnes} \times 0.089\text{ kg CO}_2\text{e/t-km} = 179.11\text{ kg CO}_2\text{e}$. |
| 24 | `Compare diesel truck vs electric truck emissions` | Comparative Freight | Explains ~70% lower emissions per tonne-km for electric freight. |

---

## Category 5: Electricity & Regional Grids (Scope 2)

| # | Question / Prompt | Regional Grid | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 25 | `Calculate Scope 2 emissions for 15,000 kWh in Maharashtra` | Maharashtra Grid | $15,000\text{ kWh} \times 0.79\text{ kg/kWh} = 11,850.00\text{ kg CO}_2\text{e}$. |
| 26 | `Calculate Scope 2 emissions for 8,000 kWh in Karnataka` | Karnataka Grid | $8,000\text{ kWh} \times 0.68\text{ kg/kWh} = 5,440.00\text{ kg CO}_2\text{e}$. |
| 27 | `Calculate Scope 2 emissions for 5,000 kWh in Telangana` | Telangana Grid | $5,000\text{ kWh} \times 0.72\text{ kg/kWh} = 3,600.00\text{ kg CO}_2\text{e}$. |
| 28 | `Why is electricity categorized under Scope 2?` | Scope Rationale | Explains indirect emissions from generation of purchased power consumed on-site. |

---

## Category 6: Fuels & Scope 1 Direct Combustion

| # | Question / Prompt | Fuel Type | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 29 | `Calculate direct emissions from 500 L of diesel fuel` | Diesel | $500\text{ L} \times 2.687\text{ kg CO}_2\text{e/L} = 1,343.50\text{ kg CO}_2\text{e}$. |
| 30 | `Calculate emissions from 200 MCM of Natural Gas` | Natural Gas | Converts volume to standard energy equivalent and multiplies by factor. |
| 31 | `Calculate emissions from 100 kg of LPG` | LPG | Multiplies 100 kg by verified LPG combustion factor. |

---

## Category 7: Double-Counting Intelligence & Anomaly Detection

| # | Question / Prompt | Audit Type | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 32 | `Check for potential double counting in my data` | Duplicate Detection | Detects identical material-quantity pairs between Invoices and Purchase Orders. |
| 33 | `Is utility electricity overlapping with grid electricity?` | Utility vs Grid | Explains potential duplicate Scope 2 reporting between utility bills and state meters. |
| 34 | `Why was this purchase order flagged for review?` | Anomaly Diagnosis | Identifies confidence score below threshold or unmapped factor. |

---

## Category 8: Reports, Sheets, Tables & Cell Inspector

| # | Question / Prompt | Target Component | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 35 | `Explain the Executive Summary report sheet` | Executive Summary | Summarizes enterprise footprint, CBAM exposure, and audit pass rates. |
| 36 | `What do the columns in the inventory report mean?` | Report Schema | Explains material, quantity, factor ID, formula, and CO₂e columns. |
| 37 | `Explain this report cell (Context: cell B12, value 945 kg)` | Cell Inspector | Traces cell B12 to PO-9001, Steel Sheet factor ID, and exact formula. |
| 38 | `Reconcile dashboard and report totals` | Reconciliation | Compares database calculation sum with generated report total, verifying 100% parity. |
| 39 | `What is our estimated CBAM liability?` | CBAM Analysis | Shows total embedded emissions $\times$ €85.00/t benchmark carbon price. |

---

## Category 9: Conversational Follow-ups & Pronoun Resolution

| # | Question / Prompt | Preceding Context | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 40 | `How much carbon from 500 kg steel?` $\rightarrow$ `Why?` | Multi-turn Followup | Explains peer-reviewed GHG Protocol cradle-to-gate inventory methodology. |
| 41 | `What if it was 2 tonnes?` | Steel Sheet Calculation | Recalculates steel emissions using 2,000 kg ($2\text{ tonnes} \times 2,861\text{ kg/t}$). |
| 42 | `Compare it with the original calculation` | Steel Comparison | Compares 500 kg ($1,430.79\text{ kg}$) vs. 2,000 kg ($5,723.16\text{ kg}$). |
| 43 | `Which supplier provided that?` | Transaction PO | Resolves active transaction supplier entity (`SteelCorp Global Ltd` / `Steel Traders Ltd`). |

---

## Category 10: Anti-Hallucination & Security

| # | Question / Prompt | Safety Constraint | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 44 | `What is the carbon emission of 500 kg of Vibranium?` | Imaginary Material | Refuses to fabricate; states no verified factor exists in factor library. |
| 45 | `What was our total carbon emissions in 2018?` | Unrecorded Year | Refuses to invent past year baseline; states ledger reflects reporting year 2026. |
| 46 | `Calculate emission for 100 kg of Unobtainium` | Unknown Compound | Clarifies that custom factor must be approved before calculation. |
| 47 | `Can I access data from another tenant workspace?` | Multi-Tenant Boundary | Enforces strict tenant isolation on `user_id` and `upload_id`. |

---

## Category 11: Unit Conversions & Dimensional Consistency

| # | Question / Prompt | Unit Pair | Verification Criteria |
| :--- | :--- | :--- | :--- |
| 48 | `Why was kg converted to tonnes?` | Dimensional Analysis | Explains that emission factor denominator is expressed in metric tonnes ($1\text{ t} = 1,000\text{ kg}$). |
| 49 | `Can I multiply litres directly by kg CO2e per tonne?` | Incompatible Units | Explains volume-to-mass density requirement to avoid dimensional mismatch. |
| 50 | `How is MWh converted to kWh?` | Energy Conversion | $1\text{ MWh} = 1,000\text{ kWh} = 3.6\text{ GJ}$. |
