"""
item_group_data.py
------------------
Dynamic test data generators for Item Group automation.
All values are generated at runtime — no hardcoded test data.

Item Group form fields:
  - Code          (text, required, max 255, alphanumericSpecial)
  - Description   (text, required, max 255, alphanumericSpecial)
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Valid Data Generators
# ──────────────────────────────────────────────

def generate_ig_code(prefix="AutoIG"):
    """Generate a random Item Group code with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_ig_description(prefix="Auto Desc"):
    """Generate a random Item Group description."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_ig_data(code_prefix="AutoIG", desc_prefix="Auto Desc"):
    """Generate a complete dict of valid Item Group data for Create form.

    Both Code and Description are required fields.
    """
    return {
        "code": generate_ig_code(code_prefix),
        "description": generate_ig_description(desc_prefix),
    }


def generate_valid_edit_data(code_prefix="EditIG", desc_prefix="Edit Desc"):
    """Generate valid data for Edit form — new code and description to update to."""
    return {
        "code": generate_ig_code(code_prefix),
        "description": generate_ig_description(desc_prefix),
    }


# ──────────────────────────────────────────────
# Partial Data Generators (one field missing/empty)
# ──────────────────────────────────────────────

def generate_empty_code_data():
    """Return dict with empty Code — for mandatory field validation."""
    return {
        "code": "",
        "description": generate_ig_description("HasDesc"),
    }


def generate_empty_description_data():
    """Return dict with empty Description — for mandatory field validation."""
    return {
        "code": generate_ig_code("HasCode"),
        "description": "",
    }


def generate_both_empty_data():
    """Return dict with both Code and Description empty."""
    return {
        "code": "",
        "description": "",
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_spaces_only_code_data(length=10):
    """Return dict with spaces-only Code."""
    return {
        "code": generate_spaces_only(length),
        "description": generate_ig_description("SpaceCode"),
    }


def generate_spaces_only_description_data(length=10):
    """Return dict with spaces-only Description."""
    return {
        "code": generate_ig_code("SpaceDesc"),
        "description": generate_spaces_only(length),
    }


def generate_duplicate_code_data(existing_code):
    """Return valid data using an existing code — for duplicate code test.

    BEH-004: Duplicate Codes are currently ALLOWED.
    Test documents current behavior as known bug — passes either way.
    """
    return {
        "code": existing_code,
        "description": generate_ig_description("DupCode"),
    }


def generate_string_255():
    """Generate a string of exactly 255 characters (typical max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds typical max)."""
    return "A" * 256


def generate_long_string(length=300):
    """Generate a string of specified length (for maxlength boundary testing)."""
    return "X" * length


def generate_special_char_code():
    """Generate a code with common special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"IG{special}"


def generate_special_char_data():
    """Return dict with special-character code and description."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return {
        "code": f"IG{special}",
        "description": f"Desc{special}",
    }


def generate_sql_injection_code():
    """Generate SQL injection strings to test input sanitization."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE item_groups; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM item_groups --",
        "\" OR \"1\"=\"1",
    ]
    return random.choice(injections)


def generate_sql_injection_data():
    """Return dict with SQL injection code."""
    return {
        "code": generate_sql_injection_code(),
        "description": generate_ig_description("SQLTest"),
    }


def generate_xss_code():
    """Generate XSS payload strings to test input sanitization."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
    ]
    return random.choice(payloads)


def generate_xss_data():
    """Return dict with XSS payload code."""
    return {
        "code": generate_xss_code(),
        "description": generate_ig_description("XSSTest"),
    }


def generate_unicode_code():
    """Generate a code with unicode/international characters."""
    unicode_samples = [
        "IG\u00e9",           # Latin é
        "IG\u00fc",           # Latin ü
        "\u4e2d\u6587\u7ec4",  # 中文组 (Chinese group)
        "\u0938\u092e\u0942\u0939",  # समूह (Hindi group)
        "\u0433\u0440\u0443\u043f\u043f\u0430",  # группа (Russian group)
        "Grupp\u00e0",        # Italian à
        "Grup\u00f3",         # Spanish ó
    ]
    return random.choice(unicode_samples)


def generate_unicode_data():
    """Return dict with unicode code."""
    return {
        "code": generate_unicode_code(),
        "description": generate_ig_description("UniTest"),
    }


def generate_code_with_leading_trailing_spaces():
    """Generate a code with leading and trailing spaces.
    Tests whether ERP trims whitespace before storing.
    """
    base = generate_ig_code("SpaceIG")
    return f"   {base}   "


def generate_leading_trailing_spaces_data():
    """Return dict with code having leading/trailing spaces."""
    return {
        "code": generate_code_with_leading_trailing_spaces(),
        "description": generate_ig_description("TrimTest"),
    }


def generate_name_with_inner_spaces():
    """Generate a valid code containing inner spaces (should be accepted)."""
    return f"Item Group {random.randint(1000, 9999)}"


def generate_code_with_numbers():
    """Generate a code that is purely numeric."""
    return str(random.randint(100000, 999999))


def generate_code_with_mixed_case():
    """Generate a code with mixed upper/lower case to test case sensitivity."""
    base = generate_ig_code("MixIG")
    return ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(base))


def generate_single_char_code():
    """Generate a single-character code (minimum meaningful input)."""
    return random.choice(string.ascii_uppercase)
