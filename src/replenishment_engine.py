"""
Safety Stock, Reorder Point (ROP), Target Stock & Action Classification Engine
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import numpy as np
import pandas as pd


CRITICALITY_SERVICE_LEVELS = {
    "High": {"service_level_pct": 99.0, "z_score": 2.33, "review_cycle_months": 1.0},
    "Medium": {"service_level_pct": 95.0, "z_score": 1.65, "review_cycle_months": 1.5},
    "Low": {"service_level_pct": 90.0, "z_score": 1.28, "review_cycle_months": 2.0},
}


def compute_replenishment_plan(
    metrics_df: pd.DataFrame,
    backorder_wo_df: pd.DataFrame | None = None,
    custom_z_override: dict[str, float] | None = None,
) -> pd.DataFrame:
    """
    Calculates target service level, Z-score, Safety Stock, Reorder Point (ROP),
    Target Stock Level (Order-Up-To), Recommended Order Quantity, Excess Stock value,
    and operational Action recommendations.

    Formulas:
      - Safety Stock = Z * sigma_d * sqrt(Lead Time in Months)
      - Reorder Point = (Average Monthly Demand * Lead Time in Months) + Safety Stock
      - Target Stock Level = Reorder Point + (Average Monthly Demand * Review Cycle Months)
      - Recommended Order Quantity = max(0, Target Stock Level - Net Available Stock)
    """
    df = metrics_df.copy()

    # Map service level, Z-score, and review cycle by criticality
    df["target_service_level_pct"] = df["criticality"].map(
        lambda c: CRITICALITY_SERVICE_LEVELS.get(c, CRITICALITY_SERVICE_LEVELS["Medium"])[
            "service_level_pct"
        ]
    )
    df["z_score"] = df["criticality"].map(
        lambda c: CRITICALITY_SERVICE_LEVELS.get(c, CRITICALITY_SERVICE_LEVELS["Medium"])[
            "z_score"
        ]
    )
    df["review_cycle_months"] = df["criticality"].map(
        lambda c: CRITICALITY_SERVICE_LEVELS.get(c, CRITICALITY_SERVICE_LEVELS["Medium"])[
            "review_cycle_months"
        ]
    )

    if custom_z_override:
        for crit_level, z_val in custom_z_override.items():
            mask = df["criticality"] == crit_level
            df.loc[mask, "z_score"] = float(z_val)

    # 1. Safety Stock (rounded up to whole units for practical ordering)
    raw_ss = (
        df["z_score"]
        * df["demand_std_dev"]
        * np.sqrt(np.maximum(df["lead_time_months"], 0.0))
    )
    df["safety_stock_qty"] = np.ceil(np.maximum(0.0, raw_ss)).astype(int)
    df["safety_stock_value_aed"] = df["safety_stock_qty"] * df["unit_cost_aed"]

    # 2. Lead-Time Demand & Reorder Point (ROP)
    lead_time_demand = df["avg_monthly_demand"] * df["lead_time_months"]
    df["lead_time_demand_qty"] = np.round(lead_time_demand, 1)
    df["reorder_point_qty"] = np.ceil(
        np.maximum(0.0, lead_time_demand + df["safety_stock_qty"])
    ).astype(int)

    # 3. Target Stock Level (Order-Up-To Policy) & Recommended Order Quantity
    cycle_buffer = df["avg_monthly_demand"] * df["review_cycle_months"]
    df["target_stock_qty"] = np.ceil(
        np.maximum(df["reorder_point_qty"], df["reorder_point_qty"] + cycle_buffer)
    ).astype(int)

    raw_order_qty = np.where(
        df["net_available_stock"] <= df["reorder_point_qty"],
        df["target_stock_qty"] - df["net_available_stock"],
        0.0,
    )
    df["recommended_order_qty"] = np.ceil(np.maximum(0.0, raw_order_qty)).astype(int)
    df["recommended_order_value_aed"] = df["recommended_order_qty"] * df["unit_cost_aed"]

    # 4. Excess Stock Units & Tied-Up Working Capital (AED)
    excess_threshold_qty = np.ceil(df["target_stock_qty"] * 1.40)
    df["excess_stock_qty"] = np.where(
        df["net_available_stock"] > excess_threshold_qty,
        np.ceil(df["net_available_stock"] - df["target_stock_qty"]),
        0.0,
    ).astype(int)
    df["excess_stock_value_aed"] = df["excess_stock_qty"] * df["unit_cost_aed"]

    # 5. Merge delayed vehicle work order metrics if available
    if backorder_wo_df is not None and not backorder_wo_df.empty:
        wo_agg = (
            backorder_wo_df.groupby("part_number", as_index=False)
            .agg(
                delayed_wo_count=("work_order_id", "count"),
                total_wo_delay_days=("days_delayed", "sum"),
                total_wo_downtime_hrs=("downtime_hours_accumulated", "sum"),
            )
        )
        df = df.merge(wo_agg, on="part_number", how="left")
        df["delayed_wo_count"] = df["delayed_wo_count"].fillna(0).astype(int)
        df["total_wo_delay_days"] = df["total_wo_delay_days"].fillna(0).astype(int)
        df["total_wo_downtime_hrs"] = df["total_wo_downtime_hrs"].fillna(0.0).round(1)
    else:
        df["delayed_wo_count"] = 0
        df["total_wo_delay_days"] = 0
        df["total_wo_downtime_hrs"] = 0.0

    # 6. Action Classification Rules
    def _assign_action(row: pd.Series) -> str:
        # Master data / integrity check first
        if (
            row["avg_monthly_demand"] <= 0
            or row["unit_cost_aed"] <= 0
            or row["lead_time_days"] <= 0
            or row["on_hand_qty"] < 0
        ):
            return "Review master data"

        # Immediate replenishment trigger
        if row["net_available_stock"] <= row["reorder_point_qty"]:
            return "Reorder now"

        # Approaching reorder trigger (within 15% buffer above ROP)
        if row["net_available_stock"] <= row["reorder_point_qty"] * 1.15:
            return "Monitor closely"

        # Overstocked or slow-moving check
        if row["excess_stock_qty"] > 0 or row["is_slow_moving"]:
            return "Excess stock"

        return "Healthy"

    df["recommended_action"] = df.apply(_assign_action, axis=1)

    # 7. Urgent Purchase Requisition (PR) Escalation Flag & Priority Score
    df["urgent_pr_escalation"] = (
        (df["recommended_action"] == "Reorder now")
        & (
            (df["criticality"] == "High")
            | (df["usable_on_hand_qty"] <= df["safety_stock_qty"])
            | (df["delayed_wo_count"] > 0)
            | (df["has_overdue_po"])
        )
    )

    df["stockout_risk_score"] = (
        np.clip(
            (
                np.where(df["net_available_stock"] <= df["reorder_point_qty"], 45.0, 0.0)
                + np.where(df["usable_on_hand_qty"] <= df["safety_stock_qty"], 20.0, 0.0)
                + np.where(df["criticality"] == "High", 15.0, np.where(df["criticality"] == "Medium", 8.0, 3.0))
                + np.minimum(20.0, df["delayed_wo_count"] * 7.0)
            ),
            0.0,
            100.0,
        )
        .round(1)
    )

    return df.sort_values(
        ["urgent_pr_escalation", "stockout_risk_score", "recommended_order_value_aed"],
        ascending=[False, False, False],
    ).reset_index(drop=True)