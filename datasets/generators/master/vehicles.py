import os
import random
from datetime import datetime, timedelta
import pandas as pd
from generators.base import BaseGenerator

class VehiclesGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_vehicles = self.config["sizes"]["vehicles"]
        
        # Load companies
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_records = companies_df[["CompanyID", "Country"]].to_dict("records")
        
        vehicle_types = ["Heavy Duty Truck", "Medium Duty Truck", "Light Commercial Vehicle", "Electric Van", "Company Car"]
        emissions = {
            "Heavy Duty Truck": ("Diesel", 15000.0, "Euro VI"),
            "Medium Duty Truck": ("Diesel", 8000.0, "Euro VI"),
            "Light Commercial Vehicle": ("Petrol", 2000.0, "Euro V"),
            "Electric Van": ("Electricity", 1500.0, "ZEV"),
            "Company Car": ("Petrol", 500.0, "Euro VI")
        }
        
        vehicles = []
        for i in range(num_vehicles):
            vehicle_id = f"VEH-{i + 1:04d}"
            company = random.choice(company_records)
            company_id = company["CompanyID"]
            country = company["Country"]
            
            v_type = random.choice(vehicle_types)
            fuel, cap, e_class = emissions[v_type]
            
            # If electric, check company grid
            if v_type == "Electric Van":
                fuel = "Electricity"
                
            # Formatting realistic registration plates
            if country == "India":
                reg_num = f"MH-12-{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}-{random.randint(1000, 9999)}"
            elif country == "Germany":
                reg_num = f"M-{chr(random.randint(65, 90))}{chr(random.randint(65, 90))} {random.randint(100, 9999)}"
            elif country == "USA":
                reg_num = f"{random.randint(1, 9)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.randint(100, 999)}" if 'string' in globals() else f"9XX{random.randint(100,999)}"
                # fallback string
                import string as s_mod
                reg_num = f"{random.randint(1, 9)}{random.choice(s_mod.ascii_uppercase)}{random.choice(s_mod.ascii_uppercase)}{random.randint(100, 999)}"
            else:
                reg_num = f"REG-{random.randint(1000, 9999)}"
                
            purch_days = random.randint(0, 1500)
            purch_date = (datetime(2019, 1, 1) + timedelta(days=purch_days)).strftime("%Y-%m-%d")
            
            vehicles.append({
                "VehicleID": vehicle_id,
                "CompanyID": company_id,
                "VehicleType": v_type,
                "RegistrationNumber": reg_num,
                "FuelType": fuel,
                "Capacity": cap,
                "EmissionClass": e_class,
                "PurchaseDate": purch_date
            })
            
        df = pd.DataFrame(vehicles)
        self.save_data(df, output_dir, "vehicles", is_master=True, pk_col="VehicleID")
        print(f"Generated {num_vehicles} Vehicles.")
