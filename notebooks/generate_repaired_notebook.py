import nbformat as nbf
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()

nb.cells.append(new_markdown_cell("# CRIS — Exploratory Data Analysis (Repaired)\n\nThis is a repaired version of the EDA notebook that gracefully handles missing tables in the local SQLite database."))

nb.cells.append(new_code_cell("""
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Force SQLite for local EDA
os.environ['CRIS_DB_TYPE'] = 'sqlite'
sys.path.insert(0, '..')

from src.db_connector import run_query

# Style
sns.set_theme(style='whitegrid', palette='viridis')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 12

print('Libraries loaded.')
"""))

nb.cells.append(new_code_cell("""
# Load tables safely
try:
    customers = run_query('SELECT * FROM customers')
except Exception:
    customers = pd.DataFrame()
    print("Could not load customers")

try:
    orders = run_query('SELECT * FROM orders')
except Exception:
    orders = pd.DataFrame()
    print("Could not load orders (missing in local DB)")

try:
    items = run_query('SELECT * FROM order_items')
except Exception:
    items = pd.DataFrame()
    print("Could not load items (missing in local DB)")

try:
    labels = run_query('SELECT * FROM customer_labels')
except Exception:
    labels = pd.DataFrame()
    print("Could not load labels (missing in local DB)")
    
try:
    features = run_query('SELECT * FROM customer_features')
except Exception:
    features = pd.DataFrame()
    print("Could not load features")

print(f'Customers: {len(customers)} rows')
print(f'Orders:    {len(orders)} rows')
print(f'Items:     {len(items)} rows')
"""))

nb.cells.append(new_markdown_cell("## 1. Demographics Analysis"))

nb.cells.append(new_code_cell("""
if not customers.empty and 'region' in customers.columns:
    region_counts = customers['region'].value_counts()
    plt.figure(figsize=(10,5))
    sns.barplot(x=region_counts.index, y=region_counts.values, palette='viridis')
    plt.title('Customer Distribution by Region')
    plt.show()
else:
    print("Skipping regional analysis due to missing data.")
"""))

nb.cells.append(new_markdown_cell("## 2. Feature Analysis"))

nb.cells.append(new_code_cell("""
if not features.empty:
    cols_to_plot = ['recency_days', 'frequency', 'monetary']
    valid_cols = [c for c in cols_to_plot if c in features.columns]
    
    if valid_cols:
        fig, axes = plt.subplots(1, len(valid_cols), figsize=(6*len(valid_cols), 5))
        if len(valid_cols) == 1: axes = [axes]
        
        for i, col in enumerate(valid_cols):
            sns.histplot(data=features, x=col, bins=20, kde=True, ax=axes[i])
            axes[i].set_title(col)
        plt.tight_layout()
        plt.show()
else:
    print("Skipping feature analysis.")
"""))

with open('notebooks/01_eda_repaired.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Created notebooks/01_eda_repaired.ipynb")
