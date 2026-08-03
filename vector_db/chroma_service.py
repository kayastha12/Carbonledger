import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

class ChromaService:
    def __init__(self, persist_dir="d:/internship/carbonledger/vector_db/chroma_data"):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Load BAAI/bge-small-en-v1.5 from local cache or auto-download
        self.pretrained_cache_bge = "d:/internship/carbonledger/models/pretrained/bge-small-en-v1.5"
        os.makedirs(self.pretrained_cache_bge, exist_ok=True)
        try:
            print("Loading embedding model BAAI/bge-small-en-v1.5...")
            self.model = SentenceTransformer("BAAI/bge-small-en-v1.5", cache_folder=self.pretrained_cache_bge)
        except Exception as e:
            print(f"Warning: BAAI/bge-small-en-v1.5 load failed ({e}), trying default fallback.")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            
        self.collection_name = "emission_factors"
        self.collection = self.client.get_or_create_collection(self.collection_name)

    def index_factors(self, factors_json_path, refresh_embeddings=False):
        print(f"Indexing emission factors from: {factors_json_path}")
        with open(factors_json_path, "r", encoding="utf-8") as f:
            factors = json.load(f)
            
        if refresh_embeddings:
            print("Deleting existing collection for embedding refresh...")
            try:
                self.client.delete_collection(self.collection_name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(self.collection_name)
            
        ids = []
        documents = []
        metadatas = []
        
        # In-memory deduplication tracker
        existing_keys = {}
        
        batch_size = 500
        for i, f in enumerate(factors):
            # Formulate key-value uniqueness
            unique_key = f"{f.get('scope')}_{f.get('category')}_{f.get('subcategory')}_{f.get('activity')}_{f.get('detail')}_{f.get('text')}"
            
            # Duplicate detection & Version tracking
            if unique_key in existing_keys:
                existing_f = existing_keys[unique_key]
                if float(existing_f.get("factor", 0.0)) == float(f.get("factor", 0.0)):
                    # Exact duplicate, skip indexing
                    continue
                else:
                    # Factor value updated. Increment version history index
                    f["factor_version"] = f"2026.2_rev_{i}"
            else:
                existing_keys[unique_key] = f
                
            text_desc = f"{f.get('scope', '')} | {f.get('category', '')} | {f.get('subcategory', '')} | {f.get('activity', '')} | {f.get('detail', '')} | {f.get('text', '')}"
            
            ids.append(f.get("id"))
            documents.append(text_desc)
            metadatas.append({
                "id": f.get("id"),
                "scope": f.get("scope"),
                "category": f.get("category"),
                "subcategory": f.get("subcategory"),
                "activity": f.get("activity"),
                "detail": f.get("detail"),
                "text": f.get("text"),
                "uom": f.get("uom"),
                "ghg_unit": f.get("ghg_unit"),
                "factor": float(f.get("factor", 0.0)),
                "source_sheet": f.get("source_sheet"),
                "factor_version": f.get("factor_version", "2026.1")
            })
            
            if len(ids) >= batch_size or i == len(factors) - 1:
                batch_embeddings = self.model.encode(documents).tolist()
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=batch_embeddings,
                    metadatas=metadatas
                )
                ids = []
                documents = []
                metadatas = []
                
        print(f"Indexed records (Collection count: {self.collection.count()})")

    def query_factors(self, query_text, top_n=5):
        query_embedding = self.model.encode([query_text]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_n
        )
        
        candidates = []
        if results and results["ids"] and len(results["ids"]) > 0:
            for idx in range(len(results["ids"][0])):
                dist = results["distances"][0][idx]
                confidence = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
                metadata = results["metadatas"][0][idx]
                candidates.append({
                    "id": metadata.get("id"),
                    "scope": metadata.get("scope"),
                    "category": metadata.get("category"),
                    "subcategory": metadata.get("subcategory"),
                    "activity": metadata.get("activity"),
                    "detail": metadata.get("detail"),
                    "text": metadata.get("text"),
                    "uom": metadata.get("uom"),
                    "ghg_unit": metadata.get("ghg_unit"),
                    "factor": metadata.get("factor"),
                    "source_sheet": metadata.get("source_sheet"),
                    "factor_version": metadata.get("factor_version"),
                    "confidence": confidence,
                    "explanation": f"Matched via contrastive SentenceTransformer with embedding similarity of {confidence:.2%}"
                })
        return candidates

if __name__ == "__main__":
    service = ChromaService()
    factors_json = "d:/internship/carbonledger/preprocessing/master_factors_cleaned.json"
    if os.path.exists(factors_json):
        # Refresh embedding index
        service.index_factors(factors_json, refresh_embeddings=True)
        # Test query
        res = service.query_factors("Steel Sheet Metal", top_n=2)
        print(json.dumps(res, indent=2))
