import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    matthews_corrcoef, balanced_accuracy_score, roc_auc_score,
    average_precision_score, confusion_matrix
)

# Optional dependencies
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
try:
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import Input, Dense
    from tensorflow.keras.callbacks import EarlyStopping
    HAS_TF = True
except ImportError:
    HAS_TF = False

def build_autoencoder(input_dim):
    inp = Input(shape=(input_dim,))
    x = Dense(16, activation="relu")(inp)
    x = Dense(8, activation="relu")(x)
    x = Dense(16, activation="relu")(x)
    out = Dense(input_dim, activation="linear")(x)
    model = Model(inp, out)
    model.compile(optimizer="adam", loss="mse")
    return model

def main():
    os.makedirs("results_phase12", exist_ok=True)
    
    df = pd.read_csv("data/real/telemetry_ML-KEM-512_real.csv")
    
    # Exclude hardware counters that are unsupported (-1.0) and synthetic proxies (0.0)
    # The actual varying features should be execution_time, context_switches, max_rss_kb, cpu_usage
    drop_cols = [
        "hw_telemetry_available", "hw_cpu_cycles", "hw_instructions", 
        "hw_cache_references", "hw_cache_misses", "hw_branch_instructions", 
        "hw_branch_misses", "sw_page_faults", "sw_cpu_migrations",
        "synthetic_cache_proxy", "synthetic_branch_proxy", "mitigation_action", "mitigation_delay_us"
    ]
    
    X = df.drop(columns=["is_anomaly"] + drop_cols, errors='ignore')
    y = df["is_anomaly"]
    
    print("Features used for training:", X.columns.tolist())
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    results = []
    
    models = {
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000)
    }
    
    if HAS_XGB:
        models["XGBoost"] = XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric="logloss")
        
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_test_scaled)[:, 1]
        else:
            y_prob = y_pred
            
        results.append({
            "Model": name,
            "Accuracy": accuracy_score(y_test, y_pred),
            "Precision": precision_score(y_test, y_pred, zero_division=0),
            "Recall": recall_score(y_test, y_pred, zero_division=0),
            "F1": f1_score(y_test, y_pred, zero_division=0),
            "MCC": matthews_corrcoef(y_test, y_pred),
            "Balanced Acc": balanced_accuracy_score(y_test, y_pred),
            "ROC AUC": roc_auc_score(y_test, y_prob),
            "PR AUC": average_precision_score(y_test, y_prob)
        })

    # Unsupervised Models (trained only on normal data)
    X_train_normal = X_train_scaled[y_train == 0]
    
    print("Training Isolation Forest...")
    iso = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    iso.fit(X_train_normal)
    y_pred_iso = iso.predict(X_test_scaled)
    y_pred_iso = [1 if p == -1 else 0 for p in y_pred_iso]
    results.append({
        "Model": "Isolation Forest",
        "Accuracy": accuracy_score(y_test, y_pred_iso),
        "Precision": precision_score(y_test, y_pred_iso, zero_division=0),
        "Recall": recall_score(y_test, y_pred_iso, zero_division=0),
        "F1": f1_score(y_test, y_pred_iso, zero_division=0),
        "MCC": matthews_corrcoef(y_test, y_pred_iso),
        "Balanced Acc": balanced_accuracy_score(y_test, y_pred_iso),
        "ROC AUC": roc_auc_score(y_test, y_pred_iso),
        "PR AUC": average_precision_score(y_test, y_pred_iso)
    })
    
    print("Training OCSVM...")
    ocsvm = OneClassSVM(nu=0.1, kernel="rbf", gamma="auto")
    ocsvm.fit(X_train_normal)
    y_pred_svm = ocsvm.predict(X_test_scaled)
    y_pred_svm = [1 if p == -1 else 0 for p in y_pred_svm]
    results.append({
        "Model": "One-Class SVM",
        "Accuracy": accuracy_score(y_test, y_pred_svm),
        "Precision": precision_score(y_test, y_pred_svm, zero_division=0),
        "Recall": recall_score(y_test, y_pred_svm, zero_division=0),
        "F1": f1_score(y_test, y_pred_svm, zero_division=0),
        "MCC": matthews_corrcoef(y_test, y_pred_svm),
        "Balanced Acc": balanced_accuracy_score(y_test, y_pred_svm),
        "ROC AUC": roc_auc_score(y_test, y_pred_svm),
        "PR AUC": average_precision_score(y_test, y_pred_svm)
    })
    
    print("Evaluating LOF...")
    lof = LocalOutlierFactor(n_neighbors=20, novelty=True, contamination=0.1)
    lof.fit(X_train_normal)
    y_pred_lof = lof.predict(X_test_scaled)
    y_pred_lof = [1 if p == -1 else 0 for p in y_pred_lof]
    results.append({
        "Model": "LOF",
        "Accuracy": accuracy_score(y_test, y_pred_lof),
        "Precision": precision_score(y_test, y_pred_lof, zero_division=0),
        "Recall": recall_score(y_test, y_pred_lof, zero_division=0),
        "F1": f1_score(y_test, y_pred_lof, zero_division=0),
        "MCC": matthews_corrcoef(y_test, y_pred_lof),
        "Balanced Acc": balanced_accuracy_score(y_test, y_pred_lof),
        "ROC AUC": roc_auc_score(y_test, y_pred_lof),
        "PR AUC": average_precision_score(y_test, y_pred_lof)
    })
    
    if HAS_TF:
        print("Training Autoencoder...")
        ae = build_autoencoder(X_train_scaled.shape[1])
        ae.fit(X_train_normal, X_train_normal, epochs=30, batch_size=32, validation_split=0.1, verbose=0,
               callbacks=[EarlyStopping(patience=3, restore_best_weights=True)])
        preds = ae.predict(X_test_scaled, verbose=0)
        mse = np.mean(np.power(X_test_scaled - preds, 2), axis=1)
        threshold = np.percentile(np.mean(np.power(X_train_normal - ae.predict(X_train_normal, verbose=0), 2), axis=1), 95)
        y_pred_ae = [1 if err > threshold else 0 for err in mse]
        results.append({
            "Model": "Autoencoder",
            "Accuracy": accuracy_score(y_test, y_pred_ae),
            "Precision": precision_score(y_test, y_pred_ae, zero_division=0),
            "Recall": recall_score(y_test, y_pred_ae, zero_division=0),
            "F1": f1_score(y_test, y_pred_ae, zero_division=0),
            "MCC": matthews_corrcoef(y_test, y_pred_ae),
            "Balanced Acc": balanced_accuracy_score(y_test, y_pred_ae),
            "ROC AUC": roc_auc_score(y_test, mse),
            "PR AUC": average_precision_score(y_test, mse)
        })

    res_df = pd.DataFrame(results)
    print("\n--- Physical Validation Results ---")
    print(res_df.to_string(index=False))
    res_df.to_csv("results_phase12/physical_metrics.csv", index=False)
    
if __name__ == "__main__":
    main()
