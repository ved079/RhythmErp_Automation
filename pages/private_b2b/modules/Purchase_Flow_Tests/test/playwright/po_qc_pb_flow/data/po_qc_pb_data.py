"""
po_qc_pb_data.py
----------------
Payload builders for PO → QC → PB batch creation.

Tenant: Ganesh Agrotech Pvt Ltd. (kedar@rhythmflows.com / Kedar@999999)
Flow:   Purchase Order → Quality Check → Purchase Booking

Field names and structure derived from real GET responses on this tenant.

PO calculation rules:
  txn_currency_amount_detail      = rate × alternate_quantity
  txn_currency_tax_amount_details = txn_currency_amount_detail × tax_rate / 100
  total_amount (per line)         = txn_currency_amount_detail + txn_currency_tax_amount_details
  txn_currency_total_amount       = SUM(total_amount per line)

QC calculation rules:
  rate                  = base_rate × (1 - deduction_percent/100)   [0 deduction → rate = base_rate]
  txn_currency_amount   = rate × alternate_accepted_qty
  total_txn_currency_amount = SUM(txn_currency_amount per line)

PB calculation rules (from QC, no GST):
  alternate_net_qty              = alternate_qty - empty_bag_weight
  txn_currency_amount_detail     = rate × alternate_net_qty - labour_charges
  txn_currency_total_txn_amount  = txn_currency_amount_detail   [no GST in this flow]
  txn_currency_amount            = SUM(txn_currency_total_txn_amount per line)
  txn_currency_total_amount      = same
"""

import random
from datetime import date
from typing import List, Optional


# ── Tenant constants ──────────────────────────────────────────────────────────

CURRENCY_ID = 8          # AUD on Ganesh Agrotech
SUPPLIER_REF_TYPE = "Supplier"

# System-level constants (same across tenants)
PO_TYPE_DOMESTIC = 25
PO_TYPE_IMPORT   = 24
PACKING_FORWARDING_NILL = 89


# ── PO calculation helpers ────────────────────────────────────────────────────

def compute_po_line_txn_amount(rate: float, qty: float) -> float:
    return round(rate * qty, 6)


def compute_po_line_tax_amount(txn_amount: float, tax_rate: float) -> float:
    return round(txn_amount * tax_rate / 100, 6)


def compute_po_line_total(txn_amount: float, tax_amount: float) -> float:
    return round(txn_amount + tax_amount, 6)


def compute_po_total(items: List[dict]) -> float:
    return round(sum(it.get("total_amount", 0.0) for it in items), 6)


# ── PO item builder ───────────────────────────────────────────────────────────

def build_po_item(
    item_ref_id: int,
    hsn_sac_no: int,
    alternate_uom: int,    # item's primary UOM
    uom: int,              # item's base UOM
    uom_conversion: float,
    rate: float,
    alternate_quantity: float,
    is_gst_set_off: bool = True,
    tax_rate: float = 5.0,
    expected_delivery_date: str = None,
) -> dict:
    """
    Build one line item for purchasing_order_items_details.

    Field mapping from real PO GET response:
      alternate_uom   = item primary UOM  (e.g. MT)
      uom             = item base UOM     (e.g. KG)
      uom_conversion  = base_uom_conversion from Item Master

    Computed fields (ERP expects pre-calculated values on POST):
      txn_currency_amount_detail      = rate × alternate_quantity
      txn_currency_tax_amount_details = txn_currency_amount_detail × tax_rate / 100
      total_amount                    = txn_currency_amount_detail + txn_currency_tax_amount_details
    """
    if expected_delivery_date is None:
        expected_delivery_date = date.today().isoformat()

    txn_amount = compute_po_line_txn_amount(rate, alternate_quantity)
    tax_amount = compute_po_line_tax_amount(txn_amount, tax_rate) if is_gst_set_off else 0.0
    line_total = compute_po_line_total(txn_amount, tax_amount)

    return {
        "item_ref_id": item_ref_id,
        "hsn_sac_no": hsn_sac_no,
        "alternate_uom": alternate_uom,
        "uom": uom,
        "uom_conversion": uom_conversion,
        "alternate_quantity": alternate_quantity,
        "rate": rate,
        "is_gst_set_off": is_gst_set_off,
        "tax_rate": tax_rate if is_gst_set_off else None,
        "txn_currency_amount_detail": txn_amount,
        "txn_currency_tax_amount_details": tax_amount,
        "total_amount": line_total,
        "expected_delivery_date": expected_delivery_date,
    }


# ── PO master payload builder ─────────────────────────────────────────────────

def build_po_payload(
    supplier_ref_id: int,
    items: List[dict],
    po_item_type: int,           # resolved live (Farm / Non-Farm ID for this tenant)
    po_type: int = PO_TYPE_DOMESTIC,
    base_currency: int = CURRENCY_ID,
    txn_currency: int = CURRENCY_ID,
    conversion_rate: float = 1.0,
    parameter1: int = 1,         # Division
    parameter2: int = 1,         # Department
    parameter5: int = 1,         # Location
    parameter6: int = 1,         # Type of Sale
    supplier_payment_terms: int = None,
    supplier_delivery_terms: int = None,
    supplier_ship_from: int = None,
    supplier_bill_from: int = None,
    transaction_date: str = None,
) -> dict:
    """
    Build a complete PO payload ready to POST.

    supplier_ship_from and supplier_bill_from come from the Supplier's
    address list (resolve via GET Supplier/{id}).

    All FK IDs must be resolved from live ERP before calling.
    Items must be built with build_po_item().
    """
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    total = compute_po_total(items)

    return {
        "transaction_date": transaction_date,
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": SUPPLIER_REF_TYPE,
        "gst_registration_type": None,
        "po_item_type": po_item_type,
        "po_type": po_type,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": conversion_rate,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "txn_currency_total_amount": total,
        "supplier_details": {
            "supplier_payment_terms": supplier_payment_terms,
            "supplier_delivery_terms": supplier_delivery_terms,
            "packing_forwarding_ref_id": PACKING_FORWARDING_NILL,
            "supplier_ship_from": supplier_ship_from,
            "supplier_bill_from": supplier_bill_from,
        },
        "additional_details": {
            "transportation_charges": 0.0,
            "txn_currency_discount_percent": 0.0,
            "txn_currency_discount_amount": 0.0,
            "txn_currency_interest_percent": 0.0,
            "txn_currency_interest_amount": 0.0,
            "remark": None,
        },
        "purchasing_order_items_details": items,
    }


# ══════════════════════════════════════════════════════════════════════════════
# QC — Quality Check
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_QC_PARAM_IDS = [1, 2, 3]  # Moisture, Purity, Foreign Matter


def build_qc_detail_params(param_ids: list = None) -> list:
    """CQP (Commodity Quality Parameter) rows for one QC line item."""
    ids = param_ids or DEFAULT_QC_PARAM_IDS
    return [{"item_quality_parameter_ref_id": pid, "actual_value": 1} for pid in ids]


def build_qc_item(
    item_ref_id: int,
    hsn_sac_no: int,
    alternate_uom: int,    # same as PO alternate_uom (MT)
    uom: int,              # base UOM (KG)
    uom_conversion: float,
    grn_qty: float,        # in alternate UOM (MT)
    base_rate: float,      # same rate as PO
    no_of_bags: int = 1,
    deduction_percent: float = None,
    quality_param_ids: list = None,
) -> dict:
    """
    Build one QC line item (one row of qc_details).

    accepted_qty          = grn_qty (no rejection assumed)
    alternate_accepted_qty = accepted_qty  (same UOM as PO qty)
    net_rate              = base_rate * (1 - deduction_percent/100)  or base_rate if no deduction
    txn_currency_amount   = net_rate * alternate_accepted_qty
    """
    accepted_qty = grn_qty
    rejected_qty = 0.0

    if deduction_percent:
        deduction_rate = round(base_rate * deduction_percent / 100, 6)
        net_rate = round(base_rate - deduction_rate, 6)
        qc_rate = net_rate
    else:
        deduction_rate = None
        net_rate = base_rate
        qc_rate = None
        deduction_percent = None

    txn_amount = round(net_rate * accepted_qty, 6)

    return {
        "item_ref_id": item_ref_id,
        "hsn_sac_no": hsn_sac_no,
        "uom": alternate_uom,        # field name in API is uom but holds the alternate UOM ID
        "no_of_bags": no_of_bags,
        "grn_qty": grn_qty,
        "accepted_qty": accepted_qty,
        "rejected_qty": rejected_qty,
        "alternate_accepted_qty": accepted_qty,  # in MT, used by PB
        "base_rate": base_rate,
        "deduction_percent": deduction_percent,
        "deduction_rate": deduction_rate,
        "qc_rate": qc_rate,
        "net_rate": net_rate,
        "txn_currency_amount": txn_amount,
        "details": build_qc_detail_params(quality_param_ids),
    }


def build_qc_payload(
    supplier_ref_id: int,
    po_ref_id: int,
    item_type_ref_id: int,
    items: list,
    base_currency: int = CURRENCY_ID,
    txn_currency: int = CURRENCY_ID,
    conversion_rate: float = 1.0,
    parameter1: int = 1,
    parameter2: int = 1,
    parameter5: int = 1,
    parameter6: int = 1,
    transaction_date: str = None,
) -> dict:
    """
    Build a QC payload for a PO-linked quality check (no gate pass / GRN needed).

    Field names from real QC GET response (QC/2026-2027/000038 on tenant 752):
      po_ref_id_id         = the PO ID
      item_type_ref_id     = po_item_type (same as PO)
      qc_additional_details: vehicle_no and driver_name are null in this flow
      total_txn_currency_amount = SUM(txn_currency_amount per line)
    """
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    total = round(sum(it.get("txn_currency_amount", 0.0) for it in items), 6)

    return {
        "transaction_date": transaction_date,
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": SUPPLIER_REF_TYPE,
        "item_type_ref_id": item_type_ref_id,
        "po_ref_id_id": po_ref_id,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": conversion_rate,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "total_txn_currency_amount": total,
        "qc_additional_details": {
            "vehicle_no": None,
            "driver_name": None,
            "remark": None,
        },
        "qc_details": items,
    }


# ══════════════════════════════════════════════════════════════════════════════
# PB — Purchase Booking (QC-referenced)
# ══════════════════════════════════════════════════════════════════════════════

def build_pb_item(
    item_ref_id: int,
    hsn_sac_no: int,
    alternate_uom: int,
    uom: int,
    uom_conversion: float,
    rate: float,           # net_rate from QC
    alternate_qty: float,  # alternate_accepted_qty from QC
    empty_bag_weight: float = 0.0,
    labour_charges: float = 0.0,
) -> dict:
    """
    Build one PB line item.

    Field names from real PB GET (PURB/2026-2027/000026 on tenant 752).

    Calculations:
      alternate_net_qty           = alternate_qty - empty_bag_weight
      txn_currency_amount_detail  = rate × alternate_net_qty - labour_charges
      txn_currency_total_txn_amount = txn_currency_amount_detail
    """
    alternate_net_qty = round(alternate_qty - empty_bag_weight, 6)
    txn_amount = round(rate * alternate_net_qty - labour_charges, 6)

    return {
        "item_ref_id": item_ref_id,
        "hsn_sac_no": hsn_sac_no,
        "alternate_uom": alternate_uom,
        "uom": uom,
        "uom_conversion": uom_conversion,
        "alternate_qty": alternate_qty,
        "empty_bag_weight": empty_bag_weight,
        "alternate_net_qty": alternate_net_qty,
        "rate": rate,
        "labour_charges": labour_charges,
        "is_gst_set_off": True,
        "tax_rate": None,
        "discount_percentage": None,
        "txn_currency_amount_detail": txn_amount,
        "txn_currency_tax_amount_details": 0.0,
        "txn_currency_total_txn_amount": txn_amount,
    }


def build_pb_payload(
    qc_ref_id: int,
    po_ref_id: int,
    supplier_ref_id: int,
    items: list,
    supplier_payment_terms_ref_id: int = None,
    base_currency: int = CURRENCY_ID,
    txn_currency: int = CURRENCY_ID,
    conversion_rate: float = 1.0,
    parameter1: int = 1,
    parameter2: int = 1,
    parameter5: int = 1,
    parameter6: int = 1,
    transaction_date: str = None,
) -> dict:
    """
    Build a Purchase Booking payload linked to QC (and its PO).

    Field names from real PB GET (PURB/2026-2027/000026 on tenant 752).
    grn_details is empty on POST — auto-created by ERP after save.
    """
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    total = round(sum(it.get("txn_currency_total_txn_amount", 0.0) for it in items), 6)

    return {
        "transaction_date": transaction_date,
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": SUPPLIER_REF_TYPE,
        "qc_ref_id_id": qc_ref_id,
        "po_ref_id_id": po_ref_id,
        "supplier_payment_terms_ref_id": supplier_payment_terms_ref_id,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": conversion_rate,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "txn_currency_amount": total,
        "txn_currency_total_amount": total,
        "txn_currency_discount_amount": 0.0,
        "round_off_debit_amount": 0.0,
        "round_off_credit_amount": None,
        "is_tds_applicable": None,
        "section_ref_id": 0,
        "grn_details": [],
        "purchase_booking_details": items,
    }
