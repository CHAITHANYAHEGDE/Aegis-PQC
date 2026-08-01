# Aegis PQC Benchmark Summary

| Model | F1 Score | MCC | ROC AUC | PR AUC | Balanced Acc | Train Time (s) | Inference Time (s) |
|-------|----------|-----|---------|--------|--------------|----------------|--------------------|
| One-Class SVM | 0.9709 | 0.9417 | 1.0000 | 1.0000 | 0.9700 | 0.0058 | 0.0075 |
| Isolation Forest | 0.9569 | 0.9137 | 1.0000 | 1.0000 | 0.9550 | 0.0560 | 0.0051 |
| Local Outlier Factor | 0.9524 | 0.9045 | 1.0000 | 1.0000 | 0.9500 | 0.0066 | 0.0056 |
| PyTorch Autoencoder | 0.6667 | 0.5766 | 0.9935 | 0.9938 | 0.7500 | 0.5438 | 0.0004 |
