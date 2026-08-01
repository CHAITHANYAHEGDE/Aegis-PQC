# Aegis PQC Benchmark Summary

| Model | F1 Score | MCC | ROC AUC | PR AUC | Balanced Acc | Train Time (s) | Inference Time (s) |
|-------|----------|-----|---------|--------|--------------|----------------|--------------------|
| One-Class SVM | 0.9709 | 0.9417 | 1.0000 | 1.0000 | 0.9700 | 0.0055 | 0.0077 |
| Isolation Forest | 0.9569 | 0.9137 | 1.0000 | 1.0000 | 0.9550 | 0.0562 | 0.0048 |
| Local Outlier Factor | 0.9524 | 0.9045 | 1.0000 | 1.0000 | 0.9500 | 0.0067 | 0.0053 |
| PyTorch Autoencoder | 0.7118 | 0.6171 | 0.9970 | 0.9971 | 0.7762 | 0.6140 | 0.0004 |
