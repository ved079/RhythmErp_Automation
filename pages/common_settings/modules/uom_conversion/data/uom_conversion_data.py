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


UOM_CONVERSION_FACTOR_MAX_VALUE = 522222222  # confirmed backend max via API (~9 digits, ~522M). Bug #1 (22-digit scientific notation) is UI-only — API rejects oversized factors directly.
UOM_CONVERSION_FACTOR_MAX_DIGITS = 9  # backend rejects integers >= 1 billion (10+ digits)

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


def get_fk_screen_mapping():
    """Declare which FK dropdown fields need live resolution from which ERP screen."""
    return {
        "source_uom_code": "UOM",
        "target_uom_code": "UOM",
    }


def generate_uom_conversion_api_payloads(count=10, fk_ids=None, offset=0, existing_pairs=None):
    """
    Generate N API payloads for UOM Conversion using FK-resolved UOM IDs.

    Args:
        count: Number of payloads to generate.
        fk_ids: Dict with ``source_uom_code`` / ``target_uom_code`` keys
                mapping UOM code → ERP ID (live-resolved).
        offset: Skip this many pairs from the realistic CONVERSIONS pool.
        existing_pairs: Set of ``{src_id}:{tgt_id}`` strings to skip (avoid duplicates).
    """
    if existing_pairs is None:
        existing_pairs = set()
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

    payloads = []
    seen_pairs = set()

    # Build a realistic conversion pool — only using codes that exist in the FK-resolved pool
    allowed_codes = set(available_codes)
    conv_pool = []
    for src_name, tgt_name, factor in VALID_CONVERSIONS:
        if src_name not in allowed_codes or tgt_name not in allowed_codes:
            continue
        src_id = uom_ids.get(src_name)
        tgt_id = uom_ids.get(tgt_name)
        if src_id is not None and tgt_id is not None:
            conv_pool.append((src_id, tgt_id, factor, src_name, tgt_name))

    # If no valid conversions exist, fall back to random pairs
    if not conv_pool:
        codes = list(available_codes)
        random.shuffle(codes)
        for i in range(count):
            src = codes[i % len(codes)]
            tgt = codes[(i + 1) % len(codes)]
            if src == tgt and len(codes) > 1:
                tgt = codes[(i + 2) % len(codes)]
            source_id = uom_ids.get(src)
            target_id = uom_ids.get(tgt)
            if source_id is None or target_id is None:
                continue
            pair_key = f"{source_id}:{target_id}"
            if pair_key in seen_pairs or pair_key in existing_pairs:
                continue
            seen_pairs.add(pair_key)
            factor = round(random.uniform(0.1, 1000), 4)
            payload = build_uom_conversion_api_payload(
                source_uom_code=source_id,
                target_uom_code=target_id,
                conversion_factor=factor,
            )
            payloads.append(payload)
        return payloads[:count]

    # Use realistic conversions cyclically with offset, skip existing pairs
    for i in range(count * 3):
        if len(payloads) >= count:
            break
        idx = (offset + i) % len(conv_pool)
        src_id, tgt_id, factor, src_name, tgt_name = conv_pool[idx]

        pair_key = f"{src_id}:{tgt_id}"
        if pair_key in seen_pairs or pair_key in existing_pairs:
            continue
        seen_pairs.add(pair_key)

        payload = build_uom_conversion_api_payload(
            source_uom_code=src_id,
            target_uom_code=tgt_id,
            conversion_factor=factor,
        )
        payloads.append(payload)

    return payloads[:count]


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
    offset: int = 0,
    existing_entries: list = None,
    config: dict = None,
) -> list:
    """
    Generate UOM conversion payloads — full N×(N-1) matrix.

    count >= 9999 → all source UOMs (full matrix)
    otherwise     → `count` randomly sampled source UOMs

    config.conversion_factor: factor applied to every pair (default 1)
    """
    cfg = config or {}
    factor = float(cfg.get("conversion_factor", 1) or 1)

    fk_ids = dropdown_ids or {}
    src_map = fk_ids.get("source_uom_code", {})
    tgt_map = fk_ids.get("target_uom_code", {})
    merged = {**src_map, **tgt_map}
    if not merged:
        merged = UOM_IDS  # last-resort fallback
    all_ids = list(set(merged.values()))

    # Build set of existing (source_id, target_id) pairs to skip
    existing_pairs = set()
    for entry in (existing_entries or []):
        src = entry.get("source_uom_code")
        tgt = entry.get("target_uom_code")
        if src is not None and tgt is not None:
            existing_pairs.add(f"{src}:{tgt}")

    # count >= 9999 means "all sources" (sent by UI's Create All Pairs button)
    if count >= 9999:
        source_ids = all_ids
    else:
        import random as _random
        source_ids = _random.sample(all_ids, min(count, len(all_ids)))

    payloads = []
    for src_id in source_ids:
        for tgt_id in all_ids:
            if src_id == tgt_id:
                continue
            pair_key = f"{src_id}:{tgt_id}"
            if pair_key in existing_pairs:
                continue
            payloads.append(build_uom_conversion_api_payload(
                source_uom_code=src_id,
                target_uom_code=tgt_id,
                conversion_factor=factor,
            ))

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# UOM Conversion is a flat screen — no children, no steppers.
# 2 FK dropdowns (source_uom_code, target_uom_code) + 1 number field (conversion_factor).

def get_field_validation_rules(fk_ids=None):
    """Return validation rules dict with dynamic fk_options_count from FK-resolved data."""
    source_count = len(fk_ids.get("source_uom_code", {})) if fk_ids else len(UOM_IDS)
    target_count = len(fk_ids.get("target_uom_code", {})) if fk_ids else len(UOM_IDS)
    return {
        "source_uom_code": {
            "type": "dropdown",
            "required": True,
            "fk_options_count": source_count,
            "note": "FK to UOM screen. API sends integer ID, not string code.",
        },
        "target_uom_code": {
            "type": "dropdown",
            "required": True,
            "fk_options_count": target_count,
            "note": "FK to UOM screen. API sends integer ID, not string code. "
                    "Can be same as source (self-conversion allowed).",
        },
        "conversion_factor": {
            "type": "number",
            "required": True,
            "note": "Input type='character' not 'number' (Bug #2 — no native browser validation). "
                    "Backend accepts up to 21 digits; 22+ saves as scientific notation (Bug #1), making the record uneditable.",
        },
    }


# Backward-compat constant (uses hardcoded fallback counts)
FIELD_VALIDATION_RULES = get_field_validation_rules()


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


