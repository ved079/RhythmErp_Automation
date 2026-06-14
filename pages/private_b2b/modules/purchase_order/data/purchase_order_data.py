import random
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional

SUPPLIER_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

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

PO_ITEM_TYPE_IDS = [113, 114]
PO_ITEM_TYPE_NAMES = {113: "Farm", 114: "Non Farm"}

PO_TYPE_IDS = [25, 24]
PO_TYPE_NAMES = {25: "Domestic", 24: "Import"}

DEPARTMENT_IDS = [1, 2]
DEPARTMENT_NAMES = {1: "HR", 2: "Sales"}

DIVISION_IDS = [1, 2]
DIVISION_NAMES = {1: "Export", 2: "Import"}

LOCATION_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
LOCATION_NAMES = {
    1: "Pune", 2: "Mumbai", 3: "London", 4: "Amravati",
    5: "Akole", 6: "Thane", 7: "Manchester", 8: "Himachal", 9: "Kothrud",
}

TYPE_OF_SALE_IDS = [25, 24]
TYPE_OF_SALE_NAMES = {25: "Domestic", 24: "Import"}

CURRENCY_IDS = [1, 8, 38, 107, 108]
CURRENCY_NAMES = {1: "INR", 8: "AUD", 38: "EUR", 107: "GBP", 108: "USD"}

ITEM_IDS = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

ITEM_NAMES = {
    5: "Spinach Flexible Green Huge Droplet",
    6: "Cherry Flexible Green Huge Droplet",
    7: "Ginger Hollow Orange Minute Heart",
    8: "Sourcing Type Test",
    9: "Ginger Fuzzy Ruby Teeny Heart",
    10: "Both Fields Test",
    11: "Sourcing Test item_sourcing",
    12: "Apple Stiff Blue Deep Heart",
    13: "Spinach Fuzzy Magenta Small Circle",
    14: "Banana Hollow Peach Enormous Crescent",
    15: "Apple Bumpy Charcoal Broad Ring",
    16: "Onion Silky Brown Teeny Hexagon",
    17: "Papaya Stiff Cream Micro Loop",
}

HSN_SAC_IDS = [1, 2, 3, 4, 5, 6, 7]
HSN_SAC_NAMES = {1: "293729", 2: "23456765", 3: "998311", 4: "996412", 5: "996121", 6: "0401", 7: "998322"}

UOM_IDS = [1, 2, 3, 5, 6, 7, 9, 10]
UOM_NAMES = {1: "TESTUOM", 2: "NOS", 3: "QUIN", 5: "LB", 6: "QTL", 7: "KWH", 9: "CM", 10: "HRS"}

PAYMENT_TERMS_IDS = [26, 27, 131, 549, 550, 551]
PAYMENT_TERMS_NAMES = {26: "30 Days", 27: "60 Days", 131: "Immediate", 549: "7 Days", 550: "14 Days", 551: "21 Days"}

DELIVERY_TERMS_IDS = [129, 130]
DELIVERY_TERMS_NAMES = {129: "Delivery", 130: "Spot"}

PACKING_FORWARDING_IDS = [89, 90]
PACKING_FORWARDING_NAMES = {89: "Nill", 90: "Extra"}

SUPPLIER_SHIP_FROM_IDS = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
SUPPLIER_BILL_FROM_IDS = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

TAX_RATE_IDS = [0]

DEFAULT_FK_IDS = {
    "supplier_ref_id": 1,
    "po_item_type": 113,
    "po_type": 25,
    "txn_currency": 8,
    "base_currency": 8,
    "parameter1": 1,
    "parameter2": 1,
    "parameter3": 25,
    "parameter4": 1,
    "parameter5": 2,
    "parameter6": 1,
    "supplier_payment_terms": 550,
    "supplier_delivery_terms": 130,
    "packing_forwarding_ref_id": 89,
    "supplier_ship_from": 1,
    "supplier_bill_from": 2,
    "item_ref_id": 5,
    "hsn_sac_no": 2,
    "uom": 3,
    "tax_rate": 0,
}


def compute_line_amount(quantity: float, rate: float) -> float:
    return quantity * rate


def compute_line_tax(amount: float, tax_rate_percent: float) -> float:
    return amount * tax_rate_percent / 100.0


def compute_line_total(amount: float, tax: float) -> float:
    return amount + tax


def compute_master_total(lines: List[Dict]) -> float:
    return sum(line.get("total_amount", 0) for line in lines)


def compute_discount_amount(total: float, discount_percent: Optional[float]) -> float:
    if not discount_percent:
        return 0.0
    return total * discount_percent / 100.0


def compute_interest_amount(total: float, interest_percent: Optional[float]) -> float:
    if not interest_percent:
        return 0.0
    return total * interest_percent / 100.0


def compute_expected_results(payload: dict) -> dict:
    lines = payload.get("purchasing_order_items_details", [])
    computed_lines = []
    for line in lines:
        qty = float(line.get("quantity", 0))
        rate = float(line.get("rate", 0))
        amount = compute_line_amount(qty, rate)
        tax_rate = float(line.get("tax_rate", 0) or 0)
        tax = compute_line_tax(amount, tax_rate)
        total = compute_line_total(amount, tax)
        computed_lines.append({
            "txn_currency_amount_detail": amount,
            "txn_currency_tax_amount_details": tax,
            "total_amount": total,
        })

    master_total = compute_master_total(
        [{"total_amount": l["total_amount"]} for l in computed_lines]
    )

    add = payload.get("additional_details", {})
    discount_pct = add.get("txn_currency_discount_percent")
    interest_pct = add.get("txn_currency_interest_percent")
    # Backend computes discount/interest from percentage when amount is 0/null
    discount_amt = compute_discount_amount(master_total, discount_pct)
    interest_amt = compute_interest_amount(master_total, interest_pct)

    return {
        "lines": computed_lines,
        "txn_currency_total_amount": master_total,
        "txn_currency_discount_amount": discount_amt,
        "txn_currency_interest_amount": interest_amt,
        "_payload": payload,
    }


def assert_calculations_match(entry: dict, expected: dict):
    errors = []
    live_lines = entry.get("purchasing_order_items_details", [])
    for i, (live, exp) in enumerate(zip(live_lines, expected["lines"])):
        for key in ["txn_currency_amount_detail", "txn_currency_tax_amount_details", "total_amount"]:
            live_val = float(live.get(key, 0) or 0)
            exp_val = float(exp.get(key, 0))
            if abs(live_val - exp_val) > 0.01:
                errors.append(f"Line[{i}].{key}: expected {exp_val}, got {live_val}")

    live_master = float(entry.get("txn_currency_total_amount", 0) or 0)
    exp_master = float(expected.get("txn_currency_total_amount", 0))
    if abs(live_master - exp_master) > 0.01:
        errors.append(f"Master.txn_currency_total_amount: expected {exp_master}, got {live_master}")

    live_add = entry.get("additional_details", {})
    exp_discount = float(expected.get("txn_currency_discount_amount", 0))
    live_discount = float(live_add.get("txn_currency_discount_amount", 0) or 0)
    if abs(live_discount - exp_discount) > 0.01:
        errors.append(f"Additional.txn_currency_discount_amount: expected {exp_discount}, got {live_discount}")

    exp_interest = float(expected.get("txn_currency_interest_amount", 0))
    live_interest = float(live_add.get("txn_currency_interest_amount", 0) or 0)
    if abs(live_interest - exp_interest) > 0.01:
        errors.append(f"Additional.txn_currency_interest_amount: expected {exp_interest}, got {live_interest}")

    if errors:
        raise AssertionError("Calculation mismatch:\n  " + "\n  ".join(errors))


def generate_random_fk_ids() -> dict:
    return {
        "supplier_ref_id": random.choice(SUPPLIER_IDS),
        "po_item_type": random.choice(PO_ITEM_TYPE_IDS),
        "po_type": random.choice(PO_TYPE_IDS),
        "txn_currency": random.choice(CURRENCY_IDS),
        "base_currency": random.choice(CURRENCY_IDS),
        "parameter1": random.choice(DIVISION_IDS),
        "parameter2": random.choice(DEPARTMENT_IDS),
        "parameter3": random.choice(TYPE_OF_SALE_IDS),
        "parameter4": random.choice(LOCATION_IDS),
        "parameter5": 2,
        "parameter6": 1,
        "supplier_payment_terms": random.choice(PAYMENT_TERMS_IDS),
        "supplier_delivery_terms": random.choice(DELIVERY_TERMS_IDS),
        "packing_forwarding_ref_id": random.choice(PACKING_FORWARDING_IDS),
        "supplier_ship_from": random.choice(SUPPLIER_SHIP_FROM_IDS),
        "supplier_bill_from": random.choice(SUPPLIER_BILL_FROM_IDS),
        "item_ref_id": random.choice(ITEM_IDS),
        "hsn_sac_no": random.choice(HSN_SAC_IDS),
        "uom": random.choice(UOM_IDS),
    }


def build_po_payload(
    supplier_ref_id: int = 1,
    po_item_type: int = 113,
    po_type: int = 25,
    txn_currency: int = 8,
    base_currency: int = 8,
    conversion_rate: float = 1.0,
    parameter1: int = 1,
    parameter2: int = 1,
    parameter3: int = 25,
    parameter4: int = 1,
    parameter5: int = 2,
    parameter6: int = 1,
    transaction_date: str = None,
    additional_details: dict = None,
    supplier_details: dict = None,
    items: List[dict] = None,
) -> dict:
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    if additional_details is None:
        additional_details = {
            "transportation_charges": 0,
            "txn_currency_discount_percent": None,
            "txn_currency_discount_amount": 0,
            "txn_currency_interest_percent": None,
            "txn_currency_interest_amount": 0,
            "remark": None,
        }

    if supplier_details is None:
        supplier_details = {
            "supplier_payment_terms": 550,
            "supplier_delivery_terms": 130,
            "packing_forwarding_ref_id": 89,
            "supplier_ship_from": 1,
            "supplier_bill_from": 2,
        }

    if items is None:
        items = [
            {
                "item_ref_id": 5,
                "hsn_sac_no": 2,
                "uom": 3,
                "quantity": 10.0,
                "rate": 100.0,
                "expected_delivery_date": "2026-06-20",
            }
        ]

    return {
        "transaction_date": transaction_date,
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": "Supplier",
        "po_item_type": po_item_type,
        "po_type": po_type,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": conversion_rate,
        "parameter2": parameter2,
        "parameter1": parameter1,
        "parameter3": parameter3,
        "parameter4": parameter4,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "additional_details": additional_details,
        "supplier_details": supplier_details,
        "purchasing_order_items_details": items,
    }


def generate_po_payload(fk_overrides: dict = None, item_overrides: List[dict] = None) -> dict:
    fks = generate_random_fk_ids()
    if fk_overrides:
        fks.update(fk_overrides)

    items = []
    num_items = random.randint(1, 3)
    for i in range(num_items):
        qty = random.randint(1, 100)
        rate = random.randint(10, 500)
        item = {
            "item_ref_id": random.choice(ITEM_IDS),
            "hsn_sac_no": random.choice(HSN_SAC_IDS),
            "uom": random.choice(UOM_IDS),
            "quantity": float(qty),
            "rate": float(rate),
            "expected_delivery_date": (date.today().isoformat()),
        }
        if item_overrides and i < len(item_overrides):
            item.update(item_overrides[i])
        items.append(item)

    return build_po_payload(
        supplier_ref_id=fks["supplier_ref_id"],
        po_item_type=fks["po_item_type"],
        po_type=fks["po_type"],
        txn_currency=fks["txn_currency"],
        base_currency=fks["base_currency"],
        conversion_rate=1.0,
        parameter1=fks["parameter1"],
        parameter2=fks["parameter2"],
        parameter3=fks["parameter3"],
        parameter4=fks["parameter4"],
        parameter5=2,
        parameter6=1,
        supplier_details={
            "supplier_payment_terms": fks["supplier_payment_terms"],
            "supplier_delivery_terms": fks["supplier_delivery_terms"],
            "packing_forwarding_ref_id": fks["packing_forwarding_ref_id"],
            "supplier_ship_from": fks["supplier_ship_from"],
            "supplier_bill_from": fks["supplier_bill_from"],
        },
        items=items,
    )


def generate_po_payloads(count: int, fk_overrides: dict = None) -> List[dict]:
    return [generate_po_payload(fk_overrides=fk_overrides) for _ in range(count)]
