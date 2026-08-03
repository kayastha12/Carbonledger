import os
import json
import pandas as pd
import numpy as np

def validate_datasets(output_dir, config, settings):
    """Executes automated verification tests across generated datasets and returns a JSON report."""
    report = {
        "status": "PASS",
        "total_checks": 0,
        "failed_checks": 0,
        "checks": []
    }
    
    def log_check(name, passed, message):
        report["total_checks"] += 1
        if not passed:
            report["failed_checks"] += 1
            report["status"] = "FAIL"
        report["checks"].append({
            "check_name": name,
            "passed": passed,
            "message": message
        })

    master_dir = os.path.join(output_dir, "master")
    trans_dir = os.path.join(output_dir, "transactional")

    # Helper to load file
    def load_df(folder, name):
        csv_path = os.path.join(folder, f"{name}.csv")
        parquet_path = os.path.join(folder, f"{name}.parquet")
        if os.path.exists(parquet_path):
            return pd.read_parquet(parquet_path)
        elif os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        return None

    # Load master tables
    companies_df = load_df(master_dir, "companies")
    suppliers_df = load_df(master_dir, "suppliers")
    products_df = load_df(master_dir, "products")
    plants_df = load_df(master_dir, "plants")
    warehouses_df = load_df(master_dir, "warehouses")
    employees_df = load_df(master_dir, "employees")
    vehicles_df = load_df(master_dir, "vehicles")
    drivers_df = load_df(master_dir, "drivers")
    customers_df = load_df(master_dir, "customers")
    bom_df = load_df(master_dir, "bom")

    # Load transactional tables
    po_df = load_df(trans_dir, "purchase_orders")
    po_items_df = load_df(trans_dir, "purchase_order_items")
    invoices_df = load_df(trans_dir, "invoices")
    payments_df = load_df(trans_dir, "payments")
    erp_df = load_df(trans_dir, "erp_export")
    shipping_df = load_df(trans_dir, "shipping_manifest")
    logistics_df = load_df(trans_dir, "logistics")
    electricity_df = load_df(trans_dir, "electricity_bills")
    water_df = load_df(trans_dir, "water_bills")
    fuel_df = load_df(trans_dir, "fuel_logs")
    waste_df = load_df(trans_dir, "waste_logs")
    travel_df = load_df(trans_dir, "employee_travel")
    cbam_df = load_df(trans_dir, "cbam_reporting")
    mfg_df = load_df(trans_dir, "manufacturing_orders")
    inventory_df = load_df(trans_dir, "inventory")

    # 1. Primary Key Uniqueness Checks
    pk_checks = [
        ("companies", companies_df, "CompanyID"),
        ("suppliers", suppliers_df, "SupplierID"),
        ("products", products_df, "ProductID"),
        ("plants", plants_df, "PlantID"),
        ("warehouses", warehouses_df, "WarehouseID"),
        ("employees", employees_df, "EmployeeID"),
        ("vehicles", vehicles_df, "VehicleID"),
        ("drivers", drivers_df, "DriverID"),
        ("customers", customers_df, "CustomerID"),
        ("bom", bom_df, "BOMID"),
        ("purchase_orders", po_df, "POID"),
        ("purchase_order_items", po_items_df, "POItemID"),
        ("invoices", invoices_df, "InvoiceID"),
        ("payments", payments_df, "PaymentID"),
        ("erp_export", erp_df, "ERPID"),
        ("shipping_manifest", shipping_df, "ManifestID"),
        ("logistics", logistics_df, "LogisticsID"),
        ("electricity_bills", electricity_df, "ElectricityID"),
        ("water_bills", water_df, "WaterBillID"),
        ("fuel_logs", fuel_df, "FuelLogID"),
        ("waste_logs", waste_df, "WasteID"),
        ("employee_travel", travel_df, "TravelID"),
        ("cbam_reporting", cbam_df, "CBAMID"),
        ("manufacturing_orders", mfg_df, "ManufacturingOrderID"),
        ("inventory", inventory_df, "InventoryID")
    ]

    for name, df, pk in pk_checks:
        if df is not None:
            # Check for non-null and uniqueness
            total = len(df)
            unique = df[pk].nunique(dropna=True)
            non_null = df[pk].notnull().sum()
            passed = (total == unique) and (non_null == total)
            log_check(f"{name}_pk_uniqueness", passed, f"PK {pk} Unique: {unique}/{total}, Non-Null: {non_null}/{total}")
        else:
            log_check(f"{name}_pk_uniqueness", False, f"Table {name} not found.")

    # 2. Referential Integrity Check
    fk_checks = [
        ("suppliers -> companies", suppliers_df, "CompanyID", companies_df, "CompanyID"),
        ("products -> companies", products_df, "CompanyID", companies_df, "CompanyID"),
        ("plants -> companies", plants_df, "CompanyID", companies_df, "CompanyID"),
        ("warehouses -> companies", warehouses_df, "CompanyID", companies_df, "CompanyID"),
        ("employees -> companies", employees_df, "CompanyID", companies_df, "CompanyID"),
        ("vehicles -> companies", vehicles_df, "CompanyID", companies_df, "CompanyID"),
        ("drivers -> companies", drivers_df, "CompanyID", companies_df, "CompanyID"),
        ("drivers -> warehouses", drivers_df, "WarehouseID", warehouses_df, "WarehouseID"),
        ("customers -> companies", customers_df, "CompanyID", companies_df, "CompanyID"),
        ("bom -> products", bom_df, "ProductID", products_df, "ProductID"),
        ("bom -> suppliers", bom_df, "SupplierID", suppliers_df, "SupplierID"),
        ("purchase_orders -> companies", po_df, "CompanyID", companies_df, "CompanyID"),
        ("purchase_orders -> suppliers", po_df, "SupplierID", suppliers_df, "SupplierID"),
        ("purchase_order_items -> purchase_orders", po_items_df, "POID", po_df, "POID"),
        ("purchase_order_items -> products", po_items_df, "ProductID", products_df, "ProductID"),
        ("invoices -> purchase_orders", invoices_df, "POID", po_df, "POID"),
        ("invoices -> suppliers", invoices_df, "SupplierID", suppliers_df, "SupplierID"),
        ("payments -> invoices", payments_df, "InvoiceID", invoices_df, "InvoiceID"),
        ("erp_export -> companies", erp_df, "CompanyID", companies_df, "CompanyID"),
        ("erp_export -> invoices", erp_df, "InvoiceID", invoices_df, "InvoiceID"),
        ("erp_export -> purchase_orders", erp_df, "POID", po_df, "POID"),
        ("shipping_manifest -> invoices", shipping_df, "InvoiceID", invoices_df, "InvoiceID"),
        ("shipping_manifest -> purchase_orders", shipping_df, "POID", po_df, "POID"),
        ("shipping_manifest -> suppliers", shipping_df, "SupplierID", suppliers_df, "SupplierID"),
        ("logistics -> shipping_manifest", logistics_df, "ManifestID", shipping_df, "ManifestID"),
        ("logistics -> vehicles", logistics_df, "VehicleID", vehicles_df, "VehicleID"),
        ("logistics -> drivers", logistics_df, "DriverID", drivers_df, "DriverID"),
        ("logistics -> warehouses", logistics_df, "WarehouseID", warehouses_df, "WarehouseID"),
        ("electricity_bills -> companies", electricity_df, "CompanyID", companies_df, "CompanyID"),
        ("electricity_bills -> plants", electricity_df, "PlantID", plants_df, "PlantID"),
        ("water_bills -> companies", water_df, "CompanyID", companies_df, "CompanyID"),
        ("water_bills -> plants", water_df, "PlantID", plants_df, "PlantID"),
        ("fuel_logs -> companies", fuel_df, "CompanyID", companies_df, "CompanyID"),
        ("fuel_logs -> vehicles", fuel_df, "VehicleID", vehicles_df, "VehicleID"),
        ("waste_logs -> companies", waste_df, "CompanyID", companies_df, "CompanyID"),
        ("employee_travel -> companies", travel_df, "CompanyID", companies_df, "CompanyID"),
        ("employee_travel -> employees", travel_df, "EmployeeID", employees_df, "EmployeeID"),
        ("cbam_reporting -> companies", cbam_df, "CompanyID", companies_df, "CompanyID"),
        ("cbam_reporting -> suppliers", cbam_df, "SupplierID", suppliers_df, "SupplierID"),
        ("cbam_reporting -> products", cbam_df, "ProductID", products_df, "ProductID"),
        ("cbam_reporting -> invoices", cbam_df, "InvoiceID", invoices_df, "InvoiceID"),
        ("manufacturing_orders -> plants", mfg_df, "PlantID", plants_df, "PlantID"),
        ("manufacturing_orders -> products", mfg_df, "ProductID", products_df, "ProductID"),
        ("inventory -> warehouses", inventory_df, "WarehouseID", warehouses_df, "WarehouseID"),
        ("inventory -> products", inventory_df, "ProductID", products_df, "ProductID")
    ]

    for label, df_child, fk, df_parent, pk in fk_checks:
        if df_child is not None and df_parent is not None:
            # Check for orphan records (ignoring Nulls in Child since some FKs might be nullable in corruption mode)
            child_keys = df_child[fk].dropna().unique()
            parent_keys = set(df_parent[pk].unique())
            orphans = [k for k in child_keys if k not in parent_keys]
            passed = len(orphans) == 0
            log_check(f"fk_{label}", passed, f"FK check: {len(orphans)} orphans found out of {len(child_keys)} keys")
        else:
            log_check(f"fk_{label}", False, f"Table(s) for check {label} are missing.")

    # 3. Date Logical Order Checks
    if po_df is not None and invoices_df is not None:
        # Match invoice dates with PO dates
        merged = invoices_df.merge(po_df, on="POID", suffixes=("_inv", "_po"))
        # Exclude corrupt records with _DUP or status issues
        normal_records = merged[~merged["Status_po"].isnull() & ~merged["Status_inv"].isnull()]
        if len(normal_records) > 0:
            inv_dates = pd.to_datetime(normal_records["InvoiceDate"])
            po_dates = pd.to_datetime(normal_records["PODate"])
            passed = (inv_dates >= po_dates).all()
            total_bad = (inv_dates < po_dates).sum()
            log_check("invoice_date_after_po_date", passed, f"InvoiceDate >= PODate for all normal records. Violations: {total_bad}/{len(normal_records)}")

    # 4. Carbon Math Verification (Non-corrupted data)
    # Check electricity math: CO2Emission = ConsumptionKWh * GridEmissionFactor
    if electricity_df is not None:
        normal_elec = electricity_df[electricity_df["Status"] != "Corrupted"] if "Status" in electricity_df.columns else electricity_df
        if len(normal_elec) > 0:
            diff = abs(normal_elec["CO2Emission"] - (normal_elec["ConsumptionKWh"] * normal_elec["GridEmissionFactor"]))
            passed = (diff < 1e-2).all()
            log_check("electricity_carbon_math", passed, f"Electricity CO2 = KWh * Factor. Max deviation: {diff.max()}")

    # Check fuel math
    if fuel_df is not None:
        normal_fuel = fuel_df[fuel_df["Status"] != "Corrupted"] if "Status" in fuel_df.columns else fuel_df
        if len(normal_fuel) > 0:
            diff = abs(normal_fuel["CO2Emission"] - (normal_fuel["FuelVolume"] * normal_fuel["EmissionFactor"]))
            passed = (diff < 1e-2).all()
            log_check("fuel_carbon_math", passed, f"Fuel CO2 = Volume * Factor. Max deviation: {diff.max()}")

    # 5. Inventory Math Verification
    if inventory_df is not None:
        passed = (inventory_df["AvailableStock"] >= 0).all() and (inventory_df["ReservedStock"] >= 0).all()
        log_check("inventory_positive_balances", passed, f"All stock balances are positive.")

    # 6. Payment Reconciliation
    if payments_df is not None and invoices_df is not None:
        merged_pay = payments_df.merge(invoices_df, on="InvoiceID", suffixes=("_pay", "_inv"))
        passed = (merged_pay["Amount"] <= merged_pay["GrandTotal"] * 1.01).all() # allow slight rounding tolerance
        log_check("payment_reconciliation", passed, "Payments are <= Invoice GrandTotal.")

    # Save validation report
    os.makedirs(os.path.join(output_dir, "reports"), exist_ok=True)
    report_path = os.path.join(output_dir, "reports", "validation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report
