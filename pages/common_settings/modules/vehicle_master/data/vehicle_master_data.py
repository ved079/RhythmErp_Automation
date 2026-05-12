import random
import string
from datetime import datetime


def generate_vehicle_name(prefix="AutoVeh"):
    """Generate a random vehicle name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_vehicle_price():
    """Generate a random valid vehicle price (positive integer)."""
    return random.randint(10000, 9999999)


def generate_description():
    """Generate a random description text."""
    words = [
        "Test vehicle entry", "Automated test data", "Selenium validation",
        "Regression test vehicle", "QA automation entry", "Smoke test data",
        "Performance test vehicle", "Integration test entry"
    ]
    return f"{random.choice(words)} - {random.randint(1000, 9999)}"


def generate_valid_vehicle_data(name_prefix="AutoVeh"):
    """Generate a complete dict of valid vehicle data for Create form.
    Dropdown values (vehicle_type, fuel_type) are set to None — 
    must be populated from live UI at runtime via page methods.
    """
    return {
        "name": generate_vehicle_name(name_prefix),
        "price": str(generate_vehicle_price()),
        "vehicle_type": None,  # To be picked from live UI dropdown
        "fuel_type": None,     # To be picked from live UI dropdown
        "description": generate_description()
    }


def generate_valid_edit_data(name_prefix="EditVeh"):
    """Generate valid data for Edit form — only fields we want to change."""
    return {
        "name": generate_vehicle_name(name_prefix),
        "price": str(generate_vehicle_price()),
        "description": generate_description()
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary for Name)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds max for Name)."""
    return "A" * 256


def generate_spaces_only(length=10):
    """Generate a string of only spaces (for Name validation test)."""
    return " " * length


def generate_special_char_name():
    """Generate a name with special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"Vehicle{special}"


def generate_negative_price():
    """Return a negative price string."""
    return f"-{random.randint(1, 9999)}"


def generate_zero_price():
    """Return zero price string."""
    return "0"


def generate_alpha_price():
    """Return alphabetic characters to test price field rejects letters."""
    return "abcDEF"


def generate_decimal_price():
    """Return a decimal price to test if decimals are accepted."""
    return f"{random.randint(1, 999)}.{random.randint(10, 99)}"


def generate_price_with_special_chars():
    """Return special characters to test price field rejects them."""
    return "!@#$"


def generate_price_with_spaces():
    """Return spaces to test price field rejects them."""
    return "   "


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "name": "",
        "price": "",
        "vehicle_type": "",
        "fuel_type": "",
        "description": ""
    }


def generate_name_only_data(name_prefix="NameOnly"):
    """Return dict with only name filled — for partial field validation."""
    return {
        "name": generate_vehicle_name(name_prefix),
        "price": "",
        "vehicle_type": "",
        "fuel_type": "",
        "description": ""
    }


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing name — for duplicate name test."""
    return {
        "name": existing_name,
        "price": str(generate_vehicle_price()),
        "vehicle_type": None,
        "fuel_type": None,
        "description": generate_description()
    }