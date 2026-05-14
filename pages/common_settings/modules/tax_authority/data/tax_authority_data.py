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
