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