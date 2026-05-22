"""
customer_data.py
----------------
Test data generators for RhythmERP Customer screen.

Location: Registration > Customer
URL:      /#/dynamic-screens/Customer/Customer

FORM LAYOUT (3-step horizontal stepper inside popup):

  UNIVERSAL FIELDS (always visible above stepper):
    - Party Reference        (mat-select,   optional)
    - Ownership Status       (mat-select,   required)
    - Company Name           (text input,   required, maxlength=255)
    - Sale Type              (mat-select,   required)
    - Supply Type            (mat-select,   required)
    - Transaction Currency   (mat-select,   required)
    - Email                  (text input,   required, maxlength=255)
    - Phone Number           (number input, required)
    - PAN Number             (text input,   required, maxlength=255)

  TOGGLE SWITCHES:
    - Status                 (app-slide-toggle-v2, Active/Inactive, default Active, OUTSIDE stepper)
    - Is TDS Applicable      (app-slide-toggle-v2, No/Yes, default No, INSIDE stepper step 0)

  Step 0 — "Additional Details":
    - Contact Person Name    (text input,   optional, maxlength=255)
    - Office Number          (text input,   optional, maxlength=255)
    - Preferred Payment Method (mat-select, optional)
    - Gst Registration Type  (mat-select,   optional)
    - Payment Terms          (mat-select,   optional)
    - Delivery Terms         (mat-select,   optional)
    - Mode Of Delivery       (mat-select,   optional)
    - Courier Terms          (mat-select,   optional)
    - Deposite               (number input, optional, default=0)
    - Quantity Tolerance     (number input, optional)
    - Rate Tolerance         (number input, optional)

  Step 1 — "Customer Details" (Address Grid):
    Grid table with columns: Action, Address Type*, Country*, State*,
    District*, Taluka*, Village, Address*, Pin Code, GSTIN
    Starts with 1 default empty row; Add (+) button to add more rows
    Cascading dropdowns: Country -> State -> District -> Taluka -> Village

  Step 2 — "Customer Bank Details" (Bank Grid):
    Grid table with columns: Action, Bank Name*, Branch*, IFSC Code,
    Account Type*, Account Holder Name*, Account Number*, Bank Proof*, Attachment
    Starts with 1 default empty row; Add (+) button to add more rows

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - Toggle switches use <app-slide-toggle-v2> with <span class="main-label">
    and <div class="switch-wrapper compact">
  - BUG-001: Browser-clicked mat-select does NOT update Angular reactive form
    model — must use JS value-setter + dispatchEvent pattern
  - BUG-002: Stepper allows advancing even with empty required fields
  - Unique PAN Number validation (server-side)
  - Email validates with "Invalid Email" message
  - Inputs use name attribute for selection (e.g., name="Company Name")
  - Dropdowns use mat-label -> ancestor mat-form-field -> mat-select pattern
  - Address grid has cascading dropdowns (Country -> State -> District -> Taluka -> Village)
  - Stepper is non-linear: Next button does NOT validate required fields
  - Actual validation happens only on Submit button click
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_company_name(prefix="AutoCust"):
    """Generate a random company name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_email(prefix="autocust"):
    """Generate a random valid email address."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}@testmail.com"


def generate_phone_number():
    """Generate a random 10-digit Indian phone number starting with 9/8/7/6."""
    first_digit = random.choice(["9", "8", "7", "6"])
    rest = "".join([str(random.randint(0, 9)) for _ in range(9)])
    return f"{first_digit}{rest}"


def generate_pan_number():
    """Generate a random PAN number in valid Indian format: ABCDE1234F
    5 uppercase letters + 4 digits + 1 uppercase letter.
    """
    letters = "".join([random.choice(string.ascii_uppercase) for _ in range(5)])
    digits = "".join([str(random.randint(0, 9)) for _ in range(4)])
    last_letter = random.choice(string.ascii_uppercase)
    return f"{letters}{digits}{last_letter}"


def generate_address():
    """Generate a random address string."""
    numbers = ["123", "456", "789", "101", "202", "303"]
    streets = ["MG Road", "Station Road", "Main Street", "Park Avenue",
               "Laxmi Nagar", "Shivaji Path", "Gandhi Chowk", "Nehru Road"]
    areas = ["Pune", "Mumbai", "Nagpur", "Nashik", "Kolhapur", "Aurangabad"]
    return f"{random.choice(numbers)} {random.choice(streets)}, {random.choice(areas)}"


def generate_pin_code():
    """Generate a random 6-digit Indian pin code."""
    return f"{random.randint(4, 4)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"


def generate_gstin():
    """Generate a random GSTIN-like string (15 chars): 22AAAAA0000A1Z5 format."""
    state_code = f"{random.randint(1, 37):02d}"
    pan = generate_pan_number()
    entity_num = str(random.randint(1, 9))
    z = "Z"
    check = str(random.randint(0, 9))
    return f"{state_code}{pan}{entity_num}{z}{check}"


def generate_ifsc_code():
    """Generate a random IFSC code: SBIN0001234 format (4 letters + 0 + 6 digits)."""
    bank_code = "".join([random.choice(string.ascii_uppercase) for _ in range(4)])
    branch_code = f"0{random.randint(100000, 999999)}"
    return f"{bank_code}{branch_code}"


def generate_account_number():
    """Generate a random bank account number (10-16 digits)."""
    length = random.randint(10, 16)
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


def generate_deposite():
    """Generate a random deposit amount (positive number)."""
    return str(round(random.uniform(100, 100000), 2))


def generate_quantity_tolerance():
    """Generate a random quantity tolerance value."""
    return str(round(random.uniform(0, 100), 2))


def generate_rate_tolerance():
    """Generate a random rate tolerance value."""
    return str(round(random.uniform(0, 100), 2))


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_customer_data(name_prefix="AutoCust"):
    """Generate a complete dict of valid customer data for Create form.
    Dropdown values set to None — must be populated from live UI at runtime.
    """
    return {
        # Universal Fields
        "party_reference": None,            # Pick from live UI (optional)
        "ownership_status": None,           # Pick from live UI (REQUIRED)
        "company_name": generate_company_name(name_prefix),
        "sale_type": None,                  # Pick from live UI (REQUIRED)
        "supply_type": None,                # Pick from live UI (REQUIRED)
        "transaction_currency": "INR",       # Pick from live UI (REQUIRED)
        "email": generate_email(name_prefix.lower()),
        "phone_number": generate_phone_number(),
        "pan_number": generate_pan_number(),
        # Toggle switches
        "status": True,                     # Active (default)
        "is_tds_applicable": False,         # No (default)
        # Step 0: Additional Details
        "contact_person_name": f"Contact_{datetime.now().strftime('%H%M%S')}",
        "office_number": f"020{random.randint(10000000, 99999999)}",
        "preferred_payment_method": None,   # Pick from live UI (optional)
        "gst_registration_type": None,      # Pick from live UI (optional)
        "payment_terms": None,              # Pick from live UI (optional)
        "delivery_terms": None,             # Pick from live UI (optional)
        "mode_of_delivery": None,           # Pick from live UI (optional)
        "courier_terms": None,              # Pick from live UI (optional)
        "deposite": generate_deposite(),
        "quantity_tolerance": generate_quantity_tolerance(),
        "rate_tolerance": generate_rate_tolerance(),
    }


def generate_valid_address_row():
    """Generate valid data for one address row in Step 1 (Customer Details).
    Dropdown values set to None — the page object will pick a random valid
    option from the live UI at runtime. Country is set to 'India' because
    cascading dropdowns (State/District/Taluka/Village) only work for India.
    """
    return {
        "address_type": None,               # Pick random from live UI (REQUIRED)
        "country": "India",                 # MUST be India for cascading to work
        "state": None,                      # Pick random from live UI (REQUIRED, cascading)
        "district": None,                   # Pick random from live UI (REQUIRED, cascading)
        "taluka": None,                     # Pick random from live UI (REQUIRED, cascading)
        "village": None,                    # Pick random from live UI (optional, cascading)
        "address": generate_address(),
        "pin_code": generate_pin_code(),
        "gstin": generate_gstin(),
    }


def generate_valid_bank_row():
    """Generate valid data for one bank row in Step 2 (Customer Bank Details).
    Dropdown values set to None — must be populated from live UI at runtime.
    """
    return {
        "bank_name": f"Bank_{datetime.now().strftime('%H%M%S')}",
        "branch": f"Branch_{random.randint(100, 999)}",
        "ifsc_code": generate_ifsc_code(),
        "account_type": None,               # Pick from live UI (REQUIRED: Current/Saving)
        "account_holder_name": f"Holder_{datetime.now().strftime('%H%M%S')}",
        "account_number": generate_account_number(),
        "bank_proof": None,                 # Pick from live UI (REQUIRED: Cancelled Cheque/Passbook)
        "attachment": None,                 # File path (optional)
    }


def generate_full_valid_customer_data(name_prefix="AutoCust"):
    """Generate complete valid data for ALL 3 steps.
    Used for end-to-end happy path tests.
    """
    data = generate_valid_customer_data(name_prefix)
    data["address_rows"] = [generate_valid_address_row()]
    data["bank_rows"] = [generate_valid_bank_row()]
    return data


def generate_valid_edit_data(name_prefix="EditCust"):
    """Generate valid data for Edit form — only fields we want to change."""
    return {
        "company_name": generate_company_name(name_prefix),
        "email": generate_email(name_prefix.lower()),
        "phone_number": generate_phone_number(),
        "pan_number": generate_pan_number(),
        # Toggle switches — flip for edit testing
        "status": True,
        "is_tds_applicable": False,
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds maxlength 255)."""
    return "A" * 256


def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_special_char_name():
    """Generate a company name with special characters."""
    return "Test!@#$%^&*()_+-=[]{}|;':\",./<>?"


def generate_sql_injection():
    """Generate an SQL injection string."""
    return "'; DROP TABLE customers; --"


def generate_xss_payload():
    """Generate an XSS payload string."""
    return "<script>alert('xss')</script>"


def generate_invalid_email():
    """Generate an invalid email address."""
    return "invalid-email"


def generate_email_no_domain():
    """Generate an email with no domain."""
    return "test@"


def generate_email_no_at():
    """Generate an email without @ sign."""
    return "testexample.com"


def generate_negative_phone():
    """Return a negative phone number."""
    return "-9876543210"


def generate_alpha_phone():
    """Return alphabetic characters for phone."""
    return "abcdefghij"


def generate_special_char_phone():
    """Return special characters for phone."""
    return "!@#$%^&*()"


def generate_negative_deposite():
    """Return a negative deposit value."""
    return f"-{round(random.uniform(0.1, 1000.0), 2)}"


def generate_zero_deposite():
    """Return zero for deposit."""
    return "0"


def generate_alpha_deposite():
    """Return alphabetic characters for deposit."""
    return "abcDEF"


def generate_invalid_pan():
    """Return an invalid PAN number (wrong format)."""
    return "1234567890"


def generate_short_pan():
    """Return a PAN that's too short."""
    return "ABC12"


def generate_duplicate_pan_data(existing_pan):
    """Return valid data using an existing PAN — for duplicate PAN test.
    PAN must be unique across customers.
    """
    data = generate_full_valid_customer_data("DupPan")
    data["pan_number"] = existing_pan
    return data


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "party_reference": "",
        "ownership_status": "",
        "company_name": "",
        "sale_type": "",
        "supply_type": "",
        "transaction_currency": "",
        "email": "",
        "phone_number": "",
        "pan_number": "",
    }


def generate_company_name_only_data(prefix="NameOnly"):
    """Return dict with only Company Name filled — for partial field validation."""
    return {
        "company_name": generate_company_name(prefix),
        "ownership_status": "",
        "sale_type": "",
        "supply_type": "",
        "transaction_currency": "",
        "email": "",
        "phone_number": "",
        "pan_number": "",
    }


def generate_pan_with_spaces():
    """Return a PAN with leading/trailing spaces."""
    return f"  {generate_pan_number()}  "


def generate_pan_with_special_chars():
    """Return a PAN with special characters."""
    return "ABCD!@#4F"


def generate_email_with_spaces():
    """Return an email with leading/trailing spaces."""
    return f"  {generate_email()}  "


def generate_long_phone():
    """Return a very long phone number (20+ digits)."""
    return "9" * 20


def generate_emoji_name():
    """Return a company name with emojis."""
    return "Test Company \U0001f600\U0001f389"


def generate_unicode_name():
    """Return a company name with Unicode characters."""
    return "\u6d4b\u8bd5\u516c\u53f8 \u0422\u0435\u0441\u0442 \u30c6\u30b9\u30c8"
