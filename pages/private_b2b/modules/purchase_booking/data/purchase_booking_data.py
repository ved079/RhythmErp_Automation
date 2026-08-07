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
    Sub-det:  details                   (list of sub-rows per line)
  Other:      other_charges             (flat dict)
  Attach:     grn_details               (list, empty for creates)

Calculation formulas (confirmed from sample id=931):
  alternate_net_qty        = alternate_qty - empty_bag_weight
  txn_currency_amount_detail = rate * alternate_net_qty - labour_charges
  txn_currency_igst_amount   = txn_currency_amount_detail * igst_rate / 100
  txn_currency_cgst_amount   = txn_currency_amount_detail * cgst_rate / 100
  txn_currency_sgst_amount   = txn_currency_amount_detail * sgst_rate / 100
  txn_currency_tax_amount    = igst_amt + cgst_amt + sgst_amt
  txn_currency_total_txn_amount = txn_currency_amount_detail + txn_currency_tax_amount
  master.txn_currency_amount       = SUM(txn_currency_total_txn_amount)
  master.txn_currency_total_amount = SUM(txn_currency_total_txn_amount)

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
    """Map a tax rate to the ERP's gst_type (matches manual PB 2480).

    tax_rate 25  → "CGST + SGST" (split 12.5 / 12.5)
    tax_rate 5   → "IGST" (single 5%)
    anything else → None (no GST)
    """
    rate = round(float(tax_rate or 0.0), 4)
    if rate == 25.0:
        return "CGST + SGST"
    if rate == 5.0:
        return "IGST"
    return None


def _split_gst(amount: float, tax_rate: float, gst_type: Optional[str]) -> dict:
    """Split a taxable *amount* into IGST/CGST/SGST per *gst_type*.

    Returns a dict with the four rate/amount keys plus the total tax amount.
    ``gst_type`` None (or is_gst_set_off False) → all zeros / None.
    """
    if not gst_type:
        return {
            "igst_rate": None, "igst_amount": 0.0,
            "cgst_rate": None, "cgst_amount": 0.0,
            "sgst_rate": None, "sgst_amount": 0.0,
            "tax_amount": 0.0,
        }
    rate = float(tax_rate or 0.0)
    if gst_type == "IGST":
        igst = round(amount * rate / 100.0, 6)
        return {
            "igst_rate": rate, "igst_amount": igst,
            "cgst_rate": None, "cgst_amount": 0.0,
            "sgst_rate": None, "sgst_amount": 0.0,
            "tax_amount": igst,
        }
    # CGST + SGST (split evenly)
    half = rate / 2.0
    each = round(amount * half / 100.0, 6)
    return {
        "igst_rate": None, "igst_amount": 0.0,
        "cgst_rate": half, "cgst_amount": each,
        "sgst_rate": half, "sgst_amount": each,
        "tax_amount": round(each * 2, 6),
    }

# ── Supplier type constants (Role Type master — same across all tenants) ──────
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


# ── Calculation helpers ───────────────────────────────────────────────────────

def compute_line_amount(quantity: float, rate: float) -> float:
    return quantity * rate


def compute_master_total(items: List[dict]) -> int:
    return int(round(sum(it.get("txn_currency_amount", 0.0) for it in items), 6))


# ── Item / detail builders ────────────────────────────────────────────────────

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
    """
    Build one line item for purchase_booking_details matching the frontend
    CREATE payload format. Uses only the fields the serializer expects on POST.
    """
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
    is_gst_set_off: bool = False,
    tax_rate: float = 0.0,
    gst_type: Optional[str] = None,
    uom_conversion: float = 1.0,
    round_of_credit_amount: float = 0.0,
    round_of_debit_amount: float = 0.0,
) -> dict:
    """
    Build a PB line mirroring the QC/GRN line (manual PB 2480 shape).

    The caller passes the already-netted *amount_detail* (QC txn_currency_amount
    minus labour); GST split and totals are derived here so the header can
    aggregate them. ERP stores amount/discount/tax/labour as sent but
    recomputes per-line total_txn as amount - discount + tax - labour (verified
    live against PB 2482) and applies its own round-off per line.
    """
    if gst_type is None:
        gst_type = gst_type_for_rate(tax_rate)
    gst = _split_gst(amount_detail, tax_rate, gst_type if is_gst_set_off else None)
    discount = discount_amount or 0.0
    total_txn = round(amount_detail - discount + gst["tax_amount"] - labour_charges, 6)

    return {
        "item_ref_id": item_ref_id,
        "alternate_uom": alternate_uom,
        "hsn_sac_no": hsn_sac_no,
        "base_rate": base_rate,
        "alternate_qty": alternate_qty,
        "no_of_bags": no_of_bags,
        "uom_conversion": uom_conversion,
        "empty_bag_weight": empty_bag_weight,
        "empty_bags_txn_amount": empty_bags_txn_amount,
        "alternate_net_qty": alternate_net_qty,
        "discount_percentage": discount_percentage,
        "txn_currency_discount_amount_details": discount_amount,
        "txn_currency_amount_detail": amount_detail,
        "rate": base_rate,
        "labour_charges": labour_charges,
        "transport": transport,
        "is_gst_set_off": is_gst_set_off,
        "tax_rate": tax_rate,
        "gst_type": gst_type if is_gst_set_off else None,
        "txn_currency_igst_rate": gst["igst_rate"],
        "txn_currency_igst_amount": gst["igst_amount"],
        "txn_currency_cgst_rate": gst["cgst_rate"],
        "txn_currency_cgst_amount": gst["cgst_amount"],
        "txn_currency_sgst_rate": gst["sgst_rate"],
        "txn_currency_sgst_amount": gst["sgst_amount"],
        "txn_currency_tax_amount": gst["tax_amount"],
        "txn_currency_total_txn_amount": total_txn,
        "uom": uom,
        "round_of_credit_amount": round_of_credit_amount,
        "round_of_debit_amount": round_of_debit_amount,
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
    tds_amount: int = 0,
    round_off_credit_amount: Optional[float] = None,
    round_off_debit_amount: Optional[float] = None,
    agent_ref_id: Optional[int] = None,
    is_rate_percentage: bool = False,
    agent_commision: Optional[float] = None,
    transportation_charges: int = 0,
    remark: Optional[str] = None,
    transaction_date: Optional[str] = None,
) -> dict:
    """
    Build a complete Purchase Booking payload ready to POST.

    All FK IDs must be resolved from live ERP before calling.
    items should be built with build_pb_item() or build_pb_line().

    Header aggregates are derived per line so they stay self-consistent:
      txn_currency_amount       = Σ txn_currency_amount_detail
      txn_currency_discount_amount = Σ txn_currency_discount_amount_details
      txn_currency_total_amount = Σ txn_currency_total_txn_amount
    Legacy items (build_pb_item) fall back to txn_currency_amount.
    """
    if items is None:
        items = []
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    # supplier_ref_type is stored as a string name in the ERP ("Farmer", "Supplier", etc.)
    if isinstance(supplier_ref_type, int):
        supplier_ref_type = SUPPLIER_TYPE_NAMES.get(supplier_ref_type, "Supplier")

    def _f(v):
        return float(v) if v is not None else 0.0

    def _has(k):
        return any(k in it for it in items)

    if _has("txn_currency_amount_detail"):
        txn_currency_amount = round(sum(_f(it.get("txn_currency_amount_detail")) for it in items), 6)
        txn_currency_discount_amount = round(sum(_f(it.get("txn_currency_discount_amount_details")) for it in items), 6)
        txn_currency_total_amount = round(sum(_f(it.get("txn_currency_total_txn_amount")) for it in items), 6)
        total_quantity = round(sum(_f(it.get("alternate_net_qty")) for it in items), 6)
    else:
        master_total = compute_master_total(items)
        txn_currency_amount = master_total
        txn_currency_discount_amount = 0.0
        txn_currency_total_amount = master_total
        total_quantity = int(sum(it.get("quantity", 0) or 0 for it in items))

    return {
        "transaction_date": transaction_date,
        "transaction_ref_no": "",
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": supplier_ref_type,
        # Django FK write fields use the _id_id convention (same as GRN/QC)
        "qc_ref_id_id": qc_ref_id,
        "grn_ref_id_id": grn_ref_id,
        "po_ref_id_id": po_ref_id,
        "supplier_payment_terms_ref_id": supplier_payment_terms_ref_id,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": conversion_rate,
        "total_quantity": total_quantity,
        "txn_currency_amount": txn_currency_amount,
        "txn_currency_total_amount": txn_currency_total_amount,
        "txn_currency_discount_amount": txn_currency_discount_amount,
        "is_tds_applicable": is_tds_applicable if is_tds_applicable is not None else False,
        "section_ref_id": section_ref_id if section_ref_id is not None else "0",
        "tds_percent_applicable": tds_percent_applicable,
        "tds_amount": tds_amount,
        "parameter5": parameter5,       # Location
        "parameter2": parameter2,       # Department
        "parameter1": parameter1,       # Division
        "parameter6": parameter6,       # Type of Sale
        "round_off_credit_amount": round_off_credit_amount if round_off_credit_amount is not None else 0,
        "round_off_debit_amount": round_off_debit_amount if round_off_debit_amount is not None else 0,
        "remark": remark if remark is not None else "",
        "posting_status": "",
        "gst_registration_type": None,
        "transportation_charges": transportation_charges,
        # Detail grid
        "purchase_booking_details": items,
        # GRN attachments (matches frontend pattern for create)
        "grn_details": [],
        # Other charges (flat dict)
        "other_charges": {
            "agent_ref_id": agent_ref_id,
            "is_rate_percentage": is_rate_percentage,
            "agent_commision": agent_commision,
            "agent_commision_amount": 0,
        },
    }
