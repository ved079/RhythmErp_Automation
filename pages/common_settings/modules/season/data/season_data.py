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


# ================================================================
# SAFE DATA — these won't collide with existing records
# ================================================================

def _random_suffix(length=6):
    """Generate a random alphanumeric suffix to avoid collisions."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# --- Valid test data ---

def valid_season_name():
    """Unique season name for happy-path / edit tests."""
    return f"SEASON_{_random_suffix()}"


def valid_season_with_description():
    """Season name + description, both filled."""
    return {
        FIELD_NAME: f"SEASON_{_random_suffix()}",
        FIELD_DESCRIPTION: f"Test season created by automation - {_random_suffix()}",
    }


def valid_season_name_only():
    """Season name filled, description left blank (optional field)."""
    return {
        FIELD_NAME: f"SEASON_{_random_suffix()}",
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
    """Only Name filled, Description empty — should PASS (Description is optional)."""
    return {
        FIELD_NAME: f"SEASON_NAMEONLY_{_random_suffix()}",
        FIELD_DESCRIPTION: "",
    }


def sql_injection_name():
    """SQL injection payload in Name — BUG: accepted and stored as-is."""
    return {
        FIELD_NAME: f"'; DROP TABLE Season{_random_suffix()}--",
        FIELD_DESCRIPTION: "SQL injection test",
    }


def xss_in_name():
    """XSS script tag in Name — BUG: stored as raw HTML, renders in list."""
    return {
        FIELD_NAME: f"<script>alert('xss{_random_suffix()}')</script>",
        FIELD_DESCRIPTION: "XSS test",
    }


def special_chars_name():
    """Special characters in Name — BUG: accepted without validation."""
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
    """Very long string in Name field — tests max-length behavior."""
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
    """Name with leading/trailing spaces — tests trim behavior."""
    return {
        FIELD_NAME: f"  SEASON_SPACES_{_random_suffix()}  ",
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
