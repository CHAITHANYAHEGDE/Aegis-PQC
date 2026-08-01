import json
import os
import platform
import subprocess
from datetime import datetime

from torch.utils.tensorboard import SummaryWriter

from aegis_ml.utils import setup_logging


def get_system_info():
    try:
        commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .strip()
            .decode("utf-8")
        )
    except Exception:
        commit = "unknown"

    try:
        cmake_v = (
            subprocess.check_output(["cmake", "--version"])
            .decode("utf-8")
            .split("\n")[0]
        )
    except Exception:
        cmake_v = "unknown"

    try:
        cc_v = (
            subprocess.check_output(["cc", "--version"]).decode("utf-8").split("\n")[0]
        )
    except Exception:
        cc_v = "unknown"

    try:
        import pybind11

        pybind11_v = pybind11.__version__
    except ImportError:
        pybind11_v = "unknown"

    # Attempt to get liboqs version (from liboqs_src/.git if available, otherwise unknown)
    try:
        oqs_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd="liboqs_src")
            .strip()
            .decode("utf-8")
        )
    except Exception:
        oqs_commit = "unknown"

    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "cpu": platform.processor(),
        "python_version": platform.python_version(),
        "compiler_version": cc_v,
        "cmake_version": cmake_v,
        "pybind11_version": pybind11_v,
        "liboqs_version": oqs_commit,
        "git_commit": commit,
    }


class ExperimentLogger:
    def __init__(self, base_dir="experiments", random_seed=None):
        from datetime import timezone

        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.exp_dir = os.path.join(base_dir, self.timestamp)
        os.makedirs(self.exp_dir, exist_ok=True)

        # Setup logging
        self.log_file = os.path.join(self.exp_dir, "run.log")
        self.logger = setup_logging(self.log_file)
        self.logger.info(f"Initialized experiment: {self.timestamp}")

        self.writer = SummaryWriter(log_dir=os.path.join(self.exp_dir, "tb_logs"))
        self.system_info = get_system_info()
        self.random_seed = random_seed

    def log_config(self, config_dict):
        config_dict["system_info"] = self.system_info
        config_dict["timestamp"] = self.timestamp
        config_dict["random_seed"] = self.random_seed
        with open(os.path.join(self.exp_dir, "config.json"), "w") as f:
            json.dump(config_dict, f, indent=4)
        self.logger.info("Configuration and system metadata saved.")

    def log_results(self, results):
        self.logger.info(f"Saving benchmark results for {len(results)} models.")
        # Filter out numpy arrays for JSON serialization
        clean_results = []
        for res in results:
            clean = {
                k: v
                for k, v in res.items()
                if k not in ["fpr", "tpr", "prec", "rec", "confusion_matrix"]
            }
            # Convert confusion matrix to list
            if "confusion_matrix" in res:
                clean["confusion_matrix"] = res["confusion_matrix"].tolist()
            clean_results.append(clean)

            # Log to TensorBoard
            self.writer.add_scalar(f"AUC/{res['model_name']}", res.get("roc_auc", 0), 0)
            self.writer.add_scalar(f"F1/{res['model_name']}", res.get("f1", 0), 0)

        with open(
            os.path.join(self.exp_dir, "metrics.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(clean_results, f, indent=4)

        import pandas as pd

        df = pd.DataFrame(clean_results)
        df.to_csv(os.path.join(self.exp_dir, "benchmark.csv"), index=False)

        # Write markdown table
        clean_results.sort(
            key=lambda x: (x.get("f1", 0), x.get("mcc", 0), x.get("roc_auc", 0)),
            reverse=True,
        )

        with open(os.path.join(self.exp_dir, "benchmark_summary.md"), "w") as f:
            f.write("# Aegis PQC Benchmark Summary\n\n")
            f.write(
                "| Model | F1 Score | MCC | ROC AUC | PR AUC | Balanced Acc | Train Time (s) | Inference Time (s) |\n"
            )
            f.write(
                "|-------|----------|-----|---------|--------|--------------|----------------|--------------------|\n"
            )
            f.writelines(
                f"| {r['model_name']} | {r.get('f1',0):.4f} | {r.get('mcc',0):.4f} | {r.get('roc_auc',0):.4f} | {r.get('pr_auc',0):.4f} | {r.get('balanced_accuracy',0):.4f} | {r.get('train_time_s',0):.4f} | {r.get('inference_time_s',0):.4f} |\n"
                for r in clean_results
            )

        self.logger.info("Benchmark summary generated.")
        return self.exp_dir

    def close(self):
        self.writer.close()
        self.logger.info("Experiment logging complete.")
