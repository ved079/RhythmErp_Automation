"""
item_category_data.py
---------------------
Test data generators for RhythmERP Item Category screen.

Location: Commodity Settings > Item Category
URL:      /#/dynamic-screens/Item%20Category

FORM LAYOUT (Simple popup — NOT a stepper):
  - Item Category       (text input,   required)
  - Item Description    (text input,   required)
  - Level               (number input, required — accepts negatives, no decimals,
                         leading zeros stripped on save, accepts 0)

TABLE COLUMNS:
  - View / Edit / History   (action buttons per row)
  - Item Category / Item Description / Level

NOTES:
  - NO Status toggle
  - NO dropdowns
  - NO Delete button
  - HAS History button
  - Duplicates ALLOWED for Item Category name
  - Level field: accepts negative integers, strips leading zeros on save,
    accepts 0, does NOT accept decimals

KEY RULES:
  - NEVER use Keys.ESCAPE (closes entire popup form!)
  - ALL SweetAlert2 dismissals MUST use JS querySelector click
  - Test prefix: IC
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_item_category_name(prefix="AutoIC"):
    """Generate a unique Item Category name with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_item_description():
    """Generate a random Item Description text."""
    words = [
        "Test category entry", "Automated test data", "Selenium validation",
        "Regression test category", "QA automation entry", "Smoke test data",
        "Performance test category", "Integration test entry",
        "Commodity test category", "Category validation item"
    ]
    return f"{random.choice(words)} - {random.randint(1000, 9999)}"


def generate_level():
    """Generate a valid positive Level value."""
    return str(random.randint(1, 100))


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_item_category_data(name_prefix="AutoIC"):
    """Generate a complete dict of valid Item Category data for Create form."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": generate_item_description(),
        "level": generate_level(),
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_long_category_name(length=256):
    """Generate a string of exactly `length` characters for Item Category field."""
    return "C" * length


def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_special_char_category():
    """Generate a category name with special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"IC{special}"


def generate_sql_injection():
    """Generate SQL injection string for testing."""
    return "'; DROP TABLE item_category; --"


def generate_xss_attempt():
    """Generate XSS attempt string for testing."""
    return "<script>alert('xss')</script>"


def generate_negative_level():
    """Return a negative Level value — accepted by the field."""
    return f"-{random.randint(1, 99)}"


def generate_zero_level():
    """Return zero for Level — accepted by the field."""
    return "0"


def generate_decimal_level():
    """Return a decimal Level value — should be rejected or truncated."""
    return f"{random.randint(1, 99)}.{random.randint(10, 99)}"


def generate_leading_zeros_level():
    """Return a Level with leading zeros — should be stripped on save."""
    return "007"


def generate_large_level():
    """Return a very large number for Level."""
    return "9999999"


def generate_alpha_level():
    """Return alphabetic characters for Level — should not type in number field."""
    return "abc"


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "item_category": "",
        "item_description": "",
        "level": "",
    }


def generate_category_only_data(name_prefix="CatOnly"):
    """Return dict with only Item Category filled."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": "",
        "level": "",
    }


def generate_description_only_data():
    """Return dict with only Item Description filled."""
    return {
        "item_category": "",
        "item_description": generate_item_description(),
        "level": "",
    }


def generate_level_only_data():
    """Return dict with only Level filled."""
    return {
        "item_category": "",
        "item_description": "",
        "level": generate_level(),
    }


def generate_category_description_no_level(name_prefix="CatDesc"):
    """Return dict with Item Category and Description but no Level."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": generate_item_description(),
        "level": "",
    }


def generate_category_level_no_description(name_prefix="CatLvl"):
    """Return dict with Item Category and Level but no Description."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": "",
        "level": generate_level(),
    }


def generate_duplicate_category_data(existing_name):
    """Return valid data using an existing Item Category name — duplicates allowed."""
    return {
        "item_category": existing_name,
        "item_description": generate_item_description(),
        "level": generate_level(),
    }


def generate_valid_edit_data(name_prefix="EditIC"):
    """Generate valid data for Edit form — fields we want to change."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": generate_item_description(),
        "level": generate_level(),
    }
