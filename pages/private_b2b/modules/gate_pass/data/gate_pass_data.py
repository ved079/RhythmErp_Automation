import random
from datetime import date
from typing import Dict, List, Optional

# ── Reference Data ──────────────────────────────────────────────────

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
ITEM_TYPE_NAMES = {113: "Farm", 114: "Non Farm"}

DIVISION_IDS = [1, 2]
DIVISION_NAMES = {1: "Export", 2: "Import"}

DEPARTMENT_IDS = [1, 2]
DEPARTMENT_NAMES = {1: "HR", 2: "Sales"}

DELIVERY_TYPE_IDS = [28, 29]
DELIVERY_TYPE_NAMES = {28: "Delivery", 29: "Spot"}

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

AGENT_IDS = [15, 16, 17, 18, 19, 20]

UOM_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

HSN_SAC_IDS = [1, 2, 3, 4, 5, 6, 7]

DEFAULT_FK_IDS = {
    "supplier_ref_id": 1,
    "item_type_ref_id": 113,
    "parameter1": 1,
    "delivery_type": 29,
    "item_ref_id": 5,
    "agent_ref_id": 15,
    "base_uom": 4,
    "hsn_sac_no": 2,
}

# ── Random FK Generator ─────────────────────────────────────────────


def generate_random_fk_ids() -> dict:
    return {
        "supplier_ref_id": random.choice(SUPPLIER_IDS),
        "item_type_ref_id": random.choice(ITEM_TYPE_IDS),
        "parameter1": random.choice(DIVISION_IDS),
        "parameter2": random.choice(DEPARTMENT_IDS),
        "delivery_type": random.choice(DELIVERY_TYPE_IDS),
        "item_ref_id": random.choice(ITEM_IDS),
        "agent_ref_id": random.choice(AGENT_IDS),
        "base_uom": random.choice(UOM_IDS),
        "hsn_sac_no": random.choice(HSN_SAC_IDS),
    }


# ── Payload Builder ─────────────────────────────────────────────────


PARAMETER_IDS = [1, 2]


def build_gp_payload(
    supplier_ref_id: int = 1,
    supplier_ref_type: str = "Supplier",
    item_type_ref_id: int = 113,
    delivery_type: int = 29,
    agent_ref_id: int = None,
    parameter1: int = 1,
    parameter2: int = 1,
    parameter5: int = 1,
    parameter6: int = 1,
    distance: float = 50.0,
    vehicle_no: str = "MH14KK2533",
    driver_name: str = "Test Driver",
    driver_contact_no: int = 9000000000,
    transporter_name: str = None,
    supplier_bill_date: str = None,
    e_way_bill_no: str = None,
    bill_of_entry_number: str = None,
    transaction_date: str = None,
    in_time: str = None,
    out_time: str = None,
    remark: str = None,
    grn_check: bool = False,
    qc_check: bool = False,
    po_ref_id_id: int = None,
    items: List[dict] = None,
) -> dict:
    if transaction_date is None:
        transaction_date = f"{date.today().isoformat()}"
    if in_time is None:
        in_time = f"{date.today().isoformat()}T09:00:00Z"

    if items is None:
        items = [
            {
                "item_ref_id": 5,
                "no_of_bags": 10,
                "quantity": 100.0,
                "base_uom": 4,
                "hsn_sac_no": 2,
            }
        ]

    gate_pass_details = [
        {
            "item_ref_id": it["item_ref_id"],
            "no_of_bags": it.get("no_of_bags"),
            "alternate_quantity": it.get("alternate_quantity", it.get("quantity")),
            "base_uom": it.get("base_uom"),
            "alternate_uom": it.get("alternate_uom"),
            "uom_conversion": it.get("uom_conversion", 1.0),
            "hsn_sac_no": it.get("hsn_sac_no"),
        }
        for it in items
    ]

    payload = {
        "transaction_date": transaction_date,
        "supplier_ref_id": supplier_ref_id,
        "supplier_ref_type": supplier_ref_type,
        "item_type_ref_id": item_type_ref_id,
        "delivery_type": delivery_type,
        "in_time": in_time,
        "distance": distance,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "grn_check": grn_check,
        "qc_check": qc_check,
        "gate_pass_details": gate_pass_details,
    }

    # Linked PO (PO -> GP -> GRN -> QC -> PB flow). Omitted in the standalone
    # GP -> GRN -> QC -> PB flow where no PO was created.
    if po_ref_id_id is not None:
        payload["po_ref_id_id"] = po_ref_id_id
    if agent_ref_id is not None:
        payload["agent_ref_id"] = agent_ref_id

    # Stored-record shape: driver/vehicle/transporter/etc live under
    # additional_details, not at the top level. Only non-null values are sent.
    additional_details = {}
    for key, val in (
        ("vehicle_no", vehicle_no),
        ("driver_name", driver_name),
        ("driver_contact_no", driver_contact_no),
        ("transporter_name", transporter_name),
        ("supplier_bill_date", supplier_bill_date),
        ("e_way_bill_no", e_way_bill_no),
        ("bill_of_entry_number", bill_of_entry_number),
        ("out_time", out_time),
        ("remark", remark),
    ):
        if val is not None:
            additional_details[key] = val
    payload["additional_details"] = additional_details

    return payload


# ── Random Payload Generators ───────────────────────────────────────


def generate_gp_payload(
    fk_overrides: dict = None,
    item_overrides: List[dict] = None,
) -> dict:
    fks = generate_random_fk_ids()
    if fk_overrides:
        fks.update(fk_overrides)

    num_items = random.randint(1, 3)
    items = []
    for i in range(num_items):
        item = {
            "item_ref_id": random.choice(ITEM_IDS),
            "no_of_bags": random.randint(1, 20),
            "quantity": float(random.randint(10, 500)),
            "base_uom": random.choice(UOM_IDS),
            "hsn_sac_no": random.choice(HSN_SAC_IDS),
        }
        if item_overrides and i < len(item_overrides):
            item.update(item_overrides[i])
        items.append(item)

    return build_gp_payload(
        supplier_ref_id=fks["supplier_ref_id"],
        item_type_ref_id=fks["item_type_ref_id"],
        delivery_type=fks.get("delivery_type"),
        agent_ref_id=fks.get("agent_ref_id"),
        parameter1=fks.get("parameter1"),
        parameter2=fks.get("parameter2"),
        distance=float(random.randint(10, 500)),
        vehicle_no=f"MH{random.randint(10,99)}XX{random.randint(1000,9999)}",
        driver_contact_no=random.choice([9000000000, 9123456789, 9876543210]),
        items=items,
    )


def generate_gp_payloads(
    count: int, fk_overrides: dict = None
) -> List[dict]:
    return [generate_gp_payload(fk_overrides=fk_overrides) for _ in range(count)]
