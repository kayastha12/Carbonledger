import os
import random
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class EmployeeTravelGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_travel = self.config["sizes"]["employee_travel"]
        
        # Load employees
        employees_path = os.path.join(output_dir, "master", "employees.csv")
        employees_df = pd.read_csv(employees_path)
        employees_records = employees_df[["EmployeeID", "CompanyID", "Department", "TravelCategory"]].to_dict("records")
        
        # Mapped cities for travel destinations
        cities_path = os.path.join(output_dir, "master", "cities.csv")
        cities_df = pd.read_csv(cities_path)
        cities_list = cities_df["CityName"].tolist()
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)
        total_days = (end_date - start_date).days
        
        travel = []
        travel_idx = 1
        
        # Emission factors
        ef_travel = self.settings.EMISSION_FACTORS["travel"]
        
        print("Generating Employee Travel Logs...")
        for i in tqdm(range(num_travel)):
            emp = random.choice(employees_records)
            emp_id = emp["EmployeeID"]
            company_id = emp["CompanyID"]
            dept = emp["Department"]
            travel_policy = emp["TravelCategory"] # Economy, Business, First Class
            
            # Select travel mode
            mode = random.choice(["Flight", "Flight", "Train", "Car"])
            
            origin = random.choice(cities_list)
            dest = random.choice(cities_list)
            while dest == origin:
                dest = random.choice(cities_list)
                
            # Distance based on mode
            if mode == "Flight":
                distance = round(random.uniform(500.0, 10000.0), 1)
                flight_class = travel_policy
                mode_key = f"Flight {flight_class}"
            else:
                distance = round(random.uniform(50.0, 600.0), 1)
                flight_class = "N/A"
                mode_key = mode
                
            hotel_nights = random.randint(0, 7)
            
            day_offset = random.randint(0, total_days)
            t_date = start_date + timedelta(days=day_offset)
            
            # Resolve factors
            factor_mode = ef_travel[mode_key]
            factor_hotel = ef_travel["Hotel stay"]
            
            # Math
            co2 = round((distance * factor_mode["CO2"]) + (hotel_nights * factor_hotel["CO2"]), 4)
            ch4 = round((distance * factor_mode["CH4"]) + (hotel_nights * factor_hotel["CH4"]), 6)
            n2o = round((distance * factor_mode["N2O"]) + (hotel_nights * factor_hotel["N2O"]), 6)
            co2e = round((distance * factor_mode["CO2e"]) + (hotel_nights * factor_hotel["CO2e"]), 4)
            
            travel.append({
                "TravelID": travel_idx,
                "CompanyID": company_id,
                "EmployeeID": emp_id,
                "Department": dept,
                "TravelMode": mode,
                "Origin": origin,
                "Destination": dest,
                "Distance": distance,
                "HotelNights": hotel_nights,
                "FlightClass": flight_class,
                "EmissionFactor": factor_mode["CO2e"],
                "CO2Emission": co2,
                "CH4Emission": ch4,
                "N2OEmission": n2o,
                "CO2eEmission": co2e,
                "TravelDate": t_date.strftime("%Y-%m-%d")
            })
            travel_idx += 1
            
        df = pd.DataFrame(travel)
        self.save_data(df, output_dir, "employee_travel", is_master=False, pk_col="TravelID")
        print(f"Generated {len(df)} Employee Travel Records.")
