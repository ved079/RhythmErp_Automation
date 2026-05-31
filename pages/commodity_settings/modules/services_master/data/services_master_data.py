"""
services_master_data.py
-----------------------
Test data generators for RhythmERP Services Master screen.

Location: Commodity Settings > Commodity Master > Services Master
URL:      /#/dynamic-screens/Services%20Master

FORM LAYOUT (Simple popup — NOT a stepper):
  - Name                  (text input,   required, name="Name", type="text")
  - Base Uom              (mat-select,   required, label="Base Uom")
  - UOM                   (mat-select,   required, label="UOM")
  - HSN SAC Code          (mat-select,   required, label="HSN SAC Code")
  - Base Uom Conversion   (text input,   required, name="Base Uom Conversion", type="text")
  - Status                (toggle switch, optional, default ON = Active)

TABLE COLUMNS (7 columns):
  - View / Edit / History  (action buttons per row)
  - Name
  - UOM
  - HSN SAC Code
  - Status

KNOWN BUGS:
  BUG-001 (HIGH)  : No maxlength on Name input; accepts 300+ chars. Server rejects at 255.
  BUG-002 (HIGH)  : No maxlength on Base Uom Conversion; accepts 11+ chars. Server max is 10.
  BUG-003 (HIGH)  : Name accepts ALL characters — special chars, spaces-only — no restrictions.
  BUG-004 (HIGH)  : Base Uom Conversion accepts ALL input — letters, special chars, negative,
                     zero, spaces — no type or range validation at all.
  BUG-005 (MEDIUM): Duplicate Names ALLOWED — no uniqueness constraint.
  BUG-006 (MEDIUM): Generic "Failed to save record" error instead of specific field-level message.
  BUG-007 (LOW)   : History popup shows "No data available" even for existing records.

KEY RULES:
  - Name uses capital 'N': name="Name"
  - Base Uom Conversion uses capital letters: name="Base Uom Conversion"
  - Only 1 toggle: Status (Active/Inactive), inside app-slide-toggle-v2
  - History column uses cdk-column-archive (NOT cdk-column-history)
  - Base Uom and UOM share same option list but are INDEPENDENT (no auto-sync)
  - HSN SAC Code has only 4 options: 271536, 780341, 748554, 655403
  - NEVER use Keys.ESCAPE (closes entire popup form)
  - ALL SweetAlert2 dismissals MUST use JS querySelector click
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_service_name(prefix="AutoSvc"):
    """Generate a unique service name with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_base_uom_conversion():
    """Generate a valid Base Uom Conversion value (positive number, max 10 chars)."""
    return str(random.randint(1, 999))


def generate_description():
    """Generate a random description text."""
    words = [
        "Test service entry", "Automated test data", "Selenium validation",
        "Regression test service", "QA automation entry", "Smoke test data",
        "Performance test service", "Integration test entry",
        "Commodity test service", "Service validation item"
    ]
    return f"{random.choice(words)} - {random.randint(1000, 9999)}"


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_service_data(name_prefix="AutoSvc"):
    """Generate a complete dict of valid service data for Create form.
    Dropdown values set to None — will be populated from live UI at runtime.
    """
    return {
        "name": generate_service_name(name_prefix),
        "base_uom": None,           # Pick from live UI (REQUIRED)
        "uom": None,                # Pick from live UI (REQUIRED)
        "hsn_sac_code": None,       # Pick from live UI (REQUIRED)
        "base_uom_conversion": generate_base_uom_conversion(),
        "status": True,             # Active (default)
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_long_name(length=256):
    """Generate a string of exactly `length` characters for Name field.
    Server rejects names > 255 chars. BUG-001: No maxlength on input.
    """
    return "S" * length


def generate_long_base_uom_conversion(length=11):
    """Generate a string of exactly `length` characters for Base Uom Conversion.
    Server max is 10 chars. BUG-002: No maxlength on input.
    """
    return "9" * length


def generate_spaces_only(length=10):
    """Generate a string of only spaces — BUG-003: accepted without validation."""
    return " " * length


def generate_special_char_name():
    """Generate a name with special characters — BUG-003: no input restrictions."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"Svc{special}"


def generate_negative_uom_conversion():
    """Return a negative Base Uom Conversion value — BUG-004: accepted."""
    return f"-{random.randint(1, 99)}"


def generate_zero_uom_conversion():
    """Return zero for Base Uom Conversion — BUG-004: accepted."""
    return "0"


def generate_alpha_uom_conversion():
    """Return alphabetic characters for Base Uom Conversion — BUG-004: accepted."""
    return "abcDEF"


def generate_special_char_uom_conversion():
    """Return special characters for Base Uom Conversion — BUG-004: accepted."""
    return "!@#$%"


def generate_spaces_uom_conversion():
    """Return spaces for Base Uom Conversion — BUG-004: accepted."""
    return "   "


def generate_decimal_uom_conversion():
    """Return a decimal Base Uom Conversion value."""
    return f"{random.randint(1, 99)}.{random.randint(10, 99)}"


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "name": "",
        "base_uom": "",
        "uom": "",
        "hsn_sac_code": "",
        "base_uom_conversion": "",
    }


def generate_name_only_data(name_prefix="NameOnly"):
    """Return dict with only Name filled — for partial field validation."""
    return {
        "name": generate_service_name(name_prefix),
        "base_uom": "",
        "uom": "",
        "hsn_sac_code": "",
        "base_uom_conversion": "",
    }


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing name — BUG-005: duplicates allowed."""
    return {
        "name": existing_name,
        "base_uom": None,
        "uom": None,
        "hsn_sac_code": None,
        "base_uom_conversion": generate_base_uom_conversion(),
        "status": True,
    }


def generate_valid_edit_data(name_prefix="EditSvc"):
    """Generate valid data for Edit form — fields we want to change."""
    return {
        "name": generate_service_name(name_prefix),
        "base_uom_conversion": generate_base_uom_conversion(),
        "status": True,
    }
