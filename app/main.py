"""
CRIS — Streamlit Dashboard
Interactive risk scoring interface for business stakeholders.

Usage:
    streamlit run app/main.py
"""

import sys
import json
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

# Silence pandas downcasting warnings
pd.set_option('future.no_silent_downcasting', True)

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db_connector import run_query
from src.preprocessing import FEATURE_COLUMNS

MODELS_DIR = PROJECT_ROOT / "models"

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="CRIS | Customer Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS (Dark/Light Mode Compatible)
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Gradient Headers */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem !important;
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.1rem;
        font-style: italic;
        opacity: 0.8;
        margin-top: -10px;
        margin-bottom: 2rem;
    }

    /* Risk Cards with localized shadows */
    .risk-card {
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .risk-card:hover {
        transform: translateY(-2px);
    }
    
    .risk-high { background: linear-gradient(135deg, #FF416C, #FF4B2B); }
    .risk-medium { background: linear-gradient(135deg, #F7971E, #FFD200); }
    .risk-low { background: linear-gradient(135deg, #11998e, #38ef7d); }

    /* Metric Cards - adaptive transparency */
    div.stMetric {
        background-color: rgba(128, 128, 128, 0.05); /* Subtle background for both modes */
        border: 1px solid rgba(128, 128, 128, 0.1);
        border-radius: 10px;
        padding: 15px;
    }

    /* Tabs styling adjustment */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────
@st.cache_resource
def load_model():
    """Load the trained model and scaler."""
    import joblib
    try:
        model = joblib.load(MODELS_DIR / "best_model.pkl")
        scaler_path = MODELS_DIR / "scaler.pkl"
        scaler = joblib.load(scaler_path) if scaler_path.exists() else None
        
        metadata = {}
        meta_path = MODELS_DIR / "model_metadata.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                metadata = json.load(f)
        return model, scaler, metadata
    except FileNotFoundError:
        return None, None, None

def get_risk_style(prob):
    """Return styling details based on probability."""
    if prob >= 0.7:
        return "HIGH RISK", "risk-high", "🚨"
    elif prob >= 0.4:
        return "MEDIUM RISK", "risk-medium", "⚠️"
    else:
        return "LOW RISK", "risk-low", "✅"


# ──────────────────────────────────────────────
# Sidebar Navigation & Info
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/shield.png", width=60)
    st.title("CRIS")
    st.caption("Customer Risk Intelligence System v2.0")
    
    st.divider()
    
    mode = st.radio(
        "Navigation",
        ["🎯 Single Customer", "📊 Batch Analysis"],
        help="Switch between individual customer deep-dive and portfolio-wide analysis."
    )
    
    st.divider()
    
    # Model Status
    model, scaler, metadata = load_model()
    if metadata:
        with st.expander("Model Performance", expanded=True):
            st.metric("Algorithm", metadata.get('model_name', 'N/A'))
            col_a, col_b = st.columns(2)
            col_a.metric("PR-AUC", f"{metadata.get('pr_auc', 0):.2f}")
            col_b.metric("F1-Score", f"{metadata.get('f1', 0):.2f}")
    else:
        st.error("Model not found! Run training pipeline.")

    with st.expander("About"):
        st.markdown("""
        **CRIS** predicts customer churn risk using historical transaction data.
        
        - **Observation**: Jan-Jun 2024
        - **Prediction**: Jul-Aug 2024
        """)


# ──────────────────────────────────────────────
# Main Header
# ──────────────────────────────────────────────
st.markdown('<p class="main-header">🛡️ Customer Risk Intelligence</p>', unsafe_allow_html=True)
if mode == "🎯 Single Customer":
    st.markdown('<p class="sub-header">Individual Customer Deep Dive & Action Planning</p>', unsafe_allow_html=True)
else:
    st.markdown('<p class="sub-header">Portfolio-Wide Risk Assessment & Segmentation</p>', unsafe_allow_html=True)

st.divider()


if not model:
    st.warning("⚠️ Model artifacts missing. Please run `src/train_model.py`.")
    st.stop()


# ──────────────────────────────────────────────
# MODE: Single Customer
# ──────────────────────────────────────────────
if mode == "🎯 Single Customer":
    col_search, col_action = st.columns([1, 3])
    
    with col_search:
        # Fetch all customers for dropdown
        customers = run_query("SELECT customer_id, name FROM dbo.customers ORDER BY customer_id")
        # Create a mapping for display
        customer_map = {row.customer_id: f"#{row.customer_id} - {row.name}" for _, row in customers.iterrows()}
        
        selected_id = st.selectbox(
            "Select Customer",
            options=customers['customer_id'],
            format_func=lambda x: customer_map.get(x, str(x))
        )
        
        if st.button("Analyze Profile", type="primary", width="stretch"):
            st.session_state['analyzed_id'] = selected_id

    # Use session state to persist analysis
    current_id = st.session_state.get('analyzed_id', selected_id)

    # Fetch Data
    features_df = run_query(f"SELECT * FROM dbo.customer_features WHERE customer_id = {current_id}")
    
    if not features_df.empty:
        # Preprocess for Inference
        X = features_df[FEATURE_COLUMNS].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        if scaler and metadata.get("needs_scaling"):
            X_input = scaler.transform(X)
        else:
            X_input = X
            
        prob = model.predict_proba(X_input)[0][1]
        risk_label, css_class, icon = get_risk_style(prob)
        
        # ─── Top Dashboard: Risk Card & Key Metrics ───
        c1, c2, c3 = st.columns([1.5, 1, 1])
        
        with c1:
            st.markdown(f"""
            <div class="risk-card {css_class}">
                <div style="font-size: 1.2rem; opacity: 0.9;">Risk Assessment</div>
                <div style="font-size: 3rem; font-weight: 800; margin: 10px 0;">{prob:.1%}</div>
                <div style="font-size: 1.5rem;">{icon} {risk_label}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.metric("Total Spend (Lifetime)", f"${features_df['monetary'].iloc[0]:,.2f}", delta_color="normal")
            st.metric("Orders (Lifetime)", int(features_df['frequency'].iloc[0]))
            
        with c3:
            recency = int(features_df['recency_days'].iloc[0])
            st.metric("Days Since Last Order", f"{recency} days", 
                      delta=f"-{recency} days" if recency > 30 else "Active", delta_color="inverse")
            st.metric("Avg Order Value", f"${features_df['avg_order_value_lifetime'].iloc[0]:.2f}")

        # ─── Tabbed Analysis ───
        tab1, tab2, tab3 = st.tabs(["📊 Feature Deep Dive", "📋 Action Plan", "🗓️ Raw Data"])
        
        with tab1:
            st.markdown("### How this customer compares")
            
            # --- Comparative Chart ---
            # Get averages for context
            avg_stats = run_query("SELECT AVG(monetary) as monetary, AVG(frequency) as frequency, AVG(recency_days) as recency_days FROM dbo.customer_features")
            
            comparison_data = pd.DataFrame({
                'Metric': ['Monetary ($)', 'Frequency (Orders)', 'Recency (Days)'],
                'Customer': [features_df['monetary'].iloc[0], features_df['frequency'].iloc[0], features_df['recency_days'].iloc[0]],
                'Average': [avg_stats['monetary'].iloc[0], avg_stats['frequency'].iloc[0], avg_stats['recency_days'].iloc[0]]
            })
            
            # Normalize for visualization (simple scaling)
            # This is a bit complex to do generically in one chart due to scales. 
            # Let's use separate metrics or percentage of average.
            
            cols = st.columns(3)
            metrics = [('monetary', 'Total Spend'), ('frequency', 'Order Count'), ('recency_days', 'Recency')]
            
            for i, (col_name, label) in enumerate(metrics):
                cust_val = features_df[col_name].iloc[0]
                avg_val = avg_stats[col_name].iloc[0]
                pct_diff = ((cust_val - avg_val) / avg_val) * 100
                
                with cols[i]:
                    st.metric(f"{label} vs Avg", f"{cust_val:.1f}", f"{pct_diff:+.1f}%")
                    
            st.markdown("#### Feature Importance Factors")
            # Feature importance simulation (top 5 drivers)
            # In a real app, we'd use SHAP values here. For now, we show the raw values of key features.
            
            key_feats = ['trend_ratio', 'cancel_rate', 'return_rate', 'avg_days_between_orders']
            chart_data = features_df[key_feats].T.reset_index()
            chart_data.columns = ['Feature', 'Value']
            
            c_chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X('Value', title='Value'),
                y=alt.Y('Feature', sort='-x', title='Predictive Indicator'),
                color=alt.Color('Feature', legend=None),
                tooltip=['Feature', 'Value']
            ).properties(height=300)
            st.altair_chart(c_chart, width="stretch")

        with tab2:
            st.markdown("### 🎯 Recommended Strategy")
            
            if risk_label == "HIGH RISK":
                st.error("⚡ **Urgent Retention Required**")
                st.write("""
                - **Primary Action**: Assign to dedicated account manager immediately.
                - **Offer**: 20% discount on next purchase valid for 48 hours.
                - **Channel**: Phone call followed by personalized email.
                """)
            elif risk_label == "MEDIUM RISK":
                st.warning("⚠️ **Proactive Engagement**")
                st.write("""
                - **Primary Action**: Send 'We Miss You' campaign.
                - **Offer**: Free shipping or 10% loyalty bonus.
                - **Channel**: Email and Push Notification.
                """)
            else:
                st.success("✅ **Growth & Upsell**")
                st.write("""
                - **Primary Action**: Recommend complementary products.
                - **Offer**: Early access to new arrivals.
                - **Channel**: Standard newsletter.
                """)
                
            st.info("💡 **Note**: Actions are generated based on risk probability buckets defined in the business logic layer.")

        with tab3:
            st.dataframe(features_df, width="stretch")

    else:
        st.info("Please select a customer and click 'Analyze Profile'.")

# ──────────────────────────────────────────────
# MODE: Batch Analysis
# ──────────────────────────────────────────────
else:
    col_controls, col_viz = st.columns([1, 4])
    
    with col_controls:
        st.subheader("Filters")
        search_query = st.text_input("🔍 Search Customer ID")
        min_prob = st.slider("Min Risk Probability", 0.0, 1.0, 0.0)
        max_prob = st.slider("Max Risk Probability", 0.0, 1.0, 1.0)
        
    with col_viz:
        # Load all data
        with st.spinner("Processing full portfolio..."):
            all_features = run_query("SELECT * FROM dbo.customer_features")
            X_all = all_features[FEATURE_COLUMNS].apply(pd.to_numeric, errors='coerce').fillna(0)
            
            if scaler and metadata.get("needs_scaling"):
                X_input = scaler.transform(X_all)
            else:
                X_input = X_all
                
            probs = model.predict_proba(X_input)[:, 1]
            
            results_df = all_features.copy()
            results_df['Risk Probability'] = probs
            results_df['Risk Label'] = pd.cut(probs, bins=[-0.1, 0.4, 0.7, 1.1], labels=['LOW', 'MEDIUM', 'HIGH'])
            
            # Filter
            filtered_df = results_df[
                (results_df['Risk Probability'] >= min_prob) & 
                (results_df['Risk Probability'] <= max_prob)
            ]
            
            if search_query:
                filtered_df = filtered_df[filtered_df['customer_id'].astype(str).str.contains(search_query)]
            
            # KPI Cards
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Customers", len(filtered_df))
            k2.metric("High Risk", len(filtered_df[filtered_df['Risk Label'] == 'HIGH']), delta_color="inverse")
            k3.metric("Medium Risk", len(filtered_df[filtered_df['Risk Label'] == 'MEDIUM']), delta_color="off")
            k4.metric("Avg Risk Score", f"{filtered_df['Risk Probability'].mean():.1%}")
            
            # Chart
            st.subheader("Risk Distribution")
            chart = alt.Chart(filtered_df).mark_bar().encode(
                x=alt.X('Risk Probability', bin=alt.Bin(maxbins=20)),
                y='count()',
                color=alt.Color('Risk Label', scale=alt.Scale(domain=['LOW', 'MEDIUM', 'HIGH'], range=['#00b894', '#fdcb6e', '#d63031']))
            ).properties(height=250)
            st.altair_chart(chart, width="stretch")
            
            # Table
            st.subheader("Customer Details")
            display_cols = ['customer_id', 'Risk Label', 'Risk Probability', 'monetary', 'frequency', 'recency_days']
            
            st.dataframe(
                filtered_df[display_cols].sort_values('Risk Probability', ascending=False),
                column_config={
                    "Risk Probability": st.column_config.ProgressColumn(
                        "Risk Score",
                        format="%.2f",
                        min_value=0,
                        max_value=1,
                    ),
                },
                width="stretch",
                height=400
            )

            # Download
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Export Risk Report",
                data=csv,
                file_name="cris_risk_report.csv",
                mime="text/csv",
            )
