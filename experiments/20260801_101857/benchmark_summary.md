# Aegis PQC Benchmark Summary

| Model | F1 Score | MCC | ROC AUC | PR AUC | Balanced Acc | Train Time (s) | Inference Time (s) |
|-------|----------|-----|---------|--------|--------------|----------------|--------------------|
| One-Class SVM | 0.8387 | 0.7181 | 0.8812 | 0.7657 | 0.8562 | 0.0002 | 0.0003 |
| Local Outlier Factor | 0.8276 | 0.7242 | 0.9375 | 0.8970 | 0.8500 | 0.0004 | 0.0005 |
| PyTorch Autoencoder | 0.7586 | 0.5829 | 0.9154 | 0.7931 | 0.7849 | 0.7304 | 0.0002 |
| Isolation Forest | 0.0000 | -0.1512 | 0.9094 | 0.7458 | 0.4750 | 0.0431 | 0.0051 |
