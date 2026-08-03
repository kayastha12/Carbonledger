import random
from datetime import datetime, timedelta
import pandas as pd
from generators.base import BaseGenerator

class ExchangeRatesGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)
        total_days = (end_date - start_date).days
        
        currencies = ["USD", "EUR", "INR", "JPY", "CNY"]
        # Standard average exchange rates against USD
        base_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "INR": 83.12,
            "JPY": 145.50,
            "CNY": 7.15
        }
        
        rates = []
        rate_idx = 1
        
        # Generate daily rates for each currency
        for d in range(total_days + 1):
            cur_date = start_date + timedelta(days=d)
            date_str = cur_date.strftime("%Y-%m-%d")
            
            for currency in currencies:
                # Add tiny daily random walk/fluctuations to make rates dynamic
                walk = random.uniform(-0.01, 0.01) * base_rates[currency]
                rate = round(base_rates[currency] + walk, 4)
                if currency == "USD":
                    rate = 1.0 # USD remains base
                    
                rates.append({
                    "ExchangeRateID": rate_idx,
                    "Currency": currency,
                    "ExchangeRate": rate,
                    "Date": date_str
                })
                rate_idx += 1
                
        df = pd.DataFrame(rates)
        self.save_data(df, output_dir, "exchange_rates", is_master=False, pk_col="ExchangeRateID")
        print(f"Generated {len(df)} Exchange Rates.")
