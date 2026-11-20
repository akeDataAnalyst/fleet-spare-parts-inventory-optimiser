"""
Executive Overview: Fleet Spare-Parts Inventory Replenishment & Safety Stock Optimiser
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import plotly.express as px
import streamlit as st
from utils import (
    ACTION_COLOR_MAP,
    configure_page,
    format_aed,
    load_inventory_data,
    render_sidebar_footer,
)

configure_page(title="Executive Inventory Overview", icon="")

datasets = load_inventory_data()
plan_full = datasets["optimisation_plan"]
po_full = datasets["open_purchase_orders"]
bo_full = datasets["backordered_work_orders"]

# ---------------------------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------------------------
st.sidebar.header("Fleet & Hub Filters")
hub_options = sorted(plan_full["hub_location"].dropna().unique().tolist())
veh_options = sorted(plan_full["vehicle_type"].dropna().unique().tolist())
crit_options = ["High", "Medium", "Low"]

selected_hubs = st.sidebar.multiselect("UAE Hub Location", options=hub_options, default=hub_options)
selected_vehicles = st.sidebar.multiselect("Vehicle Class", options=veh_options, default=veh_options)
selected_crits = st.sidebar.multiselect("Criticality Level", options=crit_options, default=crit_options)
render_sidebar_footer()

filt_mask = (
    plan_full["hub_location"].isin(selected_hubs)
    & plan_full["vehicle_type"].isin(selected_vehicles)
    & plan_full["criticality"].isin(selected_crits)
)
plan_df = plan_full[filt_mask].copy()
po_df = po_full[po_full["hub_location"].isin(selected_hubs)].copy()
bo_df = bo_full[
    bo_full["hub_location"].isin(selected_hubs) & bo_full["vehicle_type"].isin(selected_vehicles)
].copy()

if plan_df.empty:
    st.warning("No spare parts match the active filter combination. Adjust filters in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# Header & Executive KPIs
# ---------------------------------------------------------------------------
st.title("Fleet Spare-Parts Inventory Replenishment & Safety Stock Optimiser")
st.markdown(
    "Evaluate Net Available Stock, criticality-driven Safety Stock and Reorder Points (ROP), "
    "excess working capital in AED, overdue supplier due-ins, and delayed vehicle work orders."
)

reorder_now_count = int((plan_df["recommended_action"] == "Reorder now").sum())
urgent_pr_count = int(plan_df["urgent_pr_escalation"].sum())
total_order_val_aed = float(plan_df["recommended_order_value_aed"].sum())
excess_val_aed = float(plan_df["excess_stock_value_aed"].sum())
delayed_wo_count = int(len(bo_df))
delayed_downtime_hrs = float(bo_df["downtime_hours_accumulated"].sum()) if not bo_df.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Reorder Now SKUs", f"{reorder_now_count} / {len(plan_df)}", help="Net Available Stock <= Reorder Point")
k2.metric("Urgent PR Escalations", f"{urgent_pr_count} parts", delta="Immediate Action", delta_color="inverse")
k3.metric("Recommended PO Value", format_aed(total_order_val_aed))
k4.metric("Excess Stock Tied Up", format_aed(excess_val_aed))
k5.metric("Delayed Work Orders", f"{delayed_wo_count} WOs", delta=f"{delayed_downtime_hrs:,.0f} hrs downtime", delta_color="inverse")

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 1: Action Distribution & Recommended Order Spend by Hub
# ---------------------------------------------------------------------------
c1, c2 = st.columns([1, 1.25])

with c1:
    st.subheader("Replenishment Action Breakdown")
    action_order = ["Reorder now", "Monitor closely", "Healthy", "Excess stock", "Review master data"]
    action_counts = (
        plan_df["recommended_action"]
        .value_counts()
        .reindex(action_order, fill_value=0)
        .reset_index()
    )
    action_counts.columns = ["Action", "SKU_Count"]
    action_counts = action_counts[action_counts["SKU_Count"] > 0]

    fig_act = px.bar(
        action_counts,
        x="Action",
        y="SKU_Count",
        color="Action",
        color_discrete_map=ACTION_COLOR_MAP,
        text_auto=True,
        labels={"SKU_Count": "Number of SKUs", "Action": ""},
    )
    fig_act.update_layout(
        height=370,
        template="plotly_white",
        showlegend=False,
        margin=dict(l=10, r=10, t=25, b=10),
    )
    st.plotly_chart(fig_act, use_container_width=True)

with c2:
    st.subheader("Recommended PO Spend vs. Excess Stock by Hub (AED)")
    hub_val = (
        plan_df.groupby("hub_location", as_index=False)
        .agg(
            Recommended_PO_AED=("recommended_order_value_aed", "sum"),
            Excess_Stock_AED=("excess_stock_value_aed", "sum"),
        )
        .melt(
            id_vars="hub_location",
            value_vars=["Recommended_PO_AED", "Excess_Stock_AED"],
            var_name="Capital_Metric",
            value_name="Amount_AED",
        )
    )
    hub_val["Capital_Metric"] = hub_val["Capital_Metric"].replace(
        {
            "Recommended_PO_AED": "Recommended Order Value",
            "Excess_Stock_AED": "Excess Stock Value",
        }
    )

    fig_hub = px.bar(
        hub_val,
        x="hub_location",
        y="Amount_AED",
        color="Capital_Metric",
        barmode="group",
        text_auto=",.0f",
        color_discrete_map={
            "Recommended Order Value": "#d62728",
            "Excess Stock Value": "#1f77b4",
        },
        labels={"hub_location": "UAE Hub", "Amount_AED": "Value (AED)", "Capital_Metric": ""},
    )
    fig_hub.update_layout(
        height=370,
        template="plotly_white",
        yaxis_tickformat=",.0f",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=25, b=10),
    )
    st.plotly_chart(fig_hub, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 2: Priority Replenishment & Escalation Queue
# ---------------------------------------------------------------------------
st.subheader("Priority Replenishment & Stock-Out Risk Queue")
queue_cols = [
    "part_number",
    "part_name",
    "hub_location",
    "vehicle_type",
    "criticality",
    "abc_xyz_segment",
    "on_hand_qty",
    "due_in_qty",
    "reserved_qty",
    "unserviceable_qty",
    "net_available_stock",
    "safety_stock_qty",
    "reorder_point_qty",
    "recommended_order_qty",
    "recommended_order_value_aed",
    "delayed_wo_count",
    "urgent_pr_escalation",
    "stockout_risk_score",
    "recommended_action",
]

sorted_queue = plan_df.sort_values(
    ["urgent_pr_escalation", "stockout_risk_score", "recommended_order_value_aed"],
    ascending=[False, False, False],
)

st.dataframe(
    sorted_queue[queue_cols],
    use_container_width=True,
    hide_index=True,
)