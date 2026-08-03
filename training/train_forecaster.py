import os
import json
import torch
import torch.nn as nn
import pandas as pd
import numpy as np

class LSTMForecaster(nn.Module):
    def __init__(self, input_dim=1, hidden_dim=32, num_layers=2, output_dim=1):
        super(LSTMForecaster, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.linear(out[:, -1, :])
        return out

def train_forecaster():
    print("Preparing time-series forecasting data...")
    logistics_csv = r"d:\internship\carbonledger\datasets\output\transactional\logistics.csv"
    
    use_simulated = True
    if os.path.exists(logistics_csv):
        try:
            # Check columns first
            df_sample = pd.read_csv(logistics_csv, nrows=5)
            print("Columns in logistics.csv:", df_sample.columns.tolist())
            
            # Find date column and emissions column
            date_col = None
            emissions_col = None
            for c in df_sample.columns:
                if "date" in c.lower():
                    date_col = c
                if "emission" in c.lower() or "co2" in c.lower():
                    emissions_col = c
                    
            if date_col and emissions_col:
                print(f"Using date column '{date_col}' and emissions column '{emissions_col}'")
                # Read dataset
                df_log = pd.read_csv(logistics_csv, usecols=[date_col, emissions_col])
                df_log["Date"] = pd.to_datetime(df_log[date_col]).dt.to_period("M").dt.to_timestamp()
                df_monthly = df_log.groupby("Date")[emissions_col].sum().reset_index()
                df_monthly.columns = ["Date", "co2e"]
                use_simulated = False
        except Exception as e:
            print("Error reading logistics.csv:", e)
            
    if use_simulated:
        print("Using simulated time-series emissions data...")
        dates = pd.date_range(start="2023-01-01", end="2026-12-01", freq="MS")
        # Generate trend + seasonality + noise
        t = np.arange(len(dates))
        emissions = 20000.0 + 500.0 * t + 5000.0 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 1000, len(dates))
        df_monthly = pd.DataFrame({"Date": dates, "co2e": emissions})
        
    data = df_monthly["co2e"].values.astype(np.float32)
    
    # Scale data
    mean = data.mean()
    std = data.std() if data.std() > 0 else 1.0
    scaled_data = (data - mean) / std
    
    # Prepare sequence dataset
    seq_length = 6
    x_seq = []
    y_seq = []
    for i in range(len(scaled_data) - seq_length):
        x_seq.append(scaled_data[i:i+seq_length])
        y_seq.append(scaled_data[i+seq_length])
        
    if len(x_seq) == 0:
        x_seq = [np.zeros(seq_length, dtype=np.float32)]
        y_seq = [0.0]
        
    x_tensor = torch.tensor(x_seq, dtype=torch.float32).unsqueeze(-1)
    y_tensor = torch.tensor(y_seq, dtype=torch.float32).unsqueeze(-1)
    
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print(f"Using device: {device}")
    
    model = LSTMForecaster(input_dim=1, hidden_dim=16, num_layers=1, output_dim=1)
    model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    
    # Train
    print("Training PyTorch LSTM Forecaster...")
    model.train()
    x_tensor, y_tensor = x_tensor.to(device), y_tensor.to(device)
    for epoch in range(10):
        optimizer.zero_grad()
        preds = model(x_tensor)
        loss = criterion(preds, y_tensor)
        loss.backward()
        optimizer.step()
        if (epoch+1) % 2 == 0:
            print(f"Epoch {epoch+1} | Loss: {loss.item():.4f}")
            
    # Save model
    model_dir = "d:/internship/carbonledger/models/saved_models/forecaster"
    os.makedirs(model_dir, exist_ok=True)
    
    torch.save(model.state_dict(), os.path.join(model_dir, "lstm_forecaster.pt"))
    with open(os.path.join(model_dir, "scaler_params.json"), "w") as f:
        json.dump({"mean": float(mean), "std": float(std), "seq_length": seq_length}, f, indent=2)
        
    print("Forecasting LSTM model saved successfully!")

if __name__ == "__main__":
    train_forecaster()
