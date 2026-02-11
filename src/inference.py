"""
CRIS — Inference Engine
Loads a trained model and computes risk scores for individual customers.
"""

import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db_connector import run_query
from src.preprocessing import FEATURE_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


def load_model(model_name: str = "best_model.pkl"):
    """Load a serialized model and scaler from disk."""
    model_path = MODELS_DIR / model_name
    scaler_path = MODELS_DIR / "scaler.pkl"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}\n"
            "Run the modeling notebook first to train and save a model."
        )

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path) if scaler_path.exists() else None

    return model, scaler


def get_customer_features(customer_id: int) -> pd.DataFrame:
    """Fetch features for a single customer from SQL."""
    sql = f"""
    SELECT *
    FROM dbo.customer_features
    WHERE customer_id = {customer_id}
    """
    df = run_query(sql)
    if df.empty:
        raise ValueError(f"No features found for customer_id={customer_id}")
    return df


def predict_risk(customer_id: int, model=None, scaler=None) -> dict:
    """
    Compute risk score for a given customer.

    Returns:
        dict with customer_id, risk_probability, risk_class, features
    """
    if model is None:
        model, scaler = load_model()

    # Get features from SQL
    features_df = get_customer_features(customer_id)
    X = features_df[FEATURE_COLUMNS].copy()

    # Fill any missing values
    X = X.fillna(0)

    # Scale if scaler is available
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X.values

    # Predict probability
    risk_prob = model.predict_proba(X_scaled)[0][1]  # P(churned=1)

    # Classify risk level
    if risk_prob >= 0.7:
        risk_class = "HIGH RISK"
    elif risk_prob >= 0.4:
        risk_class = "MEDIUM RISK"
    else:
        risk_class = "LOW RISK"

    return {
        "customer_id": customer_id,
        "risk_probability": round(float(risk_prob), 4),
        "risk_class": risk_class,
        "features": features_df[FEATURE_COLUMNS].iloc[0].to_dict(),
    }


def batch_predict(customer_ids: list = None) -> pd.DataFrame:
    """
    Predict risk for multiple customers.
    If customer_ids is None, predicts for all customers with features.
    """
    model, scaler = load_model()

    if customer_ids is None:
        sql = "SELECT customer_id FROM dbo.customer_features"
        customer_ids = run_query(sql)["customer_id"].tolist()

    results = []
    for cid in customer_ids:
        try:
            result = predict_risk(cid, model=model, scaler=scaler)
            results.append(result)
        except ValueError:
            continue

    df = pd.DataFrame(results)
    df = df.sort_values("risk_probability", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("CRIS Inference Engine")
    print("─" * 40)

    try:
        # Test with customer_id = 1
        result = predict_risk(1)
        print(f"\nCustomer {result['customer_id']}:")
        print(f"  Risk Probability: {result['risk_probability']:.2%}")
        print(f"  Risk Class: {result['risk_class']}")
        print(f"  Key Features:")
        for k, v in result["features"].items():
            print(f"    {k}: {v}")
    except FileNotFoundError as e:
        print(f"\n⚠️ {e}")
