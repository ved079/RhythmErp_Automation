"""
commodity_quality_parameter_data.py
------------------------------------
Dynamic test data generators for Commodity Quality Parameter automation.
All values are generated at runtime — no hardcoded test data.

CQP Form fields:
  HEADER:
    - Item Name            (mat-select, required, searchable)
    - Transaction Type     (mat-select, required, 8 options)
    - From Date            (datepicker, required, DD/MM/YYYY)
    - To Date              (datepicker, required, DD/MM/YYYY)
    - Revision Status      (text, optional)

  DETAIL GRID:
    - Quality Parameter    (mat-select, required, searchable)
    - Min Quality Value    (text, required, max 255)
    - Max Quality Value    (text, required, max 255)
    - Is Rate/Percentage   (toggle, required, Yes/No)
    - Multiplier           (text, required, max 255)

Transaction Type Options (8):
  'Return Stock Down', 'Stock Transfer Down', 'Stock Down',
  'Return Stock Up', 'Stock Transfer Up', 'Stock Up',
  Sales, Purchase
"""

import random
from datetime import datetime, timedelta


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

TRANSACTION_TYPES = [
    "'Return Stock Down'",
    "'Stock Transfer Down'",
    "'Stock Down'",
    "'Return Stock Up'",
    "'Stock Transfer Up'",
    "'Stock Up'",
    "Sales",
    "Purchase",
]


# ──────────────────────────────────────────────
# Valid Data Generators — Header
# ──────────────────────────────────────────────

def generate_from_date():
    """Generate a From Date string in DD/MM/YYYY format (current date)."""
    return datetime.now().strftime("%d/%m/%Y")


def generate_to_date():
    """Generate a To Date string in DD/MM/YYYY format (far future).
    Matches the ERP's auto-fill sentinel of 30/12/2099.
    """
    return "30/12/2099"


def generate_revision_status(prefix="AutoRev"):
    """Generate a Revision Status string."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_header_data(
    item_name=None,
    transaction_type=None,
    from_date=None,
    to_date=None,
    revision_status=None,
):
    """Generate a complete dict of valid CQP header data.

    If item_name or transaction_type is None, the page object
    will select a random option from the dropdown.

    NOTE: from_date is set to None by default because the ERP
    auto-fills From Date with today's date.  The page object
    skips filling it unless from_date_force=True is set.
    """
    data = {
        "item_name": item_name,         # None = auto-select random
        "transaction_type": transaction_type,  # None = auto-select random
        "from_date": None,              # None = skip (ERP auto-fills today)
        "to_date": to_date or generate_to_date(),  # Default: 30/12/2099
        "revision_status": revision_status,  # None = skip optional field
    }
    return data


# ──────────────────────────────────────────────
# Valid Data Generators — Detail Grid
# ──────────────────────────────────────────────

def generate_min_quality_value(prefix="Min"):
    """Generate a Min Quality Value string."""
    rand = random.uniform(0.1, 50.0)
    return f"{rand:.2f}"


def generate_max_quality_value(prefix="Max"):
    """Generate a Max Quality Value string (always > min)."""
    rand = random.uniform(51.0, 100.0)
    return f"{rand:.2f}"


def generate_multiplier():
    """Generate a Multiplier value string."""
    rand = random.uniform(0.1, 10.0)
    return f"{rand:.2f}"


def generate_valid_detail_data(
    quality_parameter=None,
    min_quality_value=None,
    max_quality_value=None,
    is_rate_percentage=False,
    multiplier=None,
):
    """Generate a complete dict of valid CQP detail row data.

    If quality_parameter is None, the page object will
    select a random option from the dropdown.
    """
    data = {
        "quality_parameter": quality_parameter,  # None = auto-select random
        "min_quality_value": min_quality_value or generate_min_quality_value(),
        "max_quality_value": max_quality_value or generate_max_quality_value(),
        "is_rate_percentage": is_rate_percentage,
        "multiplier": multiplier or generate_multiplier(),
    }
    return data


def generate_valid_cqp_data():
    """Generate complete header + detail data for a full CQP record."""
    return {
        "header": generate_valid_header_data(),
        "detail": generate_valid_detail_data(),
    }


# ──────────────────────────────────────────────
# Partial Data Generators (missing fields)
# ──────────────────────────────────────────────

def generate_header_no_item_name():
    """Return header data with item_name explicitly set to skip."""
    return {
        "item_name": None,
        "select_item_name": False,  # Don't select at all
        "transaction_type": None,   # Auto-select random
        "from_date": None,          # Skip (ERP auto-fills)
        "to_date": generate_to_date(),
    }


def generate_header_no_transaction_type():
    """Return header data with transaction_type explicitly set to skip."""
    return {
        "item_name": None,          # Auto-select random
        "transaction_type": None,
        "select_transaction_type": False,  # Don't select at all
        "from_date": None,          # Skip (ERP auto-fills)
        "to_date": generate_to_date(),
    }


def generate_empty_header_data():
    """Return header data with all fields skipped."""
    return {
        "item_name": None,
        "select_item_name": False,
        "transaction_type": None,
        "select_transaction_type": False,
        "from_date": "",
        "to_date": "",
        "revision_status": "",
    }


def generate_detail_no_qp():
    """Return detail data with quality_parameter explicitly set to skip."""
    return {
        "quality_parameter": None,
        "select_qp": False,  # Don't select at all
        "min_quality_value": generate_min_quality_value(),
        "max_quality_value": generate_max_quality_value(),
        "is_rate_percentage": False,
        "multiplier": generate_multiplier(),
    }


def generate_empty_detail_data():
    """Return detail data with all fields empty."""
    return {
        "quality_parameter": None,
        "select_qp": False,
        "min_quality_value": "",
        "max_quality_value": "",
        "is_rate_percentage": False,
        "multiplier": "",
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_string_255():
    """Generate a string of exactly 255 characters."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters."""
    return "A" * 256


def generate_long_string(length=300):
    """Generate a string of specified length."""
    return "X" * length


def generate_special_char_value():
    """Generate a value with common special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"CQP{special}"


def generate_sql_injection_value():
    """Generate SQL injection strings to test input sanitization."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE commodity_quality; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM items --",
        "\" OR \"1\"=\"1",
    ]
    return random.choice(injections)


def generate_xss_value():
    """Generate XSS payload strings to test input sanitization."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
    ]
    return random.choice(payloads)


def generate_unicode_value():
    """Generate a value with unicode/international characters."""
    unicode_samples = [
        "CQP\u00e9",           # Latin é
        "CQP\u00fc",           # Latin ü
        "\u4e2d\u6587\u53c2\u6570",  # 中文参数
        "\u0917\u0941\u0923\u0935\u0924\u094d\u0924\u093e",  # गुणवत्ता
        "\u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e",  # качество
    ]
    return random.choice(unicode_samples)


def generate_negative_number():
    """Generate a negative number string."""
    return str(random.uniform(-100.0, -0.1))


def generate_zero_value():
    """Generate a zero value string."""
    return "0"


def generate_very_large_number():
    """Generate a very large number string."""
    return "999999999.99"


# ──────────────────────────────────────────────
# Transaction Type helpers
# ──────────────────────────────────────────────

def get_random_transaction_type():
    """Return a random Transaction Type from the known list."""
    return random.choice(TRANSACTION_TYPES)


def get_all_transaction_types():
    """Return all Transaction Type options."""
    return TRANSACTION_TYPES.copy()


# ═══════════════════════════════════════════════════════════════════════════════
#  API Batch Create — Data Pool + Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Screen structure (discovered 2026-06-02):
#   Commodity Quality Parameter:
#     HEADER fields:
#       item_ref_id*      (FK dropdown → Item Master table)
#       transaction_type* (FK dropdown → 8 hardcoded options)
#       from_date*        (datetime, auto-filled to current timestamp on create)
#       to_date*          (datetime, sentinel: 2099-12-30T18:30:00Z)
#       revision_status   (text, optional)
#
#     DETAIL GRID — "Define Item Quality Parameter Details" (is_stepper=true, is_grid=true):
#       quality_type*       (FK dropdown → Quality Parameter table)
#       min_quality_value*  (decimal string, pattern: ^\d+(\.\d+)?$)
#       max_quality_value*  (decimal string, pattern: ^\d+(\.\d+)?$)
#       rate_percentage*    (toggle, default: false)
#       multiplier*         (decimal string, pattern: ^\d+(\.\d+)?$)
#
#   UNIQUE CONSTRAINT: (item_ref_id, to_date) — duplicate combos are rejected.
#
#   PAYLOAD STRUCTURE (stepper with grid detail):
#     {
#       "id": "",
#       "attribute_name": "Commodity Quality Parameter",
#       "item_ref_id": <int>,
#       "transaction_type": <int>,
#       "from_date": "<ISO datetime>",   // server auto-sets on create
#       "to_date": "2099-12-30T18:30:00Z",
#       "revision_status": "<str or null>",
#       "details": [],
#       "children": [
#         {
#           "stepper_name": "Define Item Quality Parameter Details",
#           "is_stepper": true,
#           "details": [                    <--- DETAIL ROWS GO HERE
#             {
#               "quality_type": <int>,
#               "min_quality_value": "<str>",
#               "max_quality_value": "<str>",
#               "rate_percentage": <bool>,
#               "multiplier": "<str>"
#             },
#             ...
#           ],
#           "children": []                  <--- NOT used for grid rows
#         }
#       ]
#     }
#
# FK Dropdown mappings (live from ERP as of 2026-06-02):
#
#   Item Master (item_ref_id) — 77 items total; 20 already used in CQP.
#   Transaction Type — 8 options (see TRANSACTION_TYPE_ID_MAP below).
#   Quality Parameter (quality_type) — 34 options (see QUALITY_PARAM_ID_MAP below).
#
# Existing entries in ERP (as of 2026-06-02, 23 total):
#   IDs 49-73, covering item_ref_ids: 85,86,88,89,90,91,92,93,95,96,97,98,
#   99,100,104,105,106,107,108,129. All use to_date=2099-12-30T18:30:00Z.
#   None have quality parameter detail rows (all stepper details=[]).
#
# Data pool below covers UNUSED items with relevant quality parameters per
# commodity category, ensuring each (item_ref_id, to_date) combo is unique.
# ═══════════════════════════════════════════════════════════════════════════════

# ── FK ID Mappings (from live ERP) ────────────────────────────────────

# Transaction Type options (8 total)
TRANSACTION_TYPE_ID_MAP = {
    "Purchase": 154,
    "Sales": 155,
    "Stock Up": 217,
    "Stock Transfer Up": 218,
    "Return Stock Up": 219,
    "Stock Down": 220,
    "Stock Transfer Down": 221,
    "Return Stock Down": 222,
}

# Item Master options (tenant 711 — auto-computed attribute names)
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

# Quality Parameter options (tenant 711)
QUALITY_PARAM_ID_MAP = {
    "Bulk Density": 1,
    "Particle Size": 2,
    "Color Value": 3,
    "Hardness": 4,
    "Texture Score": 5,
}

# Items already used in CQP are discovered dynamically via the API at runtime.
# No static CQP_USED_ITEM_IDS — the batch script fetches existing entries
# and passes skip_item_ids to the payload generator.


# ── Data Pool ─────────────────────────────────────────────────────────
# Each entry defines a complete CQP record:
#   (item_name, transaction_type, revision_status, quality_params)
#
# quality_params is a list of tuples:
#   (quality_parameter_name, min_value, max_value, rate_percentage, multiplier)
#
# The min_value, max_value, and multiplier are strings matching the pattern
# ^\d+(\.\d+)?$ as required by the ERP validation.
#
# Items are chosen from ITEM_ID_MAP that are NOT in CQP_USED_ITEM_IDS,
# ensuring no (item_ref_id, to_date) duplicate conflict with the sentinel
# to_date=2099-12-30T18:30:00Z.

COMMODITY_QUALITY_PARAMETER_API_DATA = [
    ("Spinach Flexible Green Huge Droplet", "Purchase", "Rev-001", [
        ("Bulk Density", "10", "15", True, "1.0"),
        ("Particle Size", "0.5", "2.0", True, "0.5"),
        ("Color Value", "70", "90", True, "2.0"),
    ]),
    ("Cherry Flexible Green Huge Droplet", "Purchase", "Rev-001", [
        ("Bulk Density", "12", "18", True, "1.0"),
        ("Hardness", "5", "8", True, "1.5"),
    ]),
    ("Ginger Hollow Orange Minute Heart", "Purchase", "Rev-001", [
        ("Color Value", "60", "80", True, "2.0"),
        ("Texture Score", "3", "7", True, "1.0"),
        ("Particle Size", "1.0", "3.0", True, "0.5"),
    ]),
    ("Ginger Fuzzy Ruby Teeny Heart", "Sales", "Rev-001", [
        ("Bulk Density", "8", "14", True, "1.0"),
        ("Color Value", "65", "85", True, "2.0"),
    ]),
    ("Apple Stiff Blue Deep Heart", "Purchase", "Rev-001", [
        ("Hardness", "4", "7", True, "1.5"),
        ("Texture Score", "5", "9", True, "1.0"),
    ]),
    ("Spinach Fuzzy Magenta Small Circle", "Sales", "Rev-001", [
        ("Bulk Density", "11", "16", True, "1.0"),
        ("Particle Size", "0.5", "1.5", True, "0.5"),
    ]),
    ("Banana Hollow Peach Enormous Crescent", "Purchase", "Rev-001", [
        ("Texture Score", "2", "6", True, "1.0"),
        ("Color Value", "75", "95", True, "2.0"),
        ("Hardness", "3", "6", True, "1.5"),
    ]),
    ("Apple Bumpy Charcoal Broad Ring", "Purchase", "Rev-001", [
        ("Hardness", "5", "9", True, "1.5"),
        ("Particle Size", "0.5", "2.0", True, "0.5"),
    ]),
    ("Onion Silky Brown Teeny Hexagon", "Sales", "Rev-001", [
        ("Bulk Density", "9", "15", True, "1.0"),
        ("Color Value", "60", "80", True, "2.0"),
        ("Texture Score", "4", "8", True, "1.0"),
    ]),
    ("Papaya Stiff Cream Micro Loop", "Purchase", "Rev-001", [
        ("Bulk Density", "10", "17", True, "1.0"),
        ("Hardness", "6", "10", True, "1.5"),
        ("Color Value", "70", "90", True, "2.0"),
        ("Texture Score", "3", "7", True, "1.0"),
    ]),
]


def build_cqp_api_payload(
    item_ref_id: int,
    transaction_type: int,
    quality_params: list,
    from_date: str = "2026-06-02T00:00:00Z",
    to_date: str = "2099-12-30T18:30:00Z",
    revision_status: str = None,
) -> dict:
    """
    Build a single API payload for Commodity Quality Parameter.

    Args:
        item_ref_id: FK ID for Item Name dropdown (e.g., 106 for Potato)
        transaction_type: FK ID for Transaction Type dropdown (e.g., 154 for Purchase)
        quality_params: List of detail row dicts, each with keys:
            quality_type (int), min_quality_value (str), max_quality_value (str),
            rate_percentage (bool), multiplier (str)
        from_date: ISO datetime string (server auto-sets on create)
        to_date: ISO datetime string (default sentinel: 2099-12-30T18:30:00Z)
        revision_status: Optional revision label (str or None)

    Returns:
        dict: API payload with attribute_name set to "Commodity Quality Parameter"
    """
    return {
        "id": "",
        "attribute_name": "Commodity Quality Parameter",
        "item_ref_id": item_ref_id,
        "transaction_type": transaction_type,
        "from_date": from_date,
        "to_date": to_date,
        "revision_status": revision_status,
        "details": [],
        "children": [
            {
                "stepper_name": "Define Item Quality Parameter Details",
                "is_stepper": True,
                "details": quality_params,
                "children": [],
            }
        ],
    }


def generate_cqp_payloads(count: int = 10, offset: int = 0,
                            skip_item_ids: set = None, fk_ids: dict = None) -> list:
    """
    Generate N API payloads for Commodity Quality Parameter.

    Resolves FK dropdown names to live ERP IDs via FkResolver results
    (fk_ids), falling back to hardcoded ID maps if not available.
    Skips items whose item_ref_id is in skip_item_ids (to avoid
    duplicate (item_ref_id, to_date) constraint violations).

    Args:
        count: Number of payloads to generate
        offset: Start index in the data pool (to skip already-used entries)
        skip_item_ids: Set of item_ref_id integers to skip. Typically
                       populated by fetching existing CQP entries from
                       the API at runtime.
        fk_ids: Optional dict of resolved FK IDs, e.g.
                {"item_ref_id": {"Sugarcane": 94, ...},
                 "quality_type": {"Moisture Content": 1, ...}}

    Returns:
        list[dict]: List of API payloads ready for batch_create
    """
    fk_ids = fk_ids or {}
    item_id_map = fk_ids.get("item_ref_id", ITEM_ID_MAP)
    quality_param_id_map = fk_ids.get("quality_type", QUALITY_PARAM_ID_MAP)

    pool = COMMODITY_QUALITY_PARAMETER_API_DATA
    payloads = []

    used_items = set(skip_item_ids or [])
    if used_items:
        print(f"  [DEDUP] Skipping {len(used_items)} already-used item IDs: "
              f"{sorted(used_items)}")

    i = 0
    scan_idx = offset
    skipped = 0

    while len(payloads) < count and scan_idx < (offset + len(pool) * 3):
        idx = scan_idx % len(pool)
        entry = pool[idx]
        scan_idx += 1

        item_name, txn_type_name, rev_status, qp_tuples = entry

        # Resolve FK codes to ERP IDs
        item_id = item_id_map.get(item_name)
        txn_type_id = TRANSACTION_TYPE_ID_MAP.get(txn_type_name)

        if item_id is None:
            print(f"  WARNING: Item '{item_name}' not found in ITEM_ID_MAP, skipping")
            continue
        if txn_type_id is None:
            print(f"  WARNING: Transaction Type '{txn_type_name}' not found in TRANSACTION_TYPE_ID_MAP, skipping")
            continue

        # ── Skip items already used in CQP with default to_date ─────────
        if item_id in used_items:
            skipped += 1
            continue

        # Build detail rows from quality parameter tuples
        detail_rows = []
        for qp_name, min_val, max_val, rate_pct, mult in qp_tuples:
            qp_id = quality_param_id_map.get(qp_name)
            if qp_id is None:
                print(f"  WARNING: Quality Parameter '{qp_name}' not found in QUALITY_PARAM_ID_MAP, skipping row")
                continue
            detail_rows.append({
                "quality_type": qp_id,
                "min_quality_value": min_val,
                "max_quality_value": max_val,
                "rate_percentage": rate_pct,
                "multiplier": mult,
            })

        # Handle potential duplicate (item_ref_id, to_date) combos when wrapping
        # Use a different to_date for wrapped entries
        to_date = "2099-12-30T18:30:00Z"
        if scan_idx > (offset + len(pool)):
            wrap_count = (scan_idx - offset) // len(pool) + 1
            # Shift the to_date by 1 year per wrap to avoid unique constraint violation
            year = 2098 + wrap_count
            to_date = f"{year}-12-30T18:30:00Z"
            rev_status = f"{rev_status} (Batch {wrap_count})" if rev_status else f"Batch {wrap_count}"

        payloads.append(
            build_cqp_api_payload(
                item_ref_id=item_id,
                transaction_type=txn_type_id,
                quality_params=detail_rows,
                to_date=to_date,
                revision_status=rev_status,
            )
        )
        i += 1

    if skipped:
        print(f"  [DEDUP] Skipped {skipped} data pool entries with used item IDs")

    if len(payloads) < count:
        print(f"  WARNING: Could only generate {len(payloads)} payloads "
              f"(requested {count}). Data pool exhausted — add more items.")

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Commodity Quality Parameter has a STEPPER structure.
# Root fields: item_ref_id, transaction_type, from_date, to_date, revision_status
# Stepper child "Define Item Quality Parameter Details":
#   quality_type, min_quality_value, max_quality_value, rate_percentage, multiplier

FIELD_VALIDATION_RULES = {
    # Root fields
    "item_ref_id": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(ITEM_ID_MAP),
        "note": "FK to Item Master. ~35 items in clean pool.",
    },
    "transaction_type": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(TRANSACTION_TYPE_ID_MAP),
        "note": "FK to Transaction Type. 8 options: Purchase, Sales, Stock Up, etc.",
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
    "revision_status": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "Optional revision label.",
    },

    # Stepper child: "Define Item Quality Parameter Details" detail lines
    "quality_type": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(QUALITY_PARAM_ID_MAP),
        "note": "FK to Quality Parameter. 30 options in stepper detail lines.",
    },
    "min_quality_value": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Min value string. In stepper detail lines.",
    },
    "max_quality_value": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Max value string. In stepper detail lines.",
    },
    "rate_percentage": {
        "type": "toggle",
        "required": False,
        "default": False,
        "note": "Is Rate/Percentage toggle in stepper detail lines. Default: False.",
    },
    "multiplier": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Multiplier value string. In stepper detail lines.",
    },
}

ITEM_NAMES = dict(ITEM_ID_MAP)
TRANSACTION_TYPE_NAMES = dict(TRANSACTION_TYPE_ID_MAP)
QUALITY_PARAM_NAMES = dict(QUALITY_PARAM_ID_MAP)

SCREEN_NAME_FIELDS = {
    "item_ref_id": "Item Master",
    "quality_type": "Quality Parameter Master",
}

DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS = {
    "item_ref_id": ITEM_ID_MAP,
    "transaction_type": TRANSACTION_TYPE_ID_MAP,
    "quality_type": QUALITY_PARAM_ID_MAP,
}

STEPPER_NAME = "Define Item Quality Parameter Details"


def generate_batch_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None) -> list:
    """Generate a batch of unique Commodity Quality Parameter API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored for CQP (data pool provides item/param combinations).
        dropdown_ids: Override specific FK ID pools.

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    return generate_cqp_payloads(count=count)
