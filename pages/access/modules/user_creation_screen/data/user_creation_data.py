"""
user_creation_data.py
---------------------
Test data generators for RhythmERP User Creation Screen.

Location: Master Setup > User Creation Screen
URL:      /#/master-setup/usercreationscreen

FORM LAYOUT (SIMPLE POPUP — NOT a stepper):
  - Username         (text input,   required, formcontrolname="username")
  - Email            (text input,   required, formcontrolname="email")
  - First Name       (text input,   required, formcontrolname="first_name")
  - Last Name        (text input,   required, formcontrolname="last_name")
  - Password         (password,     required, formcontrolname="password")
  - User Type        (mat-select,   required, no formcontrolname)
  - Role             (mat-select,   required, dynamic, no formcontrolname)
  - Entity           (mat-select,   required, dynamic, no formcontrolname)
  - Designation      (mat-select,   required, no formcontrolname)
  - Active           (mat-checkbox, optional, formcontrolname="is_active", default checked)
  - Staff            (mat-checkbox, optional, formcontrolname="is_staff", default unchecked)

KEY RULES (verified 2026-05-21 on live app):
  - Username: spaces/special-chars show SweetAlert2 error
  - No maxlength on Username — 256+ chars accepted (BUG-002)
  - No email format validation on blur (BUG-003)
  - Spaces in Username show generic "should not contain spaces" (BUG-004)
  - Designation dropdown has duplicate "Manager" option (BUG-005)
  - Only 1 mat-error visible at a time (BUG-006)
  - Duplicate username: Submit silently fails, NO error message (BUG-001)
  - Edit mode button says "Update" not "Submit"
  - View mode has disabled fields, Cancel button only
  - SweetAlert2: success toast on valid create
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_username(prefix="AutoUser"):
    """Generate a random username with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_email(prefix="autouser"):
    """Generate a random email address for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}@testmail.com"


def generate_password(length=16):
    """Generate a random password meeting ERP requirements.

    Uses uppercase, lowercase, digits, and special characters.
    Default length 16 (ERP requires strong passwords).
    """
    if length < 8:
        length = 8
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(random.choices(chars, k=length))


def generate_name(prefix="Test"):
    """Generate a random first/last name."""
    return f"{prefix}_{random.randint(1000, 9999)}"


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_user_data(name_prefix="AutoUser"):
    """Generate a complete dict of valid user data for Create form.

    Dropdown fields (user_type, role, entity, designation) set to None
    so they are picked from the live UI at runtime.
    """
    return {
        "username": generate_username(name_prefix),
        "email": generate_email(name_prefix.lower()),
        "first_name": generate_name("First"),
        "last_name": generate_name("Last"),
        "password": generate_password(),
        "user_type": None,       # Pick from live UI (REQUIRED)
        "role": None,            # Pick from live UI (REQUIRED, dynamic)
        "entity": None,          # Pick from live UI (REQUIRED, dynamic)
        "designation": None,     # Pick from live UI (REQUIRED)
        "is_active": True,       # Default checked
        "is_staff": False,       # Default unchecked
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_spaces_only(length=10):
    """Generate a string of only spaces (for Username validation test)."""
    return " " * length


def generate_special_char_username():
    """Generate a username with special characters."""
    return "Test!@#$%^&*()User"


def generate_sql_injection_username():
    """Generate a SQL injection string for Username."""
    return "'; DROP TABLE users; --"


def generate_xss_payload_username():
    """Generate an XSS payload string for Username."""
    return "<script>alert('xss')</script>"


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds typical max)."""
    return "A" * 256


def generate_string_500():
    """Generate a string of exactly 500 characters (over-max boundary)."""
    return "A" * 500


def generate_invalid_email():
    """Generate an invalid email format."""
    return "not-an-email"


def generate_numbers_only_username():
    """Generate a numbers-only username."""
    return "1234567890"


def generate_leading_trailing_spaces_username():
    """Generate a username with leading and trailing spaces."""
    return "  SpaceTestUser  "


def generate_unicode_username():
    """Generate a username with Unicode characters."""
    return "TestUser\u00e9\u00f1\u00fc\u00e4\u00f6"


def generate_duplicate_user_data(existing_email):
    """Return valid data using an existing email — for duplicate email test.

    BUG-001: Duplicate usernames silently fail. This test checks
    what happens when the same email is used.
    """
    return {
        "username": generate_username("DupUser"),
        "email": existing_email,
        "first_name": generate_name("DupFirst"),
        "last_name": generate_name("DupLast"),
        "password": generate_password(),
        "user_type": None,
        "role": None,
        "entity": None,
        "designation": None,
        "is_active": True,
        "is_staff": False,
    }


def generate_duplicate_username_data(existing_username):
    """Return valid data using an existing username — for duplicate username test.

    BUG-001: Duplicate username: Submit silently fails, NO error message.
    """
    return {
        "username": existing_username,
        "email": generate_email("dupun"),
        "first_name": generate_name("DupFirst"),
        "last_name": generate_name("DupLast"),
        "password": generate_password(),
        "user_type": None,
        "role": None,
        "entity": None,
        "designation": None,
        "is_active": True,
        "is_staff": False,
    }


def generate_case_insensitive_duplicate_username(existing_username):
    """Return a lowercase version of an existing username for case test."""
    return {
        "username": existing_username.lower(),
        "email": generate_email("dupci"),
        "first_name": generate_name("DupFirst"),
        "last_name": generate_name("DupLast"),
        "password": generate_password(),
        "user_type": None,
        "role": None,
        "entity": None,
        "designation": None,
        "is_active": True,
        "is_staff": False,
    }


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "username": "",
        "email": "",
        "first_name": "",
        "last_name": "",
        "password": "",
        "user_type": "",
        "role": "",
        "entity": "",
        "designation": "",
        "is_active": None,
        "is_staff": None,
    }


def generate_username_only_data(name_prefix="NameOnly"):
    """Return dict with only Username filled — for partial field validation."""
    return {
        "username": generate_username(name_prefix),
        "email": "",
        "first_name": "",
        "last_name": "",
        "password": "",
        "user_type": "",
        "role": "",
        "entity": "",
        "designation": "",
        "is_active": None,
        "is_staff": None,
    }


# ──────────────────────────────────────────────
# Valid Edit Data
# ──────────────────────────────────────────────

def generate_valid_edit_data(name_prefix="EditUser"):
    """Generate valid data for Edit form — only fields we want to change.

    For User Creation, the editable fields in Edit mode typically include:
    first_name, last_name, email. Username may be read-only in Edit.
    """
    return {
        "first_name": generate_name("Edited"),
        "last_name": generate_name("EditedLn"),
        "email": generate_email(name_prefix.lower()),
    }


# ──────────────────────────────────────────────
# Search Test Data
# ──────────────────────────────────────────────

def generate_search_test_data(name_prefix="SearchEx"):
    """Generate data specifically for search tests — prefix is easy to find."""
    return generate_valid_user_data(name_prefix)