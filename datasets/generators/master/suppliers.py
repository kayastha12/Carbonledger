import os
import random
from faker import Faker
import pandas as pd
from generators.base import BaseGenerator
from utils.helpers import generate_gst_number, generate_phone_number, generate_email

class SuppliersGenerator(BaseGenerator):
    def generate(self, output_dir):
        fake = Faker()
        fake.seed_instance(self.seed)
        random.seed(self.seed)
        
        num_suppliers = self.config["sizes"]["suppliers"]
        countries = self.config["countries"]
        
        # Load companies master to link them
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_ids = companies_df["CompanyID"].tolist()
        
        material_categories = list(self.settings.EMISSION_FACTORS["material"].keys())
        
        suppliers = []
        for i in range(num_suppliers):
            supplier_id = i + 1
            company_id = random.choice(company_ids)
            
            # Vendor country can be different from company country or same
            country = random.choice(countries)
            geo = self.settings.GEOGRAPHY_MAPPING[country]
            state_idx = random.randint(0, len(geo["states"]) - 1)
            state = geo["states"][state_idx]
            city = geo["cities"][state_idx % len(geo["cities"])]
            
            supplier_name = f"{fake.company()} Logistics & Materials"
            email = generate_email(supplier_name, "supplier-portal.org")
            phone = generate_phone_number(country)
            
            supplier_cat = random.choice(["Raw Material Provider", "Logistics partner", "Utility supplier", "Subcontractor"])
            mat_cat = random.choice(material_categories)
            
            rating = round(random.uniform(3.0, 5.0), 1)
            # EmissionScore (lower is better, e.g. kg CO2e / unit)
            emission_score = round(random.uniform(0.5, 12.0), 2)
            payment_terms = random.choice(["Net 30", "Net 45", "Net 60", "Due on Receipt"])
            gst = generate_gst_number(country, state_idx, self.settings)
            
            suppliers.append({
                "SupplierID": supplier_id,
                "CompanyID": company_id,
                "SupplierName": supplier_name,
                "Country": country,
                "State": state,
                "City": city,
                "Email": email,
                "Phone": phone,
                "SupplierCategory": supplier_cat,
                "MaterialCategory": mat_cat,
                "SupplierRating": rating,
                "EmissionScore": emission_score,
                "PaymentTerms": payment_terms,
                "GSTNumber": gst
            })
            
        df = pd.DataFrame(suppliers)
        self.save_data(df, output_dir, "suppliers", is_master=True, pk_col="SupplierID")
        print(f"Generated {num_suppliers} Suppliers.")
