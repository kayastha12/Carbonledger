import os
import random
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class InventoryGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_inventory = self.config["sizes"]["inventory"]
        
        # Load warehouses & products
        warehouses_path = os.path.join(output_dir, "master", "warehouses.csv")
        warehouses_df = pd.read_csv(warehouses_path)
        warehouse_records = warehouses_df[["WarehouseID", "CompanyID"]].to_dict("records")
        
        products_path = os.path.join(output_dir, "master", "products.csv")
        products_df = pd.read_csv(products_path)
        product_records = products_df[["ProductID", "CompanyID"]].to_dict("records")
        
        # Group products by CompanyID
        products_by_company = {}
        for p in product_records:
            cid = p["CompanyID"]
            if cid not in products_by_company:
                products_by_company[cid] = []
            products_by_company[cid].append(p["ProductID"])
            
        inventory = []
        
        print("Generating Inventory records...")
        for i in tqdm(range(num_inventory)):
            inv_id = i + 1
            
            # Select warehouse
            wh = random.choice(warehouse_records)
            wh_id = wh["WarehouseID"]
            company_id = wh["CompanyID"]
            
            # Select product from same company
            comp_pids = products_by_company.get(company_id, [])
            if not comp_pids:
                comp_pids = [p["ProductID"] for p in product_records] # fallback
                
            product_id = random.choice(comp_pids)
            
            min_stock = random.randint(10, 200)
            reorder_lvl = min_stock + random.randint(20, 300)
            avail_stock = reorder_lvl + random.randint(50, 10000)
            res_stock = random.randint(0, min(1000, avail_stock // 5))
            max_stock = avail_stock + random.randint(2000, 50000)
            
            inventory.append({
                "InventoryID": inv_id,
                "WarehouseID": wh_id,
                "ProductID": product_id,
                "AvailableStock": avail_stock,
                "ReservedStock": res_stock,
                "MinimumStock": min_stock,
                "MaximumStock": max_stock,
                "ReorderLevel": reorder_lvl
            })
            
        df = pd.DataFrame(inventory)
        self.save_data(df, output_dir, "inventory", is_master=False, pk_col="InventoryID")
        print(f"Generated {num_inventory} Inventory Records.")
