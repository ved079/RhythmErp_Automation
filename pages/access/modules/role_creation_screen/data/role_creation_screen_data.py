"""
role_creation_screen_data.py
-----------------------------
Test data generators for RhythmERP Role Creation Screen.

Location: Access > Role Creation Screen
URL:      /#/master-setup/Rolecreationscreen

FORM LAYOUT (Simple 2-field popup — NOT a stepper):
  - Role Name           (text input, required, formcontrolname='role_name')
  - Entity Group Name   (mat-select, required, formcontrolname='entity_type',
                         searchable, populated from Entity Group Definition)

KEY RULES:
  - Role Name is a plain editable text input (NOT readonly, NOT auto-generated)
  - Duplicate Role Name is silently rejected (form closes, no error shown) — BUG-001
  - Spaces-only Role Name is silently rejected — BUG-002
  - No maxlength on Role Name field — BUG-004
  - Special characters, SQL injection, XSS strings accepted — BUG-005
  - Entity Group Name dropdown reads values from Entity Group Definition table
  - Dropdown values are read dynamically at runtime (never hardcode)

KNOWN BUGS:
  BUG-001 (HIGH)  : Duplicate Role Name accepted silently (no error shown)
  BUG-002 (HIGH)  : Spaces-only name accepted without validation error text
  BUG-003 (MEDIUM): Inconsistent SweetAlert after successful create
  BUG-004 (MEDIUM): No maxlength on Role Name
  BUG-005 (LOW)   : Special chars / SQL injection / XSS not sanitized
  BUG-006 (LOW)   : No Delete option
  BUG-007 (MEDIUM): Empty submit shows .mat-form-field-invalid but no mat-error text
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_role_name(prefix="AutoRole"):
    """Generate a random role name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_role_data(name_prefix="AutoRole"):
    """Generate a complete dict of valid role data for Create form.
    entity_group_name is set to None — must be populated from live UI at runtime.
    """
    return {
        "role_name": generate_role_name(name_prefix),
        "entity_group_name": None,  # Pick from live UI (REQUIRED)
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
    special = "!@#$%^&*()"
    return f"TestRole{special}"


def generate_sql_injection_name():
    """Generate a SQL injection string for Name field."""
    return "1; DROP TABLE roles; --"


def generate_xss_name():
    """Generate an XSS string for Name field."""
    return "<script>alert('xss')</script>"


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing name — for duplicate name test."""
    return {
        "role_name": existing_name,
        "entity_group_name": None,  # Pick from live UI
    }


def generate_case_variant_name(existing_name):
    """Return the existing name in different case for case-insensitive test."""
    return existing_name.upper() if existing_name.islower() else existing_name.lower()


def generate_name_with_spaces(existing_name):
    """Return the existing name with leading/trailing spaces."""
    return f"  {existing_name}  "


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "role_name": "",
        "entity_group_name": "",
    }


def generate_name_only_data(name="TestRoleOnly"):
    """Return dict with only Role Name filled — for partial field validation."""
    return {
        "role_name": name,
        "entity_group_name": "",
    }


def generate_valid_edit_data(name_prefix="EditRole"):
    """Generate valid data for Edit form — only fields we want to change."""
    return {
        "role_name": generate_role_name(name_prefix),
        "entity_group_name": None,  # Pick from live UI or keep existing
    }