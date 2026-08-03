import os
import random
import pandas as pd
from generators.base import BaseGenerator

class ProductsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_products = self.config["sizes"]["products"]
        
        # Load companies
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_records = companies_df[["CompanyID", "Industry"]].to_dict("records")
        
        products = []
        for i in range(num_products):
            product_id = i + 1
            # Pick a company
            comp = random.choice(company_records)
            company_id = comp["CompanyID"]
            industry = comp["Industry"]
            
            # Get template for this industry
            templates = self.settings.PRODUCT_TEMPLATES.get(industry)
            if not templates:
                # fallback
                templates = self.settings.PRODUCT_TEMPLATES["Steel"]
                
            template = random.choice(templates)
            
            # Format SKU: e.g. STL-HR-12345
            sku_prefix = "".join(w[:2].upper() for w in template["name"].split())[:4]
            sku = f"{sku_prefix}-{random.randint(10000, 99999)}"
            
            # Add variance to product name to make it unique
            prod_name = f"{template['name']} - Lot {random.randint(100, 999)}"
            category = industry
            material = template["material"]
            weight = round(random.uniform(template["weight_mean"] * 0.8, template["weight_mean"] * 1.2), 3)
            unit = template["unit"]
            
            # Get standard emission factor
            factor_gas = self.settings.EMISSION_FACTORS["material"].get(material, {"CO2e": 1.5})
            std_ef = factor_gas["CO2e"]
            
            cost = round(random.uniform(template["cost_mean"] * 0.9, template["cost_mean"] * 1.1), 2)
            price = round(random.uniform(template["price_mean"] * 0.95, template["price_mean"] * 1.05), 2)
            
            products.append({
                "ProductID": product_id,
                "CompanyID": company_id,
                "SKU": sku,
                "ProductName": prod_name,
                "Category": category,
                "Material": material,
                "Weight": weight,
                "Unit": unit,
                "StandardEmissionFactor": std_ef,
                "SellingPrice": price,
                "ManufacturingCost": cost
            })
            
        df = pd.DataFrame(products)
        self.save_data(df, output_dir, "products", is_master=True, pk_col="ProductID")
        print(f"Generated {num_products} Products.")
