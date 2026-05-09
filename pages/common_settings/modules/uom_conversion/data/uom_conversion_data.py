"""
uom_conversion_data.py
----------------------
Test data generators for UOM Conversion automation.
Provides random UOM pairs, conversion factors, and edge-case values.
"""

import random
import string
from datetime import datetime


def generate_uom_conversion_data():
    """
    Generate random UOM Conversion test data.
    Uses common UOM codes from the master list.
    Returns dict with source_uom, target_uom, conversion_factor.
    """
    common_uoms = ["KG", "GM", "MG", "LT", "ML", "MTR", "CM", "MM", "TON", "BOX", "PCS", "DOZ"]
    source_uom = random.choice(common_uoms)
    # Ensure source != target
    available = [u for u in common_uoms if u != source_uom]
    target_uom = random.choice(available)
    conversion_factor = str(random.randint(1, 1000))
    timestamp = datetime.now().strftime("%H%M%S")
    return {
        "source_uom": source_uom,
        "target_uom": target_uom,
        "conversion_factor": conversion_factor,
        "_timestamp": timestamp,
    }


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
