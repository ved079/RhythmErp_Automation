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
    - Copy From Existing Party (app-slide-toggle-v2, No/Yes, default No, OUTSIDE stepper)
    - Status                 (app-slide-toggle-v2, Active/Inactive, default Active, OUTSIDE stepper)
    - Is TDS Applicable      (app-slide-toggle-v2, No/Yes, default No, INSIDE stepper step 0)

  Step 0 — "Additional Details":
    - Contact Person Name    (text input,   optional, maxlength=255)
    - Office Number          (text input,   optional, maxlength=255)
    - Preferred Payment Method (mat-select, optional)
    - Gst Registration Status (mat-select,  optional, Registered/Unregistered)
    - Gst Registration Type  (mat-select,   optional, Composit/Regular)
    - Payment Terms          (mat-select,   optional)
    - Delivery Terms         (mat-select,   optional)
    - Mode Of Delivery       (mat-select,   optional)
    - Courier Terms          (mat-select,   optional)
    - Deposite               (number input, optional, default=0)
    - Quantity Tolerance     (number input, optional)
    - Rate Tolerance         (number input, optional)

  Step 1 — "Address Details" (Address Grid):
    Grid table with columns: Action, Same as Above, Address Type*, Country*,
    State*, District*, Taluka*, Village, Address*, Pin Code*, GSTIN
    Starts with 1 default empty row; Add (+) button to add more rows
    Cascading dropdowns: Country -> State -> District -> Taluka -> Village

  Step 2 — "Customer Bank Details" (Bank Grid):
    Grid table with columns: Action, Bank Name*, Branch*, IFSC Code,
    Account Type*, Account Holder Name*, Account Number*, Bank Proof*, Attachment
    Starts with 1 default empty row; Add (+) button to add more rows
    NOTE: Account Type and Bank Proof are now required=True in the ERP UI

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

def generate_company_name(prefix=None):
    """
    Generate a realistic, unique-looking customer company name without numeric suffixes.
    Uses large component pools and 7 different name patterns to maximize variety.
    Collision probability is extremely low (millions of combinations).
    Different from supplier data – uses retail/consumer-oriented words.
    """
    # ---- Component lists (customer-specific) ----
    prefixes = [
        "Shree", "Sai", "Om", "Guru", "Sri", "Mahalaxmi", "Nav", "Bharat",
        "New", "Prime", "Royal", "Elite", "Global", "United", "Asian",
        "Indian", "Modern", "Classic", "Evergreen", "Golden", "Silver", "Bright",
        "Sunrise", "Lotus", "Neelgagan", "City", "Metro", "Star", "Supreme"
    ]
    core_names = [
        "Traders", "General Store", "Supermarket", "Mart", "Bazaar", "Emporium",
        "Plaza", "Galleria", "Outlet", "Showroom", "Centre", "Point", "Corner",
        "Depot", "Junction", "Square", "Tower", "House", "Home", "Style", "Trends"
    ]
    places = [
        "City", "Town", "Market", "High Street", "Main Road", "Station Road",
        "Gandhi Nagar", "Laxmi Nagar", "Shivaji Path", "Nehru Place", "Connaught",
        "Bandra", "Andheri", "Koramangala", "Indiranagar", "Salt Lake", "Rajajinagar"
    ]
    business_types = [
        "Electronics", "Furniture", "Clothing", "Footwear", "Jewelry", "Gifts",
        "Books", "Stationery", "Hardware", "Medical", "Pharmacy", "Optical",
        "Mobile", "Computer", "Kitchen", "Home Decor", "Sports", "Toys", "Baby Care"
    ]
    suffixes = [
        "Enterprises", "Industries", "Corporation", "Private Limited", "Limited",
        "Traders", "Ventures", "Group", "Associates", "Solutions", "Services",
        "Agencies", "Suppliers", "Merchants", "Dealers", "Distributors", "Store",
        "Mart", "Supermarket", "Hypermarket", "Outlet", "Showroom", "Plaza"
    ]
    connectors = ["and", "&", "of"]

    # ---- Name patterns (customer-oriented) ----
    patterns = [
        # Pattern 1: Prefix + Core Name + Business Type (e.g., "Shree Traders Electronics")
        lambda: f"{random.choice(prefixes)} {random.choice(core_names)} {random.choice(business_types)}",
        # Pattern 2: Place + Business Type + Suffix (e.g., "City Electronics Enterprises")
        lambda: f"{random.choice(places)} {random.choice(business_types)} {random.choice(suffixes)}",
        # Pattern 3: Prefix + Place + Business Type (e.g., "Shree City Electronics")
        lambda: f"{random.choice(prefixes)} {random.choice(places)} {random.choice(business_types)}",
        # Pattern 4: Place + Suffix (e.g., "City Enterprises")
        lambda: f"{random.choice(places)} {random.choice(suffixes)}",
        # Pattern 5: Prefix + Core Name + Suffix (e.g., "Om Traders Private Limited")
        lambda: f"{random.choice(prefixes)} {random.choice(core_names)} {random.choice(suffixes)}",
        # Pattern 6: Business Type + Connector + Business Type + Suffix (e.g., "Electronics and Furniture Mart")
        lambda: f"{random.choice(business_types)} {random.choice(connectors)} {random.choice(business_types)} {random.choice(suffixes)}",
        # Pattern 7: Core Name + of + Place (e.g., "Traders of Connaught")
        lambda: f"{random.choice(core_names)} {random.choice(connectors)} {random.choice(places)}",
    ]

    pattern = random.choice(patterns)
    name = pattern()
    # Ensure name length is not too long (max 255 as per spec)
    if len(name) > 255:
        # fallback to a shorter pattern
        return f"{random.choice(prefixes)} {random.choice(core_names)} {random.choice(suffixes)}"
    return name


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
        "company_name": generate_company_name(),
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
        "contact_person_name": "Contact Person",
        "office_number": "",
        "preferred_payment_method": None,   # Pick from live UI (optional)
        "gst_registration_status": None,    # Pick from live UI (optional, Registered/Unregistered)
        "gst_registration_type": None,      # Pick from live UI (optional, Composit/Regular)
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
        "bank_name": "Bank",
        "branch": "Branch",
        "ifsc_code": generate_ifsc_code(),
        "account_type": None,               # Pick from live UI (REQUIRED in ERP UI: Current/Saving)
        "account_holder_name": "Jason Holder",
        "account_number": generate_account_number(),
        "bank_proof": None,                 # Pick from live UI (REQUIRED in ERP UI: Cancelled Cheque/Passbook/Bank Statement)
        "attachment": None,                 # File path (optional)
    }


def generate_full_valid_customer_data(name_prefix="AutoCust"):
    """Generate complete valid data for ALL 3 steps.
    Used for end-to-end happy path tests.
    """
    data = generate_valid_customer_data(name_prefix)
    data["address_rows"] = [
        generate_valid_address_row(),   # Shipping (row 0, default)
        generate_valid_address_row(),   # Billing  (row 1, added via inline button)
    ]
    # Force address types so row 0 = Shipping, row 1 = Billing
    data["address_rows"][0]["address_type"] = "Shipping"
    data["address_rows"][1]["address_type"] = "Billing"
    data["bank_rows"] = [generate_valid_bank_row()]
    return data


def generate_valid_edit_data(name_prefix="EditCust"):
    """Generate valid data for Edit form — only fields we want to change."""
    return {
        "company_name": generate_company_name(),
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
        "company_name": generate_company_name(),
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


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the existing UI data format into the JSON payload
# that POST /core/dynamic-screen-wrapper/ expects.
#
# CUSTOMER SCREEN STRUCTURE (from live API):
#   {
#     "id": "",
#     "attribute_name": "Customer",
#     <root-level fields>,
#     "children": [
#       {
#         "stepper_name": "Additional Details",
#         "is_stepper": true,
#         "details": [],          <-- NOTE: empty! Fields on child object itself
#         "children": [],
#         <Additional Details fields directly here>
#       },
#       {
#         "stepper_name": "Address Details",
#         "is_stepper": true,
#         "details": [{ <Address row 1> }],
#         "children": []
#       },
#       {
#         "stepper_name": "Customer Bank Details",
#         "is_stepper": true,
#         "details": [{ <Bank row 1> }],
#         "children": []
#       }
#     ]
#   }
#
# KEY DIFFERENCE from Supplier:
#   - Additional Details fields live ON the child object, NOT inside details[]
#   - Root has supply_type_ref_id + sale_type_ref_id (instead of po_type_ref_id)
#   - Extra fields: customer_type_ref_id, preferred_payment_method_ref_id,
#     courier_terms_ref_id, gst_registration_type, deposit, qty/rate tolerance
#
# FIELD KEY MAPPING (verified 2026-06-01 from live API):
#
#   Root-level:
#     party_reference        -> party_ref_id (null)
#     ownership_status       -> ownership_status_ref_id (FK)
#     company_name           -> name
#     supply_type            -> supply_type_ref_id (FK)
#     sale_type              -> sale_type_ref_id (FK)
#     transaction_currency   -> default_currency_ref_id (FK)
#     email                  -> email_id
#     phone_number           -> mobile_no (int)
#     pan_number             -> pan_no
#     status                 -> status (boolean)
#
#   Additional Details (on child[0] directly, NOT in details[]):
#     contact_person_name    -> display_name_as
#     office_number          -> office_no
#     preferred_payment_method -> preferred_payment_method_ref_id (FK)
#     gst_registration_type  -> gst_registration_type (FK)
#     payment_terms          -> payment_terms_ref_id (FK)
#     delivery_terms         -> delivery_terms_ref_id (FK)
#     mode_of_delivery       -> mode_of_delivery_ref_id (FK)
#     courier_terms          -> courier_terms_ref_id (FK)
#     deposite               -> deposit (float)
#     quantity_tolerance     -> quantity_tolerance (float)
#     rate_tolerance         -> rate_tolerance (float)
#     is_tds_applicable      -> is_tds_applicable (boolean)
#     is_gst_set_off         -> is_gst_set_off (boolean)
#     customer_type          -> customer_type_ref_id (FK)
#     customer_status        -> customer_status (FK)
#     packing_material       -> packing_material_ref_id (FK)
#
#   Customer Details (in child[1].details[0]):
#     Same as Supplier address fields
#
#   Customer Bank Details (in child[2].details[0]):
#     Same as Supplier bank fields
# ──────────────────────────────────────────────

# Dropdown FK ID pools (verified on tenant 599)
OWNERSHIP_STATUS_IDS = [5, 6, 7, 8, 9, 1262, 1263, 1853]
#   5 = Cooperative Society, 6 = Limited, 7 = Private Limited Company,
#   8 = Public Limited Company, 9 = Government, 1262 = Partnership,
#   1263 = Proprietorship, 1853 = Individual

SUPPLY_TYPE_IDS = [135, 136, 223, 225, 1494]
#   135 = Inter-State, 136 = Intra-State, 223 = Import,
#   225 = Domestic, 1494 = Export

SALE_TYPE_IDS = [1264, 1265, 1266, 1267]
#   1264 = Retail, 1265 = Wholesale, 1266 = Direct, 1267 = Consignment

ADDRESS_TYPE_IDS = [43, 42]
#   43 = Shipping, 42 = Billing

ACCOUNT_TYPE_IDS = [1849, 1850]
#   1849 = Current, 1850 = Saving

BANK_DOC_IDS = [35, 36, 1883]
#   35 = Passbook, 36 = Bank Statement, 1883 = Cancelled Cheque

PAYMENT_TERMS_IDS = [26, 131, 549, 550, 551]
#   26 = 30 Days, 131 = Immediate, 549/550/551 = other terms

DELIVERY_TERMS_IDS = [129, 130]
#   129 = Delivery, 130 = Spot

MODE_OF_DELIVERY_IDS = [30, 31, 32, 33, 34]
#   30 = Truck, 31 = Railway, 32 = Sea, 33 = Courier, 34 = Air

PREFERRED_PAYMENT_METHOD_IDS = [53, 54, 55, 141, 143]
#   Various payment methods

COURIER_TERMS_IDS = [51, 52, 1252]
#   Various courier terms

GST_REGISTRATION_STATUS_IDS = [49, 50]
#   49 = Registered, 50 = Unregistered
#   NOTE: The ERP shows "Registered" / "Unregistered" labels for this dropdown.
#   This is a separate field from Gst Registration Type (Composit/Regular).

GST_REGISTRATION_TYPE_IDS = [49, 50]
#   49 = Unregistered, 50 = Regular

# Fixed defaults
DEFAULT_CURRENCY_REF_ID = 1   # INR
DEFAULT_COUNTRY_REF_ID = 8    # India

# Backward-compatible default FK IDs dict
DEFAULT_CUSTOMER_FK_IDS = {
    "ownership_status_ref_id": 7,            # Private Limited Company
    "supply_type_ref_id": 225,              # Domestic
    "sale_type_ref_id": 1265,               # Wholesale
    "default_currency_ref_id": 1,            # INR
    "address_type": 43,                      # Shipping
    "country_ref_id_id": 8,                  # India
    "account_type": 1849,                    # Current
    "bank_doc_id": 36,                       # Bank Statement
    "preferred_payment_method_ref_id": 55,
    "gst_registration_status": 49,           # Registered
    "gst_registration_type": 50,             # Regular
    "payment_terms_ref_id": 131,             # Immediate
    "delivery_terms_ref_id": 129,            # Delivery
    "mode_of_delivery_ref_id": 30,           # Truck
    "courier_terms_ref_id": 52,
}


# ──────────────────────────────────────────────
# FK Name Mappings (human-readable labels for each ID)
# ──────────────────────────────────────────────

OWNERSHIP_STATUS_NAMES = {
    5: "Cooperative Society",
    6: "Limited",
    7: "Private Limited Company",
    8: "Public Limited Company",
    9: "Government",
    1262: "Partnership",
    1263: "Proprietorship",
    1853: "Individual",
}

SUPPLY_TYPE_NAMES = {
    135: "Inter-State",
    136: "Intra-State",
    223: "Import",
    225: "Domestic",
    1494: "Export",
}

SALE_TYPE_NAMES = {
    1264: "Retail",
    1265: "Wholesale",
    1266: "Direct",
    1267: "Consignment",
}

ADDRESS_TYPE_NAMES = {43: "Shipping", 42: "Billing"}

ACCOUNT_TYPE_NAMES = {1849: "Current", 1850: "Saving"}

BANK_DOC_NAMES = {
    35: "Passbook",
    36: "Bank Statement",
    1883: "Cancelled Cheque",
}

PAYMENT_TERMS_NAMES = {
    26: "30 Days",
    131: "Immediate",
    549: "7 Days",
    550: "14 Days",
    551: "21 Days",
}

DELIVERY_TERMS_NAMES = {129: "Delivery", 130: "Spot"}

MODE_OF_DELIVERY_NAMES = {
    30: "Truck",
    31: "Railway",
    32: "Sea",
    33: "Courier",
    34: "Air",
}

PREFERRED_PAYMENT_METHOD_NAMES = {
    53: "Cheque",
    54: "Cash",
    55: "NEFT/RTGS",
    141: "UPI",
    143: "Credit Note",
}

COURIER_TERMS_NAMES = {
    51: "FOB",
    52: "CIF",
    1252: "Ex-Works",
}

GST_REGISTRATION_STATUS_NAMES = {
    49: "Registered",
    50: "Unregistered",
}

GST_REGISTRATION_TYPE_NAMES = {
    49: "Unregistered",
    50: "Regular",
}


# ──────────────────────────────────────────────
# Field Validation Rules (schema documentation)
# ──────────────────────────────────────────────

FIELD_VALIDATION_RULES = {
    # Root-level fields
    "party_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 143},
    "ownership_status_ref_id": {"type": "dropdown", "required": True, "fk_options_count": 8},
    "name": {"type": "character", "required": True, "max_length": 255, "pattern": None, "unique": False},
    "supply_type_ref_id": {"type": "dropdown", "required": True, "fk_options_count": 5},
    "sale_type_ref_id": {"type": "dropdown", "required": True, "fk_options_count": 4},
    "default_currency_ref_id": {"type": "dropdown", "required": True, "fk_options_count": 114},
    "email_id": {"type": "character", "required": False, "max_length": 255, "pattern": r"^[^@]+@[^@]+\.[^@]+$", "unique": False},
    "mobile_no": {"type": "integer", "required": True, "max_length": 255, "pattern": r"^[6-9]\d{9}$", "unique": False},
    "pan_no": {"type": "character", "required": True, "max_length": 255, "pattern": r"^[A-Z]{5}[0-9]{4}[A-Z]$", "unique": True},
    "status": {"type": "toggle", "required": True, "default": True},
    # Additional Details (children[0] — fields on stepper object, NOT in details[])
    "display_name_as": {"type": "character", "required": False, "max_length": 255},
    "office_no": {"type": "character", "required": False, "max_length": 255},
    "preferred_payment_method_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 5},
    "gst_registration_type": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "payment_terms_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 5},
    "delivery_terms_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "mode_of_delivery_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 5},
    "courier_terms_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 3},
    "deposit": {"type": "numeric", "required": False, "default": 0},
    "quantity_tolerance": {"type": "numeric", "required": False},
    "rate_tolerance": {"type": "numeric", "required": False},
    "is_tds_applicable": {"type": "toggle", "required": False, "default": False},
    "is_gst_set_off": {"type": "toggle", "required": False, "default": True},
    "customer_status": {"type": "dropdown", "required": False},
    "customer_type_ref_id": {"type": "dropdown", "required": False},
    "packing_material_ref_id": {"type": "dropdown", "required": False},
    # Address Details / Address (children[1].details[])
    "address_type": {"type": "dropdown", "required": True, "fk_options_count": 2},
    "country_ref_id_id": {"type": "dropdown", "required": True, "fk_options_count": 30, "cascading": True},
    "state_ref_id_id": {"type": "dropdown", "required": True, "fk_options_count": 0, "cascading": True},
    "district_ref_id_id": {"type": "dropdown", "required": True, "fk_options_count": 0, "cascading": True},
    "sub_district_ref_id_id": {"type": "dropdown", "required": True, "fk_options_count": 0, "cascading": True},
    "village_ref_id_id": {"type": "dropdown", "required": False, "fk_options_count": 0, "cascading": True},
    "address": {"type": "character", "required": True, "max_length": 255},
    "pin_code": {"type": "character", "required": True, "max_length": 255},
    "gstin": {"type": "character", "required": False, "max_length": 255, "pattern": r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"},
    # Customer Bank Details (children[2].details[])
    "bank_name": {"type": "character", "required": True, "max_length": 255},
    "bank_branch_code": {"type": "character", "required": False, "max_length": 255},
    "bank_ifsc_code": {"type": "character", "required": False, "max_length": 255},
    "account_type": {"type": "dropdown", "required": True, "fk_options_count": 2},
    "bank_account_holder_name": {"type": "character", "required": True, "max_length": 255},
    "bank_account_no": {"type": "character", "required": True, "max_length": 255},
    "bank_doc_id": {"type": "dropdown", "required": True, "fk_options_count": 3},
    "bank_attachment_path": {"type": "file", "required": False, "max_length": 255},
}


def get_random_address_chain():
    """Import and reuse the Supplier address chain pool."""
    from pages.registration.modules.supplier.data.supplier_data import (
        get_random_address_chain as _supplier_chain,
    )
    return _supplier_chain(verified_only=True)


def generate_random_fk_ids() -> dict:
    """Generate a set of random FK IDs for Customer dropdown variety."""
    return {
        "ownership_status_ref_id": random.choice(OWNERSHIP_STATUS_IDS),
        "supply_type_ref_id": random.choice(SUPPLY_TYPE_IDS),
        "sale_type_ref_id": random.choice(SALE_TYPE_IDS),
        "default_currency_ref_id": DEFAULT_CURRENCY_REF_ID,
        "address_type": random.choice(ADDRESS_TYPE_IDS),
        "country_ref_id_id": DEFAULT_COUNTRY_REF_ID,
        "account_type": random.choice(ACCOUNT_TYPE_IDS),
        "bank_doc_id": random.choice(BANK_DOC_IDS),
        "preferred_payment_method_ref_id": random.choice(PREFERRED_PAYMENT_METHOD_IDS),
        "gst_registration_status": random.choice(GST_REGISTRATION_STATUS_IDS),
        "gst_registration_type": random.choice(GST_REGISTRATION_TYPE_IDS),
        "payment_terms_ref_id": random.choice(PAYMENT_TERMS_IDS),
        "delivery_terms_ref_id": random.choice(DELIVERY_TERMS_IDS),
        "mode_of_delivery_ref_id": random.choice(MODE_OF_DELIVERY_IDS),
        "courier_terms_ref_id": random.choice(COURIER_TERMS_IDS),
    }


def generate_luhn_gstin(state_code=None):
    """Generate a valid GSTIN with Luhn mod-36 checksum.
    Reuses the Supplier function for correctness.
    """
    from pages.registration.modules.supplier.data.supplier_data import generate_gstin
    return generate_gstin(state_code)


def generate_realistic_email():
    """Generate a realistic Indian email (same style as Supplier)."""
    from pages.registration.modules.supplier.data.supplier_data import generate_email
    return generate_email()


def generate_realistic_phone():
    """Generate a valid 10-digit Indian mobile number."""
    prefix = random.choice(["6", "7", "8", "9"])
    return f"{prefix}{random.randint(100000000, 999999999)}"


def generate_realistic_ifsc():
    """Generate a valid IFSC code with realistic bank codes."""
    from pages.registration.modules.supplier.data.supplier_data import generate_ifsc
    return generate_ifsc()


def build_customer_api_payload(
    customer_data: dict = None,
    dropdown_ids: dict = None,
) -> dict:
    """Build the complete Customer API payload from data + FK IDs.

    Args:
        customer_data: Dict from generate_valid_customer_data() or None for random.
        dropdown_ids: Dict of FK IDs. Missing keys fall back to DEFAULT_CUSTOMER_FK_IDS.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    ids = {**DEFAULT_CUSTOMER_FK_IDS, **(dropdown_ids or {})}

    def _fk(key):
        val = ids.get(key)
        return val if val is not None else None

    if customer_data is None:
        customer_data = generate_valid_customer_data()

    # Get address chain
    address_chain = get_random_address_chain()

    # ── Build Additional Details stepper ──
    # NOTE: For Customer, Additional Details fields live on the child object
    # itself (NOT inside details[]). The details[] array is empty.
    additional_details = {}
    additional_details["display_name_as"] = customer_data.get("contact_person_name", "") or None
    additional_details["office_no"] = customer_data.get("office_number", "") or None
    additional_details["is_tds_applicable"] = customer_data.get("is_tds_applicable", False)
    additional_details["is_gst_set_off"] = True  # default
    additional_details["customer_status"] = None
    additional_details["customer_type_ref_id"] = None
    additional_details["packing_material_ref_id"] = None
    if _fk("preferred_payment_method_ref_id") is not None:
        additional_details["preferred_payment_method_ref_id"] = _fk("preferred_payment_method_ref_id")
    if _fk("gst_registration_status") is not None:
        additional_details["gst_registration_status"] = _fk("gst_registration_status")
    if _fk("gst_registration_type") is not None:
        additional_details["gst_registration_type"] = _fk("gst_registration_type")
    if _fk("payment_terms_ref_id") is not None:
        additional_details["payment_terms_ref_id"] = _fk("payment_terms_ref_id")
    if _fk("delivery_terms_ref_id") is not None:
        additional_details["delivery_terms_ref_id"] = _fk("delivery_terms_ref_id")
    if _fk("mode_of_delivery_ref_id") is not None:
        additional_details["mode_of_delivery_ref_id"] = _fk("mode_of_delivery_ref_id")
    if _fk("courier_terms_ref_id") is not None:
        additional_details["courier_terms_ref_id"] = _fk("courier_terms_ref_id")

    # Numeric fields
    deposit = customer_data.get("deposite", "0")
    try:
        additional_details["deposit"] = float(deposit)
    except (ValueError, TypeError):
        additional_details["deposit"] = 0.0

    qty_tol = customer_data.get("quantity_tolerance")
    try:
        additional_details["quantity_tolerance"] = float(qty_tol) if qty_tol else None
    except (ValueError, TypeError):
        additional_details["quantity_tolerance"] = None

    rate_tol = customer_data.get("rate_tolerance")
    try:
        additional_details["rate_tolerance"] = float(rate_tol) if rate_tol else None
    except (ValueError, TypeError):
        additional_details["rate_tolerance"] = None

    # ── Build Address Details (Address) stepper ──
    address_detail = {}
    if _fk("address_type") is not None:
        address_detail["address_type"] = _fk("address_type")
    if _fk("country_ref_id_id") is not None:
        address_detail["country_ref_id_id"] = _fk("country_ref_id_id")
    # Use address chain FK IDs
    address_detail["state_ref_id_id"] = address_chain.get("state_ref_id_id")
    address_detail["district_ref_id_id"] = address_chain.get("district_ref_id_id")
    address_detail["sub_district_ref_id_id"] = address_chain.get("sub_district_ref_id_id")
    address_detail["village_ref_id_id"] = address_chain.get("village_ref_id_id")
    address_detail["address"] = customer_data.get("address", generate_address())
    pin = customer_data.get("pin_code", generate_pin_code())
    address_detail["pin_code"] = int(pin) if pin and str(pin).isdigit() else None
    address_detail["gstin"] = generate_luhn_gstin()
    address_detail["same_as_above"] = None
    address_detail["address2"] = None
    address_detail["demo_details"] = None
    address_detail["details"] = []

    # ── Build Customer Bank Details stepper ──
    bank_detail = {}
    bank_detail["bank_name"] = customer_data.get("bank_name", "Bank") or None
    # Branch name: must be alpha-only, no numbers/special chars (same rule as Supplier)
    _BANK_CITIES = [
        "Mumbai", "Delhi", "Pune", "Ahmedabad", "Bangalore",
        "Chennai", "Hyderabad", "Kolkata", "Jaipur", "Lucknow",
    ]
    bank_detail["bank_branch_code"] = f"{random.choice(_BANK_CITIES)} Branch"
    bank_detail["bank_ifsc_code"] = customer_data.get("ifsc_code", generate_realistic_ifsc()) or None
    if _fk("account_type") is not None:
        bank_detail["account_type"] = _fk("account_type")
    # Account holder name: must be alpha-only, no special chars like &
    raw_name = customer_data.get("company_name", "")
    # Strip non-alpha characters (keep spaces)
    safe_name = "".join(c for c in raw_name if c.isalpha() or c == " ").strip() or "Customer Account"
    bank_detail["bank_account_holder_name"] = safe_name
    # Account number: must be numeric, 9-16 digits
    acct = customer_data.get("account_number", "")
    if not acct or not str(acct).isdigit():
        acct = str(random.randint(100000000000, 999999999999))
    bank_detail["bank_account_no"] = int(acct)
    if _fk("bank_doc_id") is not None:
        bank_detail["bank_doc_id"] = _fk("bank_doc_id")
    bank_detail["bank_attachment_path"] = None
    bank_detail["details"] = []

    # ── Assemble payload ──
    payload = {
        "id": "",
        "attribute_name": "Customer",

        # Root-level fields
        "party_ref_id": None,
        "ownership_status_ref_id": ids["ownership_status_ref_id"],
        "name": customer_data.get("company_name", generate_company_name()),
        "supply_type_ref_id": ids["supply_type_ref_id"],
        "sale_type_ref_id": ids["sale_type_ref_id"],
        "default_currency_ref_id": ids["default_currency_ref_id"],
        "email_id": customer_data.get("email", generate_realistic_email()) or None,
        "mobile_no": int(customer_data.get("phone_number", generate_realistic_phone()) or "0"),
        "pan_no": customer_data.get("pan_number", generate_pan_number()),
        "status": customer_data.get("status", True),
        "vendor_code": None,
        "ref_id": None,
        "ref_type": None,

        # Children array with stepper objects
        "children": [
            {
                "stepper_name": "Additional Details",
                "is_stepper": True,
                "details": [],       # NOTE: empty for Customer — fields on child itself
                "children": [],
                **additional_details,  # Spread fields onto the child object
            },
            {
                "stepper_name": "Address Details",
                "is_stepper": True,
                "details": [address_detail],
                "children": [],
            },
            {
                "stepper_name": "Customer Bank Details",
                "is_stepper": True,
                "details": [bank_detail],
                "children": [],
            },
        ],
    }

    return payload


def generate_customer_api_payload(
    name_prefix=None,
    dropdown_ids: dict = None,
) -> dict:
    """One-shot: generate a complete Customer API payload with random data.

    Automatically randomizes:
      - Address chain (state/district/taluka/village)
      - Ownership type, Supply type, Sale type
      - Address type, Account type, Payment method
      - Payment terms, Delivery terms, Mode of delivery
      - Courier terms, GST registration type

    Args:
        name_prefix: If provided, forces old prefix_timestamp naming.
        dropdown_ids: Override specific FK IDs.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    customer_data = generate_valid_customer_data(name_prefix or "AutoCust")
    # Use realistic email/phone (not the timestamp-based ones)
    customer_data["email"] = generate_realistic_email()
    customer_data["phone_number"] = generate_realistic_phone()
    customer_data["gstin"] = generate_luhn_gstin()

    ids = {
        **generate_random_fk_ids(),
        **get_random_address_chain(),
        **(dropdown_ids or {}),
    }

    return build_customer_api_payload(customer_data, ids)


def generate_customer_api_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """Generate multiple unique Customer API payloads for batch creation."""
    payloads = []
    for i in range(count):
        payloads.append(
            generate_customer_api_payload(prefix, dropdown_ids)
        )
    return payloads


def generate_batch_payloads(count: int = 10, **kwargs) -> list:
    """Generate N unique Customer API payloads.

    Alias for generate_customer_api_payloads() — matches the Supplier
    module's naming convention for consistency across test code.

    Args:
        count: Number of payloads to generate.
        **kwargs: Passed to each generate_customer_api_payload() call.

    Returns:
        List of payload dicts.
    """
    return [generate_customer_api_payload(**kwargs) for _ in range(count)]