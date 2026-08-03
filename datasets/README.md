# CarbonLedger — AI-Powered Supply Chain Emissions Auditor

This repository contains an enterprise-grade synthetic dataset generator that simulates a real-world manufacturing ERP system integrated with carbon accounting and CBAM compliance. The dataset is normalized, referentially consistent, and ready for use in databases, dashboards, ML models, and RAG pipelines.

---

## Folder Structure

```
├── config/
│   ├── config.yaml         # Configuration file (dataset sizes, seeds, corruption rate)
│   └── settings.py         # Static geography mapping and emission factors
├── generators/
│   ├── base.py             # Abstract base generator class
│   ├── master/             # Masters: Companies, Suppliers, Products, Plants, etc.
│   └── transactional/      # Transactions: POs, Invoices, Logistics, Utilities, RAG docs
├── utils/
│   ├── helpers.py          # ID generators & Seasonality algorithms
│   ├── corruption.py       # Data corruption simulation engine
│   └── validation.py       # Referential integrity validation framework
├── schemas/
│   ├── ddl.sql             # Optimized PostgreSQL schema (with indexes and partitions)
│   ├── erd.md              # Entity Relationship Diagram & Data Dictionary
│   └── powerbi_schema.md   # Star Schema Model & DAX Measures
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml  # PostgreSQL container deployment
├── main.py                 # Core orchestration script
├── requirements.txt
└── README.md
```

---

## Installation & Setup

1. **Clone & Open Workspace**:
   Ensure you are operating within the target workspace directory.

2. **Initialize Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # On Windows
   # source .venv/bin/activate # On macOS/Linux
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Data Generator

1. **Verify Configuration**:
   Open [config/config.yaml](file:///d:/CL_dataSets/AI%20Training%20Data/config/config.yaml) and adjust dataset sizes, random seeds, and output formats (CSV, Parquet, JSON).

2. **Execute Pipeline**:
   ```bash
   python main.py
   ```
   *This will run all master and transactional generators sequentially, calculate emissions, run the validation checks, and generate performance reports.*

3. **Inspect Outputs**:
   - Master tables are generated at `output/master/`.
   - Transactional tables are generated at `output/transactional/`.
   - Performance and validation logs are saved in `output/reports/`.

---

## Importing into PostgreSQL

1. **Run PostgreSQL via Docker**:
   ```bash
   cd docker
   docker-compose up -d
   ```
   *This starts an Alpine PostgreSQL instance (`carbonledger_db`) and automatically initialises the schema from `schemas/ddl.sql`.*

2. **Bulk Upload CSVs**:
   Use the `COPY` scripts provided at the bottom of [schemas/ddl.sql](file:///d:/CL_dataSets/AI%20Training%20Data/schemas/ddl.sql) to bulk-load data from the output directory into the container database:
   ```bash
   docker exec -it carbonledger_db psql -U carbonadmin -d carbonledger -c "\copy companies FROM '/app/output/master/companies.csv' DELIMITER ',' CSV HEADER;"
   ```

---

## Power BI Setup

1. Connect Power BI Desktop to the PostgreSQL database or point it directly to the folder containing the generated CSV/Parquet files (`output/master` and `output/transactional`).
2. Follow the model structure defined in [schemas/powerbi_schema.md](file:///d:/CL_dataSets/AI%20Training%20Data/schemas/powerbi_schema.md) to link Fact tables to Dimension tables using the standard **Star Schema** approach.
3. Import the documented DAX measures to build Scope 1/2/3 charts and CBAM Tax Liability dashboards.

---

## Machine Learning & AI/RAG Pipeline Integration

- **Supervised ML Anomaly Detection**:
  Use `output/transactional/ai_labels.csv` to train classification models (e.g. XGBoost, Random Forests) on detecting corrupted transactions or extreme carbon emission outliers.
- **RAG & Vector Databases**:
  Ingest `output/transactional/documents.csv` and `output/transactional/embeddings.csv` directly into LangChain, LlamaIndex, Chroma, or Pinecone to test vector similarity and semantic search queries over supply chain records.
