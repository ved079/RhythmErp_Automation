"""
item_attribute_data.py
----------------------
Test data provider for RhythmERP Item Attribute 1-5 automation.

Generates realistic test data for all screens. Key differences:
  - Item Attribute 1 has an extra "Base UOM" dropdown (required)
  - Item Attributes 2-5 have only: Name (required), Description, Status
  - Name input uses capital 'N' attribute: name="Name"
  - Status toggle: Active/Inactive (default ON = Active)
  - Base UOM options: 5, 10, 15 (simple numeric values)
  - Duplicate Names: ALLOWED (BUG-001, same as Item Master pattern)
  - Simple popup form (NOT a stepper)
"""

import random
import string
from datetime import datetime


# ------------------------------------------------------------------
# Valid Data Generators
# ------------------------------------------------------------------

def generate_name(prefix="AutoIA"):
    """Generate a unique attribute name with prefix and timestamp.
    Format: PREFIX_HHMMSS_RAND
    """
    timestamp = datetime.now().strftime("%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_data(attr_num=1, name_prefix="AutoIA"):
    """Generate a complete dict of valid Item Attribute data.

    attr_num=1 includes base_uom field; attr_num 2-5 omit it.
    Dropdowns use "" (empty string) which means "select random at runtime".
    """
    data = {
        "name": generate_name(name_prefix),
        "description": f"Auto test attribute {datetime.now().strftime('%H%M%S')}",
    }

    # Item Attribute 1 has Base UOM
    if attr_num == 1:
        data["base_uom"] = ""  # Random selection from live UI

    # Status toggle — default is ON (Active)
    data["status"] = True

    return data


def generate_minimal_valid_data(attr_num=1):
    """Generate only the required fields.
    Required: Name (always), Base UOM (IA1 only).
    """
    data = {
        "name": generate_name("MIN"),
    }
    if attr_num == 1:
        data["base_uom"] = ""  # Random selection
    return data


# ------------------------------------------------------------------
# Validation Test Data — Missing Required Fields
# ------------------------------------------------------------------

def generate_empty_name(attr_num=1):
    """Data with Name field empty (required field)."""
    data = {
        "name": "",
        "description": "Testing empty name",
    }
    if attr_num == 1:
        data["base_uom"] = ""  # Will be selected
    data["status"] = True
    return data


def generate_spaces_name(attr_num=1):
    """Data with Name containing only spaces."""
    data = generate_valid_data(attr_num, name_prefix="   ")
    data["name"] = "     "
    return data


def generate_missing_base_uom():
    """Data with Base UOM missing (IA1 only, required field).
    Only valid for attr_num=1.
    """
    data = {
        "name": generate_name("NOUOM"),
        "description": "Testing missing Base UOM",
        # base_uom key NOT included — skip dropdown entirely
        "status": True,
    }
    return data


def generate_all_required_missing(attr_num=1):
    """Data with ALL required fields missing."""
    data = {
        "name": "",
        "description": "",
    }
    if attr_num == 1:
        data["base_uom"] = ""  # Will NOT be selected (empty = skip)
        del data["base_uom"]   # Actually remove it to skip the dropdown
    data["status"] = True
    return data


# ------------------------------------------------------------------
# Duplicate Name Data
# ------------------------------------------------------------------

def generate_duplicate_name_data(attr_num=1):
    """Data for duplicate attribute name test.
    BUG-001: Duplicate Names are ALLOWED (expected behavior).
    """
    return generate_valid_data(attr_num, name_prefix="DUP")


# ------------------------------------------------------------------
# Boundary Test Data
# ------------------------------------------------------------------

def generate_long_name(length=256, attr_num=1):
    """Generate a Name of extreme length to test maxlength constraint.
    Server accepts up to 255 chars, rejects 256+.
    BUG-004: No maxlength attribute on Name field.
    """
    data = {
        "name": "X" * length,
        "description": "Testing long name",
    }
    if attr_num == 1:
        data["base_uom"] = ""
    data["status"] = True
    return data


def generate_long_description(length=256, attr_num=1):
    """Generate a Description of extreme length to test maxlength constraint.
    Server accepts up to 255 chars, rejects 256+.
    BUG-004: No maxlength attribute on Description field.
    """
    data = {
        "name": f"AutoIA_DescLen{length}",
        "description": "D" * length,
    }
    if attr_num == 1:
        data["base_uom"] = ""
    data["status"] = True
    return data


def generate_special_char_name(attr_num=1):
    """Generate a Name with special characters."""
    specials = [
        "!@#$_Test",
        "Attr-Code.v2",
        "Test (Copy)",
        "Attr & Co.",
        "Code+Plus=Minus",
    ]
    data = generate_valid_data(attr_num, name_prefix="SPC")
    data["name"] = random.choice(specials)
    return data


def generate_sql_injection_name(attr_num=1):
    """Generate SQL injection strings for Name field."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE items; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM items --",
    ]
    data = generate_valid_data(attr_num, name_prefix="SQL")
    data["name"] = random.choice(injections)
    return data


def generate_xss_name(attr_num=1):
    """Generate XSS payload strings for Name field."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
    ]
    data = generate_valid_data(attr_num, name_prefix="XSS")
    data["name"] = random.choice(payloads)
    return data


def generate_unicode_name(attr_num=1):
    """Generate a Name with unicode/international characters."""
    unicode_samples = [
        f"Attr\u00e9{random.randint(100, 999)}",         # Latin e-acute
        f"\u4e2d\u6587{random.randint(100, 999)}",        # Chinese
        f"Attr\u00fc{random.randint(100, 999)}",          # Latin u-umlaut
    ]
    data = generate_valid_data(attr_num, name_prefix="UNI")
    data["name"] = random.choice(unicode_samples)
    return data


def generate_numeric_name(attr_num=1):
    """Generate a purely numeric Name."""
    data = generate_valid_data(attr_num, name_prefix="NUM")
    data["name"] = str(random.randint(100000, 999999))
    return data


# ------------------------------------------------------------------
# Toggle State Data
# ------------------------------------------------------------------

def generate_status_on(attr_num=1):
    """Data with Status toggle ON (Active)."""
    data = generate_minimal_valid_data(attr_num)
    data["status"] = True
    return data


def generate_status_off(attr_num=1):
    """Data with Status toggle OFF (Inactive)."""
    data = generate_minimal_valid_data(attr_num)
    data["status"] = False
    return data


# ------------------------------------------------------------------
# Edit Mode Specific Data
# ------------------------------------------------------------------

def generate_edit_only_name(attr_num=1):
    """Edit data: only Name changed."""
    return {
        "name": generate_name("EDITNM"),
    }


def generate_edit_only_description(attr_num=1):
    """Edit data: only Description changed."""
    return {
        "description": f"Updated desc {datetime.now().strftime('%H%M%S')}",
    }


def generate_edit_change_base_uom():
    """Edit data: change Base UOM (IA1 only)."""
    return {
        "base_uom": "",  # Will select a different random option
    }


def generate_edit_toggle_status():
    """Edit data: toggle Status."""
    return {
        "status": False,  # Toggle to Inactive
    }


def generate_edit_all_fields(attr_num=1):
    """Edit data: change all fields."""
    data = {
        "name": generate_name("EDITALL"),
        "description": f"Edited all {datetime.now().strftime('%H%M%S')}",
        "status": False,
    }
    if attr_num == 1:
        data["base_uom"] = ""
    return data