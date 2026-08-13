import os
import sqlite3
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(PROJECT_ROOT, "carbonledger.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. App Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at REAL
    )
    """)
    
    # 2. Upload Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS upload_sessions (
        upload_id TEXT PRIMARY KEY,
        filename TEXT,
        pages_count INTEGER,
        tables_count INTEGER,
        total_co2e_kg REAL,
        total_cbam_cost_eur REAL,
        overall_confidence_pct REAL,
        created_at TEXT
    )
    """)

    # 3. Extracted Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS extracted_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_id TEXT,
        po_number TEXT,
        supplier TEXT,
        material TEXT,
        quantity REAL,
        unit TEXT,
        cost REAL,
        facility TEXT,
        country TEXT,
        section TEXT,
        ocr_confidence REAL,
        FOREIGN KEY (upload_id) REFERENCES upload_sessions(upload_id)
    )
    """)

    # 4. Calculation Results Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calculation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_id TEXT,
        material TEXT,
        supplier TEXT,
        quantity REAL,
        unit TEXT,
        matched_material TEXT,
        factor_id TEXT,
        factor_source TEXT,
        scope TEXT,
        emission_factor REAL,
        co2_kg REAL,
        ch4_kg REAL,
        n2o_kg REAL,
        co2e_kg REAL,
        cbam_cost_eur REAL,
        calculation_status TEXT,
        formula TEXT,
        trace_json TEXT,
        FOREIGN KEY (upload_id) REFERENCES upload_sessions(upload_id)
    )
    """)

    # Default Settings
    defaults = {
        "carbon_price_eur_per_ton": "85.0",
        "default_region": "DE",
        "reporting_year": "2026",
        "theme": "dark",
        "user_profile": json.dumps({"name": "Sustainability Manager", "email": "manager@company.com", "role": "Sustainability Lead"})
    }

    for k, v in defaults.items():
        cursor.execute("""
        INSERT OR IGNORE INTO app_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        """, (k, v, time.time()))

    # Add columns to calculation_results if they do not exist
    alter_queries = [
        "ALTER TABLE calculation_results ADD COLUMN is_anomaly INTEGER DEFAULT 0",
        "ALTER TABLE calculation_results ADD COLUMN anomaly_reason TEXT",
        "ALTER TABLE calculation_results ADD COLUMN is_duplicate INTEGER DEFAULT 0",
        "ALTER TABLE calculation_results ADD COLUMN ocr_error INTEGER DEFAULT 0",
        "ALTER TABLE calculation_results ADD COLUMN recommendations_json TEXT",
        "ALTER TABLE calculation_results ADD COLUMN po_number TEXT"
    ]
    for q in alter_queries:
        try:
            cursor.execute(q)
        except Exception:
            pass

    # Create parsing_reviews table
    cursor.execute("DROP TABLE IF EXISTS parsing_reviews")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parsing_reviews (
        upload_id TEXT PRIMARY KEY,
        original_ocr_json TEXT,
        reviewed_json TEXT,
        final_approved_json TEXT,
        audit_log TEXT,
        parser_response TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DATABASE_PATH)
