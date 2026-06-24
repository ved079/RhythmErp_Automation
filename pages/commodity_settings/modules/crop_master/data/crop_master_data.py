"""
Crop Master — Test Data Generators

All data is dynamic (timestamp + random). No hardcoded values.
Crop Master has NO type="character" validation on Name (unlike Designation).
Any text is accepted — letters, digits, special chars, spaces.
This means blank/spaces-only names are BUGS (accepted when they shouldn't be).
"""

import os
import random
import string
import tempfile
import time


# ═══════════════════════════════════════════
#  Bug IDs — referenced by test markers
# ═══════════════════════════════════════════

BUG_CM01 = 'BUG-CM01'  # Blank name accepted on Create
BUG_CM02 = 'BUG-CM02'  # Duplicate name allowed
BUG_CM03 = 'BUG-CM03'  # Leading/trailing spaces not trimmed
BUG_CM04 = 'BUG-CM04'  # No per-field inline errors
BUG_CM05 = 'BUG-CM05'  # No max length validation
BUG_CM06 = 'BUG-CM06'  # Special chars accepted without sanitization
BUG_CM07 = 'BUG-CM07'  # No history entry on creation
BUG_CM08 = 'BUG-CM08'  # History sort doesn't work
BUG_CM09 = 'BUG-CM09'  # Blank name accepted on Edit

ALL_BUGS = [BUG_CM01, BUG_CM02, BUG_CM03, BUG_CM04, BUG_CM05,
            BUG_CM06, BUG_CM07, BUG_CM08, BUG_CM09]

# ═══════════════════════════════════════════
#  Validation Messages
# ═══════════════════════════════════════════

VALIDATION_FAILED_TITLE = 'Validation Failed'
VALIDATION_FAILED_CONTENT = 'Please correct the highlighted fields'
SUCCESS_CREATE_MSG = 'Your record has been added successfully!'
SUCCESS_UPDATE_MSG = 'Your record has been updated successfully!'


# ═══════════════════════════════════════════
#  Name Generators
# ═══════════════════════════════════════════

def generate_crop_name(prefix="AutoCrop"):
    """Generate a unique crop name with timestamp + random suffix."""
    suffix = ''.join(random.choices(string.ascii_uppercase, k=6))
    return f"{prefix} {suffix}"


def generate_description(prefix="Test Description"):
    """Generate a description string with timestamp."""
    timestamp = int(time.time())
    return f"{prefix} {timestamp}"


# ═══════════════════════════════════════════
#  Valid Data Generators
# ═══════════════════════════════════════════

def generate_valid_crop_data():
    """Generate a complete valid data dict for creating a crop.
    Name: valid alphabetic with random suffix.
    Description: optional text.
    Status: 'Active' (default).
    File: None (optional).
    """
    return {
        'name': generate_crop_name(),
        'description': generate_description(),
        'status': 'Active',
        'file_path': None,
    }


def generate_valid_edit_data():
    """Generate valid data for editing an existing crop."""
    return {
        'name': generate_crop_name(prefix="EditCrop"),
        'description': generate_description(prefix="Updated Desc"),
        'status': 'Inactive',
        'file_path': None,
    }


def generate_name_only_data():
    """Generate data with only Name filled.
    Should succeed — Description is optional, Status defaults to Active.
    """
    return {
        'name': generate_crop_name(prefix="NameOnly"),
        'description': '',
        'status': 'Active',
        'file_path': None,
    }


# ═══════════════════════════════════════════
#  Invalid / Boundary Data Generators
# ═══════════════════════════════════════════

def generate_empty_data():
    """Generate empty data dict — all fields blank.
    Should trigger 'Validation Failed' SweetAlert2 for required Name.
    """
    return {
        'name': '',
        'description': '',
        'status': 'Active',
        'file_path': None,
    }


def generate_spaces_only_name():
    """Generate spaces-only name.
    BUG-CM01: Should be rejected but is accepted.
    """
    return "     "


def generate_name_with_spaces():
    """Generate name with leading/trailing spaces.
    BUG-CM03: Spaces should be trimmed but aren't.
    """
    name = generate_crop_name(prefix="SpaceCrop")
    return f"  {name}  "


def generate_duplicate_name_data():
    """Generate data with a name that already exists.
    BUG-CM02: No duplicate name validation.
    Uses a name that was just created by passing in the existing name.
    """
    return {
        'name': '',  # Will be set by test to an existing name
        'description': 'Duplicate name test',
        'status': 'Active',
        'file_path': None,
    }


def generate_special_char_name():
    """Generate name with special characters.
    BUG-CM06: Special chars accepted without sanitization.
    """
    special_names = [
        'Test!@#$%^&*()',
        'Crop<Script>',
        'Name&Company',
        'Test|Pipe',
        'Crop"Quote"',
    ]
    return random.choice(special_names)


def generate_long_name(length=300):
    """Generate very long name (300 chars).
    BUG-CM05: No max length validation.
    """
    base = "LongCropName"
    repeats = length // len(base)
    remainder = length % len(base)
    return (base * repeats) + base[:remainder]


# ═══════════════════════════════════════════
#  File Generators (temp files for upload)
# ═══════════════════════════════════════════

def generate_test_file(extension='png'):
    """Generate a temp test file for upload.
    extension: 'png', 'jpg', or 'pdf'
    Returns absolute path to the temp file.
    """
    suffix_map = {
        'png': '.png',
        'jpg': '.jpg',
        'jpeg': '.jpg',
        'pdf': '.pdf',
    }
    suffix = suffix_map.get(extension.lower(), f'.{extension}')

    if extension.lower() == 'pdf':
        content = b'%PDF-1.4 test file content'
    else:
        # Minimal valid image header bytes
        content = b'\x89PNG\r\n\x1a\n' + b'test image data ' + str(random.randint(1000, 9999)).encode()

    fd, path = tempfile.mkstemp(suffix=suffix, prefix='crop_test_')
    with os.fdopen(fd, 'wb') as f:
        f.write(content)

    return path


def generate_invalid_test_file():
    """Generate a .txt file (invalid type for upload).
    Browser accept attribute should silently reject it.
    """
    fd, path = tempfile.mkstemp(suffix='.txt', prefix='crop_invalid_')
    with os.fdopen(fd, 'w') as f:
        f.write('This is a text file, not an image or PDF')
    return path


def cleanup_temp_file(path):
    """Remove a temp file if it exists."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#  API Batch Create — Data Pool + Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Screen structure (discovered 2026-06-02):
#   Crop Master: name* (text, required, unique), description (text, optional),
#                attachment (file, optional), status (toggle, default: true)
#   FLAT screen — no steppers, no children, no FK fields.
#
# Existing entries in ERP (as of 2026-06-02, 161 total):
#   Wheat, Rice (Paddy), Maize (Corn), Barley, Jowar (Sorghum),
#   Bajra (Pearl Millet), Ragi (Finger Millet), Chana (Gram),
#   Toor (Arhar), Soyabean, Chilli, Coriander, Cotton, Tomato,
#   Mango, Pomegranate, Tea, Rubber, plus many AutoCrop test entries.
#
# This data pool provides additional crop names NOT already in the system.
# ═══════════════════════════════════════════════════════════════════════════════

# Each entry is a tuple: (name, description, status)
# status: True = Active, False = Inactive

CROP_MASTER_API_DATA = [
    # ── Cereals & Millets ────────────────────────────────────────────────
    ("Foxtail Millet", "Thinai — drought-resistant small millet grown in dryland areas", True),
    ("Proso Millet", "Panivaragu — short-season millet suitable for marginal soils", True),
    ("Kodo Millet", "Varagu — hardy millet with high fiber and antioxidant content", True),
    ("Little Millet", "Samai — small-grained millet ideal for organic farming", True),
    ("Barnyard Millet", "Kuthiraivali — low-glycemic millet for diabetic diets", True),
    ("Brown Top Millet", "Korle — rare millet gaining popularity for health benefits", True),
    ("Triticale", "Wheat-rye hybrid grain for fodder and food production", True),
    ("Oats", "Avena sativa — cool-season cereal for human consumption and fodder", True),
    ("Quinoa", "Chenopodium quinoa — protein-rich pseudocereal adapted to high altitudes", True),
    ("Buckwheat", "Kuttu — pseudocereal used in fasting foods and gluten-free products", True),

    # ── Pulses & Legumes ─────────────────────────────────────────────────
    ("Moong Dal", "Green gram — short-duration pulse with high protein content", True),
    ("Urad Dal", "Black gram — important pulse for dal and idli-dosa batter", True),
    ("Masoor Dal", "Red lentil — quick-cooking pulse popular in Indian cuisine", True),
    ("Moth Bean", "Matki — drought-tolerant pulse grown in arid regions", True),
    ("Horse Gram", "Kulthi — hardy legume with high iron and calcium content", True),
    ("Lobia", "Cowpea — versatile pulse for both grain and vegetable use", True),
    ("Rajma", "Kidney bean — protein-rich pulse popular in North Indian cuisine", True),
    ("Field Pea", "Matar — cool-season pulse for grain and vegetable production", True),
    ("Pigeon Pea Split", "Toor Dal — split pigeon pea for daily cooking", True),
    ("Chickpea Desi", "Kala Chana — small dark chickpea for traditional preparations", True),

    # ── Oilseeds ─────────────────────────────────────────────────────────
    ("Groundnut", "Peanut — oilseed and food crop rich in healthy fats", True),
    ("Sunflower", "Surajmukhi — oilseed crop with high oil content and ornamental value", True),
    ("Safflower", "Kusum — drought-tolerant oilseed for edible oil and dye", True),
    ("Sesame", "Til — ancient oilseed used in cooking and traditional sweets", True),
    ("Linseed", "Alsi — flaxseed for oil extraction and industrial use", True),
    ("Castor", "Arandi — industrial oilseed for lubricant and biodiesel production", True),
    ("Niger Seed", "Ramtil — oilseed grown in tribal and hilly areas", True),
    ("Coconut", "Nariyal — versatile plantation crop for oil, copra, and tender coconut", True),

    # ── Spices & Condiments ──────────────────────────────────────────────
    ("Turmeric", "Haldi — anti-inflammatory spice and natural food colorant", True),
    ("Black Pepper", "Kali Mirch — king of spices from Western Ghats", True),
    ("Cardamom", "Elaichi — aromatic spice used in sweets and beverages", True),
    ("Cumin", "Jeera — essential spice in Indian and global cuisine", True),
    ("Fenugreek", "Methi — dual-purpose spice and leafy vegetable", True),
    ("Mustard", "Sarson — oilseed and spice crop for tempering and oil", True),
    ("Nutmeg", "Jaiphal — tree spice from Malabar region for flavoring", True),
    ("Clove", "Laung — dried flower bud used as spice and in dentistry", True),
    ("Cinnamon", "Dalchini — bark spice used in both sweet and savory dishes", True),
    ("Star Anise", "Chakri Phool — star-shaped spice for biryani and Chinese cuisine", True),

    # ── Vegetables ───────────────────────────────────────────────────────
    ("Onion", "Pyaz — essential vegetable crop for Indian cooking", True),
    ("Potato", "Aloo — staple tuber crop grown across all seasons", True),
    ("Brinjal", "Baingan — versatile vegetable grown in varied climates", True),
    ("Cauliflower", "Gobhi — cool-season vegetable for fresh market and processing", True),
    ("Cabbage", "Patta Gobhi — leafy vegetable for fresh and fermented products", True),
    ("Okra", "Bhindi — warm-season vegetable with high export potential", True),
    ("Bitter Gourd", "Karela — medicinal vegetable for blood sugar management", True),
    ("Bottle Gourd", "Lauki — mild-flavored gourd for curries and sweets", True),
    ("Ridge Gourd", "Turai — sponge gourd for light curries and chutneys", True),
    ("Drumstick", "Moringa — nutrient-dense pods and leaves for food and health", True),

    # ── Fruits ───────────────────────────────────────────────────────────
    ("Banana", "Kela — major fruit crop with year-round production", True),
    ("Guava", "Amrud — vitamin C-rich fruit for fresh and processing markets", True),
    ("Papaya", "Papita — tropical fruit for fresh, papain extraction, and cooking", True),
    ("Litchi", "Lychee — premium seasonal fruit from eastern India", True),
    ("Grape", "Angoor — fruit crop for table, raisin, and wine production", True),
    ("Orange", "Santra — citrus fruit major in Nagpur and Coorg regions", True),
    ("Sweet Lime", "Mosambi — sweet citrus for juice and fresh consumption", True),
    ("Pineapple", "Ananas — tropical fruit for fresh, canning, and juice", True),
    ("Watermelon", "Tarbooz — summer fruit crop with high water content", True),
    ("Sapota", "Chiku — tropical fruit for fresh market and milkshakes", True),

    # ── Fiber Crops ──────────────────────────────────────────────────────
    ("Jute", "Pat — natural fiber crop for sacks, mats, and geotextiles", True),
    ("Mesta", "Kenaf — fiber crop similar to jute for rope and paper", True),
    ("Ramie", "China Grass — strong natural fiber for textiles and composites", True),
    ("Sunn Hemp", "San — green manure and fiber crop for soil improvement", True),

    # ── Plantation & Cash Crops ──────────────────────────────────────────
    ("Coffee", "Robusta and Arabica — major plantation crop in Western Ghats", True),
    ("Arecanut", "Supari — betel nut palm for traditional chewing and pharmaceuticals", True),
    ("Cocoa", "Chocolate tree — tropical crop for chocolate and butter production", True),
    ("Vanilla", "Vanilla planifolia — high-value spice for flavoring industry", True),
    ("Cashew", "Kaju — nut crop for premium kernels and CNSL extraction", True),

    # ── Fodder & Forage ──────────────────────────────────────────────────
    ("Sorghum Fodder", "Chari — multi-cut fodder sorghum for dairy feed", True),
    ("Berseem", "Egyptian Clover — winter fodder legume for dairy animals", True),
    ("Lucerne", "Alfalfa — perennial fodder crop with high protein content", True),
    ("Napier Grass", "Elephant Grass — high-yielding perennial fodder for silage", True),
    ("Oat Fodder", "Fodder Oats — cool-season fodder for ruminant feed", True),

    # ── Medicinal & Aromatic Plants ──────────────────────────────────────
    ("Ashwagandha", "Indian Ginseng — adaptogenic herb for stress relief", True),
    ("Aloe Vera", "Ghritkumari — succulent for cosmetics, pharma, and food", True),
    ("Lemongrass", "Cymbopogon — aromatic grass for essential oil and tea", True),
    ("Palmarosa", "Rosha Grass — aromatic grass for geraniol extraction", True),
    ("Vetiver", "Khus — fragrant grass for oil, erosion control, and cooling", True),
    ("Stevia", "Meethi Tulsi — natural sweetener herb for sugar-free products", True),
    ("Sarpagandha", "Rauwolfia — medicinal plant for hypertension treatment", True),
    ("Isabgol", "Psyllium — laxative seed husk crop for pharmaceutical use", True),
]


def build_crop_master_api_payload(name: str, description: str = "", status: bool = True) -> dict:
    """
    Build a single API payload for Crop Master.

    Args:
        name: Crop name (e.g., "Foxtail Millet")
        description: Optional description text
        status: True for Active, False for Inactive

    Returns:
        dict: API payload with attribute_name set to "Crop Master"
    """
    return {
        "id": "",
        "attribute_name": "Crop Master",
        "name": name,
        "description": description,
        "status": status,
    }


def generate_crop_master_payloads(count: int = 10, offset: int = 0) -> list:
    """
    Generate N API payloads for Crop Master.

    Args:
        count: Number of payloads to generate
        offset: Start index in the data pool (to skip already-used entries)

    Returns:
        list[dict]: List of API payloads ready for batch_create
    """
    pool = CROP_MASTER_API_DATA
    payloads = []

    for i in range(count):
        idx = (offset + i) % len(pool)
        name, description, status = pool[idx]

        # Handle potential duplicate names when wrapping around
        if (offset + i) >= len(pool):
            wrap_count = (offset + i) // len(pool) + 1
            name = f"{name} (Batch {wrap_count})"

        payloads.append(
            build_crop_master_api_payload(name=name, description=description, status=status)
        )

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
FIELD_VALIDATION_RULES = {
    "name": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Crop name. Must be unique (BUG-CM02: duplicates currently allowed).",
    },
    "description": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "Optional description of the crop.",
    },
    "status": {
        "type": "toggle",
        "required": False,
        "default": True,
        "note": "Active/Inactive toggle. Default: Active (True).",
    },
}

STATUS_OPTIONS = {"Active": True, "Inactive": False}

DEFAULT_CROP_MASTER_FK_IDS = {}  # No FK dropdowns


def get_fk_screen_mapping():
    """Return FK field → screen name mapping. Crop Master has no FK dropdowns."""
    return {}


def generate_batch_payloads(count=20, prefix=None, dropdown_ids=None):
    return generate_crop_master_payloads(count=count)
