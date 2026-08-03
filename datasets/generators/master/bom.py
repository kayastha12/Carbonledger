import os
import random
import pandas as pd
from generators.base import BaseGenerator

class BOMGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_bom = self.config["sizes"]["product_bom"]
        
        # Load products
        products_path = os.path.join(output_dir, "master", "products.csv")
        products_df = pd.read_csv(products_path)
        product_records = products_df[["ProductID", "CompanyID", "Material"]].to_dict("records")
        
        # Load suppliers
        suppliers_path = os.path.join(output_dir, "master", "suppliers.csv")
        suppliers_df = pd.read_csv(suppliers_path)
        supplier_records = suppliers_df[["SupplierID", "CompanyID"]].to_dict("records")
        
        # Map suppliers by company to ensure BOM component suppliers are linked to the same company
        suppliers_by_company = {}
        for s in supplier_records:
            cid = s["CompanyID"]
            if cid not in suppliers_by_company:
                suppliers_by_company[cid] = []
            suppliers_by_company[cid].append(s["SupplierID"])
            
        material_types = list(self.settings.EMISSION_FACTORS["material"].keys())
        
        bom = []
        bom_idx = 1
        
        # For each product, we want to create roughly 5 component lines
        components_per_product = num_bom // len(product_records)
        
        for p in product_records:
            pid = p["ProductID"]
            cid = p["CompanyID"]
            
            # Select matching suppliers
            supp_list = suppliers_by_company.get(cid, [])
            if not supp_list:
                supp_list = [s["SupplierID"] for s in supplier_records]
                
            for _ in range(components_per_product):
                sid = random.choice(supp_list)
                mat = random.choice(material_types)
                qty = round(random.uniform(0.1, 50.0), 2)
                unit = random.choice(["kg", "liter", "pcs"])
                waste_pct = round(random.uniform(1.0, 15.0), 2)
                cost = round(random.uniform(5.0, 150.0), 2)
                
                bom.append({
                    "BOMID": bom_idx,
                    "ProductID": pid,
                    "SupplierID": sid,
                    "Material": mat,
                    "Quantity": qty,
                    "Unit": unit,
                    "WastePercentage": waste_pct,
                    "Cost": cost
                })
                bom_idx += 1
                
        # Fill in any remainder rows to match target size
        while len(bom) < num_bom:
            p = random.choice(product_records)
            pid = p["ProductID"]
            cid = p["CompanyID"]
            supp_list = suppliers_by_company.get(cid, [s["SupplierID"] for s in supplier_records])
            sid = random.choice(supp_list)
            mat = random.choice(material_types)
            qty = round(random.uniform(0.1, 50.0), 2)
            unit = random.choice(["kg", "liter", "pcs"])
            waste_pct = round(random.uniform(1.0, 15.0), 2)
            cost = round(random.uniform(5.0, 150.0), 2)
            
            bom.append({
                "BOMID": bom_idx,
                "ProductID": pid,
                "SupplierID": sid,
                "Material": mat,
                "Quantity": qty,
                "Unit": unit,
                "WastePercentage": waste_pct,
                "Cost": cost
            })
            bom_idx += 1
            
        df = pd.DataFrame(bom)
        self.save_data(df, output_dir, "bom", is_master=True, pk_col="BOMID")
        print(f"Generated {num_bom} BOM Records.")
