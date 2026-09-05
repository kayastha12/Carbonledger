import os
import pandas as pd
import difflib
import numpy as np
from typing import Optional, Dict, Any, List
from vector_db.chroma_service import ChromaService
from services.emission_factor_service import EmissionFactorService

class MatchingService:
    """
    Supplier and Emission Factor Matching Service.
    Delegates factor retrieval to Centralized EmissionFactorService.
    """
    def __init__(self, chroma_service=None, suppliers_csv_path: Optional[str] = None):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.chroma = chroma_service if chroma_service else ChromaService()
        self.suppliers_csv = suppliers_csv_path or os.path.join(project_root, "datasets", "output", "master", "suppliers.csv")
        self.supplier_master = []
        self.factor_service = EmissionFactorService.get_instance()
        self.model = None
        self._load_suppliers()

    def _get_model(self):
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                print(f"Warning: SentenceTransformer load for supplier matcher note: {e}")
        return self.model

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

    def match_supplier(self, query_name: str, threshold: float = 0.6) -> Dict[str, Any]:
        """
        Match a supplier using a hybrid of Semantic (SentenceTransformer) and Lexical (fuzzy) matching.
        """
        if not self.supplier_master or not query_name:
            return {"matched_name": query_name, "confidence": 1.0, "is_duplicate": False, "status": "Matched (Default)"}
            
        q = str(query_name).strip().lower()
        best_match = None
        best_score = 0.0
        
        q_emb = None
        master_embs = None
        model = self._get_model()
        if model:
            try:
                q_emb = model.encode([query_name])[0]
                master_embs = model.encode(self.supplier_master)
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

    def match_emission_factor(self, item_description: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Query Centralized EmissionFactorService for top matching candidates.
        """
        match = self.factor_service.get_factor(item_description)
        candidates = [{
            "id": match.factor_id,
            "scope": match.scope,
            "category": match.activity_type,
            "activity": match.material,
            "uom": match.unit,
            "ghg_unit": match.ghg_unit,
            "factor": match.emission_factor,
            "source_sheet": match.factor_source,
            "factor_version": match.factor_version,
            "confidence": match.confidence,
            "match_method": match.match_method,
            "explanation": f"Matched via Centralized EmissionFactorService ({match.match_method})"
        }]
        
        # Optionally supplement with Chroma candidates if vector top_n requested
        if top_n > 1 and self.chroma:
            try:
                chroma_cands = self.chroma.query_factors(item_description, top_n=top_n-1)
                for c in chroma_cands:
                    if str(c.get("id")) != match.factor_id:
                        candidates.append(c)
            except Exception:
                pass
                
        return candidates

if __name__ == "__main__":
    matcher = MatchingService()
    res_sup = matcher.match_supplier("SteelCorp Inc")
    print("Supplier Match:", res_sup)
    
    res_fact = matcher.match_emission_factor("Steel sheet metal use")
    print("Emission Factor Matches:", res_fact)
