# Aegis PQC Benchmark Summary

| Model | F1 Score | MCC | ROC AUC | PR AUC | Balanced Acc | Train Time (s) | Inference Time (s) |
|-------|----------|-----|---------|--------|--------------|----------------|--------------------|
| One-Class SVM | 0.9963 | 0.9925 | 0.9970 | 0.9842 | 0.9963 | 0.0009 | 0.0014 |
| Local Outlier Factor | 0.9925 | 0.9850 | 0.9950 | 0.9733 | 0.9925 | 0.0221 | 0.0235 |
| Isolation Forest | 0.9913 | 0.9827 | 0.9975 | 0.9926 | 0.9912 | 0.0501 | 0.0083 |
| PyTorch Autoencoder | 0.6934 | 0.5818 | 0.9485 | 0.9336 | 0.7612 | 0.6730 | 0.0007 |
