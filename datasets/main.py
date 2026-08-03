import os
import sys
import time
import json
import yaml

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load settings
import config.settings as settings
from utils.validation import validate_datasets

# Import master generators
from generators.master.reference import ReferenceGenerator
from generators.master.companies import CompaniesGenerator
from generators.master.suppliers import SuppliersGenerator
from generators.master.customers import CustomersGenerator
from generators.master.plants import PlantsGenerator
from generators.master.warehouses import WarehousesGenerator
from generators.master.employees import EmployeesGenerator
from generators.master.vehicles import VehiclesGenerator
from generators.master.drivers import DriversGenerator
from generators.master.products import ProductsGenerator
from generators.master.bom import BOMGenerator

# Import transactional generators
from generators.transactional.weather import WeatherGenerator
from generators.transactional.shutdowns import ShutdownsGenerator
from generators.transactional.purchase_orders import PurchaseOrdersGenerator
from generators.transactional.invoices import InvoicesGenerator
from generators.transactional.payments import PaymentsGenerator
from generators.transactional.exchange_rates import ExchangeRatesGenerator
from generators.transactional.erp import ERPExportGenerator
from generators.transactional.shipping import ShippingManifestGenerator
from generators.transactional.logistics import LogisticsGenerator
from generators.transactional.electricity import ElectricityBillsGenerator
from generators.transactional.water import WaterBillsGenerator
from generators.transactional.fuel import FuelLogsGenerator
from generators.transactional.waste import WasteLogsGenerator
from generators.transactional.travel import EmployeeTravelGenerator
from generators.transactional.cbam import CBAMReportingGenerator
from generators.transactional.manufacturing import ManufacturingOrdersGenerator
from generators.transactional.inventory import InventoryGenerator
from generators.transactional.targets import SustainabilityTargetsGenerator
from generators.transactional.offsets import CarbonOffsetsGenerator
from generators.transactional.audits import SupplierAuditsGenerator
from generators.transactional.lifecycle import ProductLifecycleGenerator
from generators.transactional.documents import DocumentsGenerator
from generators.transactional.embeddings import EmbeddingsGenerator
from generators.transactional.ai_labels import AILabelsGenerator

def main():
    print("=" * 60)
    print("CarbonLedger Enterprise-Grade Synthetic Dataset Generator")
    print("=" * 60)
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Track performance
    perf_report = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "generators": {},
        "total_rows": 0,
        "total_duration_seconds": 0.0
    }
    
    generators_pipeline = [
        # 1. Master reference tables
        ("reference", ReferenceGenerator, True),
        ("companies", CompaniesGenerator, True),
        ("suppliers", SuppliersGenerator, True),
        ("customers", CustomersGenerator, True),
        ("plants", PlantsGenerator, True),
        ("warehouses", WarehousesGenerator, True),
        ("employees", EmployeesGenerator, True),
        ("vehicles", VehiclesGenerator, True),
        ("drivers", DriversGenerator, True),
        ("products", ProductsGenerator, True),
        ("product_bom", BOMGenerator, True),
        
        # 2. Transactional tables
        ("weather", WeatherGenerator, False),
        ("shutdowns", ShutdownsGenerator, False),
        ("purchase_orders", PurchaseOrdersGenerator, False),
        ("invoices", InvoicesGenerator, False),
        ("payments", PaymentsGenerator, False),
        ("exchange_rates", ExchangeRatesGenerator, False),
        ("erp_export", ERPExportGenerator, False),
        ("shipping_manifest", ShippingManifestGenerator, False),
        ("logistics", LogisticsGenerator, False),
        ("electricity_bills", ElectricityBillsGenerator, False),
        ("water_bills", WaterBillsGenerator, False),
        ("fuel_logs", FuelLogsGenerator, False),
        ("waste_logs", WasteLogsGenerator, False),
        ("employee_travel", EmployeeTravelGenerator, False),
        ("cbam_reporting", CBAMReportingGenerator, False),
        ("manufacturing_orders", ManufacturingOrdersGenerator, False),
        ("inventory", InventoryGenerator, False),
        ("sustainability_targets", SustainabilityTargetsGenerator, False),
        ("carbon_offsets", CarbonOffsetsGenerator, False),
        ("supplier_audits", SupplierAuditsGenerator, False),
        ("product_lifecycle", ProductLifecycleGenerator, False),
        ("documents", DocumentsGenerator, False),
        ("embeddings", EmbeddingsGenerator, False),
        ("ai_labels", AILabelsGenerator, False)
    ]
    
    total_start = time.perf_counter()
    
    for name, GenClass, is_master in generators_pipeline:
        print(f"\nRunning generator: {name}...")
        gen = GenClass(config, settings)
        
        t0 = time.perf_counter()
        
        # Reference Generator handles multiple tables internally
        if name == "reference":
            gen.generate(output_dir)
            duration = time.perf_counter() - t0
            rows = sum(config["sizes"].get(k, 0) for k in ["countries", "cities", "ports"])
        else:
            gen.generate(output_dir)
            duration = time.perf_counter() - t0
            rows = config["sizes"].get(name, 0)
            
        perf_report["generators"][name] = {
            "duration_seconds": round(duration, 2),
            "rows_generated": rows,
            "throughput_rows_per_second": round(rows / duration, 1) if duration > 0 else 0
        }
        perf_report["total_rows"] += rows
        
    total_duration = time.perf_counter() - total_start
    perf_report["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    perf_report["total_duration_seconds"] = round(total_duration, 2)
    perf_report["overall_throughput_rows_per_second"] = round(perf_report["total_rows"] / total_duration, 1)
    
    print("\n" + "=" * 60)
    print("DATA GENERATION COMPLETE")
    print(f"Total Rows: {perf_report['total_rows']:,}")
    print(f"Total Time: {perf_report['total_duration_seconds']:.2f} seconds")
    print(f"Overall Throughput: {perf_report['overall_throughput_rows_per_second']:,} rows/sec")
    print("=" * 60)
    
    # Run validation framework
    print("\nRunning automated dataset validation...")
    val_report = validate_datasets(output_dir, config, settings)
    
    print(f"Validation Status: {val_report['status']}")
    print(f"Total Checks: {val_report['total_checks']}")
    print(f"Failed Checks: {val_report['failed_checks']}")
    
    # Save performance execution report
    os.makedirs(os.path.join(output_dir, "reports"), exist_ok=True)
    with open(os.path.join(output_dir, "reports", "execution_report.json"), "w") as f:
        json.dump(perf_report, f, indent=2)
        
    print("All reports exported to output/reports/.")

if __name__ == "__main__":
    main()
