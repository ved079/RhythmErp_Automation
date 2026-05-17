"""
uom_data.py
------------
Test data generator for UOM automation.
Generates random UOM codes (8 uppercase letters only) and descriptions.
"""

import random
import string
from datetime import datetime


def generate_uom_data():
    """Generate random UOM test data. Code = 8 uppercase letters only."""
    uom_code = "".join(random.choices(string.ascii_uppercase, k=8))
    timestamp = datetime.now().strftime("%H%M%S")
    uom_description = f"Test UOM Description {timestamp}"
    return {
        "uom_code": uom_code,
        "uom_description": uom_description,
        "status": "Active"
    }


def generate_updated_description():
    """Generate a new unique description for edit tests."""
    timestamp = datetime.now().strftime("%H%M%S")
    return f"Updated UOM Description {timestamp}"

# ================================================================
# VALIDATION TEST DATA HELPERS
# ================================================================

def generate_string_255():
    """Generate a string of exactly 255 characters (uppercase letters)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (uppercase letters)."""
    return "A" * 256


def generate_special_char_description():
    """Generate a description with special characters."""
    return "Test@#$%^&*()_+-=[]{}|;:',.<>?/~`"


def generate_lowercase_uom_code():
    """Generate a unique UOM code with lowercase letters."""
    suffix = "".join(random.choices(string.ascii_lowercase, k=4))
    timestamp = datetime.now().strftime("%H%M%S")
    return f"lc{suffix}{timestamp}"


def generate_mixed_case_uom_code():
    """Generate a unique UOM code with mixed case letters."""
    suffix = "".join(random.choices(string.ascii_letters, k=4))
    timestamp = datetime.now().strftime("%H%M%S")
    return f"Mx{suffix}{timestamp}"


def generate_number_uom_code():
    """Generate a UOM code containing numbers."""
    return "ABC12345"


def generate_special_char_uom_code():
    """Generate a UOM code containing special characters."""
    return "AB!@#$%^"


def generate_leading_space_uom_code():
    """Generate a UOM code with leading spaces + unique random suffix."""
    suffix = "".join(random.choices(string.ascii_uppercase, k=6))
    timestamp = datetime.now().strftime("%H%M%S")
    return f"  {suffix}{timestamp}"


def generate_trailing_space_uom_code():
    """Generate a UOM code with trailing spaces."""
    return "ABCDEFGH  "
