"""
item_master_data.py
-------------------
Test data generators for RhythmERP Item Master screen.

Location: Commodity Settings > Commodity Master > Item Master
URL:      /#/dynamic-screens/Item%20Master

FORM LAYOUT (3-step stepper — verified 2026-05-15 on live app):
  Step 1 - Additional Details (INCLUDES ALL TOGGLES):
    - Item Name              (AUTO-GENERATED, READONLY — space-separated concat of Attr 1-5)
    - Item Code              (AUTO-GENERATED, editable — dash-separated concat of Attr 1-5)
    - Description            (text input,   optional)
    - Item Group             (mat-select,   optional)
    - Item Category          (mat-select,   required)
    - Item Type              (mat-select,   required)
    - Item Attribute1-5      (mat-select,   optional each)
    - UOM                    (mat-select,   required)
    - HSN SAC Code           (mat-select,   required)
    - Base Uom               (mat-select,   required)
    - Base Uom Conversion    (text input,   required)
    *** PLUS 3 TOGGLE SWITCHES (NOT 4! Verified 2026-05-18): ***
    - Status                 (toggle switch, Active/Inactive, default Active)
    - Is Critical            (toggle switch, Yes/No, default No)
    - Include Wip Stock Cal  (toggle switch, Yes/No, default No)
    - Is Packing Material    (toggle switch, Yes/No, default No)
    NOTE: "Allow Negative Stock" toggle DOES NOT EXIST in Item Master

  Step 2 - Define Item Master Details (ATTACHMENT ONLY — NO toggles!):
    - Attachment Type        (mat-select,   optional)
    - File Upload            (file upload,   optional)

  Step 3 - Product Order Packeging Details (GRID TABLE):
    - Packaging              (mat-select,   per table row, optional)
    - Packaging Capacity     (number input, per table row, optional)
    - Base Packaging Capacity (number input, per table row, optional)
    - Add Row button

KEY RULES:
  - Item Name is READONLY — cannot be typed into (auto-generated from attributes)
    formcontrolname="name" (NOT "itemName") — confirmed via browser exploration
  - Item Code is editable after auto-generation
    formcontrolname="code" (NOT "itemCode") — confirmed via browser exploration
  - Tests for spaces-only, long strings, special chars in Item Name are NOT possible
    since the field cannot receive keyboard input
  - Item Group is NOT required in Create or Edit mode (confirmed 2026-05-18)
  - Base Uom does NOT auto-sync with UOM — they are independent fields (confirmed 2026-05-18)
  - Duplicate Item Names are ALLOWED — no uniqueness validation (confirmed 2026-05-18)
  - DROPDOWN FILL ORDER: Category → Group → Type → Attr1 → Attr2 → Attr3 → Attr4 → Attr5
    Category/Group/Type are INDEPENDENT, but Attributes cascade

TABLE COLUMNS:
  - View / Edit / History  (action buttons per row)
  - Item Name
  - UOM
  - Status
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_item_name(prefix="AutoItem"):
    """Generate a random item name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_item_code(prefix="ITM"):
    """Generate a random item code."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(10, 99)
    return f"{prefix}-{timestamp[-6:]}-{rand}"


def generate_description():
    """Generate a random description text."""
    words = [
        "Test item entry", "Automated test data", "Selenium validation",
        "Regression test item", "QA automation entry", "Smoke test data",
        "Performance test item", "Integration test entry",
        "Commodity test item", "Packaging validation item"
    ]
    return f"{random.choice(words)} - {random.randint(1000, 9999)}"


def generate_base_uom_conversion():
    """Generate a valid Base Uom Conversion value (positive number)."""
    return str(round(random.uniform(0.1, 100.0), 3))


def generate_packaging_capacity():
    """Generate a valid Packaging Capacity value."""
    return str(round(random.uniform(1.0, 1000.0), 2))


# ──────────────────────────────────────────────
# Complete Valid Data for Create (Step 1 only)
# ──────────────────────────────────────────────

def generate_valid_item_data(name_prefix="AutoItem"):
    """Generate a complete dict of valid item data for Create form Step 1.
    Dropdown values set to None — must be populated from live UI at runtime.
    ONLY 3 toggle switches in Step 1 data (NOT 4! Verified 2026-05-18).
    "Allow Negative Stock" DOES NOT EXIST in Item Master.
    Item Name is auto-generated from Item Attribute values (not typed).
    Item Group is NOT required (confirmed 2026-05-18).
    """
    return {
        "item_name": None,           # AUTO-GENERATED from attributes — don't type
        "item_code": generate_item_code(),
        "description": generate_description(),
        "item_category": None,       # Pick from live UI (REQUIRED) — FILL FIRST
        "item_group": None,          # Pick from live UI (NOT required!)
        "item_type": None,           # Pick from live UI (REQUIRED)
        "item_attribute1": None,     # Pick from live UI (optional)
        "item_attribute2": None,     # Pick from live UI (optional)
        "item_attribute3": None,     # Pick from live UI (optional)
        "item_attribute4": None,     # Pick from live UI (optional)
        "item_attribute5": None,     # Pick from live UI (optional)
        "uom": None,                 # Pick from live UI (REQUIRED)
        "hsn_sac_code": None,        # Pick from live UI (REQUIRED)
        "base_uom": None,            # Pick from live UI (REQUIRED)
        "base_uom_conversion": generate_base_uom_conversion(),
        # Toggle switches — 3 on Step 1 (NOT 4! Verified 2026-05-18)
        "status": True,                  # Active (default)
        "is_critical": False,            # No (default)
        "include_wip": False,            # No (default)
        "is_packing_material": False,    # No (default)
    }


def generate_valid_step2_data():
    """Generate data for Step 2 (Define Item Master Details).
    Step 2 contains ONLY Attachment Type + File Upload — NO toggles!
    All toggles are on Step 1.
    """
    return {
        "attachment_type": None,       # Pick from live UI (optional)
        "file_path": None,             # File path for upload (optional)
    }


def generate_valid_step3_data():
    """Generate data for Step 3 (Product Order Packaging Details).
    Packaging table rows are optional.
    """
    return {
        "packaging_rows": []  # List of dicts: {packaging, capacity, base_capacity}
    }


def generate_full_valid_item_data(name_prefix="AutoItem"):
    """Generate complete valid data for ALL 3 steps.
    Used for end-to-end happy path tests.
    """
    data = generate_valid_item_data(name_prefix)
    data["step2"] = generate_valid_step2_data()
    data["step3"] = generate_valid_step3_data()
    return data


def generate_valid_edit_data(name_prefix="EditItem"):
    """Generate valid data for Edit form — only fields we want to change.
    On Edit, Item Name is READONLY (auto-generated from attributes).
    We can modify: Item Code, Description, Base Uom Conversion, and toggles.
    To change Item Name, you must change the Item Attribute values instead.
    """
    return {
        "item_code": generate_item_code(),
        "description": generate_description(),
        "base_uom_conversion": generate_base_uom_conversion(),
        # Toggle switches (on Step 1) — flip some for edit testing
        "status": True,
        "is_critical": False,
        "include_wip": False,
        "is_packing_material": False,
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary for Name)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds max for Name)."""
    return "A" * 256


def generate_spaces_only(length=10):
    """Generate a string of only spaces (for Name validation test)."""
    return " " * length


def generate_special_char_name():
    """Generate a name with special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"Item{special}"


def generate_negative_uom_conversion():
    """Return a negative Base Uom Conversion value."""
    return f"-{round(random.uniform(0.1, 100.0), 3)}"


def generate_zero_uom_conversion():
    """Return zero for Base Uom Conversion."""
    return "0"


def generate_alpha_uom_conversion():
    """Return alphabetic characters for Base Uom Conversion."""
    return "abcDEF"


def generate_special_char_uom_conversion():
    """Return special characters for Base Uom Conversion."""
    return "!@#$"


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation.
    Only Step 1 fields — this is what Submit sees.
    """
    return {
        "item_name": "",
        "item_code": "",
        "description": "",
        "item_category": "",        # REQUIRED — fill first in order
        "item_group": "",           # NOT required
        "item_type": "",            # REQUIRED
        "item_attribute1": "",
        "item_attribute2": "",
        "item_attribute3": "",
        "item_attribute4": "",
        "item_attribute5": "",
        "uom": "",                  # REQUIRED
        "hsn_sac_code": "",         # REQUIRED
        "base_uom": "",             # REQUIRED (independent of UOM)
        "base_uom_conversion": "",   # REQUIRED
    }


def generate_name_only_data(name_prefix="NameOnly"):
    """Return dict with only Item Name filled — for partial field validation."""
    return {
        "item_name": generate_item_name(name_prefix),
        "item_code": "",
        "description": "",
        "item_category": "",
        "item_group": "",           # NOT required
        "item_type": "",
        "item_attribute1": "",
        "item_attribute2": "",
        "item_attribute3": "",
        "item_attribute4": "",
        "item_attribute5": "",
        "uom": "",
        "hsn_sac_code": "",
        "base_uom": "",
        "base_uom_conversion": "",
    }


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing name — for duplicate name test."""
    # V2: Duplicate Item Names are ALLOWED — no uniqueness validation (confirmed 2026-05-18)
    # This test should verify that duplicates CAN be created (not that they're blocked)
    return {
        "item_name": existing_name,   # Will be ignored — auto-generated from attributes
        "item_code": generate_item_code(),
        "description": generate_description(),
        "item_category": None,       # Fill first per V2 order
        "item_group": None,          # NOT required
        "item_type": None,
        "item_attribute1": None,
        "item_attribute2": None,
        "item_attribute3": None,
        "item_attribute4": None,
        "item_attribute5": None,
        "uom": None,
        "hsn_sac_code": None,
        "base_uom": None,            # INDEPENDENT of UOM
        "base_uom_conversion": generate_base_uom_conversion(),
    }


def generate_decimal_uom_conversion():
    """Return a decimal Base Uom Conversion value."""
    return f"{random.randint(1, 99)}.{random.randint(10, 99)}"


def generate_uom_conversion_with_spaces():
    """Return spaces for Base Uom Conversion field."""
    return "   "


def generate_item_code_with_special_chars():
    """Generate an item code with special characters."""
    return f"ITM@#{random.randint(100, 999)}"


# ══════════════════════════════════════════════════════════════════════
# API BATCH CREATE — FK IDs, Data Pool & Payload Builder
# ══════════════════════════════════════════════════════════════════════
# Discovered from live ERP API on 2026-06-02.
# Used by scripts/batch_create.py for API-first bulk data creation.
#
# API Payload Structure (3-step stepper):
#   {
#     "id": "",
#     "attribute_name": "Item Master",
#     "name": "",                    # AUTO-GENERATED from attributes
#     "code": "",                    # AUTO-GENERATED but editable
#     "description": "...",
#     "item_category": <FK_ID>,      # REQUIRED
#     "item_group": <FK_ID>,         # Optional
#     "item_type": <FK_ID>,          # REQUIRED
#     "item_attribute1": <FK_ID>,    # REQUIRED
#     "item_attribute2": <FK_ID>,    # Optional
#     "item_attribute3": <FK_ID>,    # Optional
#     "item_attribute4": <FK_ID>,    # Optional
#     "item_attribute5": <FK_ID>,    # Optional
#     "uom": <FK_ID>,               # REQUIRED
#     "hsn_sac_code": <FK_ID>,       # REQUIRED
#     "base_uom": <FK_ID>,           # REQUIRED
#     "base_uom_conversion": "1",    # REQUIRED
#     "status": true,
#     "children": [
#       {"stepper_name": "Additional Details", "is_stepper": true,
#        "details": [], "children": [],
#        "is_critical": false, "include_wip_in_stock_cal": false,
#        "is_packing_material": false},
#       {"stepper_name": "Define Item Master Details", "is_stepper": true,
#        "details": [], "children": [],
#        "attachment_type": null, "item_attachment": null},
#       {"stepper_name": "Product Order Packeging Details", "is_stepper": true,
#        "details": [], "children": []}
#     ]
#   }
# ══════════════════════════════════════════════════════════════════════

# ── FK IDs from live ERP (fetched 2026-06-02) ───────────────────────

ITEM_CATEGORY_OPTIONS = {
    "Green Veggies": 61,
    "Agriculture Items": 62,
    "FMCG Items": 63,
    "Electrical Items": 64,
    "Hardware Items": 65,
    "Office & Stationery Items": 66,
    "Food Grains": 67,
    "Pulses & Legumes": 68,
    "Spices & Condiments": 69,
    "Oilseeds": 70,
    "Dairy Products": 71,
    "Textile Raw Materials": 72,
    "Rice Varieties": 73,
    "Wheat Products": 74,
    "Millets": 75,
    "Fresh Produce": 76,
    "Packaged Foods": 77,
    "Construction Materials": 78,
    "Chemical Products": 79,
    "Fertilizers": 80,
    "Pesticides": 81,
    "Basmati Rice": 82,
    "Non-Basmati Rice": 83,
    "Chickpeas": 84,
    "Turmeric": 85,
    "Cotton Raw": 86,
}

ITEM_GROUP_OPTIONS = {
    "IG001": 85,
    "AGRGRP01": 86,
    "ELEGRP01": 87,
    "PKGGRP01": 88,
    "TOOLGRP01": 89,
    "GRN001": 90,
    "PULSE002": 91,
    "SPICE003": 92,
    "OILS004": 93,
    "DAIRY005": 94,
    "TEXTL006": 95,
    "RICE007": 96,
    "WHEAT008": 97,
    "MILL009": 98,
    "FRESH010": 99,
    "PACK011": 100,
    "CONST012": 101,
    "CHEM013": 102,
    "FERT014": 103,
    "PEST015": 104,
    "TRAN016": 105,
    "STOR017": 106,
    "QC018": 107,
    "LOGS019": 108,
    "PROC020": 109,
}

ITEM_TYPE_OPTIONS = {
    "Farm": 113,
    "Non Farm": 114,
}

ITEM_ATTRIBUTE1_OPTIONS = {
    "Soyabean": 117, "Mango": 121, "Harbara": 119, "channa": 118,
    "Apple": 120, "organic": 122, "Wheat": 123, "Rice": 124,
    "Cotton": 125, "Sugarcane": 126, "Tur Dal": 127, "Groundnut": 128,
    "Soybean": 129, "Maize": 130, "Jowar": 131, "Bajra": 132,
    "Ragi": 133, "Onion": 134, "Potato": 135, "Tomato": 136,
    "Chilli": 137, "Turmeric": 138, "Ginger": 139, "Garlic": 140,
    "Coriander": 141, "Cumin": 142, "Mustard": 143, "Barley": 144,
    "Oats": 145, "Millets": 146, "Quinoa": 147,
}

ITEM_ATTRIBUTE2_OPTIONS = {
    "Green": 65, "Yellow": 66, "Single Double Layred": 67,
    "Non Green": 68, "Premium Grade": 69, "Organic Certified": 70,
    "Standard Grade": 71, "Extra Large": 72, "Medium Sized": 73,
    "Small Sized": 74, "Farm Fresh": 75, "Cold Stored": 76,
    "Sun Dried": 77, "Machine Cleaned": 78, "Hand Picked": 79,
    "Hybrid Variety": 80, "Native Variety": 81, "Early Harvest": 82,
    "Late Harvest": 83, "A Grade": 84, "B Grade": 85,
    "Washed and Graded": 86, "Packed in Jute": 87, "Vacuum Sealed": 88,
    "PP Bag": 89, "HDPE Bag": 90, "Paper Bag": 91,
    "Tin Container": 92, "Glass Jar": 93, "Plastic Crate": 94,
    "Wooden Box": 95, "Corrugated Box": 96,
}

ITEM_ATTRIBUTE3_OPTIONS = {
    "Color": 1, "Size": 2, "Material Type": 3, "Weight": 4,
    "Brand": 5, "Grade": 6, "Finish Type": 7, "Texture": 8,
    "Pattern": 9, "Thickness": 10, "Origin": 11, "Season Type": 12,
    "Fabric Type": 13, "Purity": 14, "Variety": 15, "Count": 16,
    "Staple Length": 17, "Micronaire": 18, "Moisture Content": 19,
    "Lot Number": 20, "Product Grade": 21, "Organic Certified": 22,
    "Conventional": 23, "Premium Grade": 24, "Standard Grade": 25,
    "Economy Grade": 26, "Export Quality": 27, "First Sort": 28,
    "Second Sort": 29,
}

ITEM_ATTRIBUTE4_OPTIONS = {
    "Moisture Resistant": 55, "UV Protected": 56, "Thermal Insulated": 57,
    "Anti Fungal": 58, "Bio Degradable": 59, "Heavy Duty": 60,
    "Light Weight": 61, "Perforated": 62, "Tamper Proof": 63,
    "Food Safe": 64, "Weather Proof": 65, "Aroma Retentive": 66,
    "Transparent": 67, "Reinforced Base": 68, "Stackable": 69,
    "Color Coded": 70, "Waterproof Lined": 71, "Microwaveable": 72,
    "Recyclable": 73, "Multi Layered": 74, "Biodegradable": 75,
    "Single Use": 76, "Reusable": 77, "Laminated": 78,
    "Uncoated": 79, "Coated": 80, "Foil Lined": 81, "BOPP Film": 82,
}

ITEM_ATTRIBUTE5_OPTIONS = {
    "Premium Grade": 51, "Standard Grade": 52, "Economy Grade": 53,
    "Organic Certified": 54, "Conventional": 55, "Hybrid Variety": 56,
    "Local Variety": 57, "Export Quality": 58, "Fresh Harvest": 59,
    "Dry Processed": 60, "Cold Storage": 61, "Ripened": 62,
    "Raw Unprocessed": 63, "Semi Processed": 64, "Fully Processed": 65,
    "Wholesale Lot": 66, "Retail Pack": 67, "Farm Fresh": 68,
    "Sorted Graded": 69, "Certified Origin": 70, "FSSAI Approved": 71,
    "ISO 22000": 72, "HACCP Certified": 73, "GMP Certified": 74,
    "Fair Trade": 75, "Rainforest Alliance": 76, "UTZ Certified": 77,
    "Global GAP": 78,
}

UOM_OPTIONS = {
    "KG": 249, "MT": 250, "QT": 251, "NOS": 252, "Litres": 253,
    "LTR": 501, "MTR": 502, "dozens": 504, "Litre": 506, "ML": 507,
    "MUND": 528, "BIGHA": 529, "SER": 530, "CAN": 531, "SQFT": 532,
    "SET": 533, "KM": 534, "HP": 535, "MM": 536, "SET60": 537,
}

HSN_SAC_CODE_OPTIONS = {
    "995411": 108, "995412": 109, "995421": 110, "995422": 111,
    "0101": 112, "0201": 113, "0301": 114, "0401": 115,
    "0501": 116, "0601": 117, "0701": 118, "0801": 119,
    "0901": 120, "1001": 121, "995413": 122, "995414": 123,
    "995415": 124, "996311": 125, "996312": 126, "997111": 127,
    "997112": 128, "997113": 129, "996211": 130, "996212": 131,
    "8409": 132, "5208": 133, "8525": 134, "0703": 135,
    "6203": 136, "9018": 137, "3003": 138, "4901": 139,
    "2501": 140, "2009": 141,
}

BASE_UOM_OPTIONS = UOM_OPTIONS  # Same pool as UOM

PACKAGING_OPTIONS = {
    "KG": 249, "MT": 250, "QT": 251, "NOS": 252, "Litres": 253,
    "LTR": 501, "MTR": 502, "dozens": 504, "Litre": 506, "ML": 507,
}


# ── Realistic Item Master data pool ──────────────────────────────────
# Each entry: (category, group, type, attr1, attr2, attr3, attr4, attr5, uom, base_uom, hsn, description)
# All FK values use the display names — resolved to IDs at payload build time.

ITEM_MASTER_DATA_POOL = [
    # ── Food Grains ──────────────────────────────────────────────────
    ("Food Grains", "GRN001", "Farm", "Wheat", "Premium Grade", "Product Grade", "Multi Layered", "Organic Certified", "KG", "KG", "1001", "Premium quality wheat grain for flour milling"),
    ("Food Grains", "GRN001", "Farm", "Rice", "Standard Grade", "Moisture Content", "Recyclable", "Standard Grade", "KG", "KG", "1001", "Standard rice variety for daily consumption"),
    ("Food Grains", "GRN001", "Farm", "Maize", "A Grade", "Lot Number", "Biodegradable", "Economy Grade", "MT", "MT", "1001", "Yellow maize corn for animal feed processing"),
    ("Food Grains", "RICE007", "Farm", "Rice", "Farm Fresh", "Organic Certified", "Foil Lined", "Export Quality", "KG", "KG", "1001", "Freshly harvested basmati rice for export"),
    ("Food Grains", "WHEAT008", "Farm", "Wheat", "Machine Cleaned", "Conventional", "Coated", "Local Variety", "QT", "QT", "1001", "Machine cleaned wheat for industrial milling"),

    # ── Pulses & Legumes ─────────────────────────────────────────────
    ("Pulses & Legumes", "PULSE002", "Farm", "channa", "Premium Grade", "Product Grade", "Multi Layered", "FSSAI Approved", "KG", "KG", "0713", "Premium chickpea for dal and flour production"),
    ("Pulses & Legumes", "PULSE002", "Farm", "Tur Dal", "Standard Grade", "Lot Number", "Recyclable", "ISO 22000", "KG", "KG", "0713", "Pigeon pea for dal processing and packaging"),
    ("Pulses & Legumes", "PULSE002", "Farm", "Soybean", "Organic Certified", "Moisture Content", "Biodegradable", "Organic Certified", "KG", "KG", "1201", "Organic soybean for oil extraction and protein"),
    ("Pulses & Legumes", "PULSE002", "Farm", "Harbara", "B Grade", "Conventional", "Heavy Duty", "Conventional", "QT", "QT", "0713", "Kabuli chickpea variety for food processing"),

    # ── Spices & Condiments ──────────────────────────────────────────
    ("Spices & Condiments", "SPICE003", "Farm", "Chilli", "Extra Large", "Premium Grade", "Laminated", "Premium Grade", "KG", "KG", "0904", "Red chilli for spice and oleoresin extraction"),
    ("Spices & Condiments", "SPICE003", "Farm", "Turmeric", "Premium Grade", "Organic Certified", "Multi Layered", "FSSAI Approved", "KG", "KG", "0910", "Organic turmeric rhizomes for spice and dye"),
    ("Spices & Condiments", "SPICE003", "Farm", "Coriander", "Medium Sized", "Standard Grade", "Recyclable", "Standard Grade", "KG", "KG", "0909", "Coriander seeds for spice blending and grinding"),
    ("Spices & Condiments", "SPICE003", "Farm", "Cumin", "Farm Fresh", "Product Grade", "Biodegradable", "Export Quality", "KG", "KG", "0909", "Farm fresh cumin seeds for premium spice market"),
    ("Spices & Condiments", "SPICE003", "Farm", "Ginger", "Sun Dried", "Moisture Content", "Foil Lined", "HACCP Certified", "KG", "KG", "0910", "Sun dried ginger rhizome for spice and medicinal use"),

    # ── Oilseeds ─────────────────────────────────────────────────────
    ("Oilseeds", "OILS004", "Farm", "Mustard", "Premium Grade", "Product Grade", "Laminated", "Organic Certified", "KG", "KG", "1207", "Mustard oilseeds for cold-pressed oil extraction"),
    ("Oilseeds", "OILS004", "Farm", "Groundnut", "A Grade", "Lot Number", "Coated", "Standard Grade", "KG", "KG", "1202", "Groundnut for oil extraction and confectionery"),

    # ── Fresh Produce ────────────────────────────────────────────────
    ("Fresh Produce", "FRESH010", "Farm", "Onion", "Farm Fresh", "Product Grade", "Perforated", "Farm Fresh", "QT", "QT", "0703", "Fresh red onion for wholesale and retail market"),
    ("Fresh Produce", "FRESH010", "Farm", "Potato", "Medium Sized", "Moisture Content", "Uncoated", "Local Variety", "QT", "QT", "0701", "Medium potato for fresh market and processing"),
    ("Fresh Produce", "FRESH010", "Farm", "Tomato", "Premium Grade", "Organic Certified", "Food Safe", "Fresh Harvest", "KG", "KG", "0702", "Premium tomatoes for paste and fresh market"),
    ("Fresh Produce", "FRESH010", "Farm", "Mango", "Extra Large", "Export Quality", "Stackable", "Export Quality", "KG", "KG", "0805", "Alphonso mango for pulp and export market"),
    ("Fresh Produce", "FRESH010", "Farm", "Apple", "Premium Grade", "Cold Stored", "Transparent", "Premium Grade", "KG", "KG", "0808", "Cold stored apple for juice and fresh market"),

    # ── Dairy Products ───────────────────────────────────────────────
    ("Dairy Products", "DAIRY005", "Farm", "organic", "Organic Certified", "Moisture Content", "Tamper Proof", "FSSAI Approved", "Litre", "Litre", "0401", "Organic milk product for dairy processing"),
    ("Dairy Products", "DAIRY005", "Non Farm", "organic", "Premium Grade", "Product Grade", "Aroma Retentive", "ISO 22000", "KG", "KG", "0406", "Premium ghee for retail packaging and export"),

    # ── Office & Stationery ──────────────────────────────────────────
    ("Office & Stationery Items", "TOOLGRP01", "Non Farm", "organic", "Standard Grade", "Color", "Light Weight", "Conventional", "NOS", "NOS", "995411", "Office stationery item for workplace supply"),
    ("Office & Stationery Items", "TOOLGRP01", "Non Farm", "organic", "Standard Grade", "Brand", "Recyclable", "Standard Grade", "NOS", "NOS", "995412", "Standard office supply item for procurement"),

    # ── Cotton & Textile ─────────────────────────────────────────────
    ("Cotton Raw", "AGRGRP01", "Farm", "Cotton", "A Grade", "Staple Length", "Weather Proof", "Export Quality", "QT", "QT", "5208", "Raw cotton with long staple for textile industry"),
    ("Cotton Raw", "AGRGRP01", "Farm", "Cotton", "B Grade", "Micronaire", "Reinforced Base", "Local Variety", "QT", "QT", "5208", "Medium grade cotton for domestic textile use"),

    # ── Chemical Products ────────────────────────────────────────────
    ("Chemical Products", "CHEM013", "Non Farm", "organic", "Standard Grade", "Material Type", "Heavy Duty", "Conventional", "KG", "KG", "3003", "Industrial chemical product for processing"),
    ("Chemical Products", "FERT014", "Non Farm", "organic", "Standard Grade", "Weight", "Tamper Proof", "Conventional", "KG", "KG", "3105", "Agricultural fertilizer for crop nutrition"),

    # ── Packaged Foods ───────────────────────────────────────────────
    ("Packaged Foods", "PACK011", "Non Farm", "Rice", "Machine Cleaned", "Product Grade", "Foil Lined", "FSSAI Approved", "KG", "KG", "1006", "Packaged rice for retail and distribution"),
    ("Packaged Foods", "PACK011", "Non Farm", "Wheat", "Premium Grade", "Moisture Content", "Multi Layered", "ISO 22000", "KG", "KG", "1101", "Premium packaged wheat flour for retail"),
]


def _resolve_fk(name, options_dict):
    """Resolve a FK display name to its integer ID. Returns None if not found."""
    if name is None:
        return None
    return options_dict.get(name)


def build_item_master_api_payload(
    category, group, item_type, attr1, attr2, attr3, attr4, attr5,
    uom, base_uom, hsn, description,
    base_uom_conversion="1",
    is_critical=False,
    include_wip=False,
    is_packing_material=False,
    status=True,
):
    """
    Build a complete API payload for Item Master (3-step stepper).

    Args:
        category, group, item_type, attr1-5, uom, base_uom, hsn:
            Display names from the FK option dicts above.
        description: Free text description.
        base_uom_conversion: Numeric string (default "1").
        is_critical, include_wip, is_packing_material: Toggle booleans.
        status: Active/inactive toggle.

    Returns:
        dict: Complete JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    return {
        "id": "",
        "attribute_name": "Item Master",
        "name": "",
        "code": "",
        "description": description,
        "item_category": _resolve_fk(category, ITEM_CATEGORY_OPTIONS),
        "item_group": _resolve_fk(group, ITEM_GROUP_OPTIONS),
        "item_type": _resolve_fk(item_type, ITEM_TYPE_OPTIONS),
        "item_attribute1": _resolve_fk(attr1, ITEM_ATTRIBUTE1_OPTIONS),
        "item_attribute2": _resolve_fk(attr2, ITEM_ATTRIBUTE2_OPTIONS),
        "item_attribute3": _resolve_fk(attr3, ITEM_ATTRIBUTE3_OPTIONS),
        "item_attribute4": _resolve_fk(attr4, ITEM_ATTRIBUTE4_OPTIONS),
        "item_attribute5": _resolve_fk(attr5, ITEM_ATTRIBUTE5_OPTIONS),
        "uom": _resolve_fk(uom, UOM_OPTIONS),
        "hsn_sac_code": _resolve_fk(hsn, HSN_SAC_CODE_OPTIONS),
        "base_uom": _resolve_fk(base_uom, BASE_UOM_OPTIONS),
        "base_uom_conversion": base_uom_conversion,
        "status": status,
        "children": [
            {
                "stepper_name": "Additional Details",
                "is_stepper": True,
                "details": [],
                "children": [],
                "is_critical": is_critical,
                "include_wip_in_stock_cal": include_wip,
                "is_packing_material": is_packing_material,
            },
            {
                "stepper_name": "Define Item Master Details",
                "is_stepper": True,
                "details": [],
                "children": [],
                "attachment_type": None,
                "item_attachment": None,
            },
            {
                "stepper_name": "Product Order Packeging Details",
                "is_stepper": True,
                "details": [],
                "children": [],
            },
        ],
    }


def generate_item_master_payloads(count=10, offset=0):
    """
    Generate N API payloads for Item Master from the data pool.

    Args:
        count: Number of payloads to generate.
        offset: Start index in the data pool (skip already-used entries).

    Returns:
        list[dict]: List of complete API payloads.
    """
    pool = ITEM_MASTER_DATA_POOL
    payloads = []

    for i in range(count):
        idx = (offset + i) % len(pool)
        entry = pool[idx]

        payload = build_item_master_api_payload(
            category=entry[0],
            group=entry[1],
            item_type=entry[2],
            attr1=entry[3],
            attr2=entry[4],
            attr3=entry[5],
            attr4=entry[6],
            attr5=entry[7],
            uom=entry[8],
            base_uom=entry[9],
            hsn=entry[10],
            description=entry[11],
        )
        payloads.append(payload)

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Item Master: 3-step stepper, 10 FK dropdowns
# Root fields (17): name, code, description, item_category, item_group,
#   item_type, item_attribute1-5, uom, hsn_sac_code, base_uom,
#   base_uom_conversion, status
# Stepper children (3): Additional Details, Define Item Master Details,
#   Product Order Packeging Details

FIELD_VALIDATION_RULES = {
    # Root text fields
    "name": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "AUTO-GENERATED from attributes. Readonly in UI.",
    },
    "code": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "AUTO-GENERATED but editable. Dash-separated attributes.",
    },
    "description": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "Optional description.",
    },
    "base_uom_conversion": {
        "type": "character",
        "required": True,
        "max_length": 10,
        "note": "Conversion factor as string. Max 10 chars.",
    },
    # FK Dropdowns (required)
    "item_category": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(ITEM_CATEGORY_OPTIONS),
        "note": "FK to Item Category. 26 options.",
    },
    "item_type": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(ITEM_TYPE_OPTIONS),
        "note": "FK to Item Type. 2 options: Farm, Non Farm.",
    },
    "uom": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(UOM_OPTIONS),
        "note": "FK to UOM. 20 options.",
    },
    "hsn_sac_code": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(HSN_SAC_CODE_OPTIONS),
        "note": "FK to HSN SAC Code. 34 options.",
    },
    "base_uom": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(BASE_UOM_OPTIONS),
        "note": "FK to UOM (same pool). 20 options.",
    },
    # FK Dropdowns (optional)
    "item_group": {
        "type": "dropdown",
        "required": False,
        "fk_options_count": len(ITEM_GROUP_OPTIONS),
        "note": "FK to Item Group. 25 options. Optional.",
    },
    "item_attribute1": {
        "type": "dropdown",
        "required": False,
        "fk_options_count": len(ITEM_ATTRIBUTE1_OPTIONS),
        "note": "FK to Item Attribute1. 31 options. Optional.",
    },
    "item_attribute2": {
        "type": "dropdown",
        "required": False,
        "fk_options_count": len(ITEM_ATTRIBUTE2_OPTIONS),
        "note": "FK to Item Attribute2. 32 options. Optional.",
    },
    "item_attribute3": {
        "type": "dropdown",
        "required": False,
        "fk_options_count": len(ITEM_ATTRIBUTE3_OPTIONS),
        "note": "FK to Item Attribute3. 29 options. Optional.",
    },
    "item_attribute4": {
        "type": "dropdown",
        "required": False,
        "fk_options_count": len(ITEM_ATTRIBUTE4_OPTIONS),
        "note": "FK to Item Attribute4. 28 options. Optional.",
    },
    "item_attribute5": {
        "type": "dropdown",
        "required": False,
        "fk_options_count": len(ITEM_ATTRIBUTE5_OPTIONS),
        "note": "FK to Item Attribute5. 28 options. Optional.",
    },
    # Toggle
    "status": {
        "type": "toggle",
        "required": False,
        "default": True,
        "note": "Active/Inactive toggle. Default: Active (True).",
    },
    # Stepper toggles (on children[0])
    "is_critical": {
        "type": "toggle",
        "required": False,
        "default": False,
        "note": "On Additional Details stepper. Default: No (False).",
    },
    "include_wip_in_stock_cal": {
        "type": "toggle",
        "required": False,
        "default": False,
        "note": "On Additional Details stepper. Default: No (False).",
    },
    "is_packing_material": {
        "type": "toggle",
        "required": False,
        "default": False,
        "note": "On Additional Details stepper. Default: No (False).",
    },
}

STATUS_OPTIONS = {"Active": True, "Inactive": False}

# Name aliases for schema tests
ITEM_CATEGORY_NAMES = dict(ITEM_CATEGORY_OPTIONS)
ITEM_GROUP_NAMES = dict(ITEM_GROUP_OPTIONS)
ITEM_TYPE_NAMES = dict(ITEM_TYPE_OPTIONS)
ITEM_ATTRIBUTE1_NAMES = dict(ITEM_ATTRIBUTE1_OPTIONS)
ITEM_ATTRIBUTE2_NAMES = dict(ITEM_ATTRIBUTE2_OPTIONS)
ITEM_ATTRIBUTE3_NAMES = dict(ITEM_ATTRIBUTE3_OPTIONS)
ITEM_ATTRIBUTE4_NAMES = dict(ITEM_ATTRIBUTE4_OPTIONS)
ITEM_ATTRIBUTE5_NAMES = dict(ITEM_ATTRIBUTE5_OPTIONS)
UOM_NAMES = dict(UOM_OPTIONS)
HSN_SAC_CODE_NAMES = dict(HSN_SAC_CODE_OPTIONS)
BASE_UOM_NAMES = dict(BASE_UOM_OPTIONS)

STEPPER_NAMES = ["Additional Details", "Define Item Master Details", "Product Order Packeging Details"]

DEFAULT_ITEM_MASTER_FK_IDS = {
    "item_category": ITEM_CATEGORY_OPTIONS,
    "item_group": ITEM_GROUP_OPTIONS,
    "item_type": ITEM_TYPE_OPTIONS,
    "item_attribute1": ITEM_ATTRIBUTE1_OPTIONS,
    "item_attribute2": ITEM_ATTRIBUTE2_OPTIONS,
    "item_attribute3": ITEM_ATTRIBUTE3_OPTIONS,
    "item_attribute4": ITEM_ATTRIBUTE4_OPTIONS,
    "item_attribute5": ITEM_ATTRIBUTE5_OPTIONS,
    "uom": UOM_OPTIONS,
    "hsn_sac_code": HSN_SAC_CODE_OPTIONS,
    "base_uom": BASE_UOM_OPTIONS,
}

def generate_batch_payloads(count=20, prefix=None, dropdown_ids=None):
    return generate_item_master_payloads(count=count)
