import os
import random
from faker import Faker
import pandas as pd
from generators.base import BaseGenerator
from utils.helpers import generate_gst_number

class CustomersGenerator(BaseGenerator):
    def generate(self, output_dir):
        fake = Faker()
        fake.seed_instance(self.seed)
        random.seed(self.seed)
        
        num_customers = self.config["sizes"]["customers"]
        countries = self.config["countries"]
        industries = self.config["industries"]
        
        # Load companies
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_ids = companies_df["CompanyID"].tolist()
        
        customers = []
        for i in range(num_customers):
            customer_id = i + 1
            company_id = random.choice(company_ids)
            customer_name = fake.company() + " Partners"
            industry = random.choice(industries)
            country = random.choice(countries)
            
            geo = self.settings.GEOGRAPHY_MAPPING[country]
            state_idx = random.randint(0, len(geo["states"]) - 1)
            gst = generate_gst_number(country, state_idx, self.settings)
            
            credit_limit = round(random.uniform(100000.0, 5000000.0), 2)
            risk_rating = random.choice(["Low", "Medium", "High"])
            
            customers.append({
                "CustomerID": customer_id,
                "CompanyID": company_id,
                "CustomerName": customer_name,
                "Industry": industry,
                "Country": country,
                "GST": gst,
                "CreditLimit": credit_limit,
                "RiskRating": risk_rating
            })
            
        df = pd.DataFrame(customers)
        self.save_data(df, output_dir, "customers", is_master=True, pk_col="CustomerID")
        print(f"Generated {num_customers} Customers.")
