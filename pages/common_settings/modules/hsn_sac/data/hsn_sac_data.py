"""
HSN SAC — Test Data Generators & Field Constants
===================================================
Module has 3 fields: HSN SAC Number (text), HSN SAC Type (dropdown — 4 fixed),
HSN SAC Description (text — REQUIRED).
"""

import random
from datetime import datetime


# ─── Page URL ────────────────────────────────────────────────────────────────
PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/HSN%20SAC"


# ─── Dropdown Fixed Options ─────────────────────────────────────────────────
# HSN SAC Type has exactly 4 STATIC options — NOT dynamic.
HSN_SAC_TYPE_OPTIONS = [
    "Services",
    "Transportation",
    "Commission",
    "Commodity",
]


# ─── Field Name Constants (match input[name='...']) ────────────────────────
FIELD_HSN_NUMBER = "HSN SAC Number"
FIELD_HSN_TYPE = "HSN SAC Type"
FIELD_HSN_DESC = "HSN SAC Description"


# ─── SweetAlert2 Messages ───────────────────────────────────────────────────
SUCCESS_ADD_MESSAGE = "Your record has been added successfully!"
SUCCESS_UPDATE_MESSAGE = "Your record has been updated successfully!"
VALIDATION_FAILED_TITLE = "Validation Failed"
VALIDATION_FAILED_CONTENT = "Please correct the highlighted fields"


# ─── Table Column Constants ─────────────────────────────────────────────────
COL_VIEW = "mat-column-view"
COL_EDIT = "mat-column-edit"
COL_ARCHIVE = "mat-column-archive"  # History button lives here
COL_HSN_NO = "mat-column-hsn_sac_no"
COL_HSN_TYPE = "mat-column-hsn_sac_type"


# ─── Popup Text ─────────────────────────────────────────────────────────────
POPUP_TITLE = "HSN SAC"
HISTORY_POPUP_TITLE = "HSN SAC History"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Data Generators
# ═══════════════════════════════════════════════════════════════════════════════

def generate_hsn_sac_number() -> str:
    """Generate a random HSN SAC Number (e.g. '998300')."""
    return str(random.randint(100000, 999999))


def generate_hsn_sac_description() -> str:
    """Generate a random HSN SAC Description string."""
    return f"Auto Test HSN Desc {random.randint(1000, 9999)}"


def generate_valid_hsn_sac_data(override=None) -> dict:
    """
    Generate a complete dict with all 3 fields for a valid HSN SAC record.

    Args:
        override: Optional dict to override specific fields.
                  e.g. {"hsn_sac_type": "Services", "hsn_sac_description": "Custom"}

    Returns:
        dict with keys: hsn_sac_number, hsn_sac_type, hsn_sac_description
    """
    data = {
        "hsn_sac_number": generate_hsn_sac_number(),
        "hsn_sac_type": random.choice(HSN_SAC_TYPE_OPTIONS),
        "hsn_sac_description": generate_hsn_sac_description(),
    }
    if override:
        data.update(override)
    return data


def generate_create_test_data() -> dict:
    """Generate data specifically for CREATE tests (all fields filled)."""
    return generate_valid_hsn_sac_data()


def generate_edit_test_data(override=None) -> dict:
    """Generate data for EDIT tests (changed values to update)."""
    return generate_valid_hsn_sac_data(override=override)


# ═══════════════════════════════════════════════════════════════════════════════
# Edge-Case / Negative Test Data
# ═══════════════════════════════════════════════════════════════════════════════

def empty_fields_data() -> dict:
    """All fields empty — triggers Validation Failed."""
    return {
        "hsn_sac_number": "",
        "hsn_sac_type": "",
        "hsn_sac_description": "",
    }


def missing_number_data() -> dict:
    """HSN SAC Number empty, rest filled."""
    return {
        "hsn_sac_number": "",
        "hsn_sac_type": "Services",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


def missing_type_data() -> dict:
    """HSN SAC Type empty, rest filled."""
    return {
        "hsn_sac_number": generate_hsn_sac_number(),
        "hsn_sac_type": "",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


def missing_description_data() -> dict:
    """HSN SAC Description empty, rest filled."""
    return {
        "hsn_sac_number": generate_hsn_sac_number(),
        "hsn_sac_type": "Transportation",
        "hsn_sac_description": "",
    }


def special_chars_number_data() -> dict:
    """Special characters in HSN SAC Number."""
    return {
        "hsn_sac_number": "!@#$%^&*()",
        "hsn_sac_type": "Commission",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


def very_long_number_data() -> dict:
    """256+ character HSN SAC Number."""
    return {
        "hsn_sac_number": "A" * 300,
        "hsn_sac_type": "Commodity",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


def spaces_only_number_data() -> dict:
    """Whitespace-only HSN SAC Number."""
    return {
        "hsn_sac_number": "     ",
        "hsn_sac_type": "Services",
        "hsn_sac_description": generate_hsn_sac_description(),
    }