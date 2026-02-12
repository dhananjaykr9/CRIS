import nbformat as nbf
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()

nb.cells.append(new_markdown_cell("# CRIS — Exploratory Data Analysis (Full SQL)\n\nThis notebook is the original analysis designed for SQL Server, but updated to run robustly."))

nb.cells.append(new_code_cell("""
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure project root is in path
sys.path.insert(0, '..')

from src.db_connector import run_query

# Style
sns.set_theme(style='whitegrid', palette='viridis')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 12

print('Libraries loaded.')
"""))

nb.cells.append(new_code_cell("""
# Load tables safely - Using run_query which handles DB differences
try:
    customers = run_query('SELECT * FROM customers')
except Exception as e:
    customers = pd.DataFrame()
    print(f"Could not load customers: {e}")

try:
    orders = run_query('SELECT * FROM orders')
except Exception as e:
    orders = pd.DataFrame()
    print(f"Could not load orders: {e}")

try:
    items = run_query('SELECT * FROM order_items')
except Exception as e:
    items = pd.DataFrame()
    print(f"Could not load items: {e}")

try:
    labels = run_query('SELECT * FROM customer_labels')
except Exception as e:
    labels = pd.DataFrame()
    print(f"Could not load labels: {e}")
    
try:
    features = run_query('SELECT * FROM customer_features')
except Exception as e:
    features = pd.DataFrame()
    print(f"Could not load features: {e}")

print(f'Customers: {len(customers)} rows')
print(f'Orders:    {len(orders)} rows')
print(f'Items:     {len(items)} rows')
"""))

with open('notebooks/01_eda_full_sql.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Regenerated notebooks/01_eda_full_sql.ipynb")
