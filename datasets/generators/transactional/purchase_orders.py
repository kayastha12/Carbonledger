import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from tqdm import tqdm
from generators.base import BaseGenerator
from utils.helpers import get_seasonal_date_distribution

class PurchaseOrdersGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        num_pos = self.config["sizes"]["purchase_orders"]
        
        # Load masters
        suppliers_path = os.path.join(output_dir, "master", "suppliers.csv")
        suppliers_df = pd.read_csv(suppliers_path)
        suppliers_records = suppliers_df[["SupplierID", "CompanyID", "Country"]].to_dict("records")
        
        products_path = os.path.join(output_dir, "master", "products.csv")
        products_df = pd.read_csv(products_path)
        product_records = products_df[["ProductID", "CompanyID", "ProductName", "ManufacturingCost", "Unit"]].to_dict("records")
        
        # Index products by CompanyID for fast lookup
        products_by_company = {}
        for p in product_records:
            cid = p["CompanyID"]
            if cid not in products_by_company:
                products_by_company[cid] = []
            products_by_company[cid].append(p)
            
        # Get dates with Q4 procurement spike seasonality
        dates = get_seasonal_date_distribution(2023, 2026, num_pos)
        
        po_list = []
        po_items_list = []
        po_item_idx = 1
        
        statuses = ["Draft", "Submitted", "Approved", "Released", "Delivered", "Closed", "Cancelled"]
        status_weights = [0.05, 0.05, 0.05, 0.05, 0.10, 0.65, 0.05]
        
        print("Generating Purchase Orders and Items...")
        for i in tqdm(range(num_pos)):
            po_id = i + 1
            
            # Select supplier and its linked company
            supplier = random.choice(suppliers_records)
            supplier_id = supplier["SupplierID"]
            company_id = supplier["CompanyID"]
            country = supplier["Country"]
            
            # Currency mapping based on country
            geo = self.settings.GEOGRAPHY_MAPPING.get(country, {"currency": "USD"})
            currency = geo["currency"]
            
            # PO Status
            status = np.random.choice(statuses, p=status_weights)
            
            # Date lifecycle
            po_date = dates[i]
            
            draft_dt = po_date
            sub_dt = draft_dt + timedelta(hours=random.randint(1, 24)) if status != "Draft" else None
            app_dt = sub_dt + timedelta(hours=random.randint(2, 48)) if status not in ["Draft", "Submitted"] else None
            rel_dt = app_dt + timedelta(hours=random.randint(1, 24)) if status not in ["Draft", "Submitted", "Approved"] else None
            deliv_dt = rel_dt + timedelta(days=random.randint(2, 14)) if status not in ["Draft", "Submitted", "Approved", "Released", "Cancelled"] else None
            closed_dt = deliv_dt + timedelta(days=random.randint(1, 7)) if status == "Closed" else None
            cancelled_dt = sub_dt + timedelta(hours=random.randint(1, 12)) if status == "Cancelled" else None
            
            # Items generation
            comp_products = products_by_company.get(company_id, [])
            if not comp_products:
                comp_products = product_records # fallback
                
            num_items = random.randint(1, 5)
            selected_products = random.choices(comp_products, k=num_items)
            
            subtotal = 0.0
            for prod in selected_products:
                qty = round(random.uniform(5.0, 500.0), 1)
                unit_price = round(prod["ManufacturingCost"] * random.uniform(0.95, 1.1), 2)
                discount = round(qty * unit_price * random.choice([0.0, 0.0, 0.05, 0.10]), 2)
                total_price = round((qty * unit_price) - discount, 2)
                
                po_items_list.append({
                    "POItemID": po_item_idx,
                    "POID": po_id,
                    "ProductID": prod["ProductID"],
                    "Quantity": qty,
                    "Unit": prod["Unit"],
                    "UnitPrice": unit_price,
                    "Discount": discount,
                    "TotalPrice": total_price
                })
                po_item_idx += 1
                subtotal += total_price
                
            subtotal = round(subtotal, 2)
            tax_rate = 0.18 if country == "India" else 0.10 # standard tax representation
            tax = round(subtotal * tax_rate, 2)
            shipping_cost = round(random.uniform(50.0, 1000.0), 2)
            grand_total = round(subtotal + tax + shipping_cost, 2)
            
            po_list.append({
                "POID": po_id,
                "CompanyID": company_id,
                "SupplierID": supplier_id,
                "PODate": draft_dt.strftime("%Y-%m-%d"),
                "ExpectedDelivery": (draft_dt + timedelta(days=10)).strftime("%Y-%m-%d"),
                "Status": status,
                "Currency": currency,
                "Subtotal": subtotal,
                "Tax": tax,
                "ShippingCost": shipping_cost,
                "GrandTotal": grand_total,
                "DraftDate": draft_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "SubmittedDate": sub_dt.strftime("%Y-%m-%d %H:%M:%S") if sub_dt else None,
                "ApprovedDate": app_dt.strftime("%Y-%m-%d %H:%M:%S") if app_dt else None,
                "ReleasedDate": rel_dt.strftime("%Y-%m-%d %H:%M:%S") if rel_dt else None,
                "DeliveredDate": deliv_dt.strftime("%Y-%m-%d %H:%M:%S") if deliv_dt else None,
                "ClosedDate": closed_dt.strftime("%Y-%m-%d %H:%M:%S") if closed_dt else None,
                "CancelledDate": cancelled_dt.strftime("%Y-%m-%d %H:%M:%S") if cancelled_dt else None
            })
            
        po_df = pd.DataFrame(po_list)
        po_items_df = pd.DataFrame(po_items_list)
        
        self.save_data(po_df, output_dir, "purchase_orders", is_master=False, pk_col="POID")
        self.save_data(po_items_df, output_dir, "purchase_order_items", is_master=False, pk_col="POItemID")
        print(f"Generated {num_pos} POs and {len(po_items_df)} PO Items.")
