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

# Transaction Type options (8 total) — fallback only; resolved live at runtime
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

# Fallback maps — used only when live FK resolution fails
# These are tenant-specific; prefer live resolution via FkResolver
ITEM_ID_MAP = {}
QUALITY_PARAM_ID_MAP = {}

STEPPER_NAME = "Item Quality Parameter Details"


def _yesterday_1830z() -> str:
    """Return yesterday at 18:30:00Z — midnight IST, used as from_date so ERP date filters pass."""
    from datetime import datetime, timedelta, timezone
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    return f"{yesterday}T18:30:00Z"


def build_cqp_api_payload(
    item_ref_id: int,
    transaction_type: int,
    quality_params: list,
    to_date: str = "2099-12-30T18:30:00Z",
    revision_status: str = None,
) -> dict:
    return {
        "id": "",
        "attribute_name": "Commodity Quality Parameter",
        "item_ref_id": item_ref_id,
        "transaction_type": transaction_type,
        "from_date": _yesterday_1830z(),
        "to_date": to_date,
        "revision_status": revision_status,
        "details": [],
        "children": [
            {
                "stepper_name": STEPPER_NAME,
                "is_stepper": True,
                "details": quality_params,
                "children": [],
            }
        ],
    }


def _random_detail_rows(quality_param_ids: list) -> list:
    """Pick 1–3 random quality params and generate random min/max/multiplier rows."""
    n = random.randint(1, min(3, len(quality_param_ids)))
    chosen = random.sample(quality_param_ids, n)
    rows = []
    for qp_id in chosen:
        min_val = 1
        max_val = 100
        rows.append({
            "quality_type": qp_id,
            "min_quality_value": min_val,
            "max_quality_value": max_val,
            "rate_percentage": False,
            "multiplier": 1,
        })
    return rows


def generate_cqp_payloads(count: int = 10, offset: int = 0,
                           skip_item_ids: set = None, fk_ids: dict = None) -> list:
    """
    Generate N API payloads for Commodity Quality Parameter.

    Fully dynamic — uses live FK IDs from fk_ids (resolved by FkResolver).
    Transaction Type is always Purchase.
    Each record gets 1–3 random quality parameter rows.
    Skips item IDs already used in existing CQP entries.

    Args:
        count: Number of payloads to generate
        offset: Ignored (kept for API compatibility)
        skip_item_ids: Set of item_ref_id integers already in CQP
        fk_ids: Resolved FK maps: {"item_ref_id": {name: id, ...},
                                    "quality_type": {name: id, ...},
                                    "transaction_type": {name: id, ...}}
    """
    fk_ids = fk_ids or {}
    item_id_map = fk_ids.get("item_ref_id") or ITEM_ID_MAP
    quality_param_id_map = fk_ids.get("quality_type") or QUALITY_PARAM_ID_MAP
    txn_type_map = fk_ids.get("transaction_type") or TRANSACTION_TYPE_ID_MAP

    # Always Purchase
    purchase_id = txn_type_map.get("Purchase", 154)

    # Available item IDs excluding already-used ones
    used_items = set(skip_item_ids or [])
    available_item_ids = [
        iid for iid in item_id_map.values() if iid not in used_items
    ]
    quality_param_ids = list(quality_param_id_map.values())

    if not available_item_ids:
        print("  WARNING: No available item IDs — all items already have CQP entries.")
        return []
    if not quality_param_ids:
        print("  WARNING: No quality parameter IDs resolved. Cannot generate detail rows.")
        return []

    if used_items:
        print(f"  [DEDUP] Skipping {len(used_items)} already-used item IDs")

    # Shuffle so we don't always pick the same items in the same order
    shuffled_items = available_item_ids[:]
    random.shuffle(shuffled_items)

    payloads = []
    for item_id in shuffled_items:
        if len(payloads) >= count:
            break
        detail_rows = _random_detail_rows(quality_param_ids)
        payloads.append(
            build_cqp_api_payload(
                item_ref_id=item_id,
                transaction_type=purchase_id,
                quality_params=detail_rows,
            )
        )

    if len(payloads) < count:
        print(f"  WARNING: Could only generate {len(payloads)}/{count} payloads "
              f"— not enough unused items.")

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

TRANSACTION_TYPE_NAMES = dict(TRANSACTION_TYPE_ID_MAP)

SCREEN_NAME_FIELDS = {
    "item_ref_id": "Item Master",
    "quality_type": "Quality Parameter Master",
}

DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS = {
    "transaction_type": TRANSACTION_TYPE_ID_MAP,
}


def get_fk_screen_mapping():
    """Return FK field → screen name mapping for live FkResolver resolution."""
    return {
        "item_ref_id": "Item Master",
        "quality_type": "Quality Parameter",
        "transaction_type": "Transaction Type",
    }


def generate_batch_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None, offset: int = 0, existing_entries: list = None, config: dict = None) -> list:
    fk_ids = dropdown_ids or {}

    # When fill_all=True: skip items that already have CQP entries,
    # generate for all remaining items regardless of count.
    if (config or {}).get("fill_all"):
        # Collect used item IDs from existing listing entries
        used_ids: set = set()
        for entry in (existing_entries or []):
            iid = entry.get("item_ref_id")
            if iid is not None:
                try:
                    used_ids.add(int(iid))
                except (ValueError, TypeError):
                    pass
        item_id_map = fk_ids.get("item_ref_id") or ITEM_ID_MAP
        # Generate for every item not already present
        available = [iid for iid in item_id_map.values() if iid not in used_ids]
        fill_count = len(available)
        return generate_cqp_payloads(count=fill_count, skip_item_ids=used_ids, fk_ids=fk_ids)

    return generate_cqp_payloads(count=count, offset=offset, fk_ids=dropdown_ids)
