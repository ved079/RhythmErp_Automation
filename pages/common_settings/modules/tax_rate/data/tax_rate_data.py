"""
Tax Rate — Test Data Generators & Field Constants
=================================================
All test data for Tax Rate automation.
Module: 6 header fields + nested sub-table (HSN Number + Tax Rate).
Complexity: HIGHEST in Common Settings (nested editable sub-table).
"""

import random
import string
from datetime import datetime, timedelta


# ─── Page URL ────────────────────────────────────────────────────────────────
PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Rate"


# ─── Dropdown Options ───────────────────────────────────────────────────────
# Tax Type — only 1 option
TAX_TYPE_OPTIONS = ["GST"]

# Tax Authority — 6 options (dynamic, retrieve live)
TAX_AUTHORITY_OPTIONS = [
    "GST",
    "Test206",
    "ggf",
    "Enterprises",
    "Test147",
    "SQL_INJECT_TEST",
]

# HSN Number — 23+ options from HSN SAC master (dynamic, retrieve live)
HSN_NUMBER_OPTIONS = [
    "997212",
    "10059011",
    "12024200",
    "7133100",
    "7136000",
    "11061000",
    "10063000",
    "10059000",
    "10019900",
    "9103000",
    "7132010",
    "7132000",
    "12010000",
    "998811",
]


# ─── Field Name Constants ────────────────────────────────────────────────────
FIELD_TAX_RATE_NAME = "Tax Rate Name"
FIELD_TAX_TYPE = "Tax Type"
FIELD_TAX_AUTHORITY = "Tax Authority"
FIELD_FROM_DATE = "From Date"
FIELD_TO_DATE = "To Date"
FIELD_REVISION_STATUS = "Revision Status"
FIELD_HSN_NUMBER = "HSN Number"
FIELD_TAX_RATE = "Tax Rate"


# ─── Date Defaults ───────────────────────────────────────────────────────────
# From Date auto-fills with current date (DD/MM/YYYY format)
# To Date defaults to 30/12/2099 on server when left empty
DEFAULT_TO_DATE_DISPLAY = "30/12/2099"
DEFAULT_TO_DATE_ISO = "2099-12-30T18:30:00Z"

# Revision Status common values
REVISION_STATUSES = ["effective", "Effective", "draft", "Draft"]


# ─── SweetAlert2 Messages ───────────────────────────────────────────────────
VALIDATION_FAILED_TITLE = "Validation Failed"
VALIDATION_FAILED_CONTENT = "Please correct the highlighted fields"
# Note: No success SweetAlert2 — form closes silently on success (TR-03)
# Note: Same generic "Validation Failed" for all errors — empty, duplicate, etc.


# ─── Table Column Constants ─────────────────────────────────────────────────
COL_VIEW = "mat-column-view"
COL_EDIT = "mat-column-edit"
COL_FOLDER = "mat-column-folder"          # Version button (unique to Tax Rate)
COL_ARCHIVE = "mat-column-archive"
COL_TAX_RATE_NAME = "mat-column-tax_rate_name"
COL_TAX_TYPE = "mat-column-tax_type_ref_id"
COL_TAX_AUTHORITY = "mat-column-tax_authority_ref_id"
COL_FROM_DATE = "mat-column-from_date"
COL_TO_DATE = "mat-column-to_date"
COL_REVISION_STATUS = "mat-column-revision_status"


# ─── Sub-Table Column Constants ─────────────────────────────────────────────
# Inside the "Define Tax Rate Details" tab
SUB_COL_ACTION = "ACTION"
SUB_COL_HSN_NUMBER = "HSN NUMBER"
SUB_COL_TAX_RATE = "TAX RATE"
SUB_TABLE_ROWS_PER_PAGE = 5


# ─── Popup Text ─────────────────────────────────────────────────────────────
POPUP_TITLE = "Tax Rate"
HISTORY_POPUP_TITLE = "Tax Rate History"
VERSION_BUTTON_TEXT = "Create Version"     # Version form uses this instead of Submit/Update


# ─── Bug Registry ────────────────────────────────────────────────────────────
BUG_REGISTRY = {
    "TR-01": {
        "severity": "HIGH",
        "title": "SQL injection accepted in Tax Rate Name",
        "description": "Input like 'DROP TABLE tax;--' is accepted and stored as-is.",
        "category": "Security",
    },
    "TR-02": {
        "severity": "MEDIUM",
        "title": "Edit button permanently disabled — use Version instead",
        "description": "All records show disabled Edit button. Version button (folder icon) opens editable form with 'Create Version' button.",
        "category": "Functionality",
    },
    "TR-03": {
        "severity": "LOW",
        "title": "No success SweetAlert2 on create/version",
        "description": "Form closes silently on success. No success popup visible.",
        "category": "UI/UX",
    },
    "TR-04": {
        "severity": "INFO",
        "title": "Date fields have name=null",
        "description": "From Date and To Date inputs have no name attribute. Must locate via mat-label traversal.",
        "category": "Technical",
    },
    "TR-05": {
        "severity": "INFO",
        "title": "HSN Number has duplicate entries",
        "description": "HSN '7133100' appears twice in dropdown (inherited from HSN SAC master data).",
        "category": "Data Integrity",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Test Data Generators
# ═══════════════════════════════════════════════════════════════════════════════

def generate_tax_rate_name() -> str:
    """Generate a random Tax Rate Name (e.g. 'AUTOTEST_RATE5847')."""
    return f"AUTOTEST_RATE{random.randint(1000, 9999)}"


def generate_revision_status() -> str:
    """Generate a random revision status."""
    return random.choice(REVISION_STATUSES)


def generate_tax_rate_value() -> float:
    """Generate a random tax rate percentage (1-28)."""
    return round(random.uniform(1, 28), 2)


def generate_valid_tax_rate_data(override=None) -> dict:
    """
    Generate a complete dict for a valid Tax Rate record (header fields).
    
    Args:
        override: Optional dict to override specific fields.
    
    Returns:
        dict with keys: tax_rate_name, tax_type, tax_authority, from_date, to_date, revision_status
    """
    today = datetime.now()
    data = {
        "tax_rate_name": generate_tax_rate_name(),
        "tax_type": "GST",
        "tax_authority": random.choice(TAX_AUTHORITY_OPTIONS),
        "from_date": today.strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": generate_revision_status(),
    }
    if override:
        data.update(override)
    return data


def generate_sub_table_row(override=None) -> dict:
    """
    Generate a single sub-table row (HSN Number + Tax Rate).
    
    Args:
        override: Optional dict to override specific fields.
    
    Returns:
        dict with keys: hsn_number, tax_rate
    """
    data = {
        "hsn_number": random.choice(HSN_NUMBER_OPTIONS),
        "tax_rate": generate_tax_rate_value(),
    }
    if override:
        data.update(override)
    return data


def generate_create_test_data() -> dict:
    """Generate data specifically for CREATE tests (header + 1 sub-table row)."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [generate_sub_table_row()],
    }


def generate_create_multi_row_data(row_count=3) -> dict:
    """Generate data with multiple sub-table rows."""
    rows = [generate_sub_table_row() for _ in range(row_count)]
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": rows,
    }


def generate_version_test_data(override=None) -> dict:
    """Generate data for Version tests (pre-filled, change one field)."""
    data = generate_valid_tax_rate_data(override=override)
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# Edge-Case / Negative Test Data
# ═══════════════════════════════════════════════════════════════════════════════

def empty_fields_data() -> dict:
    """All header fields empty — triggers Validation Failed."""
    return {
        "tax_rate_name": "",
        "tax_type": "",
        "tax_authority": "",
        "from_date": "",
        "to_date": "",
        "revision_status": "",
    }


def missing_name_data() -> dict:
    """Tax Rate Name empty, rest filled."""
    return {
        "tax_rate_name": "",
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def missing_tax_type_data() -> dict:
    """Tax Type empty, rest filled."""
    return {
        "tax_rate_name": generate_tax_rate_name(),
        "tax_type": "",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def missing_tax_authority_data() -> dict:
    """Tax Authority empty, rest filled."""
    return {
        "tax_rate_name": generate_tax_rate_name(),
        "tax_type": "GST",
        "tax_authority": "",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def missing_revision_status_data() -> dict:
    """Revision Status empty, rest filled."""
    return {
        "tax_rate_name": generate_tax_rate_name(),
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "",
    }


def sql_injection_name_data() -> dict:
    """SQL injection in Tax Rate Name."""
    return {
        "tax_rate_name": "DROP TABLE tax;--",
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def special_chars_name_data() -> dict:
    """Special characters in Tax Rate Name."""
    return {
        "tax_rate_name": "TEST@#$%^&*()",
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def very_long_name_data() -> dict:
    """256+ character Tax Rate Name."""
    return {
        "tax_rate_name": "A" * 300,
        "tax_type": "GST",
        "tax_authority": "GST",
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": "effective",
    }


def negative_tax_rate_data() -> dict:
    """Negative tax rate value in sub-table."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [{"hsn_number": "997212", "tax_rate": -5.0}],
    }


def zero_tax_rate_data() -> dict:
    """Zero tax rate value in sub-table."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [{"hsn_number": "997212", "tax_rate": 0}],
    }


def very_large_tax_rate_data() -> dict:
    """Very large tax rate value (999999)."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [{"hsn_number": "997212", "tax_rate": 999999}],
    }


def empty_sub_table_data() -> dict:
    """Header filled but sub-table empty (no HSN/Tax Rate rows)."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [],
    }


def unselected_hsn_data() -> dict:
    """Sub-table row with HSN Number left as 'Select HSN Number'."""
    return {
        "header": generate_valid_tax_rate_data(),
        "sub_table_rows": [{"hsn_number": "", "tax_rate": 18.0}],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# API Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Converts the existing UI data format into the JSON payload
# that POST /core/dynamic-screen-wrapper/ expects.
#
# TAX RATE SCREEN STRUCTURE (from live API):
#   {
#     "id": "",
#     "attribute_name": "Tax Rate",
#     "details": [],
#     "children": [
#       {
#         "stepper_name": "Define Tax Rate Details",
#         "is_stepper": true,
#         "details": [
#           {
#             "hsn_sac_ref_id": 1,     // FK: HSN SAC entry
#             "tax_rate": 18.0          // percentage
#           }
#         ],
#         "children": []
#       }
#     ],
#     "tax_rate_name": "GST Rate Schedule 2026-A",
#     "tax_type_ref_id": 1,          // FK: GST
#     "tax_authority_ref_id": 1,     // FK: Tax Authority
#     "from_date": "2026-06-01T00:00:00Z",
#     "to_date": "2099-12-30T18:30:00Z",
#     "revision_status": "effective"
#   }
#
# FIELD KEY MAPPING (verified from live API):
#
#   Root-level:
#     tax_rate_name       -> tax_rate_name (string)
#     tax_type            -> tax_type_ref_id (FK)
#     tax_authority       -> tax_authority_ref_id (FK)
#     from_date           -> from_date (ISO datetime string)
#     to_date             -> to_date (ISO datetime string)
#     revision_status     -> revision_status (string: "effective"/"draft")
#     details             -> details (empty array [] at root level)
#     children            -> children (array with stepper)
#
#   NOTE: NO "status" field at top level.
#
#   Sub-table (in child[0].details[]):
#     hsn_number          -> hsn_sac_ref_id (FK)
#     tax_rate            -> tax_rate (float, percentage)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Dropdown FK ID pools (placeholder — to be filled from discovery) ────────
TAX_TYPE_IDS = {"GST": None}         # Only one option
TAX_AUTHORITY_IDS = {}                # To be filled from discovery
HSN_SAC_IDS = {}                      # To be filled from discovery

# ─── Realistic Indian GST slab percentages ────────────────────────────────────
GST_SLAB_RATES = [0.25, 1, 1.5, 3, 5, 6, 7.5, 12, 15, 18, 20, 25, 28]

# ─── Realistic HSN codes (Indian commodity classifications) ──────────────────
# Maps HSN code -> description for documentation; IDs must come from discovery
REALISTIC_HSN_CODES = {
    "0101":   "Live horses, asses, mules",
    "0201":   "Meat of bovine animals, fresh",
    "0302":   "Fish, fresh or chilled",
    "0401":   "Milk and cream, not concentrated",
    "0701":   "Potatoes, fresh or chilled",
    "0801":   "Coconuts, Brazil nuts, cashew nuts",
    "0901":   "Coffee, whether or not roasted",
    "1001":   "Wheat and meslin",
    "1005":   "Maize (corn)",
    "1006":   "Rice",
    "1101":   "Wheat or meslin flour",
    "1201":   "Soya beans",
    "1511":   "Palm oil and its fractions",
    "1701":   "Cane or beet sugar",
    "2106":   "Food preparations n.e.c.",
    "2201":   "Waters, incl. mineral & aerated",
    "2401":   "Unmanufactured tobacco",
    "2523":   "Portland cement",
    "2701":   "Coal; briquettes",
    "2710":   "Petroleum oils & preparations",
    "3004":   "Medicaments, packaged",
    "3208":   "Paints and varnishes",
    "3901":   "Polymers of ethylene",
    "4011":   "New pneumatic tyres of rubber",
    "4801":   "Newsprint in rolls or sheets",
    "4819":   "Cartons, boxes, bags of paper",
    "5201":   "Cotton, not carded or combed",
    "6110":   "Sweaters, pullovers, knitwear",
    "6203":   "Men's suits, trousers, etc.",
    "7005":   "Float glass and surface ground",
    "7108":   "Gold (incl. gold plated)",
    "7208":   "Flat-rolled products of iron/steel",
    "7308":   "Structures & parts of iron/steel",
    "8415":   "Air conditioning machines",
    "8471":   "Automatic data processing machines",
    "8504":   "Electrical transformers",
    "8517":   "Telephone sets; smartphones",
    "8703":   "Motor cars and vehicles",
    "8708":   "Parts and accessories of vehicles",
    "9031":   "Measuring/checking instruments",
    "9401":   "Seats (chairs, sofas)",
    "9403":   "Furniture (desks, cabinets)",
}

# ─── Realistic Tax Rate Name patterns (Indian GST context) ───────────────────
TAX_RATE_NAME_PREFIXES = [
    "GST Schedule",
    "GST Rate Schedule",
    "Revised GST Rate",
    "GST Tariff",
    "Commodity Tax Structure",
    "GST Rate Card",
    "Indian GST Rate",
    "GST Applicable Rate",
    "Tax Rate Configuration",
    "GST Commodity Schedule",
]

TAX_RATE_NAME_QUALIFIERS = [
    "Q1", "Q2", "Q3", "Q4",
    "FY 2026", "FY 2027",
    "A", "B", "C", "D",
    "Phase 1", "Phase 2",
    "Effective", "Amended",
    "Standard", "Revised",
    "Notification", "Circular",
]

TAX_RATE_NAME_SUFFIXES = [
    "2026", "2027",
    "April", "October",
    "v1", "v2",
    "Part I", "Part II",
]


# ─── Default FK IDs (placeholder — override after discovery) ─────────────────
DEFAULT_TAX_RATE_FK_IDS = {
    "tax_type_ref_id": 1,            # GST (only option)
    "tax_authority_ref_id": None,    # To be filled from discovery
}


def generate_realistic_tax_rate_name(prefix=None) -> str:
    """Generate a realistic Indian Tax Rate Name.

    Examples:
      - "GST Schedule Q1 2026"
      - "Revised GST Rate A"
      - "Commodity Tax Structure B FY 2027"
    """
    if prefix:
        return f"{prefix} {random.randint(1000, 9999)}"

    pat = random.choice([
        lambda: f"{random.choice(TAX_RATE_NAME_PREFIXES)} {random.choice(TAX_RATE_NAME_QUALIFIERS)} {random.choice(TAX_RATE_NAME_SUFFIXES)}",
        lambda: f"{random.choice(TAX_RATE_NAME_PREFIXES)} {random.choice(TAX_RATE_NAME_QUALIFIERS)}",
        lambda: f"{random.choice(TAX_RATE_NAME_PREFIXES)} {random.choice(TAX_RATE_NAME_SUFFIXES)}",
    ])
    return pat()


def generate_from_date_iso() -> str:
    """Generate an ISO datetime for from_date (today or recent past)."""
    today = datetime.now()
    # Randomly pick today or up to 30 days ago
    offset = random.randint(0, 30)
    from_dt = today - timedelta(days=offset)
    return from_dt.strftime("%Y-%m-%dT00:00:00Z")


def generate_realistic_gst_slab() -> float:
    """Pick a random Indian GST slab rate."""
    return float(random.choice(GST_SLAB_RATES))


def generate_random_hsn_code() -> str:
    """Pick a random realistic HSN code."""
    return random.choice(list(REALISTIC_HSN_CODES.keys()))


def generate_sub_table_detail_rows(
    row_count: int = None,
    hsn_sac_ids: dict = None,
) -> list:
    """Generate detail rows for the Tax Rate sub-table.

    Args:
        row_count: Number of rows (1-5, random if None).
        hsn_sac_ids: Dict mapping HSN code string -> ref_id int.
                     If None or empty, uses placeholder ID of 1.

    Returns:
        List of dicts with hsn_sac_ref_id and tax_rate.
    """
    if row_count is None:
        row_count = random.randint(1, 4)
    row_count = max(1, min(row_count, 5))

    details = []
    used_hsn = set()

    for _ in range(row_count):
        # Pick a unique HSN code for each row
        hsn_code = generate_random_hsn_code()
        attempts = 0
        while hsn_code in used_hsn and attempts < 20:
            hsn_code = generate_random_hsn_code()
            attempts += 1
        used_hsn.add(hsn_code)

        # Look up the ref_id, fallback to 1 if not discovered yet
        if hsn_sac_ids and hsn_code in hsn_sac_ids:
            hsn_ref_id = hsn_sac_ids[hsn_code]
        else:
            hsn_ref_id = 1  # placeholder

        details.append({
            "hsn_sac_ref_id": hsn_ref_id,
            "tax_rate": generate_realistic_gst_slab(),
        })

    return details


def build_tax_rate_api_payload(
    data: dict = None,
    dropdown_ids: dict = None,
) -> dict:
    """Build the complete Tax Rate API payload from data + FK IDs.

    Args:
        data: Dict from generate_valid_tax_rate_data() or generate_create_test_data(),
              or None for random.
        dropdown_ids: Dict of FK IDs. Missing keys fall back to DEFAULT_TAX_RATE_FK_IDS.
                     Expected keys:
                       - tax_type_ref_id (int)
                       - tax_authority_ref_id (int)
                       - hsn_sac_ids (dict: HSN code -> ref_id)

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    ids = {**DEFAULT_TAX_RATE_FK_IDS, **(dropdown_ids or {})}

    if data is None:
        data = generate_create_test_data()

    # Handle both flat and nested data formats
    header = data.get("header", data) if isinstance(data, dict) and "header" in data else data
    sub_rows = data.get("sub_table_rows", [generate_sub_table_row()]) if "sub_table_rows" in data else [generate_sub_table_row()]

    # Extract HSN SAC IDs from dropdown_ids if provided
    hsn_sac_ids = ids.get("hsn_sac_ids", HSN_SAC_IDS)

    # Build sub-table detail rows
    detail_rows = []
    for row in sub_rows:
        hsn_code = row.get("hsn_number", "")
        if hsn_sac_ids and hsn_code in hsn_sac_ids:
            hsn_ref_id = hsn_sac_ids[hsn_code]
        else:
            hsn_ref_id = 1  # placeholder

        tax_rate_val = row.get("tax_rate", 18.0)
        try:
            tax_rate_val = float(tax_rate_val)
        except (ValueError, TypeError):
            tax_rate_val = 18.0

        detail_rows.append({
            "hsn_sac_ref_id": hsn_ref_id,
            "tax_rate": tax_rate_val,
        })

    # If no detail rows were built, add at least one default
    if not detail_rows:
        detail_rows = generate_sub_table_detail_rows(1, hsn_sac_ids)

    # Build from_date
    from_date_str = header.get("from_date", "")
    if from_date_str:
        # Convert DD/MM/YYYY to ISO datetime
        try:
            from_dt = datetime.strptime(from_date_str, "%d/%m/%Y")
            from_date_iso = from_dt.strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            from_date_iso = generate_from_date_iso()
    else:
        from_date_iso = generate_from_date_iso()

    # Build to_date (default: 2099-12-30T18:30:00Z)
    to_date_str = header.get("to_date", "")
    if to_date_str:
        try:
            to_dt = datetime.strptime(to_date_str, "%d/%m/%Y")
            to_date_iso = to_dt.strftime("%Y-%m-%dT18:30:00Z")
        except ValueError:
            to_date_iso = DEFAULT_TO_DATE_ISO
    else:
        to_date_iso = DEFAULT_TO_DATE_ISO

    # Revision status
    revision_status = header.get("revision_status", "effective") or "effective"

    # Assemble payload
    payload = {
        "id": "",
        "attribute_name": "Tax Rate",
        "details": [],

        # Children array with sub-table stepper
        "children": [
            {
                "stepper_name": "Define Tax Rate Details",
                "is_stepper": True,
                "details": detail_rows,
                "children": [],
            }
        ],

        # Root-level fields
        "tax_rate_name": header.get("tax_rate_name", generate_realistic_tax_rate_name()),
        "tax_type_ref_id": ids.get("tax_type_ref_id", 1),
        "tax_authority_ref_id": ids.get("tax_authority_ref_id"),
        "from_date": from_date_iso,
        "to_date": to_date_iso,
        "revision_status": revision_status,
    }

    return payload


def generate_tax_rate_api_payload(
    name_prefix=None,
    dropdown_ids: dict = None,
) -> dict:
    """One-shot: generate a complete Tax Rate API payload with random data.

    Automatically randomizes:
      - Tax Rate Name (realistic Indian GST naming)
      - From Date (today or recent)
      - Revision Status (effective/draft)
      - HSN codes with GST slab rates (5, 12, 18, 28, etc.)
      - Number of detail rows (1-4)

    Args:
        name_prefix: If provided, uses old-style prefix+random naming.
        dropdown_ids: Override specific FK IDs.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    # Generate header data
    header_data = {
        "tax_rate_name": generate_realistic_tax_rate_name(name_prefix),
        "tax_type": "GST",
        "tax_authority": random.choice(TAX_AUTHORITY_OPTIONS),
        "from_date": datetime.now().strftime("%d/%m/%Y"),
        "to_date": "",
        "revision_status": random.choice(["effective", "draft"]),
    }

    # Generate 1-4 sub-table rows with realistic GST slabs
    row_count = random.randint(1, 4)
    sub_rows = []
    used_hsn = set()
    for _ in range(row_count):
        hsn = random.choice(HSN_NUMBER_OPTIONS)
        attempts = 0
        while hsn in used_hsn and attempts < 20:
            hsn = random.choice(HSN_NUMBER_OPTIONS)
            attempts += 1
        used_hsn.add(hsn)
        sub_rows.append({
            "hsn_number": hsn,
            "tax_rate": generate_realistic_gst_slab(),
        })

    data = {
        "header": header_data,
        "sub_table_rows": sub_rows,
    }

    return build_tax_rate_api_payload(data, dropdown_ids)


def generate_tax_rate_api_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """Generate multiple unique Tax Rate API payloads for batch creation.

    Args:
        count: Number of payloads to generate (default 20).
        prefix: Optional name prefix for all payloads.
        dropdown_ids: Override specific FK IDs for all payloads.

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    payloads = []
    for i in range(count):
        payloads.append(
            generate_tax_rate_api_payload(prefix, dropdown_ids)
        )
    return payloads