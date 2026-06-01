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


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the existing UI data format into the JSON payload
# that POST /core/dynamic-screen-wrapper/ expects.
#
# ERROR CODE MST SCREEN STRUCTURE (flat — no children, no steppers):
#   {
#     "id": "",
#     "attribute_name": "Error Code Mst",
#     "error_code_type_ref_id": <FK_ID>,
#     "code": "FARM_INV_001",
#     "description": "Farmer inventory error",
#     "is_qty_amount": false,
#     "status": true
#   }
#
# FIELD KEY MAPPING (reasonable guess — to be verified by discover_all.py):
#   error_code_type  -> error_code_type_ref_id (FK dropdown — 4 fixed options)
#   code             -> code (text, required)
#   description      -> description (text, optional)
#   is_qty_amt       -> is_qty_amount (boolean toggle)
#   status           -> status (boolean, default true)
# ──────────────────────────────────────────────

# Placeholder FK IDs for the 4 Error Code Type dropdown options.
# These will be populated after running discover_all.py against the live API.
ERROR_CODE_TYPE_IDS = {
    "Farmer": None,         # To be filled from discovery
    "Debit Note": None,     # To be filled from discovery
    "Credit Note": None,    # To be filled from discovery
    "Workflow": None,       # To be filled from discovery
}

# Realistic error code patterns for API batch creation (Indian ERP context)
# Format: {type_name: [code_prefix, description_template]}
ERROR_CODE_PATTERNS = {
    "Farmer": [
        {"code": "FARM_INV_001", "description": "Farmer inventory record not found"},
        {"code": "FARM_INV_002", "description": "Duplicate farmer registration detected"},
        {"code": "FARM_INV_003", "description": "Farmer bank details verification failed"},
        {"code": "FARM_INV_004", "description": "Farmer land holding exceeds sanctioned limit"},
        {"code": "FARM_INV_005", "description": "Farmer KYC documents pending verification"},
        {"code": "FARM_PMT_001", "description": "Farmer payment processing error"},
        {"code": "FARM_PMT_002", "description": "Farmer payment amount mismatch"},
        {"code": "FARM_PMT_003", "description": "Farmer bank account validation failed"},
        {"code": "FARM_DOC_001", "description": "Farmer document upload failed"},
        {"code": "FARM_DOC_002", "description": "Farmer Aadhaar verification timeout"},
        {"code": "FARM_LND_001", "description": "Land survey number mismatch"},
        {"code": "FARM_LND_002", "description": "Land area exceeds registered extent"},
        {"code": "FARM_LND_003", "description": "Land ownership transfer pending"},
    ],
    "Debit Note": [
        {"code": "DBT_NOTE_001", "description": "Debit note amount exceeds invoice value"},
        {"code": "DBT_NOTE_002", "description": "Debit note reference invoice not found"},
        {"code": "DBT_NOTE_003", "description": "Debit note tax calculation discrepancy"},
        {"code": "DBT_NOTE_004", "description": "Debit note approval workflow rejected"},
        {"code": "DBT_NOTE_005", "description": "Debit note GST reverse charge error"},
        {"code": "DBT_NOTE_006", "description": "Debit note TDS deduction mismatch"},
        {"code": "DBT_NOTE_007", "description": "Debit note vendor settlement failed"},
        {"code": "DBT_NOTE_008", "description": "Debit note financial year closure conflict"},
    ],
    "Credit Note": [
        {"code": "CRD_NOTE_001", "description": "Credit note amount exceeds invoice value"},
        {"code": "CRD_NOTE_002", "description": "Credit note reference invoice not found"},
        {"code": "CRD_NOTE_003", "description": "Credit note tax calculation discrepancy"},
        {"code": "CRD_NOTE_004", "description": "Credit note GST adjustment error"},
        {"code": "CRD_NOTE_005", "description": "Credit note customer settlement failed"},
        {"code": "CRD_NOTE_006", "description": "Credit note against cancelled invoice"},
        {"code": "CRD_NOTE_007", "description": "Credit note partial adjustment overflow"},
    ],
    "Workflow": [
        {"code": "WKFLW_001", "description": "Workflow approval timeout exceeded"},
        {"code": "WKFLW_002", "description": "Workflow escalation rule triggered"},
        {"code": "WKFLW_003", "description": "Workflow parallel approval conflict"},
        {"code": "WKFLW_004", "description": "Workflow state transition invalid"},
        {"code": "WKFLW_005", "description": "Workflow role assignment missing"},
        {"code": "WKFLW_006", "description": "Workflow notification delivery failed"},
        {"code": "WKFLW_007", "description": "Workflow auto-approval condition unmet"},
        {"code": "WKFLW_008", "description": "Workflow rollback operation failed"},
    ],
}

# Track used codes to avoid duplicates within a batch
_used_error_codes = set()


def generate_realistic_error_code(type_name=None):
    """Generate a realistic error code entry for the given type.
    If type_name is None, picks a random type.

    Returns:
        Dict with error_code_type, code, description, is_qty_amt keys.
    """
    if type_name is None:
        type_name = random.choice(ERROR_CODE_TYPE_OPTIONS)

    patterns = ERROR_CODE_PATTERNS.get(type_name, [])
    if not patterns:
        # Fallback: generate a generic code
        code = f"{type_name.upper().replace(' ', '_')[:6]}_{random.randint(100, 999)}"
        desc = f"Error code for {type_name} module"
    else:
        pattern = random.choice(patterns)
        code = pattern["code"]
        desc = pattern["description"]

    # Ensure uniqueness within batch
    if code in _used_error_codes:
        suffix = random.randint(10, 99)
        code = f"{code}_{suffix}"
        desc = f"{desc} (Variant {suffix})"
    _used_error_codes.add(code)

    return {
        "error_code_type": type_name,
        "code": code,
        "description": desc,
        "is_qty_amt": random.choice([TOGGLE_AMOUNT, TOGGLE_QUANTITY]),
    }


def reset_error_code_pool():
    """Reset the used-code tracker (call before a new batch)."""
    _used_error_codes.clear()


def build_error_code_mst_api_payload(data=None, dropdown_ids=None):
    """Build the Error Code Mst API payload from data dict.

    Args:
        data: Dict from generate_valid_error_code_mst_data() or None for random.
        dropdown_ids: Dict mapping error_code_type names to FK IDs.
                      Example: {"Farmer": 123, "Debit Note": 456, ...}
                      If a type has no ID, it is set to None (will fail on API).

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    if data is None:
        data = generate_valid_error_code_mst_data()

    ids = dropdown_ids or {}

    # Resolve error_code_type to FK ref ID
    type_name = data.get("error_code_type", "")
    type_ref_id = None
    if type_name and ids:
        # Try provided dropdown_ids first, then fall back to ERROR_CODE_TYPE_IDS
        type_ref_id = ids.get(type_name) or ERROR_CODE_TYPE_IDS.get(type_name)
    elif type_name:
        type_ref_id = ERROR_CODE_TYPE_IDS.get(type_name)

    # Determine is_qty_amount boolean
    is_qty_amt_str = data.get("is_qty_amt", TOGGLE_AMOUNT)
    is_qty_amount = is_qty_amt_str == TOGGLE_QUANTITY

    payload = {
        "id": "",
        "attribute_name": "Error Code Mst",
        "error_code_type_ref_id": type_ref_id,
        "code": data.get("code", ""),
        "description": data.get("description", "") or None,
        "is_qty_amount": is_qty_amount,
        "status": True,
    }
    return payload


def generate_error_code_mst_api_payload(name_prefix=None, dropdown_ids=None):
    """One-shot: generate a complete Error Code Mst API payload with realistic data.

    Args:
        name_prefix: Ignored (realistic error codes are used instead).
        dropdown_ids: Dict mapping error_code_type names to FK IDs.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    data = generate_realistic_error_code()
    return build_error_code_mst_api_payload(data, dropdown_ids)


def generate_error_code_mst_api_payloads(count=20, prefix=None, dropdown_ids=None):
    """Generate multiple unique Error Code Mst API payloads for batch creation.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored (realistic error codes are used instead).
        dropdown_ids: Dict mapping error_code_type names to FK IDs.

    Returns:
        List of JSON payloads.
    """
    reset_error_code_pool()
    payloads = []
    for _ in range(count):
        payloads.append(
            generate_error_code_mst_api_payload(prefix, dropdown_ids)
        )
    return payloads
