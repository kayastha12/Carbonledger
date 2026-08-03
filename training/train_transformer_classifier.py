import os
import torch
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_scheduler
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix

class DocDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def train_classifier():
    print("Loading data...")
    docs_csv = r"d:\internship\carbonledger\datasets\output\transactional\documents.csv"
    df = pd.read_csv(docs_csv).dropna(subset=["OCRText", "DocumentType"])
    
    # We will sample 1000 items to ensure fast execution, but keep structure production-grade
    df = df.sample(n=1000, random_state=42).reset_index(drop=True)
    
    # Target label map
    label_map = {label: idx for idx, label in enumerate(df["DocumentType"].unique())}
    df["label_idx"] = df["DocumentType"].map(label_map)
    
    # Save label mapping
    model_dir = "d:/internship/carbonledger/models/saved_models/distilbert"
    os.makedirs(model_dir, exist_ok=True)
    with open(os.path.join(model_dir, "label_map.json"), "w") as f:
        import json
        json.dump(label_map, f, indent=2)
        
    X = df["OCRText"].tolist()
    y = df["label_idx"].tolist()
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    
    train_encodings = tokenizer(X_train, truncation=True, padding=True, max_length=128)
    val_encodings = tokenizer(X_val, truncation=True, padding=True, max_length=128)
    
    train_dataset = DocDataset(train_encodings, y_train)
    val_dataset = DocDataset(val_encodings, y_val)
    
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=8)
    
    # Class weights
    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y_train),
        y=y_train
    )
    class_weights = torch.tensor(class_weights, dtype=torch.float)
    
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print(f"Using device: {device}")
    
    class_weights = class_weights.to(device)
    
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=len(label_map))
    model.to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
    
    epochs = 1
    num_training_steps = epochs * len(train_loader)
    lr_scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=0, num_training_steps=num_training_steps)
    
    scaler = torch.cuda.amp.GradScaler(enabled=(device.type == 'cuda'))
    
    best_val_loss = float('inf')
    
    print("Starting training loop...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in train_loader:
            optimizer.zero_grad()
            
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            # Autocast for mixed precision
            with torch.amp.autocast(device_type=device.type, enabled=(device.type == 'cuda')):
                outputs = model(input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                loss_fct = torch.nn.CrossEntropyLoss(weight=class_weights)
                loss = loss_fct(logits, labels)
                
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            lr_scheduler.step()
            total_loss += loss.item()
            
        # Validation
        model.eval()
        val_loss = 0
        preds = []
        targets = []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                outputs = model(input_ids, attention_mask=attention_mask)
                loss_fct = torch.nn.CrossEntropyLoss()
                loss = loss_fct(outputs.logits, labels)
                val_loss += loss.item()
                
                preds.extend(torch.argmax(outputs.logits, dim=1).cpu().numpy())
                targets.extend(labels.cpu().numpy())
                
        avg_val_loss = val_loss / len(val_loader)
        print(f"Epoch {epoch+1} | Train Loss: {total_loss/len(train_loader):.4f} | Val Loss: {avg_val_loss:.4f}")
        
        # Confusion matrix and metrics
        print("\nConfusion Matrix:\n", confusion_matrix(targets, preds))
        print("\nClassification Report:\n", classification_report(targets, preds, target_names=list(label_map.keys())))
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            model.save_pretrained(model_dir)
            tokenizer.save_pretrained(model_dir)
            print("Checkpoint saved successfully!")
            
    print("Training finished.")

if __name__ == "__main__":
    train_classifier()
