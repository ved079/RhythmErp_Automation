"""
farmer_data.py
--------------
Test data generators for RhythmERP Farmer screen.

Location: Registration > Farmer
URL:      /#/dynamic-screens/Farmer/Farmer

SOURCED FROM: Browser exploration 2026-05-21 + Farmer_Field_Mapping_Complete.xlsx
Every field name, type, and validation below comes from live ERP inspection.

FORM LAYOUT (MULTI-STEP STEPPER - varies by Farmer Category):

  Step 0 - Farmer Details (ALWAYS VISIBLE):
    - Party Reference         (mat-select,   optional)
    - Farmer Name             (text input,   REQUIRED, maxlength=255, name='Farmer Name')
    - Email                   (text input,   optional, maxlength=255, name='Email')
    - Phone Number            (text input,   REQUIRED, maxlength=255, name='Phone Number')
    - Date Of Birth           (datepicker,   optional, format DD/MM/YYYY, placeholder='DD/MM/YYYY')
    - Age                     (number input, READONLY, name='Age' - auto-calculated from DOB)
    - Gender                  (mat-select,   optional, options: Female, Male)
    - Category                (mat-select,   optional, social category)
    - Religion                (mat-select,   optional)
    - Password                (text input,   REQUIRED, maxlength=255, name='Password')
    - Photo Upload            (file upload,  optional)
    - Farmer Category         (mat-select MULTI, REQUIRED for tabs - determines stepper)
    - Land Classification     (mat-select,   optional)
    - Is Member of This FPC   (toggle switch, default OFF)

  Farmer Category determines stepper tabs (tab index in parentheses):
    Walk-in Farmer  -> 3 tabs:  Current Address(0), Permanent Address(1), Bank Details(2)
    FPC Member      -> 6 tabs:  Current Address(0), Permanent Address(1), Land Details(2),
                                Crop Details(3), KYC Details(4), Bank Details(5)
    Borrower Farmer -> 13 tabs: Current Address(0), Permanent Address(1), Family Details(2),
                                Other Details(3), Land Details(4), Crop Details(5),
                                KYC Details(6), Vehicle Details(7), Income Details(8),
                                Bank Details(9), Irrigation Details(10), Award Details(11),
                                Loan Details(12)

KNOWN BUGS:
  BUG-F01 (High):   No Of Owner required but no asterisk shown - ALWAYS fill it!
  BUG-F02 (High):   Deselect+Reselect farmer category freezes Next/Back
  BUG-F03 (Medium): Farmer Name accepts special characters
  BUG-F04 (Medium): Email rejects uppercase - ALWAYS use lowercase!
  BUG-F05 (Medium): Farmer Category placeholder is selectable
  BUG-F06 (Medium): Amount fields accept 0 and . prefix
  BUG-F07 (Low):    Source of Income shows Dairy twice
  BUG-F08 (Low):    Edit mode missing Land/Crop/KYC tabs
  BUG-F09 (Low):    Character count indicator disappears on validation error

CRITICAL SCOPING RULES (from Critical Notes sheet):
  - name='Address' appears in Current Address, Permanent Address, AND Family Details
  - name='Phone Number' appears in Step 0 AND Family Details
  - name='Farm Name' appears in Land Details AND Crop Details
  - name='Pin Code' appears in Current Address AND Permanent Address
  - name='Age' appears in Step 0 AND Family Details
  - Gender dropdown appears in Step 0 AND Family Details
  -> MUST scope all interactions to the ACTIVE panel using JS

TAB CHARACTER WARNING:
  Land/Crop/Income number fields have trailing \\t in their name attribute.
  CSS selector input[name='No Of Owner'] will NOT match input[name='No Of Owner\\t'].
  Use XPath contains() or JS-based element finding that ignores trailing tabs.
"""

import random
import string
from datetime import datetime


# ==============================================================
#  HTML NAME ATTRIBUTE MAP
#  Maps our snake_case data keys to the actual HTML name attribute.
#  Fields marked with (TAB) have trailing tab characters in the name attr.
#  Fields with '-' have no name attr (use XPath/placeholder instead).
# ==============================================================

HTML_NAME_MAP = {
    # Step 0: Farmer Details
    "farmer_name":              "Farmer Name",
    "email":                    "Email",
    "phone_number":             "Phone Number",
    "date_of_birth":            "-",           # use placeholder='DD/MM/YYYY'
    "age":                      "Age",          # READONLY
    "password":                 "Password",

    # Address tabs (Current & Permanent) - MUST scope to active panel!
    "pin_code":                 "Pin Code",
    "address":                  "Address",
    "address2":                 "Address2",

    # Family Details - MUST scope to active panel!
    "member_name":              "Member Name",
    "family_phone_number":      "Phone Number", # SAME name as Step 0! Scope to panel!
    "family_dob":               "-",            # use placeholder='DD/MM/YYYY' scoped to panel
    "family_age":               "Age",          # SAME name as Step 0! Scope to panel!
    "family_pincode":           "Pincode",       # NOTE: 'Pincode' not 'Pin Code'
    "family_address":           "Address",       # SAME name as address tabs! Scope to panel!
    "no_of_childrens":          "No of Childrens",  # NOTE: has trailing TAB char
    "off_farm_income":          "Off Farm Income",

    # Other Details
    # Both are dropdowns, no name attr

    # Land Details - MUST scope to active panel! Some name attrs have trailing TAB
    "farm_name":                "Farm Name",        # SAME name in Crop Details! Scope!
    "no_of_owner":              "No Of Owner",       # (TAB) BUG-F01: required but no asterisk
    "total_land_on_document":   "Total Land On Document (hectare)",  # (TAB)
    "individual_land_holding":  "Individual Land Holding (hectare)", # (TAB)
    "gat_number":               "Gat Number",         # (TAB)
    "land_coordinate":          "Land Coordinate",    # (TAB)
    "total_land_in_hectare":    "Total Land In hectare",           # (TAB)
    "total_cultivation_land_hectare": "Total Cultivation Land In hectare",  # (TAB)
    "total_cultivation_land_acreage": "Total Cultivation Land in acreage",  # (TAB)
    "latitude":                 "Latitude(Lat)",
    "longitude":                "Longitude(Log)",

    # Crop Details - MUST scope! Some name attrs have trailing TAB
    "crop_farm_name":           "Farm Name",          # SAME as Land Details! Scope!
    "cultivation_land_hectare": "Cultivation Land In hectare",         # (TAB)
    "expected_yield_projection":"Expected Yield projection(in Quintal)", # (TAB)
    "actual_produce":           "Actual Produce(in Quintal)",           # (TAB)
    "cultivation_land_acreage": "Cultivation Land In acreage",          # (TAB)

    # KYC Details
    "kyc_number":               "KYC Number",

    # Bank Details
    "bank_name":                "Bank Name",
    "branch":                   "Branch",
    "ifsc_code":                "IFSC Code",
    "account_holder_name":      "Account Holder Name",
    "account_number":            "Account Number",

    # Income Details
    "exact_amount":             "Exact Amount",

    # Award Details
    "award_name":               "Name",
    "award_year":               "Year",

    # Loan Details
    "loan_name":                "Loan Name",
    "purpose_of_loan":          "Purpose Of Loan",
    "availed_from_date":        "-",            # DATEPICKER, not text! Format DD/MM/YYYY
    "sanctioned_amount":        "Sanctioned Amount",
    "present_outstanding_amount":"Present Outstanding Amount",
}

# Fields whose HTML name attribute has a trailing TAB character
# CSS selectors won't match these - must use XPath contains() or JS finding
TAB_NAME_FIELDS = [
    "No Of Owner",
    "Total Land On Document (hectare)",
    "Individual Land Holding (hectare)",
    "Gat Number",
    "Land Coordinate",
    "Total Land In hectare",
    "Total Cultivation Land In hectare",
    "Total Cultivation Land in acreage",
    "No of Childrens",
    "Cultivation Land In hectare",
    "Expected Yield projection(in Quintal)",
    "Actual Produce(in Quintal)",
    "Cultivation Land In acreage",
]


# ==============================================================
#  DROPDOWN OPTIONS (from live ERP exploration)
#  None means we pick from live UI at runtime (options may vary).
# ==============================================================

DROPDOWN_OPTIONS = {
    # Step 0
    "party_reference":          None,           # Dynamic, pick from UI
    "gender":                   ["Female", "Male"],
    "category":                 None,           # Social category, pick from UI
    "religion":                 None,           # Pick from UI
    "farmer_category":          ["Borrower Farmer", "FPC Member", "Walk-in Farmer"],
    "land_classification":      None,           # Pick from UI

    # Address cascading (MUST select in order: Country -> State -> District -> Taluka -> Village)
    "country":                  ["India"],       # ALWAYS India - other countries lack data
    "state":                    None,            # Depends on Country, pick from UI
    "district":                 None,            # Depends on State, pick from UI
    "taluka":                   None,            # Depends on District, pick from UI
    "village":                  None,            # Depends on Taluka, pick from UI

    # Family Details
    "family_gender":            ["Female", "Male"],
    "education_of_farmer_family": None,          # Pick from UI
    "relationship":             None,            # Pick from UI (Father, Mother, Spouse, Son, Daughter etc.)
    "marital_status":           None,            # Pick from UI (Married, Unmarried, Divorced, Widowed)
    "member_annual_income":     None,            # Pick from UI (income ranges)

    # Other Details
    "education_qualification":  None,            # Pick from UI (SSC, HSC, Graduate, Post Graduate)
    "electricity_availability": None,            # Pick from UI (Yes, No)

    # Land Details
    "land_ownership":           None,            # Pick from UI (Leased, Owned)

    # Crop Details
    "crop":                     None,            # Pick from UI
    "season":                   None,            # Pick from UI (Kharif, Rabi, Zaid)

    # KYC Details
    "kyc_document":             None,            # Pick from UI (AADHAR, PAN, AGREEMENT etc.)

    # Bank Details
    "account_type":             ["Current", "Saving"],
    "bank_proof":               ["Cancelled Cheque", "Passbook"],

    # Vehicle Details
    "vehicle_type":             None,            # Pick from UI (Agriculture Equipment, Two Wheeler, Four Wheeler)
    "vehicle_name":             None,            # Pick from UI, depends on Vehicle Type

    # Income Details
    "source_of_income":         None,            # Pick from UI. BUG-F07: Dairy shown twice
    "income_bracket":           None,            # Pick from UI

    # Irrigation Details
    "source_of_irrigation":     None,            # Pick from UI (Well, Canal, Borewell, River)
    "method_of_irrigation":     None,            # Pick from UI (Drip, Sprinkler, Flood)

    # Loan Details
    "facility_type":            ["Non Funded", "CC", "Term Loan"],
}


# ==============================================================
#  TAB INDEX MAP
#  Maps (farmer_category, tab_name) -> 0-based stepper index
# ==============================================================

TAB_INDEX_MAP = {
    # Walk-in Farmer: 3 tabs
    ("Walk-in Farmer", "Current Address Details"):   0,
    ("Walk-in Farmer", "Permanent Address Details"): 1,
    ("Walk-in Farmer", "Bank Details"):              2,

    # FPC Member: 6 tabs
    ("FPC Member", "Current Address Details"):       0,
    ("FPC Member", "Permanent Address Details"):     1,
    ("FPC Member", "Land Details"):                  2,
    ("FPC Member", "Crop Details"):                  3,
    ("FPC Member", "KYC Details"):                   4,
    ("FPC Member", "Bank Details"):                  5,

    # Borrower Farmer: 13 tabs
    ("Borrower Farmer", "Current Address Details"):  0,
    ("Borrower Farmer", "Permanent Address Details"):1,
    ("Borrower Farmer", "Family Details"):           2,
    ("Borrower Farmer", "Other Details"):            3,
    ("Borrower Farmer", "Land Details"):             4,
    ("Borrower Farmer", "Crop Details"):             5,
    ("Borrower Farmer", "KYC Details"):              6,
    ("Borrower Farmer", "Vehicle Details"):          7,
    ("Borrower Farmer", "Income Details"):           8,
    ("Borrower Farmer", "Bank Details"):             9,
    ("Borrower Farmer", "Irrigation Details"):       10,
    ("Borrower Farmer", "Award Details"):            11,
    ("Borrower Farmer", "Loan Details"):             12,
}

# Ordered tab names per category (for iteration)
TABS_BY_CATEGORY = {
    "Walk-in Farmer": [
        "Current Address Details",
        "Permanent Address Details",
        "Bank Details",
    ],
    "FPC Member": [
        "Current Address Details",
        "Permanent Address Details",
        "Land Details",
        "Crop Details",
        "KYC Details",
        "Bank Details",
    ],
    "Borrower Farmer": [
        "Current Address Details",
        "Permanent Address Details",
        "Family Details",
        "Other Details",
        "Land Details",
        "Crop Details",
        "KYC Details",
        "Vehicle Details",
        "Income Details",
        "Bank Details",
        "Irrigation Details",
        "Award Details",
        "Loan Details",
    ],
}


# ==============================================================
#  FIELD METADATA
#  Complete metadata for every field from the Excel exploration.
#  Used by the page object to know how to interact with each field.
# ==============================================================

FIELD_METADATA = {
    # ── Step 0: Farmer Details ──
    "party_reference":          {"tab": "Farmer Details", "type": "dropdown",       "required": False, "readonly": False, "html_name": None},
    "farmer_name":              {"tab": "Farmer Details", "type": "text",            "required": True,  "readonly": False, "html_name": "Farmer Name", "max_length": 255},
    "email":                    {"tab": "Farmer Details", "type": "text",            "required": False, "readonly": False, "html_name": "Email", "max_length": 255},
    "phone_number":             {"tab": "Farmer Details", "type": "text",            "required": True,  "readonly": False, "html_name": "Phone Number", "max_length": 255},
    "date_of_birth":            {"tab": "Farmer Details", "type": "datepicker",      "required": False, "readonly": False, "html_name": None, "placeholder": "DD/MM/YYYY"},
    "age":                      {"tab": "Farmer Details", "type": "number",          "required": False, "readonly": True,  "html_name": "Age"},
    "gender":                   {"tab": "Farmer Details", "type": "dropdown",        "required": False, "readonly": False, "html_name": None},
    "category":                 {"tab": "Farmer Details", "type": "dropdown",        "required": False, "readonly": False, "html_name": None},
    "religion":                 {"tab": "Farmer Details", "type": "dropdown",        "required": False, "readonly": False, "html_name": None},
    "password":                 {"tab": "Farmer Details", "type": "text",            "required": True,  "readonly": False, "html_name": "Password", "max_length": 255},
    "photo_path":               {"tab": "Farmer Details", "type": "file_upload",     "required": False, "readonly": False, "html_name": None},
    "farmer_category":          {"tab": "Farmer Details", "type": "multi_dropdown",  "required": False, "readonly": False, "html_name": None},
    "land_classification":      {"tab": "Farmer Details", "type": "dropdown",        "required": False, "readonly": False, "html_name": None},
    "is_member_of_fpc":         {"tab": "Farmer Details", "type": "toggle",          "required": False, "readonly": False, "html_name": None},

    # ── Current Address Details ──
    "country":                  {"tab": "Current Address Details", "type": "cascading_dropdown", "required": True,  "readonly": False, "html_name": None, "cascading_order": 0},
    "state":                    {"tab": "Current Address Details", "type": "cascading_dropdown", "required": True,  "readonly": False, "html_name": None, "cascading_order": 1},
    "district":                 {"tab": "Current Address Details", "type": "cascading_dropdown", "required": True,  "readonly": False, "html_name": None, "cascading_order": 2},
    "taluka":                   {"tab": "Current Address Details", "type": "cascading_dropdown", "required": True,  "readonly": False, "html_name": None, "cascading_order": 3},
    "village":                  {"tab": "Current Address Details", "type": "cascading_dropdown", "required": False, "readonly": False, "html_name": None, "cascading_order": 4},
    "pin_code":                 {"tab": "Current Address Details", "type": "text",     "required": True,  "readonly": False, "html_name": "Pin Code", "max_length": 255, "scope": "panel"},
    "address":                  {"tab": "Current Address Details", "type": "text",     "required": True,  "readonly": False, "html_name": "Address", "max_length": 255, "scope": "panel"},
    "address2":                 {"tab": "Current Address Details", "type": "text",     "required": False, "readonly": False, "html_name": "Address2", "max_length": 255, "scope": "panel"},

    # ── Permanent Address Details ──
    "perm_country":             {"tab": "Permanent Address Details", "type": "cascading_dropdown", "required": True,  "readonly": False, "html_name": None, "cascading_order": 0},
    "perm_state":               {"tab": "Permanent Address Details", "type": "cascading_dropdown", "required": True,  "readonly": False, "html_name": None, "cascading_order": 1},
    "perm_district":            {"tab": "Permanent Address Details", "type": "cascading_dropdown", "required": True,  "readonly": False, "html_name": None, "cascading_order": 2},
    "perm_taluka":              {"tab": "Permanent Address Details", "type": "cascading_dropdown", "required": True,  "readonly": False, "html_name": None, "cascading_order": 3},
    "perm_village":             {"tab": "Permanent Address Details", "type": "cascading_dropdown", "required": False, "readonly": False, "html_name": None, "cascading_order": 4},
    "perm_pin_code":            {"tab": "Permanent Address Details", "type": "text",     "required": True,  "readonly": False, "html_name": "Pin Code", "max_length": 255, "scope": "panel"},
    "perm_address":             {"tab": "Permanent Address Details", "type": "text",     "required": True,  "readonly": False, "html_name": "Address", "max_length": 255, "scope": "panel"},
    "perm_address2":            {"tab": "Permanent Address Details", "type": "text",     "required": False, "readonly": False, "html_name": "Address2", "max_length": 255, "scope": "panel"},

    # ── Family Details (Borrower Farmer) ──
    "member_name":              {"tab": "Family Details", "type": "text",              "required": False, "readonly": False, "html_name": "Member Name", "max_length": 255, "scope": "panel"},
    "family_phone_number":      {"tab": "Family Details", "type": "text",              "required": False, "readonly": False, "html_name": "Phone Number", "max_length": 255, "scope": "panel"},
    "family_dob":               {"tab": "Family Details", "type": "datepicker",        "required": False, "readonly": False, "html_name": None, "placeholder": "DD/MM/YYYY", "scope": "panel"},
    "family_age":               {"tab": "Family Details", "type": "number",            "required": False, "readonly": True,  "html_name": "Age", "scope": "panel"},
    "family_gender":            {"tab": "Family Details", "type": "dropdown",          "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "education_of_farmer_family": {"tab": "Family Details", "type": "dropdown",        "required": False, "readonly": False, "html_name": None},
    "relationship":             {"tab": "Family Details", "type": "dropdown",          "required": False, "readonly": False, "html_name": None},
    "is_member_staying_with_farmer": {"tab": "Family Details", "type": "toggle",       "required": False, "readonly": False, "html_name": None},
    "family_pincode":           {"tab": "Family Details", "type": "text",              "required": False, "readonly": False, "html_name": "Pincode", "max_length": 255, "scope": "panel"},
    "family_address":           {"tab": "Family Details", "type": "text",              "required": False, "readonly": False, "html_name": "Address", "max_length": 255, "scope": "panel"},
    "marital_status":           {"tab": "Family Details", "type": "dropdown",          "required": False, "readonly": False, "html_name": None},
    "no_of_childrens":          {"tab": "Family Details", "type": "number",            "required": False, "readonly": False, "html_name": "No of Childrens", "has_tab_char": True, "scope": "panel"},
    "member_annual_income":     {"tab": "Family Details", "type": "dropdown",          "required": False, "readonly": False, "html_name": None},
    "off_farm_income":          {"tab": "Family Details", "type": "text",              "required": False, "readonly": False, "html_name": "Off Farm Income", "max_length": 255, "scope": "panel"},

    # ── Other Details (Borrower Farmer) ──
    "education_qualification":  {"tab": "Other Details", "type": "dropdown",           "required": False, "readonly": False, "html_name": None},
    "electricity_availability": {"tab": "Other Details", "type": "dropdown",           "required": False, "readonly": False, "html_name": None},

    # ── Land Details (Borrower Farmer + FPC Member) ──
    "farm_name":                {"tab": "Land Details", "type": "text",                "required": False, "readonly": False, "html_name": "Farm Name", "max_length": 255, "scope": "panel"},
    "land_attachment":          {"tab": "Land Details", "type": "file_upload",         "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "no_of_owner":              {"tab": "Land Details", "type": "number",              "required": True,  "readonly": False, "html_name": "No Of Owner", "has_tab_char": True, "scope": "panel", "bug": "BUG-F01: required but no asterisk"},
    "total_land_on_document":   {"tab": "Land Details", "type": "number",              "required": False, "readonly": False, "html_name": "Total Land On Document (hectare)", "has_tab_char": True, "scope": "panel"},
    "individual_land_holding":  {"tab": "Land Details", "type": "number",              "required": False, "readonly": False, "html_name": "Individual Land Holding (hectare)", "has_tab_char": True, "scope": "panel"},
    "gat_number":               {"tab": "Land Details", "type": "text",                "required": False, "readonly": False, "html_name": "Gat Number", "has_tab_char": True, "max_length": 255, "scope": "panel"},
    "land_coordinate":          {"tab": "Land Details", "type": "text",                "required": False, "readonly": False, "html_name": "Land Coordinate", "has_tab_char": True, "max_length": 255, "scope": "panel"},
    "total_land_in_hectare":    {"tab": "Land Details", "type": "number",              "required": False, "readonly": False, "html_name": "Total Land In hectare", "has_tab_char": True, "scope": "panel"},
    "total_cultivation_land_hectare": {"tab": "Land Details", "type": "number",        "required": False, "readonly": False, "html_name": "Total Cultivation Land In hectare", "has_tab_char": True, "scope": "panel"},
    "total_cultivation_land_acreage": {"tab": "Land Details", "type": "number",        "required": False, "readonly": False, "html_name": "Total Cultivation Land in acreage", "has_tab_char": True, "scope": "panel"},
    "land_ownership":           {"tab": "Land Details", "type": "dropdown",            "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "latitude":                 {"tab": "Land Details", "type": "text",                "required": False, "readonly": False, "html_name": "Latitude(Lat)", "max_length": 255, "scope": "panel"},
    "longitude":                {"tab": "Land Details", "type": "text",                "required": False, "readonly": False, "html_name": "Longitude(Log)", "max_length": 255, "scope": "panel"},

    # ── Crop Details (Borrower Farmer + FPC Member) ──
    "crop_farm_name":           {"tab": "Crop Details", "type": "text",                "required": False, "readonly": False, "html_name": "Farm Name", "max_length": 255, "scope": "panel"},
    "crop":                     {"tab": "Crop Details", "type": "dropdown",            "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "season":                   {"tab": "Crop Details", "type": "dropdown",            "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "cultivation_land_hectare": {"tab": "Crop Details", "type": "number",              "required": False, "readonly": False, "html_name": "Cultivation Land In hectare", "has_tab_char": True, "scope": "panel"},
    "expected_yield_projection":{"tab": "Crop Details", "type": "number",              "required": False, "readonly": False, "html_name": "Expected Yield projection(in Quintal)", "has_tab_char": True, "scope": "panel"},
    "actual_produce":           {"tab": "Crop Details", "type": "number",              "required": False, "readonly": False, "html_name": "Actual Produce(in Quintal)", "has_tab_char": True, "scope": "panel"},
    "cultivation_land_acreage": {"tab": "Crop Details", "type": "number",              "required": False, "readonly": False, "html_name": "Cultivation Land In acreage", "has_tab_char": True, "scope": "panel"},
    "document_attachment":      {"tab": "Crop Details", "type": "file_upload",         "required": False, "readonly": False, "html_name": None, "scope": "panel"},

    # ── KYC Details (Borrower Farmer + FPC Member) ──
    "kyc_document":             {"tab": "KYC Details", "type": "dropdown",             "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "kyc_number":               {"tab": "KYC Details", "type": "text",                "required": False, "readonly": False, "html_name": "KYC Number", "max_length": 255, "scope": "panel"},
    "kyc_attachment":           {"tab": "KYC Details", "type": "file_upload",          "required": False, "readonly": False, "html_name": None, "scope": "panel"},

    # ── Vehicle Details (Borrower Farmer) ──
    "vehicle_type":             {"tab": "Vehicle Details", "type": "dropdown",         "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "vehicle_name":             {"tab": "Vehicle Details", "type": "dropdown",         "required": False, "readonly": False, "html_name": None, "scope": "panel"},

    # ── Income Details (Borrower Farmer) ──
    "source_of_income":         {"tab": "Income Details", "type": "dropdown",          "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "income_bracket":           {"tab": "Income Details", "type": "dropdown",          "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "exact_amount":             {"tab": "Income Details", "type": "number",            "required": False, "readonly": False, "html_name": "Exact Amount", "scope": "panel"},

    # ── Bank Details (all 3 categories) ──
    "bank_name":                {"tab": "Bank Details", "type": "text",                "required": False, "readonly": False, "html_name": "Bank Name", "max_length": 255, "scope": "panel"},
    "branch":                   {"tab": "Bank Details", "type": "text",                "required": False, "readonly": False, "html_name": "Branch", "max_length": 255, "scope": "panel"},
    "ifsc_code":                {"tab": "Bank Details", "type": "text",                "required": False, "readonly": False, "html_name": "IFSC Code", "max_length": 255, "scope": "panel"},
    "account_type":             {"tab": "Bank Details", "type": "dropdown",            "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "account_holder_name":      {"tab": "Bank Details", "type": "text",                "required": False, "readonly": False, "html_name": "Account Holder Name", "max_length": 255, "scope": "panel"},
    "account_number":           {"tab": "Bank Details", "type": "text",                "required": False, "readonly": False, "html_name": "Account Number", "max_length": 255, "scope": "panel"},
    "bank_proof":               {"tab": "Bank Details", "type": "dropdown",            "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "bank_attachment":          {"tab": "Bank Details", "type": "file_upload",          "required": False, "readonly": False, "html_name": None, "scope": "panel"},

    # ── Irrigation Details (Borrower Farmer) ──
    "source_of_irrigation":     {"tab": "Irrigation Details", "type": "dropdown",      "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "method_of_irrigation":     {"tab": "Irrigation Details", "type": "dropdown",      "required": False, "readonly": False, "html_name": None, "scope": "panel"},

    # ── Award Details (Borrower Farmer) ──
    "award_name":               {"tab": "Award Details", "type": "text",               "required": False, "readonly": False, "html_name": "Name", "max_length": 255, "scope": "panel"},
    "award_year":               {"tab": "Award Details", "type": "text",               "required": False, "readonly": False, "html_name": "Year", "max_length": 255, "scope": "panel"},

    # ── Loan Details (Borrower Farmer) ──
    "loan_name":                {"tab": "Loan Details", "type": "text",                "required": False, "readonly": False, "html_name": "Loan Name", "max_length": 255, "scope": "panel"},
    "facility_type":            {"tab": "Loan Details", "type": "dropdown",            "required": False, "readonly": False, "html_name": None, "scope": "panel"},
    "purpose_of_loan":          {"tab": "Loan Details", "type": "text",                "required": False, "readonly": False, "html_name": "Purpose Of Loan", "max_length": 255, "scope": "panel"},
    "availed_from_date":        {"tab": "Loan Details", "type": "datepicker",          "required": False, "readonly": False, "html_name": None, "placeholder": "DD/MM/YYYY", "scope": "panel"},
    "sanctioned_amount":        {"tab": "Loan Details", "type": "number",              "required": False, "readonly": False, "html_name": "Sanctioned Amount", "scope": "panel"},
    "present_outstanding_amount":{"tab": "Loan Details", "type": "number",             "required": False, "readonly": False, "html_name": "Present Outstanding Amount", "scope": "panel"},
}


# ==============================================================
#  Core Data Generators
# ==============================================================

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
    """Generate a random LOWERCASE email address.
    BUG-F04: Email rejects uppercase - always use lowercase!
    """
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
    """Generate a random bank account number (12 digits)."""
    return f"{random.randint(100000000000, 999999999999)}"


# ==============================================================
#  Complete Valid Data for Create - Per Tab
# ==============================================================

def generate_valid_farmer_step0(category="Walk-in Farmer"):
    """Generate a complete dict of valid farmer data for Step 0.
    Dropdown values set to None -> pick first valid option from live UI at runtime.
    """
    return {
        "party_reference":          None,       # Pick from live UI (optional)
        "farmer_name":              generate_farmer_name(),
        "email":                    generate_email(),          # ALWAYS lowercase (BUG-F04)
        "phone_number":             generate_phone_number(),
        "date_of_birth":            "01/01/1990",              # DD/MM/YYYY
        "age":                      None,                      # Auto-calculated (readonly)
        "gender":                   None,                      # Pick from live UI
        "category":                 None,                      # Pick from live UI (social category)
        "religion":                 None,                      # Pick from live UI
        "password":                 generate_password(),
        "photo_path":               None,                      # File path for upload (optional)
        "farmer_category":          category,                  # "Borrower Farmer", "FPC Member", "Walk-in Farmer"
        "land_classification":      None,                      # Pick from live UI
        "is_member_of_fpc":         False,                     # Toggle switch, default OFF
    }


def generate_valid_address_data():
    """Generate valid data for an address table row.
    Country is ALWAYS "India" (business rule - other countries lack cascading data).
    State/District/Taluka set to None -> pick first valid option from live UI.
    """
    return {
        "country":                  "India",    # ALWAYS India (business rule)
        "state":                    None,       # Pick first valid from live UI (REQUIRED, depends on Country)
        "district":                 None,       # Pick first valid from live UI (REQUIRED, depends on State)
        "taluka":                   None,       # Pick first valid from live UI (REQUIRED, depends on District)
        "village":                  None,       # Pick first valid from live UI (optional, depends on Taluka)
        "pin_code":                 generate_pin_code(),
        "address":                  generate_address(),
        "address2":                 "",
    }


def generate_valid_permanent_address_data():
    """Generate valid data for Permanent Address tab.
    Same structure as Current Address but uses perm_ prefixed keys for clarity.
    """
    addr = generate_valid_address_data()
    return {
        "perm_country":             addr["country"],
        "perm_state":               addr["state"],
        "perm_district":            addr["district"],
        "perm_taluka":              addr["taluka"],
        "perm_village":             addr["village"],
        "perm_pin_code":            generate_pin_code(),   # Different pin code
        "perm_address":             generate_address(),    # Different address
        "perm_address2":            "",
    }


def generate_valid_family_data():
    """Generate valid data for Family Details tab (Borrower Farmer only).
    NOTE: 'Address', 'Phone Number', 'Age' fields share name attrs with other tabs.
    MUST scope to active panel when filling!
    """
    return {
        "member_name":                  generate_farmer_name("Member"),
        "family_phone_number":          generate_phone_number(),   # name='Phone Number' - SCOPE!
        "family_dob":                   "15/06/1985",              # DD/MM/YYYY, scoped
        "family_age":                   None,                      # Auto-calculated (readonly), name='Age' - SCOPE!
        "family_gender":                None,                      # Pick from live UI, 2nd Gender - SCOPE!
        "education_of_farmer_family":   None,                      # Pick from live UI
        "relationship":                 None,                      # Pick from live UI
        "is_member_staying_with_farmer": False,                    # Toggle switch
        "family_pincode":               generate_pin_code(),       # name='Pincode' (not 'Pin Code')
        "family_address":               generate_address(),        # name='Address' - SCOPE!
        "marital_status":               None,                      # Pick from live UI
        "no_of_childrens":              str(random.randint(0, 5)), # name has trailing TAB char!
        "member_annual_income":         None,                      # Pick from live UI
        "off_farm_income":              str(random.randint(10000, 500000)),
    }


def generate_valid_other_details_data():
    """Generate valid data for Other Details tab (Borrower Farmer only).
    Only 2 dropdowns: Education Qualification and Electricity Availability.
    """
    return {
        "education_qualification":      None,    # Pick from live UI (SSC, HSC, Graduate, Post Graduate)
        "electricity_availability":     None,    # Pick from live UI (Yes, No)
    }


def generate_valid_land_data():
    """Generate valid data for Land Details tab (Borrower Farmer + FPC Member).
    NOTE: 'Farm Name' shares name attr with Crop Details Farm Name - SCOPE!
    NOTE: Many number fields have trailing TAB in name attr - use XPath contains()!
    BUG-F01: No Of Owner is REQUIRED but shows no asterisk - ALWAYS fill it!
    """
    return {
        "farm_name":                     f"Farm_{random.randint(100, 999)}",
        "land_attachment":               None,                     # File upload (optional)
        "no_of_owner":                   str(random.randint(1, 10)),  # BUG-F01: required! name has TAB!
        "total_land_on_document":        str(round(random.uniform(1.0, 50.0), 2)),
        "individual_land_holding":       str(round(random.uniform(0.5, 25.0), 2)),
        "gat_number":                    f"GN{random.randint(100, 999)}",
        "land_coordinate":               f"{random.uniform(18.0, 22.0):.6f},{random.uniform(73.0, 78.0):.6f}",
        "total_land_in_hectare":         str(round(random.uniform(1.0, 50.0), 2)),
        "total_cultivation_land_hectare": str(round(random.uniform(0.5, 40.0), 2)),
        "total_cultivation_land_acreage": str(round(random.uniform(1.0, 100.0), 2)),
        "land_ownership":                None,                     # Pick from live UI (Leased, Owned)
        "latitude":                      str(round(random.uniform(18.0, 22.0), 6)),
        "longitude":                     str(round(random.uniform(73.0, 78.0), 6)),
    }


def generate_valid_crop_data():
    """Generate valid data for Crop Details tab (Borrower Farmer + FPC Member).
    NOTE: 'Farm Name' shares name attr with Land Details Farm Name - SCOPE!
    NOTE: Number fields have trailing TAB in name attr - use XPath contains()!
    """
    return {
        "crop_farm_name":                f"CropFarm_{random.randint(100, 999)}",
        "crop":                          None,                     # Pick from live UI
        "season":                        None,                     # Pick from live UI (Kharif, Rabi, Zaid)
        "cultivation_land_hectare":      str(round(random.uniform(0.5, 20.0), 2)),
        "expected_yield_projection":     str(round(random.uniform(5.0, 200.0), 2)),
        "actual_produce":                str(round(random.uniform(3.0, 150.0), 2)),
        "cultivation_land_acreage":      str(round(random.uniform(1.0, 50.0), 2)),
        "document_attachment":           None,                     # File upload (optional)
    }


def generate_valid_kyc_data():
    """Generate valid data for KYC Details tab (Borrower Farmer + FPC Member)."""
    return {
        "kyc_document":                  None,                     # Pick from live UI (AADHAR, PAN, AGREEMENT)
        "kyc_number":                    f"KYC{random.randint(100000, 999999)}",
        "kyc_attachment":                None,                     # File upload (optional)
    }


def generate_valid_vehicle_data():
    """Generate valid data for Vehicle Details tab (Borrower Farmer only).
    Vehicle Name depends on Vehicle Type selection (cascading-like).
    """
    return {
        "vehicle_type":                  None,                     # Pick from live UI
        "vehicle_name":                  None,                     # Pick from live UI (depends on Vehicle Type)
    }


def generate_valid_income_data():
    """Generate valid data for Income Details tab (Borrower Farmer only).
    BUG-F07: Source of Income shows Dairy twice.
    BUG-F06: Exact Amount accepts 0 and . prefix (but we generate valid data).
    """
    return {
        "source_of_income":              None,                     # Pick from live UI
        "income_bracket":                None,                     # Pick from live UI
        "exact_amount":                  str(random.randint(50000, 1000000)),
    }


def generate_valid_bank_data():
    """Generate valid data for Bank Details tab (all 3 categories)."""
    return {
        "bank_name":                     "Test Bank",
        "branch":                        f"Branch {random.choice(['Pune', 'Mumbai', 'Nashik', 'Dhule'])}",
        "ifsc_code":                     generate_ifsc_code(),
        "account_type":                  None,                     # Pick from live UI: Current/Saving
        "account_holder_name":           "Account Holder",
        "account_number":                generate_account_number(),
        "bank_proof":                    None,                     # Pick from live UI: Cancelled Cheque/Passbook
        "bank_attachment":               None,                     # File upload (optional)
    }


def generate_valid_irrigation_data():
    """Generate valid data for Irrigation Details tab (Borrower Farmer only)."""
    return {
        "source_of_irrigation":          None,                     # Pick from live UI (Well, Canal, Borewell, River)
        "method_of_irrigation":          None,                     # Pick from live UI (Drip, Sprinkler, Flood)
    }


def generate_valid_award_data():
    """Generate valid data for Award Details tab (Borrower Farmer only)."""
    return {
        "award_name":                    f"Krishi Puraskar {random.randint(1, 100)}",
        "award_year":                    str(random.randint(2015, 2025)),
    }


def generate_valid_loan_data():
    """Generate valid data for Loan Details tab (Borrower Farmer only).
    NOTE: 'Availed From' is a DATEPICKER (not text input!) - format DD/MM/YYYY.
    BUG-F06: Amount fields accept 0 and . prefix (but we generate valid data).
    """
    return {
        "loan_name":                     f"Loan_{random.randint(100, 999)}",
        "facility_type":                 None,                     # Pick from live UI: Non Funded/CC/Term Loan
        "purpose_of_loan":               "Agricultural equipment purchase",
        "availed_from_date":             "15/03/2023",             # DATEPICKER! DD/MM/YYYY format
        "sanctioned_amount":             str(random.randint(50000, 5000000)),
        "present_outstanding_amount":    str(random.randint(1000, 500000)),
    }


# ==============================================================
#  Full Farmer Data Generator (all tabs combined)
# ==============================================================

def generate_full_valid_farmer_data(category="Walk-in Farmer"):
    """Generate complete valid data for ALL tabs based on farmer category.
    Used for end-to-end happy path tests.
    Data keys match the FIELD_METADATA keys for consistent lookup.
    """
    data = generate_valid_farmer_step0(category)

    # All 3 categories have Current Address and Permanent Address
    data["current_address"] = generate_valid_address_data()
    data["permanent_address"] = generate_valid_permanent_address_data()

    # All 3 categories have Bank Details
    data["bank_details"] = generate_valid_bank_data()

    # FPC Member and Borrower Farmer have Land, Crop, KYC
    if category in ("Borrower Farmer", "FPC Member"):
        data["land_details"] = generate_valid_land_data()
        data["crop_details"] = generate_valid_crop_data()
        data["kyc_details"] = generate_valid_kyc_data()

    # Borrower Farmer only tabs
    if category == "Borrower Farmer":
        data["family_details"] = generate_valid_family_data()
        data["other_details"] = generate_valid_other_details_data()
        data["vehicle_details"] = generate_valid_vehicle_data()
        data["income_details"] = generate_valid_income_data()
        data["irrigation_details"] = generate_valid_irrigation_data()
        data["award_details"] = generate_valid_award_data()
        data["loan_details"] = generate_valid_loan_data()

    return data


# ==============================================================
#  Validation Test Data Helpers
# ==============================================================

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
    """Return dict with all empty strings - for mandatory field validation."""
    return {
        "party_reference":          "",
        "farmer_name":              "",
        "email":                    "",
        "phone_number":             "",
        "date_of_birth":            "",
        "password":                 "",
        "farmer_category":          "",
        "land_classification":      "",
    }


def generate_farmer_name_only():
    """Return dict with only Farmer Name filled."""
    return {
        "farmer_name":              generate_farmer_name(),
        "email":                    "",
        "phone_number":             "",
        "password":                 "",
        "farmer_category":          "",
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
        "farmer_name":              existing_name,
        "phone_number":             existing_phone,
        "email":                    generate_email(),
        "password":                 generate_password(),
        "farmer_category":          "Walk-in Farmer",
    }
