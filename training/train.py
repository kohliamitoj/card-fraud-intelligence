"""
Train the fraud detection model.

Usage:
    # Step 1: generate data
    python -m training.generate_synthetic_data

    # Step 2: train
    python -m training.train

    # Or with IEEE-CIS dataset:
    python -m training.train --data data/ieee_cis_transactions.csv
"""
import argparse
import logging
import joblib
import numpy as np
import pandas as pd
import shap
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, average_precision_score, classification_report
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

from training.feature_engineering import build_features, FEATURE_COLS

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"cardholder_id", "amount", "merchant_id", "merchant_category_code",
                 "channel", "location_country", "timestamp", "is_fraud"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing columns: {missing}")
    logger.info("Loaded %d rows | Fraud rate: %.2f%%", len(df), df["is_fraud"].mean() * 100)
    return df


def train(data_path: str, model_out: str, explainer_out: str) -> None:
    df = load_data(data_path)

    logger.info("Engineering features...")
    df = build_features(df)

    X = df[FEATURE_COLS].values.astype(np.float32)
    y = df["is_fraud"].values

    logger.info("Applying SMOTE to handle class imbalance...")
    smote = SMOTE(sampling_strategy=0.15, random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    logger.info("After SMOTE: %d samples | Fraud: %.2f%%", len(y_resampled), y_resampled.mean() * 100)

    model = XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=1,
        use_label_encoder=False,
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
    )

    logger.info("Training with 5-fold cross validation...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_aucs, cv_aps = [], []

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_resampled, y_resampled), 1):
        X_tr, X_val = X_resampled[train_idx], X_resampled[val_idx]
        y_tr, y_val = y_resampled[train_idx], y_resampled[val_idx]
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        preds = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, preds)
        ap = average_precision_score(y_val, preds)
        cv_aucs.append(auc)
        cv_aps.append(ap)
        logger.info("Fold %d | AUC-ROC: %.4f | Avg Precision: %.4f", fold, auc, ap)

    logger.info("CV Mean AUC-ROC: %.4f ± %.4f", np.mean(cv_aucs), np.std(cv_aucs))
    logger.info("CV Mean Avg Precision: %.4f ± %.4f", np.mean(cv_aps), np.std(cv_aps))

    logger.info("Training final model on full dataset...")
    model.fit(X_resampled, y_resampled)

    logger.info("Building SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)

    Path(model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)
    joblib.dump(explainer, explainer_out)
    logger.info("Model saved to %s", model_out)
    logger.info("SHAP explainer saved to %s", explainer_out)

    logger.info("\nFinal model evaluation on original (non-SMOTE) data:")
    orig_preds = model.predict_proba(X)[:, 1]
    final_auc = roc_auc_score(y, orig_preds)
    final_ap = average_precision_score(y, orig_preds)
    logger.info("AUC-ROC: %.4f | Avg Precision: %.4f", final_auc, final_ap)

    threshold = 0.5
    binary_preds = (orig_preds >= threshold).astype(int)
    logger.info("\nClassification Report (threshold=%.2f):\n%s", threshold, classification_report(y, binary_preds))

    feature_importance = sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x: x[1], reverse=True)
    logger.info("\nTop 10 Feature Importances:")
    for feat, imp in feature_importance[:10]:
        logger.info("  %-40s %.4f", feat, imp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/transactions.csv")
    parser.add_argument("--model-out", default="models/fraud_detector.pkl")
    parser.add_argument("--explainer-out", default="models/shap_explainer.pkl")
    args = parser.parse_args()
    train(args.data, args.model_out, args.explainer_out)
