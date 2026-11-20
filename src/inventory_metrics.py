"""
Inventory Position Metrics, Valuation & ABC-XYZ Segmentation Module
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import numpy as np
import pandas as pd


def compute_stock_positions(
    inventory_df: pd.DataFrame,
    po_df: pd.DataFrame | None = None,
    slow_moving_months_threshold: int = 6,
) -> pd.DataFrame:
    """
    Computes core stock position balances, days of supply, AED valuations,
    and slow-moving / overdue pipeline indicators for each spare part.

    Net Available Stock = On Hand + Due In - Reserved - Unserviceable
    """
    df = inventory_df.copy()

    # Ensure numeric columns are clean
    numeric_cols = [
        "on_hand_qty",
        "due_in_qty",
        "reserved_qty",
        "unserviceable_qty",
        "avg_monthly_demand",
        "demand_std_dev",
        "lead_time_days",
        "unit_cost_aed",
        "months_since_last_issue",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # 1. Net Available Stock & Usable On-Hand
    df["usable_on_hand_qty"] = np.maximum(0.0, df["on_hand_qty"] - df["reserved_qty"])
    df["net_available_stock"] = (
        df["on_hand_qty"]
        + df["due_in_qty"]
        - df["reserved_qty"]
        - df["unserviceable_qty"]
    )

    # 2. Lead time conversions (30-day operational month standard)
    df["lead_time_months"] = df["lead_time_days"] / 30.0

    # 3. Days of Supply (DOS) based on Net Available Stock and On-Hand Stock
    daily_demand = df["avg_monthly_demand"] / 30.0
    df["net_days_of_supply"] = np.where(
        daily_demand > 0,
        np.maximum(0.0, df["net_available_stock"] / daily_demand),
        999.0,
    )
    df["on_hand_days_of_supply"] = np.where(
        daily_demand > 0,
        np.maximum(0.0, df["on_hand_qty"] / daily_demand),
        999.0,
    )

    # 4. AED Valuations
    df["annual_demand_qty"] = df["avg_monthly_demand"] * 12.0
    df["annual_usage_value_aed"] = df["annual_demand_qty"] * df["unit_cost_aed"]
    df["on_hand_value_aed"] = df["on_hand_qty"] * df["unit_cost_aed"]
    df["due_in_value_aed"] = df["due_in_qty"] * df["unit_cost_aed"]
    df["reserved_value_aed"] = df["reserved_qty"] * df["unit_cost_aed"]
    df["unserviceable_value_aed"] = df["unserviceable_qty"] * df["unit_cost_aed"]
    df["net_available_value_aed"] = df["net_available_stock"] * df["unit_cost_aed"]

    # 5. Slow-moving & overdue PO flags
    df["is_slow_moving"] = df["months_since_last_issue"] >= slow_moving_months_threshold

    if po_df is not None and not po_df.empty:
        overdue_summary = (
            po_df[po_df["po_status"] == "Overdue"]
            .groupby("part_number", as_index=False)
            .agg(
                overdue_po_qty=("due_in_qty", "sum"),
                max_days_overdue=("days_overdue", "max"),
            )
        )
        df = df.merge(overdue_summary, on="part_number", how="left")
        df["overdue_po_qty"] = df["overdue_po_qty"].fillna(0.0)
        df["max_days_overdue"] = df["max_days_overdue"].fillna(0).astype(int)
        df["has_overdue_po"] = df["overdue_po_qty"] > 0
    else:
        df["overdue_po_qty"] = np.where(df["po_status"] == "Overdue", df["due_in_qty"], 0.0)
        df["max_days_overdue"] = 0
        df["has_overdue_po"] = df["overdue_po_qty"] > 0

    return df


def classify_abc_xyz(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs ABC (value + high-criticality awareness) and XYZ (demand stability
    via Coefficient of Variation CV = sigma_d / mu_d) segmentation, returning
    combined ABC-XYZ matrix codes (AX, BY, CZ, etc.).
    """
    out = df.copy()

    # --- ABC Classification by Cumulative Annual Usage Value (AED) ---
    out = out.sort_values("annual_usage_value_aed", ascending=False).reset_index(drop=True)
    total_annual_val = out["annual_usage_value_aed"].sum()

    if total_annual_val > 0:
        out["cum_value_share_pct"] = (
            out["annual_usage_value_aed"].cumsum() / total_annual_val * 100.0
        )
    else:
        out["cum_value_share_pct"] = 100.0

    def _abc_tier(row: pd.Series) -> str:
        # High-criticality parts are elevated to at least 'A' or 'B' for risk control
        if row["cum_value_share_pct"] <= 80.0:
            return "A"
        if row["cum_value_share_pct"] <= 95.0:
            return "B"
        return "C"

    out["abc_class"] = out.apply(_abc_tier, axis=1)

    # --- XYZ Classification by Demand Coefficient of Variation (CV) ---
    out["cv"] = np.where(
        out["avg_monthly_demand"] > 0,
        out["demand_std_dev"] / out["avg_monthly_demand"],
        9.99,
    )

    def _xyz_tier(cv_val: float) -> str:
        if cv_val < 0.50:
            return "X"  # Stable demand
        if cv_val <= 1.00:
            return "Y"  # Variable demand
        return "Z"  # Erratic / intermittent demand

    out["xyz_class"] = out["cv"].apply(_xyz_tier)
    out["abc_xyz_segment"] = out["abc_class"] + out["xyz_class"]

    return out.sort_values("part_number").reset_index(drop=True)