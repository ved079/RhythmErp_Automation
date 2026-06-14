"""
register_charges_data.py
------------------------
Test data & API payload builder for Rhythm ERP Register Charges screen.
Derived from live ERP schema at /core/dynamic-screen/Register%20Charges/ (tenant 711).

FIELD REFERENCE (flat form — no steppers):

  1. Date of Creation        (date, required — API accepts null)
  2. Date of Modification    (date, required — API accepts null)
  3. Charge ID (ROC)         (character, required, UNIQUE)
     Pattern: ^(?!0+$)\\d{1,20}$  — 1-20 digits, not all zeros
  4. Type of Charge          (dropdown, required) — FK to tbl_master (master_type='Type of Charge')
     Options: Mortgage(1909), Hypothecation(1910), Pledge(1911)
  5. Description of Assets/Property (character, optional)
  6. Amount Secured          (integer, required)
     Pattern: ^(?!.*[+-])[0-9]+(\\.[0-9]{1,4})?$  — positive, up to 4 decimals
  7. Charge Holder Details   (character, required)
  8. Date of Satisfaction    (date, optional)

KEY RULES (verified 2026-06-12 on live API):
  - FLAT FORM: No steppers, no children array
  - API does NOT enforce server-side validation for most fields
  - roc_charge_id must be unique (server-enforced)
  - type_of_charge_ref_id comes from tbl_master, NOT a dynamic screen
  - Master table: register_charges
  - API returns 201 on successful creation

ENDPOINTS:
  Schema:  GET  /core/dynamic-screen/Register%20Charges/
  List:    GET  /core/dynamic-screen-wrapper/Register%20Charges/
  Create:  POST /core/dynamic-screen-wrapper/
"""

import random
import string
from datetime import datetime, date


# ──────────────────────────────────────────────
# FK ID pools (verified on tenant 711, 2026-06-12)
# ──────────────────────────────────────────────

# Type of Charge — from tbl_master (master_type='Type of Charge')
# NOT a dynamic screen — cannot be resolved via FkResolver
TYPE_OF_CHARGE_IDS = [1909, 1910, 1911]
TYPE_OF_CHARGE_NAMES = {
    1909: "Mortgage",
    1910: "Hypothecation",
    1911: "Pledge",
}

# Default FK IDs
DEFAULT_FK_IDS = {
    "type_of_charge_ref_id": 1909,
}


# ──────────────────────────────────────────────
# Realistic data pools
# ──────────────────────────────────────────────

_ASSET_DESCRIPTIONS = [
    "Agricultural land at Pune district",
    "Warehouse at MIDC industrial area",
    "Factory building with machinery",
    "Commercial office space",
    "Residential property",
    "Cold storage facility",
    "Irrigation equipment",
    "Transport vehicles fleet",
    "Godown and storage facility",
    "Processing plant and equipment",
    "Solar power installation",
    "Dairy farm infrastructure",
    "Poultry farm setup",
    "Greenhouse and polyhouse",
    "Harvesting machinery",
]

_CHARGE_HOLDERS = [
    "State Bank of India",
    "Bank of Maharashtra",
    "HDFC Bank",
    "ICICI Bank",
    "Axis Bank",
    "Punjab National Bank",
    "Bank of Baroda",
    "Canara Bank",
    "Union Bank of India",
    "Indian Bank",
    "Central Bank of India",
    "Indian Overseas Bank",
    "UCO Bank",
    "Yes Bank",
    "Kotak Mahindra Bank",
    "IDBI Bank",
    "South Indian Bank",
    "Federal Bank",
]

# Track generated ROC charge IDs to prevent duplicates
_generated_roc_ids = set()


# ──────────────────────────────────────────────
# Data generators
# ──────────────────────────────────────────────

def generate_roc_charge_id(prefix="1"):
    """Generate a unique ROC charge ID.

    Format: {prefix}{timestamp_secs}{random2}
    Pattern: ^(?!0+$)\\d{1,20}$  — digits only, 1-20 chars, not all zeros

    Args:
        prefix: Single digit prefix (default "1") for uniqueness.
    """
    for _ in range(500):
        ts = datetime.now().strftime("%H%M%S")
        rand = random.randint(10, 99)
        roc_id = f"{prefix}{ts}{rand}"
        if roc_id not in _generated_roc_ids:
            _generated_roc_ids.add(roc_id)
            return roc_id
    # Fallback
    fallback = f"{prefix}{datetime.now().strftime('%f')}"
    _generated_roc_ids.add(fallback)
    return fallback


def generate_type_of_charge_id():
    """Pick a random Type of Charge FK ID."""
    return random.choice(TYPE_OF_CHARGE_IDS)


def generate_description():
    """Generate a realistic description of assets/property."""
    return random.choice(_ASSET_DESCRIPTIONS)


def generate_amount_secured():
    """Generate a realistic amount secured (positive number, up to 2 decimals).

    Range: 100,000 to 50,000,000
    """
    base = random.randint(100000, 50000000)
    # 30% chance to add decimal
    if random.random() < 0.3:
        decimals = random.randint(1, 99)
        return round(base + decimals / 100, 2)
    return base


def generate_charge_holder_details():
    """Generate a realistic charge holder name with branch."""
    bank = random.choice(_CHARGE_HOLDERS)
    branch = random.choice(["Main Branch", "MIDC Branch", "Corporate Office",
                           "Regional Office", "SME Branch"])
    return f"{bank}, {branch}"


def generate_date_string(days_ago_range=730):
    """Generate a date string in ISO format (YYYY-MM-DDTHH:MM:SSZ).

    Args:
        days_ago_range: Max days in the past (default 2 years).
    """
    today = date.today()
    days_back = random.randint(1, days_ago_range)
    d = today - __import__("datetime").timedelta(days=days_back)
    return f"{d.strftime('%Y-%m-%d')}T18:30:00Z"


# ──────────────────────────────────────────────
# Valid data for UI form fill
# ──────────────────────────────────────────────

def generate_valid_data():
    """Generate complete valid data for the Register Charges form.

    Returns:
        dict with all form fields populated with realistic data.
    """
    return {
        "date_of_creation": generate_date_string(),
        "date_of_modification": generate_date_string(),
        "roc_charge_id": generate_roc_charge_id(),
        "type_of_charge_ref_id": generate_type_of_charge_id(),
        "description_of_assets_property": generate_description(),
        "amount_secured": generate_amount_secured(),
        "charge_holder_details": generate_charge_holder_details(),
        "date_of_satisfaction": None,
    }


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────

FIELD_KEY_MAP = {
    "date_of_creation": "date_of_creation",
    "date_of_modification": "date_of_modification",
    "roc_charge_id": "roc_charge_id",
    "type_of_charge_ref_id": "type_of_charge_ref_id",
    "description_of_assets_property": "description_of_assets_property",
    "amount_secured": "amount_secured",
    "charge_holder_details": "charge_holder_details",
    "date_of_satisfaction": "date_of_satisfaction",
}


def build_api_payload(data=None, fk_overrides=None):
    """Build JSON payload for POST /core/dynamic-screen-wrapper/.

    The Register Charges screen is FLAT — no steppers, no children array.
    All fields are at the root level.

    Args:
        data: Dict from generate_valid_data(). If None, auto-generates.
        fk_overrides: Optional dict of FK ID overrides.
                      Key: field_key (e.g. "type_of_charge_ref_id")
                      Value: FK ID.

    Returns:
        Complete JSON payload dict ready for POST.
    """
    if data is None:
        data = generate_valid_data()
    if fk_overrides is None:
        fk_overrides = {}

    payload = {
        "id": "",
        "attribute_name": "Register Charges",
        "date_of_creation": data.get("date_of_creation"),
        "date_of_modification": data.get("date_of_modification"),
        "roc_charge_id": data.get("roc_charge_id") or generate_roc_charge_id(),
        "type_of_charge_ref_id": fk_overrides.get("type_of_charge_ref_id")
                                  or data.get("type_of_charge_ref_id")
                                  or generate_type_of_charge_id(),
        "description_of_assets_property": data.get("description_of_assets_property"),
        "amount_secured": data.get("amount_secured") or generate_amount_secured(),
        "charge_holder_details": data.get("charge_holder_details") or generate_charge_holder_details(),
        "date_of_satisfaction": data.get("date_of_satisfaction"),
        "details": [],
        "children": [],
    }

    return payload


def generate_api_payload(**kwargs):
    """One-shot: generate a randomized Register Charges API payload.

    Args:
        **kwargs: Optional overrides for any payload field.

    Returns:
        Complete JSON payload dict ready for POST.
    """
    data = generate_valid_data()
    payload = build_api_payload(data)
    payload.update(kwargs)
    return payload


def generate_batch_payloads(count, offset=0, **kwargs):
    """Generate multiple unique Register Charges API payloads.

    Args:
        count: Number of payloads to generate.
        offset: Start index (seeds the ROC ID prefix to avoid collisions).
        **kwargs: Optional overrides applied to ALL payloads.

    Returns:
        List of payload dicts.
    """
    payloads = []
    for i in range(count):
        prefix = str((offset + i) % 9 + 1)
        p = generate_api_payload(**kwargs)
        p["roc_charge_id"] = generate_roc_charge_id(prefix=prefix)
        payloads.append(p)
    return payloads
