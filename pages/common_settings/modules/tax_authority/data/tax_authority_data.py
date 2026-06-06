#!/usr/bin/env python3
"""
Tax Authority — Data pool + API payload builder.

Screen: "Tax Authority" (flat, 2 FK dropdowns: tax_type_ref_id, country_ref_id)
Fields: tax_name, tax_type_ref_id, country_ref_id

Speed optimized (v4):
- Added missing UI helper functions (FIELD_TAX_NAME, PAGE_URL, etc.)
- Unique timestamp-based tax name generation (avoids collisions)
"""

import random
import time

# ── Real FK IDs from live ERP ────────────────────────────────────────
TAX_TYPE_IDS = {"GST": 93}

COUNTRY_IDS = {
    "India": 1, "Dubai": 2, "Afghanistan": 3, "Algeria": 4, "Angola": 5,
    "Argentina": 6, "Australia": 8, "Bahrain": 10, "Bhutan": 13, "Brazil": 16,
    "Canada": 20, "China (offshore)": 25, "Colombia": 26, "Denmark": 32,
    "Egypt": 34, "European Union": 38, "Hong Kong": 46, "Indonesia": 49,
    "Israel": 52, "Kenya": 55, "Kuwait": 56, "Malaysia": 64, "Maldives": 65,
    "Mexico": 67, "Myanmar": 70, "Nepal": 72, "New Zealand": 73, "Nigeria": 74,
    "Oman": 77, "Pakistan": 78, "Philippines": 82, "Qatar": 84, "Russia": 86,
    "Saudi Arabia": 89, "Singapore": 0, "South Africa": 94, "South Korea": 95,
    "Sri Lanka": 96, "Sweden": 98, "Switzerland": 99, "Taiwan": 101,
    "Thailand": 0, "Turkey": 105, "Ukraine": 106, "United Kingdom": 107,
    "United States": 108, "Vietnam": 112,
}

# ── Page constants (used by tax_authority_page.py) ──────────────────
TAX_AUTHORITY_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Authority"
FIELD_TAX_NAME = "tax_name"
VALIDATION_FAILED_TITLE = "Validation Failed"
VALIDATION_FAILED_CONTENT = "Please correct the highlighted fields"
POPUP_TITLE = "Tax Authority"
HISTORY_POPUP_TITLE = "Tax Authority History"

# ── Realistic data pools ─────────────────────────────────────────────

TAX_AUTHORITIES = [
    {"tax_name": "CGST Authority",                "tax_type": "GST", "country": "India"},
    {"tax_name": "SGST Authority",                 "tax_type": "GST", "country": "India"},
    {"tax_name": "IGST Authority",                 "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Audit Office Mumbai",        "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Audit Office Delhi",         "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Commissionerate Pune",       "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Commissionerate Chennai",    "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Commissionerate Kolkata",    "tax_type": "GST", "country": "India"},
    {"tax_name": "Central Tax Authority Bengaluru", "tax_type": "GST", "country": "India"},
    {"tax_name": "Central Tax Authority Hyderabad", "tax_type": "GST", "country": "India"},
    {"tax_name": "State Tax Authority Gujarat",    "tax_type": "GST", "country": "India"},
    {"tax_name": "State Tax Authority Rajasthan",  "tax_type": "GST", "country": "India"},
    {"tax_name": "State Tax Authority Maharashtra","tax_type": "GST", "country": "India"},
    {"tax_name": "State Tax Authority Karnataka",  "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Refund Office Mumbai",       "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Refund Office Delhi",        "tax_type": "GST", "country": "India"},
    {"tax_name": "Customs GST Authority",          "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Appellate Tribunal",         "tax_type": "GST", "country": "India"},
    {"tax_name": "State Tax Authority Madhya Pradesh","tax_type": "GST","country": "India"},
    {"tax_name": "GST Enforcement Wing",           "tax_type": "GST", "country": "India"},
]


# ── UI Validation Helpers ───────────────────────────────────────────

_ta_counter = 0

# Adjective pools for unique letter-only tax names
_ADJECTIVES = [
    "Central", "State", "Eastern", "Western", "Northern", "Southern",
    "Metro", "Urban", "Rural", "Coastal", "Inland", "Regional",
    "Primary", "Secondary", "Federal", "Local", "Civic", "National",
    "New", "Old", "Modern", "Classic", "Royal", "Capital",
]

_PLACES = [
    "Mumbai", "Delhi", "Pune", "Chennai", "Kolkata", "Bengaluru",
    "Hyderabad", "Jaipur", "Lucknow", "Indore", "Nagpur", "Surat",
    "Kochi", "Bhopal", "Patna", "Ranchi", "Vadodara", "Agra",
    "Goa", "Noida", "Thane", "Gurgaon", "Mysore", "Trivandrum",
]


def generate_tax_name():
    """Return a unique tax authority name string — LETTERS ONLY.
    No numbers, hyphens, or special characters (server rejects them)."""
    global _ta_counter
    _ta_counter += 1
    adj = _ADJECTIVES[(_ta_counter - 1) % len(_ADJECTIVES)]
    place = _PLACES[(_ta_counter - 1) % len(_PLACES)]
    # Add a letter suffix for uniqueness when counter wraps
    suffix = chr(ord('A') + (_ta_counter - 1) % 26)
    return f"{adj} GST Authority {place} {suffix}"


def valid_tax_authority_data():
    """Return a dict with all fields for UI create_record.
    Hardcoded: tax_type=GST, country=India (user requirement)."""
    return {
        FIELD_TAX_NAME: generate_tax_name(),
        "tax_type": "GST",
        "country": "India",
    }


def duplicate_tax_authority_data(tax_name):
    """Return data that duplicates an existing tax_name."""
    return {
        FIELD_TAX_NAME: tax_name,
        "tax_type": "GST",
        "country": "India",
    }


def special_chars_tax_name():
    """Return data with special characters in tax_name."""
    return {
        FIELD_TAX_NAME: "TEST@#$%^&*()_+-=[]{}|;':\",./<>?",
        "tax_type": "GST",
        "country": "India",
    }


def invalid_very_long_tax_name(length=200):
    """Return data with a very long tax_name."""
    return {
        FIELD_TAX_NAME: "X" * length,
        "tax_type": "GST",
        "country": "India",
    }


# ── Payload builder ──────────────────────────────────────────────────

def build_tax_authority_api_payload(tax_name, tax_type_ref_id, country_ref_id):
    """Build a single API payload for Tax Authority."""
    return {
        "id": "",
        "tax_name": tax_name,
        "tax_type_ref_id": tax_type_ref_id,
        "country_ref_id": country_ref_id,
        "attribute_name": "Tax Authority",
    }


def generate_tax_authority_api_payloads(count=10, fk_ids=None):
    """
    Generate N API payloads for Tax Authority.
    """
    if fk_ids is None:
        fk_ids = {}

    # Merge FK IDs
    tax_type_ids = {**TAX_TYPE_IDS, **fk_ids.get("tax_type_ref_id", {})}
    country_ids = {**COUNTRY_IDS, **fk_ids.get("country_ref_id", {})}

    gst_id = tax_type_ids.get("GST", 93)
    india_id = country_ids.get("India", 1)

    payloads = []

    for i in range(count):
        entry = TAX_AUTHORITIES[i % len(TAX_AUTHORITIES)]

        tax_type_ref_id = tax_type_ids.get(entry["tax_type"], gst_id)
        country_ref_id = country_ids.get(entry["country"], india_id)

        payload = build_tax_authority_api_payload(
            tax_name=entry["tax_name"],
            tax_type_ref_id=tax_type_ref_id,
            country_ref_id=country_ref_id,
        )
        payloads.append(payload)

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
FIELD_VALIDATION_RULES = {
    "tax_name": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Tax authority name (e.g. 'CGST Authority').",
    },
    "tax_type_ref_id": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(TAX_TYPE_IDS),
        "note": "FK to Tax Type. Currently only GST=93.",
    },
    "country_ref_id": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(COUNTRY_IDS),
        "note": "FK to Country. 45+ countries, India=1.",
    },
}

TAX_TYPE_NAMES = dict(TAX_TYPE_IDS)
COUNTRY_NAMES = dict(COUNTRY_IDS)

DEFAULT_TAX_AUTHORITY_FK_IDS = {
    "tax_type_ref_id": TAX_TYPE_IDS,
    "country_ref_id": COUNTRY_IDS,
}


def generate_batch_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None) -> list:
    """Generate a batch of unique Tax Authority API payloads."""
    return generate_tax_authority_api_payloads(count=count, fk_ids=dropdown_ids)
