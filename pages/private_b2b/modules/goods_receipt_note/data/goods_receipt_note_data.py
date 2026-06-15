import random
from datetime import date
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

DIVISION_IDS = [1, 2]
DIVISION_NAMES = {1: "Export", 2: "Import"}

DEPARTMENT_IDS = [1, 2]
DEPARTMENT_NAMES = {1: "HR", 2: "Sales"}

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

UOM_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
UOM_NAMES = {1: "TESTUOM", 2: "NOS", 3: "QUIN", 4: "KG", 5: "LB", 6: "QTL", 7: "KWH", 8: "MTR", 9: "CM", 10: "HRS"}

GATE_PASS_IDS = [493, 494, 495, 496, 499, 500, 501, 503, 505, 507]
PO_REF_IDS = [200]

DEFAULT_FK_IDS = {
    "supplier_ref_id": 1,
    "gate_pass_ref_id_id": 505,
    "po_ref_id_id": 200,
    "base_currency": 1,
    "txn_currency": 1,
    "conversion_rate": 1.0,
    "parameter1": 1,
    "parameter2": 1,
    "parameter5": 25,
    "parameter6": 1,
    "item_ref_id": 5,
    "hsn_sac_no": 2,
    "uom": 3,
    "alternate_uom": 4,
}


def compute_line_amount(received_qty: float, rate: float) -> float:
    return received_qty * rate


def compute_master_total(lines: List[Dict]) -> float:
    return sum(line.get("amount", 0) for line in lines)


def compute_expected_results(payload: dict) -> dict:
    lines = payload.get("grn_item_details", [])
    computed_lines = []
    for line in lines:
        qty = float(line.get("accepted_qty", 0))
        rate = float(line.get("rate", 0))
        amount = compute_line_amount(qty, rate)
        computed_lines.append({"amount": amount})

    master_total = compute_master_total(computed_lines)
    return {
        "lines": computed_lines,
        "master_total": master_total,
        "_payload": payload,
    }


def assert_calculations_match(entry: dict, expected: dict):
    errors = []
    live_lines = entry.get("grn_item_details", [])
    for i, (live, exp) in enumerate(zip(live_lines, expected["lines"])):
        live_amt = float(live.get("txn_currency_amount_detail", 0) or 0)
        exp_amt = float(exp.get("amount", 0))
        if abs(live_amt - exp_amt) > 0.01:
            errors.append(f"Line[{i}].amount: expected {exp_amt}, got {live_amt}")

    if errors:
        raise AssertionError("Calculation mismatch:\n  " + "\n  ".join(errors))


def generate_random_fk_ids() -> dict:
    return {
        "supplier_ref_id": random.choice(SUPPLIER_IDS),
        "gate_pass_ref_id_id": random.choice(GATE_PASS_IDS),
        "po_ref_id_id": random.choice(PO_REF_IDS),
        "txn_currency": random.choice(CURRENCY_IDS),
        "base_currency": random.choice(CURRENCY_IDS),
        "parameter1": random.choice(DIVISION_IDS),
        "parameter2": random.choice(DEPARTMENT_IDS),
        "parameter5": random.choice(TYPE_OF_SALE_IDS),
        "parameter6": random.choice(LOCATION_IDS),
        "item_ref_id": random.choice(ITEM_IDS),
        "hsn_sac_no": random.choice(HSN_SAC_IDS),
        "uom": random.choice(UOM_IDS),
        "alternate_uom": random.choice(UOM_IDS),
    }


def build_grn_payload(
    supplier_ref_id: int = 1,
    gate_pass_ref_id_id: int = 505,
    po_ref_id_id: int = 200,
    base_currency: int = 1,
    txn_currency: int = 1,
    conversion_rate: float = 1.0,
    parameter1: int = 1,
    parameter2: int = 1,
    parameter5: int = 25,
    parameter6: int = 1,
    transaction_date: str = None,
    additional_details: dict = None,
    items: List[dict] = None,
) -> dict:
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    if additional_details is None:
        additional_details = {
            "vehicle_receipt_no": None,
            "vehicle_no": "MH14KK2533",
            "transporter_name": "Test Driver API",
            "supplier_bill_no": None,
            "supplier_bill_date": date.today().isoformat(),
            "e_way_bill_no": None,
            "bill_of_entry_no": None,
            "remark": None,
        }

    if items is None:
        items = [
            {
                "item_ref_id": 5,
                "hsn_sac_no": 2,
                "uom": 3,
                "received_qty": 10.0,
                "rate": 20.0,
                "no_of_bags": 1,
                "alternate_uom": 4,
                "accepted_qty": 10.0,
                "rejected_qty": 0.0,
            }
        ]

    return {
        "transaction_date": transaction_date,
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": "Supplier",
        "gate_pass_ref_id_id": gate_pass_ref_id_id,
        "po_ref_id_id": po_ref_id_id,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": conversion_rate,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "additional_details": additional_details,
        "grn_item_details": items,
    }


def generate_grn_payload(fk_overrides: dict = None, item_overrides: List[dict] = None) -> dict:
    fks = generate_random_fk_ids()
    if fk_overrides:
        fks.update(fk_overrides)

    num_items = random.randint(1, 3)
    items = []
    for i in range(num_items):
        qty = random.randint(1, 100)
        rate = random.randint(10, 500)
        item = {
            "item_ref_id": fks["item_ref_id"],
            "hsn_sac_no": fks["hsn_sac_no"],
            "uom": fks["uom"],
            "received_qty": float(qty),
            "rate": float(rate),
            "no_of_bags": random.randint(1, 10),
            "alternate_uom": fks["alternate_uom"],
            "accepted_qty": float(qty),
            "rejected_qty": 0.0,
        }
        if item_overrides and i < len(item_overrides):
            item.update(item_overrides[i])
        items.append(item)

    return build_grn_payload(
        supplier_ref_id=fks["supplier_ref_id"],
        gate_pass_ref_id_id=fks["gate_pass_ref_id_id"],
        po_ref_id_id=fks["po_ref_id_id"],
        base_currency=fks["base_currency"],
        txn_currency=fks["txn_currency"],
        conversion_rate=1.0,
        parameter1=fks["parameter1"],
        parameter2=fks["parameter2"],
        parameter5=fks["parameter5"],
        parameter6=fks["parameter6"],
        items=items,
    )


def generate_grn_payloads(count: int, fk_overrides: dict = None) -> List[dict]:
    return [generate_grn_payload(fk_overrides=fk_overrides) for _ in range(count)]
