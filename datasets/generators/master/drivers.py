import os
import random
import pandas as pd
from generators.base import BaseGenerator
from utils.helpers import generate_phone_number

class DriversGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_drivers = self.config["sizes"]["drivers"]
        
        # Load companies & warehouses
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_records = companies_df[["CompanyID", "Country"]].to_dict("records")
        
        warehouses_path = os.path.join(output_dir, "master", "warehouses.csv")
        warehouses_df = pd.read_csv(warehouses_path)
        warehouse_records = warehouses_df[["WarehouseID", "CompanyID"]].to_dict("records")
        
        # Map warehouses by company to make sure the driver belongs to the same company and warehouse
        warehouses_by_company = {}
        for w in warehouse_records:
            cid = w["CompanyID"]
            if cid not in warehouses_by_company:
                warehouses_by_company[cid] = []
            warehouses_by_company[cid].append(w["WarehouseID"])
            
        drivers = []
        for i in range(num_drivers):
            driver_id = f"DRV-{i + 1:04d}"
            # Choose company
            comp = random.choice(company_records)
            company_id = comp["CompanyID"]
            country = comp["Country"]
            
            # Choose warehouse from same company, fallback to random if none
            wh_list = warehouses_by_company.get(company_id, [])
            warehouse_id = random.choice(wh_list) if len(wh_list) > 0 else random.choice([w["WarehouseID"] for w in warehouse_records])
            
            license_type = random.choice(["Commercial HGV", "Commercial LGV", "Standard DL"])
            experience = random.randint(2, 25)
            contact = generate_phone_number(country)
            status = random.choice(["Active", "Active", "On Leave", "Suspended"])
            
            drivers.append({
                "DriverID": driver_id,
                "CompanyID": company_id,
                "WarehouseID": warehouse_id,
                "LicenseType": license_type,
                "Experience": experience,
                "ContactNumber": contact,
                "Status": status
            })
            
        df = pd.DataFrame(drivers)
        self.save_data(df, output_dir, "drivers", is_master=True, pk_col="DriverID")
        print(f"Generated {num_drivers} Drivers.")
