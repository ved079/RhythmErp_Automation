"""
uom_data.py
------------
Test data generator for UOM automation.
Generates random UOM codes and descriptions.

Updated (v2):
- UOM Code field: type="text", maxlength=255 (auto-cutoff at 255 chars)
- UOM Description field: maxlength=255 (auto-cutoff at 255 chars)
- Description is NOT required (optional field)
- Numbers are allowed in UOM code
"""

import random
import string
from datetime import datetime


def generate_uom_data():
    """Generate random UOM test data. Code = 8 uppercase letters + timestamp for uniqueness."""
    uom_code = "".join(random.choices(string.ascii_uppercase, k=8))
    timestamp = datetime.now().strftime("%H%M%S")
    uom_description = f"Test UOM Description {timestamp}"
    return {
        "uom_code": uom_code,
        "uom_description": uom_description,
        "status": "Active"
    }


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the existing UI data format into the JSON payload
# that POST /core/dynamic-screen-wrapper/ expects.
#
# UOM SCREEN STRUCTURE (flat — no children, no steppers):
#   {
#     "id": "",
#     "attribute_name": "UOM",
#     "uom_code": "KG",
#     "uom_description": "Kilogram",
#     "status": true
#   }
#
# FIELD KEY MAPPING (reasonable guess — to be verified by discover_all.py):
#   uom_code         -> uom_code (text, required)
#   uom_description  -> uom_description (text, optional)
#   status           -> status (boolean, default true)
# ──────────────────────────────────────────────

# Realistic measurement units for API batch creation (Indian ERP context)
REALISTIC_UOM_DATA = [
    # Weight units
    {"uom_code": "KG", "uom_description": "Kilogram"},
    {"uom_code": "MT", "uom_description": "Metric Ton"},
    {"uom_code": "QTL", "uom_description": "Quintal"},
    {"uom_code": "GM", "uom_description": "Gram"},
    {"uom_code": "MG", "uom_description": "Milligram"},
    {"uom_code": "LB", "uom_description": "Pound"},
    {"uom_code": "TON", "uom_description": "Ton"},
    {"uom_code": "GWT", "uom_description": "Gross Weight"},
    {"uom_code": "NWT", "uom_description": "Net Weight"},
    {"uom_code": "TWT", "uom_description": "Tare Weight"},
    # Volume units
    {"uom_code": "LTR", "uom_description": "Litre"},
    {"uom_code": "ML", "uom_description": "Millilitre"},
    {"uom_code": "KL", "uom_description": "Kilolitre"},
    {"uom_code": "GAL", "uom_description": "Gallon"},
    {"uom_code": "CBM", "uom_description": "Cubic Metre"},
    # Count/Packaging units
    {"uom_code": "PCS", "uom_description": "Piece"},
    {"uom_code": "DZN", "uom_description": "Dozen"},
    {"uom_code": "BAG", "uom_description": "Bag"},
    {"uom_code": "BOX", "uom_description": "Box"},
    {"uom_code": "CTN", "uom_description": "Carton"},
    {"uom_code": "PKT", "uom_description": "Packet"},
    {"uom_code": "BTL", "uom_description": "Bottle"},
    {"uom_code": "CAN", "uom_description": "Can"},
    {"uom_code": "DRM", "uom_description": "Drum"},
    {"uom_code": "BNDL", "uom_description": "Bundle"},
    {"uom_code": "ROLL", "uom_description": "Roll"},
    {"uom_code": "SET", "uom_description": "Set"},
    {"uom_code": "NOS", "uom_description": "Numbers"},
    {"uom_code": "PAIR", "uom_description": "Pair"},
    # Length units
    {"uom_code": "MTR", "uom_description": "Meter"},
    {"uom_code": "FT", "uom_description": "Feet"},
    {"uom_code": "IN", "uom_description": "Inch"},
    {"uom_code": "YD", "uom_description": "Yard"},
    {"uom_code": "CM", "uom_description": "Centimetre"},
    {"uom_code": "MM", "uom_description": "Millimetre"},
    {"uom_code": "KM", "uom_description": "Kilometre"},
    # Area units
    {"uom_code": "ACR", "uom_description": "Acre"},
    {"uom_code": "HA", "uom_description": "Hectare"},
    {"uom_code": "SQM", "uom_description": "Square Metre"},
    {"uom_code": "SQFT", "uom_description": "Square Feet"},
    {"uom_code": "BIGHA", "uom_description": "Bigha"},
    {"uom_code": "GUNTHA", "uom_description": "Guntha"},
    # Agricultural specific
    {"uom_code": "QUIN", "uom_description": "Quintal"},
    {"uom_code": "MUND", "uom_description": "Maund"},
    {"uom_code": "SER", "uom_description": "Seer"},
    {"uom_code": "PALL", "uom_description": "Pall"},
    # Time/other
    {"uom_code": "DAY", "uom_description": "Day"},
    {"uom_code": "HRS", "uom_description": "Hours"},
    {"uom_code": "KWH", "uom_description": "Kilowatt Hour"},
    {"uom_code": "HP", "uom_description": "Horse Power"},
]

# Track used codes to avoid duplicates within a batch
_used_uom_codes = set()


def generate_realistic_uom_data():
    """Pick a random realistic measurement unit, ensuring no duplicates
    within the current batch by appending a suffix if needed."""
    uom = random.choice(REALISTIC_UOM_DATA)
    code = uom["uom_code"]
    desc = uom["uom_description"]

    if code not in _used_uom_codes:
        _used_uom_codes.add(code)
        return {"uom_code": code, "uom_description": desc}

    # Duplicate — append a short numeric suffix to code
    suffix = str(random.randint(1, 99))
    unique_code = f"{code}{suffix}"
    _used_uom_codes.add(unique_code)
    return {"uom_code": unique_code, "uom_description": f"{desc} (Variant {suffix})"}


def reset_uom_code_pool():
    """Reset the used-code tracker (call before a new batch)."""
    _used_uom_codes.clear()


def build_uom_api_payload(data=None, dropdown_ids=None):
    """Build the UOM API payload from data dict.

    Args:
        data: Dict with 'uom_code', 'uom_description', 'status' keys, or None for random.
        dropdown_ids: Not used for UOM (no dropdown FK fields).
                      Kept for interface consistency.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    if data is None:
        data = generate_uom_data()

    payload = {
        "id": "",
        "attribute_name": "UOM",
        "uom_code": data.get("uom_code", ""),
        "uom_description": data.get("uom_description", "") or None,
        "status": True,
    }
    return payload


def generate_uom_api_payload(name_prefix=None, dropdown_ids=None):
    """One-shot: generate a complete UOM API payload with realistic data.

    Args:
        name_prefix: Ignored (realistic UOM codes are used instead).
        dropdown_ids: Not used for UOM.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    realistic = generate_realistic_uom_data()
    data = {
        "uom_code": realistic["uom_code"],
        "uom_description": realistic["uom_description"],
        "status": True,
    }
    return build_uom_api_payload(data, dropdown_ids)


def generate_uom_api_payloads(count=20, prefix=None, dropdown_ids=None):
    """Generate multiple unique UOM API payloads for batch creation.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored (realistic UOM codes are used instead).
        dropdown_ids: Not used for UOM.

    Returns:
        List of JSON payloads.
    """
    reset_uom_code_pool()
    payloads = []
    for _ in range(count):
        payloads.append(
            generate_uom_api_payload(prefix, dropdown_ids)
        )
    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# UOM is a flat screen — no children, no steppers, no FK dropdowns.
# Only 3 fields: uom_code (required), uom_description (optional), status (toggle).

def get_field_validation_rules(fk_ids=None):
    """Return validation rules dict. UOM has no FK fields, so fk_ids is unused."""
    return {
        "uom_code": {
            "type": "text",
            "required": True,
            "max_length": 255,
            "note": "Accepts uppercase letters, numbers, hyphen (-), underscore (_). "
                    "Lowercase rejected. Frontend maxlength=255 but backend enforces max 10 chars.",
        },
        "uom_description": {
            "type": "text",
            "required": False,
            "max_length": 255,
            "note": "Optional field. Accepts special characters. "
                     "Can be empty/null.",
        },
        "status": {
            "type": "toggle",
            "required": False,
            "default": True,
            "note": "Boolean toggle. True=Active, False=Inactive.",
        },
    }


# Backward-compat constant
FIELD_VALIDATION_RULES = get_field_validation_rules()

# Status toggle options (display name -> API boolean value)
STATUS_OPTIONS = {
    "Active": True,
    "Inactive": False,
}

UOM_CODE_BACKEND_MAX_LENGTH = 10  # backend rejects codes longer than 10 chars


def get_fk_screen_mapping():
    """UOM has no FK dropdown fields — return empty mapping."""
    return {}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
    offset: int = 0,
    existing_entries: list = None,
) -> list:
    """Generate a batch of unique UOM API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules (Customer, Supplier, Company Onboarding, etc.).

    Args:
        count: Number of payloads to generate.
        prefix: Ignored for UOM (realistic codes are used instead).
        dropdown_ids: Not used for UOM (no FK dropdown fields).
        offset: Ignored for UOM (codes are unique, not pool-based).
        existing_entries: Ignored for UOM (dedup is by unique code per batch).

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    reset_uom_code_pool()
    payloads = []
    for i in range(count):
        payloads.append(
            generate_uom_api_payload(prefix, dropdown_ids)
        )
    return payloads
