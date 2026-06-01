"""
supplier_data.py
----------------
Test data & expected validation messages for Rhythm ERP Supplier Screen.
Derived from supplier_master_spec.xlsx (Step 2F).

FIELD REFERENCE (3-STEP STEPPER FORM):

  STEP 1 — Universal Fields:
    1. Party Reference        (mat-select, optional) — dynamic farmer list
    2. Ownership Status       (mat-select, required) — Owned/Leased/Proprietorship/Partnership/LLP/PLC/Private Limited Company/Individual
    3. Company Name           (text input, required, maxlength=255)
    4. PO Type                (mat-select, required) — Domestic/Import
    5. Email                  (text input, optional, maxlength=255) — NO format validation (BUG-002)
    6. Phone Number           (number input, required, no maxlength) — has spinner controls (BUG-003)
    7. Default Currency       (mat-select, required) — 100+ currencies
    8. PAN Number             (text input, required, maxlength=255) — NO format validation (BUG-004)
    9. Is MSME Registered?    (toggle switch, optional, default=No)
   10. Status                 (toggle switch, optional, default=Active)

  STEP 1 — Additional Details (scroll down):
   11. Is GST Set Off         (toggle switch, optional, default=Yes)
   12. Is TDS Applicable      (toggle switch, optional, default=No)
   13. Contact Person Name    (text input, optional, maxlength=255)
   14. Office Number          (text input, optional, maxlength=255)
   15. Payment Terms          (mat-select, optional) — 21 Days/14 Days/7 Days/Wallet/RTGS/Advance/Immediate/60 Days/30 Days
   16. Delivery Terms         (mat-select, optional) — Delivery/Spot
   17. Mode Of Delivery       (mat-select, optional) — Air/Courier/Sea/Railway/Truck

  STEP 2 — Address Details (dynamic rows):
   18. Address Type           (mat-select, required) — Shipping/Billing
   19. Country                (mat-select, required) — cascading → State → District → Taluka → Village
   20. State                  (mat-select, required, depends on Country)
   21. District               (mat-select, required, depends on State)
   22. Taluka                 (mat-select, required, depends on District)
   23. Village                (mat-select, optional, depends on Taluka)
   24. Address                (text input, required, maxlength=255)
   25. Pin Code               (text input, optional, maxlength=255)
   26. GSTIN                  (text input, optional, maxlength=255)

  STEP 3 — Bank Details (dynamic rows):
   27. Bank Name              (text input, optional, maxlength=255)
   28. Branch                 (text input, optional, maxlength=255)
   29. IFSC Code              (text input, optional, maxlength=255)
   30. Account Type           (mat-select, optional) — Current/Saving
   31. Account Holder Name    (text input, optional, maxlength=255)
   32. Account Number         (text input, optional, maxlength=255)
   33. Bank Proof             (mat-select, required) — Cancelled Cheque/Passbook
   34. Attachment             (file upload, optional) — .png/.jpg/.pdf

KEY RULES (verified 2026-05-22 on live app):
  - STEPPER FORM: 3 steps with Next/Back navigation
  - Step 1 has TWO sub-sections (Universal + Additional Details)
  - Additional Details requires scrolling down within Step 1
  - Address and Bank steps support dynamic row addition (add/remove)
  - Cascading dropdowns: Country → State → District → Taluka → Village
  - Party Reference is read-only in Edit/View mode (disabled mat-select)
  - BUG-001: Company Name accepts special characters
  - BUG-002: No email format validation
  - BUG-003: Phone Number has spinner controls (type=number)
  - BUG-004: No PAN format validation
  - BUG-005: No Update button in Edit mode — only Cancel visible
  - NO History button on Supplier screen
  - No Delete option anywhere

LOGIN: Assistant@mail.com / Vedant@12345 / Facility: RuralLife Producer Company (index 0)
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Realistic Indian data pools
# ──────────────────────────────────────────────

_COMPANY_PREFIXES = [
    "Shree", "Sri", "Maa", "Jai", "Om", "Baba", "New",
    "Royal", "Supreme", "Golden", "Maha", "Divya", "Hari",
    "Sai", "Guru", "Balaji", "Venkatesh", "Jagdamba",
]

_COMPANY_NAMES = [
    "Ganesh", "Krishna", "Patel", "Sharma", "Agro", "Bharat",
    "Lakshmi", "Durga", "Sai", "Ram", "Hanuman", "Amul",
    "Narmada", "Godavari", "Yamuna", "Sutlej", "Ganga",
    "Kaveri", "Tapi", "Krishna", "Malabar", "Konkan",
    "Maratha", "Rajput", "Chola", "Pallava", "Maurya",
    "Indus", "Deccan", "Malwa", "Kalinga", "Vindhya",
]

_COMPANY_TYPES = [
    "Traders", "Enterprises", "Industries", "Trading Co.",
    "Supply Chain", "Agro", "Packaging", "Exports",
    "Commodities", "Produce", "Foods", "Processing",
    "Grain Processors", "Oil Mills", "Spice Merchants",
    "Tea Traders", "Cotton Mills", "Sugar Works",
]

_COMPANY_SUFFIXES = [
    "Pvt Ltd", "LLP", "Co.", "& Sons", "& Bros",
    "Associates", "Group", "Corp", "", "", "",  # empty = no suffix
]

_FIRST_NAMES = [
    "Rajesh", "Amit", "Suresh", "Mahesh", "Dinesh", "Ramesh",
    "Vijay", "Sanjay", "Anil", "Sunil", "Mukesh", "Ashok",
    "Deepak", "Manoj", "Prakash", "Ravi", "Kiran", "Nitin",
    "Pankaj", "Vikram", "Ajay", "Rahul", "Sachin", "Rohit",
    "Priya", "Sunita", "Anita", "Meena", "Rekha", "Pooja",
    "Neha", "Swati", "Aarti", "Kavita", "Suman", "Geeta",
]

_LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Agarwal", "Gupta",
    "Jain", "Shah", "Mehta", "Reddy", "Nair", "Iyer",
    "Desai", "Kulkarni", "More", "Gaikwad", "Chavan",
    "Pawar", "Jadhav", "Bhosale", "Rao", "Hegde", "Shetty",
    "Hegde", "Bhat", "Pillai", "Menon", "Varma", "Chopra",
]

_EMAIL_DOMAINS = [
    "gmail.com", "yahoo.co.in", "rediffmail.com", "hotmail.com",
    "outlook.in", "ymail.com", "inbox.com",
]

_BANK_NAMES = [
    "State Bank of India", "HDFC Bank", "ICICI Bank",
    "Punjab National Bank", "Bank of Baroda", "Canara Bank",
    "Union Bank of India", "Bank of India", "Axis Bank",
    "Kotak Mahindra Bank", "Indian Bank", "Central Bank of India",
    "UCO Bank", "Indian Overseas Bank", "Dena Bank",
]

_BANK_CITIES = [
    "Mumbai", "Delhi", "Pune", "Ahmedabad", "Bangalore",
    "Chennai", "Hyderabad", "Kolkata", "Jaipur", "Lucknow",
    "Nagpur", "Indore", "Chandigarh", "Coimbatore", "Vadodara",
    "Surat", "Ludhiana", "Bhopal", "Patna", "Rajkot",
]

_STREET_NAMES = [
    "MG Road", "Station Road", "Main Road", "Industrial Area",
    "Gandhi Nagar", "Jawahar Chowk", "Shivaji Nagar",
    "Subhash Marg", "Nehru Nagar", "Patel Colony",
    "Ambedkar Road", "Tilak Road", "Laxmi Nagar",
    "Sardar Patel Road", "Tagore Marg", "Guru Nanak Pura",
    "Rani Laxmi Bai Marg", "Vivekanand Road", "Azad Nagar",
    "Prabhat Road", "FC Road", "JM Road", "SB Road",
    "FCI Godown Road", "APMC Market", "Grain Market Road",
    "Cotton Market", "Transport Nagar", "Workshop Road",
]

_AREA_TYPES = [
    "Industrial Area", "Commercial Zone", "Business Park",
    "Trade Centre", "Market Yard", "Godown Road", "",
]

_CITY_NAMES = [
    "Mumbai", "Delhi", "Pune", "Ahmedabad", "Bangalore",
    "Chennai", "Hyderabad", "Kolkata", "Jaipur", "Lucknow",
    "Nagpur", "Indore", "Chandigarh", "Coimbatore", "Vadodara",
    "Surat", "Ludhiana", "Bhopal", "Patna", "Rajkot",
]

# Track generated names to prevent duplicates within a session
_generated_names = set()


# ──────────────────────────────────────────────
# Realistic Indian data generators
# ──────────────────────────────────────────────

def generate_company_name(prefix=None):
    """Generate a realistic Indian company/supplier name.

    Composes from pools: Prefix + Name + BusinessType + optional Suffix.
    Falls back to "prefix_timestamp" if all combos exhausted.

    Examples: "Shree Ganesh Trading Co.", "Royal Patel Industries",
              "Om Sai Enterprises", "Supreme Bharat Supply Chain Pvt Ltd"

    Args:
        prefix: Optional override — if provided, uses the old
                prefix_timestamp format for backward compatibility.
    """
    if prefix:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rand = random.randint(100, 999)
        return f"{prefix}_{ts}_{rand}"

    # Compose from realistic pools (4800+ combos, more than enough for 20-50)
    for _ in range(200):  # try up to 200 times before fallback
        name = random.choice(_COMPANY_PREFIXES)
        name += " " + random.choice(_COMPANY_NAMES)
        name += " " + random.choice(_COMPANY_TYPES)
        suffix = random.choice(_COMPANY_SUFFIXES)
        if suffix:
            name += " " + suffix
        if name not in _generated_names:
            _generated_names.add(name)
            return name

    # Fallback (should never hit for < 1000 entries)
    ts = datetime.now().strftime("%H%M%S")
    rand = random.randint(100, 999)
    fallback = f"{random.choice(_COMPANY_PREFIXES)} {random.choice(_COMPANY_NAMES)} {random.choice(_COMPANY_TYPES)} {ts}{rand}"
    _generated_names.add(fallback)
    return fallback


def generate_email(prefix=None):
    """Generate a realistic Indian email address.

    Examples: "rajesh.sharma@gmail.com", "patel.agro@rediffmail.com"
    Falls back to "prefix_ts_rand@domain" if prefix is provided.
    """
    if prefix:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        rand = random.randint(100, 999)
        return f"{prefix}_{ts}_{rand}@supplier-test.com"

    first = random.choice(_FIRST_NAMES).lower()
    last = random.choice(_LAST_NAMES).lower()
    domain = random.choice(_EMAIL_DOMAINS)
    # Add a small random number for uniqueness
    num = random.randint(1, 999)
    return f"{first}.{last}{num}@{domain}"


def generate_phone():
    """Generate a valid 10-digit Indian mobile number.
    Starts with 6-9 (valid Indian mobile prefix).
    """
    prefix = random.choice(["6", "7", "8", "9"])
    return f"{prefix}{random.randint(100000000, 999999999)}"


def generate_pan():
    """Generate a valid Indian PAN number (5 letters + 4 digits + 1 letter).
    Format: ABCDE1234F
    """
    letters = random.choices(string.ascii_uppercase, k=5)
    digits = random.choices(string.digits, k=4)
    last_letter = random.choice(string.ascii_uppercase)
    return f"{''.join(letters)}{''.join(digits)}{last_letter}"


def generate_contact_person(prefix=None):
    """Generate a realistic Indian contact person name.

    Examples: "Rajesh Sharma", "Priya Patel", "Vijay Kulkarni"
    Falls back to "prefix_timestamp" if prefix is provided.
    """
    if prefix:
        ts = datetime.now().strftime("%H%M%S")
        return f"{prefix}_{ts}"

    return f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"


def generate_office_number():
    """Return None for office number.
    The ERP API rejects formatted landline numbers (e.g., 020-25531234).
    Leave blank — the field is optional.
    """
    return None


def generate_ifsc():
    """Generate a valid IFSC code (4 letters + 0 + 6 digits).
    Uses realistic bank codes: SBIN, HDFC, ICIC, PUNB, BARB, etc.
    """
    bank_codes = [
        "SBIN", "HDFC", "ICIC", "PUNB", "BARB", "CNRB",
        "UBIN", "BKID", "UTIB", "KKBK", "INDB", "CBIN",
    ]
    branch_code = "".join(random.choices(string.digits, k=6))
    return f"{random.choice(bank_codes)}0{branch_code}"


def generate_account_number():
    """Generate a random bank account number (9-16 digits)."""
    return f"{random.randint(100000000000, 999999999999)}"


def generate_gstin(state_code=None):
    """Generate a valid Indian GSTIN with Luhn mod-36 checksum.

    The ERP API validates GSTIN checksum — random chars will be REJECTED.
    This function produces GSTINs that pass the Luhn mod-36 check.

    Format: NN + 5L + 4D + 1L + 1[1-9A-Z] + Z + 1[0-9A-Z] (checksum)
    Total: 15 characters.

    Args:
        state_code: 2-digit state code (default: random 01-37)
    """
    LUHN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    if state_code is None:
        state_code = f"{random.randint(1, 37):02d}"
    else:
        state_code = f"{int(state_code):02d}"

    body = (
        state_code
        + "".join(random.choices(string.ascii_uppercase, k=5))
        + "".join(random.choices(string.digits, k=4))
        + random.choice(string.ascii_uppercase)
        + random.choice("123456789" + string.ascii_uppercase[9:])
        + "Z"
    )

    # Luhn mod-36 checksum calculation
    total = 0
    for i, ch in enumerate(body):
        val = LUHN_CHARS.index(ch)
        if i % 2 == 1:
            val *= 2
            if val >= 36:
                val -= 35
        total += val

    check = (36 - (total % 36)) % 36
    return body + LUHN_CHARS[check]


def generate_pin_code():
    """Generate a valid 6-digit Indian pin code."""
    return f"{random.randint(100000, 999999)}"


def generate_address():
    """Generate a realistic Indian address line.

    Examples: "42, MG Road, Industrial Area",
              "Plot 17, Shivaji Nagar, Market Yard"
    """
    plot = random.choice([
        f"{random.randint(1, 500)}",
        f"Plot {random.randint(1, 200)}",
        f"Shop {random.randint(1, 100)}",
        f"Gala {random.randint(1, 50)}",
        f"Unit {random.randint(1, 30)}",
    ])
    street = random.choice(_STREET_NAMES)
    area = random.choice(_AREA_TYPES)
    if area:
        return f"{plot}, {street}, {area}"
    return f"{plot}, {street}"


# ──────────────────────────────────────────────
# Complete Valid Data for Create (Step 1)
# ──────────────────────────────────────────────

def generate_valid_step1_data(company_prefix=None):
    """Generate complete valid data for Step 1 (Universal + Additional Details).
    Uses realistic Indian names by default. Pass company_prefix to use
    the old prefix_timestamp format for backward compatibility.
    Dropdown values set to None — must be populated from live UI at runtime.
    """
    return {
        # Universal fields
        "party_reference": "",         # Optional — skip by default
        "ownership_status": None,      # Pick from live UI (REQUIRED)
        "company_name": generate_company_name(company_prefix),
        "po_type": None,               # Pick from live UI (REQUIRED): Domestic/Import
        "email": generate_email(),
        "phone_number": generate_phone(),
        "default_currency": "INR",      # Pick from live UI (REQUIRED)
        "pan_number": generate_pan(),
        # Toggle switches
        "is_msme": False,              # Default: No
        "status": True,                # Default: Active
        # Additional Details
        "is_gst_set_off": True,        # Default: Yes
        "is_tds_applicable": False,    # Default: No
        "contact_person": generate_contact_person(),
        "office_number": None,              # API rejects formatted numbers — leave blank
        "payment_terms": None,         # Pick from live UI (optional)
        "delivery_terms": None,        # Pick from live UI (optional)
        "mode_of_delivery": None,      # Pick from live UI (optional)
    }


# ──────────────────────────────────────────────
# Known-good states (verified to have all cascading levels including Village)
# ──────────────────────────────────────────────

_KNOWN_CASCADING_PATHS = [
    {"country": "India", "state": "Maharashtra"},
    {"country": "India", "state": "Gujarat"},
    {"country": "India", "state": "Rajasthan"},
    {"country": "India", "state": "Karnataka"},
    {"country": "India", "state": "Tamil Nadu"},
]


def generate_valid_step2_data():
    """Generate valid data for Step 2 (Address Details).
    Country and State are hardcoded (verified to have all cascading levels).
    District, Taluka, Village are picked randomly from live UI at runtime.
    """
    path = random.choice(_KNOWN_CASCADING_PATHS)
    return {
        "address_type": None,          # Pick from live UI (REQUIRED): Shipping/Billing
        "country": path["country"],
        "state": path["state"],
        "district": None,              # Pick from live UI (random from available)
        "taluka": None,                # Pick from live UI (random from available)
        "village": None,               # Pick from live UI (optional)
        "address": generate_address(),
        "pin_code": generate_pin_code(),
        "gstin": generate_gstin(),
    }  # no change to step2 structure — address/gstin/pin already realistic


def generate_valid_step3_data():
    """Generate valid data for Step 3 (Bank Details).
    Uses realistic Indian bank names, city branches, and contact person names.
    """
    bank = random.choice(_BANK_NAMES)
    city = random.choice(_BANK_CITIES)
    holder = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
    return {
        "bank_name": bank,
        "branch": f"{city} Branch",
        "ifsc_code": generate_ifsc(),
        "account_type": None,          # Pick from live UI (optional): Current/Saving
        "account_holder_name": holder,
        "account_number": generate_account_number(),
        "bank_proof": None,            # Pick from live UI (REQUIRED): Cancelled Cheque/Passbook
        "attachment_path": None,       # File path for upload (optional)
    }


def generate_valid_supplier_data(company_prefix=None):
    """Generate complete valid data for ALL 3 steps.
    Uses realistic Indian data by default. Pass company_prefix for old format.
    Used for end-to-end happy path tests.
    """
    return {
        "step1": generate_valid_step1_data(company_prefix),
        "step2": generate_valid_step2_data(),
        "step3": generate_valid_step3_data(),
    }


def generate_valid_edit_data():
    """Generate valid data for Edit form — only fields we want to change.
    BUG-005: No Update button in Edit mode — this data may not be saveable.
    """
    return {
        "company_name": generate_company_name(),
        "email": generate_email(),
        "phone_number": generate_phone(),
        "pan_number": generate_pan(),
        "contact_person": generate_contact_person(),
        "office_number": None,  # API rejects formatted numbers
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


def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_special_char_company_name():
    """Generate a company name with special characters (BUG-001 test)."""
    return "Test@#Traders&Co!"


def generate_sql_injection_company_name():
    """Generate a SQL injection string for Company Name."""
    return "'; DROP TABLE suppliers; --"


def generate_xss_company_name():
    """Generate an XSS payload string for Company Name."""
    return "<script>alert('xss')</script>"


def generate_invalid_email():
    """Generate an invalid email (BUG-002 test)."""
    return "notanemail"


def generate_invalid_pan():
    """Generate an invalid PAN format (BUG-004 test)."""
    return "INVALIDPAN"


def generate_empty_step1_data():
    """Return dict with all Step 1 fields empty — for mandatory field validation."""
    return {
        "party_reference": "",
        "ownership_status": "",
        "company_name": "",
        "po_type": "",
        "email": "",
        "phone_number": "",
        "default_currency": "INR",
        "pan_number": "",
        "is_msme": False,
        "status": True,
        "is_gst_set_off": True,
        "is_tds_applicable": False,
        "contact_person": "",
        "office_number": "",
        "payment_terms": "",
        "delivery_terms": "",
        "mode_of_delivery": "",
    }


def generate_duplicate_company_data(existing_company_name):
    """Return valid data using an existing company name — for duplicate test."""
    return {
        "step1": {
            "ownership_status": None,
            "company_name": existing_company_name,
            "po_type": None,
            "email": generate_email("dup"),
            "phone_number": generate_phone(),
            "default_currency": "INR",
            "pan_number": generate_pan(),
            "is_msme": False,
            "status": True,
            "is_gst_set_off": True,
            "is_tds_applicable": False,
            "contact_person": "Contact Person",
            "office_number": "",
            "payment_terms": None,
            "delivery_terms": None,
            "mode_of_delivery": None,
        },
        "step2": generate_valid_step2_data(),
        "step3": generate_valid_step3_data(),
    }


def generate_duplicate_email_data(existing_email):
    """Return valid data using an existing email — for duplicate email test."""
    step1 = generate_valid_step1_data("DupEmail")
    step1["email"] = existing_email
    return {
        "step1": step1,
        "step2": generate_valid_step2_data(),
        "step3": generate_valid_step3_data(),
    }


def generate_duplicate_phone_data(existing_phone):
    """Return valid data using an existing phone — for duplicate phone test."""
    step1 = generate_valid_step1_data("DupPhone")
    step1["phone_number"] = existing_phone
    return {
        "step1": step1,
        "step2": generate_valid_step2_data(),
        "step3": generate_valid_step3_data(),
    }


def generate_alpha_phone():
    """Generate alphabetic characters for Phone Number field."""
    return "abcdefghij"


def generate_numbers_only_company_name():
    """Generate a numbers-only company name."""
    return "1234567890"


def generate_unicode_company_name():
    """Generate a company name with Unicode characters."""
    return "TestSupplie\u00e9\u00f1\u00fc\u00e4\u00f6"


def generate_leading_trailing_spaces_company_name():
    """Generate a company name with leading and trailing spaces."""
    return "  SpaceTestSupplier  "


# ──────────────────────────────────────────────
# Expected validation messages (from ERP exploration)
# ──────────────────────────────────────────────

class ExpectedMessages:
    """Exact error messages observed on the ERP."""
    VALIDATION_FAILED_TITLE = "Validation Failed"
    VALIDATION_FAILED_MSG = "Please correct the highlighted fields"
    REQUIRED_FIELD_ERROR = "This field is required"
    INVALID_EMAIL = "Invalid Email"
    INVALID_PAN = "Invalid PAN Number"
    # BUG: special chars accepted in Company Name
    SPECIAL_CHARS_ACCEPTED = "(BUG-001: Special characters accepted without validation)"
    # BUG: phone number has spinner controls
    PHONE_SPINNER_BUG = "(BUG-003: Phone Number type=number shows spinner controls)"
    # BUG: no Update button in Edit mode
    EDIT_NO_UPDATE = "(BUG-005: No Update button visible in Edit mode)"


# ──────────────────────────────────────────────
# Known bugs (from Bug Registry in master spec)
# ──────────────────────────────────────────────

class KnownBugs:
    """Bug IDs from master spec for @pytest.mark.xfail references."""
    BUG_001 = "BUG-001: Company Name accepts special characters — no validation"
    BUG_003 = "BUG-003: Phone Number field shows spinner controls (type=number)"
    # BUG-002 (No email validation) — FIXED, ERP now shows "Invalid Email"
    # BUG-004 (No PAN validation) — FIXED, ERP now shows "Invalid PAN Number"
    # BUG-005 (No Update button in Edit) — FIXED, Update button now visible


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the existing step1/step2/step3 dict format into the JSON
# payload that POST /core/dynamic-screen-wrapper/ expects.
#
# COMPLEX SCREEN STRUCTURE (Supplier, Customer, etc.):
#   The payload uses a `children` array with stepper objects.
#   This is the CORRECT structure per the RhythmERP Universal API
#   Reference v2.0 — the old flat structure was WRONG.
#
#   {
#     "id": "",
#     "attribute_name": "Supplier",
#     <root-level fields from Step 1 Universal>,
#     "children": [
#       {
#         "stepper_name": "Additional Details",
#         "is_stepper": true,
#         "details": [{ <Additional Details fields> }],
#         "children": []
#       },
#       {
#         "stepper_name": "Address Details",
#         "is_stepper": true,
#         "details": [{ <Address row 1> }, { <Address row 2> }],
#         "children": []
#       },
#       {
#         "stepper_name": "Bank Details",
#         "is_stepper": true,
#         "details": [{ <Bank row 1> }],
#         "children": []
#       }
#     ]
#   }
#
# FIELD KEY MAPPING (verified 2026-06-01 from API reference):
#
#   UI step1 key              → API field_key
#   ──────────────────────────────────────────────────
#   party_reference           → party_ref_id (dropdown FK, skip = null)
#   ownership_status          → ownership_status_ref_id (dropdown FK)
#   company_name              → name
#   po_type                   → po_type_ref_id (dropdown FK)
#   email                     → email_id
#   phone_number              → mobile_no (string of digits)
#   default_currency          → default_currency_ref_id (dropdown FK)
#   pan_number                → pan_no
#   is_msme                   → is_msme_registered (boolean)
#   status                    → status (boolean)
#
#   Additional Details (inside children[0].details[0]):
#   contact_person            → display_name_as
#   office_number             → office_no
#   is_gst_set_off            → is_gst_set_off (boolean)
#   is_tds_applicable         → is_tds_applicable (boolean)
#   payment_terms             → payment_terms_ref_id (dropdown FK)
#   delivery_terms            → delivery_terms_ref_id (dropdown FK)
#   mode_of_delivery          → mode_of_delivery_ref_id (dropdown FK)
#
#   Address Details (inside children[1].details[0]):
#   address_type              → address_type (dropdown FK)
#   country                   → country_ref_id_id (dropdown FK)
#   state                     → state_ref_id_id (dropdown FK)
#   district                  → district_ref_id_id (dropdown FK)
#   taluka                    → sub_district_ref_id_id (dropdown FK)
#   village                   → village_ref_id_id (dropdown FK)
#   address                   → address
#   pin_code                  → pin_code
#   gstin                     → gstin
#
#   Bank Details (inside children[2].details[0]):
#   bank_name                 → bank_name
#   branch                    → bank_branch_code
#   ifsc_code                 → bank_ifsc_code
#   account_type              → account_type (dropdown FK)
#   account_holder_name       → bank_account_holder_name
#   account_number            → bank_account_no
#   bank_proof                → bank_doc_id (dropdown FK)
#   attachment_path           → bank_attachment_path (file, skip = "")
#
# IMPORTANT RULES:
#   - Use null (None) instead of "" for optional fields the API expects as null
#   - Dropdown FK fields with None value are OMITTED from payload
#   - "id" must be "" (empty string) for new entries
#   - GSTIN must pass Luhn mod-36 checksum (use generate_gstin())
#   - PAN must match [A-Z]{5}[0-9]{4}[A-Z] (use generate_pan())
# ──────────────────────────────────────────────

# Default FK IDs for common dropdowns (verified on tenant 599).
# These can be overridden per test via the dropdown_ids parameter.
# Source: RhythmERP Universal API Reference v2.0 (June 2026)
#
# IMPORTANT: These IDs are instance-specific. Always verify with
# GET /core/dynamic-screen-wrapper/<SCREEN_NAME>/?page_number=1&page_size=50
# or use client.discover_structure("Supplier") before relying on them.
# ──────────────────────────────────────────────
# Dropdown FK ID pools (verified on tenant 599)
# ──────────────────────────────────────────────
# Each pool contains all known valid IDs for that dropdown.
# generate_supplier_api_payload() picks randomly from these
# so that each entry looks different.

OWNERSHIP_STATUS_IDS = [7, 1262, 1263, 1853]
#   7 = Private Limited Company
#   1262 = Partnership
#   1263 = Proprietorship
#   1853 = Individual

PO_TYPE_IDS = [25, 24]
#   25 = Domestic
#   24 = Import

ADDRESS_TYPE_IDS = [43, 42]
#   43 = Shipping
#   42 = Billing

ACCOUNT_TYPE_IDS = [1849, 1850]
#   1849 = Current
#   1850 = Saving

PAYMENT_TERMS_IDS = [26, 27, 28, 29, 30, 31, 32, 33, 34]
#   26 = 30 Days, 27 = 60 Days, 28 = Advance,
#   29 = Immediate, 30 = RTGS, 31 = Wallet,
#   32 = 7 Days, 33 = 14 Days, 34 = 21 Days

DELIVERY_TERMS_IDS = [129, 130]
#   129 = Delivery
#   130 = Spot

MODE_OF_DELIVERY_IDS = [30, 31, 32, 33, 34]
#   30 = Truck, 31 = Railway, 32 = Sea,
#   33 = Courier, 34 = Air

BANK_DOC_IDS = [1883, 1884]
#   1883 = Bank Statement
#   1884 = Cancelled Cheque

# Fixed defaults (these never vary)
DEFAULT_CURRENCY_REF_ID = 1   # INR
DEFAULT_COUNTRY_REF_ID = 8    # India

# Backward-compatible DEFAULT_SUPPLIER_FK_IDS dict (uses first option from each pool)
DEFAULT_SUPPLIER_FK_IDS = {
    "ownership_status_ref_id": 7,    # Private Limited Company
    "po_type_ref_id": 25,           # Domestic
    "default_currency_ref_id": 1,    # INR
    "payment_terms_ref_id": 26,     # 30 Days
    "delivery_terms_ref_id": 129,   # Delivery
    "mode_of_delivery_ref_id": 30,  # Truck
    "address_type": 43,             # Shipping (Billing=42)
    "country_ref_id_id": 8,         # India
    "account_type": 1849,           # Current (Saving=1850)
    "bank_doc_id": 1883,            # Bank Statement
}


# ──────────────────────────────────────────────
# Cascading Address Pool
# ──────────────────────────────────────────────
# Each entry is a complete valid chain: state → district → taluka → village.
# These are FK IDs verified against the live ERP.
#
# The pool is built from:
#   1. Existing supplier entries (discover_structure)
#   2. Captured encrypted queries from DevTools
#   3. scripts/capture_cascade.py for easy expansion
#
# Country is always India (id=8) — not included per chain.

_ADDRESS_CHAINS = [
    # ──────────────────────────────────────────────────
    # VERIFIED chains — harvested from live Supplier entries
    # on tenant 599 via scripts/full_harvest.py
    # All chains have been confirmed valid by the API.
    # ──────────────────────────────────────────────────

    # ── Maharashtra (state 12) / Akola district ──
    {
        "state_ref_id_id": 12,
        "district_ref_id_id": 208,
        "sub_district_ref_id_id": 13041,
        "village_ref_id_id": 422660,
        "_verified": True,
    },
    {
        "state_ref_id_id": 12,
        "district_ref_id_id": 208,
        "sub_district_ref_id_id": 12723,
        "village_ref_id_id": 422597,
        "_verified": True,
    },
    {
        "state_ref_id_id": 12,
        "district_ref_id_id": 208,
        "sub_district_ref_id_id": 12750,
        "village_ref_id_id": 422600,
        "_verified": True,
    },

    # ── Punjab (state 82) / multiple districts ──
    {
        "state_ref_id_id": 82,
        "district_ref_id_id": 764,
        "sub_district_ref_id_id": 13939,
        "village_ref_id_id": 775472,
        "_verified": True,
    },
    {
        "state_ref_id_id": 82,
        "district_ref_id_id": 752,
        "sub_district_ref_id_id": 13865,
        "village_ref_id_id": 759006,
        "_verified": True,
    },
    {
        "state_ref_id_id": 82,
        "district_ref_id_id": 761,
        "sub_district_ref_id_id": 14119,
        "village_ref_id_id": 772475,
        "_verified": True,
    },
    {
        "state_ref_id_id": 82,
        "district_ref_id_id": 780,
        "sub_district_ref_id_id": 13973,
        "village_ref_id_id": 791665,
        "_verified": True,
    },
    {
        "state_ref_id_id": 82,
        "district_ref_id_id": 750,
        "sub_district_ref_id_id": 14082,
        "village_ref_id_id": 756839,
        "_verified": True,
    },
    {
        "state_ref_id_id": 82,
        "district_ref_id_id": 743,
        "sub_district_ref_id_id": 13803,
        "village_ref_id_id": 744396,
        "_verified": True,
    },

    # ── State 98 / multiple districts ──
    {
        "state_ref_id_id": 98,
        "district_ref_id_id": 505,
        "sub_district_ref_id_id": 11544,
        "village_ref_id_id": 317896,
        "_verified": True,
    },
    {
        "state_ref_id_id": 98,
        "district_ref_id_id": 479,
        "sub_district_ref_id_id": 11462,
        "village_ref_id_id": 303411,
        "_verified": True,
    },
    {
        "state_ref_id_id": 98,
        "district_ref_id_id": 480,
        "sub_district_ref_id_id": 11542,
        "village_ref_id_id": 304232,
        "_verified": True,
    },
    {
        "state_ref_id_id": 98,
        "district_ref_id_id": 494,
        "sub_district_ref_id_id": 11279,
        "village_ref_id_id": 311307,
        "_verified": True,
    },
    {
        "state_ref_id_id": 98,
        "district_ref_id_id": 484,
        "sub_district_ref_id_id": 11418,
        "village_ref_id_id": 306563,
        "_verified": True,
    },
    {
        "state_ref_id_id": 98,
        "district_ref_id_id": 502,
        "sub_district_ref_id_id": 11472,
        "village_ref_id_id": 315812,
        "_verified": True,
    },

    # ── State 101 / multiple districts ──
    {
        "state_ref_id_id": 101,
        "district_ref_id_id": 233,
        "sub_district_ref_id_id": 12979,
        "village_ref_id_id": None,
        "_verified": True,
    },
    {
        "state_ref_id_id": 101,
        "district_ref_id_id": 229,
        "sub_district_ref_id_id": 12726,
        "village_ref_id_id": 445496,
        "_verified": True,
    },
    {
        "state_ref_id_id": 101,
        "district_ref_id_id": 231,
        "sub_district_ref_id_id": 13060,
        "village_ref_id_id": 448915,
        "_verified": True,
    },
    {
        "state_ref_id_id": 101,
        "district_ref_id_id": 222,
        "sub_district_ref_id_id": 12729,
        "village_ref_id_id": 438513,
        "_verified": True,
    },

    # ── State 103 / multiple districts ──
    {
        "state_ref_id_id": 103,
        "district_ref_id_id": 569,
        "sub_district_ref_id_id": 12403,
        "village_ref_id_id": 392606,
        "_verified": True,
    },
    {
        "state_ref_id_id": 103,
        "district_ref_id_id": 575,
        "sub_district_ref_id_id": 12554,
        "village_ref_id_id": 398345,
        "_verified": True,
    },
    {
        "state_ref_id_id": 103,
        "district_ref_id_id": 585,
        "sub_district_ref_id_id": 12519,
        "village_ref_id_id": 407745,
        "_verified": True,
    },

    # ── State 107 / multiple districts ──
    {
        "state_ref_id_id": 107,
        "district_ref_id_id": 796,
        "sub_district_ref_id_id": 14523,
        "village_ref_id_id": 497349,
        "_verified": True,
    },
    {
        "state_ref_id_id": 107,
        "district_ref_id_id": 811,
        "sub_district_ref_id_id": 14387,
        "village_ref_id_id": 503970,
        "_verified": True,
    },
]


def get_random_address_chain(verified_only: bool = True) -> dict:
    """Pick a random valid cascading address chain from the pool.

    By default, only returns VERIFIED chains (ones that have been
    successfully used to create entries). Set verified_only=False
    to include unverified chains (estimated FK IDs that may fail).

    The returned dict includes state_ref_id_id, district_ref_id_id,
    sub_district_ref_id_id, village_ref_id_id. The internal
    "_verified" key is stripped before returning.

    Args:
        verified_only: If True (default), only pick from chains
                       marked _verified=True. If False, pick from
                       all chains (some may have invalid FK IDs).

    Returns:
        Dict with address chain FK IDs (no "_verified" key).
    """
    if verified_only:
        pool = [c for c in _ADDRESS_CHAINS if c.get("_verified", False)]
    else:
        pool = _ADDRESS_CHAINS

    if not pool:
        # Fallback: use all chains if no verified ones exist
        pool = _ADDRESS_CHAINS

    chain = random.choice(pool)
    # Strip the internal _verified flag before returning
    return {k: v for k, v in chain.items() if k != "_verified"}


def add_address_chain(chain: dict, verified: bool = True):
    """Add a new valid address chain to the pool.

    Used by scripts/harvest_addresses.py or scripts/verify_chains.py
    to expand the pool with chains discovered from the live ERP.

    Chain must include: state_ref_id_id, district_ref_id_id,
    sub_district_ref_id_id, village_ref_id_id.

    Args:
        chain: Dict with the 4 FK ID keys.
        verified: If True (default), marks this chain as verified
                  (successfully used to create an entry).
    """
    chain_copy = {**chain, "_verified": verified}
    _ADDRESS_CHAINS.append(chain_copy)


def build_supplier_api_payload(
    step1_data: dict,
    step2_data: dict,
    step3_data: dict,
    dropdown_ids: dict = None,
) -> dict:
    """
    Convert the existing step1/step2/step3 dict format into the JSON
    payload that the ERP API expects.

    Uses the `children` array with stepper objects — this is the CORRECT
    structure for complex screens (Supplier, Customer, etc.) as documented
    in the RhythmERP Universal API Reference v2.0.

    Structure:
      {
        "id": "",
        "attribute_name": "Supplier",
        <root-level fields>,
        "children": [
          {"stepper_name": "Additional Details", "is_stepper": true, "details": [...]},
          {"stepper_name": "Address Details",    "is_stepper": true, "details": [...]},
          {"stepper_name": "Bank Details",       "is_stepper": true, "details": [...]},
        ]
      }

    This function REUSES the same data generators (generate_company_name,
    generate_pan, etc.) — the only difference is how the data is packaged.

    IMPORTANT: For optional dropdown FKs that are None in DEFAULT_SUPPLIER_FK_IDS,
    you MUST resolve them via the API before calling this function, or pass
    them explicitly in dropdown_ids. Fields with None will be omitted from
    the payload to avoid sending null where the API expects an integer.

    Args:
        step1_data: Dict from generate_valid_step1_data() or similar.
        step2_data: Dict from generate_valid_step2_data() or similar.
        step3_data: Dict from generate_valid_step3_data() or similar.
        dropdown_ids: Dict of resolved FK IDs. Missing keys fall back to
                      DEFAULT_SUPPLIER_FK_IDS. Pass {} to use all defaults.

    Returns:
        Complete JSON payload ready for POST /core/dynamic-screen-wrapper/

    Example:
        data = generate_valid_supplier_data("Test")
        payload = build_supplier_api_payload(
            data["step1"], data["step2"], data["step3"]
        )
        client.create_entry(payload)
    """
    ids = {**DEFAULT_SUPPLIER_FK_IDS, **(dropdown_ids or {})}

    # Helper: include FK field only if the value is not None
    # (API rejects null where it expects an integer)
    def _fk(key):
        val = ids.get(key)
        return val if val is not None else None

    # Build Additional Details stepper
    # NOTE: The live API response shows that for Additional Details stepper,
    # the fields are on the child object itself (NOT inside details[]).
    # The details[] array is empty for Additional Details.
    # However, for CREATE payloads, we put the fields inside details[]
    # which is the standard pattern. The API handles both forms.
    additional_details = {}
    additional_details["display_name_as"] = step1_data.get("contact_person", "") or None
    additional_details["office_no"] = step1_data.get("office_number", "") or None
    additional_details["is_gst_set_off"] = step1_data.get("is_gst_set_off", True)
    additional_details["is_tds_applicable"] = step1_data.get("is_tds_applicable", False)
    if _fk("payment_terms_ref_id") is not None:
        additional_details["payment_terms_ref_id"] = _fk("payment_terms_ref_id")
    if _fk("delivery_terms_ref_id") is not None:
        additional_details["delivery_terms_ref_id"] = _fk("delivery_terms_ref_id")
    if _fk("mode_of_delivery_ref_id") is not None:
        additional_details["mode_of_delivery_ref_id"] = _fk("mode_of_delivery_ref_id")

    # Build Address Details stepper details
    address_detail = {}
    if _fk("address_type") is not None:
        address_detail["address_type"] = _fk("address_type")
    if _fk("country_ref_id_id") is not None:
        address_detail["country_ref_id_id"] = _fk("country_ref_id_id")
    if _fk("state_ref_id_id") is not None:
        address_detail["state_ref_id_id"] = _fk("state_ref_id_id")
    if _fk("district_ref_id_id") is not None:
        address_detail["district_ref_id_id"] = _fk("district_ref_id_id")
    if _fk("sub_district_ref_id_id") is not None:
        address_detail["sub_district_ref_id_id"] = _fk("sub_district_ref_id_id")
    if _fk("village_ref_id_id") is not None:
        address_detail["village_ref_id_id"] = _fk("village_ref_id_id")
    address_detail["address"] = step2_data.get("address", "")
    # API returns pin_code as integer (e.g., 141001) — send as int
    pin = step2_data.get("pin_code", "")
    address_detail["pin_code"] = int(pin) if pin and pin.isdigit() else None
    address_detail["gstin"] = step2_data.get("gstin", "") or None
    address_detail["same_as_above"] = None  # API returns null, not False
    address_detail["address2"] = None
    address_detail["details"] = []

    # Build Bank Details stepper details
    bank_detail = {}
    bank_detail["bank_name"] = step3_data.get("bank_name", "") or None
    bank_detail["bank_branch_code"] = step3_data.get("branch", "") or None
    bank_detail["bank_ifsc_code"] = step3_data.get("ifsc_code", "") or None
    if _fk("account_type") is not None:
        bank_detail["account_type"] = _fk("account_type")
    bank_detail["bank_account_holder_name"] = step3_data.get("account_holder_name", "") or None
    # API returns bank_account_no as integer — send as int
    acct = step3_data.get("account_number", "")
    bank_detail["bank_account_no"] = int(acct) if acct and acct.isdigit() else None
    if _fk("bank_doc_id") is not None:
        bank_detail["bank_doc_id"] = _fk("bank_doc_id")
    bank_detail["bank_attachment_path"] = None  # API returns null, not ""
    bank_detail["details"] = []

    payload = {
        "id": "",
        "attribute_name": "Supplier",

        # Step 1 — Universal Fields (root level)
        "party_ref_id": None,  # API returns null — skip Party Reference
        "ownership_status_ref_id": ids["ownership_status_ref_id"],
        "name": step1_data.get("company_name", ""),
        "po_type_ref_id": ids["po_type_ref_id"],
        "email_id": step1_data.get("email", "") or None,
        # API returns mobile_no as integer — send as int
        "mobile_no": int(step1_data.get("phone_number", "0") or "0"),
        "default_currency_ref_id": ids["default_currency_ref_id"],
        "pan_no": step1_data.get("pan_number", ""),
        "is_msme_registered": step1_data.get("is_msme", False),
        "status": step1_data.get("status", True),
        # Additional root-level fields seen in live API response
        "vendor_code": None,
        "fax": None,
        "website_link": None,
        "attachment": None,
        "ref_id": None,
        "ref_type": None,

        # Children array with stepper objects (verified against live API)
        "children": [
            {
                "stepper_name": "Additional Details",
                "is_stepper": True,
                "details": [additional_details],
                "children": [],
            },
            {
                "stepper_name": "Address Details",
                "is_stepper": True,
                "details": [address_detail],
                "children": [],
            },
            {
                "stepper_name": "Bank Details",
                "is_stepper": True,
                "details": [bank_detail],
                "children": [],
            },
        ],
    }

    return payload


def generate_random_fk_ids() -> dict:
    """Generate a set of random FK IDs for dropdown variety.

    Each call returns a different combination so that batch-created
    suppliers don't all share the same ownership type, PO type, etc.
    This is what makes the data look realistic — a mix of Pvt Ltd,
    Proprietorship, Domestic, Import, etc.

    Returns:
        Dict with all FK ID keys, values randomly chosen from their pools.
    """
    return {
        "ownership_status_ref_id": random.choice(OWNERSHIP_STATUS_IDS),
        "po_type_ref_id": random.choice(PO_TYPE_IDS),
        "default_currency_ref_id": DEFAULT_CURRENCY_REF_ID,  # INR always
        "payment_terms_ref_id": random.choice(PAYMENT_TERMS_IDS),
        "delivery_terms_ref_id": random.choice(DELIVERY_TERMS_IDS),
        "mode_of_delivery_ref_id": random.choice(MODE_OF_DELIVERY_IDS),
        "address_type": random.choice(ADDRESS_TYPE_IDS),
        "country_ref_id_id": DEFAULT_COUNTRY_REF_ID,  # India always
        "account_type": random.choice(ACCOUNT_TYPE_IDS),
        "bank_doc_id": random.choice(BANK_DOC_IDS),
    }


def generate_supplier_api_payload(
    company_prefix=None,
    dropdown_ids: dict = None,
) -> dict:
    """
    One-shot: generate a complete Supplier API payload with random data.

    Automatically randomizes:
      - Address chain (state/district/taluka/village) from the pool
      - Ownership type (Pvt Ltd, Proprietorship, Partnership, Individual)
      - PO type (Domestic, Import)
      - Address type (Shipping, Billing)
      - Account type (Current, Saving)
      - Payment terms, delivery terms, mode of delivery
      - Bank proof type

    Each call produces a payload that looks different from the last.

    Args:
        company_prefix: If provided, forces old prefix_timestamp naming.
                        If None (default), generates realistic Indian names.
        dropdown_ids: Override specific FK IDs. Takes precedence over
                      random selection. Use to force specific values.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    data = generate_valid_supplier_data(company_prefix)

    # Merge: random FK IDs + random address chain + caller overrides
    ids = {
        **generate_random_fk_ids(),
        **get_random_address_chain(),
        **(dropdown_ids or {}),
    }

    return build_supplier_api_payload(
        data["step1"], data["step2"], data["step3"], ids
    )


def generate_supplier_api_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """
    Generate multiple unique Supplier API payloads for batch creation.

    Each payload gets a DIFFERENT random address chain automatically.

    Args:
        count: Number of payloads to generate.
        prefix: If provided, forces old prefix_timestamp naming.
                If None (default), generates realistic Indian names.
        dropdown_ids: Override default FK IDs for dropdowns.

    Returns:
        List of JSON payloads ready for batch_create().
    """
    payloads = []
    for i in range(count):
        payloads.append(
            generate_supplier_api_payload(prefix, dropdown_ids)
        )
    return payloads
