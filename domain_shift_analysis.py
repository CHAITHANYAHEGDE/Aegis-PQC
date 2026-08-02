import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import entropy

def compute_kl_divergence(p, q):
    """Compute KL Divergence between two empirical distributions using histograms."""
    min_val = min(p.min(), q.min())
    max_val = max(p.max(), q.max())
    bins = np.linspace(min_val, max_val, 50)
    p_hist, _ = np.histogram(p, bins=bins, density=True)
    q_hist, _ = np.histogram(q, bins=bins, density=True)
    # Add small epsilon to avoid div by zero or log of zero
    epsilon = 1e-10
    p_hist = p_hist + epsilon
    q_hist = q_hist + epsilon
    p_hist /= p_hist.sum()
    q_hist /= q_hist.sum()
    return entropy(p_hist, q_hist)

def main():
    os.makedirs("results_phase12/plots", exist_ok=True)
    
    df_synthetic = pd.read_csv("data/telemetry_ML-KEM-512.csv")
    df_real = pd.read_csv("data/real/telemetry_ML-KEM-512_real.csv")
    
    # We will analyze only the core software metrics that are available on macOS
    features = ["execution_time_us", "max_rss_kb", "cpu_usage", "context_switches"]
    
    # 1. Feature Distributions Overlaid
    for feature in features:
        plt.figure(figsize=(8, 5))
        sns.kdeplot(df_synthetic[feature], label="Synthetic", fill=True, alpha=0.5)
        sns.kdeplot(df_real[feature], label="Real Physical", fill=True, alpha=0.5)
        plt.title(f"Domain Shift: {feature}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"results_phase12/plots/shift_{feature}.png")
        plt.close()
        
    # 2. Correlation Matrices
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    sns.heatmap(df_synthetic[features].corr(), annot=True, cmap="coolwarm", ax=axes[0], vmin=-1, vmax=1)
    axes[0].set_title("Synthetic Correlation Matrix")
    
    sns.heatmap(df_real[features].corr(), annot=True, cmap="coolwarm", ax=axes[1], vmin=-1, vmax=1)
    axes[1].set_title("Real Physical Correlation Matrix")
    
    plt.tight_layout()
    plt.savefig("results_phase12/plots/correlation_comparison.png")
    plt.close()
    
    # 3. KL Divergence
    print("--- KL Divergence (Synthetic || Real) ---")
    results = []
    for feature in features:
        kl = compute_kl_divergence(df_synthetic[feature], df_real[feature])
        print(f"{feature}: {kl:.4f}")
        results.append({"Feature": feature, "KL_Divergence": kl})
        
    pd.DataFrame(results).to_csv("results_phase12/domain_shift_metrics.csv", index=False)
    print("Domain shift analysis complete. Plots saved to results_phase12/plots/")

if __name__ == "__main__":
    main()
