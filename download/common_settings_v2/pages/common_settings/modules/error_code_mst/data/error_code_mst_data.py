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

IS_QTY_AMOUNT_OPTIONS = ["Qty", "Amount"]


# ── Payload builder ──────────────────────────────────────────────────

def build_error_code_mst_api_payload(error_code_type_id, code, description,
                                      is_qty_amount="Qty"):
    """Build a single API payload for Error Code Mst."""
    return {
        "id": "",
        "error_code_type": error_code_type_id,
        "code": code,
        "description": description,
        "is_qty_amount": is_qty_amount,
        "attribute_name": "Error Code Mst",
    }


def generate_error_code_mst_api_payloads(count=10, fk_ids=None):
    """
    Generate N API payloads for Error Code Mst.

    Args:
        count: Number of payloads to generate
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
        # Pick a type (cycle for variety)
        type_idx = i % len(type_names)
        type_name = type_names[type_idx]
        type_id = type_id_list[type_idx]

        # Pick a code from that type's pool
        available_codes = CODES_BY_TYPE.get(type_name, list(CODES_BY_TYPE.values())[0])
        # Add index suffix for uniqueness
        code = available_codes[i % len(available_codes)]
        if code in used_codes:
            code = f"{code}-{i+1:02d}"
        used_codes.add(code)

        # Pick a description
        available_descs = DESCRIPTIONS_BY_TYPE.get(type_name, list(DESCRIPTIONS_BY_TYPE.values())[0])
        description = available_descs[i % len(available_descs)]

        # Pick is_qty_amount
        is_qty_amount = IS_QTY_AMOUNT_OPTIONS[i % len(IS_QTY_AMOUNT_OPTIONS)]

        payload = build_error_code_mst_api_payload(
            error_code_type_id=type_id,
            code=code,
            description=description,
            is_qty_amount=is_qty_amount,
        )
        payloads.append(payload)

    return payloads
