import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

def train_recommender():
    print("Preparing recommendation datasets...")
    suppliers_csv = "d:/internship/carbonledger/datasets/output/master/suppliers.csv"
    
    if not os.path.exists(suppliers_csv):
        print("Suppliers master dataset not found. Skipping training.")
        return
        
    df_sups = pd.read_csv(suppliers_csv)
    
    # We will build synthetic training features for alternative supplier recommendations
    # Features: Rating difference, distance, price difference, esg score diff
    # Target: CO2 reduction percentage, ROI percentage
    np.random.seed(42)
    n_samples = 1000
    
    rating_diff = np.random.uniform(0.5, 4.0, n_samples)
    price_diff = np.random.uniform(-10.0, 30.0, n_samples) # price difference percentage
    esg_diff = np.random.uniform(5.0, 40.0, n_samples)
    distance_km = np.random.uniform(50.0, 2000.0, n_samples)
    
    # Calculate target variables based on physical formulas
    co2_reduction_pct = rating_diff * 12.5 + np.random.normal(0, 2, n_samples)
    co2_reduction_pct = np.clip(co2_reduction_pct, 5.0, 75.0)
    
    # ROI: cost savings over implementation cost
    roi_pct = (co2_reduction_pct * 1.5) - (price_diff * 0.8) + np.random.normal(0, 5, n_samples)
    roi_pct = np.clip(roi_pct, -10.0, 150.0)
    
    X = pd.DataFrame({
        "rating_diff": rating_diff,
        "price_diff": price_diff,
        "esg_diff": esg_diff,
        "distance_km": distance_km
    })
    
    # Train regressors for CO2 reduction and ROI
    model_co2 = RandomForestRegressor(n_estimators=50, random_state=42)
    model_roi = RandomForestRegressor(n_estimators=50, random_state=42)
    
    model_co2.fit(X, co2_reduction_pct)
    model_roi.fit(X, roi_pct)
    
    model_dir = "d:/internship/carbonledger/models/saved_models/recommendation"
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(model_co2, os.path.join(model_dir, "recommender_co2.pkl"))
    joblib.dump(model_roi, os.path.join(model_dir, "recommender_roi.pkl"))
    print("Recommendation ranker models saved successfully!")

if __name__ == "__main__":
    train_recommender()
