import os
import random
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator
from utils.helpers import get_seasonal_utility_load

class WaterBillsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_bills = self.config["sizes"]["water_bills"]
        
        # Load plants
        plants_path = os.path.join(output_dir, "master", "plants.csv")
        plants_df = pd.read_csv(plants_path)
        plant_records = plants_df[["PlantID", "CompanyID", "Country"]].to_dict("records")
        
        months = []
        for year in [2023, 2024, 2025, 2026]:
            for month in range(1, 13):
                months.append(f"{year}-{month:02d}")
                
        bills = []
        bill_idx = 1
        
        # 30,000 / (150 * 48) = ~4.1 meters per plant
        meters = ["METER_WATER_INLET", "METER_WATER_PROCESS", "METER_WATER_COOLING", "METER_WATER_DOMESTIC", "METER_WATER_OUTLET"]
        
        # Resolved emission factors from settings
        factors = self.settings.EMISSION_FACTORS["water"]
        
        print("Generating Water Bills...")
        for p in tqdm(plant_records):
            plant_id = p["PlantID"]
            company_id = p["CompanyID"]
            country = p["Country"]
            
            for meter in meters:
                for month_str in months:
                    if len(bills) >= num_bills:
                        break
                        
                    date_val = datetime.strptime(month_str + "-15", "%Y-%m-%d")
                    seasonal_factor = get_seasonal_utility_load(date_val, country)
                    
                    base_consumption = random.uniform(100.0, 2000.0) # in cubic meters
                    consumption = round(base_consumption * seasonal_factor, 2)
                    
                    treatment_cost = round(consumption * random.uniform(1.5, 4.5), 2)
                    
                    # Emission factor representing water processing and wastewater treatment
                    ef_supply = factors["Supply"]["CO2e"]
                    ef_treatment = factors["Treatment"]["CO2e"]
                    total_ef = ef_supply + ef_treatment
                    
                    co2 = round(consumption * (factors["Supply"]["CO2"] + factors["Treatment"]["CO2"]), 4)
                    ch4 = round(consumption * (factors["Supply"]["CH4"] + factors["Treatment"]["CH4"]), 6)
                    n2o = round(consumption * (factors["Supply"]["N2O"] + factors["Treatment"]["N2O"]), 6)
                    co2e = round(consumption * total_ef, 4)
                    
                    bills.append({
                        "WaterBillID": bill_idx,
                        "CompanyID": company_id,
                        "PlantID": plant_id,
                        "Consumption": consumption,
                        "TreatmentCost": treatment_cost,
                        "EmissionFactor": total_ef,
                        "CO2Emission": co2,
                        "CH4Emission": ch4,
                        "N2OEmission": n2o,
                        "CO2eEmission": co2e,
                        "BillingMonth": month_str
                    })
                    bill_idx += 1
                    
            if len(bills) >= num_bills:
                break
                
        df = pd.DataFrame(bills)
        self.save_data(df, output_dir, "water_bills", is_master=False, pk_col="WaterBillID")
        print(f"Generated {len(df)} Water Bills.")
