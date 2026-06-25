"""
directors_data.py
-----------------
Test data & API payload builder for Rhythm ERP Directors Screen.
Derived from live ERP schema at /core/dynamic-screen/Directors/ (tenant 681).

FIELD REFERENCE (15 top-level fields + KYC stepper with 3 child fields):

TOP-LEVEL FIELDS:
  1.  Party Reference       (dropdown, optional) — FK to party_master (356 options)
      Auto-patches: prefix_ref_id, name, pan_no, mobile_no, and other fields
      when a party is selected (is_onchange_event = true)
  2.  Prefix                 (dropdown, required) — 3 options: Mrs(1895), Mr(1896), Ms(1897)
  3.  Director Name          (character, required) — Director's full name
  4.  Designation            (dropdown, required) — 56 options (e.g., Managing Director, CFO)
  5.  PAN/Other              (character, required) — PAN number (unique per Directors screen)
  6.  Residential Address    (character, required) — Director's residential address
  7.  Phone Number           (integer, required) — 10-digit mobile number
  8.  Date of Appointment    (date, required) — When the director was appointed
  9.  Date of Cessation      (date, optional) — When the director ceased (if applicable)
  10. No. & Class of Shares  (character, required) — e.g. "100 Equity"
  11. Details of Other Directorships (character, required) — Other directorship info
  12. Percentage of Shares   (integer, required) — Percentage of shares held
  13. Age                    (integer, required) — Director's age
  14. Qualification          (dropdown, required) — 6 options: 10th, 12th, Agri Diploma, etc.
  15. Experience in Years    (integer, required) — Years of experience

KYC DETAILS STEPPER (child grid — 3 fields per row):
  1. KYC Document            (dropdown, required) — 2 options: PAN(65), AADHAR(66)
  2. KYC Number              (character, required) — PAN or Aadhaar number
  3. KYC Attachment          (file, optional) — Document attachment

KEY RULES (verified 2026-06-04 on live app):
  - COMPLEX SCREEN: Has 1 stepper child (KYC Details) with grid rows
  - party_ref_id auto-fills prefix, name, PAN, mobile, and other fields
  - Same master_table as Member/Supplier/Customer/Employee: party_master
  - Designation is a required FK dropdown (56 options from designation_master)
  - Qualification is a required FK dropdown (6 options)
  - age and experience_in_years are integer type
  - mobile_no is integer type (10-digit Indian mobile)
  - no_class_shares_held is a string (e.g., "100 Equity")
  - details_of_other_directorships is a required character field
  - date_of_appointment is a required date field
  - date_of_cessation is an optional date field
  - API returns listing page on POST (status 200/201)
  - is_bulk_upload: true
  - is_workflow_applicable: false
  - is_effective_dated: false
  - is_history_applicable: false
  - master_table_name: party_master

ENDPOINTS:
  Schema:  GET  /core/dynamic-screen/Directors/
  List:    GET  /core/dynamic-screen-wrapper/Directors/
  Detail:  GET  /core/dynamic-screen-wrapper/Directors/{id}/
  Create:  POST /core/dynamic-screen-wrapper/

SCREEN METADATA:
  Screen ID: 98
  attribute_name: "Directors"
  master_table: party_master
"""

import random
import string
from datetime import datetime, date


# ──────────────────────────────────────────────
# Realistic Indian name pools for Director data
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

_RESIDENTIAL_STREETS = [
    "MG Road", "Station Road", "Main Road", "Market Road",
    "Temple Street", "Gandhi Nagar", "Jawahar Colony", "Shivaji Path",
    "Laxmi Road", "Tilak Road", "Nehru Nagar", "Ambedkar Chowk",
    "Sadar Bazaar", "Civil Lines", "Cantonment Area", "Old City",
]

_RESIDENTIAL_CITIES = [
    "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad",
    "Solapur", "Kolhapur", "Sangli", "Satara", "Jalgaon",
    "Amravati", "Akola", "Latur", "Osmanabad", "Dhule",
    "Chandrapur", "Nanded", "Parbhani", "Beed", "Ratnagiri",
]

_DIRECTORSHIP_COMPANIES = [
    "AgriTech Solutions Pvt Ltd",
    "Greenfield Farms Co-operative",
    "Maharashtra Agro Processing Ltd",
    "Konkan Spice Traders Pvt Ltd",
    "Vidarbha Cotton Association",
    "Deccan Sugar Industries Ltd",
    "Narmada Fertilizers Pvt Ltd",
    "Sahyadri Dairy Co-operative",
    "Western Ghats Plantations Ltd",
    "Godavari Seeds Corporation",
    "Marathwada Agro Exports Ltd",
    "Pune Agricultural Research Institute",
    "Mumbai Commodity Exchange",
    "Nashik Grape Growers Association",
    "None",
]

# Track generated names to prevent duplicates within a session
_generated_names = set()


# ──────────────────────────────────────────────
# FK ID pools (verified on tenant 681, 2026-06-04)
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

# Designation dropdown — 56 options (from designation_master)
# Verified from live ERP schema on 2026-06-04
DESIGNATION_IDS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
]

DESIGNATION_NAMES = {
    1: "Test Designation",
    2: "Farm Supervisor",
    3: "Warehouse Manager",
    4: "Quality Inspector",
    5: "Procurement Officer",
    6: "Accounts Executive",
    7: "Field Officer",
    8: "Weighbridge Operator",
    9: "Dispatch Coordinator",
    10: "Commodity Analyst",
    11: "Regional Manager",
    12: "Cashier",
    13: "Compliance Officer",
    14: "Data Entry Operator",
    15: "Transport Supervisor",
    16: "Loan Recovery Agent",
    17: "Agricultural Advisor",
    18: "Store Keeper",
    19: "Billing Clerk",
    20: "Internal Auditor",
    21: "IT Support Executive",
    22: "Test Designation QA",
    23: "Finance Manager",
    24: "Clerk",
    25: "Engineer",
    26: "Production Supervisor",
    27: "Quality Analyst",
    28: "HR Manager",
    29: "Warehouse Supervisor",
    30: "Managing Director",
    31: "Godown Keeper 343",
    32: "Divisional Manager0659490",
    33: "Chief Operating Officer0659491",
    34: "Warehouse Supervisor0659492",
    35: "Junior Engineer0659493",
    36: "Legal Officer0659494",
    37: "Data Analyst0716230",
    38: "Junior Engineer0716231",
    39: "IT Manager0716232",
    40: "Accounts Officer0716233",
    41: "Managing Director0716234",
    42: "Assistant General Manager0721300",
    43: "Accounts Officer0721301",
    44: "Agricultural Officer0721302",
    45: "Junior Accountant0721303",
    46: "Accounts Officer MTJ0721304",
    47: "Senior Vice President0723340",
    48: "Senior Technician0723341",
    49: "Managing Director0723342",
    50: "Agricultural Officer0723343",
    51: "Welfare Officer0723344",
    52: "Divisional Manager0729430",
    53: "Assistant General Manager0729431",
    54: "Senior Vice President0729432",
    55: "Production Manager0729433",
    56: "Chief Operating Officer0729434",
}

# Qualification dropdown — 6 options
QUALIFICATION_IDS = [508, 509, 510, 511, 512, 513]
QUALIFICATION_NAMES = {
    508: "10 th",
    509: "12 th",
    510: "Agri Diploma",
    511: "Graduation",
    512: "Post Graduation",
    513: "Other",
}

# Party Reference IDs — 357 valid options (party_master for Directors)
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
    323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337,
    338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352,
    353, 354, 355, 356, 357, 358, 359, 360, 361, 362,
]

# Share class types for no_class_shares_held field
SHARE_CLASS_TYPES = [
    "Equity", "Preference", "Deferred", "Founders", "Bonus",
    "Rights", "Sweat Equity", "Convertible",
]

# Common director designations for realistic data
COMMON_DIRECTOR_DESIGNATIONS = [2]  # Managing Director variants

# Default FK IDs dict
DEFAULT_DIRECTORS_FK_IDS = {
    "prefix_ref_id": 1896,     # Mr
    "designation": 2,         # Managing Director
    "qualification_ref_id": 511,  # Graduation
    "party_ref_id": None,      # Skip by default — auto-patches fields
    "kyc_doc_id": 65,          # PAN
}


# ──────────────────────────────────────────────
# Realistic data generators
# ──────────────────────────────────────────────

def generate_director_name(prefix=None):
    """Generate a realistic Indian director name.

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


def generate_residential_address():
    """Generate a realistic Indian residential address string.

    Examples: "45 MG Road, Pune", "12 Station Road, Nagpur"
    """
    num = random.randint(1, 500)
    street = random.choice(_RESIDENTIAL_STREETS)
    city = random.choice(_RESIDENTIAL_CITIES)
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


def generate_share_class():
    """Generate a realistic share class description.

    Examples: "100 Equity", "250 Preference", "50 Founders"
    """
    num = random.randint(1, 10000)
    share_type = random.choice(SHARE_CLASS_TYPES)
    return f"{num} {share_type}"


def generate_percentage_of_shares():
    """Generate a realistic percentage of shares (integer 1-100)."""
    return random.randint(1, 100)


def generate_age():
    """Generate a realistic director age.

    Range: 25 to 75 (directors are typically experienced professionals).
    """
    return random.randint(25, 75)


def generate_experience_in_years():
    """Generate realistic years of experience.

    Range: 1 to 50 (correlated with age but independent for flexibility).
    """
    return random.randint(1, 50)


def generate_date_of_appointment():
    """Generate a date of appointment in ISO format.

    Returns a date string. Dates are within the past 5 years.
    """
    today = date.today()
    days_back = random.randint(1, 1825)
    appt_date = today - __import__("datetime").timedelta(days=days_back)
    return f"{appt_date.strftime('%Y-%m-%d')}T18:30:00Z"


def generate_date_of_cessation():
    """Generate a date of cessation in ISO format, or None.

    80% chance of None (most directors are active).
    """
    if random.random() < 0.8:
        return None
    today = date.today()
    days_back = random.randint(1, 365)
    cess_date = today - __import__("datetime").timedelta(days=days_back)
    return f"{cess_date.strftime('%Y-%m-%d')}T18:30:00Z"


def generate_details_of_other_directorships():
    return "NA"


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
    """Pick a random prefix ID from the verified pool."""
    return random.choice(PREFIX_IDS)


def generate_designation_id():
    """Pick a random designation ID from the verified pool."""
    return random.choice(DESIGNATION_IDS)


def generate_qualification_id():
    """Pick a random qualification ID from the verified pool."""
    return random.choice(QUALIFICATION_IDS)


def generate_party_ref_id():
    """Pick a random party reference ID from the verified pool.

    Returns:
        int or None: A valid party_ref_id FK ID, or None to skip.
    """
    # 80% chance to skip party reference (most directors are created fresh)
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

def generate_valid_directors_data():
    """Generate complete valid data for the Directors form.

    This is the UI-facing format (field names match the Angular form controls).

    Returns:
        dict with all form fields populated with realistic data.
    """
    return {
        "party_reference": None,
        "prefix": generate_prefix_id(),
        "director_name": generate_director_name(),
        "designation": generate_designation_id(),
        "pan_no": generate_pan_number(),
        "residential_address": generate_residential_address(),
        "phone_number": generate_phone(),
        "date_of_appointment": generate_date_of_appointment(),
        "date_of_cessation": generate_date_of_cessation(),
        "no_class_shares_held": generate_share_class(),
        "details_of_other_directorships": generate_details_of_other_directorships(),
        "percentage_of_shares": generate_percentage_of_shares(),
        "age": generate_age(),
        "qualification": generate_qualification_id(),
        "experience_in_years": generate_experience_in_years(),
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


def generate_minimal_directors_data():
    """Generate minimal data — only the required fields.

    All other fields are empty/null. Use for mandatory field validation tests.
    """
    return {
        "party_reference": None,
        "prefix": generate_prefix_id(),
        "director_name": generate_director_name(),
        "designation": generate_designation_id(),
        "pan_no": generate_pan_number(),
        "residential_address": generate_residential_address(),
        "phone_number": generate_phone(),
        "date_of_appointment": generate_date_of_appointment(),
        "date_of_cessation": None,
        "no_class_shares_held": generate_share_class(),
        "details_of_other_directorships": generate_details_of_other_directorships(),
        "percentage_of_shares": generate_percentage_of_shares(),
        "age": generate_age(),
        "qualification": generate_qualification_id(),
        "experience_in_years": generate_experience_in_years(),
        "kyc_details": [],
    }


def generate_empty_directors_data():
    """Generate data with all fields empty/null — for validation testing."""
    return {
        "party_reference": None,
        "prefix": None,
        "director_name": "",
        "designation": None,
        "pan_no": "",
        "residential_address": "",
        "phone_number": None,
        "date_of_appointment": None,
        "date_of_cessation": None,
        "no_class_shares_held": "",
        "details_of_other_directorships": "",
        "percentage_of_shares": None,
        "age": None,
        "qualification": None,
        "experience_in_years": None,
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
    """Generate a director name with numbers."""
    return "Rajesh123"


def generate_invalid_name_special_chars():
    """Generate a director name with special characters."""
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


def generate_negative_amount():
    """Generate a negative amount for percentage_of_shares."""
    return -5


def generate_zero_percentage():
    """Generate zero for percentage_of_shares."""
    return 0


def generate_percentage_over_100():
    """Generate a percentage over 100."""
    return 150


def generate_negative_age():
    """Generate a negative age."""
    return -1


def generate_zero_age():
    """Generate zero for age."""
    return 0


def generate_very_high_age():
    """Generate an unreasonably high age."""
    return 200


def generate_negative_experience():
    """Generate negative experience in years."""
    return -5


def generate_zero_experience():
    """Generate zero experience in years."""
    return 0


def generate_very_high_experience():
    """Generate unreasonably high experience in years."""
    return 100


def generate_sql_injection_name():
    """Generate a SQL injection string for Director Name."""
    return "'; DROP TABLE party_master; --"


def generate_xss_name():
    """Generate an XSS payload string for Director Name."""
    return "<script>alert('xss')</script>"


def generate_spaces_only_name():
    """Generate a name that's only spaces."""
    return "     "


def generate_long_other_directorships():
    """Generate an extremely long string for details_of_other_directorships."""
    return "A" * 500


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
# COMPLEX SCREEN STRUCTURE (Directors):
#   Directors has 1 stepper child: KYC Details (grid)
#
#   {
#     "id": "",
#     "attribute_name": "Directors",
#     "party_ref_id": null,
#     "prefix_ref_id": 1896,
#     "name": "Rajesh Sharma",
#     "designation": 30,
#     "pan_no": "ABCDE1234F",
#     "residential_address": "45 MG Road, Pune",
#     "mobile_no": 9876543210,
#     "date_of_appointment": "2025-06-15T18:30:00Z",
#     "date_of_cessation": null,
#     "no_class_shares_held": "100 Equity",
#     "details_of_other_directorships": "None",
#     "percentage_of_shares": 15,
#     "age": 45,
#     "qualification_ref_id": 511,
#     "experience_in_years": 20,
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
#   UI key                            → API field_key
#   ────────────────────────────────────────────────────────
#   party_reference                   → party_ref_id (dropdown FK, skip = null)
#   prefix                            → prefix_ref_id (dropdown FK)
#   director_name                     → name (string)
#   designation                       → designation (dropdown FK - integer ID)
#   pan_no                            → pan_no (string)
#   residential_address               → residential_address (string)
#   phone_number                      → mobile_no (integer)
#   date_of_appointment               → date_of_appointment (date string)
#   date_of_cessation                 → date_of_cessation (date string or null)
#   no_class_shares_held              → no_class_shares_held (string)
#   details_of_other_directorships    → details_of_other_directorships (string)
#   percentage_of_shares              → percentage_of_shares (integer)
#   age                               → age (integer)
#   qualification                     → qualification_ref_id (dropdown FK)
#   experience_in_years               → experience_in_years (integer)
#   kyc_details                       → children[0].details[] (grid rows)
#
# IMPORTANT RULES:
#   - Use null (None) for optional FK fields when not set
#   - "id" must be "" (empty string) for new entries
#   - mobile_no must be an INTEGER, not a string
#   - designation is an INTEGER FK ID, not a string
#   - qualification_ref_id is an INTEGER FK ID
#   - age and experience_in_years are INTEGER
#   - percentage_of_shares is INTEGER
#   - no_class_shares_held must be a STRING like "100 Equity"
#   - details_of_other_directorships is a required STRING
#   - details must be empty array []
#   - children must have the KYC Details stepper structure
#   - Each KYC row needs "id": "" for new entries
# ──────────────────────────────────────────────

def build_directors_api_payload(
    directors_data: dict = None,
    fk_ids: dict = None,
) -> dict:
    """
    Build the JSON payload for POST /core/dynamic-screen-wrapper/.

    The Directors screen has 1 stepper child (KYC Details) with a grid
    of document rows.

    Args:
        directors_data: Dict from generate_valid_directors_data().
                        If None, generates random data automatically.
        fk_ids: Optional dict of FK ID overrides. Keys should match
                API field names: prefix_ref_id, designation,
                qualification_ref_id, party_ref_id, kyc_doc_id.
                If None, uses random IDs from verified pools.

    Returns:
        Complete JSON payload dict ready for POST.

    Example:
        payload = build_directors_api_payload()
        client.create_entry(payload)
    """
    if directors_data is None:
        directors_data = generate_valid_directors_data()

    if fk_ids is None:
        fk_ids = {}

    # Resolve FK IDs: explicit > data > random pool > None
    prefix_ref_id = fk_ids.get("prefix_ref_id")
    if prefix_ref_id is None and directors_data.get("prefix") is not None:
        prefix_ref_id = directors_data["prefix"]
    if prefix_ref_id is None:
        prefix_ref_id = generate_prefix_id()

    designation = fk_ids.get("designation")
    if designation is None and directors_data.get("designation") is not None:
        designation = directors_data["designation"]
    if designation is None:
        designation = generate_designation_id()

    qualification_ref_id = fk_ids.get("qualification_ref_id")
    if qualification_ref_id is None and directors_data.get("qualification") is not None:
        qualification_ref_id = directors_data["qualification"]
    if qualification_ref_id is None:
        qualification_ref_id = generate_qualification_id()

    party_ref_id = fk_ids.get("party_ref_id")
    if party_ref_id is None and directors_data.get("party_reference") is not None:
        party_ref_id = directors_data["party_reference"]

    # Build KYC Details stepper children
    kyc_rows = directors_data.get("kyc_details", [])
    if not kyc_rows:
        # Generate default KYC row
        kyc_doc_id = fk_ids.get("kyc_doc_id", generate_kyc_doc_id())
        kyc_rows = [generate_valid_kyc_row(kyc_doc_id)]

    # fk_ids kyc_doc_id override: if explicitly provided, override all KYC rows
    fk_kyc_override = fk_ids.get("kyc_doc_id")

    kyc_details = []
    for row in kyc_rows:
        row_kyc_doc = fk_kyc_override if fk_kyc_override is not None else row.get("kyc_doc_id", generate_kyc_doc_id())
        kyc_entry = {
            "id": "",
            "kyc_doc_id": row_kyc_doc,
            "kyc_account_no": row.get("kyc_account_no", generate_kyc_number(row_kyc_doc)) if fk_kyc_override is None else generate_kyc_number(row_kyc_doc),
            "attachment_path": row.get("attachment_path", None),
            "details": [],
        }
        kyc_details.append(kyc_entry)

    # Build the complete payload
    payload = {
        "id": "",
        "attribute_name": "Directors",
        "copy_from_party": None,
        "party_ref_id": party_ref_id,
        "prefix_ref_id": prefix_ref_id,
        "name": directors_data.get("director_name") or generate_director_name(),
        "designation": designation,
        "pan_no": directors_data.get("pan_no") or generate_pan_number(),
        "residential_address": directors_data.get("residential_address") or generate_residential_address(),
        "mobile_no": directors_data.get("phone_number") or generate_phone(),
        "date_of_appointment": directors_data.get("date_of_appointment") or generate_date_of_appointment(),
        "date_of_cessation": directors_data.get("date_of_cessation", None),
        "no_class_shares_held": directors_data.get("no_class_shares_held") or generate_share_class(),
        "details_of_other_directorships": directors_data.get("details_of_other_directorships") or "NA",
        "percentage_of_shares": directors_data.get("percentage_of_shares") or generate_percentage_of_shares(),
        "age": directors_data.get("age") or generate_age(),
        "qualification_ref_id": qualification_ref_id,
        "experience_in_years": directors_data.get("experience_in_years") or generate_experience_in_years(),
        "details": [],
        "children": [
            {
                "stepper_name": "KYC Details",
                "is_stepper": True,
                "details": kyc_details,
                "children": [],
            }
        ],
    }

    return payload


def generate_directors_api_payload(**kwargs) -> dict:
    """One-shot: generate a randomized Directors API payload.

    This is the convenience function for batch_create scripts.
    Just call it and get a ready-to-POST payload.

    Args:
        **kwargs: Optional overrides for any payload field.
                  e.g., name="John", designation=30, qualification_ref_id=511

    Returns:
        Complete JSON payload dict ready for POST.

    Example:
        # Random director
        payload = generate_directors_api_payload()

        # With specific designation
        payload = generate_directors_api_payload(designation=30)

        # Override specific fields
        payload = generate_directors_api_payload(name="Test User", age=50)
    """
    data = generate_valid_directors_data()
    payload = build_directors_api_payload(data)

    # Apply any overrides
    payload.update(kwargs)

    return payload


# ──────────────────────────────────────────────
# Batch generation helpers
# ──────────────────────────────────────────────

def generate_batch_payloads(count: int, offset: int = 0, **kwargs) -> list:
    """Generate multiple unique Directors API payloads.

    Args:
        count: Number of payloads to generate.
        offset: Start index in data pool (used to seed variety).
        **kwargs: Optional overrides applied to ALL payloads.

    Returns:
        List of payload dicts.

    Example:
        payloads = generate_batch_payloads(10)
        payloads = generate_batch_payloads(5, designation=30, qualification_ref_id=511)
    """
    payloads = []
    for i in range(count):
        p = generate_directors_api_payload(**kwargs)
        payloads.append(p)
    return payloads


# ──────────────────────────────────────────────
# SweetAlert title constants
# ──────────────────────────────────────────────

SWAL_TITLE_VALIDATION_FAILED = "Validation Failed"
SWAL_TITLE_SUCCESS = "Your record has been added successfully!"
SWAL_TITLE_UPDATED = "Your record has been updated successfully!"


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
            "residential_address", "designation",
        ],
        "fk_options_count": 357,
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
        "label": "Director Name",
        "type": "character",
        "required": True,
        "max_length": 255,
        "visible_in_table": True,
    },
    "designation": {
        "field_key": "designation",
        "label": "Designation",
        "type": "dropdown",
        "required": True,
        "fk_options_count": 56,
    },
    "pan_no": {
        "field_key": "pan_no",
        "label": "PAN/Other",
        "type": "character",
        "required": True,
        "max_length": 255,
        "visible_in_table": True,
        "unique": True,
    },
    "residential_address": {
        "field_key": "residential_address",
        "label": "Residential Address",
        "type": "character",
        "required": True,
        "max_length": 255,
    },
    "mobile_no": {
        "field_key": "mobile_no",
        "label": "Phone Number",
        "type": "integer",
        "required": True,
        "max_length": 10,
        "visible_in_table": True,
    },
    "date_of_appointment": {
        "field_key": "date_of_appointment",
        "label": "Date of Appointment",
        "type": "date",
        "required": True,
    },
    "date_of_cessation": {
        "field_key": "date_of_cessation",
        "label": "Date of Cessation",
        "type": "date",
        "required": False,
    },
    "no_class_shares_held": {
        "field_key": "no_class_shares_held",
        "label": "Number and Class of Shares",
        "type": "character",
        "required": True,
        "max_length": 255,
    },
    "details_of_other_directorships": {
        "field_key": "details_of_other_directorships",
        "label": "NA",
        "type": "character",
        "required": True,
        "max_length": 255,
    },
    "percentage_of_shares": {
        "field_key": "percentage_of_shares",
        "label": "Percentage of Shares",
        "type": "integer",
        "required": True,
    },
    "age": {
        "field_key": "age",
        "label": "Age",
        "type": "integer",
        "required": True,
    },
    "qualification_ref_id": {
        "field_key": "qualification_ref_id",
        "label": "Qualification",
        "type": "dropdown",
        "required": True,
        "fk_options_count": 6,
    },
    "experience_in_years": {
        "field_key": "experience_in_years",
        "label": "Experience in Years",
        "type": "integer",
        "required": True,
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
