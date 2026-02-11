"""
CRIS — Preprocessing
Pulls features + labels from SQL, handles cleaning, and performs time-based splitting.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db_connector import run_query


# ──────────────────────────────────────────────
# Feature columns (from SQL view)
# ──────────────────────────────────────────────
FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary",
    "avg_order_value_lifetime",
    "avg_order_value_last_3m",
    "trend_ratio",
    "orders_last_3m",
    "orders_first_3m",
    "cancel_rate",
    "return_rate",
    "unique_categories",
    "avg_items_per_order",
    "unique_products",
    "avg_days_between_orders",
]

TARGET_COLUMN = "is_churned"


def load_feature_matrix() -> pd.DataFrame:
    """
    Pull customer features + churn labels from SQL Server.
    Returns a single DataFrame ready for modeling.
    """
    sql = """
    SELECT
        cf.*,
        cl.is_churned
    FROM dbo.customer_features cf
    INNER JOIN dbo.customer_labels cl
        ON cf.customer_id = cl.customer_id
    """
    df = run_query(sql)
    print(f"Loaded {len(df)} rows with {len(df.columns)} columns.")
    print(f"Churn distribution:\n{df['is_churned'].value_counts()}")
    return df


def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values and data type issues."""
    # Fill NaN in numeric columns with 0
    for col in FEATURE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Remove any rows with NaN target
    df = df.dropna(subset=[TARGET_COLUMN])

    return df


def get_train_test_split(df: pd.DataFrame):
    """
    Time-based split:
    - Training: All labeled data (features computed from Jan-Jun 2024)
    - We simulate a temporal split by using a 70/30 stratified split
      since all features are from the same observation window.

    In a real production system, we would train on one time period
    and test on the next. Here we use stratified split to maintain
    class balance in both sets.
    """
    from sklearn.model_selection import train_test_split

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    print(f"\nTrain set: {len(X_train)} rows")
    print(f"Test set:  {len(X_test)} rows")
    print(f"Train churn rate: {y_train.mean():.2%}")
    print(f"Test churn rate:  {y_test.mean():.2%}")

    return X_train, X_test, y_train, y_test


def scale_features(X_train: pd.DataFrame, X_test: pd.DataFrame):
    """Apply StandardScaler. Returns scaled arrays and the fitted scaler."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler


def prepare_data():
    """Full preprocessing pipeline. Returns everything needed for modeling."""
    df = load_feature_matrix()
    df = clean_features(df)
    X_train, X_test, y_train, y_test = get_train_test_split(df)
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
        "scaler": scaler,
        "feature_names": FEATURE_COLUMNS,
        "raw_df": df,
    }


if __name__ == "__main__":
    data = prepare_data()
    print("\n✅ Preprocessing complete.")
    print(f"Features: {data['feature_names']}")
