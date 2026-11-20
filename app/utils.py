"""
Shared Streamlit Utilities, Data Loaders & Formatting Helpers
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.data_generator import generate_inventory_datasets
from src.inventory_metrics import classify_abc_xyz, compute_stock_positions
from src.replenishment_engine import compute_replenishment_plan

ACTION_COLOR_MAP = {
    "Reorder now": "#d62728",
    "Monitor closely": "#ff7f0e",
    "Excess stock": "#1f77b4",
    "Healthy": "#2ca02c",
    "Review master data": "#7f7f7f",
}

CRITICALITY_COLOR_MAP = {
    "High": "#d62728",
    "Medium": "#ff7f0e",
    "Low": "#2ca02c",
}

REQUIRED_PLAN_COLS = {
    "urgent_pr_escalation",
    "stockout_risk_score",
    "recommended_action",
    "recommended_order_qty",
    "recommended_order_value_aed",
    "excess_stock_value_aed",
    "net_available_stock",
    "safety_stock_qty",
    "reorder_point_qty",
    "target_stock_qty",
    "abc_xyz_segment",
}


def configure_page(title: str, icon: str = "📦") -> None:
    """Applies consistent page metadata and layout styling across the app."""
    st.set_page_config(
        page_title=f"{title} | UAE Fleet Inventory Optimiser",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def format_aed(amount: float, decimals: int = 0) -> str:
    """Formats numeric values in UAE Dirhams (AED)."""
    val = float(amount or 0.0)
    if decimals == 0:
        return f"AED {val:,.0f}"
    return f"AED {val:,.{decimals}f}"


@st.cache_data(show_spinner="Loading fleet inventory and replenishment datasets...")
def load_inventory_data() -> dict[str, pd.DataFrame]:
    """
    Loads raw and processed datasets from disk. Automatically runs the
    generator and replenishment pipeline if files are missing or stale.
    """
    raw_files = [
        RAW_DIR / "inventory_snapshot.csv",
        RAW_DIR / "open_purchase_orders.csv",
        RAW_DIR / "backordered_work_orders.csv",
    ]
    if not all(p.exists() for p in raw_files):
        generate_inventory_datasets(
            output_dir=str(RAW_DIR),
            seed=42,
            snapshot_date_str="2025-12-15",
        )

    inv_df = pd.read_csv(RAW_DIR / "inventory_snapshot.csv")
    po_df = pd.read_csv(RAW_DIR / "open_purchase_orders.csv")
    bo_df = pd.read_csv(RAW_DIR / "backordered_work_orders.csv")

    master_path = PROCESSED_DIR / "inventory_optimisation_master.csv"
    rebuild_master = not master_path.exists()

    if not rebuild_master:
        plan_df = pd.read_csv(master_path)
        if not REQUIRED_PLAN_COLS.issubset(plan_df.columns):
            rebuild_master = True

    if rebuild_master:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        metrics_df = classify_abc_xyz(compute_stock_positions(inv_df, po_df))
        plan_df = compute_replenishment_plan(metrics_df, backorder_wo_df=bo_df)
        plan_df.to_csv(master_path, index=False)

    return {
        "inventory_snapshot": inv_df,
        "open_purchase_orders": po_df,
        "backordered_work_orders": bo_df,
        "optimisation_plan": plan_df,
    }


def render_sidebar_footer() -> None:
    """Renders consistent developer attribution in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.caption("Developed by Aklilu Abera Dana | Supply Chain Data Analyst")