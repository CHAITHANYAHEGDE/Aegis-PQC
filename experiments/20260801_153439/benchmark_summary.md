# Aegis PQC Benchmark Summary

| Model | F1 Score | MCC | ROC AUC | PR AUC | Balanced Acc | Train Time (s) | Inference Time (s) |
|-------|----------|-----|---------|--------|--------------|----------------|--------------------|
| One-Class SVM | 0.9938 | 0.9876 | 0.9995 | 0.9994 | 0.9938 | 0.0011 | 0.0016 |
| Isolation Forest | 0.9938 | 0.9876 | 0.9987 | 0.9984 | 0.9938 | 0.1164 | 0.0092 |
| Local Outlier Factor | 0.9757 | 0.9534 | 0.9985 | 0.9983 | 0.9763 | 0.0209 | 0.0237 |
| PyTorch Autoencoder | 0.8680 | 0.7836 | 0.9819 | 0.9748 | 0.8825 | 0.6269 | 0.0008 |
