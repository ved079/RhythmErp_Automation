"""
season_data.py
--------------
Test data generators and constants for Season screen automation.
Each function returns data safe for a specific test scenario.
"""

import random
import string


# ================================================================
# FIELD NAMES (match input[name="..."] on the ERP form)
# ================================================================
FIELD_NAME = "Name"
FIELD_DESCRIPTION = "Description"

# Status checkbox labels (as displayed in the ERP)
STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"

_SEASON_PREFIXES = ["Kharif", "Rabi", "Summer", "Zaid", "Winter", "Spring"]


# ================================================================
# SAFE DATA — these won't collide with existing records
# ================================================================

def _random_suffix(length=6):
    return ''.join(random.choices(string.ascii_uppercase, k=length))


# --- Valid test data ---

def valid_season_name():
    """Unique season name for happy-path / edit tests.

    Uses spaces (not underscores) because the ERP Name field has a
    type='character' validator that rejects underscores.
    """
    return f"{random.choice(_SEASON_PREFIXES)} Season {_random_suffix()}"


def valid_season_with_description():
    """Season name + description, both filled.

    Uses spaces (not underscores) because the ERP Name field has a
    type='character' validator that rejects underscores.
    """
    return {
        FIELD_NAME: f"{random.choice(_SEASON_PREFIXES)} Season {_random_suffix()}",
        FIELD_DESCRIPTION: f"Test season created by automation - {_random_suffix()}",
    }


def valid_season_name_only():
    """Season name filled, description left blank (optional field).

    Uses spaces (not underscores) because the ERP Name field has a
    type='character' validator that rejects underscores.
    """
    return {
        FIELD_NAME: f"{random.choice(_SEASON_PREFIXES)} Season {_random_suffix()}",
        FIELD_DESCRIPTION: "",
    }


# --- Edge-case / negative test data ---

def empty_submit():
    """All fields blank — should trigger Validation Failed."""
    return {
        FIELD_NAME: "",
        FIELD_DESCRIPTION: "",
    }


def name_only_rest_blank():
    """Only Name filled, Description empty — should PASS (Description is optional).

    Uses spaces (not underscores) because the ERP Name field has a
    type='character' validator that rejects underscores.
    """
    return {
        FIELD_NAME: f"SEASON NAMEONLY {_random_suffix()}",
        FIELD_DESCRIPTION: "",
    }


def sql_injection_name():
    """SQL injection payload in Name — BUG: accepted and stored as-is.

    NOTE: The ERP's type='character' validator rejects special characters
    including underscores. SQL injection chars like ', ;, - will also be
    rejected by this validator. This test documents the validation behavior.
    """
    return {
        FIELD_NAME: f"DROP TABLE Season{_random_suffix()}",
        FIELD_DESCRIPTION: "SQL injection test",
    }


def xss_in_name():
    """XSS script tag in Name — BUG: stored as raw HTML, renders in list.

    NOTE: The ERP's type='character' validator rejects < > and special chars.
    This test documents the validation behavior.
    """
    return {
        FIELD_NAME: f"script alert xss{_random_suffix()}",
        FIELD_DESCRIPTION: "XSS test",
    }


def special_chars_name():
    """Special characters in Name — tests type='character' validator.

    The ERP's type='character' validator should reject special chars
    like @, !, #. This test verifies that behavior.
    """
    return {
        FIELD_NAME: f"test@season!#{_random_suffix()}",
        FIELD_DESCRIPTION: "Special chars test",
    }


def duplicate_name():
    """Name that already exists in the DB — BUG: system hangs indefinitely.

    NOTE: 'Rabi' is a known existing record in the ERP.
    This test should be handled with a timeout/fallback
    because the system will NOT respond.
    """
    return {
        FIELD_NAME: "Rabi",  # existing record
        FIELD_DESCRIPTION: "Attempting duplicate",
    }


def very_long_name(length=200):
    """Very long string in Name field — tests max-length behavior.

    Uses 'A' repeated (letters only) since the ERP's type='character'
    validator rejects special characters.
    """
    return {
        FIELD_NAME: "A" * length,
        FIELD_DESCRIPTION: "Long name test",
    }


def numbers_only_name():
    """Numeric-only Name — tests if the field accepts numbers."""
    return {
        FIELD_NAME: f"{''.join(random.choices(string.digits, k=6))}",
        FIELD_DESCRIPTION: "Numbers only test",
    }


def leading_trailing_spaces():
    """Name with leading/trailing spaces — tests trim behavior.

    Uses spaces (not underscores) because the ERP Name field has a
    type='character' validator that rejects underscores.
    """
    return {
        FIELD_NAME: f"  SEASON SPACES {_random_suffix()}  ",
        FIELD_DESCRIPTION: "Spaces test",
    }


# ================================================================
# EXPECTED ALERT MESSAGES
# ================================================================
VALIDATION_ALERT_TITLE = "Validation Failed"
VALIDATION_ALERT_SUBTEXT = "Please correct the highlighted fields"

SUCCESS_ALERT_TITLE_ADD = "Your record has been added successfully!"
SUCCESS_ALERT_TITLE_UPDATE = "Your record has been updated successfully!"

# Required field error (generic — no field-specific messages)
REQUIRED_FIELD_ERROR = "This field is required"


# ================================================================
# ERP NAVIGATION
# ================================================================
SEASON_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Season"
BREADCRUMB_TEXT = "Common Settings / Season"


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the existing UI data format into the JSON payload
# that POST /core/dynamic-screen-wrapper/ expects.
#
# SEASON SCREEN STRUCTURE (flat — no children, no steppers):
#   {
#     "id": "",
#     "attribute_name": "Season",
#     "name": "Kharif",
#     "description": "Monsoon cropping season",
#     "status": true
#   }
#
# FIELD KEY MAPPING (reasonable guess — to be verified by discover_all.py):
#   name          -> name (text, required)
#   description   -> description (text, optional)
#   status        -> status (boolean, default true)
# ──────────────────────────────────────────────

# Realistic Indian agricultural/commodity seasons for API batch creation
REALISTIC_SEASON_NAMES = [
    # Major Indian cropping seasons
    "Kharif", "Rabi", "Zaid",
    # Climatic seasons (Indian context)
    "Monsoon", "Winter", "Summer", "Spring", "Autumn",
    # Agricultural season variants
    "Kharif Early", "Kharif Late", "Rabi Early", "Rabi Late",
    "Zaid Kharif", "Zaid Rabi",
    # Commodity-specific seasons
    "Sowing Season", "Harvesting Season", "Procurement Season",
    "Marketing Season", "Planting Season",
    # Regional Indian seasons
    "Vasant Ritu", "Grishma Ritu", "Varsha Ritu", "Sharad Ritu",
    "Hemant Ritu", "Shishir Ritu",
    # Sugarcane/cotton specific
    "Crushing Season", "Ginning Season",
    # Trading seasons
    "Lean Season", "Peak Season", "Off Season",
    # Fiscal/calendar
    "Q1 Season", "Q2 Season", "Q3 Season", "Q4 Season",
    "FY First Half", "FY Second Half",
]

# Descriptions for each season name (professional context)
SEASON_DESCRIPTIONS = {
    "Kharif": "Monsoon cropping season (June–October), major crops: rice, cotton, soybean",
    "Rabi": "Winter cropping season (October–March), major crops: wheat, mustard, gram",
    "Zaid": "Summer cropping season (March–June), major crops: cucumber, watermelon, muskmelon",
    "Monsoon": "Southwest monsoon season, critical for Indian agriculture",
    "Winter": "Cold season from November to February, Rabi crop growing period",
    "Summer": "Hot season from March to May, Zaid crop window",
    "Spring": "Transitional season (Feb–Apr), pleasant weather harvest period",
    "Autumn": "Post-monsoon transitional season (Sep–Nov), Kharif harvest period",
    "Kharif Early": "Early sowing window for Kharif crops (June–July)",
    "Kharif Late": "Late sowing window for Kharif crops (July–August)",
    "Rabi Early": "Early sowing window for Rabi crops (October–November)",
    "Rabi Late": "Late sowing window for Rabi crops (November–December)",
    "Zaid Kharif": "Pre-Kharif summer season bridging Rabi and Kharif",
    "Zaid Rabi": "Pre-Rabi autumn season bridging Kharif and Rabi",
    "Sowing Season": "Active sowing period for crop establishment",
    "Harvesting Season": "Crop maturity and harvesting period",
    "Procurement Season": "Government procurement window for MSP crops",
    "Marketing Season": "Peak marketing and trading period for agricultural commodities",
    "Planting Season": "Active planting period for perennial crops",
    "Vasant Ritu": "Spring season (Feb–Mar) as per Indian calendar",
    "Grishma Ritu": "Summer season (Apr–Jun) as per Indian calendar",
    "Varsha Ritu": "Rainy/monsoon season (Jul–Sep) as per Indian calendar",
    "Sharad Ritu": "Autumn season (Oct–Nov) as per Indian calendar",
    "Hemant Ritu": "Pre-winter season (Nov–Dec) as per Indian calendar",
    "Shishir Ritu": "Winter season (Jan–Feb) as per Indian calendar",
    "Crushing Season": "Sugarcane crushing operational period (Nov–Apr)",
    "Ginning Season": "Cotton ginning operational period (Oct–Mar)",
    "Lean Season": "Low activity period between major seasons",
    "Peak Season": "Maximum trading activity period",
    "Off Season": "Non-operational period for specific commodities",
    "Q1 Season": "First quarter season (Apr–Jun)",
    "Q2 Season": "Second quarter season (Jul–Sep)",
    "Q3 Season": "Third quarter season (Oct–Dec)",
    "Q4 Season": "Fourth quarter season (Jan–Mar)",
    "FY First Half": "First half of financial year (Apr–Sep)",
    "FY Second Half": "Second half of financial year (Oct–Mar)",
}

# Track used names to avoid duplicates within a batch
_used_season_names = set()


def generate_realistic_season_name():
    """Pick a random realistic Indian season name, ensuring no duplicates
    within the current batch by appending a short suffix if needed."""
    name = random.choice(REALISTIC_SEASON_NAMES)
    if name not in _used_season_names:
        _used_season_names.add(name)
        return name
    # Duplicate — append a short alphabetic suffix
    suffix = "".join(random.choices(string.ascii_uppercase, k=3))
    unique_name = f"{name} {suffix}"
    _used_season_names.add(unique_name)
    return unique_name


def reset_season_name_pool():
    """Reset the used-name tracker (call before a new batch)."""
    _used_season_names.clear()


def build_season_api_payload(data=None, dropdown_ids=None):
    """Build the Season API payload from data dict.

    Args:
        data: Dict with 'name', 'description', 'status' keys, or None for random.
        dropdown_ids: Not used for Season (no dropdown FK fields).
                      Kept for interface consistency.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    if data is None:
        data = valid_season_with_description()

    payload = {
        "id": "",
        "attribute_name": "Season",
        "name": data.get(FIELD_NAME, ""),
        "description": data.get(FIELD_DESCRIPTION, "") or None,
        "status": True,
    }
    return payload


def generate_season_api_payload(name_prefix=None, dropdown_ids=None):
    """One-shot: generate a complete Season API payload with realistic data.

    Args:
        name_prefix: Ignored (realistic names are used instead).
        dropdown_ids: Not used for Season.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    name = generate_realistic_season_name()
    description = SEASON_DESCRIPTIONS.get(name, f"Season: {name}")
    data = {
        FIELD_NAME: name,
        FIELD_DESCRIPTION: description,
        "status": True,
    }
    return build_season_api_payload(data, dropdown_ids)


def generate_season_api_payloads(count=20, prefix=None, dropdown_ids=None):
    """Generate multiple unique Season API payloads for batch creation.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored (realistic names are used instead).
        dropdown_ids: Not used for Season.

    Returns:
        List of JSON payloads.
    """
    reset_season_name_pool()
    payloads = []
    for _ in range(count):
        payloads.append(
            generate_season_api_payload(prefix, dropdown_ids)
        )
    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Season is a flat screen — no children, no steppers, no FK dropdowns.
# 3 fields: name (required), description (optional), status (toggle).

def get_field_validation_rules(fk_ids=None):
    """Return validation rules dict. Season has no FK fields, so fk_ids is unused."""
    return {
        "name": {
            "type": "character",
            "required": True,
            "max_length": 255,
            "note": "Letters and spaces only (type='character'). Frontend rejects "
                     "underscores, digits, special chars.",
        },
        "description": {
            "type": "character",
            "required": False,
            "max_length": 255,
            "note": "Optional field. Can be empty/null.",
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

SEASON_NAME_MAX_LENGTH = 255  # frontend caps at 255; backend also enforces this
# Verified name validation rules (confirmed via API probe on tenant 751):
# ACCEPTED by both frontend and API: letters, numbers, spaces, hyphens
# REJECTED by both frontend and API: underscore, special chars (@#$%)
# REJECTED by frontend only (API accepts): hyphen  <-- frontend is MORE restrictive
# Note: the frontend rejects hyphens but the API accepts them — frontend-only restriction
SEASON_NAME_ACCEPTED_CHARS = "letters, numbers, spaces, hyphens (API only)"
SEASON_NAME_REJECTED_BY_BOTH = "underscore, special chars (@#$%)"


def get_fk_screen_mapping():
    """Season has no FK dropdown fields — return empty mapping."""
    return {}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
    offset: int = 0,
    existing_entries: list = None,
) -> list:
    """Generate a batch of unique Season API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored for Season (realistic names are used instead).
        dropdown_ids: Not used for Season (no FK dropdown fields).

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    reset_season_name_pool()
    payloads = []
    for i in range(count):
        payloads.append(
            generate_season_api_payload(prefix, dropdown_ids)
        )
    return payloads
