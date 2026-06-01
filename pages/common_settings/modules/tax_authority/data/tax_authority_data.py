"""
tax_authority_data.py
---------------------
Test data generators and constants for Tax Authority screen automation.
Each function returns data safe for a specific test scenario.

Module: Common Settings > Tax Authority
Fields: Tax Name (text), Tax Type (mat-select), Country (mat-select)
"""

import random
import string


# ================================================================
# FIELD NAMES (match input[name="..."] on the ERP form)
# ================================================================
FIELD_TAX_NAME = "Tax Name"

# Dropdown values
TAX_TYPE_GST = "GST"

# Country options (subset of 114 available — used for testing)
COUNTRY_INDIA = "India"
COUNTRY_DUBAI = "Dubai"
COUNTRY_UNITED_STATES = "United States"
COUNTRY_UNITED_KINGDOM = "United Kingdom"


# ================================================================
# SAFE DATA — these won't collide with existing records
# ================================================================

def _random_suffix(length=6):
    """Generate a random alphabetic suffix to avoid collisions.
    
    IMPORTANT: Tax Name field only accepts alphabetic characters (no digits).
    """
    return ''.join(random.choices(string.ascii_uppercase, k=length))


# --- Valid test data ---

def valid_tax_authority_data():
    """All 3 required fields filled with valid data.

    Tax Name uses a random suffix to avoid collisions with existing records.
    Tax Type is always GST (only option available).
    Country defaults to India.
    """
    return {
        FIELD_TAX_NAME: f"TaxAuth{_random_suffix()}",
        "tax_type": TAX_TYPE_GST,
        "country": COUNTRY_INDIA,
    }


def valid_tax_authority_dubai():
    """Tax Authority with Dubai as country."""
    data = valid_tax_authority_data()
    data["country"] = COUNTRY_DUBAI
    return data


def valid_tax_authority_usa():
    """Tax Authority with United States as country."""
    data = valid_tax_authority_data()
    data["country"] = COUNTRY_UNITED_STATES
    return data


# --- Edge-case / negative test data ---

def invalid_empty_tax_name():
    """Empty Tax Name — server rejects with Validation Failed."""
    data = valid_tax_authority_data()
    data[FIELD_TAX_NAME] = ""
    return data


def invalid_very_long_tax_name(length=200):
    """Very long Tax Name (200 chars) — tests max-length behavior.

    BUG: No maxlength restriction on Tax Name field (maxlength=-1).
    Server may accept or reject extremely long names.
    """
    data = valid_tax_authority_data()
    data[FIELD_TAX_NAME] = "A" * length
    return data


def special_chars_tax_name():
    """Tax Name with special characters — tests input sanitization.

    Checks if characters like @#$%^&*() are accepted or rejected.
    """
    data = valid_tax_authority_data()
    data[FIELD_TAX_NAME] = f"Test@#$%^&*{_random_suffix()}"
    return data


def duplicate_tax_authority_data(existing_name):
    """Duplicate Tax Name — tests duplicate detection.

    Args:
        existing_name: The name of an existing record to duplicate.
    """
    return {
        FIELD_TAX_NAME: existing_name,
        "tax_type": TAX_TYPE_GST,
        "country": COUNTRY_INDIA,
    }


# ================================================================
# EXPECTED ALERT MESSAGES
# ================================================================
VALIDATION_ALERT_TITLE = "Validation Failed"
SUCCESS_ALERT_TITLE_ADD = "Your record has been added successfully!"
SUCCESS_ALERT_TITLE_UPDATE = "Your record has been updated successfully!"


# ================================================================
# ERP NAVIGATION
# ================================================================
TAX_AUTHORITY_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Authority"
BREADCRUMB_TEXT = "Common Settings / Tax Authority"


# ═══════════════════════════════════════════════════════════════════════════════
# API Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Converts UI data format into the JSON payload that
# POST /core/dynamic-screen-wrapper/ expects.
#
# TAX AUTHORITY SCREEN STRUCTURE (flat — no children/steppers):
#   {
#     "id": "",
#     "attribute_name": "Tax Authority",
#     "name": "GST Authority Mumbai",
#     "tax_type_ref_id": <FK ID>,
#     "country_ref_id": <FK ID>,
#     "status": true
#   }
#
# FIELD KEY MAPPING:
#   Tax Name   -> name (text, alphabetic only!)
#   tax_type   -> tax_type_ref_id (FK dropdown, only GST option)
#   country    -> country_ref_id (FK dropdown, India=8)
#   status     -> status (boolean)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── FK ID Placeholders ──────────────────────────────────────────────────────
TAX_TYPE_IDS = {
    "GST": None,  # Only option — ID to be filled from discovery
}

COUNTRY_IDS = {
    "India": 8,
    "Dubai": None,
    "United States": None,
    "United Kingdom": None,
}

# ─── Realistic Indian Tax Authority names ────────────────────────────────────
# All alphabetic (no digits) as per field validation rule
REALISTIC_TAX_AUTHORITY_NAMES = [
    # GST authorities by region
    "GST Authority Mumbai",
    "GST Authority Delhi",
    "GST Authority Pune",
    "GST Authority Ahmedabad",
    "GST Authority Bangalore",
    "GST Authority Chennai",
    "GST Authority Hyderabad",
    "GST Authority Kolkata",
    "GST Authority Jaipur",
    "GST Authority Lucknow",
    "GST Authority Nagpur",
    "GST Authority Nashik",
    "GST Authority Indore",
    "GST Authority Bhopal",
    "GST Authority Chandigarh",
    "GST Authority Kochi",
    "GST Authority Coimbatore",
    "GST Authority Surat",
    "GST Authority Vadodara",
    "GST Authority Thane",
    # Commissioner-level names
    "Central GST Commissioner Mumbai",
    "Central GST Commissioner Delhi",
    "Central GST Commissioner Pune",
    "Central GST Commissioner Bangalore",
    "Central GST Commissioner Chennai",
    "Central GST Commissioner Hyderabad",
    "Central GST Commissioner Kolkata",
    "Central GST Commissioner Jaipur",
    "Central GST Commissioner Ahmedabad",
    "Central GST Commissioner Lucknow",
    # State GST department names
    "State GST Department Maharashtra",
    "State GST Department Gujarat",
    "State GST Department Karnataka",
    "State GST Department Tamil Nadu",
    "State GST Department Uttar Pradesh",
    "State GST Department Rajasthan",
    "State GST Department Madhya Pradesh",
    "State GST Department West Bengal",
    "State GST Department Kerala",
    "State GST Department Telangana",
    # Additional realistic names
    "GST Commissionerate Central Mumbai",
    "GST Commissionerate South Mumbai",
    "GST Commissionerate North Delhi",
    "GST Commissionerate South Delhi",
    "GST Audit Circle Pune",
    "GST Audit Circle Ahmedabad",
    "GST Division Nashik",
    "GST Division Kolhapur",
    "GST Range Aurangabad",
    "GST Range Solapur",
    # International (Dubai)
    "Federal Tax Authority Dubai",
    "Dubai Tax Administration",
    "UAE Tax Authority",
    # International (others)
    "Internal Revenue Service United States",
    "HM Revenue and Customs United Kingdom",
]


def build_tax_authority_api_payload(data: dict = None, dropdown_ids: dict = None) -> dict:
    """Build the Tax Authority API payload from data + FK IDs.

    Args:
        data: Dict with 'Tax Name', 'tax_type', 'country' keys, or None for random.
        dropdown_ids: Dict of FK IDs. Must contain 'tax_type_ref_id' and 'country_ref_id'.
                      Falls back to TAX_TYPE_IDS / COUNTRY_IDS placeholders.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    if data is None:
        data = valid_tax_authority_data()

    # Resolve FK IDs
    tax_type_name = data.get("tax_type", TAX_TYPE_GST)
    country_name = data.get("country", COUNTRY_INDIA)

    default_tax_type_id = TAX_TYPE_IDS.get(tax_type_name)
    default_country_id = COUNTRY_IDS.get(country_name)

    ids = dropdown_ids or {}
    tax_type_ref_id = ids.get("tax_type_ref_id", default_tax_type_id)
    country_ref_id = ids.get("country_ref_id", default_country_id)

    payload = {
        "id": "",
        "attribute_name": "Tax Authority",
        "name": data.get(FIELD_TAX_NAME, f"TaxAuth{_random_suffix()}"),
        "tax_type_ref_id": tax_type_ref_id,
        "country_ref_id": country_ref_id,
        "status": True,
    }
    return payload


def generate_tax_authority_api_payload(name_prefix: str = None, dropdown_ids: dict = None) -> dict:
    """One-shot: generate a complete Tax Authority API payload with realistic data.

    Picks a random name from REALISTIC_TAX_AUTHORITY_NAMES for authentic
    Indian tax authority entries.

    Args:
        name_prefix: If provided, prepended to a random realistic name.
        dropdown_ids: Override specific FK IDs (e.g., tax_type_ref_id, country_ref_id).

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    name = random.choice(REALISTIC_TAX_AUTHORITY_NAMES)
    if name_prefix:
        name = f"{name_prefix} {name}"

    data = {
        FIELD_TAX_NAME: name,
        "tax_type": TAX_TYPE_GST,
        "country": COUNTRY_INDIA,
    }
    return build_tax_authority_api_payload(data, dropdown_ids)


def generate_tax_authority_api_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None) -> list:
    """Generate multiple unique Tax Authority API payloads for batch creation.

    Picks unique entries from REALISTIC_TAX_AUTHORITY_NAMES (without
    replacement). If count exceeds pool size, adds random suffix for
    uniqueness.

    Args:
        count: Number of payloads to generate (default 20).
        prefix: Optional prefix for each name.
        dropdown_ids: Override specific FK IDs.

    Returns:
        List of JSON payloads.
    """
    pool = list(REALISTIC_TAX_AUTHORITY_NAMES)
    random.shuffle(pool)

    payloads = []
    for i in range(count):
        if i < len(pool):
            name = pool[i]
        else:
            # Generate unique name beyond the pool
            name = f"{random.choice(REALISTIC_TAX_AUTHORITY_NAMES)} {_random_suffix(4)}"

        if prefix:
            name = f"{prefix} {name}"

        data = {
            FIELD_TAX_NAME: name,
            "tax_type": TAX_TYPE_GST,
            "country": COUNTRY_INDIA,
        }
        payloads.append(build_tax_authority_api_payload(data, dropdown_ids))

    return payloads
