"""
CRIS - Model Training Script
Trains Logistic Regression, Random Forest, and XGBoost.
Evaluates and saves the best model.
"""

import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    average_precision_score,
    roc_auc_score,
    f1_score
)

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("XGBoost not installed. Skipping XGBoost model.")

from src.preprocessing import prepare_data, FEATURE_COLUMNS


def evaluate_model(model, X, y, model_name, needs_scaling=False, X_scaled=None):
    """Evaluate a model and return metrics."""
    X_eval = X_scaled if needs_scaling else X
    
    y_pred = model.predict(X_eval)
    y_prob = model.predict_proba(X_eval)[:, 1]
    
    pr_auc = average_precision_score(y, y_prob)
    roc = roc_auc_score(y, y_prob)
    f1 = f1_score(y, y_pred)
    
    print(f"\n{'='*50}")
    print(f"  {model_name}")
    print(f"{'='*50}")
    print(f"  PR-AUC:   {pr_auc:.4f}")
    print(f"  ROC-AUC:  {roc:.4f}")
    print(f"  F1-Score: {f1:.4f}")
    print(classification_report(y, y_pred, target_names=["Safe", "Churned"]))
    
    return {'name': model_name, 'model': model, 'pr_auc': pr_auc, 'roc_auc': roc, 'f1': f1,
            'needs_scaling': needs_scaling}


def train_and_evaluate():
    print("Step 1: Preparing data...")
    data = prepare_data()
    
    X_train = data['X_train']
    X_test = data['X_test']
    y_train = data['y_train']
    y_test = data['y_test']
    X_train_scaled = data['X_train_scaled']
    X_test_scaled = data['X_test_scaled']
    scaler = data['scaler']

    print(f"Training on {len(X_train)} rows, testing on {len(X_test)} rows.")

    results = []

    # 1. Logistic Regression
    print("\nTraining Logistic Regression...")
    lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    results.append(evaluate_model(lr, X_test, y_test, 'Logistic Regression', needs_scaling=True, X_scaled=X_test_scaled))

    # 2. Random Forest
    print("\nTraining Random Forest...")
    rf = RandomForestClassifier(n_estimators=200, class_weight='balanced', max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    results.append(evaluate_model(rf, X_test, y_test, 'Random Forest'))

    # 3. XGBoost
    if HAS_XGBOOST:
        print("\nTraining XGBoost...")
        n_neg = (y_train == 0).sum()
        n_pos = (y_train == 1).sum()
        spw = n_neg / n_pos if n_pos > 0 else 1
        
        xgb = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            scale_pos_weight=spw,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        xgb.fit(X_train, y_train)
        results.append(evaluate_model(xgb, X_test, y_test, 'XGBoost'))

    # Save Best Model
    best = max(results, key=lambda r: r['pr_auc'])
    print(f"\n🏆 Best model: {best['name']} (PR-AUC: {best['pr_auc']:.4f})")

    joblib.dump(best['model'], MODELS_DIR / 'best_model.pkl')
    joblib.dump(scaler, MODELS_DIR / 'scaler.pkl')
    
    import json
    metadata = {
        'model_name': best['name'],
        'pr_auc': best['pr_auc'],
        'roc_auc': best['roc_auc'],
        'f1': best['f1'],
        'features': FEATURE_COLUMNS,
        'needs_scaling': best['needs_scaling']
    }
    with open(MODELS_DIR / 'model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"✅ Model artifacts saved to {MODELS_DIR}")

if __name__ == "__main__":
    train_and_evaluate()
