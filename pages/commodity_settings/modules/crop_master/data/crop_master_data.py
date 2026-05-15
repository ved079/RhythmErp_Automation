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
