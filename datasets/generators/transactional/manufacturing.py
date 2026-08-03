import os
import random
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class ManufacturingOrdersGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_mfg = self.config["sizes"]["manufacturing_orders"]
        
        # Load plants & products
        plants_path = os.path.join(output_dir, "master", "plants.csv")
        plants_df = pd.read_csv(plants_path)
        plant_records = plants_df[["PlantID", "CompanyID"]].to_dict("records")
        
        products_path = os.path.join(output_dir, "master", "products.csv")
        products_df = pd.read_csv(products_path)
        product_records = products_df[["ProductID", "CompanyID", "ProductName"]].to_dict("records")
        
        # Group products by CompanyID
        products_by_company = {}
        for p in product_records:
            cid = p["CompanyID"]
            if cid not in products_by_company:
                products_by_company[cid] = []
            products_by_company[cid].append(p["ProductID"])
            
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)
        total_days = (end_date - start_date).days
        
        mfg = []
        
        print("Generating Manufacturing Orders...")
        for i in tqdm(range(num_mfg)):
            mfg_id = i + 1
            
            # Select plant
            plant = random.choice(plant_records)
            plant_id = plant["PlantID"]
            company_id = plant["CompanyID"]
            
            # Select product from same company
            comp_pids = products_by_company.get(company_id, [])
            if not comp_pids:
                comp_pids = [p["ProductID"] for p in product_records] # fallback
                
            product_id = random.choice(comp_pids)
            
            day_offset = random.randint(0, total_days)
            prod_date = start_date + timedelta(days=day_offset)
            
            shift = random.choice(["Shift 1", "Shift 2", "Shift 3"])
            machine_hours = round(random.uniform(2.0, 16.0), 1)
            electricity = round(machine_hours * random.uniform(50.0, 250.0), 2) # in kWh
            
            qty = round(random.uniform(10.0, 1000.0), 1)
            waste = round(qty * random.uniform(0.01, 0.08), 2)
            
            mfg.append({
                "ManufacturingOrderID": mfg_id,
                "PlantID": plant_id,
                "ProductID": product_id,
                "ProductionDate": prod_date.strftime("%Y-%m-%d"),
                "Shift": shift,
                "MachineHours": machine_hours,
                "ElectricityConsumed": electricity,
                "QuantityProduced": qty,
                "WasteGenerated": waste
            })
            
        df = pd.DataFrame(mfg)
        self.save_data(df, output_dir, "manufacturing_orders", is_master=False, pk_col="ManufacturingOrderID")
        print(f"Generated {num_mfg} Manufacturing Orders.")
