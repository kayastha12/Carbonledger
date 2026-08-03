import os
import random
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class FuelLogsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_logs = self.config["sizes"]["fuel_logs"]
        
        # Load vehicles
        vehicles_path = os.path.join(output_dir, "master", "vehicles.csv")
        vehicles_df = pd.read_csv(vehicles_path)
        vehicles_records = vehicles_df[["VehicleID", "CompanyID", "VehicleType", "FuelType"]].to_dict("records")
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)
        total_days = (end_date - start_date).days
        
        fuel_prices = {
            "Diesel": 1.45,
            "Petrol": 1.55,
            "CNG": 1.10,
            "LPG": 0.85,
            "Electricity": 0.15 # price per kWh
        }
        
        logs = []
        for i in range(num_logs):
            log_id = i + 1
            # Pick random vehicle
            veh = random.choice(vehicles_records)
            vehicle_id = veh["VehicleID"]
            company_id = veh["CompanyID"]
            fuel_type = veh["FuelType"]
            v_type = veh["VehicleType"]
            
            # Select date
            day_offset = random.randint(0, total_days)
            log_date = start_date + timedelta(days=day_offset)
            
            # Volume based on vehicle type
            if v_type == "Heavy Duty Truck":
                volume = round(random.uniform(150.0, 450.0), 2)
                mileage_rate = random.uniform(3.0, 5.0) # km per liter
            elif v_type == "Medium Duty Truck":
                volume = round(random.uniform(80.0, 200.0), 2)
                mileage_rate = random.uniform(6.0, 9.0)
            elif v_type == "Light Commercial Vehicle":
                volume = round(random.uniform(40.0, 100.0), 2)
                mileage_rate = random.uniform(10.0, 14.0)
            elif v_type == "Electric Van":
                volume = round(random.uniform(60.0, 120.0), 2) # in kWh consumption equivalent
                mileage_rate = random.uniform(4.0, 6.0) # km per kWh
            else: # Company Car
                volume = round(random.uniform(30.0, 60.0), 2)
                mileage_rate = random.uniform(12.0, 18.0)
                
            cost = round(volume * fuel_prices.get(fuel_type, 1.30) * random.uniform(0.9, 1.1), 2)
            mileage = round(volume * mileage_rate, 2)
            
            # Resolve factors
            if fuel_type == "Electricity":
                # uses electricity emission factor (using USA base as fallback, or we can use default grid factor)
                factors = self.settings.EMISSION_FACTORS["electricity"].get("USA", {"CO2": 0.37, "CH4": 0.000003, "N2O": 0.0000008, "CO2e": 0.38})
            else:
                factors = self.settings.EMISSION_FACTORS["fuel"].get(fuel_type, {"CO2": 2.5, "CH4": 0.0002, "N2O": 0.001, "CO2e": 2.55})
                
            co2 = round(volume * factors["CO2"], 4)
            ch4 = round(volume * factors["CH4"], 6)
            n2o = round(volume * factors["N2O"], 6)
            co2e = round(volume * factors["CO2e"], 4)
            
            logs.append({
                "FuelLogID": log_id,
                "CompanyID": company_id,
                "VehicleID": vehicle_id,
                "FuelType": fuel_type,
                "FuelVolume": volume,
                "FuelCost": cost,
                "Mileage": mileage,
                "EmissionFactor": factors["CO2e"],
                "CO2Emission": co2,
                "CH4Emission": ch4,
                "N2OEmission": n2o,
                "CO2eEmission": co2e,
                "FuelDate": log_date.strftime("%Y-%m-%d")
            })
            
        df = pd.DataFrame(logs)
        self.save_data(df, output_dir, "fuel_logs", is_master=False, pk_col="FuelLogID")
        print(f"Generated {num_logs} Fuel Logs.")
