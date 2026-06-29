import joblib
import logging
import numpy as np
from pathlib import Path
from typing import Optional
from config.settings import settings
from app.core.feature_builder import features_to_array, FEATURE_NAMES

logger = logging.getLogger(__name__)

_model = None
_explainer = None


def load_model() -> None:
    global _model, _explainer
    model_path = Path(settings.MODEL_PATH)
    explainer_path = Path(settings.SHAP_EXPLAINER_PATH)

    if not model_path.exists():
        logger.warning("Fraud model not found at %s. Run training/train.py first.", model_path)
        return

    _model = joblib.load(model_path)
    logger.info("Fraud detection model loaded from %s", model_path)

    if explainer_path.exists():
        _explainer = joblib.load(explainer_path)
        logger.info("SHAP explainer loaded from %s", explainer_path)


def score_transaction(features: dict) -> tuple[float, list[dict]]:
    if _model is None:
        logger.warning("Model not loaded, returning random score for demo purposes.")
        import random
        prob = round(random.uniform(0.1, 0.95), 4)
        return prob, _demo_risk_factors(features, prob)

    X = features_to_array(features)
    prob = float(_model.predict_proba(X)[0][1])
    risk_factors = _compute_shap_factors(X, prob)
    return round(prob, 4), risk_factors


def _compute_shap_factors(X: np.ndarray, prob: float) -> list[dict]:
    if _explainer is None:
        return _demo_risk_factors({}, prob)

    try:
        shap_values = _explainer.shap_values(X)
        vals = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
        pairs = sorted(zip(FEATURE_NAMES, vals), key=lambda x: abs(x[1]), reverse=True)
        return [
            {"feature": name, "impact": round(float(val), 4), "direction": "increases_risk" if val > 0 else "decreases_risk"}
            for name, val in pairs[:8]
        ]
    except Exception as e:
        logger.error("SHAP computation failed: %s", e)
        return []


def _demo_risk_factors(features: dict, prob: float) -> list[dict]:
    factors = []
    if features.get("is_high_risk_mcc"):
        factors.append({"feature": "is_high_risk_mcc", "impact": 0.18, "direction": "increases_risk"})
    if features.get("velocity_1h", 0) > 2:
        factors.append({"feature": "velocity_1h", "impact": 0.15, "direction": "increases_risk"})
    if features.get("amount_zscore", 0) > 2:
        factors.append({"feature": "amount_zscore", "impact": 0.14, "direction": "increases_risk"})
    if features.get("is_new_merchant"):
        factors.append({"feature": "is_new_merchant", "impact": 0.12, "direction": "increases_risk"})
    if features.get("is_night"):
        factors.append({"feature": "is_night", "impact": 0.10, "direction": "increases_risk"})
    if features.get("impossible_travel"):
        factors.append({"feature": "impossible_travel", "impact": 0.25, "direction": "increases_risk"})
    if features.get("is_international"):
        factors.append({"feature": "is_international", "impact": 0.09, "direction": "increases_risk"})
    return factors[:8]


def risk_level_from_prob(prob: float) -> str:
    if prob >= 0.85:
        return "CRITICAL"
    if prob >= 0.65:
        return "HIGH"
    if prob >= 0.40:
        return "MEDIUM"
    return "LOW"
