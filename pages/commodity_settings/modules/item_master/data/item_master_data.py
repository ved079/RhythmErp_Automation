"""
item_master_data.py
-------------------
Test data generators for RhythmERP Item Master screen.

Location: Commodity Settings > Commodity Master > Item Master
URL:      /#/dynamic-screens/Item%20Master

FORM LAYOUT (3-step stepper — verified 2026-05-15 on live app):
  Step 1 - Additional Details (INCLUDES ALL TOGGLES):
    - Item Name              (AUTO-GENERATED, READONLY — space-separated concat of Attr 1-5)
    - Item Code              (AUTO-GENERATED, editable — dash-separated concat of Attr 1-5)
    - Description            (text input,   optional)
    - Item Group             (mat-select,   optional)
    - Item Category          (mat-select,   required)
    - Item Type              (mat-select,   required)
    - Item Attribute1-5      (mat-select,   optional each)
    - UOM                    (mat-select,   required)
    - HSN SAC Code           (mat-select,   required)
    - Base Uom               (mat-select,   required)
    - Base Uom Conversion    (text input,   required)
    *** PLUS 3 TOGGLE SWITCHES (NOT 4! Verified 2026-05-18): ***
    - Status                 (toggle switch, Active/Inactive, default Active)
    - Is Critical            (toggle switch, Yes/No, default No)
    - Include Wip Stock Cal  (toggle switch, Yes/No, default No)
    - Is Packing Material    (toggle switch, Yes/No, default No)
    NOTE: "Allow Negative Stock" toggle DOES NOT EXIST in Item Master

  Step 2 - Define Item Master Details (ATTACHMENT ONLY — NO toggles!):
    - Attachment Type        (mat-select,   optional)
    - File Upload            (file upload,   optional)

  Step 3 - Product Order Packeging Details (GRID TABLE):
    - Packaging              (mat-select,   per table row, optional)
    - Packaging Capacity     (number input, per table row, optional)
    - Base Packaging Capacity (number input, per table row, optional)
    - Add Row button

KEY RULES:
  - Item Name is READONLY — cannot be typed into (auto-generated from attributes)
    formcontrolname="name" (NOT "itemName") — confirmed via browser exploration
  - Item Code is editable after auto-generation
    formcontrolname="code" (NOT "itemCode") — confirmed via browser exploration
  - Tests for spaces-only, long strings, special chars in Item Name are NOT possible
    since the field cannot receive keyboard input
  - Item Group is NOT required in Create or Edit mode (confirmed 2026-05-18)
  - Base Uom does NOT auto-sync with UOM — they are independent fields (confirmed 2026-05-18)
  - Duplicate Item Names are ALLOWED — no uniqueness validation (confirmed 2026-05-18)
  - DROPDOWN FILL ORDER: Category → Group → Type → Attr1 → Attr2 → Attr3 → Attr4 → Attr5
    Category/Group/Type are INDEPENDENT, but Attributes cascade

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
    ONLY 3 toggle switches in Step 1 data (NOT 4! Verified 2026-05-18).
    "Allow Negative Stock" DOES NOT EXIST in Item Master.
    Item Name is auto-generated from Item Attribute values (not typed).
    Item Group is NOT required (confirmed 2026-05-18).
    """
    return {
        "item_name": None,           # AUTO-GENERATED from attributes — don't type
        "item_code": generate_item_code(),
        "description": generate_description(),
        "item_category": None,       # Pick from live UI (REQUIRED) — FILL FIRST
        "item_group": None,          # Pick from live UI (NOT required!)
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
        # Toggle switches — 3 on Step 1 (NOT 4! Verified 2026-05-18)
        "status": True,                  # Active (default)
        "is_critical": False,            # No (default)
        "include_wip": False,            # No (default)
        "is_packing_material": False,    # No (default)
    }


def generate_valid_step2_data():
    """Generate data for Step 2 (Define Item Master Details).
    Step 2 contains ONLY Attachment Type + File Upload — NO toggles!
    All toggles are on Step 1.
    """
    return {
        "attachment_type": None,       # Pick from live UI (optional)
        "file_path": None,             # File path for upload (optional)
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
    On Edit, Item Name is READONLY (auto-generated from attributes).
    We can modify: Item Code, Description, Base Uom Conversion, and toggles.
    To change Item Name, you must change the Item Attribute values instead.
    """
    return {
        "item_code": generate_item_code(),
        "description": generate_description(),
        "base_uom_conversion": generate_base_uom_conversion(),
        # Toggle switches (on Step 1) — flip some for edit testing
        "status": True,
        "is_critical": False,
        "include_wip": False,
        "is_packing_material": False,
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
        "item_category": "",        # REQUIRED — fill first in order
        "item_group": "",           # NOT required
        "item_type": "",            # REQUIRED
        "item_attribute1": "",
        "item_attribute2": "",
        "item_attribute3": "",
        "item_attribute4": "",
        "item_attribute5": "",
        "uom": "",                  # REQUIRED
        "hsn_sac_code": "",         # REQUIRED
        "base_uom": "",             # REQUIRED (independent of UOM)
        "base_uom_conversion": "",   # REQUIRED
    }


def generate_name_only_data(name_prefix="NameOnly"):
    """Return dict with only Item Name filled — for partial field validation."""
    return {
        "item_name": generate_item_name(name_prefix),
        "item_code": "",
        "description": "",
        "item_category": "",
        "item_group": "",           # NOT required
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
    # V2: Duplicate Item Names are ALLOWED — no uniqueness validation (confirmed 2026-05-18)
    # This test should verify that duplicates CAN be created (not that they're blocked)
    return {
        "item_name": existing_name,   # Will be ignored — auto-generated from attributes
        "item_code": generate_item_code(),
        "description": generate_description(),
        "item_category": None,       # Fill first per V2 order
        "item_group": None,          # NOT required
        "item_type": None,
        "item_attribute1": None,
        "item_attribute2": None,
        "item_attribute3": None,
        "item_attribute4": None,
        "item_attribute5": None,
        "uom": None,
        "hsn_sac_code": None,
        "base_uom": None,            # INDEPENDENT of UOM
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
