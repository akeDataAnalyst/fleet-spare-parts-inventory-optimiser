# **Fleet Spare-Parts Inventory Replenishment & Safety Stock Optimiser**

## Description
An operational inventory control and safety stock optimisation platform built in Python and Streamlit. Designed for fleet and logistics supply chains in the UAE (with AED valuation, UAE regional hubs, and 2025 operational snapshots), the system evaluates physical stock, incoming purchase orders, reserved allocations, and unserviceable repairable cores to prevent stock-outs, reduce vehicle downtime, and free up excess working capital.

---

## Problem
Fleet supply chain teams face a constant operational trade-off:
* **Stock-Out & Downtime Risk:** Missing critical components (such as brake pads, fuel filters, A/C compressors, or batteries) grounds vehicles in the workshop, delays fleet dispatch, and forces expensive emergency spot buying.
* **Excess & Slow-Moving Capital:** Ordering without clear stock visibility or demand stability rules ties up cash (AED) and warehouse capacity in overstocked or slow-moving parts.
* **Incomplete Stock Visibility:** Relying solely on raw on-hand counts ignores reserved stock, overdue incoming deliveries, and unserviceable cores awaiting overhaul—leading to poor reorder timing and delayed vehicle work orders.

---

## Solution
The project provides a modular Python analytical pipeline and a multi-page Streamlit command center that turns raw stock, purchase order, and work order data into clear procurement actions:

1. **Stock Position & ABC-XYZ Segmentation (`src/inventory_metrics.py`):**
   * Reconciles Net Available Stock (`On Hand + Due In - Reserved - Unserviceable`) alongside Days of Supply and AED valuations.
   * Segments spare parts across ABC (value contribution) and XYZ (demand variability via coefficient of variation) while flagging slow-moving stock and overdue purchase orders.
2. **Safety Stock, Reorder Point (ROP) & Order Engine (`src/replenishment_engine.py`):**
   * Calculates Safety Stock, Reorder Points (ROP), Target Stock Levels, and Recommended Order Quantities using criticality-based service levels (99% for High, 95% for Medium, 90% for Low) and supplier lead times.
   * Assigns actionable statuses (Reorder now, Monitor closely, Healthy, Excess stock, Review master data), escalates urgent Purchase Requisitions (PRs), and tracks delayed vehicle work orders.
3. **Interactive Streamlit Dashboard & Reorder Export (`app/`):**
   * Delivers an executive overview plus dedicated pages for stock positions and ABC-XYZ matrices, interactive $Z$-score service-level simulation, excess and slow-moving stock audits, supplier/PO tracking, and downloadable CSV reorder requisitions.

---

## Tech Stack
* **Language & Data Analysis:** Python, Pandas, NumPy
* **Interactive Dashboard & Visuals:** Streamlit, Plotly
* **Inventory & Supply Chain Methods:** Net Available Stock Reconciliation, ABC-XYZ Segmentation, Service-Level Safety Stock ($Z$-Score), Reorder Point (ROP) Modeling
* **Development & Version Control:** Jupyter Notebook, Git, GitHub

---

## Recommendation
Fleet and inventory planners can apply the findings and replenishment model through four practical steps:

* **Prioritise High-Criticality Buffers & Urgent PRs:** Enforce higher service-level safety stock on high-criticality components and immediately escalate Purchase Requisitions where net stock falls at or below ROP or where vehicle work orders are already delayed.
* **Audit Overdue Due-Ins & Repairable Cores:** Track purchase orders past their expected receipt date and separate unserviceable cores from usable stock so incoming supply risks are caught early.
* **Reallocate or Clear Excess & Slow-Moving Stock:** Review items with high days of supply or extended months since last issue to redeploy stock across hubs, adjust order quantities, or free up tied-up **AED** working capital.
* **Standardise Reorder Exports:** Use the exported reorder plan (`procurement_reorder_plan.csv`) as a structured daily or weekly review input for procurement and warehouse teams.

---

**Developed by Aklilu Abera Dana | Supply Chain Data Analyst**