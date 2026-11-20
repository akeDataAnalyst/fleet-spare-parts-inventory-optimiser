"""
Page 3: Excess Stock, Slow-Moving Items & Tied-Up Working Capital (AED)
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import sys
from pathlib import Path
import plotly.express as px
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

configure_page(title="Excess & Slow-Moving Stock", icon="")

datasets = load_inventory_data()
plan_full = datasets["optimisation_plan"]

# ---------------------------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------------------------
st.sidebar.header("Excess & Slow-Moving Filters")
hubs = sorted(plan_full["hub_location"].dropna().unique().tolist())
sel_hubs = st.sidebar.multiselect("UAE Hub Location", hubs, default=hubs)
min_dos = st.sidebar.slider("Minimum Net Days of Supply (DOS)", min_value=0, max_value=360, value=120, step=15)
only_flagged = st.sidebar.checkbox("Show only Excess / Slow-Moving SKUs", value=True)
render_sidebar_footer()

df = plan_full[plan_full["hub_location"].isin(sel_hubs)].copy()
excess_mask = (df["excess_stock_qty"] > 0) | (df["is_slow_moving"]) | (df["net_days_of_supply"] >= min_dos)
view_df = df[excess_mask].copy() if only_flagged else df.copy()

if view_df.empty:
    st.info("No spare parts meet the current excess or slow-moving criteria.")
    st.stop()

# ---------------------------------------------------------------------------
# Header & Working Capital KPIs
# ---------------------------------------------------------------------------
st.title("Excess Stock, Slow-Moving Parts & Working Capital Audit")
st.markdown(
    "Identify capital tied up in overstocked units (AED), slow-moving parts with long periods since "
    "last issue, and unserviceable cores awaiting workshop repair."
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Excess Stock Value", format_aed(df["excess_stock_value_aed"].sum()))
k2.metric("Slow-Moving SKUs (>=6M)", int(df["is_slow_moving"].sum()))
k3.metric("Unserviceable Core Value", format_aed(df["unserviceable_value_aed"].sum()))
k4.metric("Median Net DOS", f"{view_df['net_days_of_supply'].median():,.0f} days")

st.markdown("---")

# ---------------------------------------------------------------------------
# Excess Value Chart & Detailed Table
# ---------------------------------------------------------------------------
st.subheader("Tied-Up Excess Inventory Value by Part (AED)")
top_excess = view_df.sort_values("excess_stock_value_aed", ascending=False).head(12)

fig = px.bar(
    top_excess,
    x="part_name",
    y="excess_stock_value_aed",
    color="hub_location",
    text_auto=",.0f",
    labels={"excess_stock_value_aed": "Excess Stock Value (AED)", "part_name": "Spare Part", "hub_location": "UAE Hub"},
)
fig.update_layout(
    height=400,
    template="plotly_white",
    xaxis_tickangle=-30,
    yaxis_tickformat=",.0f",
    margin=dict(l=15, r=15, t=25, b=80),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Excess & Slow-Moving Inventory Register")
cols = [
    "part_number",
    "part_name",
    "hub_location",
    "abc_xyz_segment",
    "on_hand_qty",
    "unserviceable_qty",
    "net_available_stock",
    "target_stock_qty",
    "excess_stock_qty",
    "excess_stock_value_aed",
    "net_days_of_supply",
    "months_since_last_issue",
    "is_slow_moving",
    "recommended_action",
]
st.dataframe(
    view_df[cols].sort_values(["excess_stock_value_aed", "net_days_of_supply"], ascending=[False, False]),
    use_container_width=True,
    hide_index=True,
)