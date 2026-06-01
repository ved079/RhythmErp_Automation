"""
uom_data.py
------------
Test data generator for UOM automation.
Generates random UOM codes and descriptions.

Updated (v2):
- UOM Code field: type="text", maxlength=255 (auto-cutoff at 255 chars)
- UOM Description field: maxlength=255 (auto-cutoff at 255 chars)
- Description is NOT required (optional field)
- Numbers are allowed in UOM code
"""

import random
import string
from datetime import datetime


def generate_uom_data():
    """Generate random UOM test data. Code = 8 uppercase letters + timestamp for uniqueness."""
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
    """Generate a string of exactly 255 characters (uppercase letters).
    This is the maximum length allowed by the field (maxlength=255)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (uppercase letters).
    When typed into a maxlength=255 field, only 255 chars will be accepted
    (auto-cutoff). Used to verify the auto-cutoff behavior."""
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
    """Generate a unique UOM code containing numbers.
    Live system accepts numbers in UOM code (type='text', not type='character').
    Uses timestamp suffix to avoid duplicate collisions from previous test runs.
    """
    prefix = "".join(random.choices(string.ascii_uppercase, k=3))
    timestamp = datetime.now().strftime("%H%M%S")
    return f"{prefix}{timestamp}"


def generate_special_char_uom_code():
    """Generate a UOM code containing special characters.
    Special characters are rejected by the frontend validation (Pattern A).
    """
    return "AB!@#$%^"


def generate_leading_space_uom_code():
    """Generate a UOM code with leading spaces + unique random suffix.
    Backend auto-trims leading/trailing spaces.
    """
    suffix = "".join(random.choices(string.ascii_uppercase, k=6))
    timestamp = datetime.now().strftime("%H%M%S")
    return f"  {suffix}{timestamp}"


def generate_trailing_space_uom_code():
    """Generate a UOM code with trailing spaces + unique random suffix.
    Backend silently trims trailing spaces.
    """
    suffix = "".join(random.choices(string.ascii_uppercase, k=6))
    timestamp = datetime.now().strftime("%H%M%S")
    return f"{suffix}{timestamp}  "
