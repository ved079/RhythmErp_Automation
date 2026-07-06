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
from datetime import datetime

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
    No numbers, hyphens, or special characters (server rejects them).
    Uses HHMMSS timestamp + counter for cross-session uniqueness."""
    global _ta_counter
    _ta_counter += 1
    ts = datetime.now().strftime("%H%M%S")
    adj = _ADJECTIVES[(_ta_counter - 1) % len(_ADJECTIVES)]
    place = _PLACES[(_ta_counter - 1) % len(_PLACES)]
    # Use letter suffix from counter for extra uniqueness
    suffix = chr(ord('A') + (_ta_counter - 1) % 26)
    # Spell out the timestamp digits as letters to avoid rejection
    # e.g. 091523 -> AIBAEC (A=0, B=1, ... J=9)
    _digit_to_letter = {'0':'A','1':'B','2':'C','3':'D','4':'E',
                        '5':'F','6':'G','7':'H','8':'I','9':'J'}
    ts_alpha = ''.join(_digit_to_letter.get(c, c) for c in ts)
    return f"{adj} GST Auth {place} {suffix}{ts_alpha}"


def valid_tax_authority_data():
    """Return a dict with all fields for UI create_record.
    Hardcoded: tax_type=GST, country=India (user requirement)."""
    return {
        "tax_name": generate_tax_name(),
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


def generate_tax_authority_api_payloads(count=10, offset=0, fk_ids=None):
    """
    Generate N API payloads for Tax Authority.

    Args:
        count: Number of payloads to generate
        offset: Start index in data pool
        fk_ids: dict with resolved FK IDs (must include tax_type_ref_id, country_ref_id)
    """
    if not fk_ids:
        raise ValueError(
            "fk_ids is required. Resolve FK IDs via FkResolver first: "
            "from common.fk_resolver import FkResolver"
        )

    tax_type_ids = fk_ids.get("tax_type_ref_id", {})
    country_ids = fk_ids.get("country_ref_id", {})

    payloads = []

    for i in range(count):
        idx = offset + i
        entry = TAX_AUTHORITIES[idx % len(TAX_AUTHORITIES)]

        tax_type_ref_id = tax_type_ids.get(entry["tax_type"])
        country_ref_id = country_ids.get(entry["country"])

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

def get_field_validation_rules():
    """Return field validation rules (FK counts resolved at runtime)."""
    return {
        "tax_name": {
            "type": "character",
            "required": True,
            "max_length": 255,
            "note": "Tax authority name (e.g. 'CGST Authority').",
        },
        "tax_type_ref_id": {
            "type": "dropdown",
            "required": True,
            "fk_options_count": 0,
            "note": "FK to Tax Type. Resolved at runtime via FkResolver.",
        },
        "country_ref_id": {
            "type": "dropdown",
            "required": True,
            "fk_options_count": 0,
            "note": "FK to Country. Resolved at runtime via FkResolver.",
        },
    }


def get_fk_screen_mapping():
    """Return FK field → screen name mapping for live FkResolver resolution."""
    return {
        "tax_type_ref_id": "Tax Type",
        "country_ref_id":  "Country",
    }


def generate_batch_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None, offset: int = 0, existing_entries: list = None) -> list:
    """Generate a batch of unique Tax Authority API payloads, deduping against existing_entries.

    Args:
        dropdown_ids: Must contain resolved FK IDs (tax_type_ref_id, country_ref_id).
                      Resolve via FkResolver before calling.
    """
    if not dropdown_ids:
        raise ValueError("dropdown_ids is required. Resolve FK IDs via FkResolver first.")
    fk_ids = dropdown_ids
    if existing_entries:
        used_names = {e.get("tax_name", "").lower().strip() for e in existing_entries if e.get("tax_name")}
        tax_type_ids = fk_ids.get("tax_type_ref_id", {})
        country_ids = fk_ids.get("country_ref_id", {})
        unique_payloads = []
        pool_idx = 0
        while len(unique_payloads) < count:
            entry = TAX_AUTHORITIES[(offset + pool_idx) % len(TAX_AUTHORITIES)]
            name = entry["tax_name"]
            if name.lower().strip() not in used_names:
                used_names.add(name.lower().strip())
                unique_payloads.append(build_tax_authority_api_payload(
                    tax_name=name,
                    tax_type_ref_id=tax_type_ids.get(entry["tax_type"]),
                    country_ref_id=country_ids.get(entry["country"]),
                ))
            pool_idx += 1
        return unique_payloads
    return generate_tax_authority_api_payloads(count=count, offset=offset, fk_ids=fk_ids)
