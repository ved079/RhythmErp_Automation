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
import string
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

# Item Master options (clean/useful items — excluding test/None/auto-generated items)
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

# Quality Parameter options (production-use only — excludes Test_QP entries)
QUALITY_PARAM_ID_MAP = {
    "Moisture Content": 1,
    "Protein Content": 2,
    "Foreign Matter": 3,
    "Damaged Grains": 4,
    "Broken Grains": 5,
    "Weeviled Grains": 6,
    "Admixture Content": 7,
    "Oil Content": 8,
    "Ash Content": 9,
    "Fiber Content": 10,
    "Gluten Content": 11,
    "Fat Content": 12,
    "Hardness Index": 13,
    "Test Weight": 14,
    "Impurities": 15,
    "Insect Damage": 16,
    "Mould Damage": 17,
    "Germination Rate": 18,
    "Shrivelled Grains": 19,
    "Chalky Grains": 20,
    "Bulk Density": 23,
    "Particle Size": 24,
    "Color Value": 27,
    "Hardness": 28,
    "Texture Score": 29,
    "Thousand Grain Weight": 30,
    "Hectoliter Weight": 31,
    "Grain Uniformity": 32,
    "Length-Breadth Ratio": 33,
    "Grain Whiteness": 34,
}

# Items already used in CQP (item_ref_id values with to_date=2099-12-30T18:30:00Z)
# These items CANNOT be reused with the same to_date; they can be reused
# with a different to_date if needed.
# Updated 2026-06-02: Added 94, 101, 102, 103, 130 (discovered via API
# duplicate errors).  Also added 131-135 (created by batch run on 2026-06-02).
# NOTE: The batch_create.py script now also fetches used items dynamically
# from the API at runtime — this static list is a safety net / baseline.
CQP_USED_ITEM_IDS = {85, 86, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98,
                     99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 129,
                     130, 131, 132, 133, 134, 135}


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
    # ── Agricultural Commodities — Cereals & Grains ────────────────────
    ("Sugarcane", "Purchase", "Rev-001", [
        ("Moisture Content", "10", "15", True, "1.0"),
        ("Foreign Matter", "0", "2", True, "0.5"),
        ("Fiber Content", "10", "14", True, "1.5"),
    ]),
    # NOTE: Groundnut(95), Sunflower Seeds(96), Mustard Seeds(97), Green Gram(98),
    # Black Gram(99), Chickpeas(100) are already used in CQP with to_date=2099-12-30.
    # Using only items NOT in CQP_USED_ITEM_IDS to avoid unique constraint violations.
    ("Turmeric Powder", "Purchase", "Rev-001", [
        ("Moisture Content", "8", "10", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
        ("Color Value", "70", "90", True, "2.0"),
    ]),
    ("Red Chilli", "Purchase", "Rev-001", [
        ("Moisture Content", "10", "14", True, "1.0"),
        ("Color Value", "60", "80", True, "2.0"),
        ("Foreign Matter", "0", "2", True, "0.5"),
    ]),
    ("Coriander Seeds", "Sales", "Rev-001", [
        ("Moisture Content", "6", "9", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
        ("Damaged Grains", "0", "2", True, "1.0"),
    ]),

    # NOTE: Onion(105), Potato(106), Tomato(107), Mango(108) are already used
    # in CQP with to_date=2099-12-30. Skipped to avoid unique constraint violations.

    # ── Construction & Industrial Materials ─────────────────────────────
    ("Iron Pipe", "Purchase", "Rev-001", [
        ("Hardness Index", "50", "70", True, "1.0"),
        ("Impurities", "0", "2", True, "0.5"),
    ]),
    ("Cement Bag", "Purchase", "Rev-001", [
        ("Moisture Content", "0", "1", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
        ("Test Weight", "1440", "1500", True, "1.0"),
    ]),
    ("Paint Bucket", "Purchase", "Rev-001", [
        ("Moisture Content", "0", "2", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Nut Bolt Set", "Purchase", "Rev-001", [
        ("Hardness Index", "55", "75", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("PVC Pipe", "Sales", "Rev-001", [
        ("Hardness Index", "40", "60", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Drill Machine", "Purchase", "Rev-001", [
        ("Hardness Index", "60", "80", True, "1.0"),
    ]),
    ("Hammer", "Purchase", "Rev-001", [
        ("Hardness Index", "55", "75", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Welding Rod", "Purchase", "Rev-001", [
        ("Moisture Content", "0", "1", True, "1.0"),
        ("Impurities", "0", "2", True, "0.5"),
    ]),
    ("Measuring Tape", "Sales", "Rev-001", [
        ("Impurities", "0", "1", True, "0.5"),
    ]),

    # ── FMCG / Household Products ──────────────────────────────────────
    ("Bath Soap", "Purchase", "Rev-001", [
        ("Moisture Content", "8", "15", True, "1.0"),
        ("Fat Content", "50", "70", True, "2.0"),
    ]),
    ("Shampoo Bottle", "Purchase", "Rev-001", [
        ("Moisture Content", "60", "80", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("Hair Oil", "Sales", "Rev-001", [
        ("Moisture Content", "0", "2", True, "1.0"),
        ("Oil Content", "90", "100", True, "2.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("Toothpaste", "Purchase", "Rev-001", [
        ("Moisture Content", "20", "35", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("Detergent Powder", "Purchase", "Rev-001", [
        ("Moisture Content", "5", "12", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("Dish Wash Liquid", "Sales", "Rev-001", [
        ("Moisture Content", "65", "80", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("Floor Cleaner", "Purchase", "Rev-001", [
        ("Moisture Content", "70", "85", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("Hand Wash", "Purchase", "Rev-001", [
        ("Moisture Content", "65", "80", True, "1.0"),
    ]),
    ("Face Cream", "Sales", "Rev-001", [
        ("Moisture Content", "30", "50", True, "1.0"),
        ("Fat Content", "15", "30", True, "2.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("Talcum Powder", "Purchase", "Rev-001", [
        ("Moisture Content", "0", "5", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),

    # ── Electrical & Appliances ────────────────────────────────────────
    ("LED Bulb", "Purchase", "Rev-001", [
        ("Impurities", "0", "1", True, "0.5"),
        ("Hardness Index", "30", "50", True, "1.0"),
    ]),
    ("Ceiling Fan", "Purchase", "Rev-001", [
        ("Hardness Index", "40", "60", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Extension Board", "Sales", "Rev-001", [
        ("Hardness Index", "35", "55", True, "1.0"),
    ]),
    ("Electric Wire", "Purchase", "Rev-001", [
        ("Impurities", "0", "1", True, "0.5"),
        ("Moisture Content", "0", "1", True, "1.0"),
    ]),
    ("Switch Board", "Purchase", "Rev-001", [
        ("Hardness Index", "35", "55", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Water Heater", "Purchase", "Rev-001", [
        ("Hardness Index", "45", "65", True, "1.0"),
        ("Impurities", "0", "2", True, "0.5"),
    ]),
    ("Mixer Grinder", "Sales", "Rev-001", [
        ("Hardness Index", "50", "70", True, "1.0"),
    ]),
    ("Electric Kettle", "Purchase", "Rev-001", [
        ("Hardness Index", "40", "60", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Inverter Battery", "Purchase", "Rev-001", [
        ("Moisture Content", "0", "2", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Solar Panel", "Sales", "Rev-001", [
        ("Hardness Index", "40", "60", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),

    # ── Office & Stationery ────────────────────────────────────────────
    ("A4 Paper", "Purchase", "Rev-001", [
        ("Moisture Content", "4", "7", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("Ball Pen", "Purchase", "Rev-001", [
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Stapler", "Purchase", "Rev-001", [
        ("Hardness Index", "45", "65", True, "1.0"),
    ]),
    ("Printer Ink", "Sales", "Rev-001", [
        ("Moisture Content", "50", "70", True, "1.0"),
        ("Foreign Matter", "0", "1", True, "0.5"),
    ]),
    ("File Folder", "Purchase", "Rev-001", [
        ("Moisture Content", "4", "8", True, "1.0"),
    ]),
    ("Marker Pen", "Purchase", "Rev-001", [
        ("Moisture Content", "50", "70", True, "1.0"),
    ]),
    ("Whiteboard", "Sales", "Rev-001", [
        ("Hardness Index", "30", "50", True, "1.0"),
        ("Impurities", "0", "1", True, "0.5"),
    ]),
    ("Calculator", "Purchase", "Rev-001", [
        ("Hardness Index", "35", "55", True, "1.0"),
    ]),

    # ── Additional items — Stock movement transaction types ──────────────
    # These use the same item but with different transaction types.
    # Since the unique constraint is (item_ref_id, to_date), these entries
    # would fail with default to_date=2099-12-30. They use a different
    # to_date to avoid the constraint. The batch_create script handles
    # this by adjusting to_date automatically.
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
                            skip_item_ids: set = None) -> list:
    """
    Generate N API payloads for Commodity Quality Parameter.

    Resolves FK dropdown names to live ERP IDs using the ID maps.
    Validates that all FK fields resolve before building payloads.
    Skips items whose item_ref_id is in skip_item_ids (to avoid
    duplicate (item_ref_id, to_date) constraint violations).

    Args:
        count: Number of payloads to generate
        offset: Start index in the data pool (to skip already-used entries)
        skip_item_ids: Set of item_ref_id integers to skip (merged with
                       CQP_USED_ITEM_IDS).  Typically populated by
                       fetching existing CQP entries from the API at runtime.

    Returns:
        list[dict]: List of API payloads ready for batch_create
    """
    pool = COMMODITY_QUALITY_PARAMETER_API_DATA
    payloads = []

    # Merge static + dynamic skip sets
    used_items = set(CQP_USED_ITEM_IDS)
    if skip_item_ids:
        used_items.update(skip_item_ids)

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
        item_id = ITEM_ID_MAP.get(item_name)
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
            qp_id = QUALITY_PARAM_ID_MAP.get(qp_name)
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
