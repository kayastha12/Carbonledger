import os
import random
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class DocumentsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_docs = self.config["sizes"]["documents"]
        
        # Load transactional data to link
        po_path = os.path.join(output_dir, "transactional", "purchase_orders.csv")
        po_df = pd.read_csv(po_path)
        po_records = po_df[["POID", "CompanyID", "SupplierID", "PODate", "GrandTotal"]].to_dict("records")
        
        inv_path = os.path.join(output_dir, "transactional", "invoices.csv")
        inv_df = pd.read_csv(inv_path)
        inv_records = inv_df[["InvoiceID", "POID", "SupplierID", "InvoiceDate", "GrandTotal"]].to_dict("records")
        
        doc_types = ["Purchase Order", "Invoice", "Bill of Lading", "Packing List", "Electricity Bill", "Water Bill", "Fuel Receipt"]
        
        documents = []
        doc_idx = 1
        
        print("Generating ERP Documents OCR Text...")
        for i in tqdm(range(num_docs)):
            doc_type = random.choice(doc_types)
            
            # Resolve companies & suppliers
            if doc_type in ["Purchase Order", "Packing List"]:
                ref = random.choice(po_records)
                cid = ref["CompanyID"]
                sid = ref["SupplierID"]
                date = ref["PODate"]
                amount = ref["GrandTotal"]
                ref_num = f"PO-{ref['POID']}"
            elif doc_type in ["Invoice", "Bill of Lading"]:
                ref = random.choice(inv_records)
                cid = random.choice(po_records)["CompanyID"] # fallback
                # Find matching PO
                po_info = po_df[po_df["POID"] == ref["POID"]]
                if len(po_info) > 0:
                    cid = int(po_info["CompanyID"].values[0])
                sid = ref["SupplierID"]
                date = ref["InvoiceDate"]
                amount = ref["GrandTotal"]
                ref_num = f"INV-{ref['InvoiceID']}"
            else: # Bills & receipts
                ref = random.choice(po_records) # fallback for IDs
                cid = ref["CompanyID"]
                sid = ref["SupplierID"]
                date = ref["PODate"]
                amount = round(random.uniform(500.0, 5000.0), 2)
                ref_num = f"UTIL-{random.randint(1000, 9999)}"
                
            lang = random.choice(["English", "English", "English", "German", "French"])
            quality = round(random.uniform(0.75, 0.99), 2)
            
            # Generate OCR Text
            ocr_text = (
                f"=== CarbonLedger ERP Document ===\n"
                f"Document Type: {doc_type}\n"
                f"Reference Number: {ref_num}\n"
                f"Date: {date}\n"
                f"Company ID: {cid}\n"
                f"Supplier ID: {sid}\n"
                f"Total Value: {amount}\n"
                f"Verification Status: Processed\n"
                f"OCR Quality Score: {quality}\n"
                f"Language: {lang}\n"
            )
            
            # File name and path
            safe_type = doc_type.replace(" ", "_").lower()
            file_name = f"{safe_type}_{ref_num}_{date[:4]}.pdf"
            file_path = f"/var/erp/documents/{safe_type}/{file_name}"
            
            documents.append({
                "DocumentID": doc_idx,
                "CompanyID": cid,
                "SupplierID": sid,
                "DocumentType": doc_type,
                "OCRText": ocr_text.replace("\n", " | "), # flatten for CSV compatibility
                "Language": lang,
                "FileName": file_name,
                "FilePath": file_path,
                "QualityScore": quality
            })
            doc_idx += 1
            
        df = pd.DataFrame(documents)
        self.save_data(df, output_dir, "documents", is_master=False, pk_col="DocumentID")
        print(f"Generated {len(df)} Documents.")
