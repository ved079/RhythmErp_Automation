"""
member_data.py
--------------
Test data & API payload builder for Rhythm ERP Member Screen.
Derived from live ERP schema at /core/dynamic-screen/Member/ (tenant 599).

FIELD REFERENCE (15 top-level fields + KYC stepper with 3 child fields):

TOP-LEVEL FIELDS:
  1.  Party Reference       (dropdown, optional) — FK to party_master (excludes non-Member roles)
      Auto-patches: prefix_ref_id, name, pan_no, mobile_no, date_of_cessation,
                    no_class_shares_held, percentage_of_shares, and KYC Details
      when a party is selected (is_onchange_event = true)
  2.  Prefix                 (dropdown, required) — 3 options: Mrs(1895), Mr(1896), Ms(1897)
  3.  Member Name            (character, required, maxlength=255)
  4.  Member Address         (character, required, maxlength=255)
  5.  PAN/Other              (character, required, maxlength=255) — shown in listing
  6.  Folio Number           (character, required, maxlength=255)
  7.  Registration Date      (date, required)
  8.  No. & Class of Shares  (character, required, maxlength=255) — e.g. "100 Equity"
  9.  Distinctive Number     (character, required, maxlength=255)
  10. Amount Paid on Shares  (integer, required)
  11. Date of Allotment      (date, required)
  12. Date of Cessation      (date, optional)
  13. Percentage of Shares   (integer, required)
  14. Phone Number           (integer, required, maxlength=10) — shown in listing
  15. Is Member Director     (toggle, optional) — boolean

KYC DETAILS STEPPER (child grid — 3 fields per row):
  1. KYC Document            (dropdown, required) — 2 options: PAN(65), AADHAR(66)
  2. KYC Number              (character, required, maxlength=255)
  3. KYC Attachment          (file, optional)

KEY RULES (verified 2026-06-04 on live app):
  - COMPLEX SCREEN: Has 1 stepper child (KYC Details) with grid rows
  - party_ref_id auto-fills prefix, name, PAN, phone, cessation, shares, and KYC
  - Backend ENFORCES some validations (unlike other screens):
    * Name must match ^[A-Za-z ]+$ (letters and spaces only, no numbers/hyphens)
    * Distinctive Number must be a pure INTEGER (no letters/dashes like "DN-001")
    * Number and Class of Shares must be a STRING (e.g. "100 Equity"), not an integer
    * PAN must be unique per Member screen ("'XXX' already exists")
  - Phone has NO server-side length validation — 3-digit numbers accepted
  - foli_number accepts both string and integer
  - amount_paid_on_shares and percentage_of_shares are integer type
  - mobile_no is integer type (10-digit Indian mobile)
  - is_member_director is a toggle (boolean)
  - API returns listing page on POST (status 200/201)
  - Master table: party_master (same as Supplier/Customer/Employee)
  - is_bulk_upload: true
  - is_workflow_applicable: false
  - is_effective_dated: false
  - is_history_applicable: false
  - master_table_name: party_master

ENDPOINTS:
  Schema:  GET  /core/dynamic-screen/Member/
  List:    GET  /core/dynamic-screen-wrapper/Member/
  Detail:  GET  /core/dynamic-screen-wrapper/Member/{id}/
  Create:  POST /core/dynamic-screen-wrapper/

SCREEN METADATA:
  Screen ID: 99
  attribute_name: "Member"
  master_table: party_master
"""

import random
import string
from datetime import datetime, date


# ──────────────────────────────────────────────
# Realistic Indian name pools for Member data
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

_MEMBER_ADDRESS_STREETS = [
    "MG Road", "Station Road", "Main Road", "Market Road",
    "Temple Street", "Gandhi Nagar", "Jawahar Colony", "Shivaji Path",
    "Laxmi Road", "Tilak Road", "Nehru Nagar", "Ambedkar Chowk",
    "Sadar Bazaar", "Civil Lines", "Cantonment Area", "Old City",
]

_MEMBER_ADDRESS_CITIES = [
    "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad",
    "Solapur", "Kolhapur", "Sangli", "Satara", "Jalgaon",
    "Amravati", "Akola", "Latur", "Osmanabad", "Dhule",
    "Chandrapur", "Nanded", "Parbhani", "Beed", "Ratnagiri",
]

# Track generated names to prevent duplicates within a session
_generated_names = set()


# ──────────────────────────────────────────────
# FK ID pools (verified on tenant 599, 2026-06-04)
# ──────────────────────────────────────────────

# Prefix dropdown — 3 options
PREFIX_IDS = [1895, 1896, 1897]
PREFIX_NAMES = {
    1895: "Mrs",
    1896: "Mr",
    1897: "Ms",
}

# KYC Document dropdown — 2 options
KYC_DOC_IDS = [65, 66]
KYC_DOC_NAMES = {
    65: "PAN",
    66: "AADHAR",
}

# Party Reference IDs — 329 valid options (party_master excluding non-Member roles)
# Verified from live ERP schema on 2026-06-04
PARTY_REF_IDS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 41,
    42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
    60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77,
    78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
    96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
    111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
    126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140,
    141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155,
    156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170,
    171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185,
    186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200,
    201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215,
    216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230,
    231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245,
    246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260,
    261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275,
    276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290,
    291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305,
    306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320,
    323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334,
]

# Share class types for no_class_shares_held field
SHARE_CLASS_TYPES = [
    "Equity", "Preference", "Deferred", "Founders", "Bonus",
    "Rights", "Sweat Equity", "Convertible",
]

# Default FK IDs dict
DEFAULT_MEMBER_FK_IDS = {
    "prefix_ref_id": 1896,    # Mr
    "party_ref_id": None,     # Skip by default — auto-patches fields
    "kyc_doc_id": 65,         # PAN
}


# ──────────────────────────────────────────────
# Realistic data generators
# ──────────────────────────────────────────────

def generate_member_name(prefix=None):
    """Generate a realistic Indian member name.

    Composes: FirstName LastName (e.g., "Rajesh Sharma", "Priya Patel").

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


def generate_member_address():
    """Generate a realistic Indian address string.

    Examples: "45 MG Road, Pune", "12 Station Road, Nagpur"
    """
    num = random.randint(1, 500)
    street = random.choice(_MEMBER_ADDRESS_STREETS)
    city = random.choice(_MEMBER_ADDRESS_CITIES)
    return f"{num} {street}, {city}"


def generate_pan_number():
    """Generate a valid Indian PAN number in ABCDE1234F format.

    Pattern: 5 uppercase letters + 4 digits + 1 uppercase letter.
    Returns a string matching ^[A-Z]{5}[0-9]{4}[A-Z]$
    """
    first5 = ''.join(random.choices(string.ascii_uppercase, k=5))
    middle4 = ''.join(random.choices(string.digits, k=4))
    last1 = random.choice(string.ascii_uppercase)
    return f"{first5}{middle4}{last1}"


def generate_phone():
    """Generate a valid 10-digit Indian mobile number.

    Starts with 6-9 (valid Indian mobile prefix).
    Returns an integer (the API expects integer type for mobile_no).
    """
    prefix = random.choice(["6", "7", "8", "9"])
    remaining = random.randint(100000000, 999999999)
    return int(f"{prefix}{remaining}")


def generate_folio_number():
    """Generate a unique folio number string.

    Format: FOL-{RANDOM}-{TIMESTAMP}
    """
    rand = random.randint(1000, 9999)
    ts = datetime.now().strftime("%H%M%S")
    return f"FOL-{rand}-{ts}"


def generate_distinctive_number():
    """Generate a distinctive number (INTEGER, not string).

    The ERP validates that distinctive_number must be a pure integer.
    String formats like "DN-12345" are rejected with "Invalid Distinctive Number".
    Returns an integer.
    """
    return random.randint(10000, 99999)


def generate_share_class():
    """Generate a realistic share class description.

    Examples: "100 Equity", "250 Preference", "50 Founders"
    """
    num = random.randint(1, 10000)
    share_type = random.choice(SHARE_CLASS_TYPES)
    return f"{num} {share_type}"


def generate_amount_paid():
    """Generate a realistic amount paid on shares (integer).

    Range: 1,000 to 10,000,000
    """
    return random.randint(1000, 10000000)


def generate_percentage_of_shares():
    """Generate a realistic percentage of shares (integer 1-100).

    Range: 1 to 100
    """
    return random.randint(1, 100)


def generate_registration_date():
    """Generate a registration date in ISO format.

    Returns a date string in "YYYY-MM-DDTHH:MM:SSZ" format.
    Dates are within the past 2 years.
    """
    today = date.today()
    days_back = random.randint(1, 730)
    reg_date = today - __import__("datetime").timedelta(days=days_back)
    return f"{reg_date.strftime('%Y-%m-%d')}T18:30:00Z"


def generate_date_of_allotment():
    """Generate a date of allotment in ISO format.

    Returns a date string. Dates are within the past 1 year.
    """
    today = date.today()
    days_back = random.randint(1, 365)
    allot_date = today - __import__("datetime").timedelta(days=days_back)
    return f"{allot_date.strftime('%Y-%m-%d')}T18:30:00Z"


def generate_kyc_number(kyc_doc_id=65):
    """Generate a KYC number based on document type.

    Args:
        kyc_doc_id: 65 for PAN, 66 for AADHAR
    """
    if kyc_doc_id == 65:
        # PAN format
        return generate_pan_number()
    else:
        # AADHAR format: 12 digits
        return ''.join(random.choices(string.digits, k=12))


def generate_prefix_id():
    """Pick a random prefix ID from the verified pool.

    Returns:
        int: A valid prefix FK ID.
    """
    return random.choice(PREFIX_IDS)


def generate_party_ref_id():
    """Pick a random party reference ID from the verified pool.

    Returns:
        int or None: A valid party_ref_id FK ID, or None to skip.
    """
    # 80% chance to skip party reference (most members are created fresh)
    if random.random() < 0.8:
        return None
    return random.choice(PARTY_REF_IDS)


def generate_kyc_doc_id():
    """Pick a random KYC document ID.

    Returns:
        int: 65 (PAN) or 66 (AADHAR)
    """
    return random.choice(KYC_DOC_IDS)


# ──────────────────────────────────────────────
# Valid data for UI form fill
# ──────────────────────────────────────────────

def generate_valid_member_data():
    """Generate complete valid data for the Member form.

    This is the UI-facing format (field names match the Angular form controls).

    Returns:
        dict with all form fields populated with realistic data.
    """
    return {
        "party_reference": None,
        "prefix": generate_prefix_id(),
        "member_name": generate_member_name(),
        "member_address": generate_member_address(),
        "pan_no": generate_pan_number(),
        "folio_number": generate_folio_number(),
        "registration_date": generate_registration_date(),
        "no_class_shares_held": generate_share_class(),
        "distinctive_number": generate_distinctive_number(),
        "amount_paid_on_shares": generate_amount_paid(),
        "date_of_allotment": generate_date_of_allotment(),
        "date_of_cessation": None,
        "percentage_of_shares": generate_percentage_of_shares(),
        "phone_number": generate_phone(),
        "is_member_director": random.choice([True, False]),
        "kyc_details": [generate_valid_kyc_row()],
    }


def generate_valid_kyc_row(kyc_doc_id=None):
    """Generate a single valid KYC detail row.

    Args:
        kyc_doc_id: Override KYC document type (65=PAN, 66=AADHAR).
                    If None, picks randomly.

    Returns:
        dict with kyc_doc_id, kyc_account_no, attachment_path.
    """
    if kyc_doc_id is None:
        kyc_doc_id = generate_kyc_doc_id()
    return {
        "kyc_doc_id": kyc_doc_id,
        "kyc_account_no": generate_kyc_number(kyc_doc_id),
        "attachment_path": None,
    }


def generate_minimal_member_data():
    """Generate minimal data — only the required fields.

    All other fields are empty/null. Use for mandatory field validation tests.
    """
    return {
        "party_reference": None,
        "prefix": generate_prefix_id(),
        "member_name": generate_member_name(),
        "member_address": generate_member_address(),
        "pan_no": generate_pan_number(),
        "folio_number": generate_folio_number(),
        "registration_date": None,
        "no_class_shares_held": generate_share_class(),
        "distinctive_number": generate_distinctive_number(),
        "amount_paid_on_shares": generate_amount_paid(),
        "date_of_allotment": None,
        "date_of_cessation": None,
        "percentage_of_shares": generate_percentage_of_shares(),
        "phone_number": generate_phone(),
        "is_member_director": False,
        "kyc_details": [],
    }


def generate_empty_member_data():
    """Generate data with all fields empty/null — for validation testing."""
    return {
        "party_reference": None,
        "prefix": None,
        "member_name": "",
        "member_address": "",
        "pan_no": "",
        "folio_number": "",
        "registration_date": None,
        "no_class_shares_held": "",
        "distinctive_number": "",
        "amount_paid_on_shares": None,
        "date_of_allotment": None,
        "date_of_cessation": None,
        "percentage_of_shares": None,
        "phone_number": None,
        "is_member_director": None,
        "kyc_details": [],
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
    """Generate a member name with numbers."""
    return "Rajesh123"


def generate_invalid_name_special_chars():
    """Generate a member name with special characters."""
    return "Rajesh@Sharma!"


def generate_invalid_phone_starts_with_5():
    """Generate a phone number starting with 5."""
    return int(f"5{random.randint(100000000, 999999999)}")


def generate_invalid_phone_too_short():
    """Generate a phone number that's too short (less than 10 digits)."""
    return random.randint(100, 9999)


def generate_invalid_phone_too_long():
    """Generate a phone number that's too long (more than 10 digits)."""
    return random.randint(10000000000, 99999999999)


def generate_invalid_pan_format():
    """Generate an invalid PAN that doesn't match ABCDE1234F format."""
    return "INVALIDPAN"


def generate_negative_amount():
    """Generate a negative amount for amount_paid_on_shares."""
    return -1000


def generate_zero_percentage():
    """Generate zero for percentage_of_shares."""
    return 0


def generate_negative_percentage():
    """Generate a negative percentage of shares."""
    return -5


def generate_percentage_over_100():
    """Generate a percentage over 100."""
    return 150


def generate_sql_injection_name():
    """Generate a SQL injection string for Member Name."""
    return "'; DROP TABLE party_master; --"


def generate_xss_name():
    """Generate an XSS payload string for Member Name."""
    return "<script>alert('xss')</script>"


def generate_spaces_only_name():
    """Generate a name that's only spaces."""
    return "     "


# ──────────────────────────────────────────────
# Expected validation messages (from ERP schema)
# ──────────────────────────────────────────────

class ExpectedMessages:
    """Exact error messages from the ERP validation patterns."""
    REQUIRED_FIELD = "This field is required"
    INVALID_PAN = "Invalid PAN format"
    INVALID_PHONE = "Invalid Phone Number"
    MAX_LENGTH_EXCEEDED = "Ensure this field has no more than 255 characters."


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the UI-facing dict format into the JSON payload that
# POST /core/dynamic-screen-wrapper/ expects.
#
# COMPLEX SCREEN STRUCTURE (Member):
#   Member has 1 stepper child: KYC Details (grid)
#
#   {
#     "id": "",
#     "attribute_name": "Member",
#     "party_ref_id": null,
#     "prefix_ref_id": 1896,
#     "name": "Rajesh Sharma",
#     "member_address": "45 MG Road, Pune",
#     "foli_number": "FOL-1234-123456",
#     "pan_no": "ABCDE1234F",
#     "registration_date": "2025-06-15T18:30:00Z",
#     "no_class_shares_held": "100 Equity",
#     "distintive_number": "DN-12345",
#     "amount_paid_on_shares": 50000,
#     "date_of_allotment": "2025-05-31T18:30:00Z",
#     "date_of_cessation": null,
#     "percentage_of_shares": 10,
#     "mobile_no": 9876543210,
#     "is_member_director": false,
#     "details": [],
#     "children": [
#       {
#         "stepper_name": "KYC Details",
#         "details": [
#           {
#             "id": "",
#             "kyc_doc_id": 65,
#             "kyc_account_no": "ABCDE1234F",
#             "attachment_path": null
#           }
#         ]
#       }
#     ]
#   }
#
# FIELD KEY MAPPING:
#   UI key                  → API field_key
#   ──────────────────────────────────────────────────
#   party_reference         → party_ref_id (dropdown FK, skip = null)
#   prefix                  → prefix_ref_id (dropdown FK)
#   member_name             → name (string)
#   member_address          → member_address (string)
#   pan_no                  → pan_no (string)
#   folio_number            → foli_number (string/integer)
#   registration_date       → registration_date (date string)
#   no_class_shares_held    → no_class_shares_held (string)
#   distinctive_number      → distintive_number (string, note the typo in ERP)
#   amount_paid_on_shares   → amount_paid_on_shares (integer)
#   date_of_allotment       → date_of_allotment (date string)
#   date_of_cessation       → date_of_cessation (date string or null)
#   percentage_of_shares    → percentage_of_shares (integer)
#   phone_number            → mobile_no (integer)
#   is_member_director      → is_member_director (boolean/toggle)
#   kyc_details             → children[0].details[] (grid rows)
#
# IMPORTANT RULES:
#   - Use null (None) for optional FK fields when not set
#   - "id" must be "" (empty string) for new entries
#   - mobile_no must be an INTEGER, not a string
#   - amount_paid_on_shares must be an INTEGER
#   - percentage_of_shares must be an INTEGER
#   - details must be empty array []
#   - children must have the KYC Details stepper structure
#   - Each KYC row needs "id": "" for new entries
#   - distinctive_number has a typo in the API: "distintive_number"
# ──────────────────────────────────────────────

def build_member_api_payload(
    member_data: dict = None,
    fk_ids: dict = None,
) -> dict:
    """
    Build the JSON payload for POST /core/dynamic-screen-wrapper/.

    The Member screen has 1 stepper child (KYC Details) with a grid
    of document rows.

    Args:
        member_data: Dict from generate_valid_member_data().
                     If None, generates random data automatically.
        fk_ids: Optional dict of FK ID overrides. Keys should match
                API field names: prefix_ref_id, party_ref_id, kyc_doc_id.
                If None, uses random IDs from verified pools.

    Returns:
        Complete JSON payload dict ready for POST.

    Example:
        payload = build_member_api_payload()
        client.create_entry(payload)
    """
    if member_data is None:
        member_data = generate_valid_member_data()

    if fk_ids is None:
        fk_ids = {}

    # Resolve FK IDs: explicit > data > random pool > None
    prefix_ref_id = fk_ids.get("prefix_ref_id")
    if prefix_ref_id is None and member_data.get("prefix") is not None:
        prefix_ref_id = member_data["prefix"]
    if prefix_ref_id is None:
        prefix_ref_id = generate_prefix_id()

    party_ref_id = fk_ids.get("party_ref_id")
    if party_ref_id is None and member_data.get("party_reference") is not None:
        party_ref_id = member_data["party_reference"]

    # Build KYC Details stepper children
    kyc_rows = member_data.get("kyc_details", [])
    if not kyc_rows:
        # Generate default KYC row
        kyc_doc_id = fk_ids.get("kyc_doc_id", generate_kyc_doc_id())
        kyc_rows = [generate_valid_kyc_row(kyc_doc_id)]

    kyc_details = []
    for row in kyc_rows:
        kyc_entry = {
            "id": "",
            "kyc_doc_id": row.get("kyc_doc_id", generate_kyc_doc_id()),
            "kyc_account_no": row.get("kyc_account_no", generate_kyc_number(row.get("kyc_doc_id", 65))),
            "attachment_path": row.get("attachment_path", None),
        }
        kyc_details.append(kyc_entry)

    # Build the complete payload
    payload = {
        "id": "",
        "attribute_name": "Member",
        "party_ref_id": party_ref_id,
        "prefix_ref_id": prefix_ref_id,
        "name": member_data.get("member_name") or generate_member_name(),
        "member_address": member_data.get("member_address") or generate_member_address(),
        "foli_number": member_data.get("folio_number") or generate_folio_number(),
        "pan_no": member_data.get("pan_no") or generate_pan_number(),
        "registration_date": member_data.get("registration_date") or generate_registration_date(),
        "no_class_shares_held": member_data.get("no_class_shares_held") or generate_share_class(),
        "distintive_number": member_data.get("distinctive_number") if member_data.get("distinctive_number") is not None else generate_distinctive_number(),
        "amount_paid_on_shares": member_data.get("amount_paid_on_shares") or generate_amount_paid(),
        "date_of_allotment": member_data.get("date_of_allotment") or generate_date_of_allotment(),
        "date_of_cessation": member_data.get("date_of_cessation", None),
        "percentage_of_shares": member_data.get("percentage_of_shares") or generate_percentage_of_shares(),
        "mobile_no": member_data.get("phone_number") or generate_phone(),
        "is_member_director": member_data.get("is_member_director", False),
        "details": [],
        "children": [
            {
                "stepper_name": "KYC Details",
                "details": kyc_details,
            }
        ],
    }

    return payload


def generate_member_api_payload(**kwargs) -> dict:
    """One-shot: generate a randomized Member API payload.

    This is the convenience function for batch_create scripts.
    Just call it and get a ready-to-POST payload.

    Args:
        **kwargs: Optional overrides for any payload field.
                  e.g., name="John", prefix_ref_id=1895, is_member_director=True

    Returns:
        Complete JSON payload dict ready for POST.

    Example:
        # Random member
        payload = generate_member_api_payload()

        # With specific prefix
        payload = generate_member_api_payload(prefix_ref_id=1895)

        # Override specific fields
        payload = generate_member_api_payload(name="Test User", is_member_director=True)
    """
    data = generate_valid_member_data()
    payload = build_member_api_payload(data)

    # Apply any overrides
    payload.update(kwargs)

    return payload


# ──────────────────────────────────────────────
# Batch generation helpers
# ──────────────────────────────────────────────

def generate_batch_payloads(count: int, **kwargs) -> list:
    """Generate multiple unique Member API payloads.

    Args:
        count: Number of payloads to generate.
        **kwargs: Optional overrides applied to ALL payloads.

    Returns:
        List of payload dicts.

    Example:
        payloads = generate_batch_payloads(10)
        payloads = generate_batch_payloads(5, prefix_ref_id=1896, is_member_director=True)
    """
    return [generate_member_api_payload(**kwargs) for _ in range(count)]


# ──────────────────────────────────────────────
# Field validation summary (for test parametrize)
# ──────────────────────────────────────────────

FIELD_VALIDATION_RULES = {
    "party_ref_id": {
        "field_key": "party_ref_id",
        "label": "Party Reference",
        "type": "dropdown",
        "required": False,
        "max_length": 255,
        "is_onchange": True,
        "auto_patch_fields": [
            "prefix_ref_id", "name", "pan_no", "mobile_no",
            "date_of_cessation", "no_class_shares_held",
            "percentage_of_shares",
        ],
        "fk_options_count": 329,
    },
    "prefix_ref_id": {
        "field_key": "prefix_ref_id",
        "label": "Prefix",
        "type": "dropdown",
        "required": True,
        "fk_options_count": 3,
    },
    "name": {
        "field_key": "name",
        "label": "Member Name",
        "type": "character",
        "required": True,
        "max_length": 255,
        "visible_in_table": True,
        "pattern": r"^[A-Za-z ]+$",
        "server_validated": True,
        "validation_error": "Invalid Name",
    },
    "member_address": {
        "field_key": "member_address",
        "label": "Member Address",
        "type": "character",
        "required": True,
        "max_length": 255,
    },
    "pan_no": {
        "field_key": "pan_no",
        "label": "PAN/Other",
        "type": "character",
        "required": True,
        "max_length": 255,
        "visible_in_table": True,
        "unique": True,  # Server enforces: "'XXX' already exists"
    },
    "foli_number": {
        "field_key": "foli_number",
        "label": "Folio Number",
        "type": "character",
        "required": True,
        "max_length": 255,
    },
    "registration_date": {
        "field_key": "registration_date",
        "label": "Registration Date",
        "type": "date",
        "required": True,
    },
    "no_class_shares_held": {
        "field_key": "no_class_shares_held",
        "label": "Number and Class of Shares",
        "type": "character",  # MUST be string like "100 Equity", NOT integer
        "required": True,
        "server_validated": True,
        "validation_error": "Invalid Number and Class of Shares Held",
        "max_length": 255,
    },
    "distintive_number": {
        "field_key": "distintive_number",
        "label": "Distinctive Number",
        "type": "integer",  # MUST be pure integer, string formats like "DN-001" rejected
        "required": True,
        "max_length": 255,
        "server_validated": True,
        "validation_error": "Invalid Distinctive Number",
    },
    "amount_paid_on_shares": {
        "field_key": "amount_paid_on_shares",
        "label": "Amount Paid on Shares",
        "type": "integer",
        "required": True,
    },
    "date_of_allotment": {
        "field_key": "date_of_allotment",
        "label": "Date of Allotment",
        "type": "date",
        "required": True,
    },
    "date_of_cessation": {
        "field_key": "date_of_cessation",
        "label": "Date of Cessation",
        "type": "date",
        "required": False,
    },
    "percentage_of_shares": {
        "field_key": "percentage_of_shares",
        "label": "Percentage of Shares",
        "type": "integer",
        "required": True,
    },
    "mobile_no": {
        "field_key": "mobile_no",
        "label": "Phone Number",
        "type": "integer",
        "required": True,
        "max_length": 10,
        "visible_in_table": True,
    },
    "is_member_director": {
        "field_key": "is_member_director",
        "label": "Is Member Director",
        "type": "toggle",
        "required": False,
    },
    # KYC Details (child grid fields)
    "kyc_doc_id": {
        "field_key": "kyc_doc_id",
        "label": "KYC Document",
        "type": "dropdown",
        "required": True,
        "max_length": 255,
        "is_grid": True,
        "fk_options_count": 2,
    },
    "kyc_account_no": {
        "field_key": "kyc_account_no",
        "label": "KYC Number",
        "type": "character",
        "required": True,
        "max_length": 255,
        "is_grid": True,
    },
    "attachment_path": {
        "field_key": "attachment_path",
        "label": "KYC Attachment",
        "type": "file",
        "required": False,
        "max_length": 255,
        "is_grid": True,
    },
}
