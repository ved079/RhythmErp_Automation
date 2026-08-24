"""
purchase_booking_data.py
------------------------
Payload builders for the "Purchase Booking" ERP screen.

Field names derived from an actual GET response (id=931), not just the schema.
The schema field_keys differ from the real API field names in several places —
this file reflects reality.

Structure:
  Master:     tbl_purchase_booking_mst
  Details:    purchase_booking_details  (list of line items)
  Other:      other_charges             (flat dict)
  Attach:     grn_details               (list, empty for creates)

Calculation formulas (confirmed from successful PBs):
  amount_detail = rate * alternate_net_qty  (after QC deductions)
  gst = amount_detail * tax_rate / 100
  total_txn = amount_detail - discount + gst
  master.txn_currency_amount       = SUM(amount_detail)
  master.txn_currency_total_amount = SUM(total_txn)

GST REQUIRED for non-zero tax rates: the CALCULATION step uses the item master
tax rate; omitting GST causes "Debit credit SUM is not zero" at accounting.

Supplier Type — ERP expects a string name ("Farmer", "Supplier", etc.).
  Integer constants are provided for legacy callers; build_pb_payload auto-converts.
  Farmer   = 1769  → "Farmer"
  Supplier = 1771  → "Supplier"
  Customer = 1770  → "Customer"
  Operator = 1814  → "Operator"
  Agent    = 1855  → "Agent"
"""

from datetime import date
from typing import List, Optional


# ── GST type helpers ─────────────────────────────────────────────────────────

def gst_type_for_rate(tax_rate: float) -> Optional[str]:
    """Map a non-zero tax rate to a GST type (IGST or CGST+SGST)."""
    import random
    rate = round(float(tax_rate or 0.0), 4)
    if rate == 0.0:
        return None
    return random.choice(["IGST", "CGST + SGST"])


def _split_gst(amount: float, tax_rate: float, gst_type: Optional[str]) -> dict:
    """Split a taxable amount into IGST/CGST/SGST per gst_type.

    Returns floats (not strings); None for unused rate/amount fields.
    gst_type None → all None/zero.
    """
    if not gst_type:
        return {
            "igst_rate": None, "igst_amount": None,
            "cgst_rate": None, "cgst_amount": None,
            "sgst_rate": None, "sgst_amount": None,
            "tax_amount": 0.0,
        }
    rate = float(tax_rate or 0.0)
    if gst_type == "IGST":
        igst = round(amount * rate / 100.0, 3)
        return {
            "igst_rate": rate, "igst_amount": igst,
            "cgst_rate": None, "cgst_amount": None,
            "sgst_rate": None, "sgst_amount": None,
            "tax_amount": igst,
        }
    # CGST + SGST (split evenly)
    half = rate / 2.0
    each = round(amount * half / 100.0, 3)
    return {
        "igst_rate": None, "igst_amount": None,
        "cgst_rate": half, "cgst_amount": each,
        "sgst_rate": half, "sgst_amount": each,
        "tax_amount": round(each * 2, 3),
    }


# ── Supplier type constants ───────────────────────────────────────────────────
SUPPLIER_TYPE_FARMER   = 1769
SUPPLIER_TYPE_SUPPLIER = 1771
SUPPLIER_TYPE_CUSTOMER = 1770
SUPPLIER_TYPE_OPERATOR = 1814
SUPPLIER_TYPE_AGENT    = 1855

SUPPLIER_TYPE_NAMES = {
    SUPPLIER_TYPE_FARMER:   "Farmer",
    SUPPLIER_TYPE_SUPPLIER: "Supplier",
    SUPPLIER_TYPE_CUSTOMER: "Customer",
    SUPPLIER_TYPE_OPERATOR: "Operator",
    SUPPLIER_TYPE_AGENT:    "Agent",
}


# ── Legacy helpers (kept for backward compat) ─────────────────────────────────

def compute_line_amount(quantity: float, rate: float) -> float:
    return quantity * rate


def compute_master_total(items: List[dict]) -> int:
    return int(round(sum(it.get("txn_currency_amount", 0.0) for it in items), 6))


def build_pb_item(
    item_ref_id: int,
    hsn_sac_no: int,
    alternate_uom: int,
    uom: int,
    rate: float,
    no_of_bags: int = 1,
    alternate_qty: float = None,
    quantity: float = None,
    is_gst_set_off: bool = False,
) -> dict:
    """Legacy simple line builder (no QC fields). Use build_pb_line for new code."""
    if alternate_qty is None:
        alternate_qty = float(no_of_bags)
    if quantity is None:
        quantity = alternate_qty
    line_amount = int(compute_line_amount(quantity, rate))
    return {
        "item_ref_id": item_ref_id,
        "hsn_sac_no": hsn_sac_no,
        "no_of_bags": no_of_bags,
        "alternate_qty": int(alternate_qty),
        "alternate_uom": alternate_uom,
        "quantity": int(quantity),
        "uom": uom,
        "rate": int(rate),
        "txn_currency_amount": line_amount,
        "amount": line_amount,
        "gst_percent": None,
        "igst": None,
        "cgst": None,
        "sgst": None,
        "is_gst_set_off": is_gst_set_off,
        "tax_rate": None,
    }


# ── Line builder ──────────────────────────────────────────────────────────────

def build_pb_line(
    item_ref_id: int,
    hsn_sac_no: int,
    alternate_uom: int,
    uom: int,
    base_rate: float,
    alternate_qty: float,
    no_of_bags: int,
    empty_bag_weight: float,
    empty_bags_txn_amount: float,
    alternate_net_qty: float,
    discount_percentage: float,
    discount_amount: Optional[float],
    amount_detail: float,
    labour_charges: float = 0.0,
    transport: Optional[float] = None,
    tax_rate: float = 0.0,
    gst_type: Optional[str] = None,
    uom_conversion: float = 1.0,
    # QC pass-through fields
    alternate_gate_pass_quantity: float = 0.0,
    grn_alternate_rejected_qty: float = 0.0,
    total_amount: float = 0.0,
    net_of_empty_bag_amount: float = 0.0,
    alternate_deduction_weight: float = 0.0,
    alternate_c_d_deduction: float = 0.0,
    qc_deduction_amount: float = 0.0,
    transaction_amount_without_discount: float = 0.0,
    # deprecated params kept for backward compat
    is_gst_set_off: bool = False,
    round_of_credit_amount: Optional[float] = None,
    round_of_debit_amount: Optional[float] = None,
) -> dict:
    """
    Build a PB line that matches the ERP UI request format.

    Amounts are floats (not f3 strings). GST is applied whenever tax_rate > 0
    and gst_type is set (or auto-selected). The caller must pass the correct
    tax_rate from the item master — omitting GST causes accounting failure.
    """
    if tax_rate and not gst_type:
        gst_type = gst_type_for_rate(tax_rate)

    gst = _split_gst(amount_detail, tax_rate, gst_type)
    discount = discount_amount or 0.0
    # amount_detail from QC is post-discount; total_txn does NOT subtract discount again.
    # discount is tracked separately in txn_currency_discount_amount_details for accounting.
    total_txn = round(amount_detail + gst["tax_amount"] - labour_charges, 3)

    return {
        "item_ref_id": item_ref_id,
        "alternate_uom": alternate_uom,
        "hsn_sac_no": hsn_sac_no,
        "uom_conversion": str(uom_conversion),
        "empty_bags_txn_amount": float(empty_bags_txn_amount),
        "base_rate": float(base_rate),
        "alternate_gate_pass_quantity": float(alternate_gate_pass_quantity),
        "grn_alternate_rejected_qty": float(grn_alternate_rejected_qty),
        "alternate_qty": float(alternate_qty),
        "total_amount": float(total_amount),
        "no_of_bags": int(no_of_bags),
        "empty_bag_weight": float(empty_bag_weight),
        "alternate_net_qty": float(alternate_net_qty),
        "uom": uom,
        "net_of_empty_bag_amount": float(net_of_empty_bag_amount),
        "alternate_deduction_weight": float(alternate_deduction_weight),
        "alternate_c_d_deduction": float(alternate_c_d_deduction),
        "qc_alternate_rejected_qty": 0.0,
        "alternate_net_purchase_qty": 0.0,
        "qc_deduction_amount": float(qc_deduction_amount),
        "transaction_amount_without_discount": float(transaction_amount_without_discount),
        "discount_percentage": float(discount_percentage),
        "txn_currency_discount_amount_details": float(discount),
        "txn_currency_amount_detail": float(amount_detail),
        "tax_rate": float(tax_rate),
        "gst_type": gst_type,
        "txn_currency_igst_rate": gst["igst_rate"],
        "txn_currency_igst_amount": gst["igst_amount"],
        "txn_currency_cgst_rate": gst["cgst_rate"],
        "txn_currency_cgst_amount": gst["cgst_amount"],
        "txn_currency_sgst_rate": gst["sgst_rate"],
        "txn_currency_sgst_amount": gst["sgst_amount"],
        "txn_currency_tax_amount": float(gst["tax_amount"]),
        "labour_charges": float(labour_charges),
        "transport": float(transport) if transport is not None else 0.0,
        "advance_paid": None,
        "txn_currency_total_txn_amount": float(total_txn),
        "rate": round(amount_detail / alternate_net_qty, 6) if alternate_net_qty else float(base_rate),
        "isChecked": True,
    }


# ── Master payload builder ────────────────────────────────────────────────────

def build_pb_payload(
    supplier_ref_id: int,
    supplier_ref_type: int = SUPPLIER_TYPE_FARMER,
    parameter1: int = 1,        # Division
    parameter2: int = 1,        # Department
    parameter5: int = 1,        # Location
    parameter6: int = 1,        # Type of Sale (B2B=1)
    base_currency: int = 8,     # INR
    txn_currency: int = 8,      # INR
    conversion_rate: str = "1",
    items: Optional[List[dict]] = None,
    qc_ref_id: Optional[int] = None,
    po_ref_id: Optional[int] = None,
    grn_ref_id: Optional[int] = None,
    supplier_payment_terms_ref_id: Optional[int] = None,
    is_tds_applicable: Optional[bool] = None,
    section_ref_id: Optional[int] = None,
    tds_percent_applicable: Optional[int] = None,
    tds_amount: Optional[float] = None,
    round_off_credit_amount: Optional[float] = None,
    round_off_debit_amount: Optional[float] = None,
    agent_ref_id: Optional[int] = None,
    is_rate_percentage: bool = False,
    agent_commision: Optional[float] = None,
    # deprecated — kept for backward compat, ignored
    transportation_charges: int = 0,
    remark: Optional[str] = None,
    transaction_date: Optional[str] = None,
    tax_registration_status: str = "Registered",
) -> dict:
    """
    Build a complete Purchase Booking payload ready to POST.

    All FK IDs must be resolved from live ERP before calling.
    Items should be built with build_pb_line().

    Header aggregates are derived per line:
      txn_currency_amount       = Σ amount_detail
      txn_currency_discount_amount = Σ discount_amount_details
      txn_currency_total_amount = Σ total_txn_amount
    """
    if items is None:
        items = []
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    if isinstance(supplier_ref_type, int):
        supplier_ref_type = SUPPLIER_TYPE_NAMES.get(supplier_ref_type, "Supplier")

    def _f(v):
        return float(v) if v is not None else 0.0

    txn_currency_amount = round(sum(_f(it.get("txn_currency_amount_detail")) for it in items), 6)
    txn_currency_discount_amount = round(sum(_f(it.get("txn_currency_discount_amount_details")) for it in items), 6)
    txn_currency_total_amount = round(sum(_f(it.get("txn_currency_total_txn_amount")) for it in items), 6)

    return {
        "transaction_date": transaction_date,
        "type_of_bags_ref_id": None,
        "is_tds_applicable": is_tds_applicable,
        "transaction_ref_no": "",
        "purchase_booking_details": items,
        "supplier_ref_id": supplier_ref_id,
        "qc_summary": {},
        "tax_registration_status": tax_registration_status,
        "supplier_ref_type": supplier_ref_type,
        "grn_details": [],
        "qc_ref_id_id": qc_ref_id,
        "item_quality_parameter_ref_id": None,
        "other_charges": {
            "agent_ref_id": agent_ref_id,
            "is_rate_percentage": is_rate_percentage,
            "agent_commision": agent_commision,
            "agent_commision_amount": None,
        },
        "grn_ref_id_id": grn_ref_id,
        "po_ref_id_id": po_ref_id,
        "so_ref_id": None,
        "booking_status": "Pending",
        "parameter6": parameter6,
        "parameter2": parameter2,
        "posting_status": "",
        "parameter1": parameter1,
        "parameter5": parameter5,
        "supplier_payment_terms_ref_id": supplier_payment_terms_ref_id,
        "txn_currency": txn_currency,
        "txn_currency_amount": float(txn_currency_amount),
        "section_ref_id": "0",
        "tds_percent_applicable": tds_percent_applicable,
        "tds_amount": None,
        "purchase_booking_ref_type": 144,
        "txn_currency_total_amount": float(txn_currency_total_amount),
        "round_off_credit_amount": round_off_credit_amount,
        "round_off_debit_amount": round_off_debit_amount,
        "remark": remark if remark is not None else "",
        "base_currency": base_currency,
        "conversion_rate": str(conversion_rate),
        "txn_currency_discount_amount": float(txn_currency_discount_amount),
        "omitted_fields": [],
    }
