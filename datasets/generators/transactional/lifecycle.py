import os
import random
import pandas as pd
from generators.base import BaseGenerator

class ProductLifecycleGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        # Load products
        products_path = os.path.join(output_dir, "master", "products.csv")
        products_df = pd.read_csv(products_path)
        product_records = products_df[["ProductID", "Weight", "StandardEmissionFactor", "Category"]].to_dict("records")
        
        lifecycle = []
        for i, prod in enumerate(product_records):
            lifecycle_id = i + 1
            pid = prod["ProductID"]
            weight = prod["Weight"]
            std_ef = prod["StandardEmissionFactor"]
            cat = prod["Category"]
            
            # Carbon calculations based on weight and standard factors (which are in kg CO2e / kg or tonne)
            # Standard emission factor represents raw material footprint. Let's make it our baseline.
            # Total weight * standard factor = total cradle-to-gate footprint
            base_em = weight * std_ef
            
            raw_mat_em = round(base_em * random.uniform(0.75, 0.85), 3)
            mfg_em = round(base_em * random.uniform(0.10, 0.15), 3)
            transport_em = round(base_em * random.uniform(0.03, 0.08), 3)
            
            # If product is Automobile, usage emission is very high
            if cat == "Automobile":
                usage_em = round(base_em * random.uniform(2.0, 5.0), 3)
            elif cat in ["Chemical", "Electronics"]:
                usage_em = round(base_em * random.uniform(0.2, 0.5), 3)
            else:
                usage_em = 0.0
                
            eol_em = round(base_em * random.uniform(0.01, 0.05), 3)
            
            total_em = round(raw_mat_em + mfg_em + transport_em + usage_em + eol_em, 3)
            
            lifecycle.append({
                "LifecycleID": lifecycle_id,
                "ProductID": pid,
                "RawMaterialEmission": raw_mat_em,
                "ManufacturingEmission": mfg_em,
                "TransportEmission": transport_em,
                "UsageEmission": usage_em,
                "EndOfLifeEmission": eol_em,
                "TotalEmission": total_em
            })
            
        df = pd.DataFrame(lifecycle)
        self.save_data(df, output_dir, "lifecycle", is_master=False, pk_col="LifecycleID")
        print(f"Generated {len(df)} Product Lifecycle Records.")
