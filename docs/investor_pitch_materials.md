# CarbonLedger AI Auditor – Investor Pitch & Product Presentation Material

This document contains presentation outlines, scripts, brochures, and architectural visualizers to demonstrate CarbonLedger to investors, academic review boards, and prospective clients.

---

## 1. System Architecture & Workflows

### 1.1 Core Multi-Agent AI Pipeline
This sequence diagram shows the autonomous transfer of states and checkpoints across the 12 cooperative nodes:

```mermaid
sequenceDiagram
    participant User as User / ERP
    participant Intake as Intake Agent
    participant OCR as OCR Agent
    participant NER as NER Agent
    participant Factor as Factor Matcher Agent
    participant Calc as Calc Agent
    participant Rec as Recs Agent
    participant DB as Postgres/ChromaDB

    User->>Intake: Upload PDF Invoice
    Intake->>OCR: Ingest & Extract Words
    OCR->>NER: Parse Layout & Tokens
    NER->>Factor: Mapped Material & Supplier
    Factor->>DB: Query Vector DB Embeddings
    DB-->>Factor: Return Top-5 Mapped Factors
    Factor->>Calc: Selected Factor Mapped
    Calc->>Rec: Calculation Complete
    Rec->>User: Audit Dashboard Refreshed
```

### 1.2 Entity Relationship Diagram (ERD)
Exposes the database schema model containing multi-tenant credentials, invoice items, and calculation mappings:

```mermaid
erDiagram
    TENANTS ||--o{ WORKSPACES : owns
    WORKSPACES ||--o{ INVOICES : tracks
    INVOICES ||--o{ CALCULATIONS : computes
    CALCULATIONS ||--|| FACTORS : reference
```

### 1.3 CBAM Compliance Flow
Validation flow matching European Commission carbon border declarations:

```mermaid
graph TD
    A[Raw Manifest/Invoice Ingest] --> B[Extract Weight & HS Code]
    B --> C[Compute Direct Emissions]
    B --> D[Compute Indirect Grid Emissions]
    C --> E[Calculate Specific Intensity t/t]
    D --> E
    E --> F[Generate CBAM Quarterly Declaration XML]
```

---

## 2. Investor Pitch Slides Outline
- **Slide 1: Title & Purpose**: CarbonLedger AI Auditor - Autonomous Scope 1/2/3 Supply Chain ESG Auditor.
- **Slide 2: The Problem**: EU CBAM tariffs and corporate CSRD audits require granular, traceable carbon footprints; manual spreadsheets lead to audit failures.
- **Slide 3: The Solution**: Autonomous AI agent workflows replacing manual inputs with trainable deep learning classifiers, contrastive SentenceTransformers, and hybrid RAG.
- **Slide 4: Competitive Advantage**: Open-source model controls, sub-second latency, local edge deployment readiness, and Model Context Protocol (MCP) integrations.
- **Slide 5: Business Model**: Multi-tenant SaaS subscriptions (Free, Pro, Enterprise) powered by consumption-capped API keys and Stripe webhooks.

---

## 3. Screen Recording Demo Script
- **0:00 - 0:15 (Login)**: Presenter navigates to port 3000, enters demo credentials (`admin@carbonledger.ai`), and unlocks the main control screen.
- **0:15 - 0:45 (Dashboard & Audit)**: Showcases the 4 KPI boxes and the real-time agent execution stream logs.
- **0:45 - 1:15 (One-Click AI Demo)**: Presenter clicks "Run Complete AI Demo", highlighting the progress bar as the system runs OCR, classification, supplier risk estimation, and factors queries.
- **1:15 - 1:45 (CBAM Generation)**: Opens the *CBAM* tab to export XML and Excel formats.
- **1:45 - 2:00 (AI Copilot Chat)**: Type "Compare suppliers" in the Copilot chat, showing grounded citations from the RAG store.
