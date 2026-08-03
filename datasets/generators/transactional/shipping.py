import os
import random
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator
from utils.helpers import generate_container_number

class ShippingManifestGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_manifests = self.config["sizes"]["shipping_manifest"]
        
        # Load invoices
        invoices_path = os.path.join(output_dir, "transactional", "invoices.csv")
        invoices_df = pd.read_csv(invoices_path)
        invoice_records = invoices_df[["InvoiceID", "POID", "SupplierID", "InvoiceDate"]].to_dict("records")
        
        # Load suppliers and companies to resolve countries
        suppliers_path = os.path.join(output_dir, "master", "suppliers.csv")
        suppliers_df = pd.read_csv(suppliers_path)
        supplier_map = suppliers_df.set_index("SupplierID")[["Country", "CompanyID"]].to_dict("index")
        
        companies_path = os.path.join(output_dir, "master", "companies.csv")
        companies_df = pd.read_csv(companies_path)
        company_map = companies_df.set_index("CompanyID")["Country"].to_dict()
        
        # We need to choose exactly num_manifests (50,000) invoices to link.
        # Let's take a slice or random sample of invoices.
        sample_invoices = random.sample(invoice_records, num_manifests)
        
        shipping = []
        manifest_idx = 1
        
        print("Generating Shipping Manifests...")
        for inv in tqdm(sample_invoices):
            inv_id = inv["InvoiceID"]
            po_id = inv["POID"]
            supplier_id = inv["SupplierID"]
            inv_date_str = inv["InvoiceDate"]
            inv_date = datetime.strptime(inv_date_str, "%Y-%m-%d")
            
            supp_info = supplier_map.get(supplier_id, {"Country": "India", "CompanyID": 1})
            origin_country = supp_info["Country"]
            company_id = supp_info["CompanyID"]
            dest_country = company_map.get(company_id, "USA")
            
            # Select port from destination country
            geo = self.settings.GEOGRAPHY_MAPPING.get(dest_country, {"ports": ["Port of NY/NJ"]})
            port = random.choice(geo["ports"])
            
            # Transport Mode based on geography
            is_same_continent = False
            european_countries = ["Germany", "UK", "France", "Italy", "Turkey"]
            asian_countries = ["India", "China", "Japan", "South Korea", "Vietnam", "Thailand", "UAE"]
            american_countries = ["USA", "Canada", "Brazil"]
            
            if origin_country in european_countries and dest_country in european_countries:
                is_same_continent = True
            elif origin_country in asian_countries and dest_country in asian_countries:
                is_same_continent = True
            elif origin_country in american_countries and dest_country in american_countries:
                is_same_continent = True
                
            if is_same_continent:
                mode = random.choice(["Road", "Rail", "Air"])
                dist = random.uniform(200.0, 2500.0)
            else:
                mode = random.choice(["Ocean", "Ocean", "Ocean", "Air"]) # Ocean heavy
                dist = random.uniform(3000.0, 15000.0)
                
            container_num = generate_container_number() if mode == "Ocean" else "N/A (Air/Road)"
            weight = round(random.uniform(500.0, 24000.0), 2)
            
            ship_date = inv_date - timedelta(days=random.randint(1, 3))
            
            # Transittime
            if mode == "Ocean":
                transit = random.randint(14, 35)
            elif mode == "Rail":
                transit = random.randint(4, 9)
            elif mode == "Road":
                transit = random.randint(1, 4)
            else: # Air
                transit = random.randint(1, 2)
                
            arrival_date = ship_date + timedelta(days=transit)
            
            shipping.append({
                "ManifestID": manifest_idx,
                "InvoiceID": inv_id,
                "POID": po_id,
                "SupplierID": supplier_id,
                "OriginCountry": origin_country,
                "DestinationCountry": dest_country,
                "Port": port,
                "TransportMode": mode,
                "ContainerNumber": container_num,
                "Weight": weight,
                "Distance": round(dist, 2),
                "ShipmentDate": ship_date.strftime("%Y-%m-%d"),
                "ArrivalDate": arrival_date.strftime("%Y-%m-%d")
            })
            manifest_idx += 1
            
        df = pd.DataFrame(shipping)
        self.save_data(df, output_dir, "shipping_manifest", is_master=False, pk_col="ManifestID")
        print(f"Generated {len(df)} Shipping Manifests.")
