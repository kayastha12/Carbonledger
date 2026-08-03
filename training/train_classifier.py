import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

def train_document_classifier(csv_path, output_dir):
    print(f"Loading documents dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Drop rows with missing OCRText
    df = df.dropna(subset=["OCRText", "DocumentType"])
    
    X = df["OCRText"]
    y = df["DocumentType"]
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Vectorizing text...")
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_val_vec = vectorizer.transform(X_val)
    
    print("Training Logistic Regression classifier...")
    clf = LogisticRegression(max_iter=500, C=1.0)
    clf.fit(X_train_vec, y_train)
    
    y_pred = clf.predict(X_val_vec)
    acc = accuracy_score(y_val, y_pred)
    print(f"Validation Accuracy: {acc:.4%}")
    print("\nClassification Report:\n", classification_report(y_val, y_pred))
    
    # Save the vectorizer and classifier
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(output_dir, "document_vectorizer.pkl"))
    joblib.dump(clf, os.path.join(output_dir, "document_classifier.pkl"))
    print(f"Model saved to: {output_dir}")

if __name__ == "__main__":
    docs_csv = r"d:\internship\carbonledger\datasets\output\transactional\documents.csv"
    model_dir = r"d:\internship\carbonledger\models\saved_models"
    train_document_classifier(docs_csv, model_dir)
