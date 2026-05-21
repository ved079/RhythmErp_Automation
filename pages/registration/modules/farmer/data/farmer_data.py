"""
farmer_data.py
--------------
Test data generators for RhythmERP Farmer screen.

Location: Registration > Farmer
URL:      /#/dynamic-screens/Farmer/Farmer

FORM LAYOUT (MULTI-STEP STEPPER — varies by Farmer Category):

  Step 0 — Farmer Details (ALWAYS VISIBLE):
    UNIVERSAL FIELDS (fill upper visible fields first, then scroll-down):
      - Farmer Name             (text input,   REQUIRED, maxlength=255)
      - Email                   (text input,   optional, maxlength=255)
      - Phone Number            (text input,   REQUIRED, maxlength=255)
      - Date Of Birth           (datepicker,   optional, format DD/MM/YYYY)
      - Age                     (number input, READONLY — auto-calculated from DOB)
      - Gender                  (mat-select,   optional)
      - Category                (mat-select,   optional)
      - Religion                (mat-select,   optional)
      - Password                (text input,   REQUIRED, maxlength=255)
      - Farmer Category         (mat-select MULTI, optional) ← DETERMINES STEPPER TABS
      - Land Classification     (mat-select,   optional)
    Non-universal fields:
      - Party Reference         (mat-select,   optional)
      - Photo Upload            (file upload,  optional)
      - Is Member of This FPC   (toggle switch, default OFF)

  Farmer Category determines stepper tabs:
    Walk-in Farmer → 3 tabs (Current Address, Permanent Address, Bank Details)
    FPC Member → 6 tabs (Current Address, Permanent Address, Land Details,
        Crop Details, KYC Details, Bank Details)
    Borrower Farmer → 13 tabs (Current Address, Permanent Address, Family Details,
        Other Details, Land Details, Crop Details, KYC Details, Vehicle Details,
        Income Details, Bank Details, Irrigation Details, Award Details, Loan Details)

  Address Tabs (Current/Permanent) — TABLE/GRID ROW with:
    - Country* (mat-select, required, cascading) ← ALWAYS "India"
    - State* (mat-select, required, cascading, depends on Country)
    - District* (mat-select, required, cascading, depends on State)
    - Taluka* (mat-select, required, cascading, depends on District)
    - Village (mat-select, optional, cascading, depends on Taluka)
    - Pin Code (text input, maxlength=255)
    - Address* (text input, required, maxlength=255)
    - Address2 (text input, optional, maxlength=255)

  Bank Details Tab:
    - Bank Name, Branch, IFSC Code, Account Type (Current/Saving),
      Account Holder Name, Account Number, Bank Proof (Cancelled Cheque/Passbook)

KEY BUSINESS RULES:
  - Country MUST ALWAYS be "India" — other countries lack cascading data
  - Fill upper/visible fields first, then scroll down for lower fields
  - Farmer Category must be filled LAST in Step 0 (triggers stepper tabs)

KNOWN BUGS:
  BUG-F01 (High):   No Of Owner required but no asterisk shown
  BUG-F02 (High):   Deselect+Reselect farmer category freezes Next/Back
  BUG-F03 (Medium): Farmer Name accepts special characters
  BUG-F04 (Medium): Email rejects uppercase letters
  BUG-F05 (Medium): Farmer Category placeholder is selectable
  BUG-F06 (Medium): Amount fields accept 0 and . prefix
  BUG-F07 (Low):    Source of Income shows Dairy twice
  BUG-F08 (Low):    Edit mode missing Land/Crop/KYC tabs
  BUG-F09 (Low):    Character count indicator disappears on validation error
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_farmer_name(prefix="AutoFarmer"):
    """Generate a random farmer name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_phone_number():
    """Generate a random 10-digit Indian phone number starting with 9/8/7."""
    first = random.choice(["9", "8", "7"])
    rest = "".join([str(random.randint(0, 9)) for _ in range(9)])
    return f"{first}{rest}"


def generate_email(name="autofarmer"):
    """Generate a random email address."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    domains = ["gmail.com", "yahoo.com", "outlook.com"]
    return f"{name}{timestamp}@{random.choice(domains)}".lower()


def generate_password():
    """Generate a valid password."""
    return "TestPass@12345"


def generate_pin_code():
    """Generate a random 6-digit Indian pin code."""
    return f"{random.randint(100000, 999999)}"


def generate_address():
    """Generate a random address string."""
    streets = [
        "Farm Road", "Village Lane", "Main Street",
        "Agriculture Colony", "Market Road", "Temple Street"
    ]
    return f"{random.randint(1, 999)} {random.choice(streets)}"


def generate_ifsc_code():
    """Generate a random IFSC code (4 letters + 0 + 6 digits)."""
    letters = "".join(random.choices(string.ascii_uppercase, k=4))
    digits = "".join([str(random.randint(0, 9)) for _ in range(6)])
    return f"{letters}0{digits}"


def generate_account_number():
    """Generate a random bank account number."""
    return f"{random.randint(100000000000, 999999999999)}"


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_farmer_step0(category="Walk-in Farmer"):
    """Generate a complete dict of valid farmer data for Step 0.

    UNIVERSAL FIELDS are listed first (upper visible fields that
    should be filled before scrolling down).
    Dropdown values set to None — will be populated from live UI at runtime.
    Farmer Category is filled LAST because it triggers stepper tab creation.
    """
    return {
        # === UNIVERSAL FIELDS (upper visible — fill first) ===
        "farmer_name": generate_farmer_name(),
        "email": generate_email(),
        "phone_number": generate_phone_number(),
        "date_of_birth": "01/01/1990",  # DD/MM/YYYY
        "age": None,                    # Auto-calculated (readonly)
        "gender": None,                 # Pick from live UI
        "category": None,               # Pick from live UI (social category)
        "religion": None,               # Pick from live UI
        "password": generate_password(),
        "farmer_category": category,    # "Borrower Farmer", "FPC Member", "Walk-in Farmer"
        "land_classification": None,    # Pick from live UI
        # === NON-UNIVERSAL FIELDS (may need scrolling) ===
        "party_reference": None,       # Pick from live UI (optional)
        "photo_path": None,            # File path for upload (optional)
        "is_member_of_fpc": False,      # Toggle switch, default OFF
    }


def generate_valid_address_data():
    """Generate valid data for an address table row.

    Country is ALWAYS forced to "India" in the code (other countries
    lack cascading data). State/District/Taluka will pick first valid
    option from the UI since they depend on the previous selection.
    """
    return {
        "country": "India",    # ALWAYS India — forced in code, other countries lack cascading data
        "state": None,         # Pick first valid from live UI (REQUIRED, depends on Country)
        "district": None,      # Pick first valid from live UI (REQUIRED, depends on State)
        "taluka": None,        # Pick first valid from live UI (REQUIRED, depends on District)
        "village": None,       # Pick first valid from live UI (optional, depends on Taluka)
        "pin_code": generate_pin_code(),
        "address": generate_address(),
        "address2": "",
    }


def generate_valid_bank_data():
    """Generate valid data for Bank Details tab."""
    return {
        "bank_name": f"Test Bank {random.randint(100, 999)}",
        "branch": f"Branch {random.choice(['Pune', 'Mumbai', 'Nashik', 'Dhule'])}",
        "ifsc_code": generate_ifsc_code(),
        "account_type": None,           # Pick from live UI: Current/Saving
        "account_holder_name": generate_farmer_name("Holder"),
        "account_number": generate_account_number(),
        "bank_proof": None,             # Pick from live UI: Cancelled Cheque/Passbook
    }


def generate_valid_family_data():
    """Generate valid data for Family Details tab (Borrower Farmer only)."""
    return {
        "member_name": generate_farmer_name("Member"),
        "phone_number": generate_phone_number(),
        "date_of_birth": "15/06/1985",
        "age": None,                     # Auto-calculated (readonly)
        "gender": None,                  # Pick from live UI
        "education_of_farmer_family": None,  # Pick from live UI
        "relationship": None,            # Pick from live UI
        "pincode": generate_pin_code(),
        "address": generate_address(),
        "marital_status": None,          # Pick from live UI
        "no_of_childrens": str(random.randint(0, 5)),
        "member_annual_income": None,    # Pick from live UI
        "off_farm_income": str(random.randint(10000, 500000)),
    }


def generate_valid_land_data():
    """Generate valid data for Land Details tab (Borrower Farmer + FPC Member)."""
    return {
        "farm_name": f"Farm_{random.randint(100, 999)}",
        "no_of_owner": str(random.randint(1, 10)),
        "total_land_on_document_hectare": str(round(random.uniform(1.0, 50.0), 2)),
        "individual_land_holding_hectare": str(round(random.uniform(0.5, 25.0), 2)),
        "gat_number": f"GN{random.randint(100, 999)}",
        "land_coordinate": f"{random.uniform(18.0, 22.0):.6f},{random.uniform(73.0, 78.0):.6f}",
        "total_land_in_hectare": str(round(random.uniform(1.0, 50.0), 2)),
        "total_cultivation_land_in_hectare": str(round(random.uniform(0.5, 40.0), 2)),
        "total_cultivation_land_in_acreage": str(round(random.uniform(1.0, 100.0), 2)),
        "land_ownership": None,          # Pick from live UI: Leased/Owned
        "latitude": str(round(random.uniform(18.0, 22.0), 6)),
        "longitude": str(round(random.uniform(73.0, 78.0), 6)),
    }


def generate_valid_income_data():
    """Generate valid data for Income Details tab (Borrower Farmer only)."""
    return {
        "source_of_income": None,        # Pick from live UI
        "income_bracket": None,          # Pick from live UI
        "exact_amount": str(random.randint(50000, 1000000)),
    }


def generate_valid_loan_data():
    """Generate valid data for Loan Details tab (Borrower Farmer only)."""
    return {
        "loan_name": f"Loan_{random.randint(100, 999)}",
        "facility_type": None,           # Pick from live UI: Non Funded/CC/Term Loan
        "purpose_of_loan": "Agricultural equipment purchase",
        "availed_from": f"Bank_{random.randint(100, 999)}",
        "sanctioned_amount": str(random.randint(50000, 5000000)),
        "present_outstanding_amount": str(random.randint(0, 500000)),
    }


def generate_valid_crop_data():
    """Generate valid data for Crop Details tab (Borrower Farmer + FPC Member)."""
    return {
        "farm_name": f"CropFarm_{random.randint(100, 999)}",
        "crop": None,                    # Pick from live UI (often empty)
        "season": None,                  # Pick from live UI: Kharif etc.
        "cultivation_land_in_hectare": str(round(random.uniform(0.5, 20.0), 2)),
        "expected_yield_projection": str(round(random.uniform(5.0, 200.0), 2)),
        "actual_produce": str(round(random.uniform(3.0, 150.0), 2)),
        "cultivation_land_in_acreage": str(round(random.uniform(1.0, 50.0), 2)),
    }


def generate_valid_kyc_data():
    """Generate valid data for KYC Details tab (Borrower Farmer + FPC Member)."""
    return {
        "kyc_document": None,            # Pick from live UI: AGREEMENT/AADHAR/PAN
        "kyc_number": f"KYC{random.randint(100000, 999999)}",
    }


def generate_valid_vehicle_data():
    """Generate valid data for Vehicle Details tab (Borrower Farmer only)."""
    return {
        "vehicle_type": None,            # Pick from live UI: Agriculture Equipment/Two Wheeler/Four Wheeler
        "vehicle_name": None,            # Pick from live UI (often empty, depends on vehicle type)
    }


def generate_valid_irrigation_data():
    """Generate valid data for Irrigation Details tab (Borrower Farmer only)."""
    return {
        "source_of_irrigation": None,    # Pick from live UI: Well/Canal/Borewell etc.
        "method_of_irrigation": None,    # Pick from live UI: Drip/Sprinkler etc.
    }


def generate_valid_award_data():
    """Generate valid data for Award Details tab (Borrower Farmer only)."""
    return {
        "name": f"Krishi Puraskar {random.randint(1, 100)}",
        "year": str(random.randint(2015, 2025)),
    }


def generate_full_valid_farmer_data(category="Walk-in Farmer"):
    """Generate complete valid data for ALL tabs based on farmer category.
    Used for end-to-end happy path tests.
    """
    data = generate_valid_farmer_step0(category)
    data["current_address"] = generate_valid_address_data()
    data["permanent_address"] = generate_valid_address_data()
    data["bank_details"] = generate_valid_bank_data()

    if category in ("Borrower Farmer", "FPC Member"):
        data["land_details"] = generate_valid_land_data()
        data["crop_details"] = generate_valid_crop_data()
        data["kyc_details"] = generate_valid_kyc_data()

    if category == "Borrower Farmer":
        data["family_details"] = generate_valid_family_data()
        data["other_details"] = {
            "education_qualification": None,
            "electricity_availability": None,
        }
        data["vehicle_details"] = generate_valid_vehicle_data()
        data["income_details"] = generate_valid_income_data()
        data["irrigation_details"] = generate_valid_irrigation_data()
        data["award_details"] = generate_valid_award_data()
        data["loan_details"] = generate_valid_loan_data()

    return data


# ──────────────────────────────────────────────
# Validation Test Data Helpers
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


def generate_special_char_name():
    """Generate a name with special characters (BUG-F03 test)."""
    return "Rahul@@#$%"


def generate_sql_injection():
    """Generate a SQL injection string."""
    return "'; DROP TABLE farmers; --"


def generate_xss_payload():
    """Generate an XSS payload string."""
    return "<script>alert('xss')</script>"


def generate_uppercase_email():
    """Generate an email with uppercase letters (BUG-F04 test)."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TestFarmer{timestamp}@Gmail.com"


def generate_invalid_email():
    """Generate an invalid email format."""
    return "notanemail"


def generate_zero_amount():
    """Return zero for amount field (BUG-F06 test)."""
    return "0"


def generate_dot_prefix_amount():
    """Return amount starting with dot (BUG-F06 test)."""
    return ".50"


def generate_negative_amount():
    """Return a negative amount value."""
    return f"-{random.randint(100, 9999)}"


def generate_empty_farmer_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "party_reference": "",
        "farmer_name": "",
        "email": "",
        "phone_number": "",
        "date_of_birth": "",
        "password": "",
        "farmer_category": "",
        "land_classification": "",
    }


def generate_farmer_name_only():
    """Return dict with only Farmer Name filled."""
    return {
        "farmer_name": generate_farmer_name(),
        "email": "",
        "phone_number": "",
        "password": "",
        "farmer_category": "",
    }


def generate_future_date():
    """Generate a future date string (DD/MM/YYYY)."""
    return "01/01/2099"


def generate_invalid_date():
    """Generate an invalid date string."""
    return "31/02/2020"


def generate_duplicate_farmer_data(existing_name, existing_phone):
    """Return data using an existing farmer name and phone for duplicate test."""
    return {
        "farmer_name": existing_name,
        "phone_number": existing_phone,
        "email": generate_email(),
        "password": generate_password(),
        "farmer_category": "Walk-in Farmer",
    }
