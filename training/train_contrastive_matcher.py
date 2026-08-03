import os
import json
import random
import torch
from sentence_transformers import SentenceTransformer

class TripletLoss(torch.nn.Module):
    def __init__(self, margin=1.0):
        super(TripletLoss, self).__init__()
        self.margin = margin
    
    def forward(self, anchor, positive, negative):
        pos_dist = torch.nn.functional.pairwise_distance(anchor, positive)
        neg_dist = torch.nn.functional.pairwise_distance(anchor, negative)
        loss = torch.clamp(pos_dist - neg_dist + self.margin, min=0.0)
        return loss.mean()

def train_contrastive_matcher():
    print("Loading cleaned master factors...")
    factors_json = "d:/internship/carbonledger/preprocessing/master_factors_cleaned.json"
    if not os.path.exists(factors_json):
        print(f"Error: master factors file not found at {factors_json}")
        return
        
    with open(factors_json, "r", encoding="utf-8") as f:
        factors = json.load(f)
        
    print("Constructing contrastive triplets...")
    triplets = []
    
    categories = {}
    for f in factors:
        cat = f.get("category", "")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)
        
    for f in factors:
        pos_text = f"{f.get('scope', '')} | {f.get('category', '')} | {f.get('subcategory', '')} | {f.get('activity', '')} | {f.get('detail', '')} | {f.get('text', '')}"
        anchor_text = f.get('activity', '')
        if f.get('text', '') and f.get('text', '') != "nan":
            anchor_text += " " + f.get('text', '')
        anchor_text += f" {f.get('scope', '')}"
        
        cat = f.get("category", "")
        same_cat_factors = categories.get(cat, [])
        
        neg_factor = None
        if len(same_cat_factors) > 1:
            choices = [sf for sf in same_cat_factors if sf.get("id") != f.get("id")]
            if choices:
                neg_factor = random.choice(choices)
                
        if not neg_factor:
            neg_factor = random.choice(factors)
            
        neg_text = f"{neg_factor.get('scope', '')} | {neg_factor.get('category', '')} | {neg_factor.get('subcategory', '')} | {neg_factor.get('activity', '')} | {neg_factor.get('detail', '')} | {neg_factor.get('text', '')}"
        
        triplets.append((anchor_text, pos_text, neg_text))
        
    triplets = triplets[:400]
    print(f"Generated {len(triplets)} triplet examples.")
    
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print(f"Using device: {device}")
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    model.to(device)
    
    criterion = TripletLoss(margin=1.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    
    batch_size = 16
    epochs = 1
    
    print("Starting custom PyTorch TripletLoss training loop...")
    model.train()
    for epoch in range(epochs):
        random.shuffle(triplets)
        epoch_loss = 0.0
        
        for i in range(0, len(triplets), batch_size):
            batch = triplets[i:i+batch_size]
            if len(batch) < 2:
                continue
                
            anchors = [b[0] for b in batch]
            positives = [b[1] for b in batch]
            negatives = [b[2] for b in batch]
            
            optimizer.zero_grad()
            
            feat_anchors = model.tokenize(anchors)
            feat_positives = model.tokenize(positives)
            feat_negatives = model.tokenize(negatives)
            
            # Safely move only tensor fields to device
            feat_anchors = {k: v.to(device) for k, v in feat_anchors.items() if hasattr(v, "to")}
            feat_positives = {k: v.to(device) for k, v in feat_positives.items() if hasattr(v, "to")}
            feat_negatives = {k: v.to(device) for k, v in feat_negatives.items() if hasattr(v, "to")}
            
            emb_anchors = model(feat_anchors)['sentence_embedding']
            emb_positives = model(feat_positives)['sentence_embedding']
            emb_negatives = model(feat_negatives)['sentence_embedding']
            
            loss = criterion(emb_anchors, emb_positives, emb_negatives)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        print(f"Epoch {epoch+1} | Triplet Loss: {epoch_loss / (len(triplets)/batch_size):.4f}")
        
    model_dir = "d:/internship/carbonledger/models/saved_models/contrastive_matcher"
    os.makedirs(model_dir, exist_ok=True)
    model.save(model_dir)
    print("Contrastive matcher model saved successfully!")

if __name__ == "__main__":
    train_contrastive_matcher()
