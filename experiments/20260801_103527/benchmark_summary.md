# Aegis PQC Benchmark Summary

| Model | F1 Score | MCC | ROC AUC | PR AUC | Balanced Acc | Train Time (s) | Inference Time (s) |
|-------|----------|-----|---------|--------|--------------|----------------|--------------------|
| One-Class SVM | 0.8000 | 0.6625 | 0.8625 | 0.7377 | 0.8250 | 0.0002 | 0.0003 |
| PyTorch Autoencoder | 0.7586 | 0.5829 | 0.8309 | 0.7351 | 0.7849 | 1.0246 | 0.0004 |
| Isolation Forest | 0.0000 | -0.1512 | 0.9188 | 0.7722 | 0.4750 | 0.0493 | 0.0058 |
| Local Outlier Factor | 0.0000 | -0.1512 | 0.9000 | 0.7250 | 0.4750 | 0.0005 | 0.0007 |
