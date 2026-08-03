import os
import random
from datetime import datetime, timedelta
import pandas as pd
from generators.base import BaseGenerator

class SupplierAuditsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_audits = self.config["sizes"]["supplier_audits"]
        
        # Load suppliers
        suppliers_path = os.path.join(output_dir, "master", "suppliers.csv")
        suppliers_df = pd.read_csv(suppliers_path)
        supplier_ids = suppliers_df["SupplierID"].tolist()
        
        auditors = ["SGS Carbon Verification", "TUV SUD ESG Division", "Bureau Veritas", "Intertek Sustainability", "CarbonLedger Internal auditor"]
        
        findings_pool = [
            "Minor discrepancy in Scope 2 billing verification.",
            "Fully compliant ESG systems and documentation.",
            "Insufficient tracking of logistics fuel emissions.",
            "Water treatment plant operational but minor waste logs missing.",
            "Exemplary sustainability program and carbon tracking."
        ]
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)
        total_days = (end_date - start_date).days
        
        audits = []
        for i in range(num_audits):
            audit_id = i + 1
            supplier_id = random.choice(supplier_ids)
            
            day_offset = random.randint(0, total_days)
            a_date = start_date + timedelta(days=day_offset)
            
            auditor = random.choice(auditors)
            score = round(random.uniform(55.0, 100.0), 1)
            
            if score >= 85:
                risk = "Low"
                finding = findings_pool[4] if random.random() < 0.5 else findings_pool[1]
                status = "Passed"
            elif score >= 70:
                risk = "Medium"
                finding = random.choice([findings_pool[0], findings_pool[3]])
                status = "Passed with Conditions"
            else:
                risk = "High"
                finding = findings_pool[2]
                status = "Failed"
                
            audits.append({
                "AuditID": audit_id,
                "SupplierID": supplier_id,
                "AuditDate": a_date.strftime("%Y-%m-%d"),
                "Auditor": auditor,
                "ComplianceScore": score,
                "RiskLevel": risk,
                "Findings": finding,
                "Status": status
            })
            
        df = pd.DataFrame(audits)
        self.save_data(df, output_dir, "audits", is_master=False, pk_col="AuditID")
        print(f"Generated {num_audits} Supplier ESG Audits.")
