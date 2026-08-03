import os
import random
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class ERPExportGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_erp = self.config["sizes"]["erp_export"]
        
        # Load invoices
        invoices_path = os.path.join(output_dir, "transactional", "invoices.csv")
        invoices_df = pd.read_csv(invoices_path)
        invoice_records = invoices_df[["InvoiceID", "POID", "InvoiceDate", "Subtotal", "GrandTotal"]].to_dict("records")
        
        # Load POs to get CompanyID and Currency
        po_path = os.path.join(output_dir, "transactional", "purchase_orders.csv")
        po_df = pd.read_csv(po_path)
        po_map = po_df.set_index("POID")[["CompanyID", "Currency"]].to_dict("index")
        
        # Load products to get SKUs
        products_path = os.path.join(output_dir, "master", "products.csv")
        products_df = pd.read_csv(products_path)
        products_by_company = {}
        for p in products_df[["ProductID", "CompanyID", "SKU"]].to_dict("records"):
            cid = p["CompanyID"]
            if cid not in products_by_company:
                products_by_company[cid] = []
            products_by_company[cid].append(p["SKU"])
            
        gl_codes = list(self.settings.GL_ACCOUNTS.keys())
        cost_centers = self.settings.COST_CENTERS
        
        erp = []
        erp_idx = 1
        
        print("Generating ERP Export...")
        for inv in tqdm(invoice_records):
            inv_id = inv["InvoiceID"]
            po_id = inv["POID"]
            
            po_info = po_map.get(po_id, {"CompanyID": 1, "Currency": "USD"})
            company_id = po_info["CompanyID"]
            currency = po_info["Currency"]
            
            # Select SKU of a product owned by the company
            company_skus = products_by_company.get(company_id, ["SKU-DEFAULT"])
            sku = random.choice(company_skus)
            
            gl_account = random.choice(gl_codes)
            cost_center = random.choice(cost_centers)
            posting_date = inv["InvoiceDate"]
            
            qty = round(random.uniform(5.0, 100.0), 1)
            amount = inv["Subtotal"]
            
            erp.append({
                "ERPID": erp_idx,
                "CompanyID": company_id,
                "InvoiceID": inv_id,
                "POID": po_id,
                "GLAccount": gl_account,
                "CostCenter": cost_center,
                "PostingDate": posting_date,
                "MaterialCode": sku,
                "Quantity": qty,
                "Amount": amount,
                "Currency": currency
            })
            erp_idx += 1
            
        df = pd.DataFrame(erp)
        self.save_data(df, output_dir, "erp_export", is_master=False, pk_col="ERPID")
        print(f"Generated {len(df)} ERP Export Records.")
