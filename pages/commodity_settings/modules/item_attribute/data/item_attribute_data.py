"""
Item Attribute — API Payload Generators

Item Attribute has 2-4 fields depending on attr_num:
  IA1: Name (required), Base UOM (required FK → UOM), Description (optional), Status (toggle)
  IA2-5: Name (required), Description (optional), Status (toggle)

Resolve base_uom FK IDs via FkResolver before calling generators.
No hardcoded FK IDs in production — only MOCK_FK_IDS for tests.
"""

import random
import string
import time


# ═══════════════════════════════════════════
#  Bug IDs — referenced by test markers
# ═══════════════════════════════════════════

BUG_IA01 = 'BUG-IA01'
BUG_IA02 = 'BUG-IA02'
BUG_IA03 = 'BUG-IA03'
BUG_IA04 = 'BUG-IA04'
BUG_IA05 = 'BUG-IA05'
BUG_IA06 = 'BUG-IA06'
BUG_IA07 = 'BUG-IA07'
BUG_IA08 = 'BUG-IA08'

ALL_BUGS = [BUG_IA01, BUG_IA02, BUG_IA03, BUG_IA04, BUG_IA05,
            BUG_IA06, BUG_IA07, BUG_IA08]

# ═══════════════════════════════════════════
#  Attribute Pools
# ═══════════════════════════════════════════

ATTRIBUTE_POOLS = {
    1: ["Item Attribute1", "Primary attribute with Base UOM"],
    2: ["Item Attribute2", "Secondary attribute (no UOM)"],
    3: ["Item Attribute3", "Tertiary attribute (no UOM)"],
    4: ["Item Attribute4", "Quaternary attribute (no UOM)"],
    5: ["Item Attribute5", "Quinary attribute (no UOM)"],
}

# ═══════════════════════════════════════════
#  Mock FK IDs — for tests only
# ═══════════════════════════════════════════

MOCK_FK_IDS = {
    "base_uom": {"NOS": 1, "KGS": 2, "QTL": 3, "MTR": 4, "LTR": 5, "PCS": 6},
}

# ═══════════════════════════════════════════
#  Payload builders
# ═══════════════════════════════════════════

def build_item_attribute_payload(attr_number, name, description="", base_uom_id=None, status=True):
    """
    Build a single API payload for Item Attribute.

    Args:
        attr_number: 1-5
        name: Attribute name (required)
        description: Optional description
        base_uom_id: FK ID for base_uom (required for IA1)
        status: Boolean toggle

    Returns:
        dict: API payload
    """
    payload = {
        "id": "",
        "attribute_name": f"Item Attribute{attr_number}",
        "name": name,
        "description": description or "",
        "status": status,
    }
    if attr_number == 1:
        payload["base_uom"] = base_uom_id
    return payload


def generate_item_attribute_payloads(count=10, offset=0, attr_number=1, fk_ids=None):
    """
    Generate N API payloads for a specific Item Attribute screen.

    Args:
        count: Number of payloads to generate
        offset: Start index in data pool
        attr_number: Attribute number (1-5). IA1 requires fk_ids["base_uom"]
        fk_ids: Dict with resolved FK IDs, e.g. {"base_uom": {name: id, ...}}

    Returns:
        list[dict]: List of API payloads
    """
    if attr_number == 1:
        if not fk_ids:
            raise ValueError(
                "fk_ids is required for Item Attribute1. "
                "Resolve base_uom FK IDs via FkResolver first."
            )
        uom_ids = fk_ids.get("base_uom", {})
        uom_values = list(uom_ids.values()) if uom_ids else []
        if not uom_values:
            raise ValueError("fk_ids['base_uom'] is empty. Resolve UOM IDs via FkResolver first.")
    else:
        uom_values = []

    payloads = []
    for i in range(count):
        idx = offset + i
        uom_id = uom_values[idx % len(uom_values)] if uom_values else None
        payloads.append(build_item_attribute_payload(
            attr_number=attr_number,
            name=generate_ia_name(attr_number),
            description=generate_ia_description(),
            base_uom_id=uom_id,
            status=True,
        ))
    return payloads


def generate_all_attribute_payloads(count=3, fk_ids=None):
    """
    Generate payloads for all 5 Item Attribute screens.

    Returns:
        dict: {attr_num: [payloads, ...], ...}
    """
    return {
        n: generate_item_attribute_payloads(count=count, attr_number=n, fk_ids=fk_ids)
        for n in range(1, 6)
    }


# ═══════════════════════════════════════════
#  FK Screen Mapping
# ═══════════════════════════════════════════

def get_fk_screen_mapping():
    """Return FK field → screen name mapping for live FkResolver resolution."""
    return {
        "base_uom": "UOM",
    }


# ═══════════════════════════════════════════
#  Batch Payload Generator (with dedup)
# ═══════════════════════════════════════════

def generate_batch_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None, offset: int = 0, existing_entries: list = None, attr_number: int = 1) -> list:
    """Generate a batch of unique Item Attribute API payloads.

    Args:
        dropdown_ids: Must contain resolved FK IDs (base_uom) for IA1.
                      Resolve via FkResolver before calling.
        attr_number: Attribute screen number (1-5). Defaults to 1.
    """
    if attr_number == 1 and not dropdown_ids:
        raise ValueError("dropdown_ids is required for Item Attribute1. Resolve FK IDs via FkResolver first.")

    fk_ids = dropdown_ids or {}
    if existing_entries:
        used_names = {e.get("name", "").lower().strip() for e in existing_entries if e}
        uom_ids = fk_ids.get("base_uom", {})
        uom_values = list(uom_ids.values()) if uom_ids else []
        unique_payloads = []
        pool_idx = 0
        while len(unique_payloads) < count:
            name = generate_ia_name(attr_number)
            if name.lower().strip() not in used_names:
                used_names.add(name.lower().strip())
                uom_id = uom_values[(offset + pool_idx) % len(uom_values)] if uom_values else None
                unique_payloads.append(build_item_attribute_payload(
                    attr_number=attr_number,
                    name=name,
                    description=generate_ia_description(),
                    base_uom_id=uom_id,
                    status=True,
                ))
            pool_idx += 1
        return unique_payloads
    return generate_item_attribute_payloads(count=count, offset=offset, attr_number=attr_number, fk_ids=fk_ids)


# ═══════════════════════════════════════════
#  Name/Description Generators
# ═══════════════════════════════════════════

_IA1_CROPS = [
    "Basmati 1121 Rice", "Basmati 1509 Rice", "Sona Masoori Rice", "IR-64 Rice",
    "PR-106 Rice", "Pusa Basmati Rice", "Swarna Rice", "MTU-7029 Rice",
    "BPT-5204 Rice", "Sarjoo-52 Rice", "Dubraj Rice", "Indrayani Rice",
    "Kolam Rice", "HMT Rice", "Minikit Rice",
    "Sharbati Wheat", "Lok-1 Wheat", "GW-322 Wheat", "HD-2967 Wheat",
    "PBW-343 Wheat", "K-307 Wheat", "NW-1014 Wheat", "HI-8498 Wheat",
    "MP-3173 Wheat", "GW-496 Wheat",
    "Chana Dal", "Tur Dal", "Moong Dal", "Urad Dal", "Masoor Dal",
    "Rajma", "Chawli", "Vatana", "Kulthi Dal", "Moth Dal",
    "Soybean", "Groundnut Bold", "Groundnut Java", "Sunflower Seed",
    "Mustard Seed", "Sesame Seed", "Linseed", "Castor Seed",
    "Safflower Seed", "Niger Seed",
    "Shankar-6 Cotton", "H-4 Cotton", "MCU-5 Cotton", "DCH-32 Cotton",
    "Bunny BT Cotton",
    "Jowar", "Bajra", "Maize", "Ragi", "Kodo Millet", "Foxtail Millet",
    "Turmeric Finger", "Red Chilli Teja", "Coriander Seed", "Cumin Seed",
    "Fenugreek Seed", "Ginger Dry", "Garlic", "Onion Dry",
    "Sugarcane", "Potato", "Tomato", "Banana Robusta", "Mango Alphonso",
]

_IA1_QUALIFIERS = [
    "FAQ Grade", "Premium Grade", "Grade A", "Grade B", "Grade C",
    "Export Quality", "Sortex Quality", "Bold Grade", "Medium Grade", "Small Grade",
    "Sun Dried", "Machine Dried", "Raw", "Processed", "Milled",
    "Certified Seed", "Foundation Seed", "Hybrid Seed", "OPV",
    "Kharif Lot", "Rabi Lot",
]

_IA25_TERMS = [
    "Parboiled", "Polished", "Milled", "Sortex", "Graded", "Cleaned",
    "Sieved", "Husked", "Dehusked", "Bleached", "Roasted", "Puffed",
    "Flaked", "Powdered", "Crushed", "Dried", "Fermented", "Sprouted",
    "Steamed", "Pressed", "Refined", "Extracted", "Filtered", "Decorticated",
    "Bold", "Fine", "Medium", "Small", "Large", "Extra", "Super",
    "Regular", "Special", "Desi", "Hybrid", "Organic", "Raw", "Premium",
    "Standard", "FAQ", "Certified", "Export", "Local", "Commercial",
    "Bold Grade", "Fine Meal", "Raw Paddy", "Sun Dried", "Hand Picked",
    "Machine Cleaned", "Double Sortex", "Triple Cleaned", "Steam Processed", "Cold Pressed",
    "Light Weight", "Heavy Weight", "Short Grain", "Long Grain", "Medium Grain",
    "Thin Flake", "Thick Flake", "Coarse Ground", "Fine Ground", "Extra Bold",
    "New Crop", "Old Stock", "Kharif Crop", "Rabi Crop", "Mixed Lot",
    "Dry Milled", "Wet Milled", "Air Cleaned", "Screen Cleaned", "Gravity Sorted",
]

_ia_name_counter = 0
_ia_rng = random.Random(int(time.time()))


def generate_ia_name(attr_num=1):
    """Generate a unique realistic Item Attribute name."""
    global _ia_name_counter
    _ia_name_counter += 1
    if attr_num == 1:
        crop      = _ia_rng.choice(_IA1_CROPS)
        qualifier = _ia_rng.choice(_IA1_QUALIFIERS)
        return f"{crop} - {qualifier} {_ia_name_counter}"
    else:
        term = _ia_rng.choice(_IA25_TERMS)
        return f"{term} {_ia_name_counter}"


# kept for backwards-compat with any code that imports REAL_ATTRIBUTE_NAMES
REAL_ATTRIBUTE_NAMES = {n: _IA1_CROPS if n == 1 else _IA25_TERMS for n in range(1, 6)}


def generate_ia_description(prefix="Auto Desc"):
    """Generate a description string with random suffix."""
    timestamp = int(time.time()) % 100000
    suffix = ''.join(random.choices(string.ascii_uppercase, k=4))
    return f"{prefix} {timestamp}{suffix}"


# ═══════════════════════════════════════════
#  Valid Data Generators
# ═══════════════════════════════════════════

def generate_valid_ia_data(attr_num=1, name_prefix="AutoIA", desc_prefix="Auto Desc"):
    """Generate a complete valid data dict for creating an item attribute.
    Name is required. Base UOM is required for IA1. Description is optional.
    Status defaults to Active."""
    data = {
        'name': generate_ia_name(attr_num),
        'description': generate_ia_description(desc_prefix),
    }
    # IA1 needs Base UOM — pass empty string to trigger random selection
    if attr_num == 1:
        data['base_uom'] = ''
    return data


def generate_valid_edit_data(attr_num=1, name_prefix="EditIA", desc_prefix="Edit Desc"):
    """Generate valid data for editing an existing item attribute.
    Only Name and Description are editable (Base UOM change is also possible on IA1)."""
    data = {
        'name': generate_ia_name(attr_num),
        'description': generate_ia_description(desc_prefix),
    }
    if attr_num == 1:
        data['base_uom'] = ''  # Random new UOM
    return data


def generate_name_only_data(attr_num=1):
    """Generate data with only Name filled. Description omitted.
    Should PASS — Description is optional."""
    data = {
        'name': generate_ia_name("NameOnly", attr_num),
        'description': None,
    }
    if attr_num == 1:
        data['base_uom'] = ''
    return data


def generate_description_only_data():
    """Generate data with only Description filled, Name empty.
    Should FAIL — Name is required."""
    return {
        'name': '',
        'description': generate_ia_description("DescOnly"),
    }


# ═══════════════════════════════════════════
#  Invalid / Boundary Data Generators
# ═══════════════════════════════════════════

def generate_empty_data():
    """Generate empty data dict — all fields blank.
    Should trigger 'Validation Failed' SweetAlert2."""
    return {
        'name': '',
        'description': '',
    }


def generate_spaces_only_name():
    """Generate spaces-only name. BUG-IA06: Should be rejected but is accepted."""
    return "     "


def generate_spaces_only_description():
    """Generate spaces-only description. May be rejected or accepted."""
    return "     "


def generate_name_with_spaces(attr_num=1):
    """Generate name with leading/trailing spaces. BUG-IA06 variant."""
    name = generate_ia_name(attr_num)
    return f"  {name}  "


def generate_duplicate_name_data(existing_name, attr_num=1):
    """Generate data with an existing name. BUG-IA01: Duplicates are allowed."""
    data = {
        'name': existing_name,
        'description': generate_ia_description("DupName"),
    }
    if attr_num == 1:
        data['base_uom'] = ''
    return data


def generate_special_char_name():
    """Generate name with special characters. BUG-IA07."""
    special_names = [
        'Test!@#$%^&*()',
        'IA<Script>',
        'Attr&Company',
        'Test|Pipe',
        'IA"Quote"',
    ]
    return random.choice(special_names)


def generate_special_char_description():
    """Generate description with special characters."""
    return 'Test!@#$%^&*()_+-={}[]|:;<>,.?/'


def generate_long_name(length=300):
    """Generate very long name (300 chars). BUG-IA04: No max length validation."""
    base = "LongIAName"
    repeats = length // len(base)
    remainder = length % len(base)
    return (base * repeats) + base[:remainder]



