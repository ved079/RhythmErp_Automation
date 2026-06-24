"""
item_category_data.py
---------------------
Test data generators for RhythmERP Item Category screen.

Location: Commodity Settings > Item Category
URL:      /#/dynamic-screens/Item%20Category

FORM LAYOUT (Simple popup — NOT a stepper):
  - Item Category       (text input,   required)
  - Item Description    (text input,   required)
  - Level               (number input, required — accepts negatives, no decimals,
                         leading zeros stripped on save, accepts 0)

TABLE COLUMNS:
  - View / Edit / History   (action buttons per row)
  - Item Category / Item Description / Level

NOTES:
  - NO Status toggle
  - NO dropdowns
  - NO Delete button
  - HAS History button
  - Duplicates ALLOWED for Item Category name
  - Level field: accepts negative integers, strips leading zeros on save,
    accepts 0, does NOT accept decimals

KEY RULES:
  - NEVER use Keys.ESCAPE (closes entire popup form!)
  - ALL SweetAlert2 dismissals MUST use JS querySelector click
  - Test prefix: IC
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def generate_item_category_name(prefix="AutoIC"):
    """Generate a unique Item Category name with timestamp.
    NOTE: Item Category field only accepts chars, nums, hyphen (-) and slash (/).
    NO underscores — they cause 'Validation Failed' on the live system."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}-{timestamp}-{rand}"


def generate_item_description():
    """Generate a random Item Description text."""
    words = [
        "Test category entry", "Automated test data", "Selenium validation",
        "Regression test category", "QA automation entry", "Smoke test data",
        "Performance test category", "Integration test entry",
        "Commodity test category", "Category validation item"
    ]
    return f"{random.choice(words)} - {random.randint(1000, 9999)}"


def generate_level():
    """Generate a valid positive Level value."""
    return str(random.randint(1, 100))


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_item_category_data(name_prefix="AutoIC"):
    """Generate a complete dict of valid Item Category data for Create form."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": generate_item_description(),
        "level": generate_level(),
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_long_category_name(length=256):
    """Generate a string of exactly `length` characters for Item Category field."""
    return "C" * length


def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_special_char_category():
    """Generate a category name with special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"IC{special}"


def generate_sql_injection():
    """Generate SQL injection string for testing."""
    return "'; DROP TABLE item_category; --"


def generate_xss_attempt():
    """Generate XSS attempt string for testing."""
    return "<script>alert('xss')</script>"


def generate_negative_level():
    """Return a negative Level value — accepted by the field."""
    return f"-{random.randint(1, 99)}"


def generate_zero_level():
    """Return zero for Level — accepted by the field."""
    return "0"


def generate_decimal_level():
    """Return a decimal Level value — should be rejected or truncated."""
    return f"{random.randint(1, 99)}.{random.randint(10, 99)}"


def generate_leading_zeros_level():
    """Return a Level with leading zeros — should be stripped on save."""
    return "007"


def generate_large_level():
    """Return a very large number for Level."""
    return "9999999"


def generate_alpha_level():
    """Return alphabetic characters for Level — should not type in number field."""
    return "abc"


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "item_category": "",
        "item_description": "",
        "level": "",
    }


def generate_category_only_data(name_prefix="CatOnly"):
    """Return dict with only Item Category filled."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": "",
        "level": "",
    }


def generate_description_only_data():
    """Return dict with only Item Description filled."""
    return {
        "item_category": "",
        "item_description": generate_item_description(),
        "level": "",
    }


def generate_level_only_data():
    """Return dict with only Level filled."""
    return {
        "item_category": "",
        "item_description": "",
        "level": generate_level(),
    }


def generate_category_description_no_level(name_prefix="CatDesc"):
    """Return dict with Item Category and Description but no Level."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": generate_item_description(),
        "level": "",
    }


def generate_category_level_no_description(name_prefix="CatLvl"):
    """Return dict with Item Category and Level but no Description."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": "",
        "level": generate_level(),
    }


def generate_duplicate_category_data(existing_name):
    """Return valid data using an existing Item Category name — duplicates allowed."""
    return {
        "item_category": existing_name,
        "item_description": generate_item_description(),
        "level": generate_level(),
    }


def generate_valid_edit_data(name_prefix="EditIC"):
    """Generate valid data for Edit form — fields we want to change."""
    return {
        "item_category": generate_item_category_name(name_prefix),
        "item_description": generate_item_description(),
        "level": generate_level(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  API Batch Create — Data Pool + Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Screen structure (discovered 2026-06-02):
#   Item Category: item_code* (text, required, unique — the category name),
#                  item_description (text, optional),
#                  level* (integer, required — hierarchy level 1/2/3),
#                  status (boolean, no toggle shown but accepted in payload)
#   FLAT screen — no steppers, no children, no FK dropdowns.
#
# Note on field naming:
#   - UI label says "Item Category" but the API field key is "item_code"
#   - UI label says "Item Description" but the API field key is "item_description"
#   - Level is an integer (1 = top-level, 2 = sub-category, 3 = sub-sub-category)
#
# Existing entries in ERP (as of 2026-06-02, 26 total):
#   Level 1: Food Grains, Pulses & Legumes, Spices & Condiments, Oilseeds,
#            Dairy Products, Textile Raw Materials, Green Veggies
#   Level 2: Rice Varieties, Wheat Products, Millets, Fresh Produce,
#            Packaged Foods, Construction Materials, Chemical Products,
#            Fertilizers, Pesticides, Agriculture Items, FMCG Items,
#            Electrical Items, Hardware Items, Office & Stationery Items
#   Level 3: Basmati Rice, Non-Basmati Rice, Chickpeas, Turmeric, Cotton Raw
#
# This data pool provides additional category entries NOT already in the system.
# ═══════════════════════════════════════════════════════════════════════════════

# Each entry is a tuple: (item_code, item_description, level)
# level: 1 = top-level category, 2 = sub-category, 3 = sub-sub-category

ITEM_CATEGORY_API_DATA = [
    # ── Level 1: Top-Level Categories ───────────────────────────────────
    ("Beverages", "Tea, coffee, juices and drink products", 1),
    ("Sugar & Sweeteners", "Sugar, jaggery, honey and sweetener products", 1),
    ("Animal Feed", "Cattle feed, poultry feed and fodder products", 1),
    ("Forestry Products", "Timber, bamboo and forest produce", 1),
    ("Marine Products", "Fish, shrimp and seafood products", 1),
    ("Pharmaceuticals", "Medicines and pharmaceutical raw materials", 1),
    ("Packaging Materials", "Bags, containers and packaging supplies", 1),
    ("Automotive Parts", "Vehicle spare parts and accessories", 1),

    # ── Level 2: Sub-Categories ─────────────────────────────────────────
    # Under Food Grains
    ("Coarse Cereals", "Maize, barley, oats and other coarse grains", 2),
    ("Paddy Rice", "Raw paddy and unprocessed rice", 2),

    # Under Pulses & Legumes
    ("Gram Varieties", "Chana, moong, urad and other gram types", 2),
    ("Lentil Varieties", "Masoor, toor and other lentil types", 2),

    # Under Spices & Condiments
    ("Whole Spices", "Unprocessed whole spice products", 2),
    ("Ground Spices", "Processed and ground spice powders", 2),
    ("Dry Fruits & Nuts", "Almond, cashew, raisin and dried fruit products", 2),

    # Under Oilseeds
    ("Edible Oils", "Refined and cold-pressed edible oils", 2),
    ("Oilseed Cakes", "Expeller cakes and oilseed meal byproducts", 2),

    # Under Sugar & Sweeteners
    ("Raw Sugar", "Unrefined and raw sugar products", 2),
    ("Jaggery Products", "Traditional jaggery and gur products", 2),

    # Under Dairy Products
    ("Milk Products", "Milk, curd, paneer and fresh dairy", 2),
    ("Butter & Ghee", "Butter, ghee and clarified fat products", 2),

    # Under Beverages
    ("Tea Products", "Tea leaves, dust and blended teas", 2),
    ("Coffee Products", "Green beans, roasted and ground coffee", 2),

    # Under Animal Feed
    ("Cattle Feed", "Dairy cattle feed and supplements", 2),
    ("Poultry Feed", "Broiler and layer poultry feed", 2),

    # Under Packaging Materials
    ("Woven Sacks", "PP woven bags and sacks for packing", 2),
    ("Jute Bags", "Traditional jute bags and packaging", 2),

    # Under Marine Products
    ("Freshwater Fish", "Rohu, katla and other freshwater fish", 2),
    ("Shrimp & Prawns", "Vannamei and black tiger shrimp products", 2),

    # Under Textile Raw Materials
    ("Cotton Fiber", "Raw cotton and lint for textile mills", 2),
    ("Jute Fiber", "Raw jute fiber for sacks and textiles", 2),

    # Under Forestry Products
    ("Timber Products", "Processed timber and wood products", 2),
    ("Bamboo Products", "Bamboo poles, sticks and crafted items", 2),

    # Under Construction Materials
    ("Cement Products", "OPC, PPC and specialty cements", 2),
    ("Steel Products", "TMT bars, structural steel and rebar", 2),

    # Under Chemical Products
    ("Agrochemicals", "Pesticides, herbicides and fungicides", 2),
    ("Industrial Chemicals", "Solvents, acids and industrial reagents", 2),

    # Under Fertilizers
    ("Organic Fertilizers", "Vermicompost, bio-fertilizers and organic manure", 2),
    ("Chemical Fertilizers", "NPK, urea, DAP and chemical nutrient blends", 2),

    # Under Pharmaceuticals
    ("OTC Medicines", "Over-the-counter medicines and health products", 2),
    ("Pharma Raw Materials", "API and excipient raw materials for pharma", 2),

    # ── Level 3: Sub-Sub-Categories ─────────────────────────────────────
    # Under Whole Spices
    ("Black Pepper Whole", "Whole black peppercorn for grinding", 3),
    ("Cardamom Whole", "Green and black cardamom pods", 3),

    # Under Edible Oils
    ("Mustard Oil", "Cold-pressed and refined mustard oil", 3),
    ("Soybean Oil", "Refined soybean cooking oil", 3),
    ("Groundnut Oil", "Cold-pressed and filtered groundnut oil", 3),
    ("Sunflower Oil", "Refined sunflower cooking oil", 3),

    # Under Tea Products
    ("CTC Tea", "Crush-tear-curl processed black tea", 3),
    ("Orthodox Tea", "Traditional whole-leaf processed tea", 3),
    ("Green Tea", "Unoxidized tea leaves for health beverages", 3),

    # Under Coffee Products
    ("Arabica Coffee", "Premium Arabica coffee beans and powder", 3),
    ("Robusta Coffee", "Strong Robusta coffee beans and powder", 3),

    # Under Woven Sacks
    ("PP Woven Bags", "Polypropylene woven bags for grain storage", 3),
    ("HDPE Bags", "High-density polyethylene packaging bags", 3),

    # Under Organic Fertilizers
    ("Vermicompost", "Earthworm-processed organic compost", 3),
    ("Bio Fertilizers", "Nitrogen-fixing and phosphate-solubilizing biofertilizers", 3),

    # Under Jaggery Products
    ("Palm Jaggery", "Traditional palm jaggery blocks", 3),
    ("Sugarcane Jaggery", "Cane jaggery and gur products", 3),

    # Under Cotton Fiber
    ("Raw Cotton Bales", "Compressed raw cotton bales for mills", 3),
    ("Cotton Seed", "Cotton seed for oil extraction and feed", 3),

    # Under Freshwater Fish
    ("Rohu Fish", "Freshwater rohu for domestic markets", 3),
    ("Katla Fish", "Freshwater katla for domestic markets", 3),

    # Under Cement Products
    ("OPC Cement", "Ordinary Portland Cement 43 and 53 grade", 3),
    ("PPC Cement", "Pozzolana Portland Cement for general use", 3),

    # Under Chemical Fertilizers
    ("Urea Fertilizer", "Nitrogen-rich urea for crop application", 3),
    ("DAP Fertilizer", "Di-ammonium phosphate for soil nutrition", 3),
    ("NPK Blends", "Balanced NPK fertilizer mixtures", 3),

    # Under Cattle Feed
    ("Dairy Cattle Pellets", "Compressed feed pellets for dairy cattle", 3),
    ("Calf Starter Feed", "Nutritional starter feed for young calves", 3),

    # Under Poultry Feed
    ("Broiler Feed", "High-protein feed for broiler chickens", 3),
    ("Layer Feed", "Calcium-enriched feed for egg-laying hens", 3),
]


def build_item_category_api_payload(item_code: str, item_description: str = "", level: int = 1, status: bool = True) -> dict:
    """
    Build a single API payload for Item Category.

    Args:
        item_code: Category name (e.g., "Beverages") — maps to the "Item Category" UI field
        item_description: Optional description text
        level: Hierarchy level (1=top, 2=sub, 3=sub-sub)
        status: True for Active (default)

    Returns:
        dict: API payload with attribute_name set to "Item Category"
    """
    return {
        "id": "",
        "attribute_name": "Item Category",
        "item_code": item_code,
        "item_description": item_description,
        "level": level,
        "status": status,
    }


def generate_item_category_payloads(count: int = 10, offset: int = 0) -> list:
    """
    Generate N API payloads for Item Category.

    Args:
        count: Number of payloads to generate
        offset: Start index in the data pool (to skip already-used entries)

    Returns:
        list[dict]: List of API payloads ready for batch_create
    """
    pool = ITEM_CATEGORY_API_DATA
    payloads = []

    for i in range(count):
        idx = (offset + i) % len(pool)
        item_code, item_description, level = pool[idx]

        # Handle potential duplicate names when wrapping around
        if (offset + i) >= len(pool):
            wrap_count = (offset + i) // len(pool) + 1
            item_code = f"{item_code} (Batch {wrap_count})"

        payloads.append(
            build_item_category_api_payload(
                item_code=item_code,
                item_description=item_description,
                level=level,
            )
        )

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Item Category is a flat screen — no children, no steppers, no FK dropdowns.
# 4 fields: item_code (required), item_description (required),
#           level (required, number), status (optional, toggle).

FIELD_VALIDATION_RULES = {
    "item_code": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Item Category name. Maps to 'Item Category' UI label. API field key is item_code.",
    },
    "item_description": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Item Category description text.",
    },
    "level": {
        "type": "number",
        "required": True,
        "note": "Hierarchy level: 1=top, 2=sub-category, 3=sub-sub-category. Integer.",
    },
    "status": {
        "type": "toggle",
        "required": False,
        "default": True,
        "note": "Active/Inactive toggle. Default: Active (True).",
    },
}

# Status toggle options (display name -> API boolean value)
STATUS_OPTIONS = {"Active": True, "Inactive": False}

# No FK dropdown pools — Item Category has zero FK fields
DEFAULT_ITEM_CATEGORY_FK_IDS = {}


def get_fk_screen_mapping():
    """Return FK field → screen name mapping. Item Category has no FK dropdowns."""
    return {}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
    config: dict = None,
    **kwargs,
) -> list:
    """Generate a batch of unique Item Category API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules.

    Args:
        count: Number of payloads to generate.
        prefix: Ignored for Item Category (realistic names from data pool are used).
        dropdown_ids: Not used for Item Category (no FK dropdown fields).

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    return generate_item_category_payloads(count=count)
