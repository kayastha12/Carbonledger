import os
import random
import pandas as pd
from tqdm import tqdm
from generators.base import BaseGenerator

class EmbeddingsGenerator(BaseGenerator):
    def generate(self, output_dir):
        random.seed(self.seed)
        
        num_embeddings = self.config["sizes"]["embeddings"]
        
        # Load documents
        docs_path = os.path.join(output_dir, "transactional", "documents.csv")
        docs_df = pd.read_csv(docs_path)
        doc_records = docs_df[["DocumentID", "OCRText"]].to_dict("records")
        
        embeddings = []
        embedding_idx = 1
        
        print("Generating Simulated Document Embeddings...")
        # Map 1-to-1 with documents
        for doc in tqdm(doc_records[:num_embeddings]):
            doc_id = doc["DocumentID"]
            ocr_text = doc["OCRText"]
            
            # Simulated embeddings chunk text
            chunk_text = f"Document Chunk {doc_id}: {ocr_text[:200]}"
            model = "text-embedding-3-small"
            dimensions = 1536
            
            embeddings.append({
                "EmbeddingID": embedding_idx,
                "DocumentID": doc_id,
                "ChunkID": 1,
                "ChunkText": chunk_text,
                "EmbeddingModel": model,
                "VectorDimensions": dimensions,
                "EmbeddingVersion": "v1"
            })
            embedding_idx += 1
            
        # Fallback if we have fewer documents than requested embeddings
        while len(embeddings) < num_embeddings:
            doc = random.choice(doc_records)
            doc_id = doc["DocumentID"]
            ocr_text = doc["OCRText"]
            chunk_text = f"Document Chunk Extra: {ocr_text[:200]}"
            
            embeddings.append({
                "EmbeddingID": embedding_idx,
                "DocumentID": doc_id,
                "ChunkID": 2,
                "ChunkText": chunk_text,
                "EmbeddingModel": "text-embedding-3-small",
                "VectorDimensions": 1536,
                "EmbeddingVersion": "v1"
            })
            embedding_idx += 1
            
        df = pd.DataFrame(embeddings)
        self.save_data(df, output_dir, "embeddings", is_master=False, pk_col="EmbeddingID")
        print(f"Generated {len(df)} Document Embeddings.")
