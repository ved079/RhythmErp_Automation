"""
uom_conversion_data.py
----------------------
Test data generators for UOM Conversion automation.
Provides random UOM pairs, conversion factors, and edge-case values.
Uses dynamic pair generation — no hardcoded SAFE_PAIRS list needed.
"""

import random
from datetime import datetime


# ================================================================
#  EDGE-CASE GENERATORS (used directly by tests)
# ================================================================

def generate_decimal_conversion_factor():
    """Generate a small decimal conversion factor (e.g. 0.001, 0.123)."""
    decimal = round(random.uniform(0.001, 0.999), 3)
    return str(decimal)


def generate_large_conversion_factor(digits):
    """
    Generate a large integer conversion factor with exactly *digits* digits.
    E.g. digits=21 -> '100000000000000000000'
    """
    return "1" + "0" * (digits - 1)


def generate_negative_conversion_factor():
    """Generate a negative conversion factor."""
    return "-" + str(random.randint(1, 100))


def generate_zero_conversion_factor():
    """Return '0' for zero conversion factor tests."""
    return "0"


def generate_text_conversion_factor():
    """Generate alphabetic text for conversion factor validation test."""
    return "abc"


def generate_special_char_conversion_factor():
    """Generate special characters for conversion factor validation test."""
    return "@#$%^&*"


# ================================================================
#  DYNAMIC PAIR GENERATOR
# ================================================================

def generate_fresh_pair(available_uoms, existing_pairs):
    """
    Generate a (source_uom, target_uom) pair that does NOT already exist.
    Args:
        available_uoms: list of UOM codes from the dropdown (e.g. ['KG', 'LT', ...])
        existing_pairs: set of tuples already in the table (e.g. {('KG','ML'), ...})
    Returns:
        dict with 'source_uom', 'target_uom', 'conversion_factor'
    Raises:
        RuntimeError if no fresh pair can be found
    """
    if not available_uoms or len(available_uoms) < 2:
        raise RuntimeError("Need at least 2 UOMs in dropdown to generate a pair")

    # Try random pairs up to 50 times before giving up
    for _ in range(50):
        source, target = random.sample(available_uoms, 2)
        if (source, target) not in existing_pairs:
            factor = str(random.randint(1, 1000))
            timestamp = datetime.now().strftime("%H%M%S")
            return {
                "source_uom": source,
                "target_uom": target,
                "conversion_factor": factor,
                "_timestamp": timestamp,
            }

    raise RuntimeError(
        "Could not find a fresh pair. All possible combinations already exist in the table. "
        "Total UOMs: " + str(len(available_uoms)) + ", "
        "Existing pairs: " + str(len(existing_pairs))
    )


# ================================================================
#  LEGACY ALIAS (kept for backward compatibility)
# ================================================================

def generate_uom_conversion_data():
    """
    Legacy function — kept for Tests 1-11 which use hardcoded UOMs.
    Tests 15-22 should use generate_fresh_pair(available, existing) instead.
    """
    all_uoms = ["KG", "LT", "ML", "Dozens", "Fest", "NOS", "MT", "BAKMRMRY"]
    source, target = random.sample(all_uoms, 2)
    factor = str(random.randint(1, 1000))
    timestamp = datetime.now().strftime("%H%M%S")
    return {
        "source_uom": source,
        "target_uom": target,
        "conversion_factor": factor,
        "_timestamp": timestamp,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# API Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Converts the existing UI data format into the JSON payload
# that POST /core/dynamic-screen-wrapper/ expects.
#
# UOM CONVERSION SCREEN STRUCTURE (from live API):
#   {
#     "id": "",
#     "attribute_name": "UOM Conversion",
#     "source_uom_ref_id": 1,       // FK: Source UOM
#     "target_uom_ref_id": 2,       // FK: Target UOM
#     "conversion_factor": 1000.0,  // numeric, positive
#     "status": true
#   }
#
# SIMPLE STRUCTURE: No children/steppers — flat payload only.
#
# FIELD KEY MAPPING (verified from live API):
#
#   Root-level:
#     source_uom           -> source_uom_ref_id (FK)
#     target_uom           -> target_uom_ref_id (FK)
#     conversion_factor    -> conversion_factor (float, positive)
#     status               -> status (boolean)
#
# DEPENDENCY: UOM Conversion requires UOM entries to exist first.
# The source_uom_ref_id and target_uom_ref_id must reference valid
# UOM master entries. Use batch_create.py AFTER UOM entries are created.
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Dropdown FK ID pools (placeholder — to be filled from discovery) ────────
UOM_IDS = {}  # To be filled from discovery after UOM entries exist
# Example after discovery:
#   UOM_IDS = {
#       "KG": 1, "Gram": 2, "Metric Ton": 3, "Quintal": 4,
#       "Litre": 5, "Millilitre": 6, "Dozen": 7, "Piece": 8,
#       "Bag (50KG)": 9, "Acre": 10, "Hectare": 11,
#       "Meter": 12, "Feet": 13, "NOS": 14, "MT": 15,
#   }

# ─── Realistic Indian UOM conversion pairs ────────────────────────────────────
# Each tuple: (source_uom_name, target_uom_name, conversion_factor, description)
REALISTIC_UOM_CONVERSION_PAIRS = [
    # Weight conversions (agricultural/commodity)
    ("KG",        "Gram",        1000.0,    "Kilogram to Gram"),
    ("Metric Ton","KG",          1000.0,    "Metric Ton to Kilogram"),
    ("Quintal",   "KG",          100.0,     "Quintal to Kilogram (Indian agricultural)"),
    ("Bag (50KG)","KG",          50.0,      "50KG Bag to Kilogram (cement/grain)"),
    ("Bag (100KG)","KG",         100.0,     "100KG Bag to Kilogram (fertilizer)"),

    # Volume conversions
    ("Litre",     "Millilitre",  1000.0,    "Litre to Millilitre"),
    ("Kilolitre", "Litre",       1000.0,    "Kilolitre to Litre"),
    ("Gallon",    "Litre",       3.7854,    "US Gallon to Litre"),

    # Count conversions
    ("Dozen",     "Piece",       12.0,      "Dozen to Piece"),
    ("Gross",     "Piece",       144.0,     "Gross to Piece"),
    ("Set",       "Piece",       2.0,       "Set to Piece (pair)"),

    # Length / Area conversions (Indian agricultural land)
    ("Acre",      "Hectare",     0.4047,    "Acre to Hectare"),
    ("Bigha",     "Acre",        0.6193,    "Bigha to Acre (UP/Bihar standard)"),
    ("Acre",      "Square Meter",4046.86,   "Acre to Square Meter"),
    ("Hectare",   "Acre",        2.4711,    "Hectare to Acre"),
    ("Meter",     "Feet",        3.2808,    "Meter to Feet"),
    ("Meter",     "Centimetre",  100.0,     "Meter to Centimetre"),
    ("Kilometer", "Meter",       1000.0,    "Kilometer to Meter"),
    ("Feet",      "Inch",        12.0,      "Feet to Inch"),

    # Indian agricultural specific
    ("Quintal",   "Metric Ton",  0.1,       "Quintal to Metric Ton"),
    ("Maund",     "KG",          37.3242,    "Maund to KG (Bengal maund ≈ 37.32 kg)"),
    ("Ser",       "KG",          0.9331,    "Ser to KG (traditional Indian weight)"),
    ("Tola",      "Gram",        11.6638,   "Tola to Gram (gold/jewellery)"),

    # Textile specific
    ("Meter",     "Yard",        1.0936,    "Meter to Yard (textile)"),
    ("Bale",      "KG",          170.0,     "Bale to KG (cotton bale India)"),
]

# ─── Default FK IDs (placeholder — override after discovery) ─────────────────
DEFAULT_UOM_CONVERSION_FK_IDS = {
    "source_uom_ref_id": None,   # Must be filled from discovery
    "target_uom_ref_id": None,   # Must be filled from discovery
}


def generate_realistic_conversion_pair(uom_ids: dict = None) -> dict:
    """Generate a realistic Indian UOM conversion pair with proper factor.

    Args:
        uom_ids: Dict mapping UOM name string -> ref_id int.
                 If None or empty, names are set but IDs remain None.

    Returns:
        Dict with source_uom, target_uom, conversion_factor,
        and optional source_uom_ref_id / target_uom_ref_id.
    """
    pair = random.choice(REALISTIC_UOM_CONVERSION_PAIRS)
    source_name, target_name, factor, _description = pair

    result = {
        "source_uom": source_name,
        "target_uom": target_name,
        "conversion_factor": factor,
    }

    if uom_ids:
        result["source_uom_ref_id"] = uom_ids.get(source_name)
        result["target_uom_ref_id"] = uom_ids.get(target_name)

    return result


def build_uom_conversion_api_payload(
    data: dict = None,
    dropdown_ids: dict = None,
) -> dict:
    """Build the complete UOM Conversion API payload from data + FK IDs.

    Args:
        data: Dict with source_uom, target_uom, conversion_factor keys,
              or None for random realistic data.
        dropdown_ids: Dict of FK IDs. Expected keys:
                       - source_uom_ref_id (int)
                       - target_uom_ref_id (int)
                      If data contains UOM names, these can also be a dict
                      mapping UOM name -> ref_id under the key "uom_ids".

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    ids = {**DEFAULT_UOM_CONVERSION_FK_IDS, **(dropdown_ids or {})}

    if data is None:
        data = generate_uom_conversion_data()

    # Try to resolve FK IDs from uom_ids if provided
    uom_ids = ids.get("uom_ids", UOM_IDS)

    # Determine source_uom_ref_id
    source_ref_id = ids.get("source_uom_ref_id")
    if source_ref_id is None and uom_ids:
        source_name = data.get("source_uom", "")
        source_ref_id = uom_ids.get(source_name)

    # Determine target_uom_ref_id
    target_ref_id = ids.get("target_uom_ref_id")
    if target_ref_id is None and uom_ids:
        target_name = data.get("target_uom", "")
        target_ref_id = uom_ids.get(target_name)

    # Parse conversion_factor
    factor = data.get("conversion_factor", 1.0)
    try:
        factor = float(factor)
    except (ValueError, TypeError):
        factor = 1.0

    # Ensure source and target are different
    if source_ref_id is not None and target_ref_id is not None:
        if source_ref_id == target_ref_id:
            # Shift target_ref_id to a different one
            if uom_ids:
                other_ids = [v for v in uom_ids.values() if v != source_ref_id]
                if other_ids:
                    target_ref_id = random.choice(other_ids)

    # Assemble payload
    payload = {
        "id": "",
        "attribute_name": "UOM Conversion",

        # Root-level fields
        "source_uom_ref_id": source_ref_id,
        "target_uom_ref_id": target_ref_id,
        "conversion_factor": factor,
        "status": data.get("status", True),
    }

    return payload


def generate_uom_conversion_api_payload(
    name_prefix=None,
    dropdown_ids: dict = None,
) -> dict:
    """One-shot: generate a complete UOM Conversion API payload with random data.

    Uses realistic Indian agricultural/commodity conversion pairs with
    proper conversion factors (e.g., KG to Gram = 1000, Acre to Hectare = 0.4047).

    Args:
        name_prefix: Ignored for UOM Conversion (no name field), kept for
                     API consistency with other modules.
        dropdown_ids: Override specific FK IDs or provide "uom_ids" dict
                      mapping UOM name -> ref_id.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    ids = {**DEFAULT_UOM_CONVERSION_FK_IDS, **(dropdown_ids or {})}
    uom_ids = ids.get("uom_ids", UOM_IDS)

    # Pick a realistic conversion pair
    pair_data = generate_realistic_conversion_pair(uom_ids)

    # Build payload
    return build_uom_conversion_api_payload(pair_data, dropdown_ids)


def generate_uom_conversion_api_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """Generate multiple unique UOM Conversion API payloads for batch creation.

    Tries to avoid duplicate (source, target) pairs within the batch.
    Since there are 24+ realistic pairs, this works for up to ~20 payloads
    without collision issues.

    Args:
        count: Number of payloads to generate (default 20).
        prefix: Ignored for UOM Conversion (no name field), kept for
                API consistency with other modules.
        dropdown_ids: Override specific FK IDs or provide "uom_ids" dict.

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    ids = {**DEFAULT_UOM_CONVERSION_FK_IDS, **(dropdown_ids or {})}
    uom_ids = ids.get("uom_ids", UOM_IDS)

    # Build from realistic pairs first, then fall back to random
    available_pairs = list(REALISTIC_UOM_CONVERSION_PAIRS)
    random.shuffle(available_pairs)

    payloads = []
    used_pairs = set()

    for i in range(count):
        # Try to find an unused pair
        pair_data = None
        for pair in available_pairs:
            source_name, target_name, factor, _desc = pair
            pair_key = (source_name, target_name)
            if pair_key not in used_pairs:
                pair_data = {
                    "source_uom": source_name,
                    "target_uom": target_name,
                    "conversion_factor": factor,
                }
                if uom_ids:
                    pair_data["source_uom_ref_id"] = uom_ids.get(source_name)
                    pair_data["target_uom_ref_id"] = uom_ids.get(target_name)
                used_pairs.add(pair_key)
                break

        if pair_data is None:
            # All realistic pairs used, generate random
            pair_data = generate_realistic_conversion_pair(uom_ids)

        payload = build_uom_conversion_api_payload(pair_data, dropdown_ids)
        payloads.append(payload)

    return payloads