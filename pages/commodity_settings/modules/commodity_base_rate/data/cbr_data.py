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
    "Pune": 1,
    "Mumbai": 2,
    "London": 3,
    "Amravati": 4,
    "Akole": 5,
    "Thane": 6,
    "Manchester": 7,
    "Himachal": 8,
    "Kothrud": 9,
}

ITEM_ID_MAP = {
    "Spinach Flexible Green Huge Droplet": 5,
    "Cherry Flexible Green Huge Droplet": 6,
    "Ginger Hollow Orange Minute Heart": 7,
    "Ginger Fuzzy Ruby Teeny Heart": 9,
    "Apple Stiff Blue Deep Heart": 12,
    "Spinach Fuzzy Magenta Small Circle": 13,
    "Banana Hollow Peach Enormous Crescent": 14,
    "Apple Bumpy Charcoal Broad Ring": 15,
    "Onion Silky Brown Teeny Hexagon": 16,
    "Papaya Stiff Cream Micro Loop": 17,
}

UOM_ID_MAP = {
    "TESTUOM": 1,
    "NOS": 2,
    "QUIN": 3,
    "CAN": 4,
    "LB": 5,
    "QTL": 6,
    "KWH": 7,
    "BTL": 8,
    "CM": 9,
    "HRS": 10,
    "QUIN76": 11,
}

# Grid detail data: (item_name, uom_name) pairs for CBR detail rows
CBR_GRID_DATA = [
    ("Spinach Flexible Green Huge Droplet", "NOS"),
    ("Cherry Flexible Green Huge Droplet", "QUIN"),
    ("Ginger Hollow Orange Minute Heart", "CAN"),
    ("Ginger Fuzzy Ruby Teeny Heart", "LB"),
    ("Apple Stiff Blue Deep Heart", "NOS"),
    ("Spinach Fuzzy Magenta Small Circle", "QUIN"),
    ("Banana Hollow Peach Enormous Crescent", "CAN"),
    ("Apple Bumpy Charcoal Broad Ring", "LB"),
    ("Onion Silky Brown Teeny Hexagon", "NOS"),
    ("Papaya Stiff Cream Micro Loop", "QUIN"),
]

CBR_USED_LOCATION_IDS = set()

COMMODITY_BASE_RATE_API_DATA = [
    ("Common", "London"),
    ("Common", "Amravati"),
    ("Common", "Akole"),
    ("Common", "Thane"),
    ("Common", "Manchester"),
    ("Common", "Himachal"),
    ("Common", "Kothrud"),
    ("Supplier", "London"),
    ("Supplier", "Amravati"),
    ("Supplier", "Akole"),
    ("Supplier", "Thane"),
    ("Supplier", "Manchester"),
    ("Supplier", "Himachal"),
    ("Supplier", "Kothrud"),
]


def build_cbr_api_payload(pricing_type_ref_id, location_ref_id,
                          from_date="2026-06-02T00:00:00Z",
                          to_date="2099-12-30T18:30:00Z",
                          detail_rows=None):
    """Build a single CBR API payload with header + item detail rows."""
    if detail_rows is None:
        # Default: one row using first item and UOM from the pool
        item_name, uom_name = CBR_GRID_DATA[0]
        detail_rows = [
            {
                "item_ref_id": ITEM_ID_MAP[item_name],
                "uom": UOM_ID_MAP[uom_name],
                "minimum_range": round(random.uniform(500, 2000), 2),
                "maximum_range": round(random.uniform(5000, 10000), 2),
                "details": [],
            }
        ]
    return {
        "id": "",
        "attribute_name": "Commodity Base Rate",
        "pricing_type_ref_id": pricing_type_ref_id,
        "from_date": from_date,
        "to_date": to_date,
        "location_ref_id": location_ref_id,
        "details": [],
        "children": [
            {
                "stepper_name": "Define Item Rate Details",
                "is_stepper": True,
                "details": detail_rows,
                "children": [],
            }
        ],
    }


def generate_cbr_payloads(count=10, offset=0, skip_location_ids=None, used_combos=None, fk_ids=None):
    """Generate N API payloads for CBR. Resolves FK names to IDs via FkResolver
    or fallback maps. Automatically shifts to_date years when a location would
    cause a duplicate."""
    fk_ids = fk_ids or {}
    loc_map = fk_ids.get("location_ref_id", LOCATION_ID_MAP)
    pt_map = PRICING_TYPE_ID_MAP

    pool = COMMODITY_BASE_RATE_API_DATA
    payloads = []

    combo_set = set()
    if skip_location_ids:
        for loc_id in skip_location_ids:
            combo_set.add((2099, loc_id))
    if used_combos:
        combo_set.update(used_combos)

    for i in range(count):
        idx = (offset + i) % len(pool)
        pricing_type_name, location_name = pool[idx]

        pt_id = pt_map.get(pricing_type_name)
        loc_id = loc_map.get(location_name)
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

SCREEN_NAME_FIELDS = {
    "pricing_type_ref_id": None,
    "location_ref_id": "Location",
    "item_ref_id": "Item Master",
    "uom": "UOM",
}

PRICING_TYPE_NAMES = dict(PRICING_TYPE_ID_MAP)
LOCATION_NAMES = dict(LOCATION_ID_MAP)

DEFAULT_COMMODITY_BASE_RATE_FK_IDS = {
    "pricing_type_ref_id": PRICING_TYPE_ID_MAP,
    "location_ref_id": LOCATION_ID_MAP,
}


def get_fk_screen_mapping():
    """Return FK field → screen name mapping for live FkResolver resolution."""
    return {
        "location_ref_id": "Location",
        "item_ref_id":     "Item Master",
        "uom":             "UOM",
    }


def enrich_existing_entries(client, entries):
    """Fetch full detail for each CBR listing row.

    Returns enriched entries with:
      - _detail: full raw detail response
      - _existing_item_ids: set of item_ref_ids already in the detail grid
      - location_ref_id: resolved to integer ID
    """
    enriched = []
    for entry in entries:
        try:
            detail = client.get_entry("Commodity Base Rate", entry["id"])
            existing_item_ids = set()
            for child in detail.get("children", []):
                for row in child.get("details", []):
                    iid = row.get("item_ref_id")
                    if iid is not None:
                        existing_item_ids.add(int(iid))
            enriched.append({
                **entry,
                "_detail": detail,
                "_existing_item_ids": existing_item_ids,
            })
        except Exception:
            enriched.append({**entry, "_detail": None, "_existing_item_ids": set()})
    return enriched


def generate_batch_payloads(count=20, prefix=None, dropdown_ids=None, offset=0, existing_entries=None):
    """Generate CBR UPDATE payloads: add missing items to each location's detail grid.

    CBR unique constraint is (to_date, location_ref_id) — one header per location.
    Items go in the detail grid rows. This function updates existing records to
    add all items not yet present in their grid.

    Requires dropdown_ids:
      - location_ref_id: {name: id}
      - item_ref_id:     {name: id}
      - item_uom_map:    {item_id: uom_name_or_id}
      - uom:             {name: id}

    existing_entries must be enriched via enrich_existing_entries().
    """
    fk_ids = dropdown_ids or {}
    loc_map = fk_ids.get("location_ref_id", {})
    item_map = fk_ids.get("item_ref_id", {})
    item_uom_map = fk_ids.get("item_uom_map", {})
    uom_map = fk_ids.get("uom", {})
    pt_id = PRICING_TYPE_ID_MAP["Common"]

    def _to_id(val, name_map):
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return int(val)
        v = name_map.get(val)
        if v is not None:
            return int(v)
        for k, vid in name_map.items():
            if k.lower().strip() == val.lower().strip():
                return int(vid)
        return None

    def _resolve_uom(val):
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return int(val)
        return int(uom_map[val]) if val in uom_map else None

    all_item_ids = [int(v) for v in item_map.values()]
    all_uom_ids = [int(v) for v in uom_map.values()] if uom_map else []

    def _resolve_uom_with_fallback(item_id):
        uom_id = _resolve_uom(item_uom_map.get(item_id))
        if uom_id is None and all_uom_ids:
            uom_id = random.choice(all_uom_ids)
        return uom_id

    # Build map of location_id → enriched existing entry (if any)
    existing_by_loc = {}
    for entry in (existing_entries or []):
        loc_id = _to_id(entry.get("location_ref_id"), loc_map)
        if loc_id is not None:
            existing_by_loc[loc_id] = entry

    payloads = []
    for loc_id in loc_map.values():
        if len(payloads) >= count:
            break

        loc_id = int(loc_id)
        existing = existing_by_loc.get(loc_id)

        if existing and existing.get("_detail"):
            # Location already has a record — UPDATE with any missing items
            detail = existing["_detail"]
            already_have = existing.get("_existing_item_ids", set())
            missing_items = [iid for iid in all_item_ids if iid not in already_have]
            if not missing_items:
                continue  # all items already present, nothing to do

            existing_rows = []
            for child in detail.get("children", []):
                existing_rows = child.get("details", [])
                break

            new_rows = list(existing_rows)
            for item_id in missing_items:
                uom_id = _resolve_uom_with_fallback(item_id)
                new_rows.append({
                    "item_ref_id": item_id,
                    "uom": uom_id,
                    "minimum_range": round(random.uniform(500, 2000), 2),
                    "maximum_range": round(random.uniform(5000, 10000), 2),
                    "details": [],
                })

            payloads.append({
                **detail,
                "id": existing["id"],
                "children": [{
                    "stepper_name": "Define Item Rate Details",
                    "is_stepper": True,
                    "details": new_rows,
                    "children": [],
                }],
            })

        else:
            # No record for this location yet — CREATE with all items
            detail_rows = []
            for item_id in all_item_ids:
                uom_id = _resolve_uom_with_fallback(item_id)
                detail_rows.append({
                    "item_ref_id": item_id,
                    "uom": uom_id,
                    "minimum_range": round(random.uniform(500, 2000), 2),
                    "maximum_range": round(random.uniform(5000, 10000), 2),
                    "details": [],
                })

            payloads.append(build_cbr_api_payload(pt_id, loc_id, detail_rows=detail_rows))

    return payloads


