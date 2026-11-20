"""
Page 1: Stock Position Reconciliation & ABC-XYZ Segmentation
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))

from utils import (
    ACTION_COLOR_MAP,
    configure_page,
    format_aed,
    load_inventory_data,
    render_sidebar_footer,
)

configure_page(title="Stock Position & ABC-XYZ", icon="")

datasets = load_inventory_data()
plan_full = datasets["optimisation_plan"]

# ---------------------------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
hubs = sorted(plan_full["hub_location"].dropna().unique().tolist())
segments = sorted(plan_full["abc_xyz_segment"].dropna().unique().tolist())
actions = sorted(plan_full["recommended_action"].dropna().unique().tolist())

sel_hubs = st.sidebar.multiselect("UAE Hub Location", hubs, default=hubs)
sel_segments = st.sidebar.multiselect("ABC-XYZ Segment", segments, default=segments)
sel_actions = st.sidebar.multiselect("Recommended Action", actions, default=actions)
render_sidebar_footer()

df = plan_full[
    plan_full["hub_location"].isin(sel_hubs)
    & plan_full["abc_xyz_segment"].isin(sel_segments)
    & plan_full["recommended_action"].isin(sel_actions)
].copy()

if df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Header & KPIs
# ---------------------------------------------------------------------------
st.title("Stock Position Reconciliation & ABC-XYZ Matrix")
st.markdown(
    "Compare On-Hand, Due-In, Reserved, and Unserviceable quantities to evaluate "
    "Net Available Stock and segment spare parts by value (ABC) and demand stability (XYZ)."
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("On-Hand Stock Value", format_aed(df["on_hand_value_aed"].sum()))
k2.metric("Due-In Pipeline Value", format_aed(df["due_in_value_aed"].sum()))
k3.metric("Reserved + Unserviceable", format_aed(df["reserved_value_aed"].sum() + df["unserviceable_value_aed"].sum()))
k4.metric("Net Available Value", format_aed(df["net_available_value_aed"].sum()))

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 1: ABC-XYZ Heatmap & Segment Valuation
# ---------------------------------------------------------------------------
c1, c2 = st.columns([1, 1.25])

with c1:
    st.subheader("ABC-XYZ SKU Count Matrix")
    matrix_ct = pd.crosstab(
        df["abc_class"],
        df["xyz_class"],
    ).reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"], fill_value=0)

    fig_hm = px.imshow(
        matrix_ct,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        labels={"x": "XYZ Demand Stability (CV)", "y": "ABC Value Tier", "color": "SKUs"},
    )
    fig_hm.update_layout(height=360, margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(fig_hm, use_container_width=True)

with c2:
    st.subheader("Annual Usage Value (AED) by ABC-XYZ Segment")
    seg_summary = (
        df.groupby(["abc_xyz_segment", "recommended_action"], as_index=False)
        .agg(annual_usage_aed=("annual_usage_value_aed", "sum"))
        .sort_values("annual_usage_aed", ascending=False)
    )
    fig_seg = px.bar(
        seg_summary,
        x="abc_xyz_segment",
        y="annual_usage_aed",
        color="recommended_action",
        color_discrete_map=ACTION_COLOR_MAP,
        labels={"abc_xyz_segment": "ABC-XYZ Segment", "annual_usage_aed": "Annual Usage (AED)", "recommended_action": "Action"},
    )
    fig_seg.update_layout(
        height=360,
        template="plotly_white",
        yaxis_tickformat=",.0f",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=25, b=10),
    )
    st.plotly_chart(fig_seg, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 2: Part-Level Stock Balance & Net Available Stock Table
# ---------------------------------------------------------------------------
st.subheader("Part-Level Stock Balance & ABC-XYZ Breakdown")
display_cols = [
    "part_number",
    "part_name",
    "hub_location",
    "abc_xyz_segment",
    "cv",
    "on_hand_qty",
    "due_in_qty",
    "reserved_qty",
    "unserviceable_qty",
    "net_available_stock",
    "net_days_of_supply",
    "annual_usage_value_aed",
    "net_available_value_aed",
    "recommended_action",
]
st.dataframe(
    df[display_cols].sort_values(["abc_xyz_segment", "annual_usage_value_aed"], ascending=[True, False]),
    use_container_width=True,
    hide_index=True,
)