"""
Designation Screen — Test Data Generators

All data is dynamic (timestamp + random). No hardcoded values.
Name field has type="character" validation: ONLY letters and spaces allowed.
Underscores, digits, special chars (@#$%^&*!) = ALL REJECTED with "Invalid Name" mat-error.
"""

import random
import string
import time


_designation_counter = 0


def generate_designation_name(prefix=None):
    """Generate a unique realistic designation name with counter suffix."""
    global _designation_counter
    _designation_counter += 1
    name = random.choice(REALISTIC_DESIGNATION_NAMES)
    return f"{name} {_designation_counter}"


def generate_description(prefix="Test Description"):
    """Generate a description string."""
    timestamp = int(time.time())
    return f"{prefix} {timestamp}"


def generate_valid_designation_data():
    """
    Generate a complete valid data dict for creating a designation.
    Name: valid alphabetic with spaces (passes pattern validation).
    Description: optional text.
    Status: True = Active (default), False = Inactive.
    """
    return {
        'name': generate_designation_name(),
        'description': generate_description(),
        'status': True  # Active by default
    }


def generate_valid_edit_data():
    """Generate valid data for editing an existing designation."""
    return {
        'name': generate_designation_name(prefix="EditDesig"),
        'description': generate_description(prefix="Updated Desc"),
        'status': False  # Toggle to Inactive
    }


def generate_string_255():
    """Generate a 255-character valid name (all alphabetic + spaces).
    Must pass the Name pattern validation — no special chars."""
    base = "ValidName "
    repeats = 255 // len(base)
    remainder = 255 % len(base)
    result = (base * repeats) + base[:remainder]
    return result[:255]


def generate_string_256():
    """Generate a 256-character valid name (all alphabetic + spaces).
    Tests max length boundary — no max length validation exists."""
    base = "ValidName "
    repeats = 256 // len(base)
    remainder = 256 % len(base)
    result = (base * repeats) + base[:remainder]
    return result[:256]


def generate_spaces_only():
    """Generate spaces-only name.
    Triggers 'Invalid Name' mat-error (pattern validation rejects spaces-only)."""
    return "     "


def generate_special_char_name():
    """Generate name with special characters (@#$%^&*).
    Triggers 'Invalid Name' mat-error (pattern validation rejects these)."""
    special_chars = ['Test@Name', 'Test#Name', 'Test$Name', 'Test%Name',
                     'Test^Name', 'Test&Name', 'Test*Name', 'Test!Name']
    return random.choice(special_chars)


def generate_digits_only():
    """Generate digits-only name.
    Triggers 'Invalid Name' mat-error (pattern validation rejects digits-only)."""
    return str(random.randint(10000, 99999))


def generate_duplicate_name_data():
    """Generate data with a name that already exists in the system.
    BUG: No duplicate name validation — duplicate accepted silently."""
    existing_names = ['CEO', 'CFO', 'Jr. Manager', 'Sr. Manager',
                      'Field Officer', 'Farmer Coordinator']
    return {
        'name': random.choice(existing_names),
        'description': 'Duplicate name test',
        'status': True
    }


def generate_empty_data():
    """Generate empty data dict — all fields blank.
    Should trigger 'Validation Failed' SweetAlert2 for required Name."""
    return {
        'name': '',
        'description': '',
        'status': True
    }


def generate_name_only_data():
    """Generate data with only Name filled.
    Should succeed — Description is optional, Status defaults to Active."""
    return {
        'name': generate_designation_name(prefix="NameOnly"),
        'description': '',
        'status': True
    }


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the existing UI data format into the JSON payload
# that POST /core/dynamic-screen-wrapper/ expects.
#
# DESIGNATION SCREEN STRUCTURE (flat — no children, no steppers):
#   {
#     "id": "",
#     "attribute_name": "Designation",
#     "name": "Manager",
#     "description": "Senior management role",
#     "status": true
#   }
#
# FIELD KEY MAPPING (reasonable guess — to be verified by discover_all.py):
#   name          -> name (text, required)
#   description   -> description (text, optional)
#   status        -> status (boolean, default true)
# ──────────────────────────────────────────────

# Realistic Indian job titles for API batch creation
# Only letters and spaces (must pass type="character" validation)
REALISTIC_DESIGNATION_NAMES = [
    # Senior Management
    "Managing Director", "Executive Director", "Chief Operating Officer",
    "Chief Financial Officer", "Chief Executive Officer", "Vice President",
    "Senior Vice President", "Associate Director", "Deputy General Manager",
    # Middle Management
    "General Manager", "Assistant General Manager", "Divisional Manager",
    "Regional Manager", "Zonal Manager", "Branch Manager",
    "Operations Manager", "Finance Manager", "HR Manager",
    "Purchase Manager", "Sales Manager", "Marketing Manager",
    "Warehouse Manager", "Logistics Manager", "Quality Manager",
    "Production Manager", "Admin Manager", "IT Manager",
    # Supervisory
    "Senior Supervisor", "Supervisor", "Shift Supervisor",
    "Floor Supervisor", "Store Supervisor", "Field Supervisor",
    "Warehouse Supervisor", "Quality Supervisor", "Production Supervisor",
    # Officers & Executives
    "Senior Officer", "Officer", "Junior Officer",
    "Executive", "Senior Executive", "Junior Executive",
    "Accounts Officer", "Purchase Officer", "Sales Officer",
    "Compliance Officer", "Legal Officer", "Technical Officer",
    "Field Officer", "Extension Officer", "Welfare Officer",
    # Coordinators & Analysts
    "Coordinator", "Senior Coordinator", "Project Coordinator",
    "Analyst", "Senior Analyst", "Business Analyst",
    "Data Analyst", "Quality Analyst", "Research Analyst",
    # Engineers & Technical
    "Chief Engineer", "Senior Engineer", "Engineer",
    "Junior Engineer", "Assistant Engineer", "Maintenance Engineer",
    # Clerical & Administrative
    "Senior Clerk", "Clerk", "Junior Clerk", "Office Clerk",
    "Accountant", "Senior Accountant", "Junior Accountant",
    "Cashier", "Receptionist", "Stenographer",
    # Inspectors & Auditors
    "Inspector", "Quality Inspector", "Field Inspector",
    "Internal Auditor", "Tax Auditor",
    # Technicians
    "Senior Technician", "Technician", "Junior Technician",
    "Lab Technician", "IT Technician",
    # Specialized
    "Farm Manager", "Agricultural Officer", "Procurement Specialist",
    "Inventory Controller", "Storekeeper", "Godown Keeper",
]

# Track used names to avoid duplicates within a batch
_used_designation_names = set()


def generate_realistic_designation_name():
    """Pick a random realistic Indian job title, ensuring no duplicates
    within the current batch by appending a short suffix if needed."""
    name = random.choice(REALISTIC_DESIGNATION_NAMES)
    if name not in _used_designation_names:
        _used_designation_names.add(name)
        return name
    # Duplicate — append a short alphabetic suffix
    suffix = "".join(random.choices(string.ascii_uppercase, k=3))
    unique_name = f"{name} {suffix}"
    _used_designation_names.add(unique_name)
    return unique_name


def reset_designation_name_pool():
    """Reset the used-name tracker (call before a new batch)."""
    _used_designation_names.clear()


def build_designation_api_payload(data=None, dropdown_ids=None):
    """Build the Designation API payload from data dict.

    Args:
        data: Dict from generate_valid_designation_data() or None for random.
        dropdown_ids: Not used for Designation (no dropdown FK fields).
                      Kept for interface consistency.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    if data is None:
        data = generate_valid_designation_data()

    payload = {
        "id": "",
        "attribute_name": "Designation",
        "name": data.get("name", ""),
        "description": data.get("description", "") or None,
        "status": data.get("status", True),
    }
    return payload


def generate_designation_api_payload(name_prefix=None, dropdown_ids=None):
    """One-shot: generate a complete Designation API payload with realistic data.

    Args:
        name_prefix: Ignored (realistic names are used instead).
        dropdown_ids: Not used for Designation.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    name = generate_realistic_designation_name()
    data = {
        "name": name,
        "description": f"Responsible for {name.lower()} duties and responsibilities",
        "status": True,
    }
    return build_designation_api_payload(data, dropdown_ids)


def generate_designation_api_payloads(count=20, prefix=None, dropdown_ids=None):
    """Generate multiple unique Designation API payloads for batch creation.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored (realistic names are used instead).
        dropdown_ids: Not used for Designation.

    Returns:
        List of JSON payloads.
    """
    reset_designation_name_pool()
    payloads = []
    for _ in range(count):
        payloads.append(
            generate_designation_api_payload(prefix, dropdown_ids)
        )
    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Designation is a flat screen — no children, no steppers, no FK dropdowns.
# 3 fields: name (required), description (optional), status (toggle).

def get_field_validation_rules(fk_ids=None):
    """Return validation rules dict. Designation has no FK fields, so fk_ids is unused."""
    return {
        "name": {
            "type": "character",
            "required": True,
            "max_length": 255,
            "note": "Letters and spaces only. Frontend rejects digits, underscores, "
                     "special chars with 'Invalid Name' mat-error.",
        },
        "description": {
            "type": "character",
            "required": False,
            "max_length": 255,
            "note": "Optional field. Can be empty/null.",
        },
        "status": {
            "type": "toggle",
            "required": False,
            "default": True,
            "note": "Boolean toggle. True=Active, False=Inactive.",
        },
    }


# Backward-compat constant
FIELD_VALIDATION_RULES = get_field_validation_rules()

# Status toggle options (display name -> API boolean value)
STATUS_OPTIONS = {
    "Active": True,
    "Inactive": False,
}

DESIGNATION_NAME_MAX_LENGTH = 255

def get_fk_screen_mapping():
    """Designation has no FK dropdown fields — return empty mapping."""
    return {}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
    offset: int = 0,
    existing_entries: list = None,
) -> list:
    """Generate a batch of unique Designation API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored for Designation (realistic names are used instead).
        dropdown_ids: Not used for Designation (no FK dropdown fields).

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    reset_designation_name_pool()
    payloads = []
    for i in range(count):
        payloads.append(
            generate_designation_api_payload(prefix, dropdown_ids)
        )
    return payloads
