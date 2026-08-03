import os
import random
from datetime import datetime, timedelta
import pandas as pd
from generators.base import BaseGenerator

class WasteLogsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_logs = self.config["sizes"]["waste_logs"]
        
        # Load companies
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_ids = companies_df["CompanyID"].tolist()
        
        categories = ["Hazardous", "Organic", "Metal Scraps", "Plastic Waste", "Paper/Cardboard"]
        disposal_methods = ["Recycle", "Landfill", "Incineration"]
        recyclers = ["WasteManagement Inc", "CleanHarbors", "EcoRecycle Corp", "ReCycleAll Ltd"]
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)
        total_days = (end_date - start_date).days
        
        logs = []
        for i in range(num_logs):
            waste_id = i + 1
            company_id = random.choice(company_ids)
            
            category = random.choice(categories)
            weight = round(random.uniform(0.1, 15.0), 3) # in metric tonnes
            
            # Simple business logic: Hazardous goes to Landfill/Incinerate, Metal goes to Recycle, etc.
            if category == "Metal Scraps":
                disposal = "Recycle"
            elif category == "Hazardous":
                disposal = random.choice(["Landfill", "Incineration"])
            else:
                disposal = random.choice(disposal_methods)
                
            recycler = random.choice(recyclers) if disposal == "Recycle" else "Municipal Waste Site"
            
            day_offset = random.randint(0, total_days)
            w_date = start_date + timedelta(days=day_offset)
            
            # Resolve factors (which are in kg per kg, which is identical to tonnes per tonne)
            factors = self.settings.EMISSION_FACTORS["waste"].get(disposal, {"CO2": 0.1, "CH4": 0.001, "N2O": 0.0001, "CO2e": 0.12})
            
            # Multiply weight (tonnes) by factor (since it is 1-to-1)
            # 1 metric tonne = 1000 kg. If factor is kg CO2e / kg of waste, then 1 tonne of waste * 1000 kg/tonne * factor kg CO2e / kg = 1000 * weight * factor kg CO2e = weight * factor tonnes CO2e.
            # So the math: CO2Emission (in tonnes or kg) = weight (tonnes) * factor (kg/kg) = weight * factor * 1000 kg.
            # Let's keep emissions in kg to match standard formats.
            weight_kg = weight * 1000.0
            co2 = round(weight_kg * factors["CO2"], 4)
            ch4 = round(weight_kg * factors["CH4"], 6)
            n2o = round(weight_kg * factors["N2O"], 6)
            co2e = round(weight_kg * factors["CO2e"], 4)
            
            logs.append({
                "WasteID": waste_id,
                "CompanyID": company_id,
                "WasteCategory": category,
                "WasteWeight": weight, # in tonnes
                "DisposalMethod": disposal,
                "Recycler": recycler,
                "EmissionFactor": factors["CO2e"],
                "CO2Emission": co2, # in kg
                "CH4Emission": ch4,
                "N2OEmission": n2o,
                "CO2eEmission": co2e,
                "WasteDate": w_date.strftime("%Y-%m-%d")
            })
            
        df = pd.DataFrame(logs)
        self.save_data(df, output_dir, "waste_logs", is_master=False, pk_col="WasteID")
        print(f"Generated {num_logs} Waste Logs.")
