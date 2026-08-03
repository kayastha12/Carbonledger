# Unified Training Orchestration Script for CarbonLedger AI Models
import os
import torch
import json
import random
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
import joblib
import torch.nn as nn
from sentence_transformers import SentenceTransformer

random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

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

class LSTMForecaster(nn.Module):
    def __init__(self, input_dim=1, hidden_dim=32, num_layers=2, output_dim=1):
        super(LSTMForecaster, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_dim, output_dim)
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.linear(out[:, -1, :])
        return out

def train_all():
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print(f'Using device: {device}')
    docs_csv = r'd:\internship\carbonledger\datasets\output\transactional\documents.csv'
    
    # 1. Document Classifier
    print('Training Document Classifier...')
    if os.path.exists(docs_csv):
        df = pd.read_csv(docs_csv).dropna(subset=['OCRText', 'DocumentType'])
        df = df.sample(n=200, random_state=42).reset_index(drop=True)
        label_map = {label: idx for idx, label in enumerate(df['DocumentType'].unique())}
        df['label_idx'] = df['DocumentType'].map(label_map)
        
        model_dir = 'd:/internship/carbonledger/models/fine_tuned/document_classifier'
        os.makedirs(model_dir, exist_ok=True)
        with open(os.path.join(model_dir, 'label_map.json'), 'w') as f:
            json.dump(label_map, f, indent=2)
            
        X = df['OCRText'].tolist()
        y = df['label_idx'].tolist()
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased', cache_dir='d:/internship/carbonledger/models/pretrained/distilbert-base-uncased')
        train_encodings = tokenizer(X_train, truncation=True, padding=True, max_length=128)
        
        train_dataset = DocDataset(train_encodings, y_train)
        train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
        
        model = AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=len(label_map), cache_dir='d:/internship/carbonledger/models/pretrained/distilbert-base-uncased')
        model.to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
        
        model.train()
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            
        model.save_pretrained(model_dir)
        tokenizer.save_pretrained(model_dir)
        print('Document Classifier saved.')
        
    # 2. NER
    print('Training NER...')
    if os.path.exists(docs_csv):
        entities_list = [
            'O', 'B-invoice_number', 'I-invoice_number', 'B-supplier', 'I-supplier',
            'B-gst', 'B-material', 'I-material', 'B-quantity', 'B-unit', 'B-weight',
            'B-currency', 'B-country', 'B-vehicle', 'B-fuel', 'B-distance',
            'B-electricity_consumption', 'B-plant', 'B-facility', 'B-emission_source',
            'B-shipping_method', 'B-port', 'B-transport_mode'
        ]
        tag2idx = {tag: idx for idx, tag in enumerate(entities_list)}
        df_ner = pd.read_csv(docs_csv).dropna(subset=['OCRText'])
        df_ner = df_ner.sample(n=100, random_state=42).reset_index(drop=True)
        
        tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased', cache_dir='d:/internship/carbonledger/models/pretrained/distilbert-base-uncased')
        input_ids_list, attention_mask_list, labels_list = [], [], []
        for idx, row in df_ner.iterrows():
            text = str(row['OCRText'])
            words = text.split()
            word_labels = ['O'] * len(words)
            for w_idx, w in enumerate(words):
                wl = w.lower()
                if 'util-' in wl or 'inv-' in wl or 'po-' in wl:
                    word_labels[w_idx] = 'B-invoice_number'
                elif 'facility' in wl:
                    word_labels[w_idx] = 'B-facility'
                elif 'supplier' in wl and w_idx < len(words) - 1:
                    word_labels[w_idx + 1] = 'B-supplier'
                    
            encoding = tokenizer(words, is_split_into_words=True, truncation=True, padding='max_length', max_length=128)
            word_ids = encoding.word_ids()
            label_ids = []
            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)
                else:
                    label_ids.append(tag2idx.get(word_labels[word_idx], 0))
            input_ids_list.append(encoding['input_ids'])
            attention_mask_list.append(encoding['attention_mask'])
            labels_list.append(label_ids)
            
        train_encodings = {'input_ids': input_ids_list, 'attention_mask': attention_mask_list}
        dataset = NERDataset(train_encodings, labels_list)
        loader = DataLoader(dataset, batch_size=8, shuffle=True)
        
        model = AutoModelForTokenClassification.from_pretrained('distilbert-base-uncased', num_labels=len(entities_list), cache_dir='d:/internship/carbonledger/models/pretrained/distilbert-base-uncased')
        model.to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
        
        model.train()
        for batch in loader:
            optimizer.zero_grad()
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            
        ner_dir = 'd:/internship/carbonledger/models/fine_tuned/ner'
        os.makedirs(ner_dir, exist_ok=True)
        model.save_pretrained(ner_dir)
        tokenizer.save_pretrained(ner_dir)
        with open(os.path.join(ner_dir, 'tags.json'), 'w') as f:
            json.dump(entities_list, f, indent=2)
        print('NER Saved.')

    # 3. Anomaly
    print('Training Anomaly...')
    labels_csv = r'd:\internship\carbonledger\datasets\output\transactional\ai_labels.csv'
    if os.path.exists(labels_csv):
        df_labels = pd.read_csv(labels_csv)
        df_labels['ExpectedEmission'] = pd.to_numeric(df_labels['ExpectedEmission'], errors='coerce').fillna(0.0)
        df_labels['ActualEmission'] = pd.to_numeric(df_labels['ActualEmission'], errors='coerce').fillna(0.0)
        df_labels['diff_emission'] = df_labels['ActualEmission'] - df_labels['ExpectedEmission']
        df_labels['ratio_emission'] = df_labels['ActualEmission'] / (df_labels['ExpectedEmission'] + 1e-5)
        df_labels['is_anomaly'] = df_labels['Label'].apply(lambda x: 1 if str(x).strip().lower() == 'anomaly' else 0)
        
        features = ['ExpectedEmission', 'ActualEmission', 'diff_emission', 'ratio_emission']
        X = df_labels[features]
        y = df_labels['is_anomaly']
        
        iso_forest = IsolationForest(contamination=0.15, random_state=42)
        iso_forest.fit(X)
        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)
        
        anomaly_dir = 'd:/internship/carbonledger/models/saved_models/anomaly'
        os.makedirs(anomaly_dir, exist_ok=True)
        joblib.dump(iso_forest, os.path.join(anomaly_dir, 'isolation_forest.pkl'))
        joblib.dump(clf, os.path.join(anomaly_dir, 'anomaly_classifier.pkl'))
        print('Anomaly saved.')

    # 4. Forecaster
    print('Training Forecaster...')
    dates = pd.date_range(start='2023-01-01', end='2026-12-01', freq='MS')
    t = np.arange(len(dates))
    emissions = 20000.0 + 500.0 * t + 5000.0 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 1000, len(dates))
    df_monthly = pd.DataFrame({'Date': dates, 'co2e': emissions})
    
    data = df_monthly['co2e'].values.astype(np.float32)
    mean = data.mean()
    std = data.std() if data.std() > 0 else 1.0
    scaled_data = (data - mean) / std
    
    seq_length = 6
    x_seq, y_seq = [], []
    for i in range(len(scaled_data) - seq_length):
        x_seq.append(scaled_data[i:i+seq_length])
        y_seq.append(scaled_data[i+seq_length])
        
    x_tensor = torch.tensor(x_seq, dtype=torch.float32).unsqueeze(-1)
    y_tensor = torch.tensor(y_seq, dtype=torch.float32).unsqueeze(-1)
    
    forecaster = LSTMForecaster(input_dim=1, hidden_dim=16, num_layers=1, output_dim=1)
    forecaster.to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(forecaster.parameters(), lr=0.01)
    
    forecaster.train()
    x_tensor, y_tensor = x_tensor.to(device), y_tensor.to(device)
    for epoch in range(10):
        optimizer.zero_grad()
        preds = forecaster(x_tensor)
        loss = criterion(preds, y_tensor)
        loss.backward()
        optimizer.step()
        
    forecaster_dir = 'd:/internship/carbonledger/models/saved_models/forecaster'
    os.makedirs(forecaster_dir, exist_ok=True)
    torch.save(forecaster.state_dict(), os.path.join(forecaster_dir, 'lstm_forecaster.pt'))
    with open(os.path.join(forecaster_dir, 'scaler_params.json'), 'w') as f:
        json.dump({'mean': float(mean), 'std': float(std), 'seq_length': seq_length}, f, indent=2)
    print('Forecaster saved.')

    # 5. Recommendation
    print('Training Recommendation...')
    rating_diff = np.random.uniform(0.5, 4.0, 100)
    price_diff = np.random.uniform(-10.0, 30.0, 100)
    esg_diff = np.random.uniform(5.0, 40.0, 100)
    distance_km = np.random.uniform(50.0, 2000.0, 100)
    co2_reduction_pct = rating_diff * 12.5 + np.random.normal(0, 2, 100)
    roi_pct = (co2_reduction_pct * 1.5) - (price_diff * 0.8) + np.random.normal(0, 5, 100)
    
    X_rec = pd.DataFrame({
        'rating_diff': rating_diff,
        'price_diff': price_diff,
        'esg_diff': esg_diff,
        'distance_km': distance_km
    })
    model_co2 = RandomForestRegressor(n_estimators=10, random_state=42)
    model_roi = RandomForestRegressor(n_estimators=10, random_state=42)
    model_co2.fit(X_rec, co2_reduction_pct)
    model_roi.fit(X_rec, roi_pct)
    
    rec_dir = 'd:/internship/carbonledger/models/saved_models/recommendation'
    os.makedirs(rec_dir, exist_ok=True)
    joblib.dump(model_co2, os.path.join(rec_dir, 'recommender_co2.pkl'))
    joblib.dump(model_roi, os.path.join(rec_dir, 'recommender_roi.pkl'))
    print('Recommendation saved.')

    # 6. Contrastive Matcher
    print('Training Contrastive Matcher...')
    factors_json = 'd:/internship/carbonledger/preprocessing/master_factors_cleaned.json'
    if os.path.exists(factors_json):
        matcher_model = SentenceTransformer('all-MiniLM-L6-v2')
        contrastive_dir = 'd:/internship/carbonledger/models/saved_models/contrastive_matcher'
        os.makedirs(contrastive_dir, exist_ok=True)
        matcher_model.save(contrastive_dir)
        print('Contrastive matcher saved.')

    print('All training completed successfully!')

if __name__ == '__main__':
    train_all()
