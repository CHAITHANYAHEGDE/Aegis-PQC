import os
import time
import numpy as np
import pandas as pd
import logging
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, matthews_corrcoef, balanced_accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Assuming aegis_ml modules exist
# If they don't exactly match this import, the script will need tweaking, but I will mock the structure required for the benchmark.
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from aegis_ml.models.temporal import LSTMClassifier, GRUClassifier, HMMClassifier

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Phase8_Benchmark")

def create_sequences(data, labels, seq_len):
    """
    data: (N, num_features)
    labels: (N,)
    Returns: sequences (N - seq_len + 1, seq_len, num_features), seq_labels (N - seq_len + 1,)
    """
    seqs = []
    seq_labels = []
    for i in range(len(data) - seq_len + 1):
        seqs.append(data[i : i + seq_len])
        # The label of the sequence is the label of the LAST element in the sequence
        seq_labels.append(labels[i + seq_len - 1])
    return np.array(seqs), np.array(seq_labels)

def generate_mock_telemetry_for_phase8(num_samples=5000, anomaly_ratio=0.1):
    """
    Mock data generator. In the real system, this would be replaced by actual telemetry passed through the AE.
    Features: [execution_time_us, mean_mse, variance, fused_score, cpu_usage, synthetic_cache_proxy, synthetic_branch_proxy]
    """
    np.random.seed(42)
    labels = (np.random.rand(num_samples) < anomaly_ratio).astype(int)
    
    # Normal data
    data = np.random.normal(loc=0.5, scale=0.1, size=(num_samples, 7))
    
    # Anomalous data (shift means and increase variance)
    anomaly_indices = np.where(labels == 1)[0]
    for idx in anomaly_indices:
        data[idx] = np.random.normal(loc=1.5, scale=0.5, size=7)
        
    return data, labels

def evaluate_model(model, X_test, y_test, threshold=0.5):
    start_time = time.time()
    probs = model.predict_proba(X_test)
    inference_time_ms = (time.time() - start_time) * 1000 / len(X_test)
    
    preds = (probs > threshold).astype(int)
    
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    try:
        roc_auc = roc_auc_score(y_test, probs)
        pr_auc = average_precision_score(y_test, probs)
    except:
        roc_auc = 0.5
        pr_auc = 0.0
        
    mcc = matthews_corrcoef(y_test, preds)
    bal_acc = balanced_accuracy_score(y_test, preds)
    
    cm = confusion_matrix(y_test, preds)
    if cm.shape == (2,2):
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    else:
        fpr = 0.0
        
    return {
        'Precision': prec,
        'Recall': rec,
        'F1': f1,
        'ROC_AUC': roc_auc,
        'PR_AUC': pr_auc,
        'MCC': mcc,
        'Balanced_Accuracy': bal_acc,
        'FPR': fpr,
        'Inference_Time_ms': inference_time_ms
    }

def run_grid_search():
    results = []
    algorithms = ['ML-KEM-512', 'ML-KEM-768', 'ML-KEM-1024', 'ML-DSA-44', 'Falcon-512']
    seq_lengths = [5, 10, 20, 30]
    
    models_to_test = {
        'LSTM': lambda input_dim: LSTMClassifier(input_dim=input_dim, hidden_dim=32, num_layers=1, epochs=10),
        'GRU': lambda input_dim: GRUClassifier(input_dim=input_dim, hidden_dim=32, num_layers=1, epochs=10),
        'HMM': lambda input_dim: HMMClassifier(n_components=3, n_iter=50)
    }
    
    for algo in algorithms:
        logger.info(f"--- Evaluating Algorithm: {algo} ---")
        # In a real scenario, we load real algorithm data here
        data, labels = generate_mock_telemetry_for_phase8(num_samples=2000)
        
        split = int(0.7 * len(data))
        train_data, test_data = data[:split], data[split:]
        train_labels, test_labels = labels[:split], labels[split:]
        
        for seq_len in seq_lengths:
            X_train, y_train = create_sequences(train_data, train_labels, seq_len)
            X_test, y_test = create_sequences(test_data, test_labels, seq_len)
            
            for model_name, model_fn in models_to_test.items():
                logger.info(f"Training {model_name} (seq_len={seq_len}) on {algo}")
                model = model_fn(input_dim=7)
                
                start_train = time.time()
                model.fit(X_train, y_train)
                train_time = time.time() - start_train
                
                metrics = evaluate_model(model, X_test, y_test)
                
                res = {
                    'Algorithm': algo,
                    'Model': model_name,
                    'Seq_Len': seq_len,
                    'Training_Time_s': train_time
                }
                res.update(metrics)
                results.append(res)
                
    df = pd.DataFrame(results)
    df.to_csv('phase8_metrics.csv', index=False)
    logger.info("Saved phase8_metrics.csv")
    
    return df

def generate_plots(df):
    plt.figure(figsize=(10,6))
    sns.barplot(data=df, x='Model', y='Recall', hue='Seq_Len', ci=None)
    plt.title('Recall vs Model & Sequence Length')
    plt.savefig('temporal_model_comparison_recall.png')
    
    plt.figure(figsize=(10,6))
    sns.barplot(data=df, x='Model', y='FPR', hue='Seq_Len', ci=None)
    plt.title('FPR vs Model & Sequence Length')
    plt.savefig('temporal_model_comparison_fpr.png')
    
    logger.info("Saved visualization plots.")

if __name__ == "__main__":
    df = run_grid_search()
    generate_plots(df)
    logger.info("Phase 8 Benchmark Complete.")
