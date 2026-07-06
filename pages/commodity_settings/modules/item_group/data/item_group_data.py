"""
Item Group — Test Data Generators

All data is dynamic (timestamp + random). No hardcoded values.
Item Group has 2 fields: Item Group code (required), Description (required).
No status toggle, no file upload, no dropdowns.
"""

import random
import string


# ═══════════════════════════════════════════
#  Bug IDs — referenced by test markers
# ═══════════════════════════════════════════

BUG_IG01 = 'BUG-IG01'  # Duplicate code allowed
BUG_IG02 = 'BUG-IG02'  # Spaces-only code accepted
BUG_IG03 = 'BUG-IG03'  # Leading/trailing spaces not trimmed
BUG_IG04 = 'BUG-IG04'  # No per-field inline errors
BUG_IG05 = 'BUG-IG05'  # Special chars accepted without sanitization
BUG_IG06 = 'BUG-IG06'  # No max length validation (255+)
BUG_IG07 = 'BUG-IG07'  # No history entry on creation
BUG_IG08 = 'BUG-IG08'  # History sort doesn't work
BUG_IG09 = 'BUG-IG09'  # Spaces-only description accepted when it shouldn't be

ALL_BUGS = [BUG_IG01, BUG_IG02, BUG_IG03, BUG_IG04, BUG_IG05,
            BUG_IG06, BUG_IG07, BUG_IG08, BUG_IG09]

# ═══════════════════════════════════════════
#  Code/Description Generators
# ═══════════════════════════════════════════

def generate_ig_code(prefix="AutoIG"):
    """Generate a unique Item Group code with random suffix."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{suffix}"


def generate_ig_description(prefix="Auto Desc"):
    """Generate a description string with random suffix."""
    import time
    timestamp = int(time.time()) % 100000
    suffix = ''.join(random.choices(string.ascii_uppercase, k=4))
    return f"{prefix} {timestamp}{suffix}"


# ═══════════════════════════════════════════
#  Valid Data Generators
# ═══════════════════════════════════════════

def generate_valid_ig_data(code_prefix="AutoIG", desc_prefix="Auto Desc"):
    """Generate a complete valid data dict for creating an item group.
    Both Code and Description are required fields."""
    return {
        'code': generate_ig_code(code_prefix),
        'description': generate_ig_description(desc_prefix),
    }


def generate_valid_edit_data(code_prefix="EditIG", desc_prefix="Edit Desc"):
    """Generate valid data for editing an existing item group."""
    return {
        'code': generate_ig_code(code_prefix),
        'description': generate_ig_description(desc_prefix),
    }


def generate_code_only_data():
    """Generate data with only Code filled, Description empty.
    Should FAIL — Description is required."""
    return {
        'code': generate_ig_code("CodeOnly"),
        'description': '',
    }


def generate_description_only_data():
    """Generate data with only Description filled, Code empty.
    Should FAIL — Code is required."""
    return {
        'code': '',
        'description': generate_ig_description("DescOnly"),
    }


# ═══════════════════════════════════════════
#  Invalid / Boundary Data Generators
# ═══════════════════════════════════════════

def generate_empty_data():
    """Generate empty data dict — all fields blank.
    Should trigger 'Validation Failed' SweetAlert2."""
    return {
        'code': '',
        'description': '',
    }


def generate_spaces_only_code():
    """Generate spaces-only code. BUG-IG02: Should be rejected but is accepted."""
    return "     "


def generate_spaces_only_description():
    """Generate spaces-only description. May be rejected or accepted."""
    return "     "


def generate_code_with_spaces():
    """Generate code with leading/trailing spaces. BUG-IG03."""
    code = generate_ig_code(prefix="SpaceIG")
    return f"  {code}  "


def generate_duplicate_code_data(existing_code):
    """Generate data with an existing code. BUG-IG01: Duplicates are allowed."""
    return {
        'code': existing_code,
        'description': generate_ig_description("DupCode"),
    }


def generate_special_char_code():
    """Generate code with special characters. BUG-IG05."""
    special_names = [
        'Test!@#$%^&*()',
        'IG<Script>',
        'Code&Company',
        'Test|Pipe',
        'IG"Quote"',
    ]
    return random.choice(special_names)


def generate_special_char_description():
    """Generate description with special characters."""
    return 'Test!@#$%^&*()_+-={}[]|:;<>,.?/'


def generate_long_code(length=300):
    """Generate very long code (300 chars). BUG-IG06: No max length validation."""
    base = "LongIGCode"
    repeats = length // len(base)
    remainder = length % len(base)
    return (base * repeats) + base[:remainder]


# ═══════════════════════════════════════════════════════════════════════════════
#  API Batch Create — Data Pool + Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════

ITEM_GROUP_API_DATA = [
    ("Beverages", "Tea, coffee, juices and drink products"),
    ("Sugar & Sweeteners", "Sugar, jaggery, honey and sweetener products"),
    ("Animal Feed", "Cattle feed, poultry feed and fodder products"),
    ("Forestry Products", "Timber, bamboo and forest produce"),
    ("Marine Products", "Fish, shrimp and seafood products"),
    ("Pharmaceuticals", "OTC medicines and pharmaceutical raw materials"),
    ("Packaging Materials", "Woven sacks, HDPE bags and packaging supplies"),
    ("Automotive Parts", "Spare parts and automotive components"),
    ("Seeds & Planting Material", "Agricultural seeds and planting stock"),
    ("Fiber & Textile Products", "Cotton, jute and textile raw materials"),
    ("Coarse Cereals", "Maize, millet, barley and other coarse grains"),
    ("Paddy Rice", "Paddy, rice and rice by-products"),
    ("Gram Varieties", "Chickpeas, Bengal gram and gram variants"),
    ("Lentil Varieties", "Red lentils, yellow lentils and pulse varieties"),
    ("Whole Spices", "Black pepper, cardamom, cinnamon and whole spices"),
    ("Ground Spices", "Turmeric powder, chili powder and ground masalas"),
    ("Dry Fruits & Nuts", "Almonds, cashews, raisins and dry fruit products"),
    ("Edible Oils", "Mustard oil, soybean oil and cooking oils"),
    ("Oilseed Cakes", "Mustard cake, groundnut cake and oilseed meals"),
    ("Raw Sugar", "Raw sugar, brown sugar and molasses"),
]


def build_item_group_api_payload(code: str, description: str = "") -> dict:
    """Build a single API payload for Item Group."""
    return {
        "id": "",
        "attribute_name": "Item Group",
        "code": code,
        "description": description,
    }


def generate_item_group_payloads(count: int = 10, offset: int = 0) -> list:
    """Generate N API payloads for Item Group."""
    pool = ITEM_GROUP_API_DATA
    payloads = []
    for i in range(count):
        idx = (offset + i) % len(pool)
        code, description = pool[idx]
        if (offset + i) >= len(pool):
            wrap_count = (offset + i) // len(pool) + 1
            code = f"{code} (Batch {wrap_count})"
        payloads.append(build_item_group_api_payload(code=code, description=description))
    return payloads


def get_fk_screen_mapping():
    """Return FK field → screen name mapping. Item Group has no FK dropdowns."""
    return {}


def generate_batch_payloads(count=20, prefix=None, dropdown_ids=None):
    return generate_item_group_payloads(count=count)
