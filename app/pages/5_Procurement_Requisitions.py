"""
Page 5: Urgent Purchase Requisition (PR) Escalations & Reorder Export
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import sys
from pathlib import Path
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))

from utils import (
    PROCESSED_DIR,
    configure_page,
    format_aed,
    load_inventory_data,
    render_sidebar_footer,
)

configure_page(title="Procurement Requisitions", icon="")

datasets = load_inventory_data()
plan_full = datasets["optimisation_plan"].copy()

# ---------------------------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------------------------
st.sidebar.header("Requisition Filters")
hubs = sorted(plan_full["hub_location"].dropna().unique().tolist())
crits = ["High", "Medium", "Low"]

sel_hubs = st.sidebar.multiselect("UAE Hub Location", hubs, default=hubs)
sel_crits = st.sidebar.multiselect("Criticality Level", crits, default=crits)
only_urgent_pr = st.sidebar.checkbox("Show Urgent PR Escalations only", value=False)
only_order_needed = st.sidebar.checkbox("Show only parts with Recommended Order > 0", value=True)
render_sidebar_footer()

df = plan_full[
    plan_full["hub_location"].isin(sel_hubs) & plan_full["criticality"].isin(sel_crits)
].copy()

if only_urgent_pr:
    df = df[df["urgent_pr_escalation"]].copy()
if only_order_needed:
    df = df[df["recommended_order_qty"] > 0].copy()

# ---------------------------------------------------------------------------
# Header & Requisition KPIs
# ---------------------------------------------------------------------------
st.title("Procurement Requisitions & Reorder Recommendation Export")
st.markdown(
    "Review parts requiring immediate replenishment, escalate **Urgent Purchase Requisitions (PRs)** "
    "impacting critical fleet assets or active work orders, and export a ready-to-process reorder list."
)

urgent_df = df[df["urgent_pr_escalation"]] if not df.empty else df
k1, k2, k3, k4 = st.columns(4)
k1.metric("Requisition Line Items", len(df))
k2.metric("Urgent PR Escalations", len(urgent_df))
k3.metric("Total Requisition Value", format_aed(df["recommended_order_value_aed"].sum() if not df.empty else 0.0))
k4.metric("Urgent PR Value", format_aed(urgent_df["recommended_order_value_aed"].sum() if not urgent_df.empty else 0.0))

st.markdown("---")

if df.empty:
    st.info("No spare parts match the selected requisition filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Requisition Table & CSV Export
# ---------------------------------------------------------------------------
export_cols = [
    "snapshot_date",
    "part_number",
    "part_name",
    "category",
    "vehicle_type",
    "hub_location",
    "supplier",
    "criticality",
    "abc_xyz_segment",
    "on_hand_qty",
    "due_in_qty",
    "reserved_qty",
    "unserviceable_qty",
    "net_available_stock",
    "safety_stock_qty",
    "reorder_point_qty",
    "target_stock_qty",
    "recommended_order_qty",
    "unit_cost_aed",
    "recommended_order_value_aed",
    "delayed_wo_count",
    "total_wo_downtime_hrs",
    "urgent_pr_escalation",
    "stockout_risk_score",
    "recommended_action",
]

sorted_req = df.sort_values(
    ["urgent_pr_escalation", "stockout_risk_score", "recommended_order_value_aed"],
    ascending=[False, False, False],
)[export_cols]

st.subheader("Actionable Purchase Requisition Schedule")
st.dataframe(sorted_req, use_container_width=True, hide_index=True)

# Persist & offer instant CSV download
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
reorder_csv_path = PROCESSED_DIR / "procurement_reorder_plan.csv"
sorted_req.to_csv(reorder_csv_path, index=False)

st.download_button(
    label="Download Procurement Reorder Plan (CSV)",
    data=sorted_req.to_csv(index=False).encode("utf-8"),
    file_name="procurement_reorder_plan.csv",
    mime="text/csv",
)