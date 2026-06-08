"""
cbr_data.py - Commodity Base Rate test data generators
Screen: Commodity Settings > Commodity Base Rate

Optimised (v2) — UOM golden standard:
- Cleaner data generators
- Kept API payload builders and FK maps (needed for batch create)
- None = select first available option from dropdown (resilient to ERP data changes)
"""

import random
from datetime import datetime, timedelta


# ─── Date Format ─────────────────────────────────────────────────────────────
DATE_FORMAT = "%d/%m/%Y"
DEFAULT_TO_DATE = "30/12/2099"


# ─── Valid Data Generators ───────────────────────────────────────────────────

def generate_from_date(offset_days=0):
    """Generate From Date string. Default: today + offset."""
    dt = datetime.now() + timedelta(days=offset_days)
    return dt.strftime(DATE_FORMAT)


def generate_to_date(offset_days=0):
    """Generate To Date string. Default: today + offset."""
    dt = datetime.now() + timedelta(days=offset_days)
    return dt.strftime(DATE_FORMAT)


def generate_future_from_date(days_ahead=30):
    """Generate a future From Date for version creation."""
    return generate_from_date(offset_days=days_ahead)


def generate_valid_cbr_data(pricing_type="Common", location="Jafrabad",
                            item_name=None, item_rate="1500", uom=None):
    """Generate valid CBR data for Create form.
    item_name and uom default to None = select FIRST available option."""
    return {
        "pricing_type": pricing_type,
        "from_date": generate_from_date(),
        "to_date": DEFAULT_TO_DATE,
        "location": location,
        "item_name": item_name,
        "item_rate": item_rate,
        "uom": uom,
    }


def generate_valid_common_record():
    """Generate valid Common pricing type record."""
    rate = str(random.randint(1000, 5000))
    return generate_valid_cbr_data(
        pricing_type="Common",
        location="Jafrabad",
        item_name=None,
        item_rate=rate,
        uom=None,
    )


def generate_valid_supplier_record():
    """Generate valid Supplier pricing type record."""
    rate = str(random.randint(1000, 5000))
    return generate_valid_cbr_data(
        pricing_type="Supplier",
        location="Akola",
        item_name=None,
        item_rate=rate,
        uom=None,
    )


def generate_multi_row_record():
    """Generate record with multiple grid rows."""
    return {
        "pricing_type": "Common",
        "from_date": generate_from_date(),
        "to_date": DEFAULT_TO_DATE,
        "location": "Jafrabad",
        "grid_rows": [
            {"item_name": None, "item_rate": str(random.randint(1000, 3000)), "uom": None},
            {"item_name": None, "item_rate": str(random.randint(2000, 4000)), "uom": None},
            {"item_name": None, "item_rate": str(random.randint(3000, 5000)), "uom": None},
        ],
    }


# ─── Validation Test Data ────────────────────────────────────────────────────

def generate_empty_field_data():
    """Return data with all fields empty for mandatory field validation."""
    return {
        "pricing_type": "",
        "from_date": "",
        "to_date": "",
        "location": "",
        "item_name": "",
        "item_rate": "",
        "uom": "",
    }


def generate_negative_rate_data():
    """Generate data with negative Item Rate. BUG-001."""
    return generate_valid_cbr_data(item_rate="-100")


def generate_special_chars_rate_data():
    """Generate data with special chars in Item Rate. BUG-001."""
    return generate_valid_cbr_data(item_rate="abc!@#")


def generate_zero_rate_data():
    """Generate data with zero Item Rate. BUG-002."""
    return generate_valid_cbr_data(item_rate="0")


def generate_custom_to_date_data(to_date="31/12/2026"):
    """Generate data with a custom To Date (not the default). BUG-004."""
    return generate_valid_cbr_data(
        item_rate=str(random.randint(1000, 3000)),
    ) | {"to_date": to_date}


# ─── Edit Data ───────────────────────────────────────────────────────────────

def generate_edit_data(new_rate=None):
    """Generate data for editing a record."""
    if new_rate is None:
        new_rate = str(random.randint(2000, 6000))
    return {"item_rate": new_rate}


# ─── Bug IDs ─────────────────────────────────────────────────────────────────
BUG_001 = "BUG-001: Item Rate accepts non-numeric input (negative/special chars)"
BUG_002 = "BUG-002: Item Rate accepts zero value"
BUG_003 = "BUG-003: Listing shows raw ISO timestamps instead of formatted dates"
BUG_004 = "BUG-004: To Date overridden to 30/12/2099 on submit, ignoring user selection"
BUG_005 = "BUG-005: Edit button disabled for newly created records"
BUG_006 = "BUG-006: Version creation fails with same From Date, generic error"


# ═══════════════════════════════════════════════════════════════════════════════
#  API Batch Create — Data Pool + Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════

# ── FK ID Mappings (from live ERP) ────────────────────────────────────

PRICING_TYPE_ID_MAP = {
    "Common": 118,
    "Supplier": 120,
}

LOCATION_ID_MAP = {
    "Charholi": 1,
    "Pune": 2,
    "Kothurd": 3,
    "London": 4,
    "Barcelona": 5,
    "Mumbai": 6,
    "Akola": 7,
    "Delhi": 8,
    "Agra": 9,
    "Indore": 10,
}

ITEM_ID_MAP = {
    "Sugarcane": 94,
    "Groundnut": 95,
    "Sunflower Seeds": 96,
    "Mustard Seeds": 97,
    "Green Gram": 98,
    "Black Gram": 99,
    "Chickpeas": 100,
    "Turmeric Powder": 101,
    "Red Chilli": 102,
    "Coriander Seeds": 103,
    "Cumin Seeds": 104,
    "Onion": 105,
    "Potato": 106,
    "Tomato": 107,
    "Mango": 108,
    "Iron Pipe": 130,
    "Cement Bag": 131,
    "Paint Bucket": 132,
    "Nut Bolt Set": 133,
    "PVC Pipe": 134,
    "Drill Machine": 135,
    "Hammer": 136,
    "Welding Rod": 137,
    "Measuring Tape": 138,
    "Bath Soap": 109,
    "Shampoo Bottle": 110,
    "Hair Oil": 111,
    "Toothpaste": 112,
    "Detergent Powder": 113,
    "Dish Wash Liquid": 114,
    "Floor Cleaner": 115,
    "Hand Wash": 116,
    "Face Cream": 117,
    "Talcum Powder": 118,
    "LED Bulb": 119,
    "Ceiling Fan": 120,
    "Extension Board": 121,
    "Electric Wire": 122,
    "Switch Board": 123,
    "Water Heater": 124,
    "Mixer Grinder": 125,
    "Electric Kettle": 126,
    "Inverter Battery": 127,
    "Solar Panel": 128,
    "A4 Paper": 139,
    "Ball Pen": 140,
    "Stapler": 141,
    "Printer Ink": 142,
    "File Folder": 143,
    "Marker Pen": 145,
    "Whiteboard": 146,
    "Calculator": 147,
}

UOM_ID_MAP = {
    "KG": 249,
    "MT": 250,
    "QT": 251,
    "NOS": 252,
    "Litres": 253,
    "LTR": 501,
    "MTR": 502,
    "dozens": 504,
    "MUND": 528,
    "BIGHA": 529,
    "CAN": 531,
    "SET": 533,
    "KM": 534,
    "MM": 536,
}

CBR_USED_LOCATION_IDS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

COMMODITY_BASE_RATE_API_DATA = [
    ("Common", "Kothurd"),
    ("Common", "London"),
    ("Common", "Barcelona"),
    ("Supplier", "Kothurd"),
    ("Supplier", "London"),
    ("Supplier", "Barcelona"),
    ("Common", "Charholi"),
    ("Common", "Pune"),
    ("Common", "Akola"),
    ("Common", "Delhi"),
    ("Supplier", "Charholi"),
    ("Supplier", "Pune"),
    ("Supplier", "Mumbai"),
    ("Supplier", "Akola"),
    ("Common", "Mumbai"),
    ("Common", "Agra"),
    ("Common", "Indore"),
    ("Supplier", "Delhi"),
    ("Supplier", "Agra"),
    ("Supplier", "Indore"),
]


def build_cbr_api_payload(pricing_type_ref_id, location_ref_id,
                          from_date="2026-06-02T00:00:00Z",
                          to_date="2099-12-30T18:30:00Z"):
    """Build a single API payload for CBR (header-only)."""
    return {
        "id": "",
        "attribute_name": "Commodity Base Rate",
        "pricing_type_ref_id": pricing_type_ref_id,
        "from_date": from_date,
        "to_date": to_date,
        "location_ref_id": location_ref_id,
    }


def generate_cbr_payloads(count=10, offset=0, skip_location_ids=None, used_combos=None):
    """Generate N API payloads for CBR. Resolves FK names to IDs.
    Automatically shifts to_date years when a location would cause a duplicate."""
    pool = COMMODITY_BASE_RATE_API_DATA
    payloads = []

    combo_set = set()
    for loc_id in CBR_USED_LOCATION_IDS:
        combo_set.add((2099, loc_id))
    if skip_location_ids:
        for loc_id in skip_location_ids:
            combo_set.add((2099, loc_id))
    if used_combos:
        combo_set.update(used_combos)

    for i in range(count):
        idx = (offset + i) % len(pool)
        pricing_type_name, location_name = pool[idx]

        pt_id = PRICING_TYPE_ID_MAP.get(pricing_type_name)
        loc_id = LOCATION_ID_MAP.get(location_name)
        if pt_id is None or loc_id is None:
            continue

        year = 2099
        while (year, loc_id) in combo_set and year >= 2026:
            year -= 1

        if year < 2026:
            continue

        payloads.append(build_cbr_api_payload(pt_id, loc_id, to_date=f"{year}-12-30T18:30:00Z"))
        combo_set.add((year, loc_id))

    return payloads


# ── Field Validation Rules ────────────────────────────────────────────

FIELD_VALIDATION_RULES = {
    "pricing_type_ref_id": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(PRICING_TYPE_ID_MAP),
        "note": "FK to Pricing Type. 2 options: Common=118, Supplier=120.",
    },
    "from_date": {
        "type": "date",
        "required": True,
        "note": "ISO datetime. Server auto-sets on create.",
    },
    "to_date": {
        "type": "date",
        "required": True,
        "note": "ISO datetime. Default sentinel: 2099-12-30T18:30:00Z.",
    },
    "location_ref_id": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(LOCATION_ID_MAP),
        "note": "FK to Location. 10 options.",
    },
}

PRICING_TYPE_NAMES = dict(PRICING_TYPE_ID_MAP)
LOCATION_NAMES = dict(LOCATION_ID_MAP)

DEFAULT_COMMODITY_BASE_RATE_FK_IDS = {
    "pricing_type_ref_id": PRICING_TYPE_ID_MAP,
    "location_ref_id": LOCATION_ID_MAP,
}


def generate_batch_payloads(count=20, prefix=None, dropdown_ids=None):
    """Generate a batch of unique CBR API payloads."""
    return generate_cbr_payloads(count=count)
