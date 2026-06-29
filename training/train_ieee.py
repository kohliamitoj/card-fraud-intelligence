"""
Train the fraud detection model on the real IEEE-CIS Fraud Detection dataset.

Dataset: https://www.kaggle.com/c/ieee-fraud-detection
Place the Kaggle files in: ieee-fraud-detection/
  - train_transaction.csv
  - train_identity.csv  (optional, improves accuracy)

Usage:
    python -m training.train_ieee
    python -m training.train_ieee --data-dir ieee-fraud-detection --model-out models/fraud_detector.pkl
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
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

V_COLS_SELECTED = [f"V{i}" for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                                       12, 13, 14, 15, 17, 19, 20, 29, 30,
                                       33, 34, 35, 36, 37, 38, 39, 40, 41,
                                       44, 45, 46, 47, 48, 49, 50, 51, 52,
                                       53, 54, 56, 57, 58, 59, 60, 61, 62,
                                       69, 70, 71, 72, 73, 74, 75, 76, 78,
                                       79, 80, 81, 82, 83, 84, 85, 86, 87,
                                       90, 91, 92, 93, 94, 95, 96, 98, 99,
                                       100, 101, 126, 127, 128, 129, 130,
                                       131, 132, 133, 134, 135, 136, 137,
                                       138, 139, 142, 143, 144, 145, 150,
                                       151, 160, 161, 162, 163, 164, 165,
                                       166, 167, 168, 169, 170, 187, 188,
                                       189, 196, 197, 198, 199, 200, 201,
                                       202, 203, 204, 205, 206, 207, 208,
                                       209, 210, 211, 212, 213, 214, 215,
                                       279, 280, 281, 282, 283, 284, 285,
                                       286, 287, 288, 289, 290, 291, 292,
                                       293, 294, 295, 296, 297, 298, 299,
                                       300, 301, 302, 303, 304, 305, 306,
                                       307, 308, 309, 310, 311, 312, 313,
                                       314, 315, 316, 317, 318, 319, 320,
                                       321, 322, 323, 324, 325, 326, 327,
                                       328, 329, 330, 331, 332, 333, 334,
                                       335, 336, 337, 338, 339]]

C_COLS = [f"C{i}" for i in range(1, 15)]
D_COLS = [f"D{i}" for i in range(1, 16)]
M_COLS = [f"M{i}" for i in range(1, 10)]

CARD_COLS = ["card1", "card2", "card3", "card5"]
BASE_COLS = ["TransactionAmt", "dist1", "dist2"]


def load_and_engineer(data_dir: str) -> tuple[pd.DataFrame, list[str]]:
    txn_path = Path(data_dir) / "train_transaction.csv"
    identity_path = Path(data_dir) / "train_identity.csv"

    logger.info("Loading transactions from %s ...", txn_path)
    df = pd.read_csv(txn_path)
    logger.info("Loaded %d rows | Fraud rate: %.3f%%", len(df), df["isFraud"].mean() * 100)

    if identity_path.exists():
        logger.info("Merging identity data ...")
        identity = pd.read_csv(identity_path)
        df = df.merge(identity, on="TransactionID", how="left")
        logger.info("After identity merge: %d rows", len(df))

    df["hour"] = (df["TransactionDT"] // 3600) % 24
    df["day"] = (df["TransactionDT"] // (3600 * 24)) % 7
    df["is_night"] = ((df["hour"] < 6) | (df["hour"] >= 22)).astype(int)
    df["is_weekend"] = (df["day"] >= 5).astype(int)
    df["amount_log"] = np.log1p(df["TransactionAmt"])

    for col in M_COLS:
        if col in df.columns:
            df[col] = df[col].map({"T": 1, "F": 0}).fillna(-1)

    cat_cols = ["ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain"]
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category").cat.codes

    available_v = [c for c in V_COLS_SELECTED if c in df.columns]
    available_c = [c for c in C_COLS if c in df.columns]
    available_d = [c for c in D_COLS if c in df.columns]
    available_m = [c for c in M_COLS if c in df.columns]
    available_card = [c for c in CARD_COLS if c in df.columns]
    extra_cat = [c for c in cat_cols if c in df.columns]

    feature_cols = (
        BASE_COLS + ["hour", "day", "is_night", "is_weekend", "amount_log"]
        + available_card + extra_cat
        + available_c + available_d + available_m
        + available_v
    )
    feature_cols = [c for c in feature_cols if c in df.columns]

    for col in feature_cols:
        if df[col].dtype == object:
            df[col] = df[col].astype("category").cat.codes
        df[col] = df[col].fillna(-999)

    logger.info("Total features: %d", len(feature_cols))
    return df, feature_cols


def train(data_dir: str, model_out: str, explainer_out: str) -> None:
    df, feature_cols = load_and_engineer(data_dir)

    X = df[feature_cols].values.astype(np.float32)
    y = df["isFraud"].values

    fraud_count = y.sum()
    legit_count = len(y) - fraud_count
    scale_pos_weight = legit_count / fraud_count
    logger.info("scale_pos_weight = %.2f (handles class imbalance)", scale_pos_weight)

    model = XGBClassifier(
        n_estimators=500,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.5,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
        tree_method="hist",
    )

    logger.info("Training with 5-fold stratified cross validation ...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_aucs, cv_aps = [], []

    for fold, (tr_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_tr, X_val = X[tr_idx], X[val_idx]
        y_tr, y_val = y[tr_idx], y[val_idx]
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=100)
        preds = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, preds)
        ap = average_precision_score(y_val, preds)
        cv_aucs.append(auc)
        cv_aps.append(ap)
        logger.info("Fold %d | AUC-ROC: %.4f | Avg Precision: %.4f", fold, auc, ap)

    logger.info("CV Mean AUC-ROC : %.4f ± %.4f", np.mean(cv_aucs), np.std(cv_aucs))
    logger.info("CV Mean Avg Prec: %.4f ± %.4f", np.mean(cv_aps), np.std(cv_aps))

    logger.info("Training final model on full dataset ...")
    model.fit(X, y, verbose=100)

    logger.info("Building SHAP TreeExplainer on 5000-sample background ...")
    background = X[np.random.choice(len(X), size=min(5000, len(X)), replace=False)]
    explainer = shap.TreeExplainer(model, background)

    Path(model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)
    joblib.dump(explainer, explainer_out)
    joblib.dump(feature_cols, model_out.replace(".pkl", "_feature_cols.pkl"))

    logger.info("Model saved      → %s", model_out)
    logger.info("SHAP explainer   → %s", explainer_out)
    logger.info("Feature cols     → %s", model_out.replace(".pkl", "_feature_cols.pkl"))

    final_preds = model.predict_proba(X)[:, 1]
    final_auc = roc_auc_score(y, final_preds)
    final_ap = average_precision_score(y, final_preds)
    logger.info("Final train AUC-ROC: %.4f | Avg Precision: %.4f", final_auc, final_ap)
    logger.info("\n%s", classification_report(y, (final_preds >= 0.5).astype(int)))

    importances = sorted(zip(feature_cols, model.feature_importances_), key=lambda x: x[1], reverse=True)
    logger.info("Top 15 features:")
    for feat, imp in importances[:15]:
        logger.info("  %-45s %.4f", feat, imp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="ieee-fraud-detection")
    parser.add_argument("--model-out", default="models/fraud_detector.pkl")
    parser.add_argument("--explainer-out", default="models/shap_explainer.pkl")
    args = parser.parse_args()
    train(args.data_dir, args.model_out, args.explainer_out)
