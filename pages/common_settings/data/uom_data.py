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
