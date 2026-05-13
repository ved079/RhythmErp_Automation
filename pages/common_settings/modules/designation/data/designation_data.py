"""
Designation Screen — Test Data Generators

All data is dynamic (timestamp + random). No hardcoded values.
Name field has type="character" validation: ONLY letters and spaces allowed.
Underscores, digits, special chars (@#$%^&*!) = ALL REJECTED with "Invalid Name" mat-error.
"""

import random
import string
import time


def generate_designation_name(prefix="AutoDesig"):
    """Generate a unique valid designation name - alphabetic only (no digits/underscores).
    Uses random alphabetic suffix to ensure uniqueness."""
    suffix = ''.join(random.choices(string.ascii_uppercase, k=8))
    return f"{prefix} {suffix}"


def generate_description(prefix="Test Description"):
    """Generate a description string."""
    timestamp = int(time.time())
    return f"{prefix} {timestamp}"


def generate_valid_designation_data():
    """
    Generate a complete valid data dict for creating a designation.
    Name: valid alphabetic with spaces (passes pattern validation).
    Description: optional text.
    Status: True = Active (default), False = Inactive.
    """
    return {
        'name': generate_designation_name(),
        'description': generate_description(),
        'status': True  # Active by default
    }


def generate_valid_edit_data():
    """Generate valid data for editing an existing designation."""
    return {
        'name': generate_designation_name(prefix="EditDesig"),
        'description': generate_description(prefix="Updated Desc"),
        'status': False  # Toggle to Inactive
    }


def generate_string_255():
    """Generate a 255-character valid name (all alphabetic + spaces).
    Must pass the Name pattern validation — no special chars."""
    base = "ValidName "
    repeats = 255 // len(base)
    remainder = 255 % len(base)
    result = (base * repeats) + base[:remainder]
    return result[:255]


def generate_string_256():
    """Generate a 256-character valid name (all alphabetic + spaces).
    Tests max length boundary — no max length validation exists."""
    base = "ValidName "
    repeats = 256 // len(base)
    remainder = 256 % len(base)
    result = (base * repeats) + base[:remainder]
    return result[:256]


def generate_spaces_only():
    """Generate spaces-only name.
    Triggers 'Invalid Name' mat-error (pattern validation rejects spaces-only)."""
    return "     "


def generate_special_char_name():
    """Generate name with special characters (@#$%^&*).
    Triggers 'Invalid Name' mat-error (pattern validation rejects these)."""
    special_chars = ['Test@Name', 'Test#Name', 'Test$Name', 'Test%Name',
                     'Test^Name', 'Test&Name', 'Test*Name', 'Test!Name']
    return random.choice(special_chars)


def generate_digits_only():
    """Generate digits-only name.
    Triggers 'Invalid Name' mat-error (pattern validation rejects digits-only)."""
    return str(random.randint(10000, 99999))


def generate_duplicate_name_data():
    """Generate data with a name that already exists in the system.
    BUG: No duplicate name validation — duplicate accepted silently."""
    existing_names = ['CEO', 'CFO', 'Jr. Manager', 'Sr. Manager',
                      'Field Officer', 'Farmer Coordinator']
    return {
        'name': random.choice(existing_names),
        'description': 'Duplicate name test',
        'status': True
    }


def generate_empty_data():
    """Generate empty data dict — all fields blank.
    Should trigger 'Validation Failed' SweetAlert2 for required Name."""
    return {
        'name': '',
        'description': '',
        'status': True
    }


def generate_name_only_data():
    """Generate data with only Name filled.
    Should succeed — Description is optional, Status defaults to Active."""
    return {
        'name': generate_designation_name(prefix="NameOnly"),
        'description': '',
        'status': True
    }