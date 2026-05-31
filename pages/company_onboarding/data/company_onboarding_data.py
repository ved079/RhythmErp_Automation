"""
company_onboarding_data.py
---------------------------
Test data for Company Onboarding screen.

6 Steps:
  Step 1 = Company Details (including Company Code — maxlength 4)
  Step 2 = Promoters
  Step 3 = Address
  Step 4 = Business Details
  Step 5 = Infrastructure
  Step 6 = Configuration (Base Currency)
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
