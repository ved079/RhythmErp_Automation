"""
chain_po_qc_pb.py — PO→QC→PB flow (no GP/GRN).

QC logic: CQP slab-based deduction.
  actual_value    = slab1_max_q + 0.1  (just inside slab2)
  deduction       = (actual - allowable) × slab2_multiplier  (per-param, summed)
  empty_bag_weight = 3–5% of accepted_qty (back-calculated to consistent weight_of_bags)

This is correct for items with a two-slab CQP configuration (item_category≠1).
"""

from pages.private_b2b.scripts.purchase_chain import PurchaseChain, _qc_items_from


class POQCPBChain(PurchaseChain):
    """PO→QC→PB flow using CQP slab-based QC deduction logic."""

    _get_qc_items = staticmethod(_qc_items_from)
