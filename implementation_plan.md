# CRIS — Customer Risk Intelligence System — Implementation Plan

## Overview

Build a complete ML-powered customer risk scoring system from scratch at `d:\VNIT\Projects\CRIS`. The system follows a **SQL-First** architecture: raw data → SQL Server (Docker) → SQL feature engineering → Python ML → Streamlit dashboard.

> [!IMPORTANT]
> This is a greenfield project — the target directory is currently empty. All code, data, and configuration will be created from scratch.

---

## Proposed Changes

### 1. Project Scaffolding

#### [NEW] [docker-compose.yml](file:///d:/VNIT/Projects/CRIS/docker-compose.yml)
Docker Compose file to spin up a SQL Server 2022 Linux container with SA credentials and persistent volume.

#### [NEW] [requirements.txt](file:///d:/VNIT/Projects/CRIS/requirements.txt)
Python dependencies: `pyodbc`, `sqlalchemy`, `pandas`, `scikit-learn`, `xgboost`, `matplotlib`, `seaborn`, `streamlit`, `joblib`.

#### [NEW] [.gitignore](file:///d:/VNIT/Projects/CRIS/.gitignore)
Ignore `models/*.pkl`, `__pycache__`, `.env`, Docker volumes, notebook checkpoints.

---

### 2. Synthetic Data Generation

#### [NEW] [data/raw/customers.csv](file:///d:/VNIT/Projects/CRIS/data/raw/customers.csv)
~200 synthetic customers with columns: `customer_id`, `name`, `email`, `signup_date`, `region`, `segment`.

#### [NEW] [data/raw/orders.csv](file:///d:/VNIT/Projects/CRIS/data/raw/orders.csv)
~1500 orders with columns: `order_id`, `customer_id`, `order_date`, `total_amount`, `status`.

#### [NEW] [data/raw/order_items.csv](file:///d:/VNIT/Projects/CRIS/data/raw/order_items.csv)
~4000 items with columns: `item_id`, `order_id`, `product_name`, `category`, `quantity`, `unit_price`.

Data spans **Jan 2024 – Aug 2024** to support observation (Jan–Jun) and prediction (Jul–Aug) windows.

---

### 3. SQL Layer

#### [NEW] [sql/schema_creation.sql](file:///d:/VNIT/Projects/CRIS/sql/schema_creation.sql)
- `CREATE TABLE customers` (PK: `customer_id`)
- `CREATE TABLE orders` (PK: `order_id`, FK → `customers`)
- `CREATE TABLE order_items` (PK: `item_id`, FK → `orders`)

#### [NEW] [sql/target_engineering.sql](file:///d:/VNIT/Projects/CRIS/sql/target_engineering.sql)
- Defines observation cutoff (`2024-06-30`) and prediction window (`2024-07-01` to `2024-08-31`)
- Labels customers as `is_churned = 1` (no orders in prediction window) or `0`
- Creates a `customer_labels` view/table

#### [NEW] [sql/feature_eng.sql](file:///d:/VNIT/Projects/CRIS/sql/feature_eng.sql)
Creates `Customer_Features` view with:
- **RFM**: `recency_days`, `frequency`, `monetary`
- **Trends**: `avg_order_value_last_3m`, `avg_order_value_lifetime`, `trend_ratio`
- **Ratios**: `cancel_rate`, `unique_categories`, `avg_items_per_order`

---

### 4. TDDQ — Test-Driven Data Quality

#### [NEW] [sql/tests/test_schema.sql](file:///d:/VNIT/Projects/CRIS/sql/tests/test_schema.sql)
Asserts: PK uniqueness, NOT NULL constraints, FK integrity.

#### [NEW] [sql/tests/test_target_logic.sql](file:///d:/VNIT/Projects/CRIS/sql/tests/test_target_logic.sql)
Asserts: churn labels match expected logic (customers with orders in prediction window → 0, without → 1).

#### [NEW] [sql/tests/test_leakage.sql](file:///d:/VNIT/Projects/CRIS/sql/tests/test_leakage.sql)
Asserts: 0% overlap — features only use data from observation window, labels only from prediction window.

#### [NEW] [src/run_tddq.py](file:///d:/VNIT/Projects/CRIS/src/run_tddq.py)
Python runner: executes each `.sql` test file, reports PASS/FAIL for each assertion.

---

### 5. Python Source Layer

#### [NEW] [src/db_connector.py](file:///d:/VNIT/Projects/CRIS/src/db_connector.py)
- `get_engine()` → SQLAlchemy engine using `pyodbc` driver
- `run_sql_file(path)` → executes a `.sql` file against the engine
- `run_query(sql)` → returns a `pd.DataFrame`

#### [NEW] [src/data_ingestion.py](file:///d:/VNIT/Projects/CRIS/src/data_ingestion.py)
- Reads CSVs from `data/raw/`
- Bulk-inserts into SQL Server tables
- Runs schema creation SQL first

#### [NEW] [src/preprocessing.py](file:///d:/VNIT/Projects/CRIS/src/preprocessing.py)
- Pulls `Customer_Features` + `customer_labels` from SQL
- Handles missing values, scaling
- Time-based train/test split

#### [NEW] [src/inference.py](file:///d:/VNIT/Projects/CRIS/src/inference.py)
- Loads serialized model from `models/`
- Accepts customer ID → queries SQL features → returns risk probability

---

### 6. Notebooks

#### [NEW] [notebooks/01_eda.ipynb](file:///d:/VNIT/Projects/CRIS/notebooks/01_eda.ipynb)
- Churn distribution, RFM distributions, correlation heatmap, time-series order trends

#### [NEW] [notebooks/02_modeling.ipynb](file:///d:/VNIT/Projects/CRIS/notebooks/02_modeling.ipynb)
- Logistic Regression baseline → Random Forest → XGBoost
- Evaluation: PR-AUC, F1, Confusion Matrix, Feature Importances
- Saves best model to `models/best_model.pkl`

---

### 7. Streamlit Dashboard

#### [NEW] [app/main.py](file:///d:/VNIT/Projects/CRIS/app/main.py)
- Sidebar: customer ID selector
- Main panel: risk score gauge, feature breakdown, recommended action
- Batch mode: table of all customers with risk scores, sortable/filterable

---

### 8. Documentation

#### [NEW] [README.md](file:///d:/VNIT/Projects/CRIS/README.md)
Project overview, setup instructions, architecture diagram, usage, interview defense notes.

---

## Verification Plan

### Automated Tests
1. **TDDQ suite**: `python src/run_tddq.py` — runs all SQL assertion tests
2. **Data ingestion check**: `python src/data_ingestion.py` — verify row counts match CSV line counts
3. **Model training**: `python -c "from src.preprocessing import *; print('OK')"` — verify imports work

### Manual Verification
1. **Docker**: Run `docker compose up -d` and confirm SQL Server is accessible on port `1433`
2. **Streamlit**: Run `streamlit run app/main.py` and verify a customer risk score is displayed
3. **Notebook**: Open `notebooks/02_modeling.ipynb`, run all cells, verify PR-AUC > 0.5 (better than random)

> [!NOTE]
> Since this is a greenfield project with synthetic data, the primary verification is that the full pipeline runs end-to-end without errors and produces reasonable outputs.
