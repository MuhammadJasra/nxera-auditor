# fraud_model.py — Uses trained LightGBM model to score fraud risk
from __future__ import annotations
import pandas as pd, joblib, os
import numpy as np
import shap

_MODEL_PATH = "fraud_cc_model.pkl"  # Make sure this is in your root directory

def _feature_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert Nxera audit-format ledger to fraud model format:
    - Time: seconds since first transaction
    - Amount: absolute value of transaction
    - V1–V28: filled with 0.0 (as placeholder PCA features)
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    out = pd.DataFrame()
    out["Time"] = (df["date"] - df["date"].min()).dt.total_seconds().fillna(0)
    out["Amount"] = df["amount"].abs().fillna(0)

    # Add V1 to V28 columns as 0.0 — these were used during training
    for i in range(1, 29):
        out[f"V{i}"] = 0.0

    return out

def score_transactions(df: pd.DataFrame) -> pd.Series:
    """
    Apply trained LightGBM model to incoming DataFrame and return
    fraud risk as percentage (0 to 100).
    """
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(
            f"⚠️ Model file '{_MODEL_PATH}' not found. Train it using train_creditcard_fraud.py."
        )

    model = joblib.load(_MODEL_PATH)
    features = _feature_df(df)
    probabilities = model.predict_proba(features)[:, 1]
    return pd.Series((probabilities * 100).round(1), index=df.index)  # as percentage

def shap_explain(df: pd.DataFrame):
    """
    Return SHAP values and expected value for the fraud model for the given DataFrame.
    """
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(
            f"⚠️ Model file '{_MODEL_PATH}' not found. Train it using train_creditcard_fraud.py."
        )
    model = joblib.load(_MODEL_PATH)
    features = _feature_df(df)
    explainer = shap.TreeExplainer(model.named_steps['clf'])
    shap_values = explainer.shap_values(model.named_steps['prep'].transform(features))
    return shap_values, explainer.expected_value, features.columns.tolist()

def shap_natural_language_explanation(df: pd.DataFrame, idx: int) -> str:
    """
    Generate a natural language explanation for a transaction's fraud risk using SHAP values.
    """
    shap_values, expected_value, feature_names = shap_explain(df)
    # Get the top contributing features for this transaction
    contrib = list(zip(feature_names, shap_values[idx]))
    # Sort by absolute SHAP value (importance)
    contrib_sorted = sorted(contrib, key=lambda x: abs(x[1]), reverse=True)
    # Take top 3 features
    top_features = [f for f, v in contrib_sorted[:3] if abs(v) > 0.01]
    risk_pct = score_transactions(df).iloc[idx]
    if not top_features:
        return f"This transaction was flagged as {risk_pct:.1f}% risk (no dominant feature detected)."
    # Map feature names to human-friendly reasons
    feature_map = {
        'Amount': 'large amount',
        'Time': 'date anomaly',
        'V1': 'unusual pattern (V1)',
        'V2': 'unusual pattern (V2)',
        'V3': 'unusual pattern (V3)',
        # ... add more mappings as needed ...
    }
    reasons = [feature_map.get(f, f) for f in top_features]
    reasons = [r for r in reasons if r is not None]
    return f"This transaction was flagged as {risk_pct:.1f}% risk due to: {', '.join(reasons)}."
