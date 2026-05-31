"""
cbr_data.py - Commodity Base Rate test data generators
Screen: Commodity Settings > Commodity Base Rate

NOTE: Item Name and UOM options are ERP-dependent and may vary.
      The page object uses a "first available" fallback when
      exact option text is not found, so tests remain robust
      even if dropdown options change.
"""

import random
from datetime import datetime, timedelta


# ─── Date Format ─────────────────────────────────────────────────────────────
DATE_FORMAT = "%d/%m/%Y"
DEFAULT_TO_DATE = "30/12/2099"


# ─── Valid Data Generators ───────────────────────────────────────────────────

def generate_from_date(offset_days=0):
    """Generate From Date string. Default: today + offset."""
    dt = datetime.now() + timedelta(days=offset_days)
    return dt.strftime(DATE_FORMAT)


def generate_to_date(offset_days=0):
    """Generate To Date string. Default: today + offset."""
    dt = datetime.now() + timedelta(days=offset_days)
    return dt.strftime(DATE_FORMAT)


def generate_future_from_date(days_ahead=30):
    """Generate a future From Date for version creation."""
    return generate_from_date(offset_days=days_ahead)


def generate_valid_cbr_data(pricing_type="Common", location="Jafrabad",
                            item_name=None, item_rate="1500", uom=None):
    """Generate valid CBR data for Create form.
    
    item_name and uom default to None, which tells the page object
    to select the FIRST AVAILABLE option from the dropdown.
    This makes tests resilient to ERP data changes.
    """
    return {
        "pricing_type": pricing_type,
        "from_date": generate_from_date(),
        "to_date": DEFAULT_TO_DATE,
        "location": location,
        "item_name": item_name,  # None = select first available
        "item_rate": item_rate,
        "uom": uom,  # None = select first available
    }


def generate_valid_common_record():
    """Generate valid Common pricing type record.
    Uses first available Item Name and UOM from dropdowns.
    """
    rate = str(random.randint(1000, 5000))
    return generate_valid_cbr_data(
        pricing_type="Common",
        location="Jafrabad",
        item_name=None,  # Will pick first available option
        item_rate=rate,
        uom=None,  # Will pick first available option
    )


def generate_valid_supplier_record():
    """Generate valid Supplier pricing type record.
    Uses first available Item Name and UOM from dropdowns.
    """
    rate = str(random.randint(1000, 5000))
    return generate_valid_cbr_data(
        pricing_type="Supplier",
        location="Akola",
        item_name=None,  # Will pick first available option
        item_rate=rate,
        uom=None,  # Will pick first available option
    )


def generate_multi_row_record():
    """Generate record with multiple grid rows.
    Uses first available Item Name and UOM from dropdowns.
    """
    return {
        "pricing_type": "Common",
        "from_date": generate_from_date(),
        "to_date": DEFAULT_TO_DATE,
        "location": "Jafrabad",
        "grid_rows": [
            {"item_name": None, "item_rate": str(random.randint(1000, 3000)), "uom": None},
            {"item_name": None, "item_rate": str(random.randint(2000, 4000)), "uom": None},
            {"item_name": None, "item_rate": str(random.randint(3000, 5000)), "uom": None},
        ],
    }


# ─── Validation Test Data ────────────────────────────────────────────────────

def generate_empty_field_data():
    """Return data with all fields empty for mandatory field validation."""
    return {
        "pricing_type": "",
        "from_date": "",
        "to_date": "",
        "location": "",
        "item_name": "",
        "item_rate": "",
        "uom": "",
    }


def generate_negative_rate_data():
    """Generate data with negative Item Rate. BUG-001.
    Uses first available Item Name and UOM.
    """
    return generate_valid_cbr_data(item_rate="-100")


def generate_special_chars_rate_data():
    """Generate data with special chars in Item Rate. BUG-001.
    Uses first available Item Name and UOM.
    """
    return generate_valid_cbr_data(item_rate="abc!@#")


def generate_zero_rate_data():
    """Generate data with zero Item Rate. BUG-002.
    Uses first available Item Name and UOM.
    """
    return generate_valid_cbr_data(item_rate="0")


def generate_custom_to_date_data(to_date="31/12/2026"):
    """Generate data with a custom To Date (not the default). BUG-004.
    Uses first available Item Name and UOM.
    """
    return generate_valid_cbr_data(
        item_rate=str(random.randint(1000, 3000)),
    ) | {"to_date": to_date}


# ─── Edit Data ───────────────────────────────────────────────────────────────

def generate_edit_data(new_rate=None):
    """Generate data for editing a record."""
    if new_rate is None:
        new_rate = str(random.randint(2000, 6000))
    return {"item_rate": new_rate}


# ─── Bug IDs ─────────────────────────────────────────────────────────────────
BUG_001 = "BUG-001: Item Rate accepts non-numeric input (negative/special chars)"
BUG_002 = "BUG-002: Item Rate accepts zero value"
BUG_003 = "BUG-003: Listing shows raw ISO timestamps instead of formatted dates"
BUG_004 = "BUG-004: To Date overridden to 30/12/2099 on submit, ignoring user selection"
BUG_005 = "BUG-005: Edit button disabled for newly created records"
BUG_006 = "BUG-006: Version creation fails with same From Date, generic error"
