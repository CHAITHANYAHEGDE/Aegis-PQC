import time

from sklearn.metrics import (
    auc,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_curve,
)

from .utils import get_model_size


def evaluate_model(model, X_train, X_test, y_test):
    """
    Train and evaluate a model, returning a dictionary of metrics.
    """
    t0 = time.time()
    model.fit(X_train)
    t_train = time.time() - t0

    t0 = time.time()
    preds = model.predict(X_test)
    scores = model.score(X_test)
    t_inf = time.time() - t0

    model_size_bytes = get_model_size(model)

    # Classification metrics
    f1 = f1_score(y_test, preds)
    mcc = matthews_corrcoef(y_test, preds)
    bal_acc = balanced_accuracy_score(y_test, preds)
    precision = precision_score(y_test, preds, zero_division=0)
    recall = recall_score(y_test, preds, zero_division=0)
    cm = confusion_matrix(y_test, preds)

    # Curves
    fpr, tpr, _ = roc_curve(y_test, scores)
    roc_auc = auc(fpr, tpr)

    prec, rec, _ = precision_recall_curve(y_test, scores)
    pr_auc = auc(rec, prec)

    return {
        "model_name": model.name,
        "f1": f1,
        "mcc": mcc,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "balanced_accuracy": bal_acc,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": cm,
        "train_time_s": t_train,
        "inference_time_s": t_inf,
        "model_size_bytes": model_size_bytes,
        "fpr": fpr,
        "tpr": tpr,
        "prec": prec,
        "rec": rec,
    }
