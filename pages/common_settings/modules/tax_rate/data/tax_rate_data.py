#!/usr/bin/env python3
"""
Tax Rate — Data pool + API payload builder.

Screen: "Tax Rate" (COMPLEX — has stepper "Define Tax Rate Details")
Fields: tax_rate_name, tax_type_ref_id, tax_authority_ref_id,
        from_date, to_date, revision_status
+ Stepper children with tax rate detail lines (hsn_sac_number + tax_rate)

Discovered FK IDs (2026-06-02):
  tax_type_ref_id:       GST=93
  tax_authority_ref_id:  20 authorities (CGST=103, SGST=104, IGST=105, etc.)
  hsn_sac_number:        24 HSN/SAC codes (in stepper detail)
"""

import random
from datetime import date

# ── Realistic GST rate structures ────────────────────────────────────

GST_RATES = [
    {"name": "GST Zero Nil",              "rate": 0.0,    "cgst": 0.0,    "sgst": 0.0,    "igst": 0.0,    "cess": 0.0},
    {"name": "GST Zero Two Five",          "rate": 0.25,   "cgst": 0.125,  "sgst": 0.125,  "igst": 0.25,   "cess": 0.0},
    {"name": "GST Three",                  "rate": 3.0,    "cgst": 1.5,    "sgst": 1.5,    "igst": 3.0,    "cess": 0.0},
    {"name": "GST Five",                   "rate": 5.0,    "cgst": 2.5,    "sgst": 2.5,    "igst": 5.0,    "cess": 0.0},
    {"name": "GST Twelve",                 "rate": 12.0,   "cgst": 6.0,    "sgst": 6.0,    "igst": 12.0,   "cess": 0.0},
    {"name": "GST Fifteen",                "rate": 15.0,   "cgst": 7.5,    "sgst": 7.5,    "igst": 15.0,   "cess": 0.0},
    {"name": "GST Eighteen",               "rate": 18.0,   "cgst": 9.0,    "sgst": 9.0,    "igst": 18.0,   "cess": 0.0},
    {"name": "GST Twenty Eight",           "rate": 28.0,   "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 0.0},
    {"name": "GST Five Plus Cess",         "rate": 5.0,    "cgst": 2.5,    "sgst": 2.5,    "igst": 5.0,    "cess": 2.5},
    {"name": "GST Twelve Plus Cess",       "rate": 12.0,   "cgst": 6.0,    "sgst": 6.0,    "igst": 12.0,   "cess": 5.0},
    {"name": "GST Eighteen Plus Cess",     "rate": 18.0,   "cgst": 9.0,    "sgst": 9.0,    "igst": 18.0,   "cess": 10.0},
    {"name": "GST Twenty Eight Plus Cess", "rate": 28.0,   "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 15.0},
    {"name": "GST Twenty Eight Twelve Cess","rate": 28.0,  "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 12.0},
    {"name": "GST Twenty Eight Sixty Cess", "rate": 28.0,  "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 60.0},
    {"name": "GST Eighteen One Cess",       "rate": 18.0,  "cgst": 9.0,    "sgst": 9.0,    "igst": 18.0,   "cess": 1.0},
    {"name": "GST Twelve Two Cess",         "rate": 12.0,  "cgst": 6.0,    "sgst": 6.0,    "igst": 12.0,   "cess": 2.0},
    {"name": "GST Five One Cess",           "rate": 5.0,   "cgst": 2.5,    "sgst": 2.5,    "igst": 5.0,    "cess": 1.0},
    {"name": "GST Twenty Eight Two Zero Four Cess", "rate": 28.0, "cgst": 14.0, "sgst": 14.0, "igst": 28.0, "cess": 204.0},
    {"name": "GST Five Five Cess",          "rate": 5.0,   "cgst": 2.5,    "sgst": 2.5,    "igst": 5.0,    "cess": 5.0},
    {"name": "GST Twenty Eight Eighteen Cess","rate": 28.0,"cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 18.0},
]

# ── Tenant-agnostic display name pool for HSN/SAC codes ───────────────
# These are used as lookup keys for the FkResolver against the "HSN SAC" screen.
# No hardcoded IDs — resolved at runtime via API.
HSN_SAC_CODES = [
    "995411", "995412", "995421", "995422",
    "0101",   "0201",   "0301",   "0401",
    "0501",   "0601",   "0701",   "0801",
    "0901",   "1001",   "995413", "995414",
    "995415", "996311", "996312", "997111",
    "997112", "997113", "996211", "996212",
]


# ── Payload builder ──────────────────────────────────────────────────

def build_tax_rate_api_payload(tax_rate_name, tax_type_ref_id, tax_authority_ref_id,
                                from_date, to_date, revision_status="Active",
                                tax_detail_lines=None):
    """
    Build a single API payload for Tax Rate.

    This screen has a STEPPER structure with "Define Tax Rate Details" sub-table.
    Each detail line has: hsn_sac_number (FK) + tax_rate (numeric percentage)
    """
    children_details = tax_detail_lines or [{}]

    payload = {
        "id": "",
        "tax_rate_name": tax_rate_name,
        "tax_type_ref_id": tax_type_ref_id,
        "tax_authority_ref_id": tax_authority_ref_id,
        "from_date": from_date,
        "to_date": to_date,
        "revision_status": revision_status,
        "attribute_name": "Tax Rate",
        "children": [
            {
                "stepper_name": "Define Tax Rate Details",
                "is_stepper": True,
                "details": children_details,
                "children": [],
            }
        ],
    }
    return payload


def _generate_tax_detail_lines(rate_info, hsn_sac_ids):
    """
    Generate tax rate detail lines using real HSN/SAC number IDs.

    For Indian GST, each tax rate maps to HSN/SAC codes.
    We create one detail line per HSN/SAC code with the tax rate percentage.
    """
    lines = []
    # Use up to 3 HSN/SAC codes per tax rate for variety
    hsn_items = list(hsn_sac_ids.items())
    # Pick some HSN/SAC codes (spread across the list)
    indices = [0, len(hsn_items)//3, 2*len(hsn_items)//3]
    selected = [hsn_items[idx % len(hsn_items)] for idx in indices]

    tax_rate_val = random.choice([5,10])
    for hsn_code, hsn_id in selected:
        line = {
            "hsn_sac_number": hsn_id,
            "tax_rate": tax_rate_val,
        }
        lines.append(line)

    return lines


def generate_tax_rate_api_payloads(count=10, offset=0, fk_ids=None):
    """
    Generate N API payloads for Tax Rate.

    Args:
        count: Number of payloads to generate
        offset: Start index in data pool
        fk_ids: dict with resolved FK IDs (must include tax_type_ref_id,
                tax_authority_ref_id, hsn_sac_number)
    """
    if not fk_ids:
        raise ValueError(
            "fk_ids is required. Resolve FK IDs via FkResolver first: "
            "from common.fk_resolver import FkResolver"
        )

    tax_auth_ids = fk_ids.get("tax_authority_ref_id", {})
    hsn_sac_ids = fk_ids.get("hsn_sac_number", {})

    gst_id = TAX_TYPE_REF_ID

    date_ranges = [
        (date(2025, 4, 1), date(2026, 3, 31)),
        (date(2024, 4, 1), date(2025, 3, 31)),
        (date(2023, 4, 1), date(2024, 3, 31)),
        (date(2026, 4, 1), date(2027, 3, 31)),
    ]

    valid_rates = [r for r in GST_RATES if r["rate"] > 0]
    if not valid_rates:
        valid_rates = GST_RATES

    payloads = []

    for i in range(count):
        idx = offset + i
        rate_info = valid_rates[idx % len(valid_rates)]
        from_dt, to_dt = date_ranges[idx % len(date_ranges)]

        auth_name = list(tax_auth_ids.keys())[idx % len(tax_auth_ids)] if tax_auth_ids else None
        auth_id = tax_auth_ids[auth_name] if auth_name else None
        detail_lines = _generate_tax_detail_lines(rate_info, hsn_sac_ids)

        payload = build_tax_rate_api_payload(
            tax_rate_name=rate_info["name"],
            tax_type_ref_id=gst_id,
            tax_authority_ref_id=auth_id,
            from_date=from_dt.isoformat(),
            to_date=to_dt.isoformat(),
            revision_status="Active",
            tax_detail_lines=detail_lines,
        )
        payloads.append(payload)

    return payloads


TAX_TYPE_REF_ID = 93  # GST — hardcoded (no resolvable screen in ERP)

def get_fk_screen_mapping():
    """tax_type_ref_id is hardcoded (no resolvable ERP screen). Only resolve Tax Authority and HSN SAC."""
    return {
        "tax_authority_ref_id": "Tax Authority",
        "hsn_sac_number":       "HSN SAC",
    }


def generate_batch_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None, offset: int = 0, existing_entries: list = None) -> list:
    """Generate a batch of unique Tax Rate API payloads, deduping against existing_entries.

    Args:
        dropdown_ids: Must contain resolved FK IDs (tax_type_ref_id, tax_authority_ref_id, hsn_sac_number).
                      Resolve via FkResolver before calling.
    """
    if not dropdown_ids:
        raise ValueError("dropdown_ids is required. Resolve FK IDs via FkResolver first.")

    fk_ids = dropdown_ids
    if existing_entries:
        used_names = {e.get("tax_rate_name", "").lower().strip() for e in existing_entries if e}
        tax_auth_ids = fk_ids.get("tax_authority_ref_id", {})
        hsn_sac_ids = fk_ids.get("hsn_sac_number", {})
        gst_id = TAX_TYPE_REF_ID
        date_ranges = [
            (date(2025, 4, 1), date(2026, 3, 31)),
            (date(2024, 4, 1), date(2025, 3, 31)),
            (date(2023, 4, 1), date(2024, 3, 31)),
            (date(2026, 4, 1), date(2027, 3, 31)),
        ]
        valid_rates = [r for r in GST_RATES if r["rate"] > 0]
        if not valid_rates:
            valid_rates = GST_RATES
        unique_payloads = []
        pool_idx = 0
        while len(unique_payloads) < count:
            rate_info = valid_rates[(offset + pool_idx) % len(valid_rates)]
            name = rate_info["name"]
            if name.lower().strip() not in used_names:
                used_names.add(name.lower().strip())
                from_dt, to_dt = date_ranges[pool_idx % len(date_ranges)]
                auth_name = list(tax_auth_ids.keys())[pool_idx % len(tax_auth_ids)] if tax_auth_ids else None
                detail_lines = _generate_tax_detail_lines(rate_info, hsn_sac_ids)
                unique_payloads.append(build_tax_rate_api_payload(
                    tax_rate_name=name,
                    tax_type_ref_id=gst_id,
                    tax_authority_ref_id=tax_auth_ids[auth_name] if auth_name else None,
                    from_date=from_dt.isoformat(),
                    to_date=to_dt.isoformat(),
                    revision_status="Active",
                    tax_detail_lines=detail_lines,
                ))
            pool_idx += 1
        return unique_payloads
    return generate_tax_rate_api_payloads(count=count, offset=offset, fk_ids=fk_ids)
