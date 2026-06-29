"""
Evaluate a trained model and generate performance plots.
Run: python -m training.evaluate
"""
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import (
    roc_auc_score, average_precision_score, confusion_matrix,
    precision_recall_curve, roc_curve, classification_report,
)
from training.feature_engineering import build_features, FEATURE_COLS

MODEL_PATH = "models/fraud_detector.pkl"
DATA_PATH = "data/transactions.csv"
OUTPUT_DIR = "models/evaluation"


def evaluate():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    model = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)
    df = build_features(df)

    X = df[FEATURE_COLS].values.astype(np.float32)
    y = df["is_fraud"].values
    probs = model.predict_proba(X)[:, 1]

    auc = roc_auc_score(y, probs)
    ap = average_precision_score(y, probs)
    print(f"AUC-ROC: {auc:.4f}")
    print(f"Average Precision: {ap:.4f}")

    _plot_roc_curve(y, probs, auc)
    _plot_pr_curve(y, probs, ap)
    _plot_confusion_matrix(y, probs, threshold=0.5)
    _plot_score_distribution(y, probs)
    _plot_feature_importance(model)

    print(f"\nAll plots saved to {OUTPUT_DIR}/")
    print("\nClassification Report (threshold=0.5):\n")
    print(classification_report(y, (probs >= 0.5).astype(int)))


def _plot_roc_curve(y, probs, auc):
    fpr, tpr, _ = roc_curve(y, probs)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f"AUC = {auc:.4f}", color="steelblue", lw=2)
    plt.plot([0, 1], [0, 1], "k--", lw=1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve — Card Fraud Detection")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/roc_curve.png", dpi=150)
    plt.close()


def _plot_pr_curve(y, probs, ap):
    precision, recall, _ = precision_recall_curve(y, probs)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, label=f"AP = {ap:.4f}", color="darkorange", lw=2)
    plt.axhline(y=y.mean(), color="gray", linestyle="--", label="Baseline")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve — Card Fraud Detection")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/pr_curve.png", dpi=150)
    plt.close()


def _plot_confusion_matrix(y, probs, threshold):
    preds = (probs >= threshold).astype(int)
    cm = confusion_matrix(y, preds)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Legitimate", "Fraud"],
                yticklabels=["Legitimate", "Fraud"])
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"Confusion Matrix (threshold={threshold})")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/confusion_matrix.png", dpi=150)
    plt.close()


def _plot_score_distribution(y, probs):
    plt.figure(figsize=(10, 5))
    plt.hist(probs[y == 0], bins=50, alpha=0.6, color="steelblue", label="Legitimate", density=True)
    plt.hist(probs[y == 1], bins=50, alpha=0.6, color="crimson", label="Fraud", density=True)
    plt.axvline(0.5, color="black", linestyle="--", label="Threshold (0.5)")
    plt.xlabel("Fraud Probability Score")
    plt.ylabel("Density")
    plt.title("Score Distribution — Fraud vs Legitimate Transactions")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/score_distribution.png", dpi=150)
    plt.close()


def _plot_feature_importance(model):
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:15]
    plt.figure(figsize=(10, 6))
    plt.barh(
        [FEATURE_COLS[i].replace("_", " ").title() for i in indices[::-1]],
        importances[indices[::-1]],
        color="steelblue",
    )
    plt.xlabel("Feature Importance (Gain)")
    plt.title("Top 15 Features — XGBoost Fraud Detector")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/feature_importance.png", dpi=150)
    plt.close()


if __name__ == "__main__":
    evaluate()
