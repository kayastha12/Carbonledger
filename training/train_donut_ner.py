import os
import torch
import json
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForTokenClassification, get_scheduler

class NERDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def train_ner():
    print("Preparing NER training data...")
    # List of entities we want to extract
    entities_list = [
        "O", "B-invoice_number", "I-invoice_number", "B-supplier", "I-supplier",
        "B-gst", "B-material", "I-material", "B-quantity", "B-unit", "B-weight",
        "B-currency", "B-country", "B-vehicle", "B-fuel", "B-distance",
        "B-electricity_consumption", "B-plant", "B-facility", "B-emission_source",
        "B-shipping_method", "B-port", "B-transport_mode"
    ]
    tag2idx = {tag: idx for idx, tag in enumerate(entities_list)}
    
    docs_csv = r"d:\internship\carbonledger\datasets\output\transactional\documents.csv"
    df = pd.read_csv(docs_csv).dropna(subset=["OCRText"])
    df = df.sample(n=500, random_state=42).reset_index(drop=True)
    
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    
    # Tokenize and create word-level alignment tags
    input_ids_list = []
    attention_mask_list = []
    labels_list = []
    
    for idx, row in df.iterrows():
        text = str(row["OCRText"])
        words = text.split()
        
        # Simple heuristic word tagger to generate training labels from structured texts
        word_labels = ["O"] * len(words)
        for w_idx, w in enumerate(words):
            wl = w.lower()
            if "util-" in wl or "inv-" in wl or "po-" in wl:
                word_labels[w_idx] = "B-invoice_number"
            elif "facility" in wl:
                word_labels[w_idx] = "B-facility"
            elif "supplier" in wl and w_idx < len(words) - 1:
                word_labels[w_idx + 1] = "B-supplier"
            elif "total" in wl and "value" in wl:
                word_labels[w_idx] = "B-quantity"
                
        # Align with subword tokenization
        encoding = tokenizer(words, is_split_into_words=True, truncation=True, padding="max_length", max_length=128)
        
        # Map word labels to token labels
        word_ids = encoding.word_ids()
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100) # Special tokens are ignored in PyTorch loss
            else:
                label_ids.append(tag2idx.get(word_labels[word_idx], 0))
                
        input_ids_list.append(encoding["input_ids"])
        attention_mask_list.append(encoding["attention_mask"])
        labels_list.append(label_ids)
        
    train_encodings = {"input_ids": input_ids_list, "attention_mask": attention_mask_list}
    dataset = NERDataset(train_encodings, labels_list)
    loader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print(f"Using device: {device}")
    
    model = AutoModelForTokenClassification.from_pretrained("distilbert-base-uncased", num_labels=len(entities_list))
    model.to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
    
    epochs = 1
    num_training_steps = epochs * len(loader)
    lr_scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=0, num_training_steps=num_training_steps)
    
    print("Starting NER training loop...")
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch in loader:
            optimizer.zero_grad()
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            lr_scheduler.step()
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1} | Loss: {total_loss/len(loader):.4f}")
        
    model_dir = "d:/internship/carbonledger/models/saved_models/ner_tagger"
    os.makedirs(model_dir, exist_ok=True)
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)
    
    with open(os.path.join(model_dir, "tags.json"), "w") as f:
        json.dump(entities_list, f, indent=2)
        
    print("NER Model saved successfully!")

if __name__ == "__main__":
    train_ner()
