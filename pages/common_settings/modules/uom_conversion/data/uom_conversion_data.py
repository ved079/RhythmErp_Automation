#!/usr/bin/env python3
"""
UOM Conversion — Data pool + API payload builder.

Screen: "UOM Conversion" (flat, 2 FK dropdowns: source_uom_code, target_uom_code)
Fields: source_uom_code, target_uom_code, conversion_factor

Discovered FK IDs (2026-06-02):
  source_uom_code / target_uom_code: 42 UOM entries
    KG=249, MT=250, QT=251, NOS=252, Litres=253,
    LTR=501, MTR=502, NBPFJJTZo=503, dozens=504, mh-13=505,
    Litre=506, ML=507, MUND=528, BIGHA=529, SER=530,
    CAN=531, SQFT=532, SET=533, KM=534, HP=535, MM=536, SET60=537
    (+ auto-generated codes 508-527)
"""

import random

# ── Real FK IDs from live ERP ────────────────────────────────────────
UOM_IDS = {
    "KG":      249,
    "MT":      250,
    "QT":      251,
    "NOS":     252,
    "Litres":  253,
    "LTR":     501,
    "MTR":     502,
    "dozens":  504,
    "Litre":   506,
    "ML":      507,
    "MUND":    528,
    "BIGHA":   529,
    "SER":     530,
    "CAN":     531,
    "SQFT":    532,
    "SET":     533,
    "KM":      534,
    "HP":      535,
    "MM":      536,
    "SET60":   537,
}

# ── Realistic conversion data ────────────────────────────────────────
# Format: (source_uom_name, target_uom_name, factor) — 1 source = factor target
CONVERSIONS = [
    ("MT",   "KG",   1000.0),       # 1 MT = 1000 KG
    ("KG",   "G",    1000.0),       # Note: "G" not in UOM list — skip
    ("LTR",  "ML",   1000.0),       # 1 LTR = 1000 ML
    ("MTR",  "CM",   100.0),        # Note: "CM" not in UOM list
    ("KM",   "MTR",  1000.0),       # 1 KM = 1000 MTR
    ("MTR",  "MM",   1000.0),       # 1 MTR = 1000 MM
    ("NOS",  "dozens", 0.083333),   # 1 NOS = 1/12 dozens
    ("dozens","NOS",  12.0),        # 1 dozen = 12 NOS
    ("MUND", "KG",   37.3242),      # 1 Maund ≈ 37.3242 KG
    ("BIGHA","SQFT",  27225.0),     # 1 Bigha ≈ 27225 sq ft (varies by state)
    ("HP",   "SET",   1.0),         # placeholder
    ("SET",  "NOS",   1.0),         # 1 SET = 1 NOS
    ("MT",   "QT",    100.0),       # 1 MT = 100 Quintal
    ("KG",   "SER",   1.0719),      # 1 KG ≈ 1.0719 Seer
    ("Litre","ML",    1000.0),      # 1 Litre = 1000 ML
    ("LTR",  "Litre", 1.0),         # 1 LTR = 1 Litre
    ("KM",   "MTR",   1000.0),      # duplicate for variety
    ("CAN",  "Litre", 0.5),         # 1 CAN ≈ 0.5 Litre
    ("MTR",  "SQFT",  10.7639),     # 1 MTR² = 10.7639 sq ft (conceptual)
    ("KG",   "QT",    0.1),         # 1 KG = 0.1 Quintal
    ("Litres","ML",   1000.0),      # 1 Litres = 1000 ML
    ("MT",   "MUND",  26.7923),     # 1 MT ≈ 26.79 Maund
    ("MTR",  "MM",   1000.0),       # 1 MTR = 1000 MM
    ("BIGHA","MTR",   1011.71),     # 1 Bigha ≈ 1011.71 m²
    ("SET60","NOS",   60.0),        # 1 SET60 = 60 NOS
]

# Filter to only include conversions where BOTH source and target exist in UOM_IDS
VALID_CONVERSIONS = []
for src, tgt, factor in CONVERSIONS:
    if src in UOM_IDS and tgt in UOM_IDS:
        VALID_CONVERSIONS.append((src, tgt, factor))


# ── Payload builder ──────────────────────────────────────────────────

def build_uom_conversion_api_payload(source_uom_code, target_uom_code, conversion_factor):
    """Build a single API payload for UOM Conversion."""
    return {
        "id": "",
        "source_uom_code": source_uom_code,
        "target_uom_code": target_uom_code,
        "conversion_factor": conversion_factor,
        "attribute_name": "UOM Conversion",
    }


def generate_uom_conversion_api_payloads(count=10, fk_ids=None):
    """
    Generate N API payloads for UOM Conversion using FK-resolved UOM IDs.
    """
    if fk_ids is None:
        fk_ids = {}

    # Merge FK IDs — prefer FK-resolved (tenant-specific) over hardcoded
    uom_ids = {**UOM_IDS, **fk_ids.get("source_uom_code", {}),
               **fk_ids.get("target_uom_code", {})}

    # Determine available UOM codes — use FK-resolved if present, else hardcoded
    fk_source = fk_ids.get("source_uom_code", {})
    available_codes = list(fk_source.keys()) if fk_source else list(UOM_IDS.keys())
    if not available_codes:
        return []

    # Shuffle for variety, then pair up sequentially
    codes = list(available_codes)
    random.shuffle(codes)

    payloads = []
    seen_pairs = set()

    for i in range(count):
        src = codes[i % len(codes)]
        tgt = codes[(i + 1) % len(codes)]
        # Avoid self-conversions when enough options exist
        if src == tgt and len(codes) > 1:
            tgt = codes[(i + 2) % len(codes)]

        pair = (src, tgt)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        source_id = uom_ids.get(src)
        target_id = uom_ids.get(tgt)

        if source_id is None or target_id is None:
            continue

        factor = round(random.uniform(0.1, 1000), 4)

        payload = build_uom_conversion_api_payload(
            source_uom_code=source_id,
            target_uom_code=target_id,
            conversion_factor=factor,
        )
        payloads.append(payload)

    return payloads[:count]


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# UOM Conversion is a flat screen — no children, no steppers.
# 2 FK dropdowns (source_uom_code, target_uom_code) + 1 number field (conversion_factor).

FIELD_VALIDATION_RULES = {
    "source_uom_code": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(UOM_IDS),
        "note": "FK to UOM screen. API sends integer ID, not string code.",
    },
    "target_uom_code": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(UOM_IDS),
        "note": "FK to UOM screen. API sends integer ID, not string code. "
                "Can be same as source (self-conversion allowed).",
    },
    "conversion_factor": {
        "type": "number",
        "required": True,
        "note": "Decimal number. 21-digit values OK, 22+ digits cause "
                "scientific notation display bug (record becomes uneditable). "
                "Input type='character' in UI (no native number validation).",
    },
}

# Default FK IDs for UOM Conversion (standardized naming pattern)
DEFAULT_UOM_CONVERSION_FK_IDS = {
    "source_uom_code": UOM_IDS,
    "target_uom_code": UOM_IDS,
}

# UOM display names for schema tests (same dict, exposed for name verification)
UOM_NAMES = dict(UOM_IDS)


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """Generate a batch of unique UOM Conversion API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules (Customer, Supplier, Company Onboarding, etc.).

    Args:
        count: Number of payloads to generate.
        prefix: Ignored for UOM Conversion (conversions are deterministic).
        dropdown_ids: Override specific FK ID pools.

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    return generate_uom_conversion_api_payloads(count=count, fk_ids=dropdown_ids)


# ── UI Validation Helpers (restored for test compatibility) ──

_counter = 0

def _next_pair():
    """Return a unique (source, target) pair from UOM_IDS."""
    global _counter
    keys = list(UOM_IDS.keys())
    src = keys[_counter % len(keys)]
    tgt = keys[(_counter + 1) % len(keys)]
    _counter += 1
    return src, tgt


def generate_uom_conversion_data():
    """Return a dict with source_uom, target_uom, conversion_factor for UI tests."""
    src, tgt = _next_pair()
    return {
        "source_uom": src,
        "target_uom": tgt,
        "conversion_factor": "1",
    }


def generate_fresh_pair():
    """Return a tuple of (source_uom, target_uom) from the UOM_IDS."""
    return _next_pair()


def generate_decimal_conversion_factor():
    """Return a decimal conversion factor string."""
    return "1.5"


def generate_large_conversion_factor(n=22):
    """Return a string of n digits for boundary testing."""
    return "9" * n


def generate_negative_conversion_factor():
    """Return a negative conversion factor string."""
    return "-5"


def generate_zero_conversion_factor():
    """Return a zero conversion factor string."""
    return "0"


def generate_text_conversion_factor():
    """Return a text (non-numeric) conversion factor string."""
    return "abc"


def generate_special_char_conversion_factor():
    """Return a special-character conversion factor string."""
    return "@#$"
