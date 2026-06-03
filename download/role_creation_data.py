"""
role_creation_data.py
---------------------
Test data generators for RhythmERP Role Creation Screen.

Location: Master Setup > Role Creation Screen
URL:      /#/master-setup/Rolecreationscreen

FORM LAYOUT (simple popup — NOT a stepper):
  - Role Name              (text input,   required, no maxlength)
  - Entity Group Name      (mat-select,   required, searchable)

KEY RULES (verified 2026-05-20 on live app):
  - Role Name has NO maxlength attribute — 500+ chars accepted client-side
  - Spaces-only Role Name accepted as ng-valid (BUG-001)
  - Special characters accepted in Role Name (BUG-002)
  - SQL injection accepted in Role Name (BUG-003)
  - XSS payloads accepted in Role Name (BUG-004)
  - Duplicate Role Names allowed — no uniqueness validation (BUG-005)
  - No client maxlength — 500-char name silently fails server-side (BUG-006)
  - No visible mat-error text on required field validation (BUG-007)
  - No Delete option anywhere on screen (BUG-008)
  - Leading/trailing spaces are TRIMMED on save
  - Entity Group Name options loaded dynamically from Entity Group Definition master

TABLE COLUMNS:
  - View / Edit / History  (action buttons per row)
  - Name (Role Name)
  - Creation Date Time
  - Updated Date Time
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


def generate_role_name_with_dot(prefix="Test.Role"):
    """Generate a role name containing a dot character."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(10, 99)
    return f"{prefix}_{timestamp[-6:]}_{rand}"


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_role_data(name_prefix="AutoRole"):
    """Generate a complete dict of valid role data for Create form.
    Entity Group value set to None — must be populated from live UI at runtime.
    """
    return {
        "role_name": generate_role_name(name_prefix),
        "entity_group": None,       # Pick from live UI (REQUIRED)
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_spaces_only(length=10):
    """Generate a string of only spaces (for Role Name validation test)."""
    return " " * length


def generate_special_char_name():
    """Generate a name with special characters."""
    return "!@#$%^&*()_+-=[]{}|;:,./<>?"


def generate_sql_injection_name():
    """Generate a SQL injection string for Role Name."""
    return "'; DROP TABLE roles; --"


def generate_xss_payload_name():
    """Generate an XSS payload string for Role Name."""
    return "<script>alert('xss')</script>"


def generate_string_500():
    """Generate a string of exactly 500 characters (over-max boundary for Role Name)."""
    return "A" * 500


def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary for name fields)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds max for name fields)."""
    return "A" * 256


def generate_numbers_only_name():
    """Generate a numbers-only role name."""
    return "123456"


def generate_leading_trailing_spaces_name():
    """Generate a role name with leading and trailing spaces."""
    return "  SpaceTestRole  "


def generate_unicode_name():
    """Generate a role name with Unicode characters."""
    return "TestRole\u00e9\u00f1\u00fc\u00e4\u00f6"


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing name — for duplicate name test.
    BUG-005: Duplicate Role Names are ALLOWED — no uniqueness validation.
    This test should verify that duplicates CAN be created (not that they're blocked).
    """
    return {
        "role_name": existing_name,
        "entity_group": None,       # Pick from live UI (REQUIRED)
    }


def generate_case_insensitive_duplicate_name(existing_name):
    """Return a lowercase version of an existing name for case-insensitive duplicate test.
    BUG-005b: Case-insensitive duplicates are also ALLOWED.
    """
    return {
        "role_name": existing_name.lower(),
        "entity_group": None,
    }


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "role_name": "",
        "entity_group": "",
    }


def generate_role_name_only_data(name_prefix="NameOnly"):
    """Return dict with only Role Name filled — for partial field validation."""
    return {
        "role_name": generate_role_name(name_prefix),
        "entity_group": "",
    }


def generate_entity_group_only_data():
    """Return dict with only Entity Group filled — for partial field validation.
    Entity Group value set to None — must be picked from live UI at runtime.
    """
    return {
        "role_name": "",
        "entity_group": None,       # Pick from live UI
    }


# ──────────────────────────────────────────────
# Valid Edit Data
# ──────────────────────────────────────────────

def generate_valid_edit_data(name_prefix="EditRole"):
    """Generate valid data for Edit form — only fields we want to change."""
    return {
        "role_name": generate_role_name(name_prefix),
        "entity_group": None,       # Pick from live UI (change to different option)
    }
