import os
import random
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class AILabelsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_labels = self.config["sizes"]["ai_labels"]
        
        # Load electricity and fuel logs to scan for label references
        elec_path = os.path.join(output_dir, "transactional", "electricity_bills.csv")
        elec_df = pd.read_csv(elec_path)
        elec_records = elec_df[["ElectricityID", "ConsumptionKWh", "GridEmissionFactor", "RenewablePercentage", "CO2eEmission", "Status"]].to_dict("records")
        
        fuel_path = os.path.join(output_dir, "transactional", "fuel_logs.csv")
        fuel_df = pd.read_csv(fuel_path)
        fuel_records = fuel_df[["FuelLogID", "FuelVolume", "EmissionFactor", "CO2eEmission", "Status"]].to_dict("records")
        
        labels = []
        label_idx = 1
        
        # We will iterate through these tables and generate anomaly labels
        # We want to match exactly num_labels.
        # Let's take equal parts from electricity and fuel logs.
        half_labels = num_labels // 2
        
        print("Generating AI Training Labels...")
        
        # Process Electricity
        for rec in tqdm(elec_records[:half_labels]):
            eid = rec["ElectricityID"]
            cons = rec["ConsumptionKWh"]
            ef = rec["GridEmissionFactor"]
            r_pct = rec["RenewablePercentage"]
            actual = rec["CO2eEmission"]
            status = rec["Status"]
            
            expected = round(cons * ef * (1 - r_pct / 100.0), 4)
            
            # Check for anomalies
            is_anomaly = status != "Active" or abs(actual - expected) > 1.0 or actual < 0 or cons < 0
            
            if is_anomaly:
                label = "Anomaly"
                severity = "High" if abs(actual - expected) > 1000.0 or actual < 0 else "Medium"
                rc = "Grid Factor Corruption" if abs(actual - expected) > 1.0 else "Data Entry Error"
            else:
                label = "Normal"
                severity = "None"
                rc = "None"
                
            labels.append({
                "LabelID": label_idx,
                "RecordID": f"ELEC-{eid}",
                "Label": label,
                "Severity": severity,
                "ExpectedEmission": expected,
                "ActualEmission": actual,
                "RootCause": rc
            })
            label_idx += 1
            
        # Process Fuel
        for rec in tqdm(fuel_records[:(num_labels - len(labels))]):
            fid = rec["FuelLogID"]
            vol = rec["FuelVolume"]
            ef = rec["EmissionFactor"]
            actual = rec["CO2eEmission"]
            status = rec["Status"]
            
            expected = round(vol * ef, 4)
            
            is_anomaly = status != "Active" or abs(actual - expected) > 1.0 or actual < 0 or vol < 0
            
            if is_anomaly:
                label = "Anomaly"
                severity = "High" if abs(actual - expected) > 500.0 or actual < 0 else "Medium"
                rc = "Fuel Volume Outlier" if abs(actual - expected) > 1.0 else "Sensor Malfunction"
            else:
                label = "Normal"
                severity = "None"
                rc = "None"
                
            labels.append({
                "LabelID": label_idx,
                "RecordID": f"FUEL-{fid}",
                "Label": label,
                "Severity": severity,
                "ExpectedEmission": expected,
                "ActualEmission": actual,
                "RootCause": rc
            })
            label_idx += 1
            
        # Fallback if needed to exactly match target size
        while len(labels) < num_labels:
            labels.append({
                "LabelID": label_idx,
                "RecordID": f"ELEC-EXTRA-{label_idx}",
                "Label": "Normal",
                "Severity": "None",
                "ExpectedEmission": 0.0,
                "ActualEmission": 0.0,
                "RootCause": "None"
            })
            label_idx += 1
            
        df = pd.DataFrame(labels)
        self.save_data(df, output_dir, "ai_labels", is_master=False, pk_col="LabelID")
        print(f"Generated {len(df)} AI Anomaly Labels.")
