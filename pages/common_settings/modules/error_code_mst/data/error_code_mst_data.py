"""
Error Code Mst — Test Data Generators & Field Constants
========================================================
All test data for Error Code Mst automation.
Module has 4 fields: Error Code Type (dropdown — 4 fixed),
Code (text — REQUIRED), Description (text — optional),
Is Qty/Amt (toggle — default Amount).
"""

import random
import string
from datetime import datetime


# ─── Page URL ────────────────────────────────────────────────────────────────
PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Error%20Code%20Mst"


# ─── Dropdown Fixed Options ─────────────────────────────────────────────────
# Error Code Type has exactly 4 STATIC options — NOT dynamic.
ERROR_CODE_TYPE_OPTIONS = [
    "Farmer",
    "Debit Note",
    "Credit Note",
    "Workflow",
]


# ─── Toggle States ───────────────────────────────────────────────────────────
TOGGLE_AMOUNT = "amount"   # Default state (unchecked) → table shows "No"
TOGGLE_QUANTITY = "quantity"  # Toggled state (checked) → table shows "Yes"


# ─── Field Name Constants (match input[name='...']) ────────────────────────
FIELD_ERROR_CODE_TYPE = "Error Code Type"
FIELD_CODE = "Code"
FIELD_DESCRIPTION = "Description"
FIELD_IS_QTY_AMT = "Is Qty/Amt"


# ─── SweetAlert2 Messages ───────────────────────────────────────────────────
VALIDATION_FAILED_TITLE = "Validation Failed"
VALIDATION_FAILED_CONTENT = "Please correct the highlighted fields"
# Note: No success message popup — form closes silently on successful create/update
# Note: Duplicate also gives generic "Validation Failed" — no specific duplicate msg


# ─── Table Column Constants ─────────────────────────────────────────────────
COL_VIEW = "mat-column-view"
COL_EDIT = "mat-column-edit"
COL_ARCHIVE = "mat-column-archive"  # History button lives here
COL_ERROR_CODE_TYPE = "mat-column-error_code_type"
COL_CODE = "mat-column-code"
COL_DESCRIPTION = "mat-column-description"
COL_IS_QTY_AMT = "mat-column-is_qty_amount"


# ─── Popup Text ─────────────────────────────────────────────────────────────
POPUP_TITLE = "Error Code Mst"
HISTORY_POPUP_TITLE = "Error Code Mst History"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Data Generators
# ═══════════════════════════════════════════════════════════════════════════════

def generate_error_code() -> str:
    """Generate a random Error Code string (e.g. 'AUTOTEST5847')."""
    return f"AUTOTEST{random.randint(1000, 9999)}"


def generate_error_description() -> str:
    """Generate a random Description string."""
    return f"Auto test description {random.randint(1000, 9999)}"


def generate_valid_error_code_mst_data(override=None) -> dict:
    """
    Generate a complete dict with all 4 fields for a valid Error Code Mst record.

    Args:
        override: Optional dict to override specific fields.
                  e.g. {"code": "CUSTOM01", "is_qty_amt": "quantity"}

    Returns:
        dict with keys: error_code_type, code, description, is_qty_amt
    """
    data = {
        "error_code_type": random.choice(ERROR_CODE_TYPE_OPTIONS),
        "code": generate_error_code(),
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,  # Default: amount (off)
    }
    if override:
        data.update(override)
    return data


def generate_create_test_data() -> dict:
    """Generate data specifically for CREATE tests (all fields filled)."""
    return generate_valid_error_code_mst_data()


def generate_edit_test_data(override=None) -> dict:
    """Generate data for EDIT tests (changed values to update)."""
    return generate_valid_error_code_mst_data(override=override)


def generate_create_with_toggle_qty() -> dict:
    """Generate data with toggle set to Quantity."""
    return generate_valid_error_code_mst_data(override={"is_qty_amt": TOGGLE_QUANTITY})


def generate_create_without_description() -> dict:
    """Generate data without Description (optional field)."""
    return {
        "error_code_type": random.choice(ERROR_CODE_TYPE_OPTIONS),
        "code": generate_error_code(),
        "description": "",
        "is_qty_amt": TOGGLE_AMOUNT,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Edge-Case / Negative Test Data
# ═══════════════════════════════════════════════════════════════════════════════

def empty_fields_data() -> dict:
    """All fields empty — triggers Validation Failed."""
    return {
        "error_code_type": "",
        "code": "",
        "description": "",
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def missing_dropdown_data() -> dict:
    """Error Code Type empty, rest filled."""
    return {
        "error_code_type": "",
        "code": generate_error_code(),
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def missing_code_data() -> dict:
    """Code empty, rest filled."""
    return {
        "error_code_type": "Farmer",
        "code": "",
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def special_chars_code_data() -> dict:
    """Special characters in Code."""
    return {
        "error_code_type": "Credit Note",
        "code": "TEST@#$%^&*()",
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def very_long_code_data() -> dict:
    """256+ character Code."""
    return {
        "error_code_type": "Workflow",
        "code": "A" * 300,
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def spaces_only_code_data() -> dict:
    """Whitespace-only Code."""
    return {
        "error_code_type": "Debit Note",
        "code": "     ",
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def very_long_description_data() -> dict:
    """500+ character Description."""
    return {
        "error_code_type": "Farmer",
        "code": generate_error_code(),
        "description": "A" * 500,
        "is_qty_amt": TOGGLE_QUANTITY,
    }
