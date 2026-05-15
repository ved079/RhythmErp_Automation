"""
item_master_data.py
-------------------
Test data generators for RhythmERP Item Master screen.

Location: Commodity Settings > Commodity Master > Item Master
URL:      /#/dynamic-screens/Item%20Master

FORM LAYOUT (3-step stepper):
  Step 1 - Additional Details:
    - Item Name              (text input,   required)
    - Item Code              (text input,   optional)
    - Description            (text input,   optional)
    - Item Group             (mat-select,   optional)
    - Item Category          (mat-select,   required)
    - Item Type              (mat-select,   required)
    - Item Attribute1-5      (mat-select,   optional each)
    - UOM                    (mat-select,   required)
    - HSN SAC Code           (mat-select,   required)
    - Base Uom               (mat-select,   required)
    - Base Uom Conversion    (text input,   required)
    - Status                 (toggle switch, Active/Inactive, default Active)
    - Is Critical            (toggle switch, Yes/No, default No)
    - Include Wip Stock Cal  (toggle switch, Yes/No, default No)
    - Is Packing Material    (toggle switch, Yes/No, default No)

  Step 2 - Define Item Master Details:
    - Attachment Type        (mat-select,   optional)
    - File Upload            (file input,   .png/.jpg/.pdf, optional)
    - Packaging              (mat-select,   optional)

  Step 3 - Product Order Packaging Details:
    - Packaging              (mat-select,   per table row, optional)
    - Packaging Capacity     (number input, per table row, optional)
    - Base Packaging Capacity (number input, per table row, optional)
    - Add Row button

TABLE COLUMNS:
  - View / Edit / History  (action buttons per row)
  - Item Name
  - UOM
  - Status
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_item_name(prefix="AutoItem"):
    """Generate a random item name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_item_code(prefix="ITM"):
    """Generate a random item code."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(10, 99)
    return f"{prefix}-{timestamp[-6:]}-{rand}"


def generate_description():
    """Generate a random description text."""
    words = [
        "Test item entry", "Automated test data", "Selenium validation",
        "Regression test item", "QA automation entry", "Smoke test data",
        "Performance test item", "Integration test entry",
        "Commodity test item", "Packaging validation item"
    ]
    return f"{random.choice(words)} - {random.randint(1000, 9999)}"


def generate_base_uom_conversion():
    """Generate a valid Base Uom Conversion value (positive number)."""
    return str(round(random.uniform(0.1, 100.0), 3))


def generate_packaging_capacity():
    """Generate a valid Packaging Capacity value."""
    return str(round(random.uniform(1.0, 1000.0), 2))


# ──────────────────────────────────────────────
# Complete Valid Data for Create (Step 1 only)
# ──────────────────────────────────────────────

def generate_valid_item_data(name_prefix="AutoItem"):
    """Generate a complete dict of valid item data for Create form Step 1.
    Dropdown values set to None — must be populated from live UI at runtime.
    Toggle values use sensible defaults.
    """
    return {
        "item_name": generate_item_name(name_prefix),
        "item_code": generate_item_code(),
        "description": generate_description(),
        "item_group": None,          # Pick from live UI
        "item_category": None,       # Pick from live UI (REQUIRED)
        "item_type": None,           # Pick from live UI (REQUIRED)
        "item_attribute1": None,     # Pick from live UI (optional)
        "item_attribute2": None,     # Pick from live UI (optional)
        "item_attribute3": None,     # Pick from live UI (optional)
        "item_attribute4": None,     # Pick from live UI (optional)
        "item_attribute5": None,     # Pick from live UI (optional)
        "uom": None,                 # Pick from live UI (REQUIRED)
        "hsn_sac_code": None,        # Pick from live UI (REQUIRED)
        "base_uom": None,            # Pick from live UI (REQUIRED)
        "base_uom_conversion": generate_base_uom_conversion(),
        "status": True,              # Active (default)
        "is_critical": False,        # No (default)
        "include_wip_stock_cal": False,  # No (default)
        "is_packing_material": False,    # No (default)
    }


def generate_valid_step2_data():
    """Generate data for Step 2 (Define Item Master Details).
    All fields optional — most tests will just click Next.
    """
    return {
        "attachment_type": None,     # Pick from live UI (optional)
        "packaging": None,           # Pick from live UI (optional)
    }


def generate_valid_step3_data():
    """Generate data for Step 3 (Product Order Packaging Details).
    Packaging table rows are optional.
    """
    return {
        "packaging_rows": []  # List of dicts: {packaging, capacity, base_capacity}
    }


def generate_full_valid_item_data(name_prefix="AutoItem"):
    """Generate complete valid data for ALL 3 steps.
    Used for end-to-end happy path tests.
    """
    data = generate_valid_item_data(name_prefix)
    data["step2"] = generate_valid_step2_data()
    data["step3"] = generate_valid_step3_data()
    return data


def generate_valid_edit_data(name_prefix="EditItem"):
    """Generate valid data for Edit form — only fields we want to change.
    On Edit, we can modify fields in Step 1.
    """
    return {
        "item_name": generate_item_name(name_prefix),
        "item_code": generate_item_code(),
        "description": generate_description(),
        "base_uom_conversion": generate_base_uom_conversion(),
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
    return f"Item{special}"


def generate_negative_uom_conversion():
    """Return a negative Base Uom Conversion value."""
    return f"-{round(random.uniform(0.1, 100.0), 3)}"


def generate_zero_uom_conversion():
    """Return zero for Base Uom Conversion."""
    return "0"


def generate_alpha_uom_conversion():
    """Return alphabetic characters for Base Uom Conversion."""
    return "abcDEF"


def generate_special_char_uom_conversion():
    """Return special characters for Base Uom Conversion."""
    return "!@#$"


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation.
    Only Step 1 fields — this is what Submit sees.
    """
    return {
        "item_name": "",
        "item_code": "",
        "description": "",
        "item_group": "",
        "item_category": "",
        "item_type": "",
        "item_attribute1": "",
        "item_attribute2": "",
        "item_attribute3": "",
        "item_attribute4": "",
        "item_attribute5": "",
        "uom": "",
        "hsn_sac_code": "",
        "base_uom": "",
        "base_uom_conversion": "",
    }


def generate_name_only_data(name_prefix="NameOnly"):
    """Return dict with only Item Name filled — for partial field validation."""
    return {
        "item_name": generate_item_name(name_prefix),
        "item_code": "",
        "description": "",
        "item_group": "",
        "item_category": "",
        "item_type": "",
        "item_attribute1": "",
        "item_attribute2": "",
        "item_attribute3": "",
        "item_attribute4": "",
        "item_attribute5": "",
        "uom": "",
        "hsn_sac_code": "",
        "base_uom": "",
        "base_uom_conversion": "",
    }


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing name — for duplicate name test."""
    return {
        "item_name": existing_name,
        "item_code": generate_item_code(),
        "description": generate_description(),
        "item_group": None,
        "item_category": None,
        "item_type": None,
        "item_attribute1": None,
        "item_attribute2": None,
        "item_attribute3": None,
        "item_attribute4": None,
        "item_attribute5": None,
        "uom": None,
        "hsn_sac_code": None,
        "base_uom": None,
        "base_uom_conversion": generate_base_uom_conversion(),
    }


def generate_decimal_uom_conversion():
    """Return a decimal Base Uom Conversion value."""
    return f"{random.randint(1, 99)}.{random.randint(10, 99)}"


def generate_uom_conversion_with_spaces():
    """Return spaces for Base Uom Conversion field."""
    return "   "


def generate_item_code_with_special_chars():
    """Generate an item code with special characters."""
    return f"ITM@#{random.randint(100, 999)}"