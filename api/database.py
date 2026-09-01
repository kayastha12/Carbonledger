import os
import sqlite3
import json
import time
import hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(PROJECT_ROOT, "carbonledger.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(password: str) -> str:
    salt = "carbonledger_secure_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

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
    
    # 2. Users Table (SaaS User Accounts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        organization TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'subscriber',
        default_region TEXT DEFAULT 'DE',
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 1,
        verification_token TEXT,
        reset_token TEXT,
        reset_token_expires REAL,
        token_balance INTEGER DEFAULT 100,
        total_tokens_consumed INTEGER DEFAULT 0,
        created_at TEXT,
        last_login TEXT
    )
    """)

    # 3. Subscriptions Table (SaaS Tiers: trial, starter, professional, enterprise)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        plan_tier TEXT NOT NULL DEFAULT 'trial',
        billing_cycle TEXT NOT NULL DEFAULT 'monthly',
        status TEXT NOT NULL DEFAULT 'trial',
        start_date TEXT,
        renewal_date TEXT,
        price_usd REAL DEFAULT 0.0,
        report_limit INTEGER DEFAULT 3,
        reports_generated_count INTEGER DEFAULT 0,
        updated_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 4. Token Transactions Table (Ledger of Token Consumption & Allocation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS token_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        balance_after INTEGER NOT NULL,
        action_type TEXT NOT NULL,
        description TEXT,
        metadata_json TEXT,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 5. Billing Records Table (Invoices & Receipts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS billing_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        plan_name TEXT NOT NULL,
        billing_cycle TEXT NOT NULL,
        amount_usd REAL NOT NULL,
        payment_status TEXT NOT NULL DEFAULT 'PAID',
        payment_method TEXT DEFAULT 'Credit Card (Stripe)',
        invoice_date TEXT,
        period_start TEXT,
        period_end TEXT,
        pdf_receipt_url TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 6. Upload Sessions Table (Multi-tenant)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS upload_sessions (
        upload_id TEXT PRIMARY KEY,
        user_id INTEGER DEFAULT 1,
        filename TEXT,
        pages_count INTEGER,
        tables_count INTEGER,
        total_co2e_kg REAL,
        total_cbam_cost_eur REAL,
        overall_confidence_pct REAL,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 7. Extracted Records Table (Multi-tenant)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS extracted_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_id TEXT,
        user_id INTEGER DEFAULT 1,
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
        FOREIGN KEY (upload_id) REFERENCES upload_sessions(upload_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 8. Calculation Results Table (Multi-tenant)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calculation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_id TEXT,
        user_id INTEGER DEFAULT 1,
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
        is_anomaly INTEGER DEFAULT 0,
        anomaly_reason TEXT,
        is_duplicate INTEGER DEFAULT 0,
        ocr_error INTEGER DEFAULT 0,
        recommendations_json TEXT,
        po_number TEXT,
        FOREIGN KEY (upload_id) REFERENCES upload_sessions(upload_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 9. Parsing Reviews Table (Multi-tenant)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parsing_reviews (
        upload_id TEXT PRIMARY KEY,
        user_id INTEGER DEFAULT 1,
        original_ocr_json TEXT,
        reviewed_json TEXT,
        final_approved_json TEXT,
        audit_log TEXT,
        parser_response TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 10. Reports Table (Multi-tenant compliance exports)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        upload_id TEXT,
        report_type TEXT NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        total_co2e_kg REAL,
        total_cbam_cost_eur REAL,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 11. User Activities Table (Activity Timeline)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_type TEXT NOT NULL,
        description TEXT NOT NULL,
        ip_address TEXT DEFAULT '127.0.0.1',
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 12. Chat History Table (AI Assistant Queries)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        message TEXT NOT NULL,
        tokens_consumed INTEGER DEFAULT 5,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 13. Custom Rules Table
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

    # 14. Factor Overrides Table
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

    # 15. Admin Audit Logs Table
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

    # Column Alterations / Migrations for existing databases
    tables_to_add_user_id = [
        "upload_sessions",
        "extracted_records",
        "calculation_results",
        "parsing_reviews"
    ]
    for tbl in tables_to_add_user_id:
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN user_id INTEGER DEFAULT 1")
        except Exception:
            pass

    user_alter_queries = [
        "ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1",
        "ALTER TABLE users ADD COLUMN verification_token TEXT",
        "ALTER TABLE users ADD COLUMN reset_token TEXT",
        "ALTER TABLE users ADD COLUMN reset_token_expires REAL",
        "ALTER TABLE users ADD COLUMN token_balance INTEGER DEFAULT 100",
        "ALTER TABLE users ADD COLUMN total_tokens_consumed INTEGER DEFAULT 0"
    ]
    for q in user_alter_queries:
        try:
            cursor.execute(q)
        except Exception:
            pass

    # Default App Settings
    defaults = {
        "carbon_price_eur_per_ton": "85.0",
        "default_region": "DE",
        "reporting_year": "2026",
        "theme": "dark"
    }
    for k, v in defaults.items():
        cursor.execute("""
        INSERT OR IGNORE INTO app_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        """, (k, v, time.time()))

    # Initialize Master Administrator User
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    renewal_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 30 * 86400))

    cursor.execute("SELECT id FROM users WHERE LOWER(email) = 'admin@carbonledger.io'")
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute("""
        INSERT INTO users (email, password_hash, full_name, organization, role, default_region, is_active, is_verified, token_balance, total_tokens_consumed, created_at)
        VALUES ('admin@carbonledger.io', ?, 'System Administrator', 'CarbonLedger Global', 'admin', 'DE', 1, 1, 999999, 0, ?)
        """, (hash_pw("Admin@12345"), now_str))
        admin_id = cursor.lastrowid

        # Admin Enterprise Subscription
        cursor.execute("""
        INSERT INTO subscriptions (user_id, plan_tier, billing_cycle, status, start_date, renewal_date, price_usd, report_limit, reports_generated_count, updated_at)
        VALUES (?, 'enterprise', 'yearly', 'active', ?, ?, 4790.0, 99999, 0, ?)
        """, (admin_id, now_str, renewal_str, now_str))

        # Initial Admin Token Transaction
        cursor.execute("""
        INSERT INTO token_transactions (user_id, amount, balance_after, action_type, description, timestamp)
        VALUES (?, 999999, 999999, 'PLAN_ALLOCATION', 'Enterprise Unlimited Administrator Allocation', ?)
        """, (admin_id, now_str))
    else:
        # Ensure role is admin
        cursor.execute("UPDATE users SET role = 'admin', is_active = 1, is_verified = 1 WHERE id = ?", (admin_row["id"],))

    # Initialize Demo Subscriber User for seamless showcase testing
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = 'subscriber@carbonledger.io'")
    sub_row = cursor.fetchone()
    if not sub_row:
        cursor.execute("""
        INSERT INTO users (email, password_hash, full_name, organization, role, default_region, is_active, is_verified, token_balance, total_tokens_consumed, created_at)
        VALUES ('subscriber@carbonledger.io', ?, 'Alex Morgan (ESG Director)', 'Apex Manufacturing Ltd', 'subscriber', 'DE', 1, 1, 1000, 150, ?)
        """, (hash_pw("Subscriber@12345"), now_str))
        sub_id = cursor.lastrowid

        # Starter Plan Subscription
        cursor.execute("""
        INSERT INTO subscriptions (user_id, plan_tier, billing_cycle, status, start_date, renewal_date, price_usd, report_limit, reports_generated_count, updated_at)
        VALUES (?, 'starter', 'monthly', 'active', ?, ?, 49.0, 25, 2, ?)
        """, (sub_id, now_str, renewal_str, now_str))

        # Initial Token Allocation
        cursor.execute("""
        INSERT INTO token_transactions (user_id, amount, balance_after, action_type, description, timestamp)
        VALUES (?, 1000, 1000, 'PLAN_ALLOCATION', 'Starter Monthly Quota Allocation (1,000 Tokens)', ?)
        """, (sub_id, now_str))

        # Billing Invoice Record
        cursor.execute("""
        INSERT INTO billing_records (invoice_number, user_id, plan_name, billing_cycle, amount_usd, payment_status, payment_method, invoice_date, period_start, period_end, pdf_receipt_url)
        VALUES ('INV-2026-00101', ?, 'Starter Plan', 'monthly', 49.0, 'PAID', 'Visa ending in 4242', ?, ?, ?, '/api/v1/user/billing/invoice/INV-2026-00101')
        """, (sub_id, now_str, now_str, renewal_str))

        cursor.execute("""
        INSERT INTO user_activities (user_id, activity_type, description, ip_address, created_at)
        VALUES (?, 'ACCOUNT_CREATED', 'Subscribed to Starter Plan with 1,000 token monthly balance', '127.0.0.1', ?)
        """, (sub_id, now_str))

    # Seed initial rules if empty
    cursor.execute("SELECT COUNT(*) FROM custom_rules")
    if cursor.fetchone()[0] == 0:
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
