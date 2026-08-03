import os
import random
from datetime import datetime, timedelta
import pandas as pd
from generators.base import BaseGenerator

class WeatherGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_weather = self.config["sizes"].get("weather", 100000)
        
        # Load cities
        cities_path = os.path.join(output_dir, "master", "cities.csv")
        cities_df = pd.read_csv(cities_path)
        city_records = cities_df[["CityName", "CountryName"]].to_dict("records")
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)
        total_days = (end_date - start_date).days
        
        weather = []
        weather_idx = 1
        
        # We need to distribute num_weather observations across all city-day combinations.
        # Let's generate observations sequentially to meet the exact count.
        for i in range(num_weather):
            city = random.choice(city_records)
            city_name = city["CityName"]
            country = city["CountryName"]
            
            day_offset = random.randint(0, total_days)
            obs_date = start_date + timedelta(days=day_offset)
            
            month = obs_date.month
            
            # Real temperature estimation based on hemisphere
            southern_countries = ["Australia", "Brazil"]
            is_southern = country in southern_countries
            
            if is_southern:
                # Dec, Jan, Feb are hot
                if month in [12, 1, 2]:
                    temp = round(random.uniform(22.0, 36.0), 1)
                    humidity = round(random.uniform(60.0, 95.0), 1)
                    rainfall = round(random.uniform(0.0, 25.0), 2) if random.random() < 0.3 else 0.0
                else:
                    temp = round(random.uniform(10.0, 22.0), 1)
                    humidity = round(random.uniform(40.0, 75.0), 1)
                    rainfall = round(random.uniform(0.0, 5.0), 2) if random.random() < 0.1 else 0.0
            else:
                # Northern Hemisphere
                if month in [6, 7, 8]:
                    temp = round(random.uniform(20.0, 38.0), 1)
                    humidity = round(random.uniform(50.0, 90.0), 1)
                    # monsoon check for Asia
                    if country in ["India", "Vietnam", "Thailand"] and random.random() < 0.6:
                        rainfall = round(random.uniform(5.0, 55.0), 2) # monsoon rain
                    else:
                        rainfall = round(random.uniform(0.0, 10.0), 2) if random.random() < 0.2 else 0.0
                elif month in [12, 1, 2]:
                    # Cold winter
                    if country in ["Canada", "Germany", "UK", "France", "USA", "Japan"]:
                        temp = round(random.uniform(-10.0, 8.0), 1)
                        rainfall = round(random.uniform(0.0, 10.0), 2) if random.random() < 0.3 else 0.0 # snow/sleet
                    else:
                        temp = round(random.uniform(10.0, 22.0), 1)
                        rainfall = 0.0
                    humidity = round(random.uniform(40.0, 80.0), 1)
                else:
                    temp = round(random.uniform(12.0, 25.0), 1)
                    humidity = round(random.uniform(50.0, 75.0), 1)
                    rainfall = round(random.uniform(0.0, 8.0), 2) if random.random() < 0.15 else 0.0
                    
            wind_speed = round(random.uniform(2.0, 30.0), 1)
            
            weather.append({
                "WeatherID": weather_idx,
                "Date": obs_date.strftime("%Y-%m-%d"),
                "Temperature": temp,
                "Humidity": humidity,
                "Rainfall": rainfall,
                "WindSpeed": wind_speed,
                "City": city_name,
                "Country": country
            })
            weather_idx += 1
            
        df = pd.DataFrame(weather)
        self.save_data(df, output_dir, "weather", is_master=False, pk_col="WeatherID")
        print(f"Generated {num_weather} Weather Records.")
