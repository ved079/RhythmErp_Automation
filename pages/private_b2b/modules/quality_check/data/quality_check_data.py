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

ITEM_TYPE_IDS = [1, 2, 3]

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
    "item_type_ref_id": 1,
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
    "alternate_uom": 1,
}


def compute_line_amount(accepted_qty: float, net_rate: float) -> float:
    return accepted_qty * net_rate


def compute_master_total(lines: List[Dict]) -> float:
    return sum(line.get("txn_currency_amount", 0) for line in lines)


def compute_expected_results(payload: dict) -> dict:
    lines = payload.get("qc_details", [])
    computed_lines = []
    for line in lines:
        aqty = float(line.get("alternate_accepted_qty", 0))
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
        "alternate_uom": 1,
    }


def _default_qc_parameter_details() -> List[dict]:
    return [
        {"item_quality_parameter_ref_id": 1, "actual_value": 0},
    ]


def _default_qc_bags_details(no_of_bags: int, empty_bag_weight: float) -> List[dict]:
    weight_per_bag = round(empty_bag_weight / no_of_bags, 4) if no_of_bags else 0.0
    return [
        {
            "type_of_bags_ref_id": 1,
            "quantity_of_bags": no_of_bags,
            "weight_of_bags": weight_per_bag,
            "total_weight_of_bags": empty_bag_weight,
        }
    ]


def build_qc_payload(
    supplier_ref_id: int = 1,
    item_type_ref_id: int = 1,
    gate_pass_ref_id_id: int = 505,
    grn_ref_id_id: int = 146,
    po_ref_id_id: int = None,
    base_currency: int = 8,
    txn_currency: int = 1,
    conversion_rate: float = 1.0,
    parameter1: int = 1,
    parameter2: int = 1,
    parameter5: int = 1,
    parameter6: int = 1,
    transaction_date: str = None,
    vehicle_no: str = None,
    driver_name: str = None,
    remark: str = None,
    items: List[dict] = None,
    total_txn_currency_amount: float = None,
) -> dict:
    if transaction_date is None:
        transaction_date = date.today().isoformat()

    if items is None:
        no_of_bags = 1
        empty_bag_weight = 0.4
        items = [
            {
                "item_ref_id": 5,
                "no_of_bags": no_of_bags,
                "grn_qty": 66.0,
                "alternate_accepted_qty": 66.0,
                "alternate_rejected_qty": 0.0,
                "empty_bag_weight": empty_bag_weight,
                "base_rate": 20.0,
                "is_rate_weight_deduction": False,
                "deduction_percent": 0.0,
                "qc_deduction_rate": 0.0,
                "deduction_weight": 0.0,
                "net_rate": 20.0,
                "discount_rate": None,
                "c_d_deduction": 0.0,
                "alternate_uom": 1,
                "uom": 4,
                "uom_conversion": 0.001,
                "hsn_sac_no": 2,
                "qc_parameter_details": _default_qc_parameter_details(),
                "qc_bags_details": _default_qc_bags_details(no_of_bags, empty_bag_weight),
            }
        ]

    payload = {
        "transaction_date": transaction_date,
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": "Supplier",
        "item_type_ref_id": item_type_ref_id,
        "gate_pass_ref_id_id": gate_pass_ref_id_id,
        "grn_ref_id_id": grn_ref_id_id,
        "po_ref_id_id": po_ref_id_id,
        "base_currency": base_currency,
        "txn_currency": txn_currency,
        "conversion_rate": conversion_rate,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "vehicle_no": vehicle_no,
        "driver_name": driver_name,
        "qc_additional_details": {"remark": remark},
        "qc_details": items,
    }
    if total_txn_currency_amount is not None:
        payload["total_txn_currency_amount"] = total_txn_currency_amount
    return payload


def generate_qc_payload(fk_overrides: dict = None, item_overrides: List[dict] = None) -> dict:
    fks = generate_random_fk_ids()
    if fk_overrides:
        fks.update(fk_overrides)

    num_items = random.randint(1, 3)
    items = []
    for i in range(num_items):
        grn_qty = float(random.randint(10, 100))
        rejected = float(random.randint(0, 4))
        accepted = grn_qty - rejected
        rate = float(random.randint(10, 500))
        no_of_bags = random.randint(1, 10)
        empty_bag_weight = round(no_of_bags * 0.4, 2)
        item = {
            "item_ref_id": fks["item_ref_id"],
            "no_of_bags": no_of_bags,
            "grn_qty": grn_qty,
            "alternate_accepted_qty": accepted,
            "alternate_rejected_qty": rejected,
            "empty_bag_weight": empty_bag_weight,
            "base_rate": rate,
            "is_rate_weight_deduction": False,
            "deduction_percent": 0.0,
            "qc_deduction_rate": 0.0,
            "deduction_weight": 0.0,
            "net_rate": rate,
            "discount_rate": None,
            "c_d_deduction": 0.0,
            "alternate_uom": fks.get("alternate_uom", 1),
            "uom": fks["uom"],
            "uom_conversion": 0.001,
            "hsn_sac_no": fks["hsn_sac_no"],
            "qc_parameter_details": _default_qc_parameter_details(),
            "qc_bags_details": _default_qc_bags_details(no_of_bags, empty_bag_weight),
        }
        if item_overrides and i < len(item_overrides):
            item.update(item_overrides[i])
        items.append(item)

    return build_qc_payload(
        supplier_ref_id=fks["supplier_ref_id"],
        item_type_ref_id=fks["item_type_ref_id"],
        gate_pass_ref_id_id=fks["gate_pass_ref_id_id"],
        grn_ref_id_id=fks["grn_ref_id_id"],
        po_ref_id_id=fks.get("po_ref_id_id"),
        base_currency=fks["base_currency"],
        txn_currency=fks["txn_currency"],
        conversion_rate=1.0,
        parameter1=fks["parameter1"],
        parameter2=fks["parameter2"],
        parameter5=fks["parameter5"],
        parameter6=fks["parameter6"],
        vehicle_no=None,
        driver_name=None,
        remark=None,
        items=items,
    )


def generate_qc_payloads(count: int, fk_overrides: dict = None) -> List[dict]:
    return [generate_qc_payload(fk_overrides=fk_overrides) for _ in range(count)]
