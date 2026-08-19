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

_AGENT_FIRST_NAMES = [
    "Rajesh", "Amit", "Suresh", "Mahesh", "Vijay", "Sanjay",
    "Deepak", "Manoj", "Ravi", "Kiran", "Prakash", "Ajay",
    "Rahul", "Sachin", "Rohit", "Arun", "Ganesh", "Mohan",
    "Priya", "Sunita", "Anita", "Meena", "Rekha", "Pooja",
    "Neha", "Swati", "Kavita", "Suman", "Geeta", "Seema",
]

_AGENT_LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Agarwal", "Gupta",
    "Jain", "Shah", "Mehta", "Reddy", "Nair", "Iyer",
    "Desai", "Kulkarni", "More", "Chavan", "Pawar", "Jadhav",
    "Rao", "Hegde", "Shetty", "Bhat", "Pillai", "Varma",
]

_generated_agent_names = set()

def generate_agent_name():
    """Generate a realistic Indian agent name (letters and spaces only)."""
    for _ in range(200):
        first = random.choice(_AGENT_FIRST_NAMES)
        last = random.choice(_AGENT_LAST_NAMES)
        name = f"{first} {last}"
        if name not in _generated_agent_names:
            _generated_agent_names.add(name)
            return name
    # Fallback — unlikely to reach
    return f"{random.choice(_AGENT_FIRST_NAMES)} {random.choice(_AGENT_LAST_NAMES)}"


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

def generate_valid_agent_data():
    """Generate a complete dict of valid agent data for the Create form."""
    return {
        "agent_name": generate_agent_name(),
        "phone_number": generate_phone_number(),
        "email": generate_email("agent"),
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
        "agent_name": generate_agent_name(),
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


# ──────────────────────────────────────────────
# FK ID pools
# ──────────────────────────────────────────────

ADDRESS_TYPE_IDS = [43, 42]
# 43 = Shipping, 42 = Billing

COUNTRY_REF_ID = 8       # India
STATE_REF_IDS = [98]      # Maharashtra
DISTRICT_REF_IDS = [479]  # Pune
SUB_DISTRICT_REF_IDS = [11462]
VILLAGE_REF_IDS = [None]
PINCODE_REF_IDS = [2148]

PAYMENT_TERMS_IDS = [26, 27, 131, 549, 550, 551]
# 26 = 30 Days, 27 = 60 Days, 131 = Immediate

PREFERRED_PAYMENT_METHOD_IDS = [1, 2, 3]
# 1 = Cash, 2 = Cheque, 3 = Bank Transfer

ACCOUNT_TYPE_IDS = [1849, 1850]
# 1849 = Current, 1850 = Saving

BANK_DOC_IDS = [36, 35, 1883]
# 36 = Cancelled Cheque, 35 = Passbook, 1883 = Bank Statement

DEFAULT_AGENT_FK_IDS = {
    "shipping_address_type": 43,
    "billing_address_type": 42,
    "country_ref_id_id": COUNTRY_REF_ID,
    "state_ref_id_id": STATE_REF_IDS[0],
    "district_ref_id_id": DISTRICT_REF_IDS[0],
    "sub_district_ref_id_id": SUB_DISTRICT_REF_IDS[0],
    "village_ref_id_id": VILLAGE_REF_IDS[0],
    "payment_terms_ref_id": PAYMENT_TERMS_IDS[0],
    "preferred_payment_method_ref_id": PREFERRED_PAYMENT_METHOD_IDS[0],
    "account_type": ACCOUNT_TYPE_IDS[0],
    "bank_doc_id": BANK_DOC_IDS[0],
}


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────

def _build_address_row(addr_type_fk_key: str, data: dict, ids: dict) -> dict:
    """Build a single address detail row for the Address Details stepper."""
    row = {
        "address_type": ids.get(addr_type_fk_key),
        "country_ref_id_id": ids.get("country_ref_id_id"),
        "state_ref_id_id": ids.get("state_ref_id_id"),
        "district_ref_id_id": ids.get("district_ref_id_id"),
        "sub_district_ref_id_id": ids.get("sub_district_ref_id_id"),
        "village_ref_id_id": ids.get("village_ref_id_id"),
        "address": data.get("address", "") or None,
        "pin_code": int(data.get("pin_code", "0") or "0") or None,
        "gstin": None,
        "address2": None,
        "details": [],
    }
    return row


def build_agent_api_payload(data: dict, fk_ids: dict = None) -> dict:
    """Build the JSON payload for POST /core/dynamic-screen-wrapper/Agent/.

    Args:
        data: Dict from generate_valid_agent_data().
        fk_ids: Optional FK ID overrides.

    Returns:
        Complete JSON payload dict ready for POST.
    """
    ids = {**DEFAULT_AGENT_FK_IDS, **(fk_ids or {})}

    # Address Details — always shipping + billing rows
    shipping = _build_address_row("shipping_address_type", data.get("address", {}), ids)
    billing = _build_address_row("billing_address_type", data.get("address", {}), ids)

    # Bank Details — one row
    bank_data = data.get("bank", {})
    bank_detail = {
        "bank_name": bank_data.get("bank_name") or None,
        "bank_branch_code": bank_data.get("branch") or None,
        "bank_ifsc_code": bank_data.get("ifsc_code") or None,
        "account_type": ids.get("account_type"),
        "bank_account_holder_name": bank_data.get("account_holder_name") or None,
        "bank_account_no": int(bank_data.get("account_number", "0") or "0") or None,
        "bank_doc_id": ids.get("bank_doc_id"),
        "bank_attachment_path": None,
        "details": [],
    }

    payload = {
        "id": "",
        "attribute_name": "Agent",
        "details": [],
        "children": [
            {
                "stepper_name": "Address Details",
                "is_stepper": True,
                "details": [shipping, billing],
                "children": [],
            },
            {
                "stepper_name": "Payment Details",
                "is_stepper": True,
                "details": [],
                "children": [],
                "id": "",
                "display_name_as": None,
                "office_no": None,
                "delivery_terms_ref_id": None,
                "is_tds_applicable": None,
                "preferred_payment_method_ref_id": ids.get("preferred_payment_method_ref_id"),
                "deposit": None,
                "gst_registration_type": None,
                "mode_of_delivery_ref_id": None,
                "payment_terms_ref_id": ids.get("payment_terms_ref_id"),
                "courier_terms_ref_id": None,
                "quantity_tolerance": None,
                "gst_registration_status": None,
                "is_gst_set_off": False,
                "customer_type_ref_id": None,
                "customer_status": None,
                "supply_type_ref_id": None,
                "sale_type_ref_id": None,
                "ownership_status_ref_id": None,
                "packing_material_ref_id": None,
                "status": None,
            },
            {
                "stepper_name": "Bank Details",
                "is_stepper": True,
                "details": [bank_detail],
                "children": [],
            },
        ],
        "party_ref_id": None,
        "name": data.get("agent_name", ""),
        "mobile_no": int(data.get("phone_number", "0") or "0"),
        "email_id": data.get("email", "") or None,
        "status": True,
    }

    return payload


def generate_agent_api_payload(fk_ids: dict = None) -> dict:
    """One-shot: generate a randomized Agent API payload with a real human name."""
    data = generate_valid_agent_data()
    return build_agent_api_payload(data, fk_ids)


def generate_batch_payloads(count: int = 10, **kwargs) -> list:
    """Generate multiple unique Agent API payloads."""
    return [generate_agent_api_payload(**kwargs) for _ in range(count)]


# ──────────────────────────────────────────────
# SweetAlert titles (used by UI tests)
# ──────────────────────────────────────────────
SWAL_TITLE_SUCCESS = "Your record has been added successfully!"
SWAL_TITLE_VALIDATION_FAILED = "Validation Failed"
SWAL_TITLE_UPDATED = "Your record has been updated successfully!"


def generate_ui_form_data():
    """Tenant-universal form data for fill_form(). Cascade dropdowns set to None for auto-pick."""
    return {
        "agent_name": generate_agent_name(),
        "phone_number": generate_phone_number(),
        "email": generate_email("agent"),
        # Address cascade — auto-picked by UI (tenant-universal)
        "country": None,
        "state": None,
        "district": None,
        "taluka": None,
        "village": None,
        "address": generate_address(),
        "pin_code": generate_pin_code(),
        # Payment — optional, skip
        "preferred_payment_method": None,
        # Bank
        "bank_name": generate_bank_name(),
        "ifsc_code": generate_ifsc_code(),
        "account_type": None,
        "account_holder_name": generate_account_holder_name(),
        "account_number": generate_account_number(),
    }
