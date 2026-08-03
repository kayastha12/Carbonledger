import os
import random
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class CBAMReportingGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_cbam = self.config["sizes"]["cbam_reporting"]
        
        # Load products (filter for CBAM categories: Steel, Aluminium, Cement)
        products_path = os.path.join(output_dir, "master", "products.csv")
        products_df = pd.read_csv(products_path)
        cbam_categories = ["Steel", "Aluminium", "Cement"]
        cbam_products = products_df[products_df["Category"].isin(cbam_categories)].to_dict("records")
        
        if not cbam_products:
            # fallback
            cbam_products = products_df.to_dict("records")
            
        # Load invoices
        invoices_path = os.path.join(output_dir, "transactional", "invoices.csv")
        invoices_df = pd.read_csv(invoices_path)
        invoice_records = invoices_df[["InvoiceID", "POID", "SupplierID", "InvoiceDate", "Subtotal"]].to_dict("records")
        
        # Load POs to get CompanyID
        po_path = os.path.join(output_dir, "transactional", "purchase_orders.csv")
        po_df = pd.read_csv(po_path)
        po_company_map = po_df.set_index("POID")["CompanyID"].to_dict()
        
        # Sample invoices to build reports
        sample_invoices = random.choices(invoice_records, k=num_cbam)
        
        cbam = []
        cbam_idx = 1
        
        print("Generating CBAM Reporting Records...")
        for inv in tqdm(sample_invoices):
            inv_id = inv["InvoiceID"]
            po_id = inv["POID"]
            supplier_id = inv["SupplierID"]
            company_id = po_company_map.get(po_id, 1)
            
            # Select CBAM product
            prod = random.choice(cbam_products)
            prod_id = prod["ProductID"]
            
            # Direct emissions = material weight * standard emission factor
            weight_tonnes = random.uniform(5.0, 100.0)
            direct_em = round(weight_tonnes * prod["StandardEmissionFactor"], 3)
            
            # Indirect emissions (electricity overhead during fabrication)
            indirect_em = round(direct_em * random.uniform(0.1, 0.35), 3)
            embedded_em = round(direct_em + indirect_em, 3)
            
            # EU ETS Carbon price (USD per metric ton of CO2)
            carbon_price = round(random.uniform(80.0, 110.0), 2)
            
            # Resolve Reporting Quarter based on invoice date
            inv_date = datetime.strptime(inv["InvoiceDate"], "%Y-%m-%d")
            quarter = (inv_date.month - 1) // 3 + 1
            reporting_quarter = f"{inv_date.year}-Q{quarter}"
            
            cbam.append({
                "CBAMID": cbam_idx,
                "CompanyID": company_id,
                "SupplierID": supplier_id,
                "ProductID": prod_id,
                "InvoiceID": inv_id,
                "EmbeddedEmission": embedded_em,
                "DirectEmission": direct_em,
                "IndirectEmission": indirect_em,
                "CarbonPrice": carbon_price,
                "ReportingQuarter": reporting_quarter,
                "VerificationStatus": random.choice(["Verified", "Verified", "Pending", "Disputed"]),
                "SubmissionStatus": random.choice(["Submitted", "Submitted", "Approved", "Draft"])
            })
            cbam_idx += 1
            
        df = pd.DataFrame(cbam)
        self.save_data(df, output_dir, "cbam_reporting", is_master=False, pk_col="CBAMID")
        print(f"Generated {len(df)} CBAM Reporting Records.")
