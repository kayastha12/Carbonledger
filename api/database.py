import sqlite3
import time

DATABASE_PATH = "d:/internship/carbonledger/carbonledger.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 2. Roles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 3. Permissions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        action TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 4. Workspaces Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        name TEXT,
        tenant_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 5. Suppliers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        country TEXT,
        esg_score REAL,
        risk_level TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 6. Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        doc_type TEXT,
        content TEXT,
        status TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 7. Invoices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT,
        supplier TEXT,
        material TEXT,
        quantity REAL,
        unit TEXT,
        cost REAL,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 8. PurchaseOrders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT,
        supplier TEXT,
        material TEXT,
        quantity REAL,
        unit TEXT,
        cost REAL,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 9. UtilityBills Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utility_bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        utility_provider TEXT,
        utility_type TEXT,
        consumption REAL,
        unit TEXT,
        cost REAL,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 10. Facilities Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        location TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 11. FuelConsumption Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fuel_consumption (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fuel_type TEXT,
        quantity REAL,
        unit TEXT,
        facility TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 12. MaterialConsumption Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS material_consumption (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material TEXT,
        quantity REAL,
        unit TEXT,
        facility TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 13. Logistics Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transport_mode TEXT,
        distance REAL,
        weight REAL,
        origin TEXT,
        destination TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 14. EmissionCalculations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emission_calculations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        co2e_kg REAL,
        scope TEXT,
        confidence REAL,
        factor_used REAL,
        factor_source TEXT,
        anomaly_check TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 15. Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        report_type TEXT,
        filepath TEXT,
        metadata_json TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 16. Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        message TEXT,
        recipient_role TEXT,
        recipient_email TEXT,
        is_read INTEGER DEFAULT 0,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 17. AuditTrail Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_trail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        details TEXT,
        user_email TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # 18. Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        payload TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        created_by TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    # Seed default workspaces
    cursor.execute("SELECT id FROM workspaces WHERE id = 'workspace_default'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO workspaces (id, name, tenant_id, created_by, created_at, updated_at)
        VALUES ('workspace_default', 'Main Workspace', 'tenant_default', 'system', ?, ?)
        """, (time.time(), time.time()))
        
    # Seed default users
    demo_users = [
        ('admin@carbonledger.ai', 'demo123', 'Company Administrator', 'tenant_default', 'workspace_default'),
        ('auditor@carbonledger.ai', 'demo123', 'Carbon Auditor', 'tenant_default', 'workspace_default'),
        ('supplier@steelcorp.com', 'demo123', 'Supplier Representative', 'tenant_default', 'workspace_default'),
        ('ceo@ecosteel.eu', 'demo123', 'Executive (CEO)', 'tenant_default', 'workspace_default'),
    ]
    
    for email, pw, role, tenant, ws in demo_users:
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO users (email, password, role, tenant_id, workspace_id, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'system', ?, ?)
            """, (email, pw, role, tenant, ws, time.time(), time.time()))
            
    # Seed default suppliers
    suppliers = [
        ('Supplier_1', 'DE', 4.2, 'Low'),
        ('Supplier_2', 'CN', 2.5, 'High'),
        ('SteelCorp India', 'IN', 4.5, 'Medium')
    ]
    for name, country, esg, risk in suppliers:
        cursor.execute("SELECT name FROM suppliers WHERE name = ?", (name,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO suppliers (name, country, esg_score, risk_level, tenant_id, workspace_id, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'tenant_default', 'workspace_default', 'system', ?, ?)
            """, (name, country, esg, risk, time.time(), time.time()))
            
    conn.commit()
    conn.close()
    print("SQLite database tables initialized and seeded successfully.")

if __name__ == "__main__":
    init_db()
