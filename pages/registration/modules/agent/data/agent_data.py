"""
agent_data.py
-------------
Test data generators for RhythmERP Agent screen.

Location: Registration > Agent
URL:      /#/dynamic-screens/Agent

FORM LAYOUT (multi-step STEPPER popup):
  Step 1 - Universal:
    - Agent Name             (text input,   required)
    - Phone Number           (text input,   required)
    - Email                  (text input,   required)

  Step 2 - Address Details:
    - Address Type           (mat-select,   required)
    - Country                (mat-select,   required)
    - State                  (mat-select,   required)
    - District               (mat-select,   required)
    - Taluka                 (mat-select,   optional)
    - Village                (mat-select,   optional)
    - Address                (text input,   required)
    - Pin Code               (text input,   required)
    - GST                    (text input,   optional)

  Step 3 - Payment Details:
    - Payment Terms          (mat-select,   optional)
    - Preferred Payment Method (mat-select, optional)

  Step 4 - Bank Details:
    - Bank Name              (text input,   required)
    - Branch                 (text input,   optional)
    - IFSC Code              (text input,   required)
    - Account Type           (mat-select,   required)
    - Account Holder Name    (text input,   required)
    - Account Number         (text input,   required)
    - Bank Proof             (file upload,  required)
    - Attachment             (file upload,  optional)
"""

import random
import string
from datetime import datetime


# --------------------------------------------------
# Core Data Generators
# --------------------------------------------------

def _rand_upper(n):
    """Generate n random uppercase ASCII letters."""
    return "".join(random.choices(string.ascii_uppercase, k=n))


def _rand_digits(n):
    """Generate n random digits as a string."""
    return "".join(random.choices(string.digits, k=n))


def _rand_alnum(n):
    """Generate n random alphanumeric characters."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def _rand_alpha(n):
    """Generate n random letters (mixed case)."""
    return "".join(random.choices(string.ascii_letters, k=n))


# --------------------------------------------------
# Agent Name Generators
# --------------------------------------------------

def generate_agent_name(prefix="AGT"):
    """Generate a valid Agent Name."""
    return f"{prefix}{_rand_upper(3)}{_rand_digits(4)}"


def generate_phone_number():
    """Generate a valid Indian phone number (10 digits)."""
    first = random.choice(["6", "7", "8", "9"])
    return first + _rand_digits(9)


def generate_email(prefix="agent"):
    """Generate a valid email address."""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "test.com"]
    return f"{prefix}{_rand_alnum(5)}@{random.choice(domains)}"


# --------------------------------------------------
# Address Data Generators
# --------------------------------------------------

def generate_address():
    """Generate a valid street address string."""
    streets = [
        "MG Road", "FC Road", "Station Road", "Main Street",
        "Temple Lane", "Lake View", "Hill Road", "Market Area",
    ]
    cities = ["Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Solapur"]
    return f"{random.randint(1, 500)} {random.choice(streets)} {random.choice(cities)}"


def generate_pin_code():
    """Generate a valid Indian PIN code (6 digits)."""
    return _rand_digits(6)


def generate_gst():
    """Generate a valid GST number format (15 chars)."""
    state_code = random.choice(["27", "22", "30", "09", "33"])
    pan = _rand_upper(4) + _rand_upper(1) + _rand_digits(4)
    entity = _rand_upper(1)
    z = random.choice(["Z", "z"])
    check = _rand_digits(1)
    return f"{state_code}{pan}{entity}{z}{check}"


# --------------------------------------------------
# Bank Detail Generators
# --------------------------------------------------

def generate_bank_name():
    """Generate a valid bank name for agent bank details."""
    banks = [
        "State Bank of India", "HDFC Bank", "ICICI Bank",
        "Axis Bank", "Punjab National Bank", "Bank of Baroda",
        "Canara Bank", "Union Bank of India",
    ]
    return random.choice(banks)


def generate_branch():
    """Generate a valid branch name."""
    locations = ["Mumbai Main", "Pune FC", "Nagpur Central", "Nashik Road"]
    return f"{random.choice(locations)} Branch"


def generate_ifsc_code(bank_prefix="SBIN"):
    """Generate a valid IFSC Code (11 chars: 4 letters + 0 + 6 alphanumeric)."""
    bank_code = bank_prefix[:4].upper().ljust(4, 'X')
    branch_code = _rand_digits(6)
    return f"{bank_code}0{branch_code}"


def generate_account_holder_name():
    """Generate a valid account holder name."""
    first_names = ["Rajesh", "Priya", "Amit", "Sunita", "Vikram", "Meera"]
    last_names = ["Patil", "Sharma", "Joshi", "Kulkarni", "Desai", "More"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_account_number():
    """Generate a valid account number (10-16 digits)."""
    return _rand_digits(random.randint(10, 16))


# --------------------------------------------------
# Validation Test Data Helpers
# --------------------------------------------------

def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds max)."""
    return "A" * 256


def generate_special_char_name():
    """Generate a name with special characters."""
    return "!@#$%^&*()Agent"


def generate_sql_injection():
    """SQL injection payload string."""
    return "'; DROP TABLE Agent; --"


def generate_xss_payload():
    """XSS payload string."""
    return "<script>alert('xss')</script>"


def generate_invalid_email():
    """Generate an invalid email address."""
    return "notanemail"


def generate_invalid_phone():
    """Generate an invalid phone number (too short)."""
    return "12345"


def generate_invalid_pin_code():
    """Generate an invalid PIN code (wrong length)."""
    return "1234"


def generate_invalid_ifsc():
    """Generate an invalid IFSC code (wrong length)."""
    return "SBIN123"


def generate_leading_trailing_spaces():
    """Agent Name with leading and trailing spaces."""
    return f"  {generate_agent_name()}  "


def generate_lowercase_agent_name():
    """Generate Agent Name with all lowercase."""
    return f"agent{_rand_digits(4)}".lower()


def generate_alpha_phone():
    """Generate phone number with letters (should be invalid)."""
    return "abcdefghij"


def generate_numeric_email():
    """Generate email without @ sign (should be invalid)."""
    return f"agent{_rand_digits(5)}gmail.com"


# --------------------------------------------------
# Complete Valid Data for Create
# --------------------------------------------------

def generate_valid_agent_data(prefix="AGT"):
    """Generate a complete dict of valid agent data for the Create form."""
    return {
        "agent_name": generate_agent_name(prefix),
        "phone_number": generate_phone_number(),
        "email": generate_email(prefix.lower()),
        "address": generate_valid_address_data(),
        "payment": generate_valid_payment_data(),
        "bank": generate_valid_bank_data(),
    }


def generate_valid_address_data():
    """Generate valid address data dict."""
    return {
        "address_type": "Permanent",
        "country": "India",
        "state": None,
        "district": None,
        "taluka": None,
        "village": None,
        "address": generate_address(),
        "pin_code": generate_pin_code(),
        "gst": generate_gst(),
    }


def generate_valid_payment_data():
    """Generate valid payment data dict."""
    return {
        "payment_terms": None,
        "preferred_payment_method": None,
    }


def generate_valid_bank_data():
    """Generate valid bank detail data dict."""
    return {
        "bank_name": generate_bank_name(),
        "branch": generate_branch(),
        "ifsc_code": generate_ifsc_code(),
        "account_type": None,
        "account_holder_name": generate_account_holder_name(),
        "account_number": generate_account_number(),
    }


def generate_valid_edit_data():
    """Generate valid data for Edit form modifications."""
    return {
        "agent_name": generate_agent_name("EDT"),
        "phone_number": generate_phone_number(),
        "email": generate_email("edit"),
        "address": generate_valid_address_data(),
        "payment": generate_valid_payment_data(),
        "bank": generate_valid_bank_data(),
    }


def generate_empty_data():
    """Return dict with all empty strings - for mandatory field validation."""
    return {
        "agent_name": "",
        "phone_number": "",
        "email": "",
        "address": {
            "address_type": "",
            "country": "India",
            "state": "",
            "district": "",
            "taluka": "",
            "village": "",
            "address": "",
            "pin_code": "",
            "gst": "",
        },
        "payment": {
            "payment_terms": "",
            "preferred_payment_method": "",
        },
        "bank": {
            "bank_name": "",
            "branch": "",
            "ifsc_code": "",
            "account_type": "",
            "account_holder_name": "",
            "account_number": "",
        },
    }


def generate_partial_required_data():
    """Return dict with only some required fields filled."""
    return {
        "agent_name": generate_agent_name("Partial"),
        "phone_number": "",
        "email": "",
        "address": {
            "address_type": "",
            "country": "India",
            "state": "",
            "district": "",
            "taluka": "",
            "village": "",
            "address": "",
            "pin_code": "",
            "gst": "",
        },
        "payment": {
            "payment_terms": "",
            "preferred_payment_method": "",
        },
        "bank": {
            "bank_name": "",
            "branch": "",
            "ifsc_code": "",
            "account_type": "",
            "account_holder_name": "",
            "account_number": "",
        },
    }


# --------------------------------------------------
# Expected Validation Messages
# --------------------------------------------------

VALIDATION_MSG_REQUIRED = "This field is required"
VALIDATION_MSG_INVALID_EMAIL = "Invalid Email"
VALIDATION_MSG_INVALID_PHONE = "Invalid Phone Number"
VALIDATION_MSG_INVALID_PIN = "Invalid Pin Code"
VALIDATION_MSG_INVALID_IFSC = "Invalid IFSC"
VALIDATION_MSG_INVALID_GST = "Invalid GST"

SWAL_TITLE_VALIDATION_FAILED = "Validation Failed"
SWAL_TITLE_SUCCESS = "Your record has been added successfully!"
SWAL_TITLE_UPDATED = "Your record has been updated successfully!"
