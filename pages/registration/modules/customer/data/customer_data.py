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
        "bank_name": "Bank",
        "branch": "Branch",
        "ifsc_code": generate_ifsc_code(),
        "account_type": None,               # Pick from live UI (REQUIRED: Current/Saving)
        "account_holder_name": "Jason Holder",
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