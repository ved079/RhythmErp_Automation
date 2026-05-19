"""
entity_group_definition_data.py
-------------------------------
Test data generators for Entity Group Definition automation.

Form Fields (2):
  - Entity Group Name  (text input,   required, formcontrolname="entity_group")
  - Level              (number input, required, formcontrolname="level")

KNOWN BUGS (documented at time of inspection):
  BUG-001 (HIGH)  : Spaces-only Entity Group Name accepted — creates blank record
  BUG-002 (HIGH)  : Exact duplicate name silently rejected with NO user feedback
  BUG-003 (HIGH)  : Case-insensitive duplicate NOT blocked ("agdi" ≠ "Agdi")
  BUG-004 (MEDIUM): Negative Level values accepted (no min validation)
  BUG-005 (MEDIUM): Decimal Level values accepted (no step="1" validation)
  BUG-006 (LOW)   : Special characters in Entity Group Name accepted
  BUG-007 (LOW)   : No maxlength on Entity Group Name
  BUG-008 (LOW)   : No success SweetAlert after create/update
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Valid Data Generators
# ──────────────────────────────────────────────

def generate_entity_group_name(prefix="AutoEGD"):
    """Generate a random Entity Group Name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_level():
    """Generate a valid integer Level value (positive, 1-50 range)."""
    return random.randint(1, 50)


def generate_valid_data(name_prefix="AutoEGD", level=None):
    """Generate a complete dict of valid Entity Group Definition data for Create form.

    Args:
        name_prefix: prefix for the auto-generated Entity Group Name
        level: explicit level value; if None, auto-generates a valid integer

    Returns:
        dict with keys: entity_group (str), level (int)
    """
    return {
        "entity_group": generate_entity_group_name(name_prefix),
        "level": level if level is not None else generate_valid_level(),
    }


def generate_valid_edit_data(name_prefix="EditEGD"):
    """Generate valid data for Edit form — new name and level to update to."""
    return {
        "entity_group": generate_entity_group_name(name_prefix),
        "level": random.randint(1, 50),
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_empty_data():
    """Return dict with both fields empty — for mandatory field validation."""
    return {
        "entity_group": "",
        "level": "",
    }


def generate_empty_name_only(level=10):
    """Return dict with empty Entity Group Name but valid Level."""
    return {
        "entity_group": "",
        "level": level,
    }


def generate_empty_level_only(name_prefix="NoLevel"):
    """Return dict with valid Entity Group Name but empty Level."""
    return {
        "entity_group": generate_entity_group_name(name_prefix),
        "level": "",
    }


def generate_spaces_only_name(length=10):
    """Generate a string of only spaces for Entity Group Name.
    BUG-001: Spaces-only name currently creates an empty record.
    """
    return " " * length


def generate_spaces_only_data(length=10, level=10):
    """Return dict with spaces-only Entity Group Name."""
    return {
        "entity_group": generate_spaces_only_name(length),
        "level": level,
    }


def generate_duplicate_name_data(existing_name, level=99):
    """Return data using an existing Entity Group Name — for duplicate test.
    BUG-002: Exact duplicates are silently rejected (no feedback).
    BUG-003: Case-insensitive duplicates are NOT blocked.
    """
    return {
        "entity_group": existing_name,
        "level": level,
    }


def generate_case_variant_name(existing_name, level=99):
    """Return data with a case-variant of existing name.
    BUG-003: "agdi" is NOT blocked when "Agdi" exists.
    """
    return {
        "entity_group": existing_name.lower(),
        "level": level,
    }


def generate_space_ignored_name(existing_name, level=99):
    """Return data with spaces added to an existing name.
    Tests whether spaces are ignored in duplicate check.
    """
    return {
        "entity_group": f" {existing_name} ",
        "level": level,
    }


def generate_string_255():
    """Generate a string of exactly 255 characters (typical max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds typical max).
    BUG-007: No maxlength on input, long names accepted.
    """
    return "A" * 256


def generate_long_string(length=300):
    """Generate a string of specified length for maxlength boundary testing.
    BUG-007: ERP accepts very long names without maxlength.
    """
    return "X" * length


def generate_negative_level(level=-5):
    """Return data with a negative Level value.
    BUG-004: Negative Level values are accepted.
    """
    return {
        "entity_group": generate_entity_group_name("NegLvl"),
        "level": level,
    }


def generate_decimal_level(level=3.5):
    """Return data with a decimal Level value.
    BUG-005: Decimal Level values are accepted.
    """
    return {
        "entity_group": generate_entity_group_name("DecLvl"),
        "level": level,
    }


def generate_zero_level():
    """Return data with Level = 0.
    Level 0 should be valid (e.g., "Agdi" has Level 0 in production).
    """
    return {
        "entity_group": generate_entity_group_name("ZeroLvl"),
        "level": 0,
    }


def generate_special_char_name():
    """Generate a name with common special characters.
    BUG-006: Special characters are accepted in Entity Group Name.
    """
    special = "!@#$%^&*()"
    return f"EGD{special}"


def generate_special_char_data(level=55):
    """Return dict with special-character name."""
    return {
        "entity_group": generate_special_char_name(),
        "level": level,
    }


def generate_sql_injection_name():
    """Generate SQL injection strings to test input sanitization."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE entity_groups; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM entity_groups --",
        "\" OR \"1\"=\"1",
    ]
    return random.choice(injections)


def generate_sql_injection_data(level=10):
    """Return dict with SQL injection name."""
    return {
        "entity_group": generate_sql_injection_name(),
        "level": level,
    }


def generate_xss_name():
    """Generate XSS payload strings to test input sanitization."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
    ]
    return random.choice(payloads)


def generate_xss_data(level=10):
    """Return dict with XSS payload name."""
    return {
        "entity_group": generate_xss_name(),
        "level": level,
    }


def generate_unicode_name():
    """Generate a name with unicode/international characters."""
    unicode_samples = [
        "Entity\u00e9",          # Latin e-acute
        "Entity\u00fc",          # Latin u-umlaut
        "\u4e2d\u6587\u5b9e\u4f53",  # Chinese characters
        "\u0924\u0924\u094d\u0935",  # Hindi characters
        "\u0421\u0443\u0449\u043d\u043e\u0441\u0442\u044c",  # Russian
        "Entit\u00e0",           # Italian a-grave
        "Entid\u00e1d",         # Spanish a-acute
    ]
    return random.choice(unicode_samples)


def generate_unicode_data(level=10):
    """Return dict with unicode name."""
    return {
        "entity_group": generate_unicode_name(),
        "level": level,
    }


def generate_name_with_leading_trailing_spaces():
    """Generate a name with leading and trailing spaces.
    Tests whether ERP trims whitespace before storing.
    """
    base = generate_entity_group_name("SpaceEGD")
    return f"   {base}   "


def generate_name_with_inner_spaces():
    """Generate a valid name containing inner spaces (should be accepted)."""
    return f"Entity Group {random.randint(1000, 9999)}"


def generate_name_with_numbers():
    """Generate a name that is purely numeric."""
    return str(random.randint(100000, 999999))


def generate_name_with_mixed_case():
    """Generate a name with mixed upper/lower case to test case sensitivity."""
    name = generate_entity_group_name("MixEGD")
    return ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(name))


def generate_single_char_name():
    """Generate a single-character name (minimum meaningful input)."""
    return random.choice(string.ascii_uppercase)
