import random
from faker import Faker
import pandas as pd
from generators.base import BaseGenerator
from utils.helpers import generate_gst_number

class CompaniesGenerator(BaseGenerator):
    def generate(self, output_dir):
        fake = Faker()
        fake.seed_instance(self.seed)
        random.seed(self.seed)
        
        num_companies = self.config["sizes"]["companies"]
        countries = self.config["countries"]
        industries = self.config["industries"]
        
        companies = []
        for i in range(num_companies):
            company_id = i + 1
            industry = random.choice(industries)
            country = random.choice(countries)
            
            # Get state & city from settings mapping
            geo = self.settings.GEOGRAPHY_MAPPING[country]
            state_idx = random.randint(0, len(geo["states"]) - 1)
            state = geo["states"][state_idx]
            city = geo["cities"][state_idx % len(geo["cities"])]
            
            # Realistic company name using industry context
            if industry == "Steel":
                suffix = "Steel Works"
            elif industry == "Aluminium":
                suffix = "Aluminium Corp"
            elif industry == "Cement":
                suffix = "Cement Materials"
            elif industry == "Chemical":
                suffix = "Chemicals Ltd"
            elif industry == "Automobile":
                suffix = "Motors"
            elif industry == "Textile":
                suffix = "Tex"
            elif industry == "Plastic":
                suffix = "Polymers"
            elif industry == "Copper":
                suffix = "Copper & Alloys"
            elif industry == "Mining":
                suffix = "Mining Resources"
            elif industry == "Food Processing":
                suffix = "Foods"
            elif industry == "Paper":
                suffix = "Paper & Pulp"
            elif industry == "Electronics":
                suffix = "Electronics Corp"
            else:
                suffix = "Machinery & Tooling"
                
            company_name = f"{fake.company()} {suffix}"
            gst = generate_gst_number(country, state_idx, self.settings)
            reg_num = f"REG-{random.randint(100000, 999999)}"
            annual_rev = round(random.uniform(50000000.0, 500000000.0), 2)
            employees = random.randint(500, 10000)
            
            # ESG features
            carbon_req = random.choice([True, False])
            net_zero_year = random.choice([2030, 2035, 2040, 2045, 2050]) if carbon_req else None
            
            companies.append({
                "CompanyID": company_id,
                "CompanyName": company_name,
                "Industry": industry,
                "Country": country,
                "State": state,
                "City": city,
                "GSTNumber": gst,
                "RegistrationNumber": reg_num,
                "AnnualRevenue": annual_rev,
                "Employees": employees,
                "CarbonReportingRequired": carbon_req,
                "NetZeroTargetYear": net_zero_year
            })
            
        df = pd.DataFrame(companies)
        self.save_data(df, output_dir, "companies", is_master=True, pk_col="CompanyID")
        print(f"Generated {num_companies} Companies.")
