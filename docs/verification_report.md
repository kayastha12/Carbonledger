# CarbonLedger Runtime Verification & Execution Report

This document contains final runtime logs, model loading stats, API response payloads, and paths to compliance reports generated on localhost.

---

## 1. Backend Startup Log (Uvicorn Port 8000)
```text
INFO:     Started server process [2284]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:49954 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:49954 - "GET /openapi.json HTTP/1.1" 200 OK
```

---

## 2. Frontend Startup Log (Vite Port 3000)
```text
> carbonledger-frontend@4.0.0 dev
> vite

  VITE v5.4.21  ready in 1261 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
12:24:12 AM [vite] hmr update /DashboardApp.jsx
```

---

## 3. Database Connection & Model Loading Logs
```text
Loading transformer DocumentClassifier from: d:/internship/carbonledger/models/saved_models/distilbert on cpu
Loading weights: 100%|##########| 104/104 [00:00<00:00, 3985.77it/s]
Loading transformer NERExtractor from: d:/internship/carbonledger/models/saved_models/ner_tagger on cpu
Loading weights: 100%|##########| 102/102 [00:00<00:00, 4049.85it/s]
Loading fine-tuned SentenceTransformer from: d:/internship/carbonledger/models/saved_models/contrastive_matcher
Loading weights: 100%|##########| 103/103 [00:00<00:00, 4115.98it/s]
Loading recommendation regressors from: d:/internship/carbonledger/models/saved_models/recommendation
ChromaDB persistent client loaded at: d:/internship/carbonledger/vector_db/chroma_data
Deduplicating and indexing 7,550 unique emission factors.
```

---

## 4. API Request & Response Logs

### GET `/api/v1/compliance/sec`
- **Request Headers**: `Authorization: Bearer tenant_enterprise:Sustainability Manager`
- **Response Payload**:
```json
{
  "format": "SEC Regulation S-K",
  "report_text": "\n============================================================\nSEC CLIMATE DISCLOSURE STATEMENT - REGULATION S-K\n============================================================\nCompany Name: tenant_enterprise\nReporting Period: Fiscal Year 2026\n...\n- Scope 1 (Direct Emissions): 5.00 metric tons CO2e\n- Scope 2 (Indirect Emissions): 12.00 metric tons CO2e\n- Scope 3 (Supply Chain): 45.00 metric tons CO2e\n\nAssurance Status: Third-party audit ready.\n============================================================\n"
}
```

### GET `/api/v1/mcp/tools`
- **Response Payload**:
```json
{
  "tools": [
    {
      "name": "lookup_emission_factor",
      "description": "Find appropriate carbon emission factors using contrastive semantic search.",
      "inputSchema": { "type": "object", "properties": { "query": { "type": "string" } } }
    },
    {
      "name": "calculate_scope_3",
      "description": "Compute Scope 3 Category 1 emissions for supply chain materials."
    }
  ]
}
```

---

## 5. Exported Compliance Files
- **Compliant Excel Spreadsheet**: [cbam_quarterly_report_q2_2026.xlsx](file:///d:/internship/carbonledger/output/reports/cbam_quarterly_report_q2_2026.xlsx)
- **Compliant PDF Layout Document**: [cbam_quarterly_report_q2_2026.pdf](file:///d:/internship/carbonledger/output/reports/cbam_quarterly_report_q2_2026.pdf)
