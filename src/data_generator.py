"""
Synthetic UAE Commercial Fleet Inventory, Purchase Order & Backorder Data Generator
Author: Aklilu Abera Dana | Supply Chain Data Analyst
"""

import os
import numpy as np
import pandas as pd


def generate_inventory_datasets(
    output_dir: str = "data/raw",
    seed: int = 42,
    snapshot_date_str: str = "2025-12-15",
) -> dict[str, pd.DataFrame]:
    """
    Generates three realistic, cross-linked CSV tables for the Fleet Spare-Parts
    Inventory Replenishment & Safety Stock Optimiser:
      1. inventory_snapshot.csv      (28 SKUs across UAE hubs & vehicle types)
      2. open_purchase_orders.csv    (Pipeline due-in POs with on-time/overdue flags)
      3. backordered_work_orders.csv (Delayed vehicle maintenance WOs awaiting parts)

    All dates are strictly capped within 2025.
    """
    rng = np.random.default_rng(seed)
    os.makedirs(output_dir, exist_ok=True)
    snapshot_date = pd.Timestamp(snapshot_date_str)

    # -----------------------------------------------------------------------
    # 1. Master SKU Catalog (28 Commercial Fleet Spare Parts in AED)
    # -----------------------------------------------------------------------
    parts_catalog = [
        # (part_number, part_name, category, vehicle_type, unit_cost_aed, criticality, lead_time_days, avg_monthly_demand, demand_std, supplier, hub, stock_profile)
        ("PRT-001", "Heavy-Duty Engine Oil Filter", "Filters & Fluids", "Heavy Truck", 95.0, "High", 14, 48.0, 9.5, "Al-Futtaim Auto Parts UAE", "Jebel Ali Hub", "Healthy"),
        ("PRT-002", "Primary Fuel Water Separator", "Filters & Fluids", "Heavy Truck", 165.0, "High", 18, 34.0, 8.2, "Emirates Fleet Supply", "Jebel Ali Hub", "Reorder_Urgent"),
        ("PRT-003", "Cabin Air Filter Element", "Filters & Fluids", "Light Commercial Van", 55.0, "Low", 10, 42.0, 7.0, "Gulf Auto Components", "Sajaa Hub", "Healthy"),
        ("PRT-004", "Heavy-Duty Air Intake Filter", "Filters & Fluids", "Medium Truck", 210.0, "Medium", 15, 26.0, 6.4, "Al-Futtaim Auto Parts UAE", "Mussafah Hub", "Monitor"),
        ("PRT-005", "Front Disc Brake Pad Set", "Braking System", "Heavy Truck", 480.0, "High", 21, 30.0, 7.5, "Arabian Brake & Axle Co.", "Jebel Ali Hub", "Reorder_Urgent"),
        ("PRT-006", "Rear Brake Shoe & Lining Kit", "Braking System", "Medium Truck", 390.0, "High", 21, 22.0, 6.8, "Arabian Brake & Axle Co.", "Mussafah Hub", "Healthy"),
        ("PRT-007", "ABS Wheel Speed Sensor", "Braking System", "Coach / Bus", 320.0, "High", 25, 11.0, 4.9, "Bosch Middle East FZE", "Jebel Ali Hub", "Reorder_Now"),
        ("PRT-008", "Air Brake Chamber Assembly", "Braking System", "Heavy Truck", 640.0, "High", 28, 9.0, 4.6, "Arabian Brake & Axle Co.", "Mussafah Hub", "Monitor"),
        ("PRT-009", "A/C Compressor Assembly (Heavy)", "Cooling & HVAC", "Heavy Truck", 1850.0, "High", 35, 8.5, 5.8, "Denso Thermal UAE", "Jebel Ali Hub", "Reorder_Urgent"),
        ("PRT-010", "Radiator Core Assembly", "Cooling & HVAC", "Coach / Bus", 2200.0, "High", 40, 5.5, 4.2, "Denso Thermal UAE", "Mussafah Hub", "Reorder_Now"),
        ("PRT-011", "Thermostat & Housing Kit", "Cooling & HVAC", "Light Commercial Van", 145.0, "Medium", 14, 19.0, 5.1, "Gulf Auto Components", "Sajaa Hub", "Excess"),
        ("PRT-012", "Viscous Fan Clutch", "Cooling & HVAC", "Medium Truck", 780.0, "Medium", 24, 7.0, 4.4, "Denso Thermal UAE", "Jebel Ali Hub", "Healthy"),
        ("PRT-013", "24V Heavy-Duty AGM Battery", "Electrical & Ignition", "Heavy Truck", 890.0, "High", 14, 24.0, 6.2, "Emirates Battery Corp", "Jebel Ali Hub", "Reorder_Now"),
        ("PRT-014", "Heavy-Duty Alternator (150A)", "Electrical & Ignition", "Coach / Bus", 1650.0, "High", 30, 6.0, 4.5, "Bosch Middle East FZE", "Mussafah Hub", "Healthy"),
        ("PRT-015", "Starter Motor Assembly", "Electrical & Ignition", "Medium Truck", 1280.0, "High", 28, 6.5, 4.8, "Bosch Middle East FZE", "Sajaa Hub", "Monitor"),
        ("PRT-016", "LED Headlamp Assembly", "Electrical & Ignition", "Light Commercial Van", 430.0, "Low", 16, 12.0, 5.5, "Gulf Auto Components", "Sajaa Hub", "Excess"),
        ("PRT-017", "Steer Axle Radial Tyre (315/80R22.5)", "Tyres & Suspension", "Heavy Truck", 1420.0, "High", 20, 28.0, 7.1, "Bridgestone MEA", "Jebel Ali Hub", "Healthy"),
        ("PRT-018", "Drive Axle Radial Tyre (315/80R22.5)", "Tyres & Suspension", "Heavy Truck", 1480.0, "High", 20, 36.0, 8.9, "Bridgestone MEA", "Mussafah Hub", "Reorder_Urgent"),
        ("PRT-019", "Air Suspension Spring Bellow", "Tyres & Suspension", "Coach / Bus", 560.0, "Medium", 26, 9.5, 5.6, "Arabian Brake & Axle Co.", "Jebel Ali Hub", "Excess"),
        ("PRT-020", "Heavy-Duty Shock Absorber", "Tyres & Suspension", "Medium Truck", 340.0, "Medium", 18, 15.0, 5.2, "Arabian Brake & Axle Co.", "Sajaa Hub", "Healthy"),
        ("PRT-021", "Clutch Pressure Plate & Disc Kit", "Drivetrain & Transmission", "Medium Truck", 1950.0, "High", 35, 5.0, 4.1, "ZF Middle East", "Mussafah Hub", "Reorder_Now"),
        ("PRT-022", "Propshaft Universal Joint Kit", "Drivetrain & Transmission", "Heavy Truck", 410.0, "Medium", 22, 8.0, 4.9, "ZF Middle East", "Jebel Ali Hub", "Healthy"),
        ("PRT-023", "Transmission Oil Cooler", "Drivetrain & Transmission", "Coach / Bus", 1540.0, "High", 38, 3.2, 3.6, "ZF Middle East", "Mussafah Hub", "Excess"),
        ("PRT-024", "Differential Pinion Seal Kit", "Drivetrain & Transmission", "Light Commercial Van", 125.0, "Low", 14, 10.0, 4.2, "Gulf Auto Components", "Sajaa Hub", "Slow_Moving"),
        ("PRT-025", "Turbocharger Actuator Valve", "Engine Components", "Heavy Truck", 2450.0, "High", 42, 2.8, 3.4, "Al-Futtaim Auto Parts UAE", "Jebel Ali Hub", "Reorder_Urgent"),
        ("PRT-026", "EGR Valve Assembly", "Engine Components", "Medium Truck", 1120.0, "Medium", 30, 4.5, 4.0, "Bosch Middle East FZE", "Mussafah Hub", "Slow_Moving"),
        ("PRT-027", "Serpentine Drive Belt", "Engine Components", "Light Commercial Van", 115.0, "Medium", 12, 25.0, 5.4, "Emirates Fleet Supply", "Sajaa Hub", "Healthy"),
        ("PRT-028", "Side Mirror Housing Assembly", "Body & Cabin", "Light Commercial Van", 290.0, "Low", 15, 4.0, 3.9, "Gulf Auto Components", "Sajaa Hub", "Excess"),
    ]

    # -----------------------------------------------------------------------
    # 2. Build Open Purchase Orders (Due-In Pipeline) & Inventory Snapshot
    # -----------------------------------------------------------------------
    po_rows = []
    snapshot_rows = []
    po_counter = 2501

    for (
        p_num,
        p_name,
        cat,
        veh_type,
        unit_cost,
        crit,
        lt_days,
        avg_dem,
        std_dem,
        supplier,
        hub,
        profile,
    ) in parts_catalog:
        lt_months = lt_days / 30.0
        base_cycle = avg_dem * lt_months

        # Determine realistic stock quantities based on operational profile
        if profile == "Reorder_Urgent":
            on_hand = int(max(1, round(base_cycle * rng.uniform(0.25, 0.55))))
            reserved = int(min(on_hand, max(1, round(avg_dem * rng.uniform(0.15, 0.30)))))
            unserviceable = int(rng.choice([0, 1, 2], p=[0.4, 0.4, 0.2]))
            due_in = int(rng.choice([0, round(avg_dem * 0.5)], p=[0.65, 0.35]))
            months_since_last_issue = 0
        elif profile == "Reorder_Now":
            on_hand = int(max(2, round(base_cycle * rng.uniform(0.65, 0.95))))
            reserved = int(min(on_hand - 1, max(0, round(avg_dem * rng.uniform(0.10, 0.20)))))
            unserviceable = int(rng.choice([0, 1, 2], p=[0.5, 0.3, 0.2]))
            due_in = 0
            months_since_last_issue = 0
        elif profile == "Monitor":
            on_hand = int(round(base_cycle * rng.uniform(1.15, 1.45)))
            reserved = int(round(avg_dem * rng.uniform(0.05, 0.15)))
            unserviceable = int(rng.choice([0, 1], p=[0.7, 0.3]))
            due_in = int(round(avg_dem * 0.4)) if rng.random() < 0.4 else 0
            months_since_last_issue = 0
        elif profile == "Excess":
            on_hand = int(round(avg_dem * rng.uniform(6.5, 9.5)))
            reserved = int(round(avg_dem * 0.05))
            unserviceable = int(rng.choice([0, 1, 2], p=[0.6, 0.25, 0.15]))
            due_in = 0
            months_since_last_issue = int(rng.choice([1, 2, 3], p=[0.5, 0.3, 0.2]))
        elif profile == "Slow_Moving":
            on_hand = int(round(avg_dem * rng.uniform(7.5, 11.0)))
            reserved = 0
            unserviceable = 1
            due_in = 0
            months_since_last_issue = int(rng.choice([7, 8, 9], p=[0.4, 0.4, 0.2]))
        else:  # Healthy
            on_hand = int(round(base_cycle * rng.uniform(1.50, 2.20)))
            reserved = int(round(avg_dem * rng.uniform(0.05, 0.12)))
            unserviceable = int(rng.choice([0, 1], p=[0.75, 0.25]))
            due_in = int(round(avg_dem * 0.6)) if rng.random() < 0.35 else 0
            months_since_last_issue = 0

        # Create Open Purchase Order record if due_in > 0
        expected_receipt_str = None
        po_status = "No Open PO"
        if due_in > 0:
            po_num = f"PO-2025-{po_counter}"
            po_counter += 1
            order_date = snapshot_date - pd.Timedelta(days=int(rng.integers(8, lt_days + 10)))
            expected_date = order_date + pd.Timedelta(days=lt_days)
            # Cap expected receipt date within 2025 (max 2025-12-30)
            if expected_date > pd.Timestamp("2025-12-30"):
                expected_date = pd.Timestamp("2025-12-30")

            days_variance = (snapshot_date - expected_date).days
            is_overdue = days_variance > 0
            po_status = "Overdue" if is_overdue else "In Transit"
            expected_receipt_str = expected_date.strftime("%Y-%m-%d")

            po_rows.append(
                {
                    "po_number": po_num,
                    "part_number": p_num,
                    "part_name": p_name,
                    "supplier": supplier,
                    "hub_location": hub,
                    "order_date": order_date.strftime("%Y-%m-%d"),
                    "expected_receipt_date": expected_receipt_str,
                    "due_in_qty": due_in,
                    "po_value_aed": round(due_in * unit_cost, 2),
                    "lead_time_days": lt_days,
                    "days_overdue": max(0, days_variance),
                    "po_status": po_status,
                }
            )

        last_issue_date = (snapshot_date - pd.DateOffset(months=months_since_last_issue)).strftime(
            "%Y-%m-%d"
        )

        snapshot_rows.append(
            {
                "snapshot_date": snapshot_date_str,
                "part_number": p_num,
                "part_name": p_name,
                "category": cat,
                "vehicle_type": veh_type,
                "hub_location": hub,
                "supplier": supplier,
                "on_hand_qty": on_hand,
                "due_in_qty": due_in,
                "expected_receipt_date": expected_receipt_str if expected_receipt_str else "N/A",
                "po_status": po_status,
                "reserved_qty": reserved,
                "unserviceable_qty": unserviceable,
                "avg_monthly_demand": avg_dem,
                "demand_std_dev": std_dem,
                "lead_time_days": lt_days,
                "unit_cost_aed": unit_cost,
                "criticality": crit,
                "last_issue_date": last_issue_date,
                "months_since_last_issue": months_since_last_issue,
            }
        )

    inventory_df = pd.DataFrame(snapshot_rows)
    po_df = pd.DataFrame(po_rows)

    # -----------------------------------------------------------------------
    # 3. Generate Backordered Vehicle Work Orders (Delayed Due to Stock-Outs)
    # -----------------------------------------------------------------------
    urgent_parts = inventory_df[
        inventory_df["part_number"].isin(
            ["PRT-002", "PRT-005", "PRT-007", "PRT-009", "PRT-010", "PRT-013", "PRT-018", "PRT-021", "PRT-025"]
        )
    ]

    fleet_plates = [
        ("DXB-H-4012", "Heavy Truck"),
        ("DXB-H-4088", "Heavy Truck"),
        ("AUH-H-7120", "Heavy Truck"),
        ("SHJ-M-2219", "Medium Truck"),
        ("AUH-M-3304", "Medium Truck"),
        ("DXB-B-9015", "Coach / Bus"),
        ("AUH-B-9042", "Coach / Bus"),
        ("DXB-V-1180", "Light Commercial Van"),
    ]

    wo_rows = []
    wo_counter = 8401
    for _, p_row in urgent_parts.iterrows():
        # Match vehicles of the same class
        matching_vehs = [v for v, vt in fleet_plates if vt == p_row["vehicle_type"]]
        n_delayed = int(rng.integers(1, 4))
        for _ in range(n_delayed):
            veh_id = rng.choice(matching_vehs)
            wo_open_date = snapshot_date - pd.Timedelta(days=int(rng.integers(2, 16)))
            delay_days = (snapshot_date - wo_open_date).days
            qty_short = int(rng.integers(1, 4))
            wo_rows.append(
                {
                    "work_order_id": f"WO-2025-{wo_counter}",
                    "vehicle_id": veh_id,
                    "vehicle_type": p_row["vehicle_type"],
                    "hub_location": p_row["hub_location"],
                    "part_number": p_row["part_number"],
                    "part_name": p_row["part_name"],
                    "criticality": p_row["criticality"],
                    "wo_opened_date": wo_open_date.strftime("%Y-%m-%d"),
                    "snapshot_date": snapshot_date_str,
                    "days_delayed": delay_days,
                    "downtime_hours_accumulated": round(delay_days * 8.5, 1),
                    "qty_required": qty_short,
                    "delay_reason": "Awaiting Spare Part Stock Replenishment",
                }
            )
            wo_counter += 1

    backorder_wo_df = pd.DataFrame(wo_rows)

    # Save CSV outputs
    inventory_df.to_csv(os.path.join(output_dir, "inventory_snapshot.csv"), index=False)
    po_df.to_csv(os.path.join(output_dir, "open_purchase_orders.csv"), index=False)
    backorder_wo_df.to_csv(os.path.join(output_dir, "backordered_work_orders.csv"), index=False)

    return {
        "inventory_snapshot": inventory_df,
        "open_purchase_orders": po_df,
        "backordered_work_orders": backorder_wo_df,
    }


if __name__ == "__main__":
    datasets = generate_inventory_datasets()
    for name, df in datasets.items():
        print(f"Generated {name}: {df.shape[0]} rows x {df.shape[1]} columns")