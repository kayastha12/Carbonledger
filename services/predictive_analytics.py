import os
import json
import torch

class PredictiveAnalyticsService:
    def __init__(self):
        # Default baseline stats
        self.annual_emissions_co2_kg = 62000.0
        self.cbam_cost_euro = 18240.0

    def predict_future_emissions(self, months_ahead=6):
        forecaster_dir = "d:/internship/carbonledger/models/saved_models/forecaster"
        lstm_path = os.path.join(forecaster_dir, "lstm_forecaster.pt")
        scaler_path = os.path.join(forecaster_dir, "scaler_params.json")
        
        if os.path.exists(lstm_path) and os.path.exists(scaler_path):
            try:
                import torch.nn as nn
                class LSTMForecaster(nn.Module):
                    def __init__(self, input_dim=1, hidden_dim=16, num_layers=1, output_dim=1):
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
                
                with open(scaler_path, "r") as f:
                    scaler = json.load(f)
                
                device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
                model = LSTMForecaster(input_dim=1, hidden_dim=16, num_layers=1, output_dim=1)
                model.load_state_dict(torch.load(lstm_path, map_location=device))
                model.to(device)
                model.eval()
                
                history = [20000.0, 22000.0, 21500.0, 23000.0, 24500.0, 24000.0]
                mean = scaler["mean"]
                std = scaler["std"]
                
                predictions = []
                current_seq = [(x - mean) / std for x in history]
                
                for _ in range(months_ahead):
                    input_tensor = torch.tensor(current_seq[-6:], dtype=torch.float32).unsqueeze(0).unsqueeze(-1).to(device)
                    with torch.no_grad():
                        pred_scaled = model(input_tensor).item()
                    predictions.append(pred_scaled * std + mean)
                    current_seq.append(pred_scaled)
                    
                return {
                    "status": "success",
                    "historical": history,
                    "forecast": [round(x, 1) for x in predictions],
                    "months": ["Month +1", "Month +2", "Month +3", "Month +4", "Month +5", "Month +6"]
                }
            except Exception as e:
                print("LSTM prediction error:", e)
                
        return {
            "status": "fallback",
            "historical": [20000.0, 22000.0, 21500.0, 23000.0, 24500.0, 24000.0],
            "forecast": [24500.0, 25000.0, 25800.0, 26200.0, 27000.0, 27500.0],
            "months": ["Month +1", "Month +2", "Month +3", "Month +4", "Month +5", "Month +6"]
        }

    def run_what_if_scenario(self, strategy_name):
        """
        Simulates the carbon, tariff, and financial changes of decapping strategies.
        Strategies: 'rail_freight', 'eaf_steel', 'green_energy_tariff'
        """
        baseline_footprint = self.annual_emissions_co2_kg
        baseline_tariff = self.cbam_cost_euro
        
        if strategy_name == "rail_freight":
            reduction_pct = 75.0
            capital_cost = 5000.0
            operational_saving = 1200.0
        elif strategy_name == "eaf_steel":
            reduction_pct = 32.5
            capital_cost = 15000.0
            operational_saving = -2000.0 # slight premium
        elif strategy_name == "green_energy_tariff":
            reduction_pct = 60.0
            capital_cost = 2000.0
            operational_saving = 800.0
        else:
            return {"status": "error", "message": f"Unknown strategy: {strategy_name}"}
            
        new_footprint = baseline_footprint * (1.0 - (reduction_pct / 100.0))
        # CBAM cost falls proportionally to direct emissions reductions
        new_tariff = baseline_tariff * (1.0 - (reduction_pct / 100.0))
        
        annual_financial_benefit = (baseline_tariff - new_tariff) + operational_saving
        roi_pct = (annual_financial_benefit / capital_cost) * 100.0 if capital_cost > 0 else 0.0
        payback_years = capital_cost / annual_financial_benefit if annual_financial_benefit > 0 else float('inf')
        
        return {
            "strategy": strategy_name,
            "annual_co2_reduction_kg": round(baseline_footprint - new_footprint, 1),
            "co2_reduction_pct": reduction_pct,
            "new_annual_co2_kg": round(new_footprint, 1),
            "new_cbam_cost_euro": round(new_tariff, 2),
            "tariff_savings_euro": round(baseline_tariff - new_tariff, 2),
            "capital_cost_euro": capital_cost,
            "estimated_annual_roi_pct": round(roi_pct, 2),
            "payback_period_years": round(payback_years, 2)
        }

if __name__ == "__main__":
    predictor = PredictiveAnalyticsService()
    res = predictor.run_what_if_scenario("rail_freight")
    import json
    print(json.dumps(res, indent=2))
