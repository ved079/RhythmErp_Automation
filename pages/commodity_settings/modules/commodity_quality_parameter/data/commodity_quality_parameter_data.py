"""
commodity_quality_parameter_data.py
------------------------------------
Dynamic test data generators for Commodity Quality Parameter automation.
All values are generated at runtime — no hardcoded test data.

CQP Form fields:
  HEADER:
    - Item Name            (mat-select, required, searchable)
    - Transaction Type     (mat-select, required, 8 options)
    - From Date            (datepicker, required, DD/MM/YYYY)
    - To Date              (datepicker, required, DD/MM/YYYY)
    - Revision Status      (text, optional)

  DETAIL GRID:
    - Quality Parameter    (mat-select, required, searchable)
    - Min Quality Value    (text, required, max 255)
    - Max Quality Value    (text, required, max 255)
    - Is Rate/Percentage   (toggle, required, Yes/No)
    - Multiplier           (text, required, max 255)

Transaction Type Options (8):
  'Return Stock Down', 'Stock Transfer Down', 'Stock Down',
  'Return Stock Up', 'Stock Transfer Up', 'Stock Up',
  Sales, Purchase
"""

import random
import string
from datetime import datetime, timedelta


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

TRANSACTION_TYPES = [
    "'Return Stock Down'",
    "'Stock Transfer Down'",
    "'Stock Down'",
    "'Return Stock Up'",
    "'Stock Transfer Up'",
    "'Stock Up'",
    "Sales",
    "Purchase",
]


# ──────────────────────────────────────────────
# Valid Data Generators — Header
# ──────────────────────────────────────────────

def generate_from_date():
    """Generate a From Date string in DD/MM/YYYY format (current date)."""
    return datetime.now().strftime("%d/%m/%Y")


def generate_to_date():
    """Generate a To Date string in DD/MM/YYYY format (far future).
    Matches the ERP's auto-fill sentinel of 30/12/2099.
    """
    return "30/12/2099"


def generate_revision_status(prefix="AutoRev"):
    """Generate a Revision Status string."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_header_data(
    item_name=None,
    transaction_type=None,
    from_date=None,
    to_date=None,
    revision_status=None,
):
    """Generate a complete dict of valid CQP header data.

    If item_name or transaction_type is None, the page object
    will select a random option from the dropdown.

    NOTE: from_date is set to None by default because the ERP
    auto-fills From Date with today's date.  The page object
    skips filling it unless from_date_force=True is set.
    """
    data = {
        "item_name": item_name,         # None = auto-select random
        "transaction_type": transaction_type,  # None = auto-select random
        "from_date": None,              # None = skip (ERP auto-fills today)
        "to_date": to_date or generate_to_date(),  # Default: 30/12/2099
        "revision_status": revision_status,  # None = skip optional field
    }
    return data


# ──────────────────────────────────────────────
# Valid Data Generators — Detail Grid
# ──────────────────────────────────────────────

def generate_min_quality_value(prefix="Min"):
    """Generate a Min Quality Value string."""
    rand = random.uniform(0.1, 50.0)
    return f"{rand:.2f}"


def generate_max_quality_value(prefix="Max"):
    """Generate a Max Quality Value string (always > min)."""
    rand = random.uniform(51.0, 100.0)
    return f"{rand:.2f}"


def generate_multiplier():
    """Generate a Multiplier value string."""
    rand = random.uniform(0.1, 10.0)
    return f"{rand:.2f}"


def generate_valid_detail_data(
    quality_parameter=None,
    min_quality_value=None,
    max_quality_value=None,
    is_rate_percentage=False,
    multiplier=None,
):
    """Generate a complete dict of valid CQP detail row data.

    If quality_parameter is None, the page object will
    select a random option from the dropdown.
    """
    data = {
        "quality_parameter": quality_parameter,  # None = auto-select random
        "min_quality_value": min_quality_value or generate_min_quality_value(),
        "max_quality_value": max_quality_value or generate_max_quality_value(),
        "is_rate_percentage": is_rate_percentage,
        "multiplier": multiplier or generate_multiplier(),
    }
    return data


def generate_valid_cqp_data():
    """Generate complete header + detail data for a full CQP record."""
    return {
        "header": generate_valid_header_data(),
        "detail": generate_valid_detail_data(),
    }


# ──────────────────────────────────────────────
# Partial Data Generators (missing fields)
# ──────────────────────────────────────────────

def generate_header_no_item_name():
    """Return header data with item_name explicitly set to skip."""
    return {
        "item_name": None,
        "select_item_name": False,  # Don't select at all
        "transaction_type": None,   # Auto-select random
        "from_date": None,          # Skip (ERP auto-fills)
        "to_date": generate_to_date(),
    }


def generate_header_no_transaction_type():
    """Return header data with transaction_type explicitly set to skip."""
    return {
        "item_name": None,          # Auto-select random
        "transaction_type": None,
        "select_transaction_type": False,  # Don't select at all
        "from_date": None,          # Skip (ERP auto-fills)
        "to_date": generate_to_date(),
    }


def generate_empty_header_data():
    """Return header data with all fields skipped."""
    return {
        "item_name": None,
        "select_item_name": False,
        "transaction_type": None,
        "select_transaction_type": False,
        "from_date": "",
        "to_date": "",
        "revision_status": "",
    }


def generate_detail_no_qp():
    """Return detail data with quality_parameter explicitly set to skip."""
    return {
        "quality_parameter": None,
        "select_qp": False,  # Don't select at all
        "min_quality_value": generate_min_quality_value(),
        "max_quality_value": generate_max_quality_value(),
        "is_rate_percentage": False,
        "multiplier": generate_multiplier(),
    }


def generate_empty_detail_data():
    """Return detail data with all fields empty."""
    return {
        "quality_parameter": None,
        "select_qp": False,
        "min_quality_value": "",
        "max_quality_value": "",
        "is_rate_percentage": False,
        "multiplier": "",
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_string_255():
    """Generate a string of exactly 255 characters."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters."""
    return "A" * 256


def generate_long_string(length=300):
    """Generate a string of specified length."""
    return "X" * length


def generate_special_char_value():
    """Generate a value with common special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"CQP{special}"


def generate_sql_injection_value():
    """Generate SQL injection strings to test input sanitization."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE commodity_quality; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM items --",
        "\" OR \"1\"=\"1",
    ]
    return random.choice(injections)


def generate_xss_value():
    """Generate XSS payload strings to test input sanitization."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
    ]
    return random.choice(payloads)


def generate_unicode_value():
    """Generate a value with unicode/international characters."""
    unicode_samples = [
        "CQP\u00e9",           # Latin é
        "CQP\u00fc",           # Latin ü
        "\u4e2d\u6587\u53c2\u6570",  # 中文参数
        "\u0917\u0941\u0923\u0935\u0924\u094d\u0924\u093e",  # गुणवत्ता
        "\u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e",  # качество
    ]
    return random.choice(unicode_samples)


def generate_negative_number():
    """Generate a negative number string."""
    return str(random.uniform(-100.0, -0.1))


def generate_zero_value():
    """Generate a zero value string."""
    return "0"


def generate_very_large_number():
    """Generate a very large number string."""
    return "999999999.99"


# ──────────────────────────────────────────────
# Transaction Type helpers
# ──────────────────────────────────────────────

def get_random_transaction_type():
    """Return a random Transaction Type from the known list."""
    return random.choice(TRANSACTION_TYPES)


def get_all_transaction_types():
    """Return all Transaction Type options."""
    return TRANSACTION_TYPES.copy()
