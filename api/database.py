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

    # 5. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        organization TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'auditor',
        default_region TEXT DEFAULT 'DE',
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        last_login TEXT
    )
    """)

    # 6. Custom Rules Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS custom_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL,
        rule_type TEXT NOT NULL,
        condition_field TEXT NOT NULL,
        condition_operator TEXT NOT NULL,
        condition_value TEXT NOT NULL,
        target_action TEXT NOT NULL,
        target_value TEXT NOT NULL,
        priority INTEGER DEFAULT 10,
        is_active INTEGER DEFAULT 1,
        updated_by TEXT,
        updated_at TEXT
    )
    """)

    # 7. Factor Overrides Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS factor_overrides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_pattern TEXT NOT NULL,
        region TEXT NOT NULL,
        scope TEXT NOT NULL DEFAULT 'Scope 3',
        custom_emission_factor REAL NOT NULL,
        unit TEXT NOT NULL DEFAULT 'kg',
        source_name TEXT NOT NULL,
        reason TEXT,
        is_active INTEGER DEFAULT 1,
        updated_by TEXT,
        updated_at TEXT
    )
    """)

    # 8. Admin Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        user_email TEXT NOT NULL,
        action_type TEXT NOT NULL,
        target_module TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT
    )
    """)

    # Seed Default Users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        import hashlib
        def _hash_pw(pw: str) -> str:
            salt = "carbonledger_secure_salt_2026"
            return hashlib.sha256((pw + salt).encode('utf-8')).hexdigest()
        
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO users (email, password_hash, full_name, organization, role, default_region, created_at)
        VALUES 
        ('admin@carbonledger.io', ?, 'System Administrator', 'CarbonLedger Global', 'admin', 'DE', ?),
        ('auditor@carbonledger.io', ?, 'Senior ESG Auditor', 'TÜV Rheinland Audit Team', 'auditor', 'IN', ?),
        ('lead@enterprise.com', ?, 'Sustainability Director', 'Siemens Energy ESG', 'auditor', 'DE', ?)
        """, (
            _hash_pw("Admin@12345"), now_str,
            _hash_pw("Auditor@12345"), now_str,
            _hash_pw("Lead@12345"), now_str
        ))

        # Seed initial rules
        cursor.execute("""
        INSERT INTO custom_rules (rule_name, rule_type, condition_field, condition_operator, condition_value, target_action, target_value, priority, is_active, updated_by, updated_at)
        VALUES 
        ('Steel Scrap Scope Routing', 'scope_routing', 'material', 'contains', 'scrap', 'set_scope', 'Scope 3', 1, 1, 'admin@carbonledger.io', ?),
        ('Solar Energy Zero Emission Override', 'factor_mapping', 'material', 'contains', 'solar', 'set_factor', '0.0', 2, 1, 'admin@carbonledger.io', ?)
        """, (now_str, now_str))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DATABASE_PATH)
