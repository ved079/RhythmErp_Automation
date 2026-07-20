"""
direct_pb_data.py
-----------------
Payload builders and constants for Direct PB batch creation.

Tenant: Eco Green Pvt Ltd (kedar@rhythmflows.com)
Flow:   Direct Purchase Booking — no PO / QC reference.

Field names and structure derived from a real GET response on this tenant.

Calculation rules (confirmed from real response):
  alternate_net_qty        = alternate_qty - empty_bag_weight
  txn_currency_amount_detail = rate * alternate_net_qty - labour_charges
  discount_amount          = txn_currency_amount_detail * discount_percentage / 100
  txn_currency_total_txn_amount = txn_currency_amount_detail - discount_amount
  master.txn_currency_amount       = SUM(txn_currency_total_txn_amount per line)
  master.txn_currency_total_amount = same as above (no GST in direct flow)
"""

import random
from datetime import date
from typing import List, Optional

# ── Tenant constants ──────────────────────────────────────────────────────────

SUPPLIER_REF_TYPE = "Farmer"
CURRENCY_ID = 8  # AUD on this tenant (base_currency and txn_currency)
CONVERSION_RATE = "1"

# Items active on Eco Green Pvt Ltd — mirrors ITEMS in direct_pb_playwright_page.py
ITEMS = [
    "Soybean Yellow FAQ Grade 5 KG",
    "Tur (Arhar) White FAQ Grade 5 KG",
    "Chana White FAQ Grade 10 KG",
    "Maize Yellow FAQ Grade 5 KG",
    "Soybean Red Grade A 10 KG",
    "Masoor Yellow Grade A 20 KG",
    "Chana White Grade A 25 KG",
    "Maize Green Grade B 20 KG",
    "Sesame (Til) Green Grade A 10 KG",
    "Ragi White 5 KG",
    "Chana Red Grade A 500 KG",
    "Bajra Yellow Grade A 20 KG",
    "Barley Red Grade A 30 KG",
    "Maize White Grade B 100 KG",
    "Chana Yellow Premium Grade 1000 KG (1 MT)",
    "Sesame (Til) Sona Masuri Grade B 20 KG",
    "Sunflower Ooty Super Grade 20 KG",
    "Bajra Sharbati Super Grade 75 KG",
    "Safflower Black Super Grade 20 KG",
    "Mustard Medium Milling Grade 25 KG",
]

# Suppliers on Eco Green Pvt Ltd — mirrors SUPPLIERS in direct_pb_playwright_page.py
SUPPLIERS = [
    "Omkar Agencies | 9389399233",
    "Vedant Company | 9494949494",
    "Jagdamba Krishna Oil Mills Group | 9978228598",
    "Jai Vindhya Exports & Sons | 9581809469",
    "Maa Agro Traders Group | 6915553555",
    "Supreme Godavari Oil Mills & Sons | 8761823111",
    "Venkatesh Amul Enterprises & Bros | 6997018367",
    "Falcon enterprises | 9388239912",
]


# ── Calculation helpers ───────────────────────────────────────────────────────

def compute_net_qty(alternate_qty: float, empty_bag_weight: float = 0.0) -> float:
    return round(alternate_qty - empty_bag_weight, 6)


def compute_txn_amount_detail(rate: float, alternate_net_qty: float,
                               labour_charges: float = 0.0) -> float:
    return round(rate * alternate_net_qty - labour_charges, 6)


def compute_discount_amount(txn_amount_detail: float,
                             discount_percentage: float = 0.0) -> float:
    return round(txn_amount_detail * discount_percentage / 100, 6)


def compute_line_total(txn_amount_detail: float,
                        discount_amount: float = 0.0) -> float:
    return round(txn_amount_detail - discount_amount, 6)


def compute_master_total(items: List[dict]) -> float:
    return round(sum(it.get("txn_currency_total_txn_amount", 0.0) for it in items), 6)


# ── Item builder ──────────────────────────────────────────────────────────────

def build_direct_pb_item(
    item_ref_id: int,
    hsn_sac_no: int,
    alternate_uom: int,   # item's primary UOM (item.uom)
    uom: int,             # item's base UOM (item.base_uom)
    uom_conversion: float,
    rate: float,
    no_of_bags: int = 1,
    alternate_qty: float = None,
    empty_bag_weight: float = 0.0,
    labour_charges: float = 0.0,
    discount_percentage: float = None,
    is_gst_set_off: bool = False,
    tax_rate=None,
) -> dict:
    """
    Build one line item for purchase_booking_details.

    alternate_qty defaults to no_of_bags if not supplied.
    All computed fields (alternate_net_qty, txn amounts) are calculated here
    so the payload matches what the ERP expects on POST.

    Field mapping from Item Master:
      alternate_uom = item.uom         (primary UOM, e.g. 1)
      uom           = item.base_uom    (base/weight UOM, e.g. 2)
      uom_conversion = item.base_uom_conversion
    """
    if alternate_qty is None:
        alternate_qty = float(no_of_bags)

    alternate_net_qty = compute_net_qty(alternate_qty, empty_bag_weight)
    txn_amount_detail = compute_txn_amount_detail(rate, alternate_net_qty, labour_charges)
    discount_pct = discount_percentage or 0.0
    discount_amount = compute_discount_amount(txn_amount_detail, discount_pct)
    line_total = compute_line_total(txn_amount_detail, discount_amount)

    return {
        "item_ref_id": item_ref_id,
        "hsn_sac_no": hsn_sac_no,
        "no_of_bags": no_of_bags,
        "alternate_qty": alternate_qty,
        "alternate_uom": alternate_uom,
        "uom": uom,
        "uom_conversion": uom_conversion,
        "empty_bag_weight": empty_bag_weight,
        "alternate_net_qty": alternate_net_qty,
        "rate": rate,
        "labour_charges": labour_charges,
        "discount_percentage": discount_percentage,
        "txn_currency_amount_detail": txn_amount_detail,
        "txn_currency_discount_amount_details": discount_amount,
        "txn_currency_total_txn_amount": line_total,
        "is_gst_set_off": is_gst_set_off,
        "tax_rate": tax_rate,
        "details": [
            {
                "no_of_bags_subdetails": no_of_bags,
                "quantity_sub_details": alternate_qty,
            }
        ],
    }


# ── Master payload builder ────────────────────────────────────────────────────

def build_direct_pb_payload(
    supplier_ref_id: int,
    items: List[dict],
    parameter1: int = 1,        # Division
    parameter2: int = 1,        # Department
    parameter5: int = 1,        # Location
    parameter6: int = 1,        # Type of Sale
    base_currency: int = CURRENCY_ID,
    txn_currency: int = CURRENCY_ID,
    conversion_rate: str = CONVERSION_RATE,
    supplier_payment_terms_ref_id: Optional[int] = None,
    transportation_charges: float = 0.0,
    round_off_credit_amount: float = 0.0,
    round_off_debit_amount: float = 0.0,
    remark: Optional[str] = None,
    transaction_date: Optional[str] = None,
) -> dict:
    """
    Build a complete Direct PB payload ready to POST.
    No QC / PO / GRN references — this is a standalone purchase booking.
    All FK IDs must be resolved from live ERP before calling.
    Items must be built with build_direct_pb_item().
    """
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    master_total = compute_master_total(items)

    return {
        "transaction_date": transaction_date,
        "transaction_ref_no": "",
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": SUPPLIER_REF_TYPE,
        "gst_registration_type": None,
        "supplier_payment_terms_ref_id": supplier_payment_terms_ref_id,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": 1.0,
        "is_tds_applicable": None,
        "section_ref_id": 0,
        "tds_percent_applicable": None,
        "tds_amount": 0,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "round_off_credit_amount": round_off_credit_amount,
        "round_off_debit_amount": round_off_debit_amount,
        "remark": remark,
        "posting_status": None,
        "txn_currency_amount": master_total,
        "txn_currency_total_amount": master_total,
        "purchase_booking_details": items,
        "grn_details": [],
        "other_charges": {
            "agent_ref_id": None,
            "is_rate_percentage": False,
            "agent_commision": None,
            "agent_commision_amount": None,
            "transportation_charges": transportation_charges,
        },
    }


# ── Random payload generator ──────────────────────────────────────────────────

def generate_direct_pb_payload(
    supplier_ref_id: int,
    item_ref_id: int,
    hsn_sac_no: int,
    alternate_uom: int,   # item.uom
    uom: int,             # item.base_uom
    uom_conversion: float,
    parameter1: int,
    parameter2: int,
    parameter5: int,
    parameter6: int,
    supplier_payment_terms_ref_id: Optional[int] = None,
) -> dict:
    """
    Generate one randomised Direct PB payload with a single line item.
    All FK IDs must be pre-resolved from live ERP.
    """
    no_of_bags = random.randint(1, 20)
    alternate_qty = float(no_of_bags) * random.uniform(50.0, 500.0)
    alternate_qty = round(alternate_qty, 2)
    rate = round(random.uniform(10.0, 200.0), 2)
    labour_charges = round(random.uniform(0.0, 5.0), 2)
    discount_pct = round(random.uniform(0.0, 5.0), 2)

    item = build_direct_pb_item(
        item_ref_id=item_ref_id,
        hsn_sac_no=hsn_sac_no,
        alternate_uom=alternate_uom,
        uom=uom,
        uom_conversion=uom_conversion,
        rate=rate,
        no_of_bags=no_of_bags,
        alternate_qty=alternate_qty,
        empty_bag_weight=0.0,
        labour_charges=labour_charges,
        discount_percentage=discount_pct,
    )

    return build_direct_pb_payload(
        supplier_ref_id=supplier_ref_id,
        items=[item],
        parameter1=parameter1,
        parameter2=parameter2,
        parameter5=parameter5,
        parameter6=parameter6,
        supplier_payment_terms_ref_id=supplier_payment_terms_ref_id,
    )
