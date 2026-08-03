import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from tqdm import tqdm
from generators.base import BaseGenerator
from utils.helpers import get_logistics_delay

class LogisticsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        num_logistics = self.config["sizes"]["logistics"]
        
        # Load shipping manifests
        manifests_path = os.path.join(output_dir, "transactional", "shipping_manifest.csv")
        manifests_df = pd.read_csv(manifests_path)
        manifest_records = manifests_df[["ManifestID", "POID", "SupplierID", "TransportMode", "Distance", "Weight", "ShipmentDate", "ArrivalDate"]].to_dict("records")
        
        # Load vehicles, drivers, warehouses
        vehicles_path = os.path.join(output_dir, "master", "vehicles.csv")
        vehicles_df = pd.read_csv(vehicles_path)
        vehicles_records = vehicles_df[["VehicleID", "CompanyID", "VehicleType", "FuelType"]].to_dict("records")
        
        drivers_path = os.path.join(output_dir, "master", "drivers.csv")
        drivers_df = pd.read_csv(drivers_path)
        drivers_records = drivers_df[["DriverID", "CompanyID", "WarehouseID"]].to_dict("records")
        
        warehouses_path = os.path.join(output_dir, "master", "warehouses.csv")
        warehouses_df = pd.read_csv(warehouses_path)
        warehouse_records = warehouses_df[["WarehouseID", "CompanyID", "Latitude", "Longitude"]].to_dict("records")
        
        # Load POs to get CompanyID
        po_path = os.path.join(output_dir, "transactional", "purchase_orders.csv")
        po_df = pd.read_csv(po_path)
        po_company_map = po_df.set_index("POID")["CompanyID"].to_dict()
        
        # Group assets by company for quick lookups
        vehicles_by_company = {}
        for v in vehicles_records:
            cid = v["CompanyID"]
            if cid not in vehicles_by_company:
                vehicles_by_company[cid] = []
            vehicles_by_company[cid].append(v)
            
        drivers_by_company = {}
        for d in drivers_records:
            cid = d["CompanyID"]
            if cid not in drivers_by_company:
                drivers_by_company[cid] = []
            drivers_by_company[cid].append(d)
            
        warehouses_by_company = {}
        for w in warehouse_records:
            cid = w["CompanyID"]
            if cid not in warehouses_by_company:
                warehouses_by_company[cid] = []
            warehouses_by_company[cid].append(w)
            
        logistics = []
        logistics_idx = 1
        
        # We need exactly 1M records from 50k manifests, so exactly 20 logs per manifest.
        logs_per_manifest = num_logistics // len(manifest_records)
        
        print("Generating Logistics IoT Sensor Logs...")
        # To avoid memory issues and speed up execution, we process in chunks of manifests
        for m in tqdm(manifest_records):
            mid = m["ManifestID"]
            po_id = m["POID"]
            company_id = po_company_map.get(po_id, 1)
            mode = m["TransportMode"]
            total_dist = m["Distance"]
            ship_date = datetime.strptime(m["ShipmentDate"], "%Y-%m-%d")
            arr_date = datetime.strptime(m["ArrivalDate"], "%Y-%m-%d")
            duration_days = (arr_date - ship_date).days
            if duration_days <= 0:
                duration_days = 1
                
            # Get assets for this company
            comp_vehicles = vehicles_by_company.get(company_id, vehicles_records)
            comp_drivers = drivers_by_company.get(company_id, drivers_records)
            comp_warehouses = warehouses_by_company.get(company_id, warehouse_records)
            
            vehicle = random.choice(comp_vehicles)
            driver = random.choice(comp_drivers)
            warehouse = random.choice(comp_warehouses)
            
            veh_id = vehicle["VehicleID"]
            drv_id = driver["DriverID"]
            wh_id = warehouse["WarehouseID"]
            wh_lat = warehouse["Latitude"]
            wh_lon = warehouse["Longitude"]
            
            # Segment increments
            dist_step = total_dist / logs_per_manifest
            time_step_mins = (duration_days * 24 * 60) / logs_per_manifest
            
            # Average speeds based on mode
            if mode == "Air":
                avg_speed = random.uniform(600.0, 800.0)
                fuel_factor = 2.5 # kg fuel per km (air freight representation)
            elif mode == "Ocean":
                avg_speed = random.uniform(15.0, 25.0)
                fuel_factor = 0.05
            elif mode == "Rail":
                avg_speed = random.uniform(40.0, 70.0)
                fuel_factor = 0.12
            else: # Road
                avg_speed = random.uniform(50.0, 90.0)
                fuel_factor = 0.32 # Liters of diesel per km
                
            for j in range(logs_per_manifest):
                log_time = ship_date + timedelta(minutes=time_step_mins * j)
                travel_dist = round(dist_step * (j + 1), 2)
                fuel_consumed = round(dist_step * fuel_factor * random.uniform(0.9, 1.1), 2)
                
                # Check seasonality delay for monsoons/blizzards
                delay = get_logistics_delay(mode, warehouse.get("Country", "USA"), log_time)
                
                # Walk coordinates from origin towards warehouse location
                fraction = (j + 1) / logs_per_manifest
                lat = round(wh_lat + random.uniform(-2.0, 2.0) * (1 - fraction), 5)
                lon = round(wh_lon + random.uniform(-2.0, 2.0) * (1 - fraction), 5)
                
                temp = round(random.uniform(15.0, 32.0), 1)
                humidity = round(random.uniform(40.0, 85.0), 1)
                
                logistics.append({
                    "LogisticsID": logistics_idx,
                    "ManifestID": mid,
                    "VehicleID": veh_id,
                    "DriverID": drv_id,
                    "WarehouseID": wh_id,
                    "Latitude": lat,
                    "Longitude": lon,
                    "FuelConsumed": fuel_consumed,
                    "TravelDistance": travel_dist,
                    "AverageSpeed": round(avg_speed * random.uniform(0.95, 1.05), 1),
                    "DelayHours": delay,
                    "Temperature": temp,
                    "Humidity": humidity,
                    "Timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S")
                })
                logistics_idx += 1
                
        # Remainder adjustment to exactly match size
        while len(logistics) < num_logistics:
            logistics.append(logistics[-1].copy())
            logistics[-1]["LogisticsID"] = logistics_idx
            logistics_idx += 1
            
        # To avoid memory errors, we export directly using Pandas
        df = pd.DataFrame(logistics)
        self.save_data(df, output_dir, "logistics", is_master=False, pk_col="LogisticsID")
        print(f"Generated {len(df)} Logistics Records.")
