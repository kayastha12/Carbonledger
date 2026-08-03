import os
import random
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class PaymentsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_payments = self.config["sizes"]["payments"]
        
        # Load invoices
        invoices_path = os.path.join(output_dir, "transactional", "invoices.csv")
        invoices_df = pd.read_csv(invoices_path)
        invoice_records = invoices_df[["InvoiceID", "InvoiceDate", "PaymentStatus", "GrandTotal"]].to_dict("records")
        
        banks = ["HSBC", "Citi", "J.P. Morgan", "Deutsche Bank", "State Bank of India", "Industrial and Commercial Bank of China", "MUFG Bank"]
        methods = ["ACH", "Wire Transfer", "Credit Card", "Bank Draft"]
        
        payments = []
        payment_idx = 1
        
        print("Generating Payments...")
        for inv in tqdm(invoice_records):
            inv_id = inv["InvoiceID"]
            inv_date_str = inv["InvoiceDate"]
            pay_status = inv["PaymentStatus"]
            grand_total = inv["GrandTotal"]
            
            inv_date = datetime.strptime(inv_date_str, "%Y-%m-%d")
            pay_date = inv_date + timedelta(days=random.randint(1, 15))
            
            bank = random.choice(banks)
            method = random.choice(methods)
            tx_ref = f"TXN-{random.randint(10000000, 99999999)}"
            
            if pay_status == "Paid":
                amount = grand_total
                status = "Success"
            elif pay_status == "Partially Paid":
                amount = round(grand_total * 0.5, 2)
                status = "Success"
            else: # Unpaid
                amount = 0.0
                status = random.choice(["Failed", "Pending"])
                
            payments.append({
                "PaymentID": payment_idx,
                "InvoiceID": inv_id,
                "PaymentMethod": method,
                "Bank": bank,
                "Amount": amount,
                "PaymentDate": pay_date.strftime("%Y-%m-%d"),
                "TransactionReference": tx_ref,
                "PaymentStatus": status
            })
            payment_idx += 1
            
        df = pd.DataFrame(payments)
        self.save_data(df, output_dir, "payments", is_master=False, pk_col="PaymentID")
        print(f"Generated {len(df)} Payments.")
