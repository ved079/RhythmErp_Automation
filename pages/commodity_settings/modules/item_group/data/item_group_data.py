"""
item_group_data.py
------------------
Test data generators for RhythmERP Item Group screen.

All values are dynamically generated using timestamps so that
every test run produces unique data (no collisions).

Field catalogue:
  - Code        (text input,   required, max 255, alphanumeric+special accepted)
  - Description (text input,   required, max 255, alphanumeric+special accepted)
"""

import time
import random
import string


# ═══════════════════════════════════════════════════════════════
#  Unique-name helpers
# ═══════════════════════════════════════════════════════════════

def generate_item_group_name(prefix="IG"):
    """Generate a unique Item Group Code string.
    Format: {prefix}_{YYYYMMDDHHMMSS}_{random3}
    Example: IG_20260518174530_482
    """
    ts = time.strftime("%Y%m%d%H%M%S")
    rnd = random.randint(100, 999)
    return f"{prefix}_{ts}_{rnd}"


def generate_item_group_description(prefix="Desc"):
    """Generate a unique Description string.
    Format: {prefix}_{YYYYMMDDHHMMSS}_{random3}
    """
    ts = time.strftime("%Y%m%d%H%M%S")
    rnd = random.randint(100, 999)
    return f"{prefix}_{ts}_{rnd}"


# ═══════════════════════════════════════════════════════════════
#  Valid / Happy-path data
# ═══════════════════════════════════════════════════════════════

def generate_valid_item_group_data():
    """Generate a valid data dict with both Code and Description filled."""
    return {
        "code": generate_item_group_name("IG"),
        "description": generate_item_group_description("TestDesc"),
    }


# ═══════════════════════════════════════════════════════════════
#  Partial / Validation-trigger data
# ═══════════════════════════════════════════════════════════════

def generate_empty_data():
    """Both fields empty — triggers 'Validation Failed'."""
    return {
        "code": "",
        "description": "",
    }


def generate_code_only_data():
    """Only Code filled — triggers 'Validation Failed' for Description."""
    return {
        "code": generate_item_group_name("IGCodeOnly"),
        "description": "",
    }


def generate_description_only_data():
    """Only Description filled — triggers 'Validation Failed' for Code."""
    return {
        "code": "",
        "description": generate_item_group_description("DescOnly"),
    }


# ═══════════════════════════════════════════════════════════════
#  Boundary / Length data
# ═══════════════════════════════════════════════════════════════

def generate_long_code(length=255):
    """Generate a Code string of exactly `length` characters."""
    ts = time.strftime("%Y%m%d%H%M%S")
    prefix = f"IG_{ts}_"
    remaining = length - len(prefix)
    if remaining <= 0:
        return prefix[:length]
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=remaining))
    return prefix + suffix


def generate_long_description(length=255):
    """Generate a Description string of exactly `length` characters."""
    ts = time.strftime("%Y%m%d%H%M%S")
    prefix = f"Desc_{ts}_"
    remaining = length - len(prefix)
    if remaining <= 0:
        return prefix[:length]
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=remaining))
    return prefix + suffix


# ═══════════════════════════════════════════════════════════════
#  Special character / Security data
# ═══════════════════════════════════════════════════════════════

def generate_special_char_code():
    """Code with special characters — tests input sanitization."""
    ts = time.strftime("%H%M%S")
    return f"IG@#{ts}$%"


def generate_special_char_description():
    """Description with special characters."""
    ts = time.strftime("%H%M%S")
    return f"Desc!@{ts}&*"


def generate_spaces_only():
    """Spaces-only string — should trigger validation."""
    return "     "


def generate_sql_injection():
    """SQL injection string — tests input sanitization."""
    return "'; DROP TABLE item_group; --"


def generate_xss_attempt():
    """XSS attempt string — tests input sanitization."""
    return '<script>alert("IG_XSS")</script>'


# ═══════════════════════════════════════════════════════════════
#  Duplicate data
# ═══════════════════════════════════════════════════════════════

def generate_duplicate_code_data(original_code):
    """Generate data with the same Code but different Description.
    Duplicates are ALLOWED on this screen (BUG).
    """
    return {
        "code": original_code,
        "description": generate_item_group_description("DupDesc"),
    }


def generate_exact_duplicate_data(original_code, original_description):
    """Generate data with same Code AND Description (exact duplicate)."""
    return {
        "code": original_code,
        "description": original_description,
    }


# ═══════════════════════════════════════════════════════════════
#  Edit data
# ═══════════════════════════════════════════════════════════════

def generate_valid_edit_data():
    """Generate data for editing an existing record."""
    return {
        "code": generate_item_group_name("IGEdit"),
        "description": generate_item_group_description("EditDesc"),
    }