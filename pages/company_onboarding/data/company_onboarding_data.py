"""
company_onboarding_data.py
---------------------------
Test data for Company Onboarding screen.

Location: Master Setup > Company Onboarding
URL:      /#/dynamic-screens/Company%20Onboarding

UI STEPPER LAYOUT (6 steps):
  Step 1 = Company Details (including Company Code — maxlength 4)
  Step 2 = Promoters
  Step 3 = Address
  Step 4 = Business Details
  Step 5 = Infrastructure
  Step 6 = Configuration (Base Currency)

API STEPPER LAYOUT (5 steppers — Configuration merged into Company Details):
  Stepper 0 = "Company Details"   (NOT a grid — fields on stepper object)
  Stepper 1 = "Promoters Details" (GRID — rows in details[])
  Stepper 2 = "Address Details"   (GRID — rows in details[])
  Stepper 3 = "Business Activities" (GRID — rows in details[])
  Stepper 4 = "Infrastructure Details" (GRID — rows in details[])

API STRUCTURE (from live schema, verified 2026-06-03):
  POST /core/dynamic-screen-wrapper/
  {
    "id": "",
    "attribute_name": "Company Onboarding",
    "name": "...",                    # Root: Company Name (REQ, max=255)
    "user_type_id": 12,              # Root: Entity Group (FK, REQ)
    "parent_id": null,                # Root: Parent Name (FK, REQ, dynamic)
    "tenant_linked": [],              # Root: Company Linked (multiselect FK, REQ)
    "level": "2",                     # Root: Level (REQ, max=10)
    "is_parent": false,               # Root: Is Parent (toggle)
    "children": [
      {
        "stepper_name": "Company Details",
        "is_stepper": true,
        "details": [],                # NOT a grid — fields ON stepper object
        "children": [],
        "tenant_short_name": "...",    # (REQ, max=255)
        "tenant_code": "...",          # (REQ, max=4)
        "contact_person_name": "...",  # (REQ, max=255)
        "company_background": "...",   # (REQ, textarea)
        "email_id": "...",             # (REQ, max=255, email pattern)
        "phone_no": "...",             # (REQ, max=10)
        "pan_no": "...",               # (REQ, max=15)
        "tan_no": null,                # (max=15)
        "gst_no": "...",               # (max=15)
        "cin_no": "...",               # (REQ, max=21)
        "plan_type_ref_id": null,      # (dropdown)
        "is_2fa_applicable": false,    # (toggle)
        "authentication_type": "email", # (dropdown: email|scanner)
        "base_currency": 8,            # (REQ, FK, INR=8)
      },
      {
        "stepper_name": "Promoters Details",
        "is_stepper": true,
        "details": [{ "promoter_name": "...", "remark": "..." }],
        "children": [],
      },
      {
        "stepper_name": "Address Details",
        "is_stepper": true,
        "details": [{
          "address_type_ref_id": 1649,  # (FK, REQ)
          "country": 8,                  # (FK, REQ, cascading)
          "state": 98,                   # (FK, REQ, cascading)
          "district": 480,               # (FK, REQ, cascading)
          "taluka": 11542,               # (FK, REQ, cascading)
          "address": "...",              # (REQ, max=255)
          "pin_code": "411001",          # (REQ, max=6)
        }],
        "children": [],
      },
      {
        "stepper_name": "Business Activities",
        "is_stepper": true,
        "details": [{
          "business_model": "...",       # (max=100)
          "market_linkages": "...",      # (max=255)
          "line_of_business": "...",     # (max=255)
          "additional_business_activities": "...", # (max=255)
        }],
        "children": [],
      },
      {
        "stepper_name": "Infrastructure Details",
        "is_stepper": true,
        "details": [{
          "infrastructure_type_ref_id": 1585, # (FK)
          "location": "...",                  # (max=50)
          "ownership_type": 531,              # (FK)
          "remarks": "...",                   # (textarea)
        }],
        "children": [],
      },
    ]
  }

KEY RULES:
  - Company Details stepper is NOT a grid: fields live ON the stepper object,
    details[] must be empty (same pattern as Customer's Additional Details)
  - All other steppers ARE grids: rows go in details[] arrays
  - Base Currency is in Company Details stepper (NOT a separate Configuration stepper)
  - authentication_type uses STRING values ("email" / "scanner"), not integer IDs
  - parent_id and tenant_linked are dynamic (depend on tenant hierarchy)
  - Address cascading: country -> state -> district -> taluka
"""

import random
import string
import uuid
from datetime import datetime


# ================================================================
# 0. VALID ADDRESS DATA (State -> District -> Taluka)
# ================================================================
COMPANY_BACKGROUNDS = [
    "Software development and IT consulting services",
    "Manufacturing and industrial solutions",
    "Financial services and banking operations",
    "Healthcare and pharmaceutical research",
    "E-commerce and digital retail platforms",
    "Telecommunications and networking infrastructure",
    "Education and e-learning technology solutions",
    "Logistics and supply chain management",
    "Real estate and construction development",
    "Agriculture and food processing industries",
]


# ================================================================
# PROMOTER DATA (random 1 per company)
# ================================================================
PROMOTER_DATA = [
    {"name": "Mr Chaitnya Namdev Chavhan", "remark": "Mr Chavhan."},
    {"name": "Mr Durgesh Vishnu Bankar", "remark": "Mr Bankar."},
    {"name": "Mr Amit Ramesh Sharma", "remark": "Mr Sharma."},
    {"name": "Mr Suresh Dnyaneshwar Patil", "remark": "Mr Patil."},
    {"name": "Mr Rajesh Bhimrao Jadhav", "remark": "Mr Jadhav."},
    {"name": "Mr Vikram Anil Deshmukh", "remark": "Mr Deshmukh."},
]

# ================================================================
# BUSINESS DETAILS (fixed values from mentor)
# ================================================================
BUSINESS_MODEL = "Agri-Input - Products and materials."

MARKET_LINKAGES = "Market linkage involves connecting farmers."

LINE_OF_BUSINESS = "Products and materials used by farmers."

ADDITIONAL_BUSINESS_ACTIVITIES = "FPC carries out the business of Production."

# ================================================================
# INFRASTRUCTURE DATA
# ================================================================
INFRASTRUCTURE_LOCATIONS = [
    "Main Market Yard, Agricultural Produce",
    "Rural Hub Center, District HQ",
    "Cooperative Society Building, Taluka",
    "Agricultural Processing Unit, Industrial Area",
    "FPC Operations Center, Village Panchayat",
]

# ================================================================
# BASE CURRENCY OPTIONS
# ================================================================
BASE_CURRENCY_OPTIONS = ["INR"]

# ================================================================
# ADDRESS DATA (State -> District -> Taluka)
# ================================================================
ADDRESS_DATA = {
    "ANDHRA PRADESH": {
        "CHITTOOR": ["Baireddipalle", "Bangarupalem"],
        "EAST GODAVARI": ["Anaparthi", "Biccavolu", "Chagallu"],
        "GUNTUR": ["Amaravathi", "Amruthalur", "Bapatla"],
        "KRISHNA": ["Avanigadda", "Bantumilli"],
        "Visakhapatnam": ["Anandapuram", "Bheemunipatnam"],
        "Y.S.R.": ["Atlur", "B.Kodur"],
    },
    "GUJARAT": {
        "AHMADABAD": ["Asarva", "Bavla", "Daskroi", "Sanand", "Viramgam"],
        "AMRELI": ["Amreli", "Babra"],
        "ANAND": ["Anand City", "Borsad", "Khambhat", "Petlad"],
        "GANDHINAGAR": ["Dehgam", "Gandhinagar", "Kalol Gandhinagar", "Mansa"],
        "RAJKOT": ["Dhoraji", "Gondal", "Jasdan", "Rajkot", "Upleta"],
        "SURAT": ["Adajan", "Bardoli", "Kamrej", "Olpad", "Udhna"],
        "VADODARA": ["Dabhoi", "Karjan", "Padra", "Savli", "Vadodara East"],
    },
    "KARNATAKA": {
        "BENGALURU URBAN": ["Anekal", "Bengaluru East", "Bengaluru North", "Bengaluru South"],
        "MYSURU": ["Hunsur", "Mysuru", "Nanjangud", "Piriyapatna"],
        "DAKSHINA KANNADA": ["Bantval", "Mangaluru", "Puttur"],
        "DHARWAD": ["Dharwad", "Hubballi", "Kalghatgi"],
        "BELAGAVI": ["Athni", "Chikodi", "Gokak", "Khanapur"],
    },
    "MADHYA PRADESH": {
        "BHOPAL": ["Berasia", "Huzur", "Kolar"],
        "INDORE": ["Depalpur", "Indore", "Mhow", "Rau"],
        "JABALPUR": ["Jabalpur", "Patan", "Sihora"],
        "UJJAIN": ["Badnagar", "Mahidpur", "Ujjain"],
        "GWALIOR": ["Bhitarwar", "Gird", "Murar"],
    },
    "MAHARASHTRA": {
        "PUNE": ["Ambegaon", "Baramati", "Haveli", "Junnar", "Maval", "Mulshi", "Pune City"],
        "MUMBAI": ["Mumbai City", "Mumbai Suburban"],
        "NAGPUR": ["Hingna", "Kamptee", "Nagpur (Rural)", "Ramtek"],
        "NASHIK": ["Igatpuri", "Malegaon", "Nashik", "Sinnar"],
        "NAGPUR": ["Hingna", "Kamptee", "Nagpur (Rural)", "Ramtek", "Savner"],
        "THANE": ["Ambarnath", "Kalyan", "Shahapur", "Thane"],
    },
}

# ================================================================
# STATE -> VALID PIN CODE RANGES
# ================================================================
STATE_PIN_RANGES = {
    "ANDHRA PRADESH": (500000, 535999),
    "GUJARAT":        (360000, 396999),
    "KARNATAKA":      (560000, 591999),
    "MADHYA PRADESH": (450000, 488999),
    "MAHARASHTRA":    (400000, 445999),
}


def _get_random_address():
    """Pick a valid state -> district -> taluka + matching pin code from ADDRESS_DATA."""
    state = random.choice(list(ADDRESS_DATA.keys()))
    district = random.choice(list(ADDRESS_DATA[state].keys()))
    taluka = random.choice(ADDRESS_DATA[state][district])
    pin_start, pin_end = STATE_PIN_RANGES.get(state, (400000, 499999))
    pin_code = str(random.randint(pin_start, pin_end))
    return state, district, taluka, pin_code


# ================================================================
# 1. SINGLE COMPANY — generates unique data every time
# ================================================================

def _generate_single_company():
    """
    Generate a unique SINGLE_COMPANY dict each time it's called.
    Uses UUID suffix + timestamp to guarantee uniqueness across runs.
    """
    uid = uuid.uuid4().hex[:4].upper()
    ts = datetime.now().strftime("%H%M%S")

    prefix = random.choice(["Apex", "Zenith", "Nova", "Pulse", "Vertex", "Orion"])
    suffix = random.choice(["Technologies", "Solutions", "Services", "Systems", "Enterprises"])
    middle = random.choice(["Global", "Prime", "Digital", "Smart", "Green", "Royal", "Elite", "Max", "Core", "Link"])
    company_name = f"{prefix} {middle} {suffix}"

    first = random.choice(["Aarav", "Vedant", "Arjun", "Rohan", "Nikhil", "Priya", "Sneha"])
    last = random.choice(["Sharma", "Patil", "Desai", "Joshi", "Kulkarni", "Mehta", "Pawar"])

    pan_prefix = "".join(random.choices(string.ascii_uppercase, k=5))
    pan_digits = "".join(random.choices(string.digits, k=4))
    pan = f"{pan_prefix}{pan_digits}F"

    cin_random = "".join(random.choices(string.digits, k=5))
    cin_year = random.choice(["2020", "2021", "2022", "2023", "2024", "2025"])
    cin_num = "".join(random.choices(string.digits, k=6))
    cin = f"U{cin_random}MH{cin_year}PTC{cin_num}"

    gst_state = random.choice(["27", "29", "33", "24", "08"])
    gstin = f"{gst_state}{pan_prefix[:5]}{pan_digits}A1Z5"

    mobile = f"9{random.randint(100000000, 999999999)}"

    state, district, taluka, pin_code = _get_random_address()

    # Company Code: 4-character alphanumeric
    company_code = prefix[:2].upper() + middle[:2].upper()

    return {
        "company_name": company_name,
        "company_code": company_code,
        "entity_group": "FPC",
        "parent_name": "Agdi",
        "company_linked": ["Agdi"],
        "company_short_name": f"{prefix[:3]}{middle[:3]}{suffix[:3]}",
        "contact_name": f"{first} {last}",
        "company_background": "Software development and IT consulting services",
        "email": f"{first.lower()}.{last.lower()}{uid}@testmail.com",
        "mobile_number": mobile,
        "pan": pan,
        "gstin": gstin,
        "cin": cin,
        "is_2fa": False,
        "address_type": "Registered Address",
        "country": "India",
        "state": state,
        "district": district,
        "taluka": taluka,
        "address": f"{uid}, Test Street, {taluka}",
        "pin_code": pin_code,
        "promoters": random.sample(PROMOTER_DATA, 2),
        "business_model": BUSINESS_MODEL,
        "market_linkages": MARKET_LINKAGES,
        "line_of_business": LINE_OF_BUSINESS,
        "additional_business_activities": ADDITIONAL_BUSINESS_ACTIVITIES,
        "infra_location": random.choice(INFRASTRUCTURE_LOCATIONS),
        "base_currency": "INR",
        "num_addresses": 2,
        "num_business_rows": 2,
        "num_infra_rows": 2,
    }


# Call it once at import time — unique every run
SINGLE_COMPANY = _generate_single_company()


# ================================================================
# 2. LOOKUP TABLES
# ================================================================

COMPANY_PREFIXES = [
    "Apex", "Zenith", "Nova", "Pulse", "Vertex", "Orion", "Nexus", "Prism",
    "Crest", "Forge", "Ember", "Atlas", "Solaris", "Quantum", "Helix", "Titan",
    "Cobalt", "Sterling", "Radiant", "Catalyst", "Pinnacle", "Vanguard", "Echo",
    "Matrix", "Vector", "Horizon", "Summit", "Cedar", "Flux", "Aether", "Lunar",
]

COMPANY_SUFFIXES = [
    "Technologies", "Industries", "Enterprises", "Solutions", "Systems",
    "Services", "Corporation", "Holdings", "Group", "Ventures",
    "Analytics", "Innovations", "Dynamics", "Networks", "Infra",
]

COMPANY_MIDDLE_WORDS = [
    "Global", "Prime", "East", "West", "North", "South", "Central",
    "Digital", "Smart", "Green", "Royal", "Golden", "Elite", "Premium",
]

ENTITY_GROUP_OPTIONS = ["FPC"]
PARENT_NAME_OPTIONS = ["Agdi"]
COMPANY_LINKED_OPTIONS = [["Agdi"]]

CONTACT_FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vedant", "Arjun", "Sai", "Rohan",
    "Amit", "Nikhil", "Prashant", "Suresh", "Mahesh", "Rajesh",
    "Priya", "Pooja", "Sneha", "Neha", "Anita", "Kavita", "Swati",
]

CONTACT_LAST_NAMES = [
    "Sharma", "Patil", "Desai", "Joshi", "Kulkarni", "Mehta", "Shah",
    "Pawar", "Jadhav", "Chavan", "Bhosale", "More", "Kale", "Gaikwad",
]

COUNTRY_OPTIONS = ["India"]


# ================================================================
# 3. BULK DATA GENERATOR
# ================================================================

def generate_bulk_companies(count=1000, start_index=1):
    """Generate a list of unique company data dicts."""
    companies = []

    for i in range(start_index, start_index + count):
        uid_suffix = uuid.uuid4().hex[:6].upper()

        prefix = random.choice(COMPANY_PREFIXES)
        middle = random.choice(COMPANY_MIDDLE_WORDS)
        background = random.choice(COMPANY_BACKGROUNDS)
        suffix = random.choice(COMPANY_SUFFIXES)
        company_name = f"{prefix} {middle} {suffix}"

        short_name = f"{prefix[:3]}{middle[:3]}{suffix[:3]}"
        company_code = prefix[:2].upper() + middle[:2].upper()

        first_name = random.choice(CONTACT_FIRST_NAMES)
        last_name = random.choice(CONTACT_LAST_NAMES)
        contact_name = f"{first_name} {last_name}"

        email_user = f"{first_name.lower()}.{last_name.lower()}{i}"
        email_domains = ["company.com", "corp.in", "enterprise.in", "testmail.com"]
        email = f"{email_user}@{random.choice(email_domains)}"

        mobile = f"9{random.randint(100000000, 999999999)}"

        pan_prefix = "".join(random.choices(string.ascii_uppercase, k=5))
        pan_digits = f"{i:04d}"[-4:]
        pan = f"{pan_prefix}{pan_digits}F"

        cin_random = "".join(random.choices(string.digits, k=5))
        cin_year = random.choice(["2020", "2021", "2022", "2023", "2024", "2025"])
        cin_num = f"{i:06d}"
        cin = f"U{cin_random}MH{cin_year}PTC{cin_num}"

        gst_state_code = random.choice(["27", "29", "33", "24", "08"])
        gst_pan_part = pan_prefix[:5] + pan_digits
        gstin = f"{gst_state_code}{gst_pan_part}A1Z5"

        entity_group = random.choice(ENTITY_GROUP_OPTIONS)
        parent_name = random.choice(PARENT_NAME_OPTIONS)
        company_linked = random.choice(COMPANY_LINKED_OPTIONS)

        state, district, taluka, pin_code = _get_random_address()
        address_line = f"{i}, Test Street, {taluka}"

        company = {
            "company_name": company_name,
            "company_code": company_code,
            "entity_group": entity_group,
            "parent_name": parent_name,
            "company_linked": company_linked,
            "company_short_name": short_name,
            "contact_name": contact_name,
            "company_background": background,
            "email": email,
            "mobile_number": mobile,
            "pan": pan,
            "gstin": gstin,
            "cin": cin,
            "plan_type": "",
            "is_2fa": False,
            "address_type": "Registered Address",
            "country": "India",
            "state": state,
            "district": district,
            "taluka": taluka,
            "address": address_line,
            "pin_code": pin_code,
            "promoters": random.sample(PROMOTER_DATA, 2),
            "business_model": BUSINESS_MODEL,
            "market_linkages": MARKET_LINKAGES,
            "line_of_business": LINE_OF_BUSINESS,
            "additional_business_activities": ADDITIONAL_BUSINESS_ACTIVITIES,
            "infra_location": random.choice(INFRASTRUCTURE_LOCATIONS),
            "base_currency": "INR",
            "num_addresses": 2,
            "num_business_rows": 2,
            "num_infra_rows": 2,
        }

        companies.append(company)

    return companies


# ================================================================
# 4. UTILITY — EXPORT TO EXCEL / CSV
# ================================================================

def save_bulk_data_to_excel(companies, filepath="bulk_companies.xlsx"):
    try:
        import pandas as pd
        df = pd.DataFrame(companies)
        for col in ["business_type", "business_model", "company_linked"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        df.to_excel(filepath, index=False, engine="openpyxl")
        print(f"Saved {len(companies)} companies to: {filepath}")
        return True
    except ImportError:
        print("ERROR: pandas and openpyxl are required.")
        return False


def save_bulk_data_to_csv(companies, filepath="bulk_companies.csv"):
    try:
        import csv
        if not companies:
            print("No data to save")
            return False
        flat_companies = []
        for c in companies:
            row = {}
            for k, v in c.items():
                if isinstance(v, list):
                    row[k] = ", ".join(v)
                else:
                    row[k] = v
            flat_companies.append(row)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=flat_companies[0].keys())
            writer.writeheader()
            writer.writerows(flat_companies)
        print(f"Saved {len(companies)} companies to: {filepath}")
        return True
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return False


# ================================================================
# 5. VALIDATION TEST DATA HELPERS
# ================================================================

def generate_company_code_4_chars():
    """Generate a valid 4-character Company Code."""
    return "".join(random.choices(string.ascii_uppercase, k=4))


def generate_company_code_5_chars():
    """Generate a 5-character Company Code (exceeds maxlength=4)."""
    return "".join(random.choices(string.ascii_uppercase, k=5))


def generate_company_code_empty():
    """Return empty Company Code for required field test."""
    return ""


def generate_company_code_spaces():
    """Return spaces-only Company Code for validation test."""
    return "    "


# ================================================================
# 6. QUICK STANDALONE TEST
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" COMPANY ONBOARDING DATA GENERATOR")
    print("=" * 60)

    print("\n[SINGLE COMPANY TEMPLATE]")
    print("-" * 40)
    for key, value in SINGLE_COMPANY.items():
        if isinstance(value, list):
            print(f"  {key:25s}: {', '.join(str(v) for v in value)}")
        else:
            print(f"  {key:25s}: {value}")

    print("\n[BULK GENERATION - 5 SAMPLE]")
    print("-" * 40)
    samples = generate_bulk_companies(5)
    for i, company in enumerate(samples, 1):
        print(f"\n  Company {i}:")
        print(f"    Name         : {company['company_name']}")
        print(f"    Code         : {company['company_code']}")
        print(f"    Entity Group : {company['entity_group']}")
        print(f"    Base Currency: {company['base_currency']}")
        print(f"    Email        : {company['email']}")

    print("\n[API PAYLOAD SAMPLE]")
    print("-" * 40)
    import json
    payload = generate_company_onboarding_api_payload()
    print(json.dumps(payload, indent=2)[:1500])


# ──────────────────────────────────────────────────────────────
# API PAYLOAD INFRASTRUCTURE
# ──────────────────────────────────────────────────────────────
# Dropdown FK ID pools (verified on tenant 681, 2026-06-03)
# ──────────────────────────────────────────────────────────────

# Entity Group: only "Branch" available (level > current tenant)
ENTITY_GROUP_IDS = [12]
ENTITY_GROUP_NAMES = {12: "Branch"}

# Authentication Type: STRING values (NOT integer IDs)
AUTHENTICATION_TYPE_IDS = ["email", "scanner"]
AUTHENTICATION_TYPE_NAMES = {"email": "Email", "scanner": "Scanner"}

# Base Currency: 30 options from dynamic_models_country_mst
BASE_CURRENCY_IDS = [8, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
                     51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66]
BASE_CURRENCY_NAMES = {
    8: "INR", 38: "EGP", 39: "USD", 40: "GBP", 41: "CAD",
    42: "AUD", 43: "EUR", 44: "EUR", 45: "JPY", 46: "CNY",
    47: "BRL", 48: "RUB", 49: "EUR", 50: "EUR", 51: "MXN",
    52: "KRW", 53: "IDR", 54: "SAR", 55: "ZAR", 56: "ARS",
    57: "TRY", 58: "EUR", 59: "CHF", 60: "SEK", 61: "NOK",
    62: "DKK", 63: "THB", 64: "MYR", 65: "SGD", 66: "NZD",
}

# Address Type
ADDRESS_TYPE_IDS = [1649, 1650]
ADDRESS_TYPE_NAMES = {1649: "Registered Address", 1650: "Corporate Address"}

# Country: 30 options (same pool as Base Currency origin)
COUNTRY_IDS = [54, 55, 56, 8, 57, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
               48, 49, 50, 51, 52, 53, 58, 59, 60, 61, 62, 63, 64, 65, 66]
COUNTRY_NAMES = {
    54: "Saudi Arabia", 55: "South Africa", 56: "Argentina", 8: "India",
    57: "Turkey", 38: "Egypt", 39: "United States", 40: "United Kingdom",
    41: "Canada", 42: "Australia", 43: "Germany", 44: "France",
    45: "Japan", 46: "China", 47: "Brazil", 48: "Russia",
    49: "Italy", 50: "Spain", 51: "Mexico", 52: "South Korea",
    53: "Indonesia", 58: "Netherlands", 59: "Switzerland", 60: "Sweden",
    61: "Norway", 62: "Denmark", 63: "Thailand", 64: "Malaysia",
    65: "Singapore", 66: "New Zealand",
}

# Infrastructure Type
INFRASTRUCTURE_TYPE_IDS = [1585, 1584, 1877, 1878, 1879]
INFRASTRUCTURE_TYPE_NAMES = {
    1585: "Office Building", 1584: "Warehouse",
    1877: "Cold Storage Unit", 1878: "Processing Unit", 1879: "Other",
}

# Ownership Type
OWNERSHIP_TYPE_IDS = [531, 530]
OWNERSHIP_TYPE_NAMES = {531: "Leased", 530: "Owned"}

# Fixed defaults
DEFAULT_BASE_CURRENCY_ID = 8   # INR
DEFAULT_COUNTRY_ID = 8         # India

# Backward-compatible default FK IDs dict
DEFAULT_CO_FK_IDS = {
    "user_type_id": 12,               # Branch
    "base_currency": DEFAULT_BASE_CURRENCY_ID,
    "address_type_ref_id": 1649,       # Registered Address
    "country": DEFAULT_COUNTRY_ID,     # India
    "infrastructure_type_ref_id": 1585, # Office Building
    "ownership_type": 531,             # Leased
    "authentication_type": "email",     # Email (string, not int!)
}


# ──────────────────────────────────────────────────────────────
# FK Name Mappings (human-readable labels for each ID)
# ──────────────────────────────────────────────────────────────

# (Names already defined above as _NAMES dicts)


# ──────────────────────────────────────────────────────────────
# Field Validation Rules (schema documentation)
# ──────────────────────────────────────────────────────────────

FIELD_VALIDATION_RULES = {
    # Root-level fields
    "name": {"type": "character", "required": True, "max_length": 255},
    "user_type_id": {"type": "dropdown", "required": True, "fk_options_count": 1},
    "parent_id": {"type": "dropdown", "required": True, "fk_options_count": 0,
                  "note": "Dynamic — depends on tenant hierarchy"},
    "tenant_linked": {"type": "multiselect", "required": True, "fk_options_count": 0,
                      "note": "Dynamic — depends on tenant hierarchy"},
    "level": {"type": "character", "required": True, "max_length": 10},
    "is_parent": {"type": "toggle", "required": False, "default": False},

    # Company Details stepper (fields ON stepper object, NOT in details[])
    "tenant_short_name": {"type": "character", "required": True, "max_length": 255},
    "tenant_code": {"type": "character", "required": True, "max_length": 4},
    "contact_person_name": {"type": "character", "required": True, "max_length": 255},
    "company_background": {"type": "textarea", "required": True, "max_length": 10000000},
    "email_id": {"type": "character", "required": True, "max_length": 255,
                 "pattern": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"},
    "phone_no": {"type": "character", "required": True, "max_length": 10},
    "pan_no": {"type": "character", "required": True, "max_length": 15},
    "tan_no": {"type": "character", "required": False, "max_length": 15},
    "gst_no": {"type": "character", "required": False, "max_length": 15},
    "cin_no": {"type": "character", "required": True, "max_length": 21},
    "plan_type_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 0},
    "is_2fa_applicable": {"type": "toggle", "required": True, "default": False},
    "authentication_type": {"type": "dropdown", "required": False, "fk_options_count": 2,
                            "note": "String values: email, scanner"},
    "base_currency": {"type": "dropdown", "required": True, "fk_options_count": 30},

    # Promoters Details (children[1].details[])
    "promoter_name": {"type": "character", "required": False, "max_length": 100},
    "remark": {"type": "textarea", "required": False, "max_length": 10000000},

    # Address Details (children[2].details[])
    "address_type_ref_id": {"type": "dropdown", "required": True, "fk_options_count": 2},
    "country": {"type": "dropdown", "required": True, "fk_options_count": 30, "cascading": True},
    "state": {"type": "dropdown", "required": True, "fk_options_count": 0, "cascading": True},
    "district": {"type": "dropdown", "required": True, "fk_options_count": 0, "cascading": True},
    "taluka": {"type": "dropdown", "required": True, "fk_options_count": 0, "cascading": True},
    "address": {"type": "character", "required": True, "max_length": 255},
    "pin_code": {"type": "character", "required": True, "max_length": 6},

    # Business Activities (children[3].details[])
    "business_model": {"type": "character", "required": False, "max_length": 100},
    "market_linkages": {"type": "character", "required": False, "max_length": 255},
    "line_of_business": {"type": "character", "required": False, "max_length": 255},
    "additional_business_activities": {"type": "character", "required": False, "max_length": 255},

    # Infrastructure Details (children[4].details[])
    "infrastructure_type_ref_id": {"type": "dropdown", "required": False, "fk_options_count": 5},
    "location": {"type": "character", "required": False, "max_length": 50},
    "ownership_type": {"type": "dropdown", "required": False, "fk_options_count": 2},
    "remarks": {"type": "textarea", "required": False, "max_length": 10000000},
}


def get_random_address_chain():
    """Import and reuse the Supplier address chain pool for cascading FK IDs."""
    from pages.registration.modules.supplier.data.supplier_data import (
        get_random_address_chain as _supplier_chain,
    )
    return _supplier_chain(verified_only=True)


def generate_random_fk_ids() -> dict:
    """Generate a set of random FK IDs for Company Onboarding dropdown variety."""
    return {
        "user_type_id": random.choice(ENTITY_GROUP_IDS),
        "base_currency": DEFAULT_BASE_CURRENCY_ID,
        "address_type_ref_id": random.choice(ADDRESS_TYPE_IDS),
        "country": DEFAULT_COUNTRY_ID,
        "infrastructure_type_ref_id": random.choice(INFRASTRUCTURE_TYPE_IDS),
        "ownership_type": random.choice(OWNERSHIP_TYPE_IDS),
        "authentication_type": random.choice(AUTHENTICATION_TYPE_IDS),
    }


def generate_luhn_gstin(state_code=None):
    """Generate a valid GSTIN with Luhn mod-36 checksum.
    Reuses the Supplier function for correctness.
    """
    from pages.registration.modules.supplier.data.supplier_data import generate_gstin
    return generate_gstin(state_code)


def generate_realistic_email():
    """Generate a realistic email (same style as Supplier)."""
    from pages.registration.modules.supplier.data.supplier_data import generate_email
    return generate_email()


def generate_realistic_phone():
    """Generate a valid 10-digit Indian mobile number."""
    prefix = random.choice(["6", "7", "8", "9"])
    return f"{prefix}{random.randint(100000000, 999999999)}"


def generate_pan():
    """Generate a random PAN number in valid Indian format: ABCDE1234F."""
    letters = "".join(random.choices(string.ascii_uppercase, k=5))
    digits = "".join(random.choices(string.digits, k=4))
    last_letter = random.choice(string.ascii_uppercase)
    return f"{letters}{digits}{last_letter}"


def generate_cin():
    """Generate a random CIN in valid format: U12345MH2024PTC123456."""
    cin_random = "".join(random.choices(string.digits, k=5))
    cin_year = random.choice(["2020", "2021", "2022", "2023", "2024", "2025"])
    cin_num = "".join(random.choices(string.digits, k=6))
    return f"U{cin_random}MH{cin_year}PTC{cin_num}"


def generate_company_name():
    """Generate a unique company name."""
    prefix = random.choice(COMPANY_PREFIXES)
    middle = random.choice(COMPANY_MIDDLE_WORDS)
    suffix = random.choice(COMPANY_SUFFIXES)
    return f"{prefix} {middle} {suffix}"


def build_company_onboarding_api_payload(
    company_data: dict = None,
    dropdown_ids: dict = None,
) -> dict:
    """Build the complete Company Onboarding API payload from data + FK IDs.

    Args:
        company_data: Dict from _generate_single_company() or None for random.
        dropdown_ids: Dict of FK IDs. Missing keys fall back to DEFAULT_CO_FK_IDS.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    ids = {**DEFAULT_CO_FK_IDS, **(dropdown_ids or {})}

    def _fk(key):
        val = ids.get(key)
        return val if val is not None else None

    if company_data is None:
        company_data = _generate_single_company()

    # Get address chain for cascading FK IDs
    address_chain = get_random_address_chain()

    # ── Build Company Details stepper ──
    # NOTE: Company Details is NOT a grid, so fields go ON the stepper object,
    # and details[] must be EMPTY. This is the same pattern as Customer's
    # Additional Details stepper.
    company_details = {}
    company_details["tenant_short_name"] = company_data.get("company_short_name") or None
    company_details["tenant_code"] = company_data.get("company_code") or None
    company_details["contact_person_name"] = company_data.get("contact_name") or None
    company_details["company_background"] = company_data.get("company_background") or None
    company_details["email_id"] = company_data.get("email") or generate_realistic_email()
    company_details["phone_no"] = company_data.get("mobile_number") or generate_realistic_phone()
    company_details["pan_no"] = company_data.get("pan") or generate_pan()
    company_details["tan_no"] = None
    company_details["gst_no"] = company_data.get("gstin") or generate_luhn_gstin("27")
    company_details["cin_no"] = company_data.get("cin") or generate_cin()
    company_details["plan_type_ref_id"] = None
    company_details["is_2fa_applicable"] = company_data.get("is_2fa", False)
    company_details["authentication_type"] = _fk("authentication_type") or "email"
    company_details["base_currency"] = _fk("base_currency") or DEFAULT_BASE_CURRENCY_ID

    # ── Build Promoters Details (GRID — rows in details[]) ──
    promoter_rows = []
    for promoter in company_data.get("promoters", PROMOTER_DATA[:2]):
        promoter_rows.append({
            "promoter_name": promoter.get("name", ""),
            "remark": promoter.get("remark", ""),
        })

    # ── Build Address Details (GRID — rows in details[]) ──
    address_detail = {}
    address_detail["address_type_ref_id"] = _fk("address_type_ref_id")
    address_detail["country"] = _fk("country")
    address_detail["state"] = address_chain.get("state_ref_id_id")
    address_detail["district"] = address_chain.get("district_ref_id_id")
    address_detail["taluka"] = address_chain.get("sub_district_ref_id_id")
    address_detail["address"] = company_data.get("address") or "123 Test Street"
    pin = company_data.get("pin_code") or "411001"
    address_detail["pin_code"] = str(pin)

    # ── Build Business Activities (GRID — rows in details[]) ──
    business_detail = {}
    business_detail["business_model"] = company_data.get("business_model") or BUSINESS_MODEL
    business_detail["market_linkages"] = company_data.get("market_linkages") or MARKET_LINKAGES
    business_detail["line_of_business"] = company_data.get("line_of_business") or LINE_OF_BUSINESS
    business_detail["additional_business_activities"] = (
        company_data.get("additional_business_activities") or ADDITIONAL_BUSINESS_ACTIVITIES
    )

    # ── Build Infrastructure Details (GRID — rows in details[]) ──
    infra_detail = {}
    infra_detail["infrastructure_type_ref_id"] = _fk("infrastructure_type_ref_id")
    infra_detail["location"] = company_data.get("infra_location") or random.choice(INFRASTRUCTURE_LOCATIONS)
    infra_detail["ownership_type"] = _fk("ownership_type")
    infra_detail["remarks"] = None

    # ── Assemble payload ──
    payload = {
        "id": "",
        "attribute_name": "Company Onboarding",

        # Root-level fields
        "name": company_data.get("company_name") or generate_company_name(),
        "user_type_id": ids["user_type_id"],
        "parent_id": None,          # Dynamic — must be set at runtime
        "tenant_linked": [],        # Dynamic — must be set at runtime
        "level": "2",
        "is_parent": False,

        # Children array with stepper objects
        "children": [
            {
                "stepper_name": "Company Details",
                "is_stepper": True,
                "details": [],            # NOT a grid — fields on stepper itself
                "children": [],
                **company_details,        # Spread fields onto the stepper object
            },
            {
                "stepper_name": "Promoters Details",
                "is_stepper": True,
                "details": promoter_rows,
                "children": [],
            },
            {
                "stepper_name": "Address Details",
                "is_stepper": True,
                "details": [address_detail],
                "children": [],
            },
            {
                "stepper_name": "Business Activities",
                "is_stepper": True,
                "details": [business_detail],
                "children": [],
            },
            {
                "stepper_name": "Infrastructure Details",
                "is_stepper": True,
                "details": [infra_detail],
                "children": [],
            },
        ],
    }

    return payload


def generate_company_onboarding_api_payload(
    name_prefix=None,
    dropdown_ids: dict = None,
) -> dict:
    """One-shot: generate a complete Company Onboarding API payload with random data.

    Automatically randomizes:
      - Address chain (state/district/taluka)
      - Infrastructure type, ownership type
      - Address type, authentication type
      - PAN, CIN, GSTIN, email, phone

    Args:
        name_prefix: Optional prefix for the company name.
        dropdown_ids: Override specific FK IDs.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    company_data = _generate_single_company()
    if name_prefix:
        company_data["company_name"] = f"{name_prefix} {company_data['company_name']}"

    ids = {
        **generate_random_fk_ids(),
        **get_random_address_chain(),
        **(dropdown_ids or {}),
    }

    return build_company_onboarding_api_payload(company_data, ids)


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """Generate a batch of unique Company Onboarding API payloads.

    Args:
        count: Number of payloads to generate.
        prefix: Optional name prefix for all companies.
        dropdown_ids: Override specific FK IDs for ALL payloads.

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    payloads = []
    for i in range(count):
        pfx = prefix or f"CO{i+1:03d}"
        payload = generate_company_onboarding_api_payload(
            name_prefix=pfx,
            dropdown_ids=dropdown_ids,
        )
        payloads.append(payload)
    return payloads
