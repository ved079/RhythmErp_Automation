"""
entity_group_definition_data.py
---------------------------------
Dynamic test data generators for Entity Group Definition automation.
All values are generated at runtime -- no hardcoded test data.

EGD Form fields:
  - Entity Group Name  (text input, required, max 255 chars)
  - Level              (text input, required, numeric, max 255 chars)

KNOWN BUGS (documented at time of inspection):
  BUG-001 (HIGH)   : Duplicate Entity Group Name accepted silently (no error shown)
  BUG-002 (HIGH)   : Spaces-only name accepted without validation
  BUG-003 (MEDIUM) : No success SweetAlert after submit -- popup just closes
  BUG-004 (MEDIUM) : Level field accepts negative numbers
  BUG-005 (LOW)    : Level field accepts decimal numbers
  BUG-006 (LOW)    : Special characters accepted in name without sanitization
  BUG-007 (LOW)    : SQL injection strings not sanitized
  BUG-008 (LOW)    : No success alert after successful submit (same as BUG-003)
"""

import random
import string
from datetime import datetime


# ---------------------------------------------------------------
# Valid Data Generators
# ---------------------------------------------------------------

def generate_valid_name(prefix="ValidE"):
    """Generate a valid Entity Group Name (unique via timestamp)."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_level():
    """Generate a valid Level value (positive integer)."""
    return str(random.randint(1, 100))


def generate_valid_data(name=None, level=None, prefix="ValidE"):
    """Generate a complete dict of valid EGD data.

    Args:
        name:  Entity Group Name. If None, auto-generates a unique name.
        level: Level value. If None, auto-generates a positive integer.
        prefix: Prefix for auto-generated name (used when name is None).

    Returns:
        dict with 'entity_group_name' and 'level' keys.
    """
    return {
        "entity_group_name": name or generate_valid_name(prefix=prefix),
        "level": level or generate_valid_level(),
    }


# ---------------------------------------------------------------
# Empty / Missing Field Generators
# ---------------------------------------------------------------

def generate_empty_data():
    """Return data with all fields empty (for empty-form submit test)."""
    return {
        "entity_group_name": "",
        "level": "",
    }


def generate_empty_name_only():
    """Return data with name empty but level filled."""
    return {
        "entity_group_name": "",
        "level": generate_valid_level(),
    }


def generate_empty_level_only():
    """Return data with level empty but name filled."""
    return {
        "entity_group_name": generate_valid_name("NoLvl"),
        "level": "",
    }


def generate_spaces_only_data():
    """Return data with spaces-only in both fields."""
    return {
        "entity_group_name": " " * 10,
        "level": " " * 5,
    }


def generate_spaces_name_only():
    """Return data with spaces-only name but valid level."""
    return {
        "entity_group_name": " " * 10,
        "level": generate_valid_level(),
    }


# ---------------------------------------------------------------
# Duplicate / Boundary Generators
# ---------------------------------------------------------------

def generate_duplicate_name_data(existing_name):
    """Return data that uses an existing Entity Group Name.

    BUG-001: ERP silently accepts duplicate names (no error shown).
    """
    return {
        "entity_group_name": existing_name,
        "level": generate_valid_level(),
    }


def generate_case_variant_name(existing_name):
    """Return data with same name in different case.

    Tests whether ERP does case-insensitive duplicate check.
    """
    if existing_name:
        # Flip the case of the first letter
        first = existing_name[0]
        flipped = first.swapcase() + existing_name[1:]
        return {
            "entity_group_name": flipped,
            "level": generate_valid_level(),
        }
    return generate_valid_data()


def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (over max)."""
    return "B" * 256


def generate_long_string(length=300):
    """Generate a string of specified length."""
    return "X" * length


# ---------------------------------------------------------------
# Level Validation Generators
# ---------------------------------------------------------------

def generate_negative_level():
    """Generate a negative Level value."""
    return str(random.randint(-100, -1))


def generate_decimal_level():
    """Generate a decimal Level value."""
    return str(round(random.uniform(1.1, 99.9), 2))


def generate_zero_level():
    """Generate a zero Level value."""
    return "0"


def generate_very_large_level():
    """Generate a very large Level value."""
    return "999999999"


# ---------------------------------------------------------------
# Special Input Generators
# ---------------------------------------------------------------

def generate_special_char_data():
    """Generate a name with common special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return {
        "entity_group_name": f"EGD{special}",
        "level": generate_valid_level(),
    }


def generate_sql_injection_data():
    """Generate SQL injection strings to test input sanitization."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE entity_group; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM items --",
        "\" OR \"1\"=\"1",
    ]
    return {
        "entity_group_name": random.choice(injections),
        "level": generate_valid_level(),
    }


def generate_xss_data():
    """Generate XSS payload strings to test input sanitization."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
    ]
    return {
        "entity_group_name": random.choice(payloads),
        "level": generate_valid_level(),
    }


def generate_unicode_data():
    """Generate a name with unicode/international characters."""
    unicode_samples = [
        "EGD\u00e9",           # Latin e-acute
        "EGD\u00fc",           # Latin u-umlaut
        "\u4e2d\u6587\u7ec4",  # Chinese: 中文组
        "\u092a\u094d\u0930\u0924\u093f\u0917\u094d\u0930\u0941\u092a",  # Hindi
        "\u0433\u0440\u0443\u043f\u043f\u0430",  # Russian: группа
    ]
    return {
        "entity_group_name": random.choice(unicode_samples),
        "level": generate_valid_level(),
    }


# ---------------------------------------------------------------
# Edit-Mode Generators
# ---------------------------------------------------------------

def generate_edit_data():
    """Generate data for editing an existing EGD record."""
    return {
        "entity_group_name": generate_valid_name("Edited"),
        "level": str(random.randint(101, 200)),
    }
