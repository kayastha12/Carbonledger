import os
import random
import pandas as pd
from generators.base import BaseGenerator

class CarbonOffsetsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_offsets = self.config["sizes"]["carbon_offsets"]
        
        # Load companies
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_ids = companies_df["CompanyID"].tolist()
        
        projects = [
            ("Amazonian Reforestation", "Afforestation"),
            ("Gujarat Wind Farm Project", "Wind Energy"),
            ("Landfill Methane Capture Texas", "Methane Abatement"),
            ("Cookstove Distribution Kenya", "Community Efficiency"),
            ("Solar Water Heaters Turkey", "Solar Heat")
        ]
        
        offsets = []
        for i in range(num_offsets):
            offset_id = i + 1
            company_id = random.choice(company_ids)
            
            proj_name, proj_type = random.choice(projects)
            credits = random.randint(100, 20000)
            used = random.randint(0, credits)
            reduction = round(used * random.uniform(0.95, 1.0), 2) # in tonnes CO2e
            
            offsets.append({
                "OffsetID": offset_id,
                "CompanyID": company_id,
                "OffsetProject": proj_name,
                "OffsetType": proj_type,
                "CreditsPurchased": credits,
                "CreditsUsed": used,
                "CarbonReduction": reduction
            })
            
        df = pd.DataFrame(offsets)
        self.save_data(df, output_dir, "offsets", is_master=False, pk_col="OffsetID")
        print(f"Generated {num_offsets} Carbon Offsets.")
