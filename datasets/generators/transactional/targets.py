import os
import random
import pandas as pd
from generators.base import BaseGenerator

class SustainabilityTargetsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        # Load companies
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_records = companies_df[["CompanyID", "NetZeroTargetYear"]].to_dict("records")
        
        targets = []
        for i, comp in enumerate(company_records):
            target_id = i + 1
            company_id = comp["CompanyID"]
            net_zero_year = comp["NetZeroTargetYear"]
            
            # If no target, generate default future target
            if pd.isnull(net_zero_year) or not net_zero_year:
                nz_year = random.choice([2040, 2045, 2050, 2060])
            else:
                nz_year = int(net_zero_year)
                
            # target % reduction relative to 2020 baseline
            scope1 = round(random.uniform(30.0, 80.0), 2)
            scope2 = round(random.uniform(40.0, 90.0), 2)
            scope3 = round(random.uniform(20.0, 60.0), 2)
            
            current_em = round(random.uniform(5000.0, 500000.0), 2) # in tonnes CO2e
            
            targets.append({
                "TargetID": target_id,
                "CompanyID": company_id,
                "Scope1Target": scope1,
                "Scope2Target": scope2,
                "Scope3Target": scope3,
                "NetZeroYear": nz_year,
                "CurrentEmission": current_em
            })
            
        df = pd.DataFrame(targets)
        self.save_data(df, output_dir, "targets", is_master=False, pk_col="TargetID")
        print(f"Generated {len(df)} Corporate Sustainability Targets.")
