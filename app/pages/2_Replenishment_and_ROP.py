"""
Page 2: Interactive Safety Stock, Reorder Point (ROP) & Service-Level Simulator
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import sys
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))

from utils import (
    configure_page,
    format_aed,
    load_inventory_data,
    render_sidebar_footer,
)

configure_page(title="Replenishment & ROP Engine", icon="")

datasets = load_inventory_data()
plan_full = datasets["optimisation_plan"]

# ---------------------------------------------------------------------------
# Sidebar Controls (Service Level Z-Score Sensitivity)
# ---------------------------------------------------------------------------
st.sidebar.header("Service Level & Policy Simulator")
hubs = sorted(plan_full["hub_location"].dropna().unique().tolist())
sel_hubs = st.sidebar.multiselect("UAE Hub Location", hubs, default=hubs)

st.sidebar.markdown("**Adjust Z-Score by Criticality**")
z_high = st.sidebar.slider("High Criticality Z (99% = 2.33)", min_value=1.28, max_value=3.09, value=2.33, step=0.01)
z_med = st.sidebar.slider("Medium Criticality Z (95% = 1.65)", min_value=1.00, max_value=2.58, value=1.65, step=0.01)
z_low = st.sidebar.slider("Low Criticality Z (90% = 1.28)", min_value=0.84, max_value=2.05, value=1.28, step=0.01)
cycle_mult = st.sidebar.slider("Order Cycle Stock Multiplier", min_value=0.5, max_value=2.5, value=1.0, step=0.1)
render_sidebar_footer()

sim_df = plan_full[plan_full["hub_location"].isin(sel_hubs)].copy()
if sim_df.empty:
    st.warning("No spare parts match the selected hub filter.")
    st.stop()

z_map = {"High": z_high, "Medium": z_med, "Low": z_low}
sim_df["sim_z_score"] = sim_df["criticality"].map(z_map).fillna(1.65)
sim_df["sim_safety_stock"] = np.ceil(
    np.maximum(0.0, sim_df["sim_z_score"] * sim_df["demand_std_dev"] * np.sqrt(sim_df["lead_time_months"]))
).astype(int)
sim_df["sim_rop"] = np.ceil(
    np.maximum(0.0, sim_df["avg_monthly_demand"] * sim_df["lead_time_months"] + sim_df["sim_safety_stock"])
).astype(int)
sim_df["sim_target_stock"] = np.ceil(
    np.maximum(sim_df["sim_rop"], sim_df["sim_rop"] + sim_df["avg_monthly_demand"] * sim_df["review_cycle_months"] * cycle_mult)
).astype(int)
sim_df["sim_order_qty"] = np.where(
    sim_df["net_available_stock"] <= sim_df["sim_rop"],
    np.ceil(np.maximum(0.0, sim_df["sim_target_stock"] - sim_df["net_available_stock"])),
    0.0,
).astype(int)
sim_df["sim_order_value_aed"] = sim_df["sim_order_qty"] * sim_df["unit_cost_aed"]

# ---------------------------------------------------------------------------
# Header & Simulated KPIs
# ---------------------------------------------------------------------------
st.title("Safety Stock, Reorder Point (ROP) & Order Quantity Engine")
st.markdown(
    "Simulate how changing target service levels ($Z$-scores) and order cycle buffers shifts "
    "Safety Stock, Reorder Points, and recommended AED replenishment quantities."
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Simulated Reorder SKUs", int((sim_df["sim_order_qty"] > 0).sum()))
k2.metric("Total Safety Stock Value", format_aed((sim_df["sim_safety_stock"] * sim_df["unit_cost_aed"]).sum()))
k3.metric("Simulated PO Spend", format_aed(sim_df["sim_order_value_aed"].sum()))
k4.metric("PO Spend Delta vs. Baseline", format_aed(sim_df["sim_order_value_aed"].sum() - sim_df["recommended_order_value_aed"].sum()))

st.markdown("---")

# ---------------------------------------------------------------------------
# Net Available Stock vs. ROP & Target Stock Chart
# ---------------------------------------------------------------------------
st.subheader("Net Available Stock vs. Reorder Point (ROP) & Target Stock")
chart_df = sim_df.sort_values("sim_order_value_aed", ascending=False).head(15)

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=chart_df["part_name"],
        y=chart_df["net_available_stock"],
        name="Net Available Stock",
        marker_color="#1f77b4",
    )
)
fig.add_trace(
    go.Scatter(
        x=chart_df["part_name"],
        y=chart_df["sim_rop"],
        name="Simulated Reorder Point (ROP)",
        mode="lines+markers",
        line=dict(color="#d62728", width=2.5),
    )
)
fig.add_trace(
    go.Scatter(
        x=chart_df["part_name"],
        y=chart_df["sim_target_stock"],
        name="Simulated Target Stock",
        mode="lines+markers",
        line=dict(color="#2ca02c", width=2, dash="dash"),
    )
)
fig.update_layout(
    height=420,
    template="plotly_white",
    xaxis_tickangle=-30,
    yaxis_title="Units",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=15, r=15, t=30, b=80),
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Detailed Replenishment Schedule Table
# ---------------------------------------------------------------------------
st.subheader("Simulated Replenishment & ROP Schedule")
table_cols = [
    "part_number",
    "part_name",
    "hub_location",
    "criticality",
    "sim_z_score",
    "avg_monthly_demand",
    "lead_time_days",
    "net_available_stock",
    "sim_safety_stock",
    "sim_rop",
    "sim_target_stock",
    "sim_order_qty",
    "sim_order_value_aed",
    "recommended_action",
]
st.dataframe(
    sim_df[table_cols].sort_values("sim_order_value_aed", ascending=False),
    use_container_width=True,
    hide_index=True,
)