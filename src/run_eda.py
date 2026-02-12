
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set env var for SQLite
os.environ["CRIS_DB_TYPE"] = "sqlite"

from src.db_connector import run_query, SQLITE_DB_PATH
from src.preprocessing import FEATURE_COLUMNS

# Configure plotting style
sns.set_theme(style="whitegrid", palette="viridis")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 12

REPORT_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORT_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def generate_eda_report():
    print("🚀 Starting Exploratory Data Analysis (Partial)...")
    
    report_lines = ["# Exploratory Data Analysis Report (Partial)\n"]
    report_lines.append("> **Note**: Full churn analysis could not be performed due to missing labels in the local database. This report focuses on customer demographics and behavior.\n")
    
    # 1. Data Loading
    print("  Loading available data...")
    try:
        customers = run_query("SELECT * FROM customers")
        features = run_query("SELECT * FROM customer_features")
        
        # Merge for unified analysis
        df = customers.merge(features, on="customer_id")
        
        report_lines.append(f"## 1. Data Overview\n")
        report_lines.append(f"- **Total Customers**: {len(df)}")
        report_lines.append(f"- **Features Available**: {len(features.columns) - 1}")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return

    # 2. Regional Analysis
    if "region" in df.columns:
        print("  Analyzing regional distribution...")
        region_counts = df["region"].value_counts()
        
        plt.figure(figsize=(10, 5))
        sns.barplot(x=region_counts.index, y=region_counts.values, palette="viridis")
        plt.title("Customer Distribution by Region")
        plt.xlabel("Region")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "region_distribution.png")
        plt.close()
        
        report_lines.append("\n## 2. Demographics\n")
        report_lines.append("### Regional Distribution\n")
        report_lines.append("![Region Distribution](figures/region_distribution.png)\n")
        
    # 3. RFM Analysis (Unlabeled)
    print("  Analyzing RFM distributions...")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for i, col in enumerate(["recency_days", "frequency", "monetary"]):
        if col in df.columns:
            ax = axes[i]
            sns.histplot(data=df, x=col, bins=20, kde=True, ax=ax, color="#3498db")
            ax.set_title(col.replace("_", " ").title())
            ax.set_xlabel(col)
            
    plt.suptitle("RFM Feature Distributions")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "rfm_distribution.png")
    plt.close()
    
    report_lines.append("\n## 3. Behavioral Analysis (RFM)\n")
    report_lines.append("Distribution of Recency, Frequency, and Monetary values across the customer base:\n")
    report_lines.append("![RFM Distribution](figures/rfm_distribution.png)\n")
    
    # 4. Correlation Analysis
    print("  Generating correlation heatmap...")
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        corr_matrix = numeric_df.corr()
        
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f", cmap="coolwarm", center=0)
        plt.title("Feature Correlation Heatmap")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "correlation_heatmap.png")
        plt.close()
        
        report_lines.append("\n## 4. Feature Correlations\n")
        report_lines.append("Relationships between behavioral features:\n")
        report_lines.append("![Correlation Heatmap](figures/correlation_heatmap.png)\n")
    
    # Save Report
    report_path = REPORT_DIR / "eda_summary.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines("\n".join(report_lines))
        
    print(f"✅ Partial EDA complete! Report saved to {report_path}")

if __name__ == "__main__":
    generate_eda_report()
