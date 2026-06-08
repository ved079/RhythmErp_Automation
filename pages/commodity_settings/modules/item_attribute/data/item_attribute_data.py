"""
Item Attribute — Test Data Generators

All data is dynamic (timestamp + random). No hardcoded values.
Item Attribute has 2-4 fields depending on attr_num:
  IA1: Name (required), Base UOM (required dropdown), Description (optional), Status (toggle)
  IA2-5: Name (required), Description (optional), Status (toggle)
No file upload.
"""

import random
import string
import time


# ═══════════════════════════════════════════
#  Bug IDs — referenced by test markers
# ═══════════════════════════════════════════

BUG_IA01 = 'BUG-IA01'  # Duplicate Name allowed
BUG_IA02 = 'BUG-IA02'  # mat-select browser click doesn't register in Angular form
BUG_IA03 = 'BUG-IA03'  # History popup "No data available" for existing records
BUG_IA04 = 'BUG-IA04'  # No maxlength on Name/Description — server rejects 256+ with generic error
BUG_IA05 = 'BUG-IA05'  # Generic "Failed to save record" instead of specific field error
BUG_IA06 = 'BUG-IA06'  # Spaces-only Name accepted (should validate)
BUG_IA07 = 'BUG-IA07'  # Special chars in Name accepted (should sanitize)
BUG_IA08 = 'BUG-IA08'  # No history entry on creation

ALL_BUGS = [BUG_IA01, BUG_IA02, BUG_IA03, BUG_IA04, BUG_IA05,
            BUG_IA06, BUG_IA07, BUG_IA08]

# ═══════════════════════════════════════════
#  Validation Messages
# ═══════════════════════════════════════════

VALIDATION_FAILED_TITLE = 'Validation Failed'
VALIDATION_FAILED_CONTENT = 'Please correct the highlighted fields'
SUCCESS_CREATE_MSG = 'Your record has been added successfully!'
SUCCESS_UPDATE_MSG = 'Your record has been updated successfully!'


# ═══════════════════════════════════════════
#  Name/Description Generators
# ═══════════════════════════════════════════

def generate_ia_name(prefix="AutoIA", attr_num=1):
    """Generate a unique Item Attribute name with random suffix."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{attr_num}{suffix}"


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
        'name': generate_ia_name(name_prefix, attr_num),
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
        'name': generate_ia_name(name_prefix, attr_num),
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
    name = generate_ia_name(prefix="SpaceIA", attr_num=attr_num)
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


# ═══════════════════════════════════════════
#  FIELD VALIDATION RULES (from live ERP schema)
# ═══════════════════════════════════════════

FIELD_VALIDATION_RULES = {
    "name": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Item Attribute name. BUG-IA01: duplicates currently allowed.",
    },
    "base_uom": {
        "type": "dropdown",
        "required": True,
        "note": "Base UOM dropdown — only on Item Attribute 1. BUG-IA02: browser click doesn't register.",
    },
    "description": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "Optional description text.",
    },
    "status": {
        "type": "toggle",
        "required": False,
        "default": True,
        "note": "Status toggle — Active/Inactive. Default is Active.",
    },
}
