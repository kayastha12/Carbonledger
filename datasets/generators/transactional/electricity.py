import os
import random
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator
from utils.helpers import get_seasonal_utility_load

class ElectricityBillsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_bills = self.config["sizes"]["electricity_bills"]
        
        # Load plants
        plants_path = os.path.join(output_dir, "master", "plants.csv")
        plants_df = pd.read_csv(plants_path)
        plant_records = plants_df[["PlantID", "CompanyID", "Country"]].to_dict("records")
        
        # Generate monthly billing dates
        months = []
        for year in [2023, 2024, 2025, 2026]:
            for month in range(1, 13):
                months.append(f"{year}-{month:02d}")
                
        bills = []
        bill_idx = 1
        
        # Determine meters per plant
        # We need roughly 40,000 bills from 150 plants over 48 months.
        # 40000 / (150 * 48) = 5.5 meters per plant.
        meters = ["METER_MAIN", "METER_HVAC", "METER_ADMIN", "METER_FABRICATION", "METER_ASSEMBLY", "METER_WWAREHOUSE"]
        
        print("Generating Electricity Bills...")
        for p in tqdm(plant_records):
            plant_id = p["PlantID"]
            company_id = p["CompanyID"]
            country = p["Country"]
            
            # Resolve emission factors from settings
            factors = self.settings.EMISSION_FACTORS["electricity"].get(country, {"CO2": 0.4, "CH4": 0.000004, "N2O": 0.000001, "CO2e": 0.41})
            
            for meter in meters:
                for month_str in months:
                    if len(bills) >= num_bills:
                        break
                        
                    date_val = datetime.strptime(month_str + "-15", "%Y-%m-%d")
                    seasonal_factor = get_seasonal_utility_load(date_val, country)
                    
                    base_consumption = random.uniform(5000.0, 50000.0)
                    consumption = round(base_consumption * seasonal_factor, 2)
                    
                    peak_demand = round(consumption * 0.003 * random.uniform(0.9, 1.1), 2)
                    energy_charge = round(consumption * random.uniform(0.08, 0.18), 2)
                    
                    # Renewable percentage representation
                    renewable_pct = round(random.choice([0.0, 0.0, 10.0, 25.0, 50.0, 80.0]), 2)
                    net_factor_mult = (1.0 - (renewable_pct / 100.0))
                    
                    co2 = round(consumption * factors["CO2"] * net_factor_mult, 4)
                    ch4 = round(consumption * factors["CH4"] * net_factor_mult, 6)
                    n2o = round(consumption * factors["N2O"] * net_factor_mult, 6)
                    co2e = round(consumption * factors["CO2e"] * net_factor_mult, 4)
                    
                    bills.append({
                        "ElectricityID": bill_idx,
                        "CompanyID": company_id,
                        "PlantID": plant_id,
                        "BillingMonth": month_str,
                        "ConsumptionKWh": consumption,
                        "PeakDemand": peak_demand,
                        "EnergyCharge": energy_charge,
                        "GridEmissionFactor": factors["CO2e"],
                        "RenewablePercentage": renewable_pct,
                        "CO2Emission": co2,
                        "CH4Emission": ch4,
                        "N2OEmission": n2o,
                        "CO2eEmission": co2e
                    })
                    bill_idx += 1
                    
            if len(bills) >= num_bills:
                break
                
        df = pd.DataFrame(bills)
        self.save_data(df, output_dir, "electricity_bills", is_master=False, pk_col="ElectricityID")
        print(f"Generated {len(df)} Electricity Bills.")
