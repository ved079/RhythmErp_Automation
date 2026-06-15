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

ITEM_TYPE_IDS = [113, 114]

DIVISION_IDS = [1, 2]
DEPARTMENT_IDS = [1, 2]
LOCATION_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

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

UOM_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

QUALITY_PARAMETER_IDS = [1, 2, 3]
QUALITY_PARAMETER_NAMES = {
    1: "Moisture",
    2: "Purity",
    3: "Foreign Matter",
}

DEFAULT_FK_IDS = {
    "supplier_ref_id": 1,
    "item_type_ref_id": 113,
    "gate_pass_ref_id_id": 505,
    "grn_ref_id_id": 146,
    "base_currency": 8,
    "txn_currency": 1,
    "parameter1": 1,
    "parameter2": 1,
    "parameter5": 1,
    "parameter6": 1,
    "item_ref_id": 5,
    "hsn_sac_no": 2,
    "uom": 4,
}


def compute_line_amount(accepted_qty: float, net_rate: float) -> float:
    return accepted_qty * net_rate


def compute_master_total(lines: List[Dict]) -> float:
    return sum(line.get("txn_currency_amount", 0) for line in lines)


def compute_expected_results(payload: dict) -> dict:
    lines = payload.get("qc_details", [])
    computed_lines = []
    for line in lines:
        aqty = float(line.get("accepted_qty", 0))
        net = float(line.get("net_rate", 0))
        amount = compute_line_amount(aqty, net)
        computed_lines.append({"amount": amount})

    master_total = compute_master_total(
        [{"txn_currency_amount": l["amount"]} for l in computed_lines]
    )
    return {
        "lines": computed_lines,
        "master_total": master_total,
        "_payload": payload,
    }


def assert_calculations_match(entry: dict, expected: dict):
    errors = []
    live_lines = entry.get("qc_details", [])
    for i, (live, exp) in enumerate(zip(live_lines, expected["lines"])):
        live_amt = float(live.get("txn_currency_amount", 0) or 0)
        exp_amt = float(exp.get("amount", 0))
        if abs(live_amt - exp_amt) > 0.01:
            errors.append(f"Line[{i}].amount: expected {exp_amt}, got {live_amt}")

    if errors:
        raise AssertionError("Calculation mismatch:\n  " + "\n  ".join(errors))


def generate_random_fk_ids() -> dict:
    return {
        "supplier_ref_id": random.choice(SUPPLIER_IDS),
        "item_type_ref_id": random.choice(ITEM_TYPE_IDS),
        "gate_pass_ref_id_id": random.choice([493, 494, 495, 496, 499, 500, 501, 503, 505, 507]),
        "grn_ref_id_id": 146,
        "base_currency": random.choice(CURRENCY_IDS),
        "txn_currency": random.choice(CURRENCY_IDS),
        "parameter1": random.choice(DIVISION_IDS),
        "parameter2": random.choice(DEPARTMENT_IDS),
        "parameter5": 1,
        "parameter6": random.choice(LOCATION_IDS),
        "item_ref_id": random.choice(ITEM_IDS),
        "hsn_sac_no": random.choice(HSN_SAC_IDS),
        "uom": random.choice(UOM_IDS),
    }


def _default_quality_details(item_ref_id: int, hsn_sac_no: int, uom: int) -> List[dict]:
    return [
        {"item_quality_parameter_ref_id": 1, "actual_value": 1},
        {"item_quality_parameter_ref_id": 2, "actual_value": 1},
        {"item_quality_parameter_ref_id": 3, "actual_value": 1},
    ]


def build_qc_payload(
    supplier_ref_id: int = 1,
    item_type_ref_id: int = 113,
    gate_pass_ref_id_id: int = 505,
    grn_ref_id_id: int = 146,
    base_currency: int = 8,
    txn_currency: int = 1,
    conversion_rate: float = 1.0,
    parameter1: int = 1,
    parameter2: int = 1,
    parameter5: int = 1,
    parameter6: int = 1,
    transaction_date: str = None,
    additional_details: dict = None,
    items: List[dict] = None,
) -> dict:
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    if additional_details is None:
        additional_details = {
            "vehicle_number": None,
            "driver_name": None,
            "remark": None,
        }

    if items is None:
        items = [
            {
                "item_ref_id": 5,
                "no_of_bags": 1,
                "grn_qty": 66.0,
                "accepted_qty": 66.0,
                "rejected_qty": 0.0,
                "base_rate": 20.0,
                "deduction_percent": None,
                "deduction_rate": None,
                "qc_rate": None,
                "net_rate": 20.0,
                "uom": 4,
                "hsn_sac_no": 2,
                "details": _default_quality_details(5, 2, 4),
            }
        ]

    payload = {
        "transaction_date": transaction_date,
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": "Supplier",
        "item_type_ref_id": item_type_ref_id,
        "gate_pass_ref_id_id": gate_pass_ref_id_id,
        "grn_ref_id_id": grn_ref_id_id,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": conversion_rate,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "qc_additional_details": additional_details,
        "qc_details": items,
    }
    return payload


def generate_qc_payload(fk_overrides: dict = None, item_overrides: List[dict] = None) -> dict:
    fks = generate_random_fk_ids()
    if fk_overrides:
        fks.update(fk_overrides)

    num_items = random.randint(1, 3)
    items = []
    for i in range(num_items):
        qty = float(random.randint(10, 100))
        rate = float(random.randint(10, 500))
        item = {
            "item_ref_id": fks["item_ref_id"],
            "no_of_bags": random.randint(1, 10),
            "grn_qty": qty,
            "accepted_qty": qty,
            "rejected_qty": 0.0,
            "base_rate": rate,
            "deduction_percent": None,
            "deduction_rate": None,
            "qc_rate": None,
            "net_rate": rate,
            "uom": fks["uom"],
            "hsn_sac_no": fks["hsn_sac_no"],
            "details": _default_quality_details(
                fks["item_ref_id"], fks["hsn_sac_no"], fks["uom"]
            ),
        }
        if item_overrides and i < len(item_overrides):
            item.update(item_overrides[i])
        items.append(item)

    return build_qc_payload(
        supplier_ref_id=fks["supplier_ref_id"],
        item_type_ref_id=fks["item_type_ref_id"],
        gate_pass_ref_id_id=fks["gate_pass_ref_id_id"],
        grn_ref_id_id=fks["grn_ref_id_id"],
        base_currency=fks["base_currency"],
        txn_currency=fks["txn_currency"],
        conversion_rate=1.0,
        parameter1=fks["parameter1"],
        parameter2=fks["parameter2"],
        parameter5=fks["parameter5"],
        parameter6=fks["parameter6"],
        items=items,
    )


def generate_qc_payloads(count: int, fk_overrides: dict = None) -> List[dict]:
    return [generate_qc_payload(fk_overrides=fk_overrides) for _ in range(count)]
