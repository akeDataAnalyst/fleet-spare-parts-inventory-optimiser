"""
Page 4: Supplier Lead Times, Due-In Purchase Orders & Delayed Work Orders
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
    PROCESSED_DIR,
    configure_page,
    format_aed,
    load_inventory_data,
    render_sidebar_footer,
)

configure_page(title="Supplier & PO Tracking", icon="")

datasets = load_inventory_data()
po_full = datasets["open_purchase_orders"].copy()
bo_full = datasets["backordered_work_orders"].copy()
plan_full = datasets["optimisation_plan"].copy()

# ---------------------------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------------------------
st.sidebar.header("Supplier & Hub Filters")
hubs = sorted(plan_full["hub_location"].dropna().unique().tolist())
suppliers = sorted(plan_full["supplier"].dropna().unique().tolist())
po_statuses = sorted(po_full["po_status"].dropna().unique().tolist()) if not po_full.empty else []

sel_hubs = st.sidebar.multiselect("UAE Hub Location", hubs, default=hubs)
sel_suppliers = st.sidebar.multiselect("Supplier", suppliers, default=suppliers)
sel_po_status = (
    st.sidebar.multiselect("PO Pipeline Status", po_statuses, default=po_statuses)
    if po_statuses
    else []
)
render_sidebar_footer()

po_df = po_full[
    po_full["hub_location"].isin(sel_hubs) & po_full["supplier"].isin(sel_suppliers)
].copy()
if sel_po_status and not po_df.empty:
    po_df = po_df[po_df["po_status"].isin(sel_po_status)].copy()

bo_df = bo_full[bo_full["hub_location"].isin(sel_hubs)].copy()
plan_df = plan_full[
    plan_full["hub_location"].isin(sel_hubs) & plan_full["supplier"].isin(sel_suppliers)
].copy()

# ---------------------------------------------------------------------------
# Header & KPIs
# ---------------------------------------------------------------------------
st.title("Supplier Lead Times, Due-In POs & Delayed Work Orders")
st.markdown(
    "Track incoming purchase orders (**AED**), flag overdue supplier deliveries, benchmark lead times "
    "across UAE vendors, and quantify vehicle work orders delayed due to unavailable parts."
)

overdue_pos = po_df[po_df["po_status"] == "Overdue"] if not po_df.empty else po_df
due_in_val = float(po_df["po_value_aed"].sum()) if not po_df.empty else 0.0
overdue_val = float(overdue_pos["po_value_aed"].sum()) if not overdue_pos.empty else 0.0
avg_lt = float(plan_df["lead_time_days"].mean()) if not plan_df.empty else 0.0
delayed_wos = int(len(bo_df))
downtime_hrs = float(bo_df["downtime_hours_accumulated"].sum()) if not bo_df.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Due-In PO Value", format_aed(due_in_val))
k2.metric("Overdue POs", f"{len(overdue_pos)} POs", delta=format_aed(overdue_val), delta_color="inverse")
k3.metric("Avg Lead Time", f"{avg_lt:.1f} days")
k4.metric("Delayed Work Orders", f"{delayed_wos} WOs")
k5.metric("Accumulated Downtime", f"{downtime_hrs:,.1f} hrs")

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 1: Supplier Lead Time & PO Value Charts
# ---------------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Average Supplier Lead Time (Days)")
    if not plan_df.empty:
        lt_summary = (
            plan_df.groupby("supplier", as_index=False)
            .agg(avg_lead_time_days=("lead_time_days", "mean"), sku_count=("part_number", "count"))
            .sort_values("avg_lead_time_days", ascending=True)
        )
        lt_summary["avg_lead_time_days"] = lt_summary["avg_lead_time_days"].round(1)
        fig_lt = px.bar(
            lt_summary,
            x="avg_lead_time_days",
            y="supplier",
            orientation="h",
            text_auto=True,
            labels={"avg_lead_time_days": "Avg Lead Time (Days)", "supplier": "Supplier"},
        )
        fig_lt.update_layout(height=360, template="plotly_white", margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_lt, use_container_width=True)
    else:
        st.info("No supplier lead-time data for current filter.")

with c2:
    st.subheader("Due-In PO Value by Status & Hub (AED)")
    if not po_df.empty:
        po_hub = (
            po_df.groupby(["hub_location", "po_status"], as_index=False)
            .agg(po_value_aed=("po_value_aed", "sum"))
        )
        fig_po = px.bar(
            po_hub,
            x="hub_location",
            y="po_value_aed",
            color="po_status",
            barmode="group",
            text_auto=",.0f",
            color_discrete_map={"Overdue": "#d62728", "In Transit": "#2ca02c"},
            labels={"hub_location": "UAE Hub", "po_value_aed": "PO Value (AED)", "po_status": "Status"},
        )
        fig_po.update_layout(
            height=360,
            template="plotly_white",
            yaxis_tickformat=",.0f",
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig_po, use_container_width=True)
    else:
        st.info("No open purchase orders match current filters.")

# ---------------------------------------------------------------------------
# Row 2: Open POs & Delayed Vehicle Work Orders Tables
# ---------------------------------------------------------------------------
st.subheader("Open Purchase Orders & Due-In Schedule")
if not po_df.empty:
    po_cols = [
        "po_number",
        "part_number",
        "part_name",
        "supplier",
        "hub_location",
        "order_date",
        "expected_receipt_date",
        "due_in_qty",
        "po_value_aed",
        "lead_time_days",
        "days_overdue",
        "po_status",
    ]
    st.dataframe(
        po_df[po_cols].sort_values(["days_overdue", "po_value_aed"], ascending=[False, False]),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No open purchase orders available.")

st.subheader("Backordered Vehicle Work Orders (Delayed Due to Missing Parts)")
if not bo_df.empty:
    bo_cols = [
        "work_order_id",
        "vehicle_id",
        "vehicle_type",
        "hub_location",
        "part_number",
        "part_name",
        "criticality",
        "wo_opened_date",
        "days_delayed",
        "downtime_hours_accumulated",
        "qty_required",
        "delay_reason",
    ]
    st.dataframe(
        bo_df[bo_cols].sort_values(["downtime_hours_accumulated", "days_delayed"], ascending=[False, False]),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No delayed vehicle work orders match current filters.")