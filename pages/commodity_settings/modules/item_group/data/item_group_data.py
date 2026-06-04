"""
item_group_data.py
------------------
Dynamic test data generators for Item Group automation.
All values are generated at runtime — no hardcoded test data.

Item Group form fields:
  - Code          (text, required, max 255, alphanumericSpecial)
  - Description   (text, required, max 255, alphanumericSpecial)
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Valid Data Generators
# ──────────────────────────────────────────────

def generate_ig_code(prefix="AutoIG"):
    """Generate a random Item Group code with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_ig_description(prefix="Auto Desc"):
    """Generate a random Item Group description."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_ig_data(code_prefix="AutoIG", desc_prefix="Auto Desc"):
    """Generate a complete dict of valid Item Group data for Create form.

    Both Code and Description are required fields.
    """
    return {
        "code": generate_ig_code(code_prefix),
        "description": generate_ig_description(desc_prefix),
    }


def generate_valid_edit_data(code_prefix="EditIG", desc_prefix="Edit Desc"):
    """Generate valid data for Edit form — new code and description to update to."""
    return {
        "code": generate_ig_code(code_prefix),
        "description": generate_ig_description(desc_prefix),
    }


# ──────────────────────────────────────────────
# Partial Data Generators (one field missing/empty)
# ──────────────────────────────────────────────

def generate_empty_code_data():
    """Return dict with empty Code — for mandatory field validation."""
    return {
        "code": "",
        "description": generate_ig_description("HasDesc"),
    }


def generate_empty_description_data():
    """Return dict with empty Description — for mandatory field validation."""
    return {
        "code": generate_ig_code("HasCode"),
        "description": "",
    }


def generate_both_empty_data():
    """Return dict with both Code and Description empty."""
    return {
        "code": "",
        "description": "",
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_spaces_only_code_data(length=10):
    """Return dict with spaces-only Code."""
    return {
        "code": generate_spaces_only(length),
        "description": generate_ig_description("SpaceCode"),
    }


def generate_spaces_only_description_data(length=10):
    """Return dict with spaces-only Description."""
    return {
        "code": generate_ig_code("SpaceDesc"),
        "description": generate_spaces_only(length),
    }


def generate_duplicate_code_data(existing_code):
    """Return valid data using an existing code — for duplicate code test.

    BEH-004: Duplicate Codes are currently ALLOWED.
    Test documents current behavior as known bug — passes either way.
    """
    return {
        "code": existing_code,
        "description": generate_ig_description("DupCode"),
    }


def generate_string_255():
    """Generate a string of exactly 255 characters (typical max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds typical max)."""
    return "A" * 256


def generate_long_string(length=300):
    """Generate a string of specified length (for maxlength boundary testing)."""
    return "X" * length


def generate_special_char_code():
    """Generate a code with common special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"IG{special}"


def generate_special_char_data():
    """Return dict with special-character code and description."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return {
        "code": f"IG{special}",
        "description": f"Desc{special}",
    }


def generate_sql_injection_code():
    """Generate SQL injection strings to test input sanitization."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE item_groups; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM item_groups --",
        "\" OR \"1\"=\"1",
    ]
    return random.choice(injections)


def generate_sql_injection_data():
    """Return dict with SQL injection code."""
    return {
        "code": generate_sql_injection_code(),
        "description": generate_ig_description("SQLTest"),
    }


def generate_xss_code():
    """Generate XSS payload strings to test input sanitization."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
    ]
    return random.choice(payloads)


def generate_xss_data():
    """Return dict with XSS payload code."""
    return {
        "code": generate_xss_code(),
        "description": generate_ig_description("XSSTest"),
    }


def generate_unicode_code():
    """Generate a code with unicode/international characters."""
    unicode_samples = [
        "IG\u00e9",           # Latin é
        "IG\u00fc",           # Latin ü
        "\u4e2d\u6587\u7ec4",  # 中文组 (Chinese group)
        "\u0938\u092e\u0942\u0939",  # समूह (Hindi group)
        "\u0433\u0440\u0443\u043f\u043f\u0430",  # группа (Russian group)
        "Grupp\u00e0",        # Italian à
        "Grup\u00f3",         # Spanish ó
    ]
    return random.choice(unicode_samples)


def generate_unicode_data():
    """Return dict with unicode code."""
    return {
        "code": generate_unicode_code(),
        "description": generate_ig_description("UniTest"),
    }


def generate_code_with_leading_trailing_spaces():
    """Generate a code with leading and trailing spaces.
    Tests whether ERP trims whitespace before storing.
    """
    base = generate_ig_code("SpaceIG")
    return f"   {base}   "


def generate_leading_trailing_spaces_data():
    """Return dict with code having leading/trailing spaces."""
    return {
        "code": generate_code_with_leading_trailing_spaces(),
        "description": generate_ig_description("TrimTest"),
    }


def generate_name_with_inner_spaces():
    """Generate a valid code containing inner spaces (should be accepted)."""
    return f"Item Group {random.randint(1000, 9999)}"


def generate_code_with_numbers():
    """Generate a code that is purely numeric."""
    return str(random.randint(100000, 999999))


def generate_code_with_mixed_case():
    """Generate a code with mixed upper/lower case to test case sensitivity."""
    base = generate_ig_code("MixIG")
    return ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(base))


def generate_single_char_code():
    """Generate a single-character code (minimum meaningful input)."""
    return random.choice(string.ascii_uppercase)


# ═══════════════════════════════════════════════════════════════════════════════
#  API Batch Create — Data Pool + Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Screen structure (discovered 2026-06-02):
#   Item Group: code* (text, required, unique — the group code),
#               description* (text, required — the group description)
#   FLAT screen — no steppers, no children, no FK dropdowns.
#
# Note: The UI label "Item Group" maps to the API field "code",
#       and "Description" maps to "description".
#
# Existing entries in ERP (as of 2026-06-02, 26 total):
#   IG001=Agriculture Products, AGRGRP01=FMCG Products, ELEGRP01=Electrical Equipment,
#   PKGGRP01=Hardware Materials, TOOLGRP01=Office Stationery,
#   GRN001=Food Grains Group, PULSE002=Pulses & Legumes Group,
#   SPICE003=Spices & Condiments Group, OILS004=Oilseeds Group,
#   DAIRY005=Dairy Products Group, TEXTL006=Textile Raw Materials Group,
#   RICE007=Rice Varieties Group, WHEAT008=Wheat Products Group,
#   MILL009=Millets Group, FRESH010=Fresh Produce Group,
#   PACK011=Packaged Foods Group, CONST012=Construction Materials Group,
#   CHEM013=Chemical Products Group, FERT014=Fertilizers Group,
#   PEST015=Pesticides Group, TRAN016=Transport Services Group,
#   STOR017=Storage Services Group, QC018=Quality Control Group,
#   LOGS019=Logistics Services Group, PROC020=Processing Services Group
#
# This data pool provides additional group entries NOT already in the system.
# ═══════════════════════════════════════════════════════════════════════════════

# Each entry is a tuple: (code, description)

ITEM_GROUP_API_DATA = [
    # ── Commodity Groups ────────────────────────────────────────────────
    ("BEVG021", "Beverages Group"),
    ("SUGR022", "Sugar & Sweeteners Group"),
    ("ANFD023", "Animal Feed Group"),
    ("FRST024", "Forestry Products Group"),
    ("MRNP025", "Marine Products Group"),
    ("PHRM026", "Pharmaceuticals Group"),
    ("PKGM027", "Packaging Materials Group"),
    ("AUTO028", "Automotive Parts Group"),
    ("SEED029", "Seeds & Planting Material Group"),
    ("FIBR030", "Fiber & Textile Products Group"),

    # ── Sub-Commodity Groups ────────────────────────────────────────────
    ("CRL031", "Coarse Cereals Group"),
    ("PDDY032", "Paddy Rice Group"),
    ("GRAM033", "Gram Varieties Group"),
    ("LENT034", "Lentil Varieties Group"),
    ("WSPC035", "Whole Spices Group"),
    ("GSPC036", "Ground Spices Group"),
    ("DRFR037", "Dry Fruits & Nuts Group"),
    ("EDOL038", "Edible Oils Group"),
    ("OLCA039", "Oilseed Cakes Group"),
    ("RSUG040", "Raw Sugar Group"),

    # ── Processing & Service Groups ─────────────────────────────────────
    ("JAGG041", "Jaggery Products Group"),
    ("MLKP042", "Milk Products Group"),
    ("BTRG043", "Butter & Ghee Group"),
    ("TEAP044", "Tea Products Group"),
    ("COFF045", "Coffee Products Group"),
    ("CTFD046", "Cattle Feed Group"),
    ("PTFD047", "Poultry Feed Group"),
    ("WVSK048", "Woven Sacks Group"),
    ("JTBF049", "Jute Bags Group"),
    ("FWFS050", "Freshwater Fish Group"),

    # ── Industrial Groups ───────────────────────────────────────────────
    ("SHRP051", "Shrimp & Prawns Group"),
    ("CTFN052", "Cotton Fiber Group"),
    ("JTFB053", "Jute Fiber Group"),
    ("TMBR054", "Timber Products Group"),
    ("BMBP055", "Bamboo Products Group"),
    ("CMNT056", "Cement Products Group"),
    ("STEL057", "Steel Products Group"),
    ("AGCH058", "Agrochemicals Group"),
    ("IDCH059", "Industrial Chemicals Group"),
    ("ORGF060", "Organic Fertilizers Group"),

    # ── Specialized Groups ──────────────────────────────────────────────
    ("CHMF061", "Chemical Fertilizers Group"),
    ("OTCM062", "OTC Medicines Group"),
    ("PHRM063", "Pharma Raw Materials Group"),
    ("BLKP064", "Black Pepper Whole Group"),
    ("CRDM065", "Cardamom Whole Group"),
    ("MSTO066", "Mustard Oil Group"),
    ("SYBO067", "Soybean Oil Group"),
    ("GNTO068", "Groundnut Oil Group"),
    ("SNFO069", "Sunflower Oil Group"),
    ("CTCT070", "CTC Tea Group"),

    # ── Export & Premium Groups ─────────────────────────────────────────
    ("ORTX071", "Orthodox Tea Group"),
    ("GRNT072", "Green Tea Group"),
    ("ARBC073", "Arabica Coffee Group"),
    ("RBST074", "Robusta Coffee Group"),
    ("PPWB075", "PP Woven Bags Group"),
    ("HDPE076", "HDPE Bags Group"),
    ("VRMC077", "Vermicompost Group"),
    ("BIFR078", "Bio Fertilizers Group"),
    ("PLJG079", "Palm Jaggery Group"),
    ("SCJG080", "Sugarcane Jaggery Group"),

    # ── Additional Groups ───────────────────────────────────────────────
    ("RCBL081", "Raw Cotton Bales Group"),
    ("CTSD082", "Cotton Seed Group"),
    ("ROHU083", "Rohu Fish Group"),
    ("KTLA084", "Katla Fish Group"),
    ("OPCM085", "OPC Cement Group"),
    ("PPCM086", "PPC Cement Group"),
    ("UREA087", "Urea Fertilizer Group"),
    ("DAPF088", "DAP Fertilizer Group"),
    ("NPKB089", "NPK Blends Group"),
    ("DCPL090", "Dairy Cattle Pellets Group"),
    ("CSFD091", "Calf Starter Feed Group"),
    ("BRFD092", "Broiler Feed Group"),
    ("LYFD093", "Layer Feed Group"),
    ("MEDI094", "Medical Equipment Group"),
    ("SFTY095", "Safety Equipment Group"),
]


def build_item_group_api_payload(code: str, description: str = "") -> dict:
    """
    Build a single API payload for Item Group.

    Args:
        code: Group code (e.g., "BEVG021") — maps to the "Item Group" UI field
        description: Group description text

    Returns:
        dict: API payload with attribute_name set to "Item Group"
    """
    return {
        "id": "",
        "attribute_name": "Item Group",
        "code": code,
        "description": description,
    }


def generate_item_group_payloads(count: int = 10, offset: int = 0) -> list:
    """
    Generate N API payloads for Item Group.

    Args:
        count: Number of payloads to generate
        offset: Start index in the data pool (to skip already-used entries)

    Returns:
        list[dict]: List of API payloads ready for batch_create
    """
    pool = ITEM_GROUP_API_DATA
    payloads = []

    for i in range(count):
        idx = (offset + i) % len(pool)
        code, description = pool[idx]

        # Handle potential duplicate codes when wrapping around
        if (offset + i) >= len(pool):
            wrap_count = (offset + i) // len(pool) + 1
            code = f"{code}-B{wrap_count}"

        payloads.append(
            build_item_group_api_payload(code=code, description=description)
        )

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Item Group is a flat screen — no children, no steppers, no FK dropdowns.
# 2 fields: code (required), description (required).

FIELD_VALIDATION_RULES = {
    "code": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Item Group code. Maps to 'Item Group' UI label.",
    },
    "description": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Item Group description text.",
    },
}

# No FK dropdown pools — Item Group has zero FK fields
DEFAULT_ITEM_GROUP_FK_IDS = {}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """Generate a batch of unique Item Group API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored for Item Group (realistic codes from data pool are used).
        dropdown_ids: Not used for Item Group (no FK dropdown fields).

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    return generate_item_group_payloads(count=count)
