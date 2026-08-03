import os
import random
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class InvoicesGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_invoices = self.config["sizes"]["invoices"]
        
        # Load POs
        po_path = os.path.join(output_dir, "transactional", "purchase_orders.csv")
        po_df = pd.read_csv(po_path)
        po_records = po_df[["POID", "SupplierID", "PODate", "Status", "Subtotal", "Tax", "ShippingCost", "GrandTotal"]].to_dict("records")
        
        invoices = []
        invoice_idx = 1
        
        # We need exactly 500,000 invoices from 100,000 POs. That means exactly 5 invoices per PO!
        invoices_per_po = num_invoices // len(po_records)
        
        print("Generating Invoices...")
        for po in tqdm(po_records):
            po_id = po["POID"]
            supplier_id = po["SupplierID"]
            po_date_str = po["PODate"]
            po_status = po["Status"]
            
            po_date = datetime.strptime(po_date_str, "%Y-%m-%d")
            
            # Subtotals, tax, freight, grand total divided by invoices_per_po
            sub_part = round(po["Subtotal"] / invoices_per_po, 2)
            tax_part = round(po["Tax"] / invoices_per_po, 2)
            freight_part = round(po["ShippingCost"] / invoices_per_po, 2)
            discount_part = 0.0 # already factored in subtotal
            total_part = round(sub_part + tax_part + freight_part, 2)
            
            for j in range(invoices_per_po):
                inv_number = f"INV-{po_id:06d}-{j + 1}"
                inv_date = po_date + timedelta(days=random.randint(1 + j*3, 3 + j*4))
                
                # Determine payment status
                if po_status == "Closed":
                    pay_status = "Paid"
                elif po_status in ["Delivered", "Released"]:
                    pay_status = random.choice(["Paid", "Unpaid", "Partially Paid"])
                else:
                    pay_status = "Unpaid"
                    
                invoices.append({
                    "InvoiceID": invoice_idx,
                    "POID": po_id,
                    "SupplierID": supplier_id,
                    "InvoiceNumber": inv_number,
                    "InvoiceDate": inv_date.strftime("%Y-%m-%d"),
                    "PaymentStatus": pay_status,
                    "Subtotal": sub_part,
                    "GST": tax_part,
                    "Discount": discount_part,
                    "Freight": freight_part,
                    "GrandTotal": total_part
                })
                invoice_idx += 1
                
        # Remainder adjustment
        while len(invoices) < num_invoices:
            po = random.choice(po_records)
            po_id = po["POID"]
            supplier_id = po["SupplierID"]
            po_date = datetime.strptime(po["PODate"], "%Y-%m-%d")
            inv_number = f"INV-{po_id:06d}-EXTRA"
            inv_date = po_date + timedelta(days=random.randint(1, 15))
            
            invoices.append({
                "InvoiceID": invoice_idx,
                "POID": po_id,
                "SupplierID": supplier_id,
                "InvoiceNumber": inv_number,
                "InvoiceDate": inv_date.strftime("%Y-%m-%d"),
                "PaymentStatus": "Unpaid",
                "Subtotal": round(po["Subtotal"] * 0.1, 2),
                "GST": round(po["Tax"] * 0.1, 2),
                "Discount": 0.0,
                "Freight": round(po["ShippingCost"] * 0.1, 2),
                "GrandTotal": round((po["Subtotal"] + po["Tax"] + po["ShippingCost"]) * 0.1, 2)
            })
            invoice_idx += 1
            
        df = pd.DataFrame(invoices)
        self.save_data(df, output_dir, "invoices", is_master=False, pk_col="InvoiceID")
        print(f"Generated {len(df)} Invoices.")
