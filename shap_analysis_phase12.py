import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import shap


def main():
    os.makedirs("results_phase12/plots", exist_ok=True)

    df = pd.read_csv("data/real/telemetry_ML-KEM-512_real.csv")

    # Exclude unavailable hardware metrics and synthetic proxies
    drop_cols = [
        "hw_telemetry_available",
        "hw_cpu_cycles",
        "hw_instructions",
        "hw_cache_references",
        "hw_cache_misses",
        "hw_branch_instructions",
        "hw_branch_misses",
        "sw_page_faults",
        "sw_cpu_migrations",
        "synthetic_cache_proxy",
        "synthetic_branch_proxy",
        "mitigation_action",
        "mitigation_delay_us",
    ]

    X = df.drop(columns=["is_anomaly"] + drop_cols, errors="ignore")
    y = df["is_anomaly"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training Random Forest for SHAP analysis...")
    rf = RandomForestClassifier(n_estimators=50, random_state=42)
    rf.fit(X_train, y_train)

    print("Computing SHAP values...")
    explainer = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(X_test)

    # shap_values for binary classification in newer SHAP returns a 3D array or list,
    # we take [:, :, 1] or [1] for the positive class
    if isinstance(shap_values, list):
        shap_vals_positive = shap_values[1]
    elif len(shap_values.shape) == 3:
        shap_vals_positive = shap_values[:, :, 1]
    else:
        shap_vals_positive = shap_values

    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_vals_positive, X_test, show=False)
    plt.title("SHAP Feature Importance (Real Physical Telemetry)")
    plt.tight_layout()
    plt.savefig("results_phase12/plots/shap_real.png")
    plt.close()

    print("SHAP analysis complete. Plot saved to results_phase12/plots/shap_real.png")


if __name__ == "__main__":
    main()
