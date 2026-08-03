import os
import pandas as pd
import difflib
import numpy as np
from sentence_transformers import SentenceTransformer
from vector_db.chroma_service import ChromaService

class MatchingService:
    def __init__(self, chroma_service=None, suppliers_csv_path="d:/internship/carbonledger/datasets/output/master/suppliers.csv"):
        self.chroma = chroma_service if chroma_service else ChromaService()
        self.suppliers_csv = suppliers_csv_path
        self.supplier_master = []
        
        # Load SentenceTransformer for Supplier matching
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder="d:/internship/carbonledger/models/pretrained/all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Warning: SentenceTransformer load for supplier matcher failed ({e})")
            self.model = None
            
        self._load_suppliers()

    def _load_suppliers(self):
        if os.path.exists(self.suppliers_csv):
            try:
                df = pd.read_csv(self.suppliers_csv)
                if "SupplierName" in df.columns:
                    self.supplier_master = df["SupplierName"].dropna().unique().tolist()
                elif "Name" in df.columns:
                    self.supplier_master = df["Name"].dropna().unique().tolist()
                else:
                    self.supplier_master = []
            except Exception as e:
                print("Error loading suppliers:", e)

    def match_supplier(self, query_name, threshold=0.6):
        """
        Match a supplier using a hybrid of Semantic (SentenceTransformer) and Lexical (fuzzy) matching.
        """
        if not self.supplier_master or not query_name:
            return {"matched_name": query_name, "confidence": 1.0, "is_duplicate": False, "status": "Matched (Default)"}
            
        q = str(query_name).strip().lower()
        
        best_match = None
        best_score = 0.0
        
        # Encode master and query if model is available
        q_emb = None
        master_embs = None
        if self.model:
            try:
                q_emb = self.model.encode([query_name])[0]
                master_embs = self.model.encode(self.supplier_master)
            except Exception:
                pass
                
        duplicates = []
        for idx, name in enumerate(self.supplier_master):
            lex_sim = difflib.SequenceMatcher(None, q, name.lower()).ratio()
            if q_emb is not None and master_embs is not None:
                a = q_emb
                b = master_embs[idx]
                sem_sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
                hybrid_score = 0.7 * sem_sim + 0.3 * lex_sim
            else:
                hybrid_score = lex_sim
                
            if hybrid_score > best_score:
                best_score = hybrid_score
                best_match = name
                
            if hybrid_score > 0.88:
                duplicates.append(name)
                
        is_duplicate = len(duplicates) > 1
        status = "Matched" if best_score >= threshold else "Unmatched (Manual Review Required)"
        
        return {
            "matched_name": best_match if best_score >= threshold else query_name,
            "confidence": best_score,
            "is_duplicate": is_duplicate,
            "status": status,
            "raw_query": query_name
        }

    def match_emission_factor(self, item_description, top_n=5):
        """
        Query ChromaDB for top-5 candidates of matching emission factors.
        """
        candidates = self.chroma.query_factors(item_description, top_n=top_n)
        return candidates

if __name__ == "__main__":
    matcher = MatchingService()
    # Test supplier matching
    res_sup = matcher.match_supplier("SteelCorp Inc")
    print("Supplier Match:", res_sup)
    
    # Test factor matching
    res_fact = matcher.match_emission_factor("Steel sheet metal use")
    print("Emission Factor Matches:")
    for idx, c in enumerate(res_fact):
        print(f"{idx+1}. ID: {c['id']}, Scope: {c['scope']}, Factor: {c['factor']}, Conf: {c['confidence']:.2%}")
