"""
Purchase Chain — creates a linked PO -> Gate Pass -> GRN -> QC chain
for the same supplier.

Usage:
    python -m pages.private_b2b.scripts.purchase_chain --supplier 1 --count 3
    python -m pages.private_b2b.scripts.purchase_chain --supplier 1 --dry-run
    python -m pages.private_b2b.scripts.purchase_chain --supplier 1 --delay 1.0
"""

import argparse
import json
import math
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Dict, List, Optional

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.private_b2b.modules.purchase_booking.utils.ad_setup import (
    fetch_coa,
    resolve_accounts,
    fetch_type_of_sale_ids,
    find_existing_pb_ad,
    build_ad_payload,
    apply_ad,
)
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    ITEM_NAMES as PO_ITEM_NAMES,
    UOM_NAMES as PO_UOM_NAMES,
    HSN_SAC_NAMES as PO_HSN_NAMES,
    PO_ITEM_TYPE_NAMES,
    PO_TYPE_NAMES,
    PAYMENT_TERMS_NAMES,
    DELIVERY_TERMS_NAMES,
    CURRENCY_NAMES as PO_CURRENCY_NAMES,
    DEPARTMENT_NAMES,
    DIVISION_NAMES,
    LOCATION_NAMES,
    TYPE_OF_SALE_NAMES,
)
from pages.private_b2b.modules.gate_pass.data.gate_pass_data import (
    DELIVERY_TYPE_NAMES,
    ITEM_NAMES as GP_ITEM_NAMES,
)
from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
    ITEM_NAMES as GRN_ITEM_NAMES,
    UOM_NAMES as GRN_UOM_NAMES,
    HSN_SAC_NAMES as GRN_HSN_NAMES,
)
from pages.private_b2b.modules.quality_check.data.quality_check_data import (
    ITEM_NAMES as QC_ITEM_NAMES,
    QUALITY_PARAMETER_NAMES,
)
from pages.private_b2b.modules.purchase_order.utils.api_purchase_order_utils import (
    POAPIUtils,
)
from pages.private_b2b.modules.gate_pass.utils.api_gate_pass_utils import (
    GPAPIUtils,
)
from pages.private_b2b.modules.goods_receipt_note.utils.api_goods_receipt_note_utils import (
    GRNAPIUtils,
)
from pages.private_b2b.modules.quality_check.utils.api_quality_check_utils import (
    QCAPIUtils,
)
from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import (
    PBAPIUtils,
)
from pages.private_b2b.modules.sales_order.utils.api_sales_order_utils import (
    SOAPIUtils,
)
from pages.private_b2b.scripts.chain_context import ChainContext, ChainContextDiscoverer

from pages.commodity_settings.modules.commodity_quality_parameter.data.commodity_quality_parameter_data import (
    cqp_entry_is_active,
    cqp_transaction_type_is,
    resolve_purchase_transaction_type_id,
)

from dataclasses import replace


# ---------------------------------------------------------------------------
# Supplier lookup
# ---------------------------------------------------------------------------
SUPPLIER_NAMES = {
    1: "Maa Kalinga Commodities",
    2: "Maha Ganga Grain Processors",
    3: "Maa Ganesh Commodities & Sons",
    4: "Guru Agro Commodities & Sons",
    5: "Baba Rajput Supply Chain",
    6: "Jagdamba Yamuna Cotton Mills Corp",
    7: "Maa Sutlej Produce Associates",
    8: "Jagdamba Yamuna Commodities Pvt Ltd",
    9: "Hari Ganesh Grain Processors",
    10: "Om Maurya Oil Mills & Bros",
}


def _supplier_name(sid: int) -> str:
    return SUPPLIER_NAMES.get(sid, f"Supplier_{sid}")


# ---------------------------------------------------------------------------
# Item generator — produces items that work across PO / GP / GRN
# ---------------------------------------------------------------------------
# Realistic pseudo-random ranges for auto-generated lines (single source of
# truth for the generated quantities/rates; adjust ranges freely). These stay
# dynamic — a fresh value is drawn per item per run, never baked per item.
_QTY_MIN = 500
_QTY_MAX = 2000
_RATE_MIN = 500.0
_RATE_MAX = 6000.0


def _rand_qty() -> float:
    return float(random.randint(_QTY_MIN, _QTY_MAX))


def _rand_rate() -> float:
    return round(random.uniform(_RATE_MIN, _RATE_MAX), 2)


# Realistic ranges for QC "user inputs" (empty bag weight / deduction /
# discount). The manual QC 1345 used 0–12 kg bags, 2–3% deductions, 0–5%
# discounts; these stay dynamic per run.
_EMPTY_BAG_MIN = 0.0
_EMPTY_BAG_MAX = 12.0
_DEDUCTION_MIN = 0.0
_DEDUCTION_MAX = 5.0
_DISCOUNT_MIN = 0.0
_DISCOUNT_MAX = 5.0


def _rand_empty_bag_weight() -> float:
    return round(random.uniform(_EMPTY_BAG_MIN, _EMPTY_BAG_MAX), 2)


def _rand_deduction_percent() -> float:
    return round(random.uniform(_DEDUCTION_MIN, _DEDUCTION_MAX), 2)


def _rand_discount_rate() -> float:
    return round(random.uniform(_DISCOUNT_MIN, _DISCOUNT_MAX), 2)


def _compute_qc_line_fields(
    base_rate: float,
    grn_qty: float,
    empty_bag_weight: float,
    deduction_percent: float,
    discount_rate: float,
    is_rate_weight_deduction: bool = False,
) -> dict:
    """Derive every stored QC line field from the manual QC 1345 math.

    Verified against QC 1345 / 1346 lines:
      total_amount            = base_rate × grn_qty
      empty_bags_txn_amount   = empty_bag_weight × base_rate
      alternate_accepted_qty  = grn_qty − empty_bag_weight
      qc_deduction_rate       = base_rate × deduction_percent / 100
      deduction_weight        = grn_qty × deduction_percent / 100

      is_rate_weight_deduction = False (rate mode, default):
        qc_deduction_amount   = (total_amount − empty_bags) × deduction_percent / 100
      is_rate_weight_deduction = True (weight mode):
        qc_deduction_amount   = deduction_weight × base_rate

      subtotal                = total_amount − empty_bags − qc_deduction_amount
      c_d_deduction           = subtotal × discount_rate / 100   (None when 0)
      txn_currency_amount     = subtotal − c_d_deduction
      rate                    = txn_currency_amount / alternate_accepted_qty
      quantity_deduction      = ceil(deduction_weight)
    """
    total_amount = round(base_rate * grn_qty, 6)
    empty_bags_txn_amount = round(empty_bag_weight * base_rate, 6)
    accepted_qty = grn_qty - empty_bag_weight
    qc_deduction_rate = round(base_rate * deduction_percent / 100.0, 6)
    deduction_weight = round(grn_qty * deduction_percent / 100.0, 6)

    if is_rate_weight_deduction:
        qc_deduction_amount = round(deduction_weight * base_rate, 6)
    else:
        net_of_empty_bag = total_amount - empty_bags_txn_amount
        qc_deduction_amount = round(net_of_empty_bag * deduction_percent / 100.0, 6)

    subtotal = total_amount - empty_bags_txn_amount - qc_deduction_amount
    c_d_deduction = round(subtotal * discount_rate / 100.0, 6) if discount_rate else None
    txn_currency_amount = round(subtotal - (c_d_deduction or 0.0), 6)
    rate = round(txn_currency_amount / accepted_qty, 6) if accepted_qty else 0.0

    return {
        "total_amount": total_amount,
        "empty_bags_txn_amount": empty_bags_txn_amount,
        "alternate_accepted_qty": accepted_qty,
        "qc_deduction_rate": qc_deduction_rate,
        "deduction_weight": deduction_weight,
        "qc_deduction_amount": qc_deduction_amount,
        "c_d_deduction": c_d_deduction,
        "txn_currency_amount": txn_currency_amount,
        "rate": rate,
        "quantity_deduction": math.ceil(deduction_weight),
    }


def _generate_chain_items(
    num_items: int = 2,
    item_ref_id: int = 5,
    item_ref_ids: Optional[List[int]] = None,
    hsn_sac_no: int = 2,
    uom: int = 3,
    base_uom: int = 4,
    alternate_uom: int = 4,
    item_data: Optional[List[dict]] = None,
) -> List[dict]:
    """Build generic chain items (PO/GP/GRN/QC share this shape).

    When *item_data* is given (per-item data resolved from Item Master, each
    dict with item_ref_id/hsn_sac_no/alternate_uom/base_uom/uom/uom_conversion),
    each line uses that item's real HSN/UOM instead of the tenant scalars.
    """
    today = date.today().isoformat()
    if item_data:
        items = []
        for i, data in enumerate(item_data):
            qty = _rand_qty()
            rate = _rand_rate()
            items.append({
                "item_ref_id": data["item_ref_id"],
                "hsn_sac_no": data["hsn_sac_no"],
                "uom": data.get("uom", data["alternate_uom"]),
                "base_uom": data.get("base_uom", data["alternate_uom"]),
                "alternate_uom": data.get("alternate_uom", data["uom"]),
                "uom_conversion": data.get("uom_conversion", 1.0),
                "alternate_quantity": str(qty),
                "quantity": qty,
                "rate": rate,
                "tax_rate": data.get("tax_rate", 0.0),
                "no_of_bags": int(qty),
                "expected_delivery_date": today,
                "received_qty": qty,
                "accepted_qty": qty,
                "rejected_qty": 0.0,
            })
        return items

    ids = item_ref_ids if item_ref_ids else [item_ref_id]
    items = []
    for i in range(num_items):
        qty = _rand_qty()
        rate = _rand_rate()
        items.append({
            "item_ref_id": ids[i % len(ids)],
            "hsn_sac_no": hsn_sac_no,
            "uom": uom,
            "base_uom": base_uom,
            "alternate_uom": alternate_uom,
            "uom_conversion": 1.0,
            "alternate_quantity": str(qty),
            "quantity": qty,
            "rate": rate,
            "tax_rate": 0.0,
            "no_of_bags": int(qty),
            "expected_delivery_date": today,
            "received_qty": qty,
            "accepted_qty": qty,
            "rejected_qty": 0.0,
        })
    return items


def _po_items_from(items: List[dict], gst_type: str = "IGST") -> List[dict]:
    """Map generic chain items to PO line shape (mirrors the stored record).

    Real PO line field set (tenant 686, /purchase_order/3242/):
      item_ref_id, hsn_sac_no, alternate_uom, uom, uom_conversion,
      alternate_quantity, rate, gst_type, tax_rate, txn_currency_amount_detail,
      txn_currency_tax_amount_details, total_amount, expected_delivery_date
    (no ``quantity``, no ``is_gst_set_off``)

    Field semantics (known-good flow):
      alternate_uom = item primary UOM (e.g. MT)
      uom           = item base UOM (e.g. KG)
    Computed fields the ERP expects pre-filled:
      txn_currency_amount_detail      = rate × alternate_quantity
      txn_currency_tax_amount_details = that × tax_rate / 100
      total_amount                    = amount + tax

    ``tax_rate`` is resolved per item (HSN-based) before this is called and
    carried on the item dict — items without a configured rate use 0.0.
    """
    out = []
    for it in items:
        rate = it["rate"]
        tax_rate = float(it.get("tax_rate") or 0.0)
        alt_qty = float(it.get("alternate_quantity") or it["quantity"])
        amount = round(rate * alt_qty, 6)
        tax = round(amount * tax_rate / 100.0, 6)
        out.append({
            "item_ref_id": it["item_ref_id"],
            "hsn_sac_no": it["hsn_sac_no"],
            "uom": it.get("base_uom", it["uom"]),
            "alternate_uom": it.get("alternate_uom", it["uom"]),
            "uom_conversion": it.get("uom_conversion", 1.0),
            "alternate_quantity": it.get("alternate_quantity", "1"),
            "rate": rate,
            "gst_type": gst_type,
            "tax_rate": tax_rate,
            "txn_currency_amount_detail": amount,
            "txn_currency_tax_amount_details": tax,
            "total_amount": round(amount + tax, 6),
            "expected_delivery_date": it["expected_delivery_date"],
        })
    return out


def _gp_items_from(items: List[dict]) -> List[dict]:
    return [
        {
            "item_ref_id": it["item_ref_id"],
            "no_of_bags": it["no_of_bags"],
            "alternate_quantity": it["quantity"],
            "alternate_uom": it.get("alternate_uom", it.get("uom")),
            "base_uom": it["base_uom"],
            "uom_conversion": 1.0,
            "hsn_sac_no": it["hsn_sac_no"],
        }
        for it in items
    ]


def _split_items_across_gps(items: List[dict], gp_count: int) -> List[List[dict]]:
    """Evenly split each item's quantity across *gp_count* gate passes.

    Every GP receives an equal share of each item; an item's remainder (if any)
    goes to the last GP. GPs left with zero quantity for every item are dropped.
    """
    n = max(1, int(gp_count))
    plans: List[List[dict]] = [[] for _ in range(n)]
    for it in items:
        total = float(it.get("quantity", 0) or 0)
        base = int(total // n)
        rem = int(total % n)
        for g in range(n):
            qty = float(base + (rem if g == n - 1 else 0))
            if qty <= 0:
                continue
            row = dict(it)
            row.update({
                "quantity": qty,
                "alternate_quantity": str(qty),
                "received_qty": qty,
                "accepted_qty": qty,
                "rejected_qty": 0.0,
                "no_of_bags": max(1, int(qty)),
            })
            plans[g].append(row)
    return [p for p in plans if p]


def _grn_items_from(
    items: List[dict],
    po_quantity_by_item: Optional[dict] = None,
    balance_by_item: Optional[dict] = None,
) -> List[dict]:
    po_qty = po_quantity_by_item or {}
    bal = balance_by_item or {}
    return [
        {
            "item_ref_id": it["item_ref_id"],
            "hsn_sac_no": it["hsn_sac_no"],
            "uom": it.get("base_uom", it["uom"]),
            "alternate_uom": it.get("alternate_uom", it["uom"]),
            "uom_conversion": it.get("uom_conversion", 1.0),
            "alternate_received_qty": it["quantity"],
            "alternate_accepted_qty": it["accepted_qty"],
            "alternate_rejected_qty": it["rejected_qty"],
            "rate": it["rate"],
            "no_of_bags": it["no_of_bags"],
            "gate_pass_quantity": it["quantity"],
            "po_quantity": float(po_qty.get(it["item_ref_id"], it["quantity"])),
            "po_balance_quantity": float(bal.get(it["item_ref_id"], it["quantity"])),
        }
        for it in items
    ]


def _qc_items_from(items: List[dict], ctx=None, cqp_by_item: Optional[dict] = None,
                   bags_type_id: int = 1, qc_discount: bool = True,
                   is_rate_weight_deduction: bool = False) -> List[dict]:
    """Build QC line items matching the manual QC 1345 stored shape.

    Every derived amount is computed here (ERP does NOT auto-patch on POST).
    The per-parameter ``actual_value`` comes from the item's Commodity Quality
    Parameter config (the lowest rate = min_quality_value); when an item has no
    CQP entry, the discovered/generic quality parameters are used instead.
    ``bags_type_id`` is the resolved Packages (bag type) FK — never hardcoded.
    """
    quality_details = (
        ctx.quality_parameters if ctx and ctx.quality_parameters
        else [
            {"item_quality_parameter_ref_id": 1, "actual_value": 1},
            {"item_quality_parameter_ref_id": 2, "actual_value": 1},
            {"item_quality_parameter_ref_id": 3, "actual_value": 1},
        ]
    )
    cqp_by_item = cqp_by_item or {}

    def _param_details(item_id: int) -> List[dict]:
        cqp = cqp_by_item.get(item_id)
        if cqp:
            return [
                {"item_quality_parameter_ref_id": p["quality_type"], "actual_value": p["min_quality_value"]}
                for p in cqp
                if p.get("quality_type") is not None
            ]
        return list(quality_details)

    out = []
    for it in items:
        empty_bag_weight = _rand_empty_bag_weight()
        deduction_percent = _rand_deduction_percent()
        discount_rate = _rand_discount_rate() if qc_discount else 0.0
        computed = _compute_qc_line_fields(
            it["rate"], it["accepted_qty"], empty_bag_weight, deduction_percent, discount_rate,
            is_rate_weight_deduction=is_rate_weight_deduction,
        )
        item_id = it["item_ref_id"]
        out.append({
            "item_ref_id": item_id,
            "is_rate_weight_deduction": is_rate_weight_deduction,
            "alternate_uom": it.get("uom", ctx.alternate_uom if ctx else 3),
            "uom": it.get("base_uom", ctx.base_uom if ctx else 4),
            "hsn_sac_no": it["hsn_sac_no"],
            "base_rate": it["rate"],
            "grn_qty": it["accepted_qty"],
            "alternate_rejected_qty": it["rejected_qty"],
            "total_amount": computed["total_amount"],
            "no_of_bags": it["no_of_bags"],
            "empty_bag_weight": empty_bag_weight,
            "empty_bags_txn_amount": computed["empty_bags_txn_amount"],
            "alternate_accepted_qty": computed["alternate_accepted_qty"],
            "deduction_percent": deduction_percent,
            "qc_deduction_rate": computed["qc_deduction_rate"],
            "deduction_weight": computed["deduction_weight"],
            "qc_deduction_amount": computed["qc_deduction_amount"],
            "discount_rate": discount_rate,
            "c_d_deduction": computed["c_d_deduction"],
            "txn_currency_amount": computed["txn_currency_amount"],
            "rate": computed["rate"],
            "uom_conversion": 1.0,
            "qc_parameter_details": [
                {**p, "allowable_percent": 0.0, "quantity_deduction": computed["quantity_deduction"]}
                for p in _param_details(item_id)
            ],
            "qc_bags_details": [
                {
                    "type_of_bags_ref_id": bags_type_id,
                    "quantity_of_bags": 1,
                    "weight_of_bags": 1.0,
                    "total_weight_of_bags": 1.0,
                }
            ],
        })
    return out


def _pb_items_from(items: List[dict], ctx=None) -> List[dict]:
    from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import build_pb_item
    alt_uom  = ctx.alternate_uom if ctx else 3
    base_uom = ctx.base_uom      if ctx else 4
    return [
        build_pb_item(
            item_ref_id=it["item_ref_id"],
            hsn_sac_no=it["hsn_sac_no"],
            alternate_uom=alt_uom,
            uom=base_uom,
            rate=it["rate"],
            no_of_bags=it["no_of_bags"],
        )
        for it in items
    ]


# Realistic ranges for PB "user inputs" (labour / transport / round off).
_LABOUR_MIN = 10.0
_LABOUR_MAX = 300.0
_TRANSPORT_MIN = 0.0
_TRANSPORT_MAX = 500.0


def _rand_labour_charges() -> float:
    return round(random.uniform(_LABOUR_MIN, _LABOUR_MAX), 2)


def _rand_transport_charges() -> float:
    return round(random.uniform(_TRANSPORT_MIN, _TRANSPORT_MAX), 2)


def _rand_round_off() -> float:
    return round(random.uniform(0.0, 1.0), 3)


def _pb_items_from_qc(qc_items: List[dict], items: List[dict] = None, ctx=None) -> List[dict]:
    """Build PB lines mirroring the in-flow QC lines (manual PB 2480 shape).

    Each QC line already carries base_rate / grn_qty / no_of_bags /
    empty_bag_weight / empty_bags_txn_amount / alternate_accepted_qty /
    discount_rate / c_d_deduction / txn_currency_amount. PB reuses those and
    adds PB-specific inputs (labour / GST / round off). GST is only applied
    when is_gst_set_off is True; gst_type follows tax_rate (25 → CGST+SGST,
    5 → IGST). amount_detail = QC txn_currency_amount − labour_charges.
    """
    from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import (
        build_pb_line,
        gst_type_for_rate,
    )

    tax_by_item = {it["item_ref_id"]: float(it.get("tax_rate") or 0.0) for it in (items or [])}

    def _q4(v):
        # ERP caps PB quantity fields at 4 decimal places.
        return round(float(v or 0.0), 4)

    out = []
    for qc in qc_items:
        labour = 0.0
        amount_detail = round(float(qc["txn_currency_amount"] or 0.0), 6)
        tax_rate = tax_by_item.get(qc["item_ref_id"], 0.0)
        gst_type = gst_type_for_rate(tax_rate)
        discount_rate = float(qc.get("discount_rate") or 0.0)
        # Monetary cash discount: amount_detail from QC is post-discount, so
        # pre_discount = amount_detail / (1 - discount_rate/100)
        # cash_discount = pre_discount - amount_detail
        if discount_rate > 0.0:
            cash_discount = round(amount_detail * discount_rate / (100.0 - discount_rate), 6)
        else:
            cash_discount = 0.0
        out.append(build_pb_line(
            item_ref_id=qc["item_ref_id"],
            hsn_sac_no=qc["hsn_sac_no"],
            alternate_uom=qc.get("alternate_uom", ctx.alternate_uom if ctx else 3),
            uom=qc.get("uom", ctx.base_uom if ctx else 4),
            base_rate=qc["base_rate"],
            alternate_qty=_q4(qc["grn_qty"]),
            no_of_bags=qc["no_of_bags"],
            empty_bag_weight=_q4(qc["empty_bag_weight"]),
            empty_bags_txn_amount=_q4(qc["empty_bags_txn_amount"]),
            alternate_net_qty=_q4(qc["alternate_accepted_qty"]),
            discount_percentage=_q4(discount_rate),
            discount_amount=cash_discount,
            amount_detail=amount_detail,
            labour_charges=labour,
            transport=0.0,
            tax_rate=tax_rate,
            gst_type=gst_type,
            uom_conversion=qc.get("uom_conversion", 1.0),
        ))
    return out


def _so_items_from_qc(qc_items: List[dict], ctx=None, tax_rates: Optional[Dict[str, List[float]]] = None) -> List[dict]:
    """Build Sales Order lines mirroring the in-flow QC lines.

    Quantity/rate come straight from the QC line (user decision #3): quantity =
    QC accepted qty, rate = QC base rate. Tax rate is picked at random from the
    available HSN tax rates (falling back to a sensible default when unknown) —
    the SO screen has no auto-patch, so every amount is computed here.
    """
    from pages.private_b2b.modules.sales_order.data.sales_order_data import build_so_line

    def _q(v):
        return round(float(v or 0.0), 6)

    out = []
    for qc in qc_items:
        tax_rate = _random_so_tax_rate(qc.get("item_ref_id"), qc.get("hsn_sac_no"), tax_rates)
        out.append(build_so_line(
            item_ref_id=qc["item_ref_id"],
            hsn_sac_no=qc["hsn_sac_no"],
            quantity=_q(qc.get("alternate_accepted_qty") or qc.get("grn_qty") or 0.0),
            rate=_q(qc.get("base_rate") or qc.get("rate") or 0.0),
            tax_rate=tax_rate,
            uom=qc.get("uom", ctx.base_uom if ctx else None),
            alternate_uom=qc.get("alternate_uom", ctx.alternate_uom if ctx else None),
            uom_conversion=qc.get("uom_conversion", 1.0),
            expected_delivery_date=qc.get("transaction_date") or date.today().isoformat(),
        ))
    return out


def _random_so_tax_rate(item_ref_id: int, hsn_sac_no=None,
                        tax_rates: Optional[Dict[str, List[float]]] = None) -> float:
    """Pick a random tax rate for an SO line.

    Uses the chain's HSN -> tax-rates map when available (same source the PO
    item filter uses); otherwise defaults to 5.0 (IGST, per the manual SO).
    """
    rates = None
    if tax_rates:
        rates = tax_rates.get(str(hsn_sac_no)) if hsn_sac_no is not None else None
        if not rates:
            rates = tax_rates.get(str(item_ref_id))
    if rates:
        return float(random.choice(list(rates)))
    return 5.0


# ---------------------------------------------------------------------------
# PurchaseChain class
# ---------------------------------------------------------------------------
class PurchaseChain:
    """Create a linked PO -> Gate Pass -> GRN chain for the same supplier.

    Args:
        token: JWT token (takes precedence if given).
        tenant: Tenant ID (default 711).
        client: Pre-authenticated RhythmERPAPIClient (avoids re-auth).
        delay: Seconds between API calls (default 0.3).
    """

    def __init__(
        self,
        token: str = "",
        tenant: str = "711",
        client: Optional[RhythmERPAPIClient] = None,
        delay: float = 0.3,
    ):
        self.delay = delay

        if client is not None:
            self.client = client
        else:
            self.client = RhythmERPAPIClient()
            if token:
                self.client.login_from_browser(token=token, tenant_id=tenant)
            else:
                self.client.login()

        self.po_api = POAPIUtils(self.client)
        self.gp_api = GPAPIUtils(self.client)
        self.grn_api = GRNAPIUtils(self.client)
        self.qc_api = QCAPIUtils(self.client)
        self.pb_api = PBAPIUtils(self.client)
        self.so_api = SOAPIUtils(self.client)

        self.results: List[dict] = []
        self._context: Optional[ChainContext] = None  # discovered lazily
        # Per-entity resolution caches (keyed by ERP id) — avoids repeated GETs
        # across chains in one run.
        self._supplier_cache: Dict[int, dict] = {}
        self._item_cache: Dict[int, Optional[dict]] = {}
        # Tenant PO header defaults, sniffed from an existing PO (schema 404s).
        self._po_defaults: Optional[dict] = None
        # Item-category resolution (ERP PO dropdown is category-scoped).
        self._categories: Optional[List[dict]] = None  # [{id, name, item_count}] desc
        self._item_category_map: Dict[int, int] = {}  # item_ref_id -> item_category
        # HSN -> available tax rates, flattened from the Tax Rate screen.
        self._tax_rates: Optional[Dict[str, List[float]]] = None
        # Item -> Commodity Quality Parameter config (item_ref_id -> [{quality_type,
        # min_quality_value, max_quality_value, rate_percentage, multiplier}]).
        self._cqp_cache: Dict[int, List[dict]] = {}
        # Resolved Packages (bag type) FK for the QC bags detail row.
        self._bags_type_id: Optional[int] = None
        # Sales Order header FKs — resolved once and cached per instance.
        self._customer_cache: Dict[int, dict] = {}
        self._customer_ref_id: Optional[int] = None
        self._so_type_id: Optional[int] = None
        self._supply_type_id: Optional[int] = None

    def _resolve_bags_type_id(self) -> int:
        """Return a valid Packages (bag type) FK for QC bags details.

        Hardcoding type_of_bags_ref_id=1 breaks tenants whose bag types don't
        start at 1. Resolved live and cached; when the tenant has no Packages
        entries, a default 'Joot Bags' entry is auto-created and its ID used.
        """
        if self._bags_type_id is not None:
            return self._bags_type_id
        from pages.private_b2b.modules.quality_check.data.quality_check_data import resolve_bags_type_id
        bags_type_id = resolve_bags_type_id(self.client, create_if_missing=True)
        if bags_type_id is None:
            raise RuntimeError(
                "Could not resolve or auto-create a 'Packages' (bag type) FK "
                "for the QC bags detail row — refusing to POST QC with a "
                "guessed bag type."
            )
        self._bags_type_id = bags_type_id
        return bags_type_id

    def _resolve_customer_ref_id(self) -> int:
        """Return a valid Customer FK for the Sales Order header.

        The SO screen's customer dropdown is populated from the Customers
        screen. Resolved live from the customer list and cached; raises a clear
        error when the tenant has no customers (so we never guess an FK).
        """
        if self._customer_ref_id is not None:
            return self._customer_ref_id
        from pages.private_b2b.modules.sales_order.data.sales_order_data import (
            resolve_customer_ref_id,
        )
        customer_ref_id = resolve_customer_ref_id(self.client)
        if customer_ref_id is None:
            raise RuntimeError(
                "No Customers found in ERP — cannot create a Sales Order. "
                "Add a Customer first."
            )
        self._customer_ref_id = customer_ref_id
        return customer_ref_id

    def _resolve_customer_details(self, customer_ref_id: int) -> dict:
        """Resolve the customer's own billing/shipping addresses + terms.

        Same reasoning as ``_resolve_supplier_details``: the generic dropdown
        values can belong to another party and cause an HTTP 500 on SO create.
        Uses the SO module's extract_customer_details() so the output keys match
        the SO payload builder exactly.
        """
        if customer_ref_id in self._customer_cache:
            return self._customer_cache[customer_ref_id]

        from pages.private_b2b.modules.sales_order.data.sales_order_data import (
            extract_customer_details,
        )
        detail = self.client.get_entry("Customer", customer_ref_id)
        out = extract_customer_details(detail)

        log.info(f"  Customer #{customer_ref_id} resolved: {out}")
        self._customer_cache[customer_ref_id] = out
        return out

    def _resolve_so_type_id(self) -> int:
        """Return a valid Sales Order Type FK (resolved by label, 'Commission')."""
        if self._so_type_id is not None:
            return self._so_type_id
        from pages.private_b2b.modules.sales_order.data.sales_order_data import (
            resolve_so_type_id,
        )
        self._so_type_id = resolve_so_type_id(self.client) or 1
        return self._so_type_id

    def _resolve_supply_type_id(self) -> int:
        """Return a valid Supply Type FK (resolved by label, 'Both')."""
        if self._supply_type_id is not None:
            return self._supply_type_id
        from pages.private_b2b.modules.sales_order.data.sales_order_data import (
            resolve_supply_type_id,
        )
        self._supply_type_id = resolve_supply_type_id(self.client) or 2
        return self._supply_type_id

    @property
    def last_ctx(self) -> Optional[ChainContext]:
        """The most recently discovered ChainContext (None before first run)."""
        return self._context

    def get_context(self, item_category_id: Optional[int] = None) -> ChainContext:
        """Return the tenant context, discovering it on first call."""
        if self._context is None:
            self._context = ChainContextDiscoverer(self.client).discover(item_category_id=item_category_id)
        return self._context

    def get_context_for_supplier(self, supplier_ref_id: int) -> ChainContext:
        """Return the tenant context with supplier-scoped fields re-resolved.

        Clones the shared context and overlays the chosen supplier's own
        addresses + payment terms (Option A: per-chain suppliers use their own
        terms instead of the default supplier's). Supplier details are cached
        per id, so repeated calls for the same supplier are cheap.
        """
        ctx = self.get_context()
        det = self._resolve_supplier_details(supplier_ref_id)
        pb_terms = det.get("payment_terms") or ctx.pb_payment_terms
        return replace(
            ctx,
            supplier_ref_id=supplier_ref_id,
            supplier_ship_from=det.get("ship_from") or ctx.supplier_ship_from,
            supplier_bill_from=det.get("bill_from") or ctx.supplier_bill_from,
            payment_terms=det.get("payment_terms") or ctx.payment_terms,
            pb_payment_terms=pb_terms,
        )

    # ------------------------------------------------------------------
    # Per-entity resolution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _err_detail(api_utils, payload: dict = None) -> str:
        """Human-readable failure detail from the last API call."""
        resp = getattr(api_utils, "_last_response", None)
        status = getattr(api_utils, "_last_status", None)
        body = ""
        if resp is not None:
            try:
                body = resp.text[:400]
            except Exception:
                body = "<unreadable response>"
        detail = f"HTTP {status}; body: {body or 'no response'}"
        if payload is not None:
            detail += f" | sent: {json.dumps(payload, default=str)[:600]}"
        return detail

    def _resolve_supplier_details(self, supplier_ref_id: int) -> dict:
        """Resolve supplier-specific addresses/terms from the Supplier detail record.

        ship_from / bill_from MUST come from the chosen supplier — the generic
        first-dropdown values can point at another supplier's address and cause
        an HTTP 500 on PO create. Raises a clear error when the supplier has no
        registered address so we never send a bogus FK silently.
        """
        if supplier_ref_id in self._supplier_cache:
            return self._supplier_cache[supplier_ref_id]

        detail = None
        for attempt in range(4):
            detail = self.client.get_entry("Supplier", supplier_ref_id)
            if detail:
                break
            log.warning(
                f"  Supplier detail fetch failed for #{supplier_ref_id} "
                f"(attempt {attempt + 1}/4) — retrying"
            )
            time.sleep(0.4 * (attempt + 1))
        if not detail:
            raise RuntimeError(
                f"Supplier #{supplier_ref_id} not found in ERP — cannot create PO."
            )

        out = {
            "id": supplier_ref_id,
            "ship_from": None,
            "bill_from": None,
            "payment_terms": None,
            "delivery_terms": None,
            # Per-supplier PO header values (the PO screen schema 404s, so the
            # generic ctx dropdowns are unusable — these come from the supplier).
            "txn_currency": detail.get("default_currency_ref_id"),
            "po_type": detail.get("po_type_ref_id"),
            "tax_registration_status": "Registered",
        }
        for stepper in (detail.get("children") or []):
            name = (stepper.get("stepper_name") or "").lower()
            if "address" in name:
                addr_list = stepper.get("details") or []
                if len(addr_list) >= 1 and addr_list[0].get("id"):
                    out["ship_from"] = int(addr_list[0]["id"])
                if len(addr_list) >= 2 and addr_list[1].get("id"):
                    out["bill_from"] = int(addr_list[1]["id"])
            elif "additional" in name:
                if stepper.get("payment_terms_ref_id"):
                    out["payment_terms"] = int(stepper["payment_terms_ref_id"])
                if stepper.get("delivery_terms_ref_id"):
                    out["delivery_terms"] = int(stepper["delivery_terms_ref_id"])

        missing = [k for k in ("ship_from", "bill_from") if out[k] is None]
        if missing:
            raise RuntimeError(
                f"Supplier #{supplier_ref_id} has no {', '.join(missing)} address in ERP "
                f"— cannot create PO. Pick a supplier with a registered address."
            )

        log.info(f"  Supplier #{supplier_ref_id} resolved: {out}")
        self._supplier_cache[supplier_ref_id] = out
        return out

    def _resolve_item_detail(self, item_ref_id: int) -> Optional[dict]:
        """Resolve an item's own HSN / UOM / base UOM / conversion from Item Master.

        Returns None when the item does not exist. An item is only usable for a
        PO when it carries a HSN, a primary UOM and a base UOM — callers decide.
        """
        if item_ref_id in self._item_cache:
            return self._item_cache[item_ref_id]

        detail = self.client.get_entry("Item Master", item_ref_id)
        if not detail:
            self._item_cache[item_ref_id] = None
            return None

        hsn = detail.get("hsn_sac_code")
        primary_uom = detail.get("uom")        # item's primary UOM (e.g. MT)
        base_uom = detail.get("base_uom")      # item's base/weight UOM (e.g. KG)
        conv = 1.0
        try:
            conv = float(detail.get("base_uom_conversion") or 1.0)
        except (TypeError, ValueError):
            conv = 1.0

        out = {
            "item_ref_id": item_ref_id,
            "item_category": detail.get("item_category"),
            "hsn_sac_no": hsn,
            "alternate_uom": primary_uom,
            "base_uom": base_uom,
            "uom": primary_uom,     # generic chain item keeps primary as `uom`
            "uom_conversion": conv,
        }
        self._item_cache[item_ref_id] = out
        return out

    def _resolve_cqp_params(self, item_ref_id: int) -> List[dict]:
        """Return the item's Commodity Quality Parameter rows.

        Each CQP entry maps one item to one or more quality parameters; the
        QC line's per-parameter ``actual_value`` is the lowest rate
        (``min_quality_value``) from this config. Returns [] when the item has
        no CQP entry (caller falls back to generic/discovered parameters).
        """
        if item_ref_id in self._cqp_cache:
            return self._cqp_cache[item_ref_id]

        params: List[dict] = []
        try:
            resp = self.client.list_entries("Commodity Quality Parameter", page=1, page_size=500)
            rows = (resp or {}).get("screenmatlistingdata_set") or []
            if not hasattr(self, "_cqp_purchase_id"):
                self._cqp_purchase_id = resolve_purchase_transaction_type_id(self.client)
            purchase_id = self._cqp_purchase_id
            for row in rows:
                entry_id = row.get("id")
                if not entry_id:
                    continue
                detail = self.client.get_entry("Commodity Quality Parameter", entry_id)
                if not detail:
                    continue
                if detail.get("item_ref_id") != item_ref_id:
                    continue
                # Only entries with transaction type Purchase are referenced by
                # the QC step — a CQP with any other type (e.g. Spot) is not
                # usable here.
                if purchase_id is not None and not cqp_transaction_type_is(detail.get("transaction_type"), purchase_id):
                    log.info(
                        f"[Discovery] CQP for item #{item_ref_id} skipped: "
                        f"transaction_type={detail.get('transaction_type')} is not Purchase"
                    )
                    continue
                # Only entries whose from_date is strictly BEFORE today are
                # applied by the QC screen. A CQP created today (from_date ==
                # today) is not picked up until tomorrow, so it does not count
                # as a usable CQP here.
                if not cqp_entry_is_active(detail.get("from_date")):
                    log.info(
                        f"[Discovery] CQP for item #{item_ref_id} skipped: "
                        f"from_date={detail.get('from_date')} is not before today"
                    )
                    continue
                children = detail.get("children") or []
                for child in children:
                    for p in (child.get("details") or []):
                        if p.get("quality_type") is None:
                            continue
                        params.append({
                            "quality_type": p.get("quality_type"),
                            "min_quality_value": p.get("min_quality_value", 1),
                            "max_quality_value": p.get("max_quality_value", 100),
                            "rate_percentage": p.get("rate_percentage"),
                            "multiplier": p.get("multiplier"),
                        })
                break
            log.info(
                f"[Discovery] CQP for item #{item_ref_id}: "
                f"{[p['quality_type'] for p in params]}"
            )
        except Exception as e:
            log.warning(f"[Discovery] CQP resolve error for item #{item_ref_id}: {e}")

        self._cqp_cache[item_ref_id] = params
        return params

    def _sniff_po_defaults(self) -> dict:
        """Sniff tenant-level PO header defaults from an existing PO, if any.

        The PO screen schema 404s (`/core/dynamic-screen/Purchase Order/`), so
        generic dropdown discovery is unusable for po_item_type / base_currency
        / parameters. A real stored PO is the ground truth for the tenant; we
        read one (first page) and reuse its header values. Returns {} if there
        is no existing PO (callers fall back to ctx).
        """
        if self._po_defaults is not None:
            return self._po_defaults
        self._po_defaults = {}
        try:
            listing = self.po_api.list_pos(page_size=3)
        except Exception as e:
            log.warning(f"  Could not list POs for sniffing: {e}")
            return self._po_defaults
        if not listing:
            return self._po_defaults

        # list_pos returns {"rows": [...]} for the procure-to-pay list.
        rows = listing.get("rows") or listing.get("screenmatlistingdata_set") or []
        if not rows:
            return self._po_defaults
        po_id = rows[0].get("id")
        if not po_id:
            return self._po_defaults

        entry = self.po_api.get_po(po_id)
        if not entry:
            return self._po_defaults
        for key in (
            "po_item_type", "po_type", "base_currency", "txn_currency",
            "parameter1", "parameter2", "parameter5", "parameter6",
        ):
            val = entry.get(key)
            if val not in (None, ""):
                self._po_defaults[key] = val
        log.info(
            f"  Sniffed tenant PO defaults from existing PO #{po_id}: "
            f"{self._po_defaults}"
        )
        return self._po_defaults

    def _resolve_item_categories(self) -> List[dict]:
        """Return Item Categories with item counts, sorted count desc.

        The ERP PO screen filters the Item dropdown by the selected Item
        Category, so PO items must come from one category. This lists the
        Item Category screen plus Item Master and groups item counts by
        ``item_category`` (the FK). The Item Master *listing* does not expose
        ``item_category`` (only id/name/code/uom/status), so each item's full
        detail is fetched to read the FK. Cached per PurchaseChain instance.
        """
        if self._categories is not None:
            return self._categories
        self._categories = []
        try:
            cat_resp = self.client.list_entries("Item Category", page_size=500)
            item_resp = self.client.list_entries("Item Master", page_size=500)
        except Exception as e:
            log.warning(f"  Could not list categories/items for category resolution: {e}")
            return self._categories

        cats = (cat_resp or {}).get("screenmatlistingdata_set") or (cat_resp or {}).get("results") or []
        items = (item_resp or {}).get("screenmatlistingdata_set") or (item_resp or {}).get("results") or []

        # Item Master listing lacks item_category — fetch each item's detail
        # (the field lives on the full entry) so counts and the item->category
        # map are accurate. Threaded to stay fast on larger tenants.
        def _fetch_category(item_row):
            iid = item_row.get("id")
            try:
                det = self.client.get_entry("Item Master", iid)
                return iid, None if det is None else det.get("item_category")
            except Exception:
                return iid, None

        counts: Dict[int, int] = {}
        if items:
            with ThreadPoolExecutor(max_workers=8) as ex:
                for iid, cid in ex.map(_fetch_category, items):
                    if iid is None or cid is None:
                        continue
                    counts[cid] = counts.get(cid, 0) + 1
                    self._item_category_map[iid] = cid

        for c in cats:
            cid = c.get("id")
            if cid is None:
                continue
            self._categories.append({
                "id": int(cid),
                "name": c.get("item_code") or c.get("name") or f"Category {cid}",
                "item_count": int(counts.get(cid, 0)),
            })
        self._categories.sort(key=lambda x: x["item_count"], reverse=True)
        log.info(
            f"  Resolved {len(self._categories)} item categories "
            f"({len(self._item_category_map)} items mapped); "
            f"top: {self._categories[0] if self._categories else 'none'}"
        )
        return self._categories

    def _resolve_item_category(self, item_category_id: Optional[int]) -> Optional[dict]:
        """Validate a requested category, or auto-pick the most-populated one.

        Returns the chosen category dict ({id, name, item_count}) or None when
        no category exists in the ERP. Raises RuntimeError if an explicitly
        requested category id does not exist.
        """
        cats = self._resolve_item_categories()
        if not cats:
            return None
        if item_category_id is not None:
            for c in cats:
                if c["id"] == int(item_category_id):
                    return c
            raise RuntimeError(
                f"Item Category #{item_category_id} not found in ERP — "
                f"pick a valid category id."
            )
        log.info(f"  Auto-picking most-populated item category: {cats[0]}")
        return cats[0]

    def _resolve_tax_rates(self) -> Dict[str, List[float]]:
        """Return ``{hsn: [tax_rate, ...]}`` flattened from the Tax Rate screen.

        Rates live per-header: ``get_entry("Tax Rate", id)`` returns a flat
        ``children[0].details[]`` list of rows with ``hsn_sac_number`` +
        ``tax_rate``. All headers are read (threaded) and merged by HSN so an
        HSN with multiple rate rows yields multiple candidates. Cached per
        PurchaseChain instance.
        """
        if self._tax_rates is not None:
            return self._tax_rates
        self._tax_rates = {}
        try:
            resp = self.client.list_entries("Tax Rate", page_size=500)
        except Exception as e:
            log.warning(f"  Could not list Tax Rate entries: {e}")
            return self._tax_rates

        headers = (resp or {}).get("screenmatlistingdata_set") or (resp or {}).get("results") or []

        def _fetch(header):
            out: Dict[str, List[float]] = {}
            hid = header.get("id")
            if hid is None:
                return out
            try:
                det = self.client.get_entry("Tax Rate", hid)
            except Exception:
                return out
            if not det:
                return out
            for child in (det.get("children") or []):
                for row in (child.get("details") or []):
                    hsn = row.get("hsn_sac_number")
                    rate = row.get("tax_rate")
                    if hsn is None or rate is None:
                        continue
                    try:
                        out.setdefault(str(hsn).strip(), []).append(float(rate))
                    except (TypeError, ValueError):
                        continue
            return out

        if headers:
            with ThreadPoolExecutor(max_workers=8) as ex:
                for hsn_map in ex.map(_fetch, headers):
                    for hsn, rates in hsn_map.items():
                        self._tax_rates.setdefault(hsn, [])
                        self._tax_rates[hsn].extend(rates)
        log.info(
            f"  Resolved tax rates for {len(self._tax_rates)} HSN(s) "
            f"from {len(headers)} Tax Rate header(s)"
        )
        return self._tax_rates

    def run(
        self,
        supplier_ref_id: int = None,
        num_items: int = 1,
        item_ref_id: int = None,
        item_ref_ids: Optional[List[int]] = None,
        item_category_id: int = None,
        require_tax_rate: bool = True,
        hsn_sac_no: int = None,
        po_overrides: dict = None,
        gp_overrides: dict = None,
        grn_overrides: dict = None,
        qc_overrides: dict = None,
        pb_overrides: dict = None,
        so_overrides: dict = None,
        ctx: Optional[ChainContext] = None,
        documents: Optional[List[str]] = None,
        multi_gate_pass: bool = False,
        gp_count: int = 2,
        customer_ref_id: int = None,
        qc_discount: bool = True,
        is_rate_weight_deduction: bool = False,
    ) -> dict:
        """Execute one full PO -> GP -> GRN -> QC chain.

        If *ctx* is not given, the context is discovered automatically from
        the ERP API (tenant-safe). Explicit arguments take precedence over
        the discovered context so existing callers are not broken.

        ``item_category_id`` restricts PO items to one Item Category (the ERP
        PO Item dropdown is category-scoped). When None, the most-populated
        category is auto-picked.

        ``require_tax_rate`` gates the PO item set: True keeps only items whose
        HSN has at least one tax rate in the Tax Rate screen (each line gets a
        random one of its rates); False keeps every item — those without a rate
        are sent with ``tax_rate=0.0``.

        ``multi_gate_pass`` + ``gp_count`` enable partial fulfillment: the PO is
        created once with each item's full quantity, then the quantity is split
        evenly across ``gp_count`` gate passes. Each GP gets its own GRN, QC and
        Purchase Booking (per-GP PB mirrors the per-GP QC).

        Returns:
            dict with keys ``po``, ``gp``, ``grn``, ``qc``, ``pb`` (single-flow
            last entries) plus ``gps``/``grns``/``qcs``/``pbs`` lists.
        """
        # Resolve context — discover once per PurchaseChain instance
        if ctx is None:
            ctx = self.get_context()

        # Which documents to create — default to full chain
        docs = set(d.upper() for d in documents) if documents else {"PO", "GP", "GRN", "QC"}

        if multi_gate_pass:
            if "PO" not in docs:
                raise RuntimeError(
                    "Multi Gate Pass requires a Purchase Order — "
                    "use the PO → GP → GRN → QC flow."
                )

        # Explicit args override discovered values
        eff_supplier  = supplier_ref_id if supplier_ref_id is not None else ctx.supplier_ref_id
        eff_item      = item_ref_id     if item_ref_id     is not None else ctx.item_ref_id
        eff_hsn       = hsn_sac_no      if hsn_sac_no      is not None else ctx.hsn_sac_no

        # Resolve supplier-specific addresses/terms — the generic ctx dropdown
        # values can belong to a different supplier and cause an HTTP 500 on PO
        # create. Raises a clear error if the chosen supplier has no address.
        supplier_det = None
        if "PO" in docs:
            supplier_det = self._resolve_supplier_details(eff_supplier)

        # Resolve item category — the ERP PO Item dropdown is scoped to one
        # category, so PO items must belong to it. Auto-pick the most-populated
        # category when the caller did not choose one.
        category = self._resolve_item_category(item_category_id)
        if category is None:
            raise RuntimeError(
                "No Item Categories found in ERP — cannot pick PO items. "
                "Add an Item Category and some Items first."
            )
        cat_id = int(category["id"])
        log.info(
            f"  Using Item Category #{cat_id} ({category['name']}) — "
            f"po_item_type={cat_id} ({'requested' if item_category_id is not None else 'auto-picked'})"
        )

        # Resolve per-item data (real HSN / UOM / conversion) for the chosen
        # items so PO lines are valid for ANY tenant. Items without HSN/UOM data
        # raise a clear error instead of silently reusing tenant scalars. Items
        # outside the chosen category are rejected.
        if item_ref_ids:
            base_ids = list(item_ref_ids)
        else:
            base_ids = [iid for iid, cid in self._item_category_map.items() if cid == cat_id]
            if not base_ids:
                raise RuntimeError(
                    f"Item Category #{cat_id} ({category['name']}) has no items in ERP "
                    f"— cannot pick PO items. Pick a category that has items."
                )
            if eff_item in base_ids:
                base_ids = [eff_item]
        num = max(1, num_items)

        # HSN -> available tax rates. When Tax Rate is ON, items whose HSN has
        # no rate are skipped (each PO line picks a random one of its rates);
        # when OFF, every item is kept and rate-less ones get 0.0.
        tax_rates = self._resolve_tax_rates()
        item_data = []
        skipped_no_rate = []
        skipped_no_cqp = []
        idx = 0
        guard = 0
        max_iter = max(num * 4, len(base_ids) * 4, 16)
        while len(item_data) < num and guard < max_iter:
            iid = base_ids[idx % len(base_ids)]
            idx += 1
            guard += 1
            det = self._resolve_item_detail(iid)
            if det is None or not det.get("hsn_sac_no") or not det.get("alternate_uom") or not det.get("base_uom"):
                raise RuntimeError(
                    f"Item #{iid} is missing HSN/UOM data in Item Master — cannot create PO. "
                    f"Pick an item with HSN, primary UOM and base UOM configured."
                )
            det_cat = det.get("item_category")
            if det_cat is not None and det_cat != cat_id:
                raise RuntimeError(
                    f"Item #{iid} belongs to category #{det_cat}, not #{cat_id} "
                    f"({category['name']}) — pick items within the selected category."
                )
            hsn = str(det.get("hsn_sac_no") or "").strip()
            rates = tax_rates.get(hsn, [])
            if require_tax_rate and not rates:
                skipped_no_rate.append(iid)
                continue
            # The QC step 500s on items without a Commodity Quality Parameter
            # entry (item_quality_parameter_ref_id=null). Skip those items so we
            # never POST a QC payload guaranteed to fail server-side.
            if "QC" in docs and not self._resolve_cqp_params(iid):
                skipped_no_cqp.append(iid)
                continue
            det["tax_rate"] = float(random.choice(rates)) if rates else 0.0
            item_data.append(det)
        if skipped_no_rate:
            log.info(
                f"  Tax Rate ON — skipped {len(skipped_no_rate)} item(s) with no "
                f"tax rate: {sorted(set(skipped_no_rate))}"
            )
        if skipped_no_cqp:
            log.info(
                f"  QC in flow — skipped {len(skipped_no_cqp)} item(s) with no CQP "
                f"entry: {sorted(set(skipped_no_cqp))}"
            )
        if not item_data:
            reasons = []
            if require_tax_rate and skipped_no_rate:
                reasons.append("no tax rate")
            if "QC" in docs and skipped_no_cqp:
                reasons.append("no CQP (Commodity Quality Parameter) entry")
            raise RuntimeError(
                f"No usable items in Item Category #{cat_id} ({category['name']}) — "
                f"{'; '.join(reasons) if reasons else 'category empty'}. "
                f"Pick a category with items that have a tax rate"
                + (" and a CQP entry configured" if "QC" in docs else "")
                + "."
            )
        items = _generate_chain_items(num_items=len(item_data), item_data=item_data)

        po_id = po_ref = po_data = po_payload = po_entry = None
        gp_id = gp_ref = gp_data = gp_payload = None
        grn_id = grn_ref = grn_data = grn_payload = None
        qc_id = qc_ref = qc_data = qc_payload = None
        pb_id = pb_ref = pb_data = pb_payload = None
        so_id = so_ref = so_data = so_payload = None

        # Sales Order header inputs — resolved once per chain (per-GP lines are
        # built from each GP's own QC, but the customer/type/terms are shared).
        so_customer = customer_ref_id if customer_ref_id is not None else (getattr(ctx, "customer_ref_id", None) if ctx else None)
        if so_customer is None:
            so_customer = self._resolve_customer_ref_id()
        so_customer_details = self._resolve_customer_details(so_customer)
        so_type_id = self._resolve_so_type_id()
        so_supply_id = self._resolve_supply_type_id()

        # ---------------------------------------------------------------
        # 1. Purchase Order
        # ---------------------------------------------------------------
        if "PO" in docs:
            po_overrides = dict(po_overrides or {})
            po_defaults = self._sniff_po_defaults()
            po_payload = self._build_po_payload(
                eff_supplier, items, po_overrides, ctx=ctx,
                supplier_det=supplier_det, po_defaults=po_defaults,
                item_category_id=cat_id,
            )
            po_data = self.po_api.create_po(po_payload)
            po_id = po_data.get("id") or po_data.get("entry_id") if po_data else None
            if not po_data or not po_id:
                raise RuntimeError(
                    f"PO creation failed ({self._err_detail(self.po_api, po_payload)})"
                )
            po_ref = po_data.get("transaction_ref_no", str(po_id))
            log.info(f"  PO created: ID={po_id}, ref={po_ref}")

            po_entry = self.po_api.get_po(po_id)
            if po_entry:
                po_items_resp = po_entry.get("purchasing_order_items_details") or []
                sent_items = po_payload.get("purchasing_order_items_details") or []
                rate_ok = True
                for ji, sent in enumerate(sent_items):
                    got = po_items_resp[ji] if ji < len(po_items_resp) else {}
                    sr = float(sent.get("rate", 0) or 0)
                    gr = float(got.get("rate", 0) or 0)
                    if abs(sr - gr) > 0.01:
                        log.warning(f"  PO rate mismatch item[{ji}]: sent={sr}, backend={gr}")
                        rate_ok = False
                    else:
                        log.info(f"  PO rate OK item[{ji}]: rate={gr}")
                if rate_ok and po_items_resp:
                    for ji, item in enumerate(items):
                        if ji < len(po_items_resp):
                            confirmed = float(po_items_resp[ji].get("rate", 0) or 0)
                            if confirmed > 0:
                                items[ji]["rate"] = confirmed
            else:
                log.warning(f"  Could not fetch PO #{po_id} back — using sent rates")

            if self.delay:
                time.sleep(self.delay)

        # ---------------------------------------------------------------
        # 2. Gate Pass + 3. GRN + 4. QC
        #    (one delivery per plan row; multi-gate-pass splits and gives
        #    each GP→GRN pair its own QC)
        # ---------------------------------------------------------------
        delivery_plans = _split_items_across_gps(items, gp_count) if multi_gate_pass else [items]
        gps = []
        grns = []
        qcs = []
        pbs = []
        sos = []
        po_quantity_by_item = {it["item_ref_id"]: it["quantity"] for it in items}
        received_so_far: dict = {}
        for gi, gp_items in enumerate(delivery_plans, start=1):
            if "GP" in docs:
                gp_payload = self._build_gp_payload(
                    eff_supplier, gp_items, gp_overrides, ctx=ctx,
                    po_id=po_id, item_category_id=cat_id,
                )
                gp_data = self.gp_api.create_gp(gp_payload)
                gp_id = gp_data.get("id") or gp_data.get("entry_id") if gp_data else None
                if not gp_data or not gp_id:
                    raise RuntimeError(
                        f"GP {gi} creation failed (HTTP {self.gp_api._last_status}); "
                        f"response: {gp_data}"
                    )
                gp_ref = gp_data.get("transaction_ref_no", str(gp_id))
                gps.append({"id": gp_id, "ref": gp_ref, "data": gp_data, "payload": gp_payload})
                log.info(f"  GP {gi}/{len(delivery_plans)} created: ID={gp_id}, ref={gp_ref}")
                if self.delay:
                    time.sleep(self.delay)

            if "GRN" in docs:
                # po_quantity = full PO line qty (constant); po_balance_quantity =
                # running balance minus quantities already received in earlier GRNs.
                balance_by_item = {
                    it["item_ref_id"]: po_quantity_by_item.get(it["item_ref_id"], it["quantity"])
                                    - received_so_far.get(it["item_ref_id"], 0.0)
                    for it in gp_items
                }
                grn_payload = self._build_grn_payload(
                    eff_supplier, po_id, gp_id, gp_items, grn_overrides, ctx=ctx,
                    po_quantity_by_item=po_quantity_by_item,
                    balance_by_item=balance_by_item,
                )
                grn_data = self.grn_api.create_grn(grn_payload)
                grn_id = grn_data.get("id") or grn_data.get("entry_id") if grn_data else None
                if not grn_data or not grn_id:
                    raise RuntimeError(
                        f"GRN {gi} creation failed (HTTP {self.grn_api._last_status}); "
                        f"response: {grn_data}"
                    )
                grn_ref = grn_data.get("transaction_ref_no", str(grn_id))
                grns.append({"id": grn_id, "ref": grn_ref, "data": grn_data, "payload": grn_payload})
                log.info(f"  GRN {gi}/{len(delivery_plans)} created: ID={grn_id}, ref={grn_ref}")
                for it in gp_items:
                    received_so_far[it["item_ref_id"]] = (
                        received_so_far.get(it["item_ref_id"], 0.0) + it["quantity"]
                    )
                if self.delay:
                    time.sleep(self.delay)

            if "QC" in docs:
                cqp_by_item = {it["item_ref_id"]: self._resolve_cqp_params(it["item_ref_id"]) for it in gp_items}
                qc_overrides = dict(qc_overrides or {})
                if item_category_id is not None:
                    qc_overrides.setdefault("item_type_ref_id", item_category_id)
                qc_payload = self._build_qc_payload(
                    eff_supplier, po_id, gp_id, grn_id, gp_items, qc_overrides, ctx=ctx,
                    cqp_by_item=cqp_by_item,
                    bags_type_id=self._resolve_bags_type_id(),
                    qc_discount=qc_discount,
                    is_rate_weight_deduction=is_rate_weight_deduction,
                )
                qc_data = self.qc_api.create_qc(qc_payload)
                qc_id = qc_data.get("id") or qc_data.get("entry_id") if qc_data else None
                if not qc_data or not qc_id:
                    raise RuntimeError(
                        f"QC {gi} creation failed ({self._err_detail(self.qc_api, qc_payload)})"
                    )
                qc_ref = qc_data.get("transaction_ref_no", str(qc_id))
                qcs.append({"id": qc_id, "ref": qc_ref, "data": qc_data, "payload": qc_payload})
                log.info(f"  QC {gi}/{len(delivery_plans)} created: ID={qc_id}, ref={qc_ref}")
                if self.delay:
                    time.sleep(self.delay)

            if "SO" in docs:
                so_qc_items = (qc_payload or {}).get("qc_details") or []
                so_payload = self._build_so_payload(
                    so_customer,
                    qc_items=so_qc_items,
                    overrides=so_overrides,
                    ctx=ctx,
                    so_type_ref_id=so_type_id,
                    supply_type_ref_id=so_supply_id,
                    customer_details=so_customer_details,
                )
                log.info(f"  SO {gi}/{len(delivery_plans)} payload (first 800 chars): {json.dumps(so_payload, default=str)[:800]}")
                so_data = self.so_api.create_so(so_payload)
                so_id = so_data.get("id") or so_data.get("entry_id") if so_data else None
                if not so_data or not so_id:
                    _so_resp = self.so_api._last_response
                    _so_body = _so_resp.text[:400] if _so_resp is not None else "no response"
                    _sent = json.dumps(so_payload, default=str)[:600]
                    raise RuntimeError(
                        f"SO {gi} creation failed (HTTP {self.so_api._last_status}); "
                        f"body: {_so_body} | sent: {_sent}"
                    )
                so_ref = so_data.get("transaction_ref_no", str(so_id))
                sos.append({"id": so_id, "ref": so_ref, "data": so_data, "payload": so_payload})
                log.info(f"  SO {gi}/{len(delivery_plans)} created: ID={so_id}, ref={so_ref}")
                if self.delay:
                    time.sleep(self.delay)

            if "PB" in docs:
                pb_qc_items = (qc_payload or {}).get("qc_details") or []
                pb_payload = self._build_pb_payload(
                    eff_supplier, qc_id, grn_id, po_id, gp_items, pb_overrides, ctx=ctx,
                    qc_items=pb_qc_items,
                )
                log.info(f"  PB {gi}/{len(delivery_plans)} payload (first 800 chars): {json.dumps(pb_payload, default=str)[:800]}")
                pb_data = self.pb_api.create_pb(pb_payload)
                pb_id = pb_data.get("id") or pb_data.get("entry_id") if pb_data else None
                if not pb_data or not pb_id:
                    _pb_resp = self.pb_api._last_response
                    _pb_body = _pb_resp.text[:400] if _pb_resp is not None else "no response"
                    _sent = json.dumps(pb_payload, default=str)[:600]
                    raise RuntimeError(
                        f"PB {gi} creation failed (HTTP {self.pb_api._last_status}); "
                        f"body: {_pb_body} | sent: {_sent}"
                    )
                pb_ref = pb_data.get("transaction_ref_no", str(pb_id))
                pbs.append({"id": pb_id, "ref": pb_ref, "data": pb_data, "payload": pb_payload})
                log.info(f"  PB {gi}/{len(delivery_plans)} created: ID={pb_id}, ref={pb_ref}")
                if self.delay:
                    time.sleep(self.delay)

        last_gp = gps[-1] if gps else None
        last_grn = grns[-1] if grns else None
        last_qc = qcs[-1] if qcs else None
        last_pb = pbs[-1] if pbs else None
        last_so = sos[-1] if sos else None
        result = {
            "ctx": ctx,
            "po": {"id": po_id, "ref": po_ref, "data": po_data, "payload": po_payload,
                   "fetched": po_entry} if po_id else None,
            "gp": last_gp,
            "grn": last_grn,
            "gps": gps,
            "grns": grns,
            "qc": last_qc,
            "qcs": qcs,
            "pb": last_pb,
            "pbs": pbs,
            "so": last_so,
            "sos": sos,
        }
        self.results.append(result)
        return result

    def run_multiple(
        self,
        count: int,
        supplier_ref_id: int = 1,
        **overrides,
    ) -> List[dict]:
        """Execute *count* chains sequentially."""
        chains = []
        for i in range(count):
            log.info(f"\nChain [{i + 1}/{count}] - supplier={supplier_ref_id}")
            result = self.run(supplier_ref_id=supplier_ref_id, **overrides)
            chains.append(result)
        return chains

    # ------------------------------------------------------------------
    # Payload builders
    # ------------------------------------------------------------------
    @staticmethod
    def _build_po_payload(
        supplier_ref_id: int,
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
        supplier_det: dict = None,
        po_defaults: dict = None,
        item_category_id: int = None,
    ) -> dict:
        """Build a PO payload aligned to the stored-record shape.

        Ground truth (tenant 686, GET /procure_to_pay/purchase_order/3242/):
          - supplier_payment_terms / supplier_delivery_terms are TOP-LEVEL
          - supplier_details holds ONLY supplier_ship_from / supplier_bill_from
          - no packing_forwarding_ref_id
          - po_type / txn_currency are per-supplier; tax_registration_status = "Registered"
        """
        from pages.private_b2b.modules.purchase_order.data.purchase_order_data import build_po_payload
        po_items = _po_items_from(items)
        overrides = dict(overrides or {})
        supplier_det = supplier_det or {}
        po_defaults = po_defaults or {}

        # Resolve per-supplier PO header values. Fallback chain:
        #   supplier_det -> sniffed po_defaults -> ctx -> legacy default.
        def _pick(det_key, po_key, ctx_key, fb):
            v = supplier_det.get(det_key)
            if v in (None, ""):
                v = po_defaults.get(po_key)
            if v in (None, ""):
                v = getattr(ctx, ctx_key, None) if ctx else None
            if v in (None, ""):
                v = fb
            return v

        po_type       = _pick("po_type",       "po_type",       "po_type",       25)
        txn_currency  = _pick("txn_currency",  "txn_currency",  "txn_currency",  1)
        base_currency = _pick(None, "base_currency", "base_currency", 1)
        payment_terms = _pick("payment_terms", None, "payment_terms", None)
        delivery_terms = _pick("delivery_terms", None, "delivery_terms", None)
        ship_from     = _pick("ship_from",     None, "supplier_ship_from", None)
        bill_from     = _pick("bill_from",     None, "supplier_bill_from", None)
        tax_reg = supplier_det.get("tax_registration_status") or "Registered"

        # supplier_details carries ONLY ship_from / bill_from (stored shape).
        supplier_details = {
            "supplier_ship_from": ship_from,
            "supplier_bill_from": bill_from,
        }
        # Merge caller-supplied nested overrides per-key (no duplicate kwarg).
        user_sd = overrides.pop("supplier_details", None) or {}
        if isinstance(user_sd, dict):
            for k, v in user_sd.items():
                if v is not None:
                    supplier_details[k] = v

        kwargs = dict(
            supplier_ref_id=supplier_ref_id,
            items=po_items,
            # po_item_type holds the selected Item Category id (stored shape).
            # Fall back to sniffed/legacy only when no category was resolved.
            po_item_type=overrides.pop("po_item_type", item_category_id or _pick(None, "po_item_type", "item_type_ref_id", 113)),
            po_type=overrides.pop("po_type", po_type),
            txn_currency=overrides.pop("txn_currency", txn_currency),
            base_currency=overrides.pop("base_currency", base_currency),
            parameter1=overrides.pop("parameter1", _pick(None, "parameter1", "parameter1", 1)),
            parameter2=overrides.pop("parameter2", _pick(None, "parameter2", "parameter2", 1)),
            parameter5=overrides.pop("parameter5", _pick(None, "parameter5", "parameter5", 1)),
            parameter6=overrides.pop("parameter6", _pick(None, "parameter6", "parameter6", 1)),
            supplier_details=supplier_details,
            supplier_payment_terms=overrides.pop("supplier_payment_terms", payment_terms),
            supplier_delivery_terms=overrides.pop("supplier_delivery_terms", delivery_terms),
            tax_registration_status=overrides.pop("tax_registration_status", tax_reg),
            item_category=overrides.pop("item_category", item_category_id),
        )
        payload = build_po_payload(**kwargs)
        # Apply any remaining caller overrides directly to the final dict.
        payload.update(overrides)
        return payload

    @staticmethod
    def _build_gp_payload(
        supplier_ref_id: int,
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
        po_id: int = None,
        item_category_id: int = None,
    ) -> dict:
        """Build a GP payload aligned to the stored-record shape.

        Ground truth (tenant 686, GP 1526):
          - po_ref_id_id links the PO created in the same chain (omitted in the
            standalone GP -> GRN -> QC -> PB flow).
          - item_type_ref_id holds the selected Item Category id (like po_item_type),
            NOT the Farm/Non-Farm 113/114 value.
          - driver / vehicle / transporter live under additional_details.
        """
        from pages.private_b2b.modules.gate_pass.data.gate_pass_data import build_gp_payload
        gp_items = _gp_items_from(items)
        overrides = dict(overrides or {})

        def _pick(key, ctx_key, fb):
            v = overrides.pop(key, None)
            if v is None:
                v = getattr(ctx, ctx_key, None) if ctx else None
            if v is None:
                v = fb
            return v

        kwargs = dict(
            supplier_ref_id=supplier_ref_id,
            items=gp_items,
            # item_type_ref_id = selected Item Category id first (stored shape).
            # Fall back to ctx/legacy only when no category was resolved.
            item_type_ref_id=overrides.pop("item_type_ref_id", item_category_id or _pick(None, "item_type_ref_id", 113)),
            delivery_type=_pick("delivery_type", "delivery_type", 29),
            parameter1=_pick("parameter1", "parameter1", 1),
            parameter2=_pick("parameter2", "parameter2", 1),
            parameter5=_pick("parameter5", "parameter5", 1),
            parameter6=_pick("parameter6", "parameter6", 1),
            grn_check=overrides.pop("grn_check", True),
            qc_check=overrides.pop("qc_check", True),
        )
        if po_id is not None:
            kwargs["po_ref_id_id"] = overrides.pop("po_ref_id_id", po_id)
        return build_gp_payload(**kwargs)

    @staticmethod
    def _build_grn_payload(
        supplier_ref_id: int,
        po_id: int,
        gp_id: int,
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
        po_quantity_by_item: Optional[dict] = None,
        balance_by_item: Optional[dict] = None,
    ) -> dict:
        from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import build_grn_payload
        grn_items = _grn_items_from(items, po_quantity_by_item, balance_by_item)
        overrides = overrides or {}
        if ctx:
            return build_grn_payload(
                supplier_ref_id=supplier_ref_id,
                gate_pass_ref_id_id=gp_id,
                po_ref_id_id=po_id,
                items=grn_items,
                parameter1=ctx.parameter1,
                parameter2=ctx.parameter2,
                parameter5=ctx.parameter5,
                parameter6=ctx.parameter6,
                additional_details={},
                **overrides,
            )
        import random
        from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
            DIVISION_IDS, DEPARTMENT_IDS, LOCATION_IDS, TYPE_OF_SALE_IDS,
        )
        return build_grn_payload(
            supplier_ref_id=supplier_ref_id,
            gate_pass_ref_id_id=gp_id,
            po_ref_id_id=po_id,
            items=grn_items,
            parameter1=random.choice(DIVISION_IDS),
            parameter2=random.choice(DEPARTMENT_IDS),
            parameter5=random.choice(TYPE_OF_SALE_IDS),
            parameter6=random.choice(LOCATION_IDS),
            additional_details={},
            **overrides,
        )

    @staticmethod
    def _build_qc_payload(
        supplier_ref_id: int,
        po_id: int,
        gp_id: int,
        grn_id: int,
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
        cqp_by_item: Optional[dict] = None,
        bags_type_id: int = 1,
        qc_discount: bool = True,
        is_rate_weight_deduction: bool = False,
    ) -> dict:
        from pages.private_b2b.modules.quality_check.data.quality_check_data import build_qc_payload
        qc_items = _qc_items_from(items, ctx=ctx, cqp_by_item=cqp_by_item or {}, bags_type_id=bags_type_id, qc_discount=qc_discount, is_rate_weight_deduction=is_rate_weight_deduction)
        overrides = overrides or {}
        total_txn = round(sum(float(l.get("txn_currency_amount") or 0.0) for l in qc_items), 6)
        header_extra = {"total_txn_currency_amount": total_txn}
        if ctx:
            overrides = dict(overrides or {})
            item_type_ref_id = overrides.pop("item_type_ref_id", None) or ctx.item_type_ref_id
            return build_qc_payload(
                supplier_ref_id=supplier_ref_id,
                gate_pass_ref_id_id=gp_id,
                grn_ref_id_id=grn_id,
                po_ref_id_id=po_id,
                items=qc_items,
                item_type_ref_id=item_type_ref_id,
                base_currency=ctx.base_currency,
                txn_currency=ctx.txn_currency,
                parameter1=ctx.parameter1,
                parameter2=ctx.parameter2,
                parameter5=ctx.parameter5,
                parameter6=ctx.parameter6,
                **header_extra,
                **overrides,
            )
        return build_qc_payload(
            supplier_ref_id=supplier_ref_id,
            gate_pass_ref_id_id=gp_id,
            grn_ref_id_id=grn_id,
            po_ref_id_id=po_id,
            items=qc_items,
            **header_extra,
            **overrides,
        )

    @staticmethod
    def _build_pb_payload(
        supplier_ref_id: int,
        qc_id: Optional[int],
        grn_id: Optional[int],
        po_id: Optional[int],
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
        qc_items: Optional[List[dict]] = None,
    ) -> dict:
        from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import build_pb_payload
        if qc_items:
            pb_items = _pb_items_from_qc(qc_items, items=items, ctx=ctx)
        else:
            pb_items = _pb_items_from(items, ctx=ctx)
        overrides = overrides or {}
        supplier_ref_type = ctx.supplier_ref_type if ctx else "Supplier"
        header_extra = {
            "round_off_credit_amount": None,
            "round_off_debit_amount": None,
        }
        if ctx:
            return build_pb_payload(
                supplier_ref_id=supplier_ref_id,
                supplier_ref_type=supplier_ref_type,
                parameter1=ctx.parameter1,
                parameter2=ctx.parameter2,
                parameter5=ctx.parameter5,
                parameter6=ctx.parameter6,
                base_currency=ctx.base_currency,
                txn_currency=ctx.txn_currency,
                supplier_payment_terms_ref_id=ctx.pb_payment_terms,
                items=pb_items,
                qc_ref_id=qc_id,
                grn_ref_id=grn_id,
                po_ref_id=po_id,
                **header_extra,
                **overrides,
            )
        return build_pb_payload(
            supplier_ref_id=supplier_ref_id,
            supplier_ref_type=supplier_ref_type,
            items=pb_items,
            qc_ref_id=qc_id,
            grn_ref_id=grn_id,
            po_ref_id=po_id,
            **header_extra,
            **overrides,
        )

    def _build_so_payload(
        self,
        customer_ref_id: int,
        qc_items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
        so_type_ref_id: int = None,
        supply_type_ref_id: int = None,
        customer_details: Optional[dict] = None,
    ) -> dict:
        from pages.private_b2b.modules.sales_order.data.sales_order_data import build_so_payload
        tax_rates = self._resolve_tax_rates()
        so_items = _so_items_from_qc(qc_items, ctx=ctx, tax_rates=tax_rates)
        overrides = overrides or {}
        kwargs = {
            "customer_ref_id": customer_ref_id,
            "items": so_items,
            "so_type_ref_id": so_type_ref_id,
            "supply_type_ref_id": supply_type_ref_id,
            "customer_details": customer_details,
        }
        if ctx:
            kwargs.update({
                "txn_currency": ctx.txn_currency,
                "base_currency": ctx.base_currency,
                "conversion_rate": getattr(ctx, "conversion_rate", 1.0),
                "parameter1": ctx.parameter1,
                "parameter2": ctx.parameter2,
                "parameter5": ctx.parameter5,
                "parameter6": ctx.parameter6,
            })
        kwargs.update(overrides)
        return build_so_payload(**kwargs)


# ---------------------------------------------------------------------------
# Detail display — prints every field sent to the ERP
# ---------------------------------------------------------------------------

def _val(v):
    """Return a display string for a value, handling None."""
    if v is None or v == "":
        return "-"
    return str(v)


def _adj(s, w):
    """Left-justify or pad a string to width w."""
    s = str(s)
    return s.ljust(w)[:w]


def _name(lookup, key):
    """Resolve an ID to 'name (ID)' or just 'ID'."""
    if key is None or key == "":
        return "-"
    k = int(key) if not isinstance(key, int) else key
    name = lookup.get(k)
    if name:
        return f"{name} ({k})"
    return str(k)


def print_chain_details(results):
    """Print a human-readable block for each doc showing what was sent."""
    for i, r in enumerate(results):
        po = r["po"]
        gp = r["gp"]
        grn = r["grn"]
        qc = r.get("qc") or {}

        print(f"\n{'=' * 72}")
        print(f"CHAIN [{i + 1}]  PO {po['id']}  ->  GP {gp['id']}  ->  "
              f"GRN {grn['id']}  ->  QC {qc.get('id', '?')}")
        print(f"{'=' * 72}")

        # -- PO -------------------------------------------------------------------
        pp = po["payload"]
        print(f"\n-- PURCHASE ORDER  #{po['id']}  ({po['ref']})")
        print(f"   Supplier:      {_name(SUPPLIER_NAMES, pp.get('supplier_ref_id'))}")
        print(f"   PO Item Type:  {_name(PO_ITEM_TYPE_NAMES, pp.get('po_item_type'))}")
        print(f"   PO Type:       {_name(PO_TYPE_NAMES, pp.get('po_type'))}")
        print(f"   Currency:      {_name(PO_CURRENCY_NAMES, pp.get('txn_currency'))}")
        print(f"   Base Currency: {_name(PO_CURRENCY_NAMES, pp.get('base_currency'))}")
        print(f"   Conv Rate:     {_val(pp.get('conversion_rate'))}")
        print(f"   Trans Date:    {_val(pp.get('transaction_date'))}")
        sd = pp.get("supplier_details") or {}
        print(f"   Payment Terms: {_name(PAYMENT_TERMS_NAMES, pp.get('supplier_payment_terms'))}")
        print(f"   Deliv. Terms:  {_name(DELIVERY_TERMS_NAMES, pp.get('supplier_delivery_terms'))}")
        print(f"   Pack & Forw:   {_val(pp.get('packing_forwarding_ref_id'))}")
        print(f"   Ship From:     {_val(sd.get('supplier_ship_from'))}")
        print(f"   Bill From:     {_val(sd.get('supplier_bill_from'))}")

        po_items = pp.get("purchasing_order_items_details") or []
        po_fetched = po.get("fetched") or {}
        po_fetched_items = po_fetched.get("purchasing_order_items_details") or []
        if po_items:
            print(f"   Items ({len(po_items)}):")
            for ji, item in enumerate(po_items):
                iname = _name(PO_ITEM_NAMES, item.get("item_ref_id"))
                hsn = _val(item.get("hsn_sac_no"))
                uom = _name(PO_UOM_NAMES, item.get("uom"))
                qty = _val(item.get("quantity"))
                rate = _val(item.get("rate"))
                edd = _val(item.get("expected_delivery_date"))
                # Backend confirmation
                fi = po_fetched_items[ji] if ji < len(po_fetched_items) else {}
                bqty = _val(fi.get("quantity"))
                brate = _val(fi.get("rate"))
                btotal = _val(fi.get("total_amount"))
                qty_match = "OK" if abs(float(fi.get("quantity", 0) or 0) - float(item.get("quantity", 0) or 0)) < 0.01 else "MISMATCH"
                rate_match = "OK" if abs(float(fi.get("rate", 0) or 0) - float(item.get("rate", 0) or 0)) < 0.01 else "MISMATCH"
                print(f"     [{ji + 1}] {_adj(iname, 34)} HSN:{hsn}  UOM:{uom}  "
                      f"Qty:{_adj(qty, 8)} Rate:{_adj(rate, 8)} Del:{edd}")
                print(f"           Backend:  qty={_adj(bqty, 6)} rate={_adj(brate, 6)} total={btotal}  "
                      f"(qty:{qty_match}, rate:{rate_match})")
        ad = pp.get("additional_details") or {}
        print(f"   Discount:      {_val(ad.get('txn_currency_discount_percent'))}% / "
              f"{_val(ad.get('txn_currency_discount_amount'))}")
        print(f"   Interest:      {_val(ad.get('txn_currency_interest_percent'))}% / "
              f"{_val(ad.get('txn_currency_interest_amount'))}")
        print(f"   Transport:     {_val(ad.get('transportation_charges'))}")
        print(f"   Remark:        {_val(ad.get('remark'))}")
        print(f"   ---")

        # -- GP -------------------------------------------------------------------
        gpp = gp["payload"]
        print(f"\n-- GATE PASS  #{gp['id']}  ({gp['ref']})")
        print(f"   Supplier:      {_name(SUPPLIER_NAMES, gpp.get('supplier_ref_id'))}")
        print(f"   Item Type:     {_name(PO_ITEM_TYPE_NAMES, gpp.get('item_type_ref_id'))}")
        print(f"   Delivery Type: {_name(DELIVERY_TYPE_NAMES, gpp.get('delivery_type'))}")
        print(f"   Vehicle No:    {_val(gpp.get('vehicle_no'))}")
        print(f"   Driver:        {_val(gpp.get('driver_name'))}")
        print(f"   Driver Contact:{_val(gpp.get('driver_contact_no'))}")
        print(f"   In Time:       {_val(gpp.get('in_time'))}")
        print(f"   Distance:      {_val(gpp.get('distance'))}")
        print(f"   Department:    {_name(DEPARTMENT_NAMES, gpp.get('parameter2'))}")
        print(f"   Location:      {_name(LOCATION_NAMES, gpp.get('parameter6'))}")
        print(f"   Division:      {_name(DIVISION_NAMES, gpp.get('parameter1'))}")
        print(f"   Type of Sale:  {_name(TYPE_OF_SALE_NAMES, gpp.get('parameter5'))}")
        print(f"   GrnCheck/QC:   {_val(gpp.get('grn_check'))} / {_val(gpp.get('qc_check'))}")
        gp_items = gpp.get("gate_pass_details") or []
        if gp_items:
            print(f"   Items ({len(gp_items)}):")
            for ji, item in enumerate(gp_items):
                iname = _name(GP_ITEM_NAMES, item.get("item_ref_id"))
                bags = _val(item.get("no_of_bags"))
                qty = _val(item.get("quantity"))
                uom = _name(GRN_UOM_NAMES, item.get("base_uom"))
                hsn = _val(item.get("hsn_sac_no"))
                print(f"     [{ji + 1}] {_adj(iname, 38)} Bags:{_adj(bags, 4)} "
                      f"Qty:{_adj(qty, 8)} UOM:{uom}  HSN:{hsn}")
        print(f"   ---")

        # -- GRN ------------------------------------------------------------------
        grpp = grn["payload"]
        print(f"\n-- GOODS RECEIPT NOTE  #{grn['id']}  ({grn['ref']})")
        print(f"   Supplier:      {_name(SUPPLIER_NAMES, grpp.get('supplier_ref_id'))}")
        print(f"   PO Ref:        {_val(grpp.get('po_ref_id_id'))}")
        print(f"   GP Ref:        {_val(grpp.get('gate_pass_ref_id_id'))}")
        print(f"   Base Currency: {_name(PO_CURRENCY_NAMES, grpp.get('base_currency'))}")
        print(f"   Txn Currency:  {_name(PO_CURRENCY_NAMES, grpp.get('txn_currency'))}")
        print(f"   Conv Rate:     {_val(grpp.get('conversion_rate'))}")
        print(f"   Trans Date:    {_val(grpp.get('transaction_date'))}")
        gad = grpp.get("additional_details") or {}
        print(f"   Vehicle:       {_val(gad.get('vehicle_no'))}")
        print(f"   Transporter:   {_val(gad.get('transporter_name'))}")
        print(f"   Bill No:       {_val(gad.get('supplier_bill_no'))}")
        print(f"   E-Way Bill:    {_val(gad.get('e_way_bill_no'))}")
        print(f"   Remark:        {_val(gad.get('remark'))}")
        grn_items = grpp.get("grn_item_details") or []
        if grn_items:
            print(f"   Items ({len(grn_items)}):")
            for ji, item in enumerate(grn_items):
                iname = _name(GRN_ITEM_NAMES, item.get("item_ref_id"))
                hsn = _val(item.get("hsn_sac_no"))
                uom = _name(GRN_UOM_NAMES, item.get("uom"))
                rcv = _val(item.get("received_qty"))
                acc = _val(item.get("accepted_qty"))
                rej = _val(item.get("rejected_qty"))
                rate = _val(item.get("rate"))
                bags = _val(item.get("no_of_bags"))
                poq = _val(item.get("po_quantity"))
                gpq = _val(item.get("gate_pass_quantity"))
                print(f"     [{ji + 1}] {_adj(iname, 34)} HSN:{hsn}  UOM:{uom}  "
                      f"Recv:{_adj(rcv, 6)} Acc:{_adj(acc, 6)} Rej:{_adj(rej, 6)} "
                      f"Rate:{_adj(rate, 6)} Bags:{bags}")
                print(f"             PO Qty:{_adj(poq, 5)}  GP Qty:{_adj(gpq, 5)}")
        print(f"   ---")

        # -- QC -------------------------------------------------------------------
        if qc:
            qpp = qc["payload"]
            qcad = qpp.get("qc_additional_details") or {}
            print(f"\n-- QUALITY CHECK  #{qc['id']}  ({qc['ref']})")
            print(f"   Supplier:      {_name(SUPPLIER_NAMES, qpp.get('supplier_ref_id'))}")
            print(f"   PO Ref:        {_val(qpp.get('po_ref_id_id'))}")
            print(f"   GP Ref:        {_val(qpp.get('gate_pass_ref_id_id'))}")
            print(f"   GRN Ref:       {_val(qpp.get('grn_ref_id_id'))}")
            print(f"   Vehicle No:    {_val(qcad.get('vehicle_number'))}")
            print(f"   Driver Name:   {_val(qcad.get('driver_name'))}")
            print(f"   Currency:      {_name(PO_CURRENCY_NAMES, qpp.get('txn_currency'))}")
            print(f"   Trans Date:    {_val(qpp.get('transaction_date'))}")
            qc_items = qpp.get("qc_details") or []
            if qc_items:
                print(f"   Items ({len(qc_items)}):")
                for ji, item in enumerate(qc_items):
                    iname = _name(QC_ITEM_NAMES, item.get("item_ref_id"))
                    hsn = _val(item.get("hsn_sac_no"))
                    uom = _name(GRN_UOM_NAMES, item.get("uom"))
                    grn_qty = _val(item.get("grn_qty"))
                    acc = _val(item.get("accepted_qty"))
                    rej = _val(item.get("rejected_qty"))
                    base = _val(item.get("base_rate"))
                    net = _val(item.get("net_rate"))
                    ded_pct = _val(item.get("deduction_percent"))
                    print(f"     [{ji + 1}] {_adj(iname, 34)} HSN:{hsn}  UOM:{uom}  "
                          f"GRN Qty:{_adj(grn_qty, 6)} Acc:{_adj(acc, 6)} Rej:{_adj(rej, 6)}")
                    print(f"             Base:{_adj(base, 8)} Net:{_adj(net, 8)} Ded%:{_adj(ded_pct, 5)}")
                    details = item.get("details") or []
                    if details:
                        parts = []
                        for d in details:
                            pname = _name(QUALITY_PARAMETER_NAMES, d.get("item_quality_parameter_ref_id"))
                            pval = _val(d.get("actual_value"))
                            parts.append(f"{pname}={pval}")
                        if parts:
                            print(f"             Quality:  {',  '.join(parts)}")
        print(f"")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def setup_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create linked PO -> Gate Pass -> GRN chains",
    )
    parser.add_argument(
        "--supplier", type=int, default=1,
        help="Supplier ref ID (default 1)",
    )
    parser.add_argument(
        "--count", type=int, default=1,
        help="Number of chains to create (default 1)",
    )
    parser.add_argument(
        "--token", default="",
        help="ERP JWT token",
    )
    parser.add_argument(
        "--tenant", default="711",
        help="Tenant ID (default 711)",
    )
    parser.add_argument(
        "--delay", type=float, default=0.3,
        help="Delay in seconds between steps (default 0.3)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print payloads without creating",
    )
    parser.add_argument(
        "--item-ref-id", type=int, default=5,
        help="Item ref ID for all items (default 5)",
    )
    parser.add_argument(
        "--num-items", type=int, default=2,
        help="Items per document (default 2)",
    )
    return parser


def dry_run_dump(supplier_ref_id: int, count: int, num_items: int, item_ref_id: int):
    items = _generate_chain_items(num_items=num_items, item_ref_id=item_ref_id)
    print(f"\n{'=' * 60}")
    print(f"DRY RUN - {count} chain(s), supplier={supplier_ref_id} "
          f"({_supplier_name(supplier_ref_id)})")
    print(f"{'=' * 60}")

    for i in range(count):
        print(f"\n--- Chain [{i + 1}/{count}] ---")

        po = PurchaseChain._build_po_payload(supplier_ref_id, items)
        gp = PurchaseChain._build_gp_payload(supplier_ref_id, items)
        grn = PurchaseChain._build_grn_payload(
            supplier_ref_id, po_id="<PO_ID>", gp_id="<GP_ID>", items=items,
        )
        qc = PurchaseChain._build_qc_payload(
            supplier_ref_id, po_id="<PO_ID>", gp_id="<GP_ID>", grn_id="<GRN_ID>", items=items,
        )

        print(f"\n  PO payload:")
        print(json.dumps(po, indent=2, default=str)[:500])
        print(f"\n  GP payload:")
        print(json.dumps(gp, indent=2, default=str)[:500])
        print(f"\n  GRN payload:")
        print(json.dumps(grn, indent=2, default=str)[:500])
        print(f"\n  QC payload:")
        print(json.dumps(qc, indent=2, default=str)[:500])

    print(f"\nDry run complete. No entries created.")


def main():
    parser = setup_argparse()
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    supplier = args.supplier
    count = args.count
    sname = _supplier_name(supplier)

    if args.dry_run:
        dry_run_dump(supplier, count, args.num_items, args.item_ref_id)
        return

    chain = PurchaseChain(
        token=token,
        tenant=args.tenant,
        delay=args.delay,
    )

    # ── Pre-flight: validate and fix Accounting Definition ────────────────────
    sep = "-" * 60
    print(f"\n{sep}")
    print(f"  Pre-flight: Accounting Definition check (tenant {args.tenant})")
    print(sep)
    try:
        coa = fetch_coa(chain.client)
        accounts = resolve_accounts(coa)
        for name, aid in accounts.items():
            print(f"    {name:30s} -> id={aid}")
        tos_ids = fetch_type_of_sale_ids(chain.client)
        print(f"  Type of Sale IDs: {tos_ids}")
        existing = find_existing_pb_ad(chain.client)
        if existing:
            print(f"  Found existing AD id={existing['id']} — updating to canonical structure")
        else:
            print("  No AD found — creating new")
        payload = build_ad_payload(accounts, tos_ids)
        apply_ad(chain.client, payload, existing["id"] if existing else None, dry_run=False)
        print(f"  AD pre-flight done.\n{sep}")
    except Exception as _ad_err:
        print(f"  WARNING: AD pre-flight failed: {_ad_err}")
        print(f"  Continuing — chains may produce silent accounting errors.\n{sep}")

    print(f"\n{'=' * 60}")
    print(f"Creating {count} purchase chain(s) - supplier={supplier} ({sname})")
    print(f"{'=' * 60}")

    start = time.time()
    results = chain.run_multiple(
        count=count,
        supplier_ref_id=supplier,
        num_items=args.num_items,
        item_ref_id=args.item_ref_id,
    )
    elapsed = time.time() - start

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    for i, r in enumerate(results):
        po = r["po"]
        gp = r["gp"]
        grn = r["grn"]
        qc = r.get("qc", {})
        qc_part = f"QC {qc.get('id', '?')} ({qc.get('ref', '?')})" if qc else "QC (skipped)"
        print(f"  Chain [{i + 1}]:  PO {po['id']} ({po['ref']})  ->  "
              f"GP {gp['id']} ({gp['ref']})  ->  "
              f"GRN {grn['id']} ({grn['ref']})  ->  "
              f"{qc_part}")

    print(f"\n  Total time: {elapsed:.1f}s  ({elapsed / count:.1f}s per chain)")
    print(f"  All {count} chain(s) completed successfully.")

    print_chain_details(results)
    print()


if __name__ == "__main__":
    main()
