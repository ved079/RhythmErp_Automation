"""
Tax Rate — Test Data Generators & Field Constants
=================================================
All test data for Tax Rate automation.
Module: 6 header fields + nested sub-table (HSN Number + Tax Rate).
Complexity: HIGHEST in Common Settings (nested editable sub-table).
"""

import random
import string
from datetime import datetime, timedelta


# ─── Page URL ────────────────────────────────────────────────────────────────
PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Rate"


# ─── Dropdown Options ───────────────────────────────────────────────────────
# Tax Type — only 1 option
TAX_TYPE_OPTIONS = ["GST"]

# Tax Authority — 6 options (dynamic, retrieve live)
TAX_AUTHORITY_OPTIONS = [
    "GST",
    "Test206",
    "ggf",
    "Enterprises",
    "Test147",
    "SQL_INJECT_TEST",
]

# HSN Number — 23+ options from HSN SAC master (dynamic, retrieve live)
HSN_NUMBER_OPTIONS = [
    "997212",
    "10059011",
    "12024200",
    "7133100",
    "7136000",
    "11061000",
    "10063000",
    "10059000",
    "10019900",
    "9103000",
    "7132010",
    "7132000",
    "12010000",
    "998811",
]


# ─── Field Name Constants ────────────────────────────────────────────────────
FIELD_TAX_RATE_NAME = "Tax Rate Name"
FIELD_TAX_TYPE = "Tax Type"
FIELD_TAX_AUTHORITY = "Tax Authority"
FIELD_FROM_DATE = "From Date"
FIELD_TO_DATE = "To Date"
FIELD_REVISION_STATUS = "Revision Status"
FIELD_HSN_NUMBER = "HSN Number"
FIELD_TAX_RATE = "Tax Rate"


# ─── Date Defaults ───────────────────────────────────────────────────────────
# From Date auto-fills with current date (DD/MM/YYYY format)
# To Date defaults to 30/12/2099 on server when left empty
DEFAULT_TO_DATE_DISPLAY = "30/12/2099"
DEFAULT_TO_DATE_ISO = "2099-12-30T18:30:00Z"

# Revision Status common values
REVISION_STATUSES = ["effective", "Effective", "draft", "Draft"]


# ─── SweetAlert2 Messages ───────────────────────────────────────────────────
VALIDATION_FAILED_TITLE = "Validation Failed"
VALIDATION_FAILED_CONTENT = "Please correct the highlighted fields"
# Note: No success SweetAlert2 — form closes silently on success (TR-03)
# Note: Same generic "Validation Failed" for all errors — empty, duplicate, etc.


# ─── Table Column Constants ─────────────────────────────────────────────────
COL_VIEW = "mat-column-view"
COL_EDIT = "mat-column-edit"
COL_FOLDER = "mat-column-folder"          # Version button (unique to Tax Rate)
COL_ARCHIVE = "mat-column-archive"
COL_TAX_RATE_NAME = "mat-column-tax_rate_name"
COL_TAX_TYPE = "mat-column-tax_type_ref_id"
COL_TAX_AUTHORITY = "mat-column-tax_authority_ref_id"
COL_FROM_DATE = "mat-column-from_date"
COL_TO_DATE = "mat-column-to_date"
COL_REVISION_STATUS = "mat-column-revision_status"


# ─── Sub-Table Column Constants ─────────────────────────────────────────────
# Inside the "Define Tax Rate Details" tab
SUB_COL_ACTION = "ACTION"
SUB_COL_HSN_NUMBER = "HSN NUMBER"
SUB_COL_TAX_RATE = "TAX RATE"
SUB_TABLE_ROWS_PER_PAGE = 5


# ─── Popup Text ─────────────────────────────────────────────────────────────
POPUP_TITLE = "Tax Rate"
HISTORY_POPUP_TITLE = "Tax Rate History"
VERSION_BUTTON_TEXT = "Create Version"     # Version form uses this instead of Submit/Update


# ─── Bug Registry ────────────────────────────────────────────────────────────
BUG_REGISTRY = {
    "TR-01": {
        "severity": "HIGH",
        "title": "SQL injection accepted in Tax Rate Name",
        "description": "Input like 'DROP TABLE tax;--' is accepted and stored as-is.",
        "category": "Security",
    },
    "TR-02": {
        "severity": "MEDIUM",
        "title": "Edit button permanently disabled — use Version instead",
        "description": "All records show disabled Edit button. Version button (folder icon) opens editable form with 'Create Version' button.",
        "category": "Functionality",
    },
    "TR-03": {
        "severity": "LOW",
        "title": "No success SweetAlert2 on create/version",
        "description": "Form closes silently on success. No success popup visible.",
        "category": "UI/UX",
    },
    "TR-04": {
        "severity": "INFO",
        "title": "Date fields have name=null",
        "description": "From Date and To Date inputs have no name attribute. Must locate via mat-label traversal.",
        "category": "Technical",
    },
    "TR-05": {
        "severity": "INFO",
        "title": "HSN Number has duplicate entries",
        "description": "HSN '7133100' appears twice in dropdown (inherited from HSN SAC master data).",
        "category": "Data Integrity",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Test Data Generators
# ═══════════════════════════════════════════════════════════════════════════════

def generate_tax_rate_name() -> str:
    """Generate a random Tax Rate Name (e.g. 'AUTOTEST_RATE5847')."""
    return f"AUTOTEST_RATE{random.randint(1000, 9999)}"


def generate_revision_status() -> str:
    """Generate a random revision status."""
    return random.choice(REVISION_STATUSES)


def generate_tax_rate_value() -> float:
    """Generate a random tax rate percentage (1-28)."""
    return round(random.uniform(1, 28), 2)


def generate_valid_tax_rate_data(override=None) -> dict:
    """
    Generate a complete dict for a valid Tax Rate record (header fields).
    
    Args:
        override: Optional dict to override specific fields.
    
    Returns:
        dict with keys: tax_rate_name, tax_type, tax_authority, from_date, to_date, revision_status
    """
    today = datetime.now()
    data = {
        "tax_rate_name": generate_tax_rate_name(),
        "tax_type": "GST",
        "tax_authority": random.choice(TAX_AUTHORITY_OPTIONS),
        "from_date": today.strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": generate_revision_status(),
    }
    if override:
        data.update(override)
    return data


def generate_sub_table_row(override=None) -> dict:
    """
    Generate a single sub-table row (HSN Number + Tax Rate).
    
    Args:
        override: Optional dict to override specific fields.
    
    Returns:
        dict with keys: hsn_number, tax_rate
    """
    data = {
        "hsn_number": random.choice(HSN_NUMBER_OPTIONS),
        "tax_rate": generate_tax_rate_value(),
    }
    if override:
        data.update(override)
    return data


def generate_create_test_data() -> dict:
    """Generate data specifically for CREATE tests (header + 1 sub-table row)."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [generate_sub_table_row()],
    }


def generate_create_multi_row_data(row_count=3) -> dict:
    """Generate data with multiple sub-table rows."""
    rows = [generate_sub_table_row() for _ in range(row_count)]
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": rows,
    }


def generate_version_test_data(override=None) -> dict:
    """Generate data for Version tests (pre-filled, change one field)."""
    data = generate_valid_tax_rate_data(override=override)
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# Edge-Case / Negative Test Data
# ═══════════════════════════════════════════════════════════════════════════════

def empty_fields_data() -> dict:
    """All header fields empty — triggers Validation Failed."""
    return {
        "tax_rate_name": "",
        "tax_type": "",
        "tax_authority": "",
        "from_date": "",
        "to_date": "",
        "revision_status": "",
    }


def missing_name_data() -> dict:
    """Tax Rate Name empty, rest filled."""
    return {
        "tax_rate_name": "",
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def missing_tax_type_data() -> dict:
    """Tax Type empty, rest filled."""
    return {
        "tax_rate_name": generate_tax_rate_name(),
        "tax_type": "",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def missing_tax_authority_data() -> dict:
    """Tax Authority empty, rest filled."""
    return {
        "tax_rate_name": generate_tax_rate_name(),
        "tax_type": "GST",
        "tax_authority": "",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def missing_revision_status_data() -> dict:
    """Revision Status empty, rest filled."""
    return {
        "tax_rate_name": generate_tax_rate_name(),
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "",
    }


def sql_injection_name_data() -> dict:
    """SQL injection in Tax Rate Name."""
    return {
        "tax_rate_name": "DROP TABLE tax;--",
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def special_chars_name_data() -> dict:
    """Special characters in Tax Rate Name."""
    return {
        "tax_rate_name": "TEST@#$%^&*()",
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def very_long_name_data() -> dict:
    """256+ character Tax Rate Name."""
    return {
        "tax_rate_name": "A" * 300,
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def negative_tax_rate_data() -> dict:
    """Negative tax rate value in sub-table."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [{"hsn_number": "997212", "tax_rate": -5.0}],
    }


def zero_tax_rate_data() -> dict:
    """Zero tax rate value in sub-table."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [{"hsn_number": "997212", "tax_rate": 0}],
    }


def very_large_tax_rate_data() -> dict:
    """Very large tax rate value (999999)."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [{"hsn_number": "997212", "tax_rate": 999999}],
    }


def empty_sub_table_data() -> dict:
    """Header filled but sub-table empty (no HSN/Tax Rate rows)."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [],
    }


def unselected_hsn_data() -> dict:
    """Sub-table row with HSN Number left as 'Select HSN Number'."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [{"hsn_number": "", "tax_rate": 18.0}],
    }