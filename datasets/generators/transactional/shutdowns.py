import os
import random
from datetime import datetime, timedelta
import pandas as pd
from generators.base import BaseGenerator

class ShutdownsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_shutdowns = self.config["sizes"].get("shutdowns", 2000)
        
        # Load plants
        plants_path = os.path.join(output_dir, "master", "plants.csv")
        plants_df = pd.read_csv(plants_path)
        plant_ids = plants_df["PlantID"].tolist()
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)
        total_days = (end_date - start_date).days
        
        reasons = ["Flood", "Strike", "Maintenance", "Power Failure"]
        
        shutdowns = []
        for i in range(num_shutdowns):
            shutdown_id = i + 1
            plant_id = random.choice(plant_ids)
            
            day_offset = random.randint(0, total_days - 5)
            s_date = start_date + timedelta(days=day_offset)
            duration = random.randint(1, 5)
            e_date = s_date + timedelta(days=duration)
            
            reason = random.choice(reasons)
            prod_loss = round(random.uniform(5000.0, 50000.0) * duration, 2)
            
            shutdowns.append({
                "ShutdownID": shutdown_id,
                "PlantID": plant_id,
                "StartDate": s_date.strftime("%Y-%m-%d"),
                "EndDate": e_date.strftime("%Y-%m-%d"),
                "Reason": reason,
                "ProductionLoss": prod_loss
            })
            
        df = pd.DataFrame(shutdowns)
        self.save_data(df, output_dir, "shutdowns", is_master=False, pk_col="ShutdownID")
        print(f"Generated {num_shutdowns} Shutdown Events.")
