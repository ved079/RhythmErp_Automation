"""
cbr_data.py - Commodity Base Rate test data generators
Screen: Commodity Settings > Commodity Base Rate

NOTE: Item Name and UOM options are ERP-dependent and may vary.
      The page object uses a "first available" fallback when
      exact option text is not found, so tests remain robust
      even if dropdown options change.
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
    
    item_name and uom default to None, which tells the page object
    to select the FIRST AVAILABLE option from the dropdown.
    This makes tests resilient to ERP data changes.
    """
    return {
        "pricing_type": pricing_type,
        "from_date": generate_from_date(),
        "to_date": DEFAULT_TO_DATE,
        "location": location,
        "item_name": item_name,  # None = select first available
        "item_rate": item_rate,
        "uom": uom,  # None = select first available
    }


def generate_valid_common_record():
    """Generate valid Common pricing type record.
    Uses first available Item Name and UOM from dropdowns.
    """
    rate = str(random.randint(1000, 5000))
    return generate_valid_cbr_data(
        pricing_type="Common",
        location="Jafrabad",
        item_name=None,  # Will pick first available option
        item_rate=rate,
        uom=None,  # Will pick first available option
    )


def generate_valid_supplier_record():
    """Generate valid Supplier pricing type record.
    Uses first available Item Name and UOM from dropdowns.
    """
    rate = str(random.randint(1000, 5000))
    return generate_valid_cbr_data(
        pricing_type="Supplier",
        location="Akola",
        item_name=None,  # Will pick first available option
        item_rate=rate,
        uom=None,  # Will pick first available option
    )


def generate_multi_row_record():
    """Generate record with multiple grid rows.
    Uses first available Item Name and UOM from dropdowns.
    """
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
    """Generate data with negative Item Rate. BUG-001.
    Uses first available Item Name and UOM.
    """
    return generate_valid_cbr_data(item_rate="-100")


def generate_special_chars_rate_data():
    """Generate data with special chars in Item Rate. BUG-001.
    Uses first available Item Name and UOM.
    """
    return generate_valid_cbr_data(item_rate="abc!@#")


def generate_zero_rate_data():
    """Generate data with zero Item Rate. BUG-002.
    Uses first available Item Name and UOM.
    """
    return generate_valid_cbr_data(item_rate="0")


def generate_custom_to_date_data(to_date="31/12/2026"):
    """Generate data with a custom To Date (not the default). BUG-004.
    Uses first available Item Name and UOM.
    """
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
# Screen structure (discovered 2026-06-02):
#   Commodity Base Rate:
#     HEADER fields:
#       pricing_type_ref_id* (FK dropdown → 2 options: Common=118, Supplier=120)
#       from_date*           (datetime, auto-filled to current timestamp on create)
#       to_date*             (datetime, sentinel: 2099-12-30T18:30:00Z)
#       location_ref_id*     (FK dropdown → 10 locations)
#
#     DETAIL GRID — "Define Item Rate Commision Details" (is_stepper=true, is_grid=true):
#       item_ref_id*  (FK dropdown → Item Master table, 77 items)
#       item_rate*    (decimal string, pattern: ^(?!.*[+-])[0-9]+(\.[0-9]{1,4})?$)
#       uom*          (FK dropdown → UOM table, 42 options)
#
#       NOTE: Grid detail rows CANNOT be created via the main POST endpoint.
#       They must be added through the UI or a separate API call.
#       The batch_create script creates HEADER-ONLY entries.
#
#   UNIQUE CONSTRAINT: (to_date, location_ref_id) — each location can only
#   have ONE active CBR entry per to_date value. Duplicate combos are rejected
#   with a 400 error containing "Duplicate entry found for to_date, location_ref_id".
#
#   PAYLOAD STRUCTURE (header-only creation):
#     {
#       "id": "",
#       "attribute_name": "Commodity Base Rate",
#       "pricing_type_ref_id": <int>,      // 118=Common, 120=Supplier
#       "from_date": "<ISO datetime>",     // server auto-sets on create
#       "to_date": "2099-12-30T18:30:00Z",
#       "location_ref_id": <int>           // FK → Location table
#     }
#
# FK Dropdown mappings (live from ERP as of 2026-06-02):
#
#   Pricing Type — 2 options (see PRICING_TYPE_ID_MAP below).
#   Location — 10 options (see LOCATION_ID_MAP below).
#   Item Master — 77 items (see ITEM_ID_MAP below, clean subset used).
#   UOM — 42 options (see UOM_ID_MAP below, clean subset used).
#
# Existing entries in ERP (as of 2026-06-02):
#   IDs 34-62, covering location_ref_ids with to_date=2099-12-30:
#   Charholi(1), Pune(2), Mumbai(6), Akola(7), Delhi(8), Agra(9), Indore(10)
#   Available with to_date=2099-12-30: Kothurd(3), London(4), Barcelona(5)
#
# Data pool below covers various (pricing_type, location) combos with the
# default to_date, ensuring each (to_date, location_ref_id) combo is unique.
# ═══════════════════════════════════════════════════════════════════════════════

# ── FK ID Mappings (from live ERP) ────────────────────────────────────

# Pricing Type options (2 total)
PRICING_TYPE_ID_MAP = {
    "Common": 118,
    "Supplier": 120,
}

# Location options (10 total)
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

# Item Master options (clean/useful items — same as CQP module for consistency)
ITEM_ID_MAP = {
    # ── Agricultural Commodities ──────────────────────────────
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
    # ── Construction & Industrial ─────────────────────────────
    "Iron Pipe": 130,
    "Cement Bag": 131,
    "Paint Bucket": 132,
    "Nut Bolt Set": 133,
    "PVC Pipe": 134,
    "Drill Machine": 135,
    "Hammer": 136,
    "Welding Rod": 137,
    "Measuring Tape": 138,
    # ── FMCG / Household ─────────────────────────────────────
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
    # ── Electrical & Appliances ──────────────────────────────
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
    # ── Office & Stationery ──────────────────────────────────
    "A4 Paper": 139,
    "Ball Pen": 140,
    "Stapler": 141,
    "Printer Ink": 142,
    "File Folder": 143,
    "Marker Pen": 145,
    "Whiteboard": 146,
    "Calculator": 147,
}

# UOM options (clean/useful subset — standard measurement units)
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

# Locations already used in CBR with to_date=2099-12-30T18:30:00Z
# These (location_ref_id, to_date) combos CANNOT be reused with the same to_date.
# Updated 2026-06-02: All 10 locations are now used with default to_date
# (including Kothurd(3), London(4), Barcelona(5) from API exploration).
# NOTE: The batch_create.py script also fetches used combos dynamically
# from the API at runtime — this static list is a safety net / baseline.
CBR_USED_LOCATION_IDS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}


# ── Data Pool ─────────────────────────────────────────────────────────
# Each entry defines a CBR header record:
#   (pricing_type, location_name)
#
# The unique constraint is (to_date, location_ref_id), so each location
# can only appear ONCE with the default to_date=2099-12-30T18:30:00Z.
#
# For subsequent entries with the same location, a different to_date
# (shifted by 1 year) is used to avoid the unique constraint.

COMMODITY_BASE_RATE_API_DATA = [
    # ── Common pricing — unused locations ────────────────────────────
    ("Common", "Kothurd"),
    ("Common", "London"),
    ("Common", "Barcelona"),

    # ── Supplier pricing — unused locations ──────────────────────────
    ("Supplier", "Kothurd"),
    ("Supplier", "London"),
    ("Supplier", "Barcelona"),

    # ── Common pricing — re-use locations with shifted to_date ──────
    ("Common", "Charholi"),     # to_date shifted to 2098-12-30
    ("Common", "Pune"),         # to_date shifted to 2098-12-30
    ("Common", "Akola"),        # to_date shifted to 2098-12-30
    ("Common", "Delhi"),        # to_date shifted to 2098-12-30

    # ── Supplier pricing — re-use locations with shifted to_date ────
    ("Supplier", "Charholi"),   # to_date shifted to 2098-12-30
    ("Supplier", "Pune"),       # to_date shifted to 2098-12-30
    ("Supplier", "Mumbai"),     # to_date shifted to 2098-12-30
    ("Supplier", "Akola"),      # to_date shifted to 2098-12-30

    # ── Additional rounds — 3rd pass with 2097-12-30 ────────────────
    ("Common", "Mumbai"),
    ("Common", "Agra"),
    ("Common", "Indore"),
    ("Supplier", "Delhi"),
    ("Supplier", "Agra"),
    ("Supplier", "Indore"),
]


def build_cbr_api_payload(
    pricing_type_ref_id: int,
    location_ref_id: int,
    from_date: str = "2026-06-02T00:00:00Z",
    to_date: str = "2099-12-30T18:30:00Z",
) -> dict:
    """
    Build a single API payload for Commodity Base Rate (header-only).

    Args:
        pricing_type_ref_id: FK ID for Pricing Type (118=Common, 120=Supplier)
        location_ref_id: FK ID for Location dropdown
        from_date: ISO datetime string (server auto-sets on create)
        to_date: ISO datetime string (default sentinel: 2099-12-30T18:30:00Z)

    Returns:
        dict: API payload with attribute_name set to "Commodity Base Rate"
    """
    return {
        "id": "",
        "attribute_name": "Commodity Base Rate",
        "pricing_type_ref_id": pricing_type_ref_id,
        "from_date": from_date,
        "to_date": to_date,
        "location_ref_id": location_ref_id,
    }


def generate_cbr_payloads(count: int = 10, offset: int = 0,
                          skip_location_ids: set = None,
                          used_combos: set = None) -> list:
    """
    Generate N API payloads for Commodity Base Rate.

    Resolves FK dropdown names to live ERP IDs using the ID maps.
    Validates that all FK fields resolve before building payloads.

    The unique constraint is (to_date, location_ref_id), so each location
    can appear in MULTIPLE entries as long as they have different to_dates.
    This function automatically shifts to_date years when a location would
    cause a duplicate.

    Args:
        count: Number of payloads to generate
        offset: Start index in the data pool (to skip already-used entries)
        skip_location_ids: Set of location_ref_id integers that already have
                          entries with the default to_date=2099-12-30.
                          Merged with CBR_USED_LOCATION_IDS. Typically
                          populated by fetching existing CBR entries from
                          the API at runtime. (Legacy parameter — prefer
                          used_combos for complete dedup.)
        used_combos: Set of (year, location_ref_id) tuples already in use.
                    This is the COMPLETE dedup set from the API — it tracks
                    ALL (to_date, location) pairs across ALL years, not just
                    the default to_date. Takes priority over skip_location_ids.
                    Typically populated by fetch_used_combos_from_api() in
                    batch_create.py.

    Returns:
        list[dict]: List of API payloads ready for batch_create
    """
    pool = COMMODITY_BASE_RATE_API_DATA
    payloads = []

    # Build set of (to_date_year, location_ref_id) combos already in use
    combo_set = set()  # Format: (year, location_id) for fast lookup

    # 1. Start with static baseline (default to_date=2099 for known locations)
    for loc_id in CBR_USED_LOCATION_IDS:
        combo_set.add((2099, loc_id))

    # 2. Merge legacy skip_location_ids (these all have default to_date=2099)
    if skip_location_ids:
        for loc_id in skip_location_ids:
            combo_set.add((2099, loc_id))

    # 3. Merge full combo set from dynamic API fetch (COMPLETE dedup)
    if used_combos:
        combo_set.update(used_combos)

    if combo_set:
        # Show summary of what we're deduping against
        years_in_use = sorted(set(y for y, _ in combo_set), reverse=True)
        print(f"  [DEDUP] {len(combo_set)} existing (year, location) combos to avoid")
        for y in years_in_use[:5]:  # Show top 5 years
            locs = sorted(l for yy, l in combo_set if yy == y)
            print(f"  [DEDUP]   Year {y}: {len(locs)} locations — {locs}")
        if len(years_in_use) > 5:
            print(f"  [DEDUP]   ... and {len(years_in_use) - 5} more years")

    skipped = 0

    for i in range(count):
        idx = (offset + i) % len(pool)
        entry = pool[idx]

        pricing_type_name, location_name = entry

        # Resolve FK codes to ERP IDs
        pt_id = PRICING_TYPE_ID_MAP.get(pricing_type_name)
        loc_id = LOCATION_ID_MAP.get(location_name)

        if pt_id is None:
            print(f"  WARNING: Pricing Type '{pricing_type_name}' not found in "
                  f"PRICING_TYPE_ID_MAP, skipping")
            continue
        if loc_id is None:
            print(f"  WARNING: Location '{location_name}' not found in "
                  f"LOCATION_ID_MAP, skipping")
            continue

        # Find the earliest available to_date year for this location
        # that doesn't conflict with existing entries
        year = 2099
        while (year, loc_id) in combo_set and year >= 2026:
            year -= 1

        if year < 2026:
            print(f"  WARNING: All to_date years exhausted for location "
                  f"'{location_name}' (id={loc_id}), skipping")
            skipped += 1
            continue

        to_date = f"{year}-12-30T18:30:00Z"

        payloads.append(
            build_cbr_api_payload(
                pricing_type_ref_id=pt_id,
                location_ref_id=loc_id,
                to_date=to_date,
            )
        )
        # Mark this combo as now used (prevents reuse within this batch)
        combo_set.add((year, loc_id))

    if skipped:
        print(f"  [DEDUP] Skipped {skipped} data pool entries with exhausted locations")

    if len(payloads) < count:
        print(f"  WARNING: Could only generate {len(payloads)} payloads "
              f"(requested {count}). Data pool may be exhausted — add more "
              f"(pricing_type, location) combos.")

    return payloads
