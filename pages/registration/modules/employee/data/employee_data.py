"""
employee_data.py
----------------
Test data & API payload builder for Rhythm ERP Employee Screen.
Derived from live ERP schema at /core/dynamic-screen/Employee/ (tenant 599).

FIELD REFERENCE (FLAT FORM — NO STEPPERS):

  1. Party Reference      (dropdown, optional) — FK to party_master (excludes Customers)
     Auto-patches: name, email_id, mobile_no when a party is selected
  2. Employee Name         (text input, optional, maxlength=255)
     Validation: ^[A-Za-z ]+$ — letters and spaces only
  3. Email                 (text input, optional, maxlength=255)
     Validation: standard email regex
  4. Phone Number          (integer input, optional, maxlength=255)
     Validation: ^[6-9]\\d{9}$ — 10-digit Indian mobile starting with 6-9
  5. Designation           (dropdown, optional) — FK to designation table (56 options)
  6. Department            (dropdown, optional) — FK to department table (0 options currently)
  7. Status                (toggle, REQUIRED, default=true) — Active/Inactive

KEY RULES (verified 2026-06-04 on live app):
  - FLAT FORM: No steppers, no children array — all fields at root level
  - Only `status` is required — all other fields are optional
  - party_ref_id auto-fills name, email, mobile via auto_patch_query
  - Designation has 56 options; Department has 0 options currently
  - Employee Name must match ^[A-Za-z ]+$ (letters + spaces only)
  - Phone must be 10 digits starting with 6-9
  - Email must be valid format
  - API returns listing page on POST (status 200), not the created record
  - Master table: party_master (same as Supplier/Customer)
  - No detail/sub-detail tables — master-only screen
  - is_bulk_upload: true (supports bulk upload)
  - is_workflow_applicable: false
  - is_effective_dated: false

ENDPOINTS:
  Schema:  GET  /core/dynamic-screen/Employee/
  List:    GET  /core/dynamic-screen-wrapper/Employee/
  Detail:  GET  /core/dynamic-screen-wrapper/Employee/{id}/
  Create:  POST /core/dynamic-screen-wrapper/Employee/
  Update:  PUT  /core/dynamic-screen-wrapper/Employee/{id}/

SCREEN METADATA:
  Screen ID: 94
  attribute_name: "Employee"
  master_table: party_master
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Realistic Indian name pools for Employee data
# ──────────────────────────────────────────────

_FIRST_NAMES_MALE = [
    "Rajesh", "Amit", "Suresh", "Mahesh", "Dinesh", "Ramesh",
    "Vijay", "Sanjay", "Anil", "Sunil", "Mukesh", "Ashok",
    "Deepak", "Manoj", "Prakash", "Ravi", "Kiran", "Nitin",
    "Pankaj", "Vikram", "Ajay", "Rahul", "Sachin", "Rohit",
    "Arun", "Sandeep", "Ganesh", "Datta", "Shankar", "Mohan",
]

_FIRST_NAMES_FEMALE = [
    "Priya", "Sunita", "Anita", "Meena", "Rekha", "Pooja",
    "Neha", "Swati", "Aarti", "Kavita", "Suman", "Geeta",
    "Savita", "Usha", "Lata", "Madhuri", "Seema", "Nisha",
    "Manisha", "Prachi", "Rashmi", "Shraddha", "Pallavi", "Vaishali",
]

_LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Agarwal", "Gupta",
    "Jain", "Shah", "Mehta", "Reddy", "Nair", "Iyer",
    "Desai", "Kulkarni", "More", "Gaikwad", "Chavan",
    "Pawar", "Jadhav", "Bhosale", "Rao", "Hegde", "Shetty",
    "Bhat", "Pillai", "Menon", "Varma", "Chopra", "Naik",
]

_EMAIL_DOMAINS = [
    "gmail.com", "yahoo.co.in", "rediffmail.com", "hotmail.com",
    "outlook.in", "ymail.com", "inbox.com",
]

# Track generated names to prevent duplicates within a session
_generated_names = set()


# ──────────────────────────────────────────────
# FK ID pools (verified on tenant 599, 2026-06-02)
# ──────────────────────────────────────────────

DESIGNATION_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                   21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
                   41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56]
#   1  = Test Designation
#   2  = Farm Supervisor
#   3  = Warehouse Manager
#   4  = Quality Inspector
#   5  = Procurement Officer
#   6  = Accounts Executive
#   7  = Field Officer
#   8  = Weighbridge Operator
#   9  = Dispatch Coordinator
#   10 = Commodity Analyst
#   11 = Regional Manager
#   12 = Cashier
#   13 = Compliance Officer
#   14 = Data Entry Operator
#   15 = Transport Supervisor
#   16 = Loan Recovery Agent
#   17 = Agricultural Advisor
#   18 = Store Keeper
#   19 = Billing Clerk
#   20 = Internal Auditor
#   21 = IT Support Executive
#   22 = Test Designation QA
#   23 = Finance Manager
#   24 = Clerk
#   25 = Engineer
#   26 = Production Supervisor
#   27 = Quality Analyst
#   28 = HR Manager
#   29 = Warehouse Supervisor
#   30 = Managing Director
#   31 = Godown Keeper 343
#   32 = Divisional Manager0659490
#   33 = Chief Operating Officer0659491
#   34 = Warehouse Supervisor0659492
#   35 = Junior Engineer0659493
#   36 = Legal Officer0659494
#   37 = Data Analyst0716230
#   38 = Junior Engineer0716231
#   39 = IT Manager0716232
#   40 = Accounts Officer0716233
#   41 = Managing Director0716234
#   42 = Assistant General Manager0721300
#   43 = Accounts Officer0721301
#   44 = Agricultural Officer0721302
#   45 = Junior Accountant0721303
#   46 = Accounts Officer MTJ0721304
#   47 = Senior Vice President0723340
#   48 = Senior Technician0723341
#   49 = Managing Director0723342
#   50 = Agricultural Officer0723343
#   51 = Welfare Officer0723344
#   52 = Divisional Manager0729430
#   53 = Assistant General Manager0729431
#   54 = Senior Vice President0729432
#   55 = Production Manager0729433
#   56 = Chief Operating Officer0729434

DESIGNATION_NAMES = {
    1: "Test Designation", 2: "Farm Supervisor", 3: "Warehouse Manager",
    4: "Quality Inspector", 5: "Procurement Officer", 6: "Accounts Executive",
    7: "Field Officer", 8: "Weighbridge Operator", 9: "Dispatch Coordinator",
    10: "Commodity Analyst", 11: "Regional Manager", 12: "Cashier",
    13: "Compliance Officer", 14: "Data Entry Operator", 15: "Transport Supervisor",
    16: "Loan Recovery Agent", 17: "Agricultural Advisor", 18: "Store Keeper",
    19: "Billing Clerk", 20: "Internal Auditor", 21: "IT Support Executive",
    22: "Test Designation QA", 23: "Finance Manager", 24: "Clerk",
    25: "Engineer", 26: "Production Supervisor", 27: "Quality Analyst",
    28: "HR Manager", 29: "Warehouse Supervisor", 30: "Managing Director",
    31: "Godown Keeper 343", 32: "Divisional Manager0659490",
    33: "Chief Operating Officer0659491", 34: "Warehouse Supervisor0659492",
    35: "Junior Engineer0659493", 36: "Legal Officer0659494",
    37: "Data Analyst0716230", 38: "Junior Engineer0716231",
    39: "IT Manager0716232", 40: "Accounts Officer0716233",
    41: "Managing Director0716234", 42: "Assistant General Manager0721300",
    43: "Accounts Officer0721301", 44: "Agricultural Officer0721302",
    45: "Junior Accountant0721303", 46: "Accounts Officer MTJ0721304",
    47: "Senior Vice President0723340", 48: "Senior Technician0723341",
    49: "Managing Director0723342", 50: "Agricultural Officer0723343",
    51: "Welfare Officer0723344", 52: "Divisional Manager0729430",
    53: "Assistant General Manager0729431", 54: "Senior Vice President0729432",
    55: "Production Manager0729433", 56: "Chief Operating Officer0729434",
}

DESIGNATION_OPTIONS_COUNT = 56

# Party Reference IDs (316 valid options in live ERP — sample pool below)
# These are FK IDs for party_master entries
PARTY_REF_IDS = [
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 21, 23, 26, 29, 30, 33,
    45, 47, 48, 49, 50, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83,
    84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101,
    102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116,
    117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131,
    132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146,
    147, 148, 149, 150, 151, 152, 153, 154, 178, 179, 180,
]

# Department has 0 options currently
DEPARTMENT_IDS = []

# Default FK IDs dict (first option from each pool)
DEFAULT_EMPLOYEE_FK_IDS = {
    "designation": 2,      # Farm Supervisor
    "department": None,     # No options available
    "party_ref_id": None,   # Skip by default — auto-patches name/email/phone
}


# ──────────────────────────────────────────────
# Realistic data generators
# ──────────────────────────────────────────────

def generate_employee_name(prefix=None):
    """Generate a realistic Indian employee name.

    Composes: FirstName LastName (e.g., "Rajesh Sharma", "Priya Patel").
    The name matches the ERP validation pattern: ^[A-Za-z ]+$

    Args:
        prefix: Optional override — if provided, uses the
                prefix_timestamp format for guaranteed uniqueness.
    """
    if prefix:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rand = random.randint(100, 999)
        return f"{prefix}_{ts}_{rand}"

    for _ in range(200):
        first = random.choice(_FIRST_NAMES_MALE + _FIRST_NAMES_FEMALE)
        last = random.choice(_LAST_NAMES)
        name = f"{first} {last}"
        if name not in _generated_names:
            _generated_names.add(name)
            return name

    # Fallback
    ts = datetime.now().strftime("%H%M%S")
    rand = random.randint(100, 999)
    fallback = f"{random.choice(_FIRST_NAMES_MALE + _FIRST_NAMES_FEMALE)} {random.choice(_LAST_NAMES)} {ts}{rand}"
    _generated_names.add(fallback)
    return fallback


def generate_email(prefix=None):
    """Generate a realistic Indian email address.

    Examples: "rajesh.sharma@gmail.com", "patel.kumar@rediffmail.com"
    """
    if prefix:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rand = random.randint(100, 999)
        return f"{prefix}_{ts}_{rand}@employee-test.com"

    first = random.choice(_FIRST_NAMES_MALE + _FIRST_NAMES_FEMALE).lower()
    last = random.choice(_LAST_NAMES).lower()
    domain = random.choice(_EMAIL_DOMAINS)
    num = random.randint(1, 999)
    return f"{first}.{last}{num}@{domain}"


def generate_phone():
    """Generate a valid 10-digit Indian mobile number.

    Starts with 6-9 (valid Indian mobile prefix per ERP validation ^[6-9]\\d{9}$).
    Returns an integer (the API expects integer type for mobile_no).
    """
    prefix = random.choice(["6", "7", "8", "9"])
    remaining = random.randint(100000000, 999999999)
    return int(f"{prefix}{remaining}")


def generate_designation_id():
    """Pick a random designation ID from the verified pool.

    Returns:
        int: A valid designation FK ID.
    """
    return random.choice(DESIGNATION_IDS)


def generate_party_ref_id():
    """Pick a random party reference ID from the verified pool.

    Returns:
        int: A valid party_ref_id FK ID, or None to skip.
    """
    # 70% chance to skip party reference (most employees are created fresh)
    if random.random() < 0.7:
        return None
    return random.choice(PARTY_REF_IDS)


# ──────────────────────────────────────────────
# Valid data for UI form fill
# ──────────────────────────────────────────────

def generate_valid_employee_data():
    """Generate complete valid data for the Employee form.

    This is the UI-facing format (field names match the Angular form controls).
    All fields are optional except status, but we fill them for happy-path tests.

    Returns:
        dict with all form fields populated with realistic data.
    """
    return {
        "party_reference": None,                          # Skip by default
        "employee_name": generate_employee_name(),
        "email": generate_email(),
        "phone_number": generate_phone(),
        "designation": None,                              # Pick from live UI
        "department": None,                               # No options currently
        "status": True,                                   # Default: Active
    }


def generate_minimal_employee_data():
    """Generate minimal data — only the required field (status).

    All other fields are empty/null. Use for mandatory field validation tests.
    """
    return {
        "party_reference": None,
        "employee_name": "",
        "email": "",
        "phone_number": "",
        "designation": None,
        "department": None,
        "status": True,
    }


def generate_empty_employee_data():
    """Generate data with all fields empty/null — for validation testing."""
    return {
        "party_reference": None,
        "employee_name": "",
        "email": "",
        "phone_number": "",
        "designation": None,
        "department": None,
        "status": True,  # Required field — always has a value
    }


# ──────────────────────────────────────────────
# Validation / boundary test data helpers
# ──────────────────────────────────────────────

def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds max)."""
    return "A" * 256


def generate_invalid_name_numbers():
    """Generate an employee name with numbers (fails ^[A-Za-z ]+$)."""
    return "Rajesh123"


def generate_invalid_name_special_chars():
    """Generate an employee name with special characters (fails ^[A-Za-z ]+$)."""
    return "Rajesh@Sharma!"


def generate_invalid_email_no_at():
    """Generate an invalid email without @ sign."""
    return "notanemail"


def generate_invalid_email_no_domain():
    """Generate an invalid email without domain."""
    return "user@"


def generate_invalid_phone_starts_with_5():
    """Generate a phone number starting with 5 (fails ^[6-9]\\d{9}$)."""
    return int(f"5{random.randint(100000000, 999999999)}")


def generate_invalid_phone_too_short():
    """Generate a phone number that's too short (less than 10 digits)."""
    return random.randint(100, 9999)


def generate_invalid_phone_too_long():
    """Generate a phone number that's too long (more than 10 digits)."""
    return random.randint(10000000000, 99999999999)


def generate_sql_injection_name():
    """Generate a SQL injection string for Employee Name."""
    return "'; DROP TABLE party_master; --"


def generate_xss_name():
    """Generate an XSS payload string for Employee Name."""
    return "<script>alert('xss')</script>"


def generate_spaces_only_name():
    """Generate a name that's only spaces."""
    return "     "


def generate_duplicate_employee_data(existing_name, existing_email=None, existing_phone=None):
    """Return valid data using an existing name — for duplicate test.

    Args:
        existing_name: An existing employee name in the system.
        existing_email: Optional — if provided, reuse this email.
        existing_phone: Optional — if provided, reuse this phone.
    """
    return {
        "party_reference": None,
        "employee_name": existing_name,
        "email": existing_email or generate_email(),
        "phone_number": existing_phone or generate_phone(),
        "designation": None,
        "department": None,
        "status": True,
    }


# ──────────────────────────────────────────────
# Expected validation messages (from ERP schema)
# ──────────────────────────────────────────────

class ExpectedMessages:
    """Exact error messages from the ERP validation patterns."""
    INVALID_NAME = "Invalid Name"                # Pattern: ^[A-Za-z ]+$
    INVALID_EMAIL = "Invalid Email"              # Pattern: standard email regex
    INVALID_PHONE = "Invalid Phone Number"       # Pattern: ^[6-9]\d{9}$
    REQUIRED_FIELD = "This field is required"


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the UI-facing dict format into the JSON payload that
# POST /core/dynamic-screen-wrapper/Employee/ expects.
#
# SIMPLE SCREEN STRUCTURE (Employee):
#   Unlike Supplier/Customer which use stepper children arrays,
#   Employee is a FLAT form — all fields go at the root level.
#
#   {
#     "id": "",
#     "attribute_name": "Employee",
#     "party_ref_id": null,
#     "name": "Rajesh Sharma",
#     "email_id": "rajesh.sharma@gmail.com",
#     "mobile_no": 9876543210,
#     "designation": 2,
#     "department": null,
#     "status": true,
#     "details": [],
#     "children": []
#   }
#
# FIELD KEY MAPPING:
#   UI key                → API field_key
#   ──────────────────────────────────────────────────
#   party_reference       → party_ref_id (dropdown FK, skip = null)
#   employee_name         → name (string)
#   email                 → email_id (string)
#   phone_number          → mobile_no (integer)
#   designation           → designation (dropdown FK)
#   department            → department (dropdown FK)
#   status                → status (boolean)
#
# IMPORTANT RULES:
#   - Use null (None) for optional FK fields when not set
#   - "id" must be "" (empty string) for new entries
#   - mobile_no must be an INTEGER, not a string
#   - details and children must be empty arrays []
#   - designation and department FK IDs go directly at root level
# ──────────────────────────────────────────────

def build_employee_api_payload(
    employee_data: dict = None,
    fk_ids: dict = None,
) -> dict:
    """
    Build the JSON payload for POST /core/dynamic-screen-wrapper/Employee/.

    The Employee screen is FLAT — no steppers, no children array.
    All fields are at the root level, making this much simpler than
    Supplier/Customer payloads.

    Args:
        employee_data: Dict from generate_valid_employee_data().
                       If None, generates random data automatically.
        fk_ids: Optional dict of FK ID overrides. Keys should match
                API field names: designation, department, party_ref_id.
                If None, uses random IDs from verified pools.

    Returns:
        Complete JSON payload dict ready for POST.

    Example:
        payload = build_employee_api_payload()
        client.create_entry(payload)
    """
    if employee_data is None:
        employee_data = generate_valid_employee_data()

    if fk_ids is None:
        fk_ids = {}

    # Resolve FK IDs: explicit > data > random pool > None
    designation_id = fk_ids.get("designation")
    if designation_id is None and employee_data.get("designation") is None:
        designation_id = generate_designation_id()

    department_id = fk_ids.get("department")
    # Department has 0 options currently — always null

    party_ref_id = fk_ids.get("party_ref_id")
    if party_ref_id is None and employee_data.get("party_reference") is not None:
        party_ref_id = employee_data["party_reference"]

    # Build the flat payload
    payload = {
        "id": "",
        "attribute_name": "Employee",
        "party_ref_id": party_ref_id,
        "name": employee_data.get("employee_name") or generate_employee_name(),
        "email_id": employee_data.get("email") or generate_email(),
        "mobile_no": employee_data.get("phone_number") or generate_phone(),
        "designation": designation_id,
        "department": department_id,
        "status": employee_data.get("status", True),
        "details": [],
        "children": [],
    }

    return payload


def generate_employee_api_payload(**kwargs) -> dict:
    """One-shot: generate a randomized Employee API payload.

    This is the convenience function for batch_create scripts.
    Just call it and get a ready-to-POST payload.

    Args:
        **kwargs: Optional overrides for any payload field.
                  e.g., name="John", designation=5, status=False

    Returns:
        Complete JSON payload dict ready for POST.

    Example:
        # Random employee
        payload = generate_employee_api_payload()

        # With specific designation
        payload = generate_employee_api_payload(designation=2)

        # Override specific fields
        payload = generate_employee_api_payload(name="Test User", status=False)
    """
    data = generate_valid_employee_data()
    payload = build_employee_api_payload(data)

    # Apply any overrides
    payload.update(kwargs)

    return payload


# ──────────────────────────────────────────────
# Batch generation helpers
# ──────────────────────────────────────────────

def generate_batch_payloads(count: int, **kwargs) -> list:
    """Generate multiple unique Employee API payloads.

    Args:
        count: Number of payloads to generate.
        **kwargs: Optional overrides applied to ALL payloads.

    Returns:
        List of payload dicts.

    Example:
        payloads = generate_batch_payloads(10)
        payloads = generate_batch_payloads(5, designation=2, status=True)
    """
    return [generate_employee_api_payload(**kwargs) for _ in range(count)]


# ──────────────────────────────────────────────
# Field validation summary (for test parametrize)
# ──────────────────────────────────────────────

FIELD_VALIDATION_RULES = {
    "name": {
        "field_key": "name",
        "label": "Employee Name",
        "type": "character",
        "required": False,
        "max_length": 255,
        "pattern": r"^[A-Za-z ]+$",
        "error_message": "Invalid Name",
        "valid_examples": ["Rajesh Sharma", "Priya", "A B C"],
        "invalid_examples": ["Rajesh123", "Raj@Sharma", "O'Brien"],
    },
    "email_id": {
        "field_key": "email_id",
        "label": "Email",
        "type": "character",
        "required": False,
        "max_length": 255,
        "pattern": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        "error_message": "Invalid Email",
        "valid_examples": ["test@gmail.com", "user.name@domain.co.in"],
        "invalid_examples": ["notanemail", "user@", "@domain.com"],
    },
    "mobile_no": {
        "field_key": "mobile_no",
        "label": "Phone Number",
        "type": "integer",
        "required": False,
        "max_length": 255,
        "pattern": r"^[6-9]\d{9}$",
        "error_message": "Invalid Phone Number",
        "valid_examples": [9876543210, 6123456789, 8765432109],
        "invalid_examples": [5123456789, 12345, 12345678901],
    },
    "designation": {
        "field_key": "designation",
        "label": "Designation",
        "type": "dropdown",
        "required": False,
        "fk_options_count": 56,
    },
    "department": {
        "field_key": "department",
        "label": "Department",
        "type": "dropdown",
        "required": False,
        "fk_options_count": 0,
    },
    "status": {
        "field_key": "status",
        "label": "Status",
        "type": "toggle",
        "required": True,
        "default": True,
    },
}
