"""
user_creation_data.py
---------------------
Test data & expected validation messages for Rhythm ERP User Creation Screen.
Derived from user_creation_master_spec.xlsx (Step 2F).

FIELD REFERENCE:
  1. Username      (text, required) — no spaces, must be unique
  2. Email          (text, required) — format not validated on blur
  3. First Name     (text, required) — no sanitization
  4. Last Name      (text, required) — no sanitization
  5. Password       (password, required on Create)
  6. User Type      (mat-select, required) — Maker / Checker / Both / Approver
  7. Role           (mat-select, required) — dynamic
  8. Entity         (mat-select, required) — dynamic
  9. Designation    (mat-select, required) — Manager / fr / AutoDesig DDXSBMAE / Manager
 10. Active         (checkbox, optional, default=checked)
 11. Staff          (checkbox, optional, default=unchecked)
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Unique-name generators
# ──────────────────────────────────────────────

def generate_username(prefix="AutoUC"):
    """Generate a unique username with prefix and timestamp."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{ts}_{rand}"


def generate_email(prefix="autouc"):
    """Generate a unique email address."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{ts}_{rand}@automation-test.com"


def generate_first_name(prefix="AutoFirst"):
    ts = datetime.now().strftime("%H%M%S")
    return f"{prefix}_{ts}"


def generate_last_name(prefix="AutoLast"):
    ts = datetime.now().strftime("%H%M%S")
    return f"{prefix}_{ts}"


def generate_password(length=12):
    """Generate a random valid password."""
    upper = random.choices(string.ascii_uppercase, k=3)
    lower = random.choices(string.ascii_lowercase, k=3)
    digits = random.choices(string.digits, k=3)
    special = random.choices("!@#$%", k=1)
    pool = upper + lower + digits + special
    random.shuffle(pool)
    return "".join(pool)


# ──────────────────────────────────────────────
# Valid data generators
# ──────────────────────────────────────────────

def generate_valid_user_data(username_prefix="AutoUC"):
    """Generate a complete dict of valid user data for the Create form.
    Dropdown values (user_type, role, entity, designation) are set to None —
    must be populated from live UI at runtime via page methods.
    """
    return {
        "username": generate_username(username_prefix),
        "email": generate_email("uc"),
        "first_name": generate_first_name(),
        "last_name": generate_last_name(),
        "password": generate_password(),
        "user_type": None,       # To be picked from live UI dropdown
        "role": None,            # To be picked from live UI dropdown
        "entity": None,          # To be picked from live UI dropdown
        "designation": None,     # To be picked from live UI dropdown
        "is_active": True,
        "is_staff": False,
    }


def generate_valid_edit_data():
    """Generate valid data for Edit form — only fields we want to change."""
    return {
        "first_name": generate_first_name("EditFn"),
        "last_name": generate_last_name("EditLn"),
        "email": generate_email("edit"),
    }


# ──────────────────────────────────────────────
# Validation / boundary test data helpers
# ──────────────────────────────────────────────

def generate_string_255():
    return "A" * 255


def generate_string_256():
    return "A" * 256


def generate_spaces_only(length=10):
    return " " * length


def generate_special_char_username():
    return "User!@#$%^&*()"


def generate_xss_username():
    return "<script>alert('xss')</script>"


def generate_sql_injection_username():
    return "' OR 1=1 --"


def generate_invalid_email():
    return "notanemail"


def generate_email_no_at():
    return "userdomain.com"


def generate_email_no_domain():
    return "user@"


def generate_special_char_name():
    return "Test!@#$%^&*()"


def generate_empty_data():
    """All fields empty — for mandatory-field validation."""
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
    }


def generate_duplicate_username_data(existing_username):
    """Return valid data using an existing username — for duplicate test."""
    return {
        "username": existing_username,
        "email": generate_email("dup"),
        "first_name": generate_first_name("Dup"),
        "last_name": generate_last_name("Dup"),
        "password": generate_password(),
        "user_type": None,
        "role": None,
        "entity": None,
        "designation": None,
    }


def generate_duplicate_email_data(existing_email):
    """Return valid data using an existing email — for duplicate email test."""
    return {
        "username": generate_username("DupEmail"),
        "email": existing_email,
        "first_name": generate_first_name("DupE"),
        "last_name": generate_last_name("DupE"),
        "password": generate_password(),
        "user_type": None,
        "role": None,
        "entity": None,
        "designation": None,
    }


def generate_case_variant_username(existing_username):
    """Return uppercase version of existing username — case sensitivity test."""
    return existing_username.upper()


# ──────────────────────────────────────────────
# Expected validation messages (from ERP exploration)
# ──────────────────────────────────────────────

class ExpectedMessages:
    """Exact error messages observed on the ERP."""
    USERNAME_REQUIRED = "Username is required"
    USERNAME_NO_SPACES = "Username should not contain spaces"
    # BUG: duplicate username shows NO error message (silent block)
    DUPLICATE_USERNAME_SILENT = "(silent block — no error message shown)"
    # BUG: only 1 mat-error visible at a time
    ONLY_ONE_MAT_ERROR = "(only Username mat-error visible; others get ng-invalid CSS only)"
    # BUG: special chars trigger same message as spaces
    SPECIAL_CHARS_SAME_AS_SPACES = "Username should not contain spaces"
    # Password placeholder in Edit
    PASSWORD_EDIT_PLACEHOLDER = "Leave blank to keep current"


# ──────────────────────────────────────────────
# Known bugs (from Bug Registry in master spec)
# ──────────────────────────────────────────────

class KnownBugs:
    """Bug IDs from master spec for @pytest.mark.xfail references."""
    BUG_001 = "BUG-001: Duplicate Username silently blocked — no error message"
    BUG_002 = "BUG-002: No maxlength on Username — 256+ chars accepted"
    BUG_003 = "BUG-003: No email format validation on blur or submit"
    BUG_004 = "BUG-004: Misleading error for special chars in Username"
    BUG_005 = "BUG-005: No input sanitization on First Name / Last Name"
    BUG_006 = "BUG-006: Only 1 mat-error visible at a time"
    BUG_007 = "BUG-007: Duplicate 'Manager' option in Designation dropdown"
