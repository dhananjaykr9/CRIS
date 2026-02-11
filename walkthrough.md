# CRIS — Walkthrough

## What Was Built

A complete **Customer Risk Intelligence System** — 21 files across 8 phases.

### Project Structure

```
CRIS/                           (21 files)
├── docker-compose.yml          SQL Server 2022 container
├── requirements.txt            Python deps (9 packages)
├── .gitignore                  Ignores models, caches, Docker volumes
├── README.md                   Full documentation + setup guide
│
├── data/raw/                   Synthetic data
│   ├── customers.csv           200 customers
│   ├── orders.csv              989 orders (Jan–Aug 2024)
│   └── order_items.csv         3,005 items
│
├── sql/                        SQL-First Layer
│   ├── schema_creation.sql     3 tables (PK/FK/indexes)
│   ├── target_engineering.sql  Time-aware churn labels
│   ├── feature_eng.sql         15-feature SQL view (RFM/trends/ratios)
│   └── tests/                  TDDQ assertions
│       ├── test_schema.sql     PK uniqueness, NOT NULL, FK integrity
│       ├── test_target_logic.sql  Churn label correctness
│       └── test_leakage.sql    No future data in features
│
├── src/                        Python Engine
│   ├── db_connector.py         SQLAlchemy + pyodbc (GO-batch aware)
│   ├── data_ingestion.py       CSV → SQL pipeline
│   ├── preprocessing.py        Feature cleaning + stratified split
│   ├── inference.py            Single/batch prediction
│   └── run_tddq.py            SQL test runner
│
├── notebooks/
│   ├── 01_eda.ipynb            7 analysis sections
│   └── 02_modeling.ipynb       LogReg + RF + XGBoost + model saving
│
├── app/
│   └── main.py                 Streamlit dashboard (2 modes)
│
└── models/                     .pkl output directory
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| SQL-First features | Scalable to BigQuery/Snowflake; features live in DB |
| Observation/Prediction windows | Prevents data leakage |
| TDDQ before modeling | Validates data at source |
| PR-AUC metric | Handles class imbalance |
| `class_weight='balanced'` | Penalizes missing churned customers |

## Phase 9: UI Enhancement
- **Tabbed Interface**: Feature Deep Dive, Action Plan, Raw Data
- **Comparative Analysis**: Metrics vs Portfolio Average
- **Visualizations**: Interactive Altair charts for risk distribution
- **Batch Mode**: Advanced filtering & search

## Phase 10: Deployment
- **Git**: Initialized and pushed to GitHub
- **Repo**: [dhananjaykr9/CRIS](https://github.com/dhananjaykr9/CRIS)

## How to Run

```bash
git clone https://github.com/dhananjaykr9/CRIS.git
cd CRIS
docker compose up -d              # 1. Start SQL Server
pip install -r requirements.txt   # 2. Install deps
python src/data_ingestion.py      # 3. Load data + build features
python src/run_tddq.py            # 4. Validate data quality
python src/train_model.py         # 5. Train models (New script)
streamlit run app/main.py         # 6. Launch dashboard
```
