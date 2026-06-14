#!/usr/bin/env python3
"""
Error Code Mst — Data pool + API payload builder.

Screen: "Error Code Mst" (flat, 1 dropdown: error_code_type)
Fields: error_code_type, code, description, is_qty_amount
"""

import random

# ── Realistic data pools ─────────────────────────────────────────────

# Real FK IDs discovered from live ERP (discover_all.py run 2026-06-02)
# Screen: Error Code Type → dropdown field: error_code_type
ERROR_CODE_TYPE_IDS = {
    "Farmer":      643,
    "Debit Note":  216,
    "Credit Note": 215,
    "Workflow":    140,
}

ERROR_CODE_TYPES = list(ERROR_CODE_TYPE_IDS.keys())

# ── Page constants (used by error_code_mst_page.py) ──────────────────
PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Error%20Code%20Mst"
FIELD_ERROR_CODE_TYPE = "Error Code Type"
FIELD_CODE = "Code"
FIELD_DESCRIPTION = "Description"
FIELD_IS_QTY_AMT = "Is Qty/Amount"
VALIDATION_FAILED_TITLE = "Validation Failed"
VALIDATION_FAILED_CONTENT = "Please correct the highlighted fields"
POPUP_TITLE = "Error Code Mst"
HISTORY_POPUP_TITLE = "Error Code Mst History"
ERROR_CODE_TYPE_OPTIONS = list(ERROR_CODE_TYPE_IDS.keys())
TOGGLE_AMOUNT = "Amount"
TOGGLE_QUANTITY = "Qty"

CODES_BY_TYPE = {
    "Farmer":       ["FM-DOC", "FM-KYC", "FM-LAND", "FM-BANK", "FM-VERIFY"],
    "Debit Note":   ["DN-REJ", "DN-SHORT", "DN-DAMG", "DN-PRICE", "DN-QTY"],
    "Credit Note":  ["CN-RETN", "CN-OVER", "CN-ADJ", "CN-DISC", "CN-REBATE"],
    "Workflow":     ["WF-APPR", "WF-REJ", "WF-HOLD", "WF-ESC", "WF-RTRY"],
}

DESCRIPTIONS_BY_TYPE = {
    "Farmer": [
        "Farmer documentation incomplete or missing",
        "Farmer KYC verification failed or pending",
        "Land record discrepancy in farmer registration",
        "Bank account details mismatch for farmer payout",
        "Farmer identity verification requires re-check",
    ],
    "Debit Note": [
        "Debit note raised for rejected material",
        "Quantity shortage — debit note for shortfall",
        "Debit note for damaged goods received",
        "Price variance — debit note for overcharge",
        "Debit note for quantity discrepancy in delivery",
    ],
    "Credit Note": [
        "Credit note for returned goods",
        "Credit note for overpayment adjustment",
        "Credit note for general ledger adjustment",
        "Credit note for discount not applied",
        "Credit note for rebate as per agreement",
    ],
    "Workflow": [
        "Workflow approval pending at approver level",
        "Workflow rejected — requires resubmission",
        "Workflow on hold pending additional info",
        "Workflow escalation — exceeded SLA threshold",
        "Workflow retry — auto-retry after transient failure",
    ],
}

IS_QTY_AMOUNT_OPTIONS = [True, False]


# ── Payload builder ──────────────────────────────────────────────────

def build_error_code_mst_api_payload(error_code_type_id, code, description,
                                      is_qty_amount=True):
    """Build a single API payload for Error Code Mst."""
    return {
        "id": "",
        "error_code_type": error_code_type_id,
        "code": code,
        "description": description,
        "is_qty_amount": is_qty_amount,
        "attribute_name": "Error Code Mst",
    }


def generate_error_code_mst_api_payloads(count=10, offset=0, fk_ids=None):
    """
    Generate N API payloads for Error Code Mst.

    Args:
        count: Number of payloads to generate
        offset: Start index in data pool
        fk_ids: dict with resolved FK IDs, e.g.:
            {"error_code_type": {name: id, ...}}

    Returns:
        list[dict]: List of API payloads
    """
    if fk_ids is None:
        fk_ids = {}

    payloads = []
    # Merge discovered FK IDs with hardcoded ones (discovered take precedence)
    ec_type_ids = {**ERROR_CODE_TYPE_IDS, **fk_ids.get("error_code_type", {})}

    type_names = list(ec_type_ids.keys())
    type_id_list = list(ec_type_ids.values())

    used_codes = set()

    for i in range(count):
        idx = offset + i
        # Pick a type (cycle for variety)
        type_idx = idx % len(type_names)
        type_name = type_names[type_idx]
        type_id = type_id_list[type_idx]

        # Pick a code from that type's pool
        available_codes = CODES_BY_TYPE.get(type_name, list(CODES_BY_TYPE.values())[0])
        # Add index suffix for uniqueness
        code = available_codes[idx % len(available_codes)]
        if code in used_codes:
            code = f"{code}-{idx+1:02d}"
        used_codes.add(code)

        # Pick a description
        available_descs = DESCRIPTIONS_BY_TYPE.get(type_name, list(DESCRIPTIONS_BY_TYPE.values())[0])
        description = available_descs[idx % len(available_descs)]

        # Pick is_qty_amount
        is_qty_amount = IS_QTY_AMOUNT_OPTIONS[idx % len(IS_QTY_AMOUNT_OPTIONS)]

        payload = build_error_code_mst_api_payload(
            error_code_type_id=type_id,
            code=code,
            description=description,
            is_qty_amount=is_qty_amount,
        )
        payloads.append(payload)

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Error Code Mst is a flat screen — no children, no steppers.
# 3 standard fields + 1 FK dropdown + 1 string enum = 5 fields.

FIELD_VALIDATION_RULES = {
    "error_code_type": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(ERROR_CODE_TYPE_IDS),
        "note": "FK to Error Code Type. 4 options: Farmer, Debit Note, Credit Note, Workflow.",
    },
    "code": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Error code identifier. Alphanumeric with hyphens (e.g. FM-DOC, DN-REJ).",
    },
    "description": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Human-readable description of the error code.",
    },
    "is_qty_amount": {
        "type": "character",
        "required": True,
        "note": "Enum: 'Qty' or 'Amount'. Determines how the error code is applied.",
    },
}

# Error Code Type display names for schema tests
ERROR_CODE_TYPE_NAMES = dict(ERROR_CODE_TYPE_IDS)

# is_qty_amount options
IS_QTY_AMOUNT_NAMES = ["Qty", "Amount"]

# Default FK IDs for Error Code Mst
DEFAULT_ERROR_CODE_MST_FK_IDS = {
    "error_code_type": ERROR_CODE_TYPE_IDS,
}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
    offset: int = 0,
) -> list:
    """Generate a batch of unique Error Code Mst API payloads."""
    return generate_error_code_mst_api_payloads(count=count, offset=offset, fk_ids=dropdown_ids)


# ── UI Validation Helpers (restored for test compatibility) ──

_ec_counter = 0


def generate_error_code():
    """Return a unique error code string."""
    global _ec_counter
    _ec_counter += 1
    return f"EC-AUTO-{_ec_counter:04d}"


def generate_error_description():
    """Return a unique error description string."""
    global _ec_counter
    _ec_counter += 1
    return f"Auto-test error description {_ec_counter}"


def generate_valid_error_code_mst_data():
    """Return a dict with all fields for UI create_record."""
    ec_type = random.choice(ERROR_CODE_TYPE_OPTIONS)
    return {
        "error_code_type": ec_type,
        "code": generate_error_code(),
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def generate_create_test_data():
    """Return a dict with all fields for UI create_record (alias)."""
    return generate_valid_error_code_mst_data()


def generate_edit_test_data():
    """Return a dict with fields for UI edit_record."""
    return {
        "error_code_type": random.choice(ERROR_CODE_TYPE_OPTIONS),
        "code": generate_error_code(),
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def generate_create_with_toggle_qty():
    """Return valid data with toggle set to Quantity."""
    ec_type = random.choice(ERROR_CODE_TYPE_OPTIONS)
    return {
        "error_code_type": ec_type,
        "code": generate_error_code(),
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_QUANTITY,
    }


def generate_create_without_description():
    """Return valid data without description (optional)."""
    ec_type = random.choice(ERROR_CODE_TYPE_OPTIONS)
    return {
        "error_code_type": ec_type,
        "code": generate_error_code(),
        "description": "",
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def empty_fields_data():
    """Return a dict with all fields empty."""
    return {
        "error_code_type": "",
        "code": "",
        "description": "",
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def missing_dropdown_data():
    """Return a dict with dropdown empty but code and description filled."""
    return {
        "error_code_type": "",
        "code": generate_error_code(),
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def missing_code_data():
    """Return a dict with code empty but dropdown and description filled."""
    return {
        "error_code_type": random.choice(ERROR_CODE_TYPE_OPTIONS),
        "code": "",
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def special_chars_code_data():
    """Return a dict with special characters in code field."""
    ec_type = random.choice(ERROR_CODE_TYPE_OPTIONS)
    return {
        "error_code_type": ec_type,
        "code": "TEST@#$%^&*()",
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def very_long_code_data():
    """Return a dict with a very long code string (256 chars)."""
    ec_type = random.choice(ERROR_CODE_TYPE_OPTIONS)
    return {
        "error_code_type": ec_type,
        "code": "A" * 256,
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def spaces_only_code_data():
    """Return a dict with spaces-only code."""
    ec_type = random.choice(ERROR_CODE_TYPE_OPTIONS)
    return {
        "error_code_type": ec_type,
        "code": "     ",
        "description": generate_error_description(),
        "is_qty_amt": TOGGLE_AMOUNT,
    }


def very_long_description_data():
    """Return a dict with a very long description string (256 chars)."""
    ec_type = random.choice(ERROR_CODE_TYPE_OPTIONS)
    return {
        "error_code_type": ec_type,
        "code": generate_error_code(),
        "description": "D" * 256,
        "is_qty_amt": TOGGLE_AMOUNT,
    }
