"""
chain_full.py — Full PO→GP→GRN→QC→PB→PYMT chain.

QC logic: random bag weight capped at 5% of grn_qty, random deduction_percent (0–5%).
This is correct for items in item_category=1 (GP flow) which typically have no CQP
slab2 and would produce 0.0 deduction if CQP-based logic were used.
"""

from pages.private_b2b.scripts.purchase_chain import PurchaseChain


class FullChain(PurchaseChain):
    """Full PO→GP→GRN→QC→PB→PYMT flow.

    Inherits PurchaseChain which uses _qc_items_from_random by default.
    No overrides needed — this class exists as an explicit named entry point.
    """
