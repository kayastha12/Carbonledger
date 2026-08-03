import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, f1_score

def train_anomaly_detector():
    print("Loading anomaly datasets...")
    labels_csv = r"d:\internship\carbonledger\datasets\output\transactional\ai_labels.csv"
    if not os.path.exists(labels_csv):
        print(f"Error: {labels_csv} not found.")
        return
        
    df_labels = pd.read_csv(labels_csv)
    
    # Preprocess features
    # Let's extract numerical columns
    df_labels["ExpectedEmission"] = pd.to_numeric(df_labels["ExpectedEmission"], errors="coerce").fillna(0.0)
    df_labels["ActualEmission"] = pd.to_numeric(df_labels["ActualEmission"], errors="coerce").fillna(0.0)
    
    # Construct engineering features
    df_labels["diff_emission"] = df_labels["ActualEmission"] - df_labels["ExpectedEmission"]
    df_labels["ratio_emission"] = df_labels["ActualEmission"] / (df_labels["ExpectedEmission"] + 1e-5)
    df_labels["is_anomaly"] = df_labels["Label"].apply(lambda x: 1 if str(x).strip().lower() == "anomaly" else 0)
    
    features = ["ExpectedEmission", "ActualEmission", "diff_emission", "ratio_emission"]
    X = df_labels[features]
    y = df_labels["is_anomaly"]
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 1. Unsupervised Isolation Forest (NFR requirement)
    print("Fitting Isolation Forest model...")
    iso_forest = IsolationForest(contamination=0.15, random_state=42)
    iso_forest.fit(X_train)
    
    # 2. Supervised Random Forest Classifier
    print("Training Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_val)
    f1 = f1_score(y_val, y_pred)
    print(f"Validation F1 Score: {f1:.4%}")
    print("\nClassification Report:\n", classification_report(y_val, y_pred))
    
    # Save the models
    model_dir = "d:/internship/carbonledger/models/saved_models/anomaly"
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(iso_forest, os.path.join(model_dir, "isolation_forest.pkl"))
    joblib.dump(clf, os.path.join(model_dir, "anomaly_classifier.pkl"))
    print("Anomaly detection models saved successfully!")

if __name__ == "__main__":
    train_anomaly_detector()
