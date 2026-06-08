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
  BUG-001 (HIGH)  : No maxlength on Name input; server ACCEPTS 256+ chars (no rejection).
  BUG-002 (HIGH)  : No maxlength on Base Uom Conversion; server ACCEPTS 11+ chars.
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


# ═══════════════════════════════════════════════════════════════════════════════
#  API Batch Create — Data Pool + Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Screen structure (discovered 2026-06-02):
#   Services Master: name* (text, required, unique),
#                    uom* (FK dropdown → UOM table),
#                    base_uom* (FK dropdown → UOM table),
#                    base_uom_conversion* (text, max 10 chars),
#                    hsn_code* (FK dropdown → HSN SAC, filtered to "Services" type),
#                    status (toggle, default: true)
#   FLAT screen — no steppers, no children, no detail tables.
#
# FK Dropdown mappings (live from ERP as of 2026-06-02):
#
#   UOM options (clean/useful ones only):
#     249=KG, 250=MT, 251=QT, 252=NOS, 253=Litres,
#     501=LTR, 502=MTR, 533=SET, 534=KM
#
#   HSN SAC Code (Services type only):
#     108=995411, 122=995413, 123=995414, 124=995415, 125=996311, 126=996312
#
# Existing entries in ERP (as of 2026-06-02, 20 total):
#   Transport Service, Warehouse Service, Loading Service, Unloading Service,
#   Packing Service, Quality Testing Service, Insurance Service,
#   Weighbridge Service, Storage Service, Freight Service, Cleaning Service,
#   Fumigation Service, Grading Service, Sorting Service, Drying Service,
#   Milling Service, Processing Service, Survey Service,
#   Consultancy Service, Logistics Service
#
# This data pool provides additional service names NOT already in the system.
# ═══════════════════════════════════════════════════════════════════════════════

# ── FK ID Mappings (from live ERP) ────────────────────────────────────

UOM_ID_MAP = {
    "KG": 249,
    "MT": 250,
    "QT": 251,
    "NOS": 252,
    "Litres": 253,
    "LTR": 501,
    "MTR": 502,
    "SET": 533,
    "KM": 534,
}

HSN_SAC_SERVICES_ID_MAP = {
    "995411": 108,
    "995413": 122,
    "995414": 123,
    "995415": 124,
    "996311": 125,
    "996312": 126,
}

# ── Data Pool ─────────────────────────────────────────────────────────
# Each entry is a tuple: (name, uom_code, base_uom_code, base_uom_conversion, hsn_sac_code, status)
# uom_code and base_uom_code are string keys that map to FK IDs via UOM_ID_MAP
# hsn_sac_code is a string key that maps to FK ID via HSN_SAC_SERVICES_ID_MAP

SERVICES_MASTER_API_DATA = [
    # ── Transportation & Logistics ──────────────────────────────────────
    ("Cold Chain Transport", "KG", "KG", "1", "996312", True),
    ("Bulk Cargo Transport", "MT", "MT", "1", "996312", True),
    ("Container Transport", "NOS", "NOS", "1", "996311", True),
    ("Last Mile Delivery", "NOS", "NOS", "1", "996312", True),
    ("Interstate Transport", "MT", "MT", "1", "996311", True),
    ("Express Courier Service", "NOS", "NOS", "1", "996312", True),
    ("Tanker Transport", "Litres", "Litres", "1", "996312", True),
    ("Rail Freight Service", "MT", "MT", "1", "996311", True),

    # ── Warehousing & Storage ──────────────────────────────────────────
    ("Cold Storage Service", "KG", "KG", "1", "995411", True),
    ("Bulk Storage Service", "MT", "MT", "1", "995411", True),
    ("Warehouse Leasing", "SET", "SET", "1", "995411", True),
    ("Inventory Management Service", "NOS", "NOS", "1", "995413", True),
    ("Stock Audit Service", "NOS", "NOS", "1", "995413", True),
    ("Bonded Warehouse Service", "KG", "KG", "1", "995411", True),

    # ── Quality & Testing ──────────────────────────────────────────────
    ("Lab Testing Service", "NOS", "NOS", "1", "995413", True),
    ("Microbial Analysis Service", "NOS", "NOS", "1", "995413", True),
    ("Chemical Analysis Service", "NOS", "NOS", "1", "995413", True),
    ("Pesticide Residue Testing", "NOS", "NOS", "1", "995413", True),
    ("Shelf Life Testing", "NOS", "NOS", "1", "995413", True),
    ("Nutritional Analysis Service", "NOS", "NOS", "1", "995413", True),
    ("Sample Collection Service", "NOS", "NOS", "1", "995414", True),
    ("Third Party Inspection", "NOS", "NOS", "1", "995414", True),

    # ── Packaging & Processing ─────────────────────────────────────────
    ("Vacuum Packaging Service", "KG", "KG", "1", "995415", True),
    ("Shrink Wrapping Service", "NOS", "NOS", "1", "995415", True),
    ("Custom Packaging Service", "KG", "KG", "1", "995415", True),
    ("Labeling Service", "NOS", "NOS", "1", "995415", True),
    ("Batch Coding Service", "NOS", "NOS", "1", "995415", True),
    ("Grading & Sorting Service", "MT", "MT", "1", "995411", True),
    ("Milling Service Premium", "MT", "MT", "1", "995411", True),
    ("Dehusking Service", "MT", "MT", "1", "995411", True),

    # ── Agricultural Services ───────────────────────────────────────────
    ("Crop Spraying Service", "Litres", "Litres", "1", "996311", True),
    ("Soil Testing Service", "NOS", "NOS", "1", "995413", True),
    ("Harvesting Service", "MT", "MT", "1", "996311", True),
    ("Sowing Service", "KG", "KG", "1", "996311", True),
    ("Irrigation Management", "SET", "SET", "1", "996311", True),
    ("Organic Certification Service", "NOS", "NOS", "1", "995414", True),

    # ── Insurance & Financial ──────────────────────────────────────────
    ("Crop Insurance Service", "NOS", "NOS", "1", "995414", True),
    ("Transit Insurance Service", "NOS", "NOS", "1", "995414", True),
    ("Warehouse Insurance Service", "NOS", "NOS", "1", "995414", True),
    ("Commodity Valuation Service", "NOS", "NOS", "1", "995414", True),

    # ── Weighbridge & Measurement ──────────────────────────────────────
    ("Weighbridge Service Premium", "MT", "MT", "1", "995415", True),
    ("Volume Measurement Service", "Litres", "Litres", "1", "995415", True),
    ("Moisture Measurement Service", "NOS", "NOS", "1", "995415", True),

    # ── Cleaning & Fumigation ──────────────────────────────────────────
    ("Fumigation Service Premium", "NOS", "NOS", "1", "995411", True),
    ("Sanitization Service", "SET", "SET", "1", "995411", True),
    ("Pest Control Service", "NOS", "NOS", "1", "995411", True),
    ("Silo Cleaning Service", "NOS", "NOS", "1", "995411", True),

    # ── Professional & Consultancy ──────────────────────────────────────
    ("Agri Consultancy Service", "NOS", "NOS", "1", "996312", True),
    ("Supply Chain Consulting", "NOS", "NOS", "1", "996312", True),
    ("Regulatory Compliance Service", "NOS", "NOS", "1", "996312", True),
    ("Market Intelligence Service", "NOS", "NOS", "1", "996312", True),
    ("Export Documentation Service", "NOS", "NOS", "1", "996312", True),

    # ── Technology & Digital ────────────────────────────────────────────
    ("ERP Integration Service", "NOS", "NOS", "1", "996311", True),
    ("IoT Monitoring Service", "SET", "SET", "1", "996311", True),
    ("Data Analytics Service", "NOS", "NOS", "1", "996311", True),
    ("GPS Tracking Service", "NOS", "NOS", "1", "996311", True),
]


def build_services_master_api_payload(
    name: str,
    uom: int,
    base_uom: int,
    base_uom_conversion: str = "1",
    hsn_code: int = None,
    status: bool = True,
) -> dict:
    """
    Build a single API payload for Services Master.

    Args:
        name: Service name (e.g., "Cold Chain Transport")
        uom: FK ID for UOM dropdown (e.g., 249 for KG)
        base_uom: FK ID for Base UOM dropdown (e.g., 249 for KG)
        base_uom_conversion: Conversion factor as string (e.g., "1")
        hsn_code: FK ID for HSN SAC Code dropdown (e.g., 108 for 995411)
        status: True for Active, False for Inactive

    Returns:
        dict: API payload with attribute_name set to "Services Master"
    """
    return {
        "id": "",
        "attribute_name": "Services Master",
        "name": name,
        "uom": uom,
        "base_uom": base_uom,
        "base_uom_conversion": base_uom_conversion,
        "hsn_code": hsn_code,
        "status": status,
    }


# ── Field Validation Rules (from live ERP schema) ────────────────────
# Services Master is a flat screen — no children, no steppers.
# 6 fields: name (required), uom (FK dropdown, required),
# base_uom (FK dropdown, required), base_uom_conversion (required),
# hsn_code (FK dropdown, required), status (toggle, optional).

FIELD_VALIDATION_RULES = {
    "name": {
        "type": "text",
        "required": True,
        "max_length": 255,
        "note": "Accepts all characters (BUG-003: no input restrictions). "
                 "BUG-001: No maxlength on frontend — server rejects > 255.",
    },
    "uom": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": 9,
        "fk_source": "UOM",
        "note": "FK dropdown → UOM table. Same pool as base_uom but independent.",
    },
    "base_uom": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": 9,
        "fk_source": "UOM",
        "note": "FK dropdown → UOM table. Same pool as uom but independent.",
    },
    "base_uom_conversion": {
        "type": "text",
        "required": True,
        "max_length": 10,
        "note": "BUG-002: No maxlength on frontend — server rejects > 10 chars. "
                 "BUG-004: Accepts all input (letters, special chars, negative, zero, spaces).",
    },
    "hsn_code": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": 6,
        "fk_source": "HSN SAC (Services type only)",
        "note": "FK dropdown → HSN SAC table, filtered to 'Services' type. "
                 "6 options: 995411, 995413, 995414, 995415, 996311, 996312.",
    },
    "status": {
        "type": "toggle",
        "required": False,
        "default": True,
        "note": "Boolean toggle. True=Active, False=Inactive. Default is ON.",
    },
}

# Status toggle options (display name -> API boolean value)
STATUS_OPTIONS = {
    "Active": True,
    "Inactive": False,
}

# Name aliases for schema test compatibility
UOM_NAMES = UOM_ID_MAP
HSN_SAC_NAMES = HSN_SAC_SERVICES_ID_MAP

# Default FK IDs for batch creation (3 pools: uom, base_uom, hsn_code)
DEFAULT_SERVICES_MASTER_FK_IDS = {
    "uom": dict(UOM_ID_MAP),
    "base_uom": dict(UOM_ID_MAP),
    "hsn_code": dict(HSN_SAC_SERVICES_ID_MAP),
}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """Generate a batch of unique Services Master API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules (UOM, Customer, Supplier, etc.).

    Args:
        count: Number of payloads to generate.
        prefix: Optional prefix for service names.
        dropdown_ids: Not used (FK IDs are resolved from data pool).

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    return generate_services_master_payloads(count=count)


def generate_services_master_payloads(count: int = 10, offset: int = 0) -> list:
    """
    Generate N API payloads for Services Master.

    Resolves FK dropdown codes to live ERP IDs using the ID maps.
    Validates that all FK fields resolve before building payloads.

    Args:
        count: Number of payloads to generate
        offset: Start index in the data pool (to skip already-used entries)

    Returns:
        list[dict]: List of API payloads ready for batch_create
    """
    pool = SERVICES_MASTER_API_DATA
    payloads = []

    for i in range(count):
        idx = (offset + i) % len(pool)
        name, uom_code, base_uom_code, conversion, hsn_code_str, status = pool[idx]

        # Handle potential duplicate names when wrapping around
        if (offset + i) >= len(pool):
            wrap_count = (offset + i) // len(pool) + 1
            name = f"{name} (Batch {wrap_count})"

        # Resolve FK codes to ERP IDs
        uom_id = UOM_ID_MAP.get(uom_code)
        base_uom_id = UOM_ID_MAP.get(base_uom_code)
        hsn_id = HSN_SAC_SERVICES_ID_MAP.get(hsn_code_str)

        payloads.append(
            build_services_master_api_payload(
                name=name,
                uom=uom_id,
                base_uom=base_uom_id,
                base_uom_conversion=conversion,
                hsn_code=hsn_id,
                status=status,
            )
        )

    return payloads
