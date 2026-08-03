import os
import pandas as pd
import difflib
import torch
from sentence_transformers import SentenceTransformer

class SupplierRiskModel:
    def __init__(self, 
                 suppliers_csv="d:/internship/carbonledger/datasets/output/master/suppliers.csv",
                 audits_csv="d:/internship/carbonledger/datasets/output/transactional/audits.csv"):
        self.suppliers_csv = suppliers_csv
        self.audits_csv = audits_csv
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        
        # Load contrastive matcher as base encoder
        matcher_dir = "d:/internship/carbonledger/models/saved_models/contrastive_matcher"
        if os.path.exists(matcher_dir):
            self.model = SentenceTransformer(matcher_dir)
        else:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            
        self.model.to(self.device)
        self.suppliers_df = None
        self.audits_df = None
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.suppliers_csv):
            self.suppliers_df = pd.read_csv(self.suppliers_csv)
        if os.path.exists(self.audits_csv):
            self.audits_df = pd.read_csv(self.audits_csv)

    def find_supplier_similarity(self, name_a, name_b):
        """
        Calculates semantic similarity using SentenceTransformer and lexical similarity using difflib.
        """
        with torch.no_grad():
            emb_a = self.model.encode([name_a], convert_to_tensor=True)
            emb_b = self.model.encode([name_b], convert_to_tensor=True)
            # Cosine similarity
            sem_sim = torch.nn.functional.cosine_similarity(emb_a, emb_b).item()
            
        lex_sim = difflib.SequenceMatcher(None, name_a.lower(), name_b.lower()).ratio()
        
        # Hybrid confidence score
        confidence = (0.7 * sem_sim) + (0.3 * lex_sim)
        return {
            "semantic_similarity": sem_sim,
            "lexical_similarity": lex_sim,
            "confidence_score": confidence,
            "is_duplicate": confidence > 0.88
        }

    def calculate_risk_score(self, supplier_name):
        """
        Computes a comprehensive supplier risk score (scale 0-100).
        """
        if self.suppliers_df is None or self.suppliers_df.empty:
            return {"supplier": supplier_name, "risk_score": 35.0, "emission_risk": "Medium", "country_risk": "Low"}
            
        # Match supplier details
        q = supplier_name.lower().strip()
        match = self.suppliers_df[self.suppliers_df["SupplierName"].str.lower().str.contains(q, na=False)]
        
        if match.empty:
            return {"supplier": supplier_name, "risk_score": 50.0, "emission_risk": "Medium", "country_risk": "Medium", "explanation": "Supplier not found in master records. Defaulting to baseline risk."}
            
        row = match.iloc[0]
        sup_id = row.get("SupplierID")
        country = row.get("Country", "Unknown")
        rating = float(row.get("CarbonRating", 3.0)) # scale 1-5 (5 is best)
        
        # 1. Emission Risk (based on CarbonRating)
        # Low rating (1.0) -> high risk (100). High rating (5.0) -> low risk (20)
        emission_risk_val = (6.0 - rating) * 16.0  # max 80, min 16
        
        # 2. Country Risk
        # Higher risk weights for countries with fossil-intensive grids (e.g., CN, IN, PL)
        country_risks = {
            "CN": 85.0, "IN": 90.0, "PL": 75.0, "ZA": 80.0,
            "DE": 45.0, "US": 50.0, "GB": 35.0, "FR": 20.0
        }
        country_risk_val = country_risks.get(country, 50.0)
        
        # 3. Audit/Compliance Risk
        audit_risk_val = 30.0
        if self.audits_df is not None and not self.audits_df.empty:
            sup_audits = self.audits_df[self.audits_df["SupplierID"] == sup_id]
            if not sup_audits.empty:
                # Average ESG score
                avg_esg = sup_audits["ESGScore"].mean() if "ESGScore" in sup_audits.columns else 80.0
                audit_risk_val = (100.0 - avg_esg) # high score -> low risk
                
        # Weighted aggregate risk score (out of 100)
        risk_score = (0.4 * emission_risk_val) + (0.35 * country_risk_val) + (0.25 * audit_risk_val)
        
        return {
            "supplier_id": int(sup_id),
            "supplier_name": row.get("SupplierName"),
            "country": country,
            "carbon_rating": rating,
            "risk_score": round(risk_score, 2),
            "emission_risk": "High" if emission_risk_val > 60 else "Medium" if emission_risk_val > 35 else "Low",
            "country_risk": "High" if country_risk_val > 70 else "Medium" if country_risk_val > 40 else "Low",
            "compliance_risk": "High" if audit_risk_val > 50 else "Medium" if audit_risk_val > 25 else "Low",
            "confidence_score": 0.95
        }

if __name__ == "__main__":
    model = SupplierRiskModel()
    # Check similarity
    sim = model.find_supplier_similarity("EcoSteel Corp", "EcoSteel Corporation")
    print("Similarity:", sim)
    
    # Calculate risk
    risk = model.calculate_risk_score("Supplier_1")
    import json
    print("Risk Score Detail:\n", json.dumps(risk, indent=2))
