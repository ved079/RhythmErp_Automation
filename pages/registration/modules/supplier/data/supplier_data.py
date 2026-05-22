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

LOGIN: Rular@admin.com / Rular@12345678 / Facility: RuralLife Producer Company (index 0)
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Unique-name generators
# ──────────────────────────────────────────────

def generate_company_name(prefix="AutoSupplier"):
    """Generate a unique company name with prefix and timestamp."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{ts}_{rand}"


def generate_email(prefix="autosp"):
    """Generate a unique email address."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{ts}_{rand}@supplier-test.com"


def generate_phone():
    """Generate a valid 10-digit Indian phone number."""
    return f"9{random.randint(100000000, 999999999)}"


def generate_pan():
    """Generate a valid Indian PAN number (5 letters + 4 digits + 1 letter).
    Format: ABCDE1234F
    """
    letters = random.choices(string.ascii_uppercase, k=5)
    digits = random.choices(string.digits, k=4)
    last_letter = random.choice(string.ascii_uppercase)
    return f"{''.join(letters)}{''.join(digits)}{last_letter}"


def generate_contact_person(prefix="Contact"):
    """Generate a contact person name."""
    ts = datetime.now().strftime("%H%M%S")
    return f"{prefix}_{ts}"


def generate_office_number():
    """Generate an office number string."""
    return f"0{random.randint(20, 29)}-{random.randint(10000000, 99999999)}"


def generate_ifsc():
    """Generate a valid IFSC code (4 letters + 0 + 6 alphanumeric)."""
    bank_code = "".join(random.choices(string.ascii_uppercase, k=4))
    branch_code = "".join(random.choices(string.digits, k=6))
    return f"{bank_code}0{branch_code}"


def generate_account_number():
    """Generate a random bank account number."""
    return f"{random.randint(100000000000, 999999999999)}"


def generate_gstin():
    """Generate a valid Indian GSTIN (15 chars: 2 digits + PAN + 1 char + 1 char + 1 digit)."""
    state_code = f"{random.randint(1, 37):02d}"
    pan_part = generate_pan()
    entity_num = str(random.randint(1, 9))
    default_char = "Z"
    check_code = str(random.randint(0, 9))
    return f"{state_code}{pan_part}{entity_num}{default_char}{check_code}"


def generate_pin_code():
    """Generate a valid 6-digit Indian pin code."""
    return f"{random.randint(100000, 999999)}"


def generate_address():
    """Generate a random address line."""
    streets = [
        "MG Road", "Station Road", "Main Street", "Park Avenue",
        "Gandhi Nagar", "Jawahar Colony", "Industrial Area",
        "Auto Test Lane", "Supply Chain Road", "Vendor Street"
    ]
    return f"{random.randint(1, 999)} {random.choice(streets)}"


# ──────────────────────────────────────────────
# Complete Valid Data for Create (Step 1)
# ──────────────────────────────────────────────

def generate_valid_step1_data(company_prefix="AutoSupplier"):
    """Generate complete valid data for Step 1 (Universal + Additional Details).
    Dropdown values set to None — must be populated from live UI at runtime.
    """
    return {
        # Universal fields
        "party_reference": "",         # Optional — skip by default
        "ownership_status": None,      # Pick from live UI (REQUIRED)
        "company_name": generate_company_name(company_prefix),
        "po_type": None,               # Pick from live UI (REQUIRED): Domestic/Import
        "email": generate_email("sp"),
        "phone_number": generate_phone(),
        "default_currency": "INR",      # Pick from live UI (REQUIRED)
        "pan_number": generate_pan(),
        # Toggle switches
        "is_msme": False,              # Default: No
        "status": True,                # Default: Active
        # Additional Details
        "is_gst_set_off": True,        # Default: Yes
        "is_tds_applicable": False,    # Default: No
        "contact_person": "Contact Person",
        "office_number": "",
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
    }


def generate_valid_step3_data():
    """Generate valid data for Step 3 (Bank Details)."""
    return {
        "bank_name": "Test Bank",
        "branch": f"Branch {random.choice(['Main', 'City', 'Central', 'West', 'East'])}",
        "ifsc_code": generate_ifsc(),
        "account_type": None,          # Pick from live UI (optional): Current/Saving
        "account_holder_name": "Account Holder",
        "account_number": generate_account_number(),
        "bank_proof": None,            # Pick from live UI (REQUIRED): Cancelled Cheque/Passbook
        "attachment_path": None,       # File path for upload (optional)
    }


def generate_valid_supplier_data(company_prefix="AutoSupplier"):
    """Generate complete valid data for ALL 3 steps.
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
        "company_name": generate_company_name("EditSup"),
        "email": generate_email("edit"),
        "phone_number": generate_phone(),
        "pan_number": generate_pan(),
        "contact_person": "Contact Person",
        "office_number": "",
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