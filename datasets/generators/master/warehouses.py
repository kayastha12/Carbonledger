import os
import random
import pandas as pd
from generators.base import BaseGenerator

class WarehousesGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_warehouses = self.config["sizes"]["warehouses"]
        
        # Load companies
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_records = companies_df[["CompanyID", "Country", "City"]].to_dict("records")
        
        warehouses = []
        for i in range(num_warehouses):
            warehouse_id = i + 1
            company = random.choice(company_records)
            company_id = company["CompanyID"]
            country = company["Country"]
            city = company["City"]
            
            warehouse_name = f"Warehouse-{warehouse_id:03d} ({city})"
            
            # Simple coordinate bounds by country
            coords = {
                "India": (19.0, 23.0, 72.0, 77.0),
                "China": (22.0, 31.0, 113.0, 121.0),
                "Germany": (48.0, 53.0, 8.0, 11.0),
                "Japan": (34.0, 36.0, 135.0, 140.0),
                "USA": (34.0, 42.0, -118.0, -74.0),
                "Canada": (43.0, 49.0, -80.0, -73.0),
                "UK": (51.0, 55.0, -2.0, 0.0),
                "France": (43.0, 48.0, 1.0, 5.0),
                "Italy": (40.0, 45.0, 9.0, 14.0),
                "Australia": (-37.0, -32.0, 144.0, 151.0),
                "Brazil": (-23.0, -20.0, -47.0, -43.0)
            }
            
            lat_min, lat_max, lon_min, lon_max = coords.get(country, (20.0, 40.0, -100.0, 100.0))
            latitude = round(random.uniform(lat_min, lat_max), 5)
            longitude = round(random.uniform(lon_min, lon_max), 5)
            
            capacity = round(random.uniform(5000.0, 100000.0), 2)
            temp_controlled = random.choice([True, False])
            warehouse_type = random.choice(["Central Distribution Center", "Regional Hub", "Cross-Docking Facility", "Fulfillment Center"])
            
            warehouses.append({
                "WarehouseID": warehouse_id,
                "CompanyID": company_id,
                "WarehouseName": warehouse_name,
                "Country": country,
                "City": city,
                "Latitude": latitude,
                "Longitude": longitude,
                "Capacity": capacity,
                "TemperatureControlled": temp_controlled,
                "WarehouseType": warehouse_type
            })
            
        df = pd.DataFrame(warehouses)
        self.save_data(df, output_dir, "warehouses", is_master=True, pk_col="WarehouseID")
        print(f"Generated {num_warehouses} Warehouses.")
