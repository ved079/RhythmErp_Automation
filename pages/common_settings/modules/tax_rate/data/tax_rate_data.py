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
from datetime import date, timedelta

# ── Real FK IDs from live ERP ────────────────────────────────────────
TAX_TYPE_IDS = {"GST": 93}

TAX_AUTHORITY_IDS = {
    "CGST Authority":                      103,
    "SGST Authority":                      104,
    "IGST Authority":                      105,
    "GST Audit Office Mumbai":             106,
    "GST Audit Office Delhi":              107,
    "GST Commissionerate Pune":            108,
    "GST Commissionerate Chennai":         109,
    "GST Commissionerate Kolkata":         110,
    "Central Tax Authority Bengaluru":     111,
    "Central Tax Authority Hyderabad":     112,
    "State Tax Authority Gujarat":         113,
    "State Tax Authority Rajasthan":       114,
    "State Tax Authority Maharashtra":     115,
    "State Tax Authority Karnataka":       116,
    "GST Refund Office Mumbai":            117,
    "GST Refund Office Delhi":             118,
    "Customs GST Authority":              119,
    "GST Appellate Tribunal":             120,
    "State Tax Authority Madhya Pradesh": 121,
    "GST Enforcement Wing":               122,
}

# HSN/SAC numbers already in the system (discovered from Tax Rate stepper)
HSN_SAC_NUMBER_IDS = {
    "995411": 108, "995412": 109, "995421": 110, "995422": 111,
    "0101":   112, "0201":   113, "0301":   114, "0401":   115,
    "0501":   116, "0601":   117, "0701":   118, "0801":   119,
    "0901":   120, "1001":   121, "995413": 122, "995414": 123,
    "995415": 124, "996311": 125, "996312": 126, "997111": 127,
    "997112": 128, "997113": 129, "996211": 130, "996212": 131,
}

# ── Realistic GST rate structures ────────────────────────────────────

GST_RATES = [
    {"name": "GST 0% (Nil)",          "rate": 0.0,    "cgst": 0.0,    "sgst": 0.0,    "igst": 0.0,    "cess": 0.0},
    {"name": "GST 0.25%",             "rate": 0.25,   "cgst": 0.125,  "sgst": 0.125,  "igst": 0.25,   "cess": 0.0},
    {"name": "GST 3%",                "rate": 3.0,    "cgst": 1.5,    "sgst": 1.5,    "igst": 3.0,    "cess": 0.0},
    {"name": "GST 5%",                "rate": 5.0,    "cgst": 2.5,    "sgst": 2.5,    "igst": 5.0,    "cess": 0.0},
    {"name": "GST 12%",               "rate": 12.0,   "cgst": 6.0,    "sgst": 6.0,    "igst": 12.0,   "cess": 0.0},
    {"name": "GST 15%",               "rate": 15.0,   "cgst": 7.5,    "sgst": 7.5,    "igst": 15.0,   "cess": 0.0},
    {"name": "GST 18%",               "rate": 18.0,   "cgst": 9.0,    "sgst": 9.0,    "igst": 18.0,   "cess": 0.0},
    {"name": "GST 28%",               "rate": 28.0,   "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 0.0},
    {"name": "GST 5% + Cess",         "rate": 5.0,    "cgst": 2.5,    "sgst": 2.5,    "igst": 5.0,    "cess": 2.5},
    {"name": "GST 12% + Cess",        "rate": 12.0,   "cgst": 6.0,    "sgst": 6.0,    "igst": 12.0,   "cess": 5.0},
    {"name": "GST 18% + Cess",        "rate": 18.0,   "cgst": 9.0,    "sgst": 9.0,    "igst": 18.0,   "cess": 10.0},
    {"name": "GST 28% + Cess",        "rate": 28.0,   "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 15.0},
    {"name": "GST 28% + 12% Cess",    "rate": 28.0,   "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 12.0},
    {"name": "GST 28% + 60% Cess",    "rate": 28.0,   "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 60.0},
    {"name": "GST 18% + 1% Cess",     "rate": 18.0,   "cgst": 9.0,    "sgst": 9.0,    "igst": 18.0,   "cess": 1.0},
    {"name": "GST 12% + 2% Cess",     "rate": 12.0,   "cgst": 6.0,    "sgst": 6.0,    "igst": 12.0,   "cess": 2.0},
    {"name": "GST 5% + 1% Cess",      "rate": 5.0,    "cgst": 2.5,    "sgst": 2.5,    "igst": 5.0,    "cess": 1.0},
    {"name": "GST 28% + 204% Cess",   "rate": 28.0,   "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 204.0},
    {"name": "GST 5% + 5% Cess",      "rate": 5.0,    "cgst": 2.5,    "sgst": 2.5,    "igst": 5.0,    "cess": 5.0},
    {"name": "GST 28% + 18% Cess",    "rate": 28.0,   "cgst": 14.0,   "sgst": 14.0,   "igst": 28.0,   "cess": 18.0},
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

    for hsn_code, hsn_id in selected:
        line = {
            "hsn_sac_number": hsn_id,
            "tax_rate": rate_info["rate"],
        }
        lines.append(line)

    return lines


def generate_tax_rate_api_payloads(count=10, fk_ids=None):
    """
    Generate N API payloads for Tax Rate.
    """
    if fk_ids is None:
        fk_ids = {}

    # Merge FK IDs
    tax_type_ids = {**TAX_TYPE_IDS, **fk_ids.get("tax_type_ref_id", {})}
    tax_auth_ids = {**TAX_AUTHORITY_IDS, **fk_ids.get("tax_authority_ref_id", {})}
    hsn_sac_ids = {**HSN_SAC_NUMBER_IDS, **fk_ids.get("hsn_sac_number", {})}

    gst_id = tax_type_ids.get("GST", 93)

    # Date ranges — spread across fiscal years
    date_ranges = [
        (date(2025, 4, 1), date(2026, 3, 31)),   # FY 2025-26
        (date(2024, 4, 1), date(2025, 3, 31)),   # FY 2024-25
        (date(2023, 4, 1), date(2024, 3, 31)),   # FY 2023-24
        (date(2026, 4, 1), date(2027, 3, 31)),   # FY 2026-27
    ]

    payloads = []

    for i in range(count):
        rate_info = GST_RATES[i % len(GST_RATES)]
        from_dt, to_dt = date_ranges[i % len(date_ranges)]

        # Cycle through tax authorities for variety
        auth_name = list(tax_auth_ids.keys())[i % len(tax_auth_ids)]
        auth_id = tax_auth_ids[auth_name]

        # Generate detail lines
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


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Tax Rate is the ONLY Common Settings screen with a stepper structure.
# Root fields + 1 stepper child "Define Tax Rate Details" with detail lines.

FIELD_VALIDATION_RULES = {
    # Root fields
    "tax_rate_name": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Tax rate name (e.g. 'GST 18%').",
    },
    "tax_type_ref_id": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(TAX_TYPE_IDS),
        "note": "FK to Tax Type. Currently only GST=93.",
    },
    "tax_authority_ref_id": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(TAX_AUTHORITY_IDS),
        "note": "FK to Tax Authority. 20 Indian GST authorities.",
    },
    "from_date": {
        "type": "date",
        "required": True,
        "note": "Start date in ISO format (YYYY-MM-DD).",
    },
    "to_date": {
        "type": "date",
        "required": True,
        "note": "End date in ISO format (YYYY-MM-DD).",
    },
    "revision_status": {
        "type": "character",
        "required": True,
        "note": "Enum: 'Active' or other status values.",
    },

    # Stepper child: "Define Tax Rate Details" detail lines
    "hsn_sac_number": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(HSN_SAC_NUMBER_IDS),
        "note": "FK to HSN/SAC Number. In stepper detail lines.",
    },
    "tax_rate": {
        "type": "number",
        "required": True,
        "note": "Tax rate percentage (decimal). In stepper detail lines.",
    },
}

TAX_TYPE_NAMES = dict(TAX_TYPE_IDS)
TAX_AUTHORITY_NAMES = dict(TAX_AUTHORITY_IDS)
HSN_SAC_NUMBER_NAMES = dict(HSN_SAC_NUMBER_IDS)

DEFAULT_TAX_RATE_FK_IDS = {
    "tax_type_ref_id": TAX_TYPE_IDS,
    "tax_authority_ref_id": TAX_AUTHORITY_IDS,
    "hsn_sac_number": HSN_SAC_NUMBER_IDS,
}

REVISION_STATUS_OPTIONS = ["Active"]

STEPPER_NAME = "Define Tax Rate Details"


def generate_batch_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None) -> list:
    """Generate a batch of unique Tax Rate API payloads."""
    return generate_tax_rate_api_payloads(count=count, fk_ids=dropdown_ids)
