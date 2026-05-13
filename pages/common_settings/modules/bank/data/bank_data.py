"""
bank_data.py
------------
Test data generators and constants for Bank screen automation.
Each function returns data safe for a specific test scenario.

14 fields total: 10 text inputs + 2 dropdowns + 2 toggles.
12 required fields (server rejects empty).
"""

import random
import string


# ================================================================
# FIELD NAMES (match input[name="..."] on the ERP form)
# ================================================================
FIELD_BANK_NAME = "Bank Name"
FIELD_BANK_CODE = "Bank Code"
FIELD_BRANCH_NAME = "Branch Name"
FIELD_BRANCH_CODE = "Branch Code"
FIELD_ACCOUNT_NUMBER = "Account Number"
FIELD_SWIFT_NUMBER = "Swift Number"         # Optional
FIELD_IBAN_NUMBER = "IBAN Number"           # Optional
FIELD_IFSC_CODE = "IFSC Code"
FIELD_CASH_CREDIT_LIMIT = "Cash Credit Limit"
FIELD_BANK_ADDRESS = "Bank Address"
FIELD_ACCOUNT_TYPE = "Account Type"         # Dropdown: Current / Saving
FIELD_GL_ACCOUNT = "GL Account"             # Dropdown: 115+ searchable options
FIELD_IS_DEFAULT_BANK = "Is Default Bank"   # Toggle: Yes / No
FIELD_STATUS = "Status"                     # Toggle: Active / Inactive

# Dropdown options
ACCOUNT_TYPE_CURRENT = "Current"
ACCOUNT_TYPE_SAVING = "Saving"

# Status values
STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"

# Toggle display labels
TOGGLE_DEFAULT_YES = "Yes"
TOGGLE_DEFAULT_NO = "No"
TOGGLE_STATUS_ACTIVE = "Active"
TOGGLE_STATUS_INACTIVE = "Inactive"


# ================================================================
# HELPERS
# ================================================================

def _random_suffix(length=6):
    """Generate a random alphanumeric suffix to avoid collisions."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _valid_ifsc():
    """Generate a valid IFSC code: 4 UPPERCASE + '0' + 6 alphanumeric."""
    bank_chars = ''.join(random.choices(string.ascii_uppercase, k=4))
    branch_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{bank_chars}0{branch_chars}"


def _valid_account_number():
    """Generate a valid-looking account number (12 digits)."""
    return ''.join(random.choices(string.digits, k=12))


def _valid_bank_code():
    """Generate a valid bank code."""
    return f"BC{_random_suffix(4)}"


def _valid_branch_code():
    """Generate a valid branch code."""
    return f"BR{_random_suffix(4)}"


# ================================================================
# VALID TEST DATA - Happy Path
# ================================================================

def valid_bank_data():
    """Full bank record with all 12 required fields + optional fields filled.

    Returns dict with keys matching FIELD_* constants.
    """
    return {
        FIELD_BANK_NAME: f"Bank{_random_suffix()}",
        FIELD_BANK_CODE: _valid_bank_code(),
        FIELD_BRANCH_NAME: f"Branch{_random_suffix()}",
        FIELD_BRANCH_CODE: _valid_branch_code(),
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),
        # SWIFT and IBAN are optional - skip to avoid server-side format validation
        FIELD_IFSC_CODE: _valid_ifsc(),
        FIELD_CASH_CREDIT_LIMIT: "500000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Test Street, City",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_CURRENT,
        FIELD_GL_ACCOUNT: "Cash",
        FIELD_IS_DEFAULT_BANK: False,
        FIELD_STATUS: True,
    }


def valid_bank_required_only():
    """Bank record with only required fields (no optional Swift/IBAN)."""
    return {
        FIELD_BANK_NAME: f"Bank{_random_suffix()}",
        FIELD_BANK_CODE: _valid_bank_code(),
        FIELD_BRANCH_NAME: f"Branch{_random_suffix()}",
        FIELD_BRANCH_CODE: _valid_branch_code(),
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),
        FIELD_IFSC_CODE: _valid_ifsc(),
        FIELD_CASH_CREDIT_LIMIT: "300000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Test Street",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_SAVING,
        FIELD_GL_ACCOUNT: "Cash",
    }

def valid_bank_with_saving_type():
    """Bank record with Saving account type."""
    data = valid_bank_data()
    data[FIELD_ACCOUNT_TYPE] = ACCOUNT_TYPE_SAVING
    return data


def valid_bank_inactive():
    """Bank record with Inactive status."""
    data = valid_bank_data()
    data[FIELD_STATUS] = False  # False = Inactive toggle
    return data


def valid_bank_default():
    """Bank record with Is Default Bank set to Yes."""
    data = valid_bank_data()
    data[FIELD_IS_DEFAULT_BANK] = True
    return data


def valid_bank_name():
    """Just a unique bank name string - for simple tests."""
    return f"Bank{_random_suffix()}"


# ================================================================
# NEGATIVE / BUG TEST DATA
# ================================================================

def empty_submit():
    """All fields blank - should trigger Validation Failed (only 4 of 12 show errors - BUG)."""
    return {}


def bank_name_with_underscore():
    """Underscore in Bank Name - server REJECTS with 'Invalid Bank Name'."""
    return {
        FIELD_BANK_NAME: f"Test_Underscore{_random_suffix()}",
        FIELD_BANK_CODE: _valid_bank_code(),
        FIELD_BRANCH_NAME: f"Branch{_random_suffix()}",
        FIELD_BRANCH_CODE: _valid_branch_code(),
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),
        FIELD_IFSC_CODE: _valid_ifsc(),
        FIELD_CASH_CREDIT_LIMIT: "500000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Street",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_CURRENT,
        FIELD_GL_ACCOUNT: "Cash",
    }


def bank_name_with_at_symbol():
    """@ symbol in Bank Name - server REJECTS with 'Invalid Bank Name'."""
    return {
        FIELD_BANK_NAME: f"Test@Bank{_random_suffix()}",
        FIELD_BANK_CODE: _valid_bank_code(),
        FIELD_BRANCH_NAME: f"Branch{_random_suffix()}",
        FIELD_BRANCH_CODE: _valid_branch_code(),
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),
        FIELD_IFSC_CODE: _valid_ifsc(),
        FIELD_CASH_CREDIT_LIMIT: "500000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Street",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_CURRENT,
        FIELD_GL_ACCOUNT: "Cash",
    }


def invalid_ifsc_lowercase():
    """Lowercase IFSC - server REJECTS with 'Invalid IFSC'."""
    data = valid_bank_required_only()
    data[FIELD_IFSC_CODE] = "sbin0001234"
    return data


def invalid_ifsc_wrong_length():
    """Wrong length IFSC (7 chars) - server REJECTS with 'Invalid IFSC'."""
    data = valid_bank_required_only()
    data[FIELD_IFSC_CODE] = "INVALID"
    return data


def invalid_ifsc_no_zero():
    """IFSC without mandatory '0' - server REJECTS with 'Invalid IFSC'."""
    data = valid_bank_required_only()
    data[FIELD_IFSC_CODE] = "ABCD1234567"
    return data


def negative_ccl():
    """Negative Cash Credit Limit - server REJECTS with 'Invalid Cash Credit Limit'."""
    data = valid_bank_required_only()
    data[FIELD_CASH_CREDIT_LIMIT] = "-50000"
    return data


def duplicate_bank_name(existing_name):
    """Data with a Bank Name that already exists - BUG: accepted (no unique constraint)."""
    return {
        FIELD_BANK_NAME: existing_name,
        FIELD_BANK_CODE: _valid_bank_code(),
        FIELD_BRANCH_NAME: f"Branch{_random_suffix()}",
        FIELD_BRANCH_CODE: _valid_branch_code(),
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),
        FIELD_IFSC_CODE: _valid_ifsc(),
        FIELD_CASH_CREDIT_LIMIT: "500000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Street",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_CURRENT,
        FIELD_GL_ACCOUNT: "Cash",
    }


def bank_code_special_chars():
    """Special characters in Bank Code - BUG: accepted without validation."""
    data = valid_bank_required_only()
    data[FIELD_BANK_CODE] = f"BC@#$%{_random_suffix(2)}"
    return data


def branch_code_special_chars():
    """Special characters in Branch Code - BUG: accepted without validation."""
    data = valid_bank_required_only()
    data[FIELD_BRANCH_CODE] = f"BR@#{_random_suffix(2)}"
    return data


def sql_injection_bank_name():
    """SQL injection in Bank Name - BUG: stored as-is in DB."""
    data = valid_bank_required_only()
    data[FIELD_BANK_NAME] = f"'; DROP TABLE Bank{_random_suffix()}--"
    return data


def xss_script_tag_bank_name():
    """XSS script tag in Bank Name - BUG: stored in DB (rendered safely by Angular)."""
    data = valid_bank_required_only()
    data[FIELD_BANK_NAME] = f"<script>alert('xss{_random_suffix()}')</script>"
    return data


def very_long_bank_name(length=500):
    """Extremely long Bank Name - BUG: no maxlength, accepted unlimited."""
    data = valid_bank_required_only()
    data[FIELD_BANK_NAME] = f"Long{'A' * length}{_random_suffix(4)}"
    return data


def leading_trailing_spaces_bank():
    """Bank Name with leading and trailing spaces - tests trim behavior."""
    data = valid_bank_required_only()
    data[FIELD_BANK_NAME] = f"   Bank{_random_suffix()}   "
    return data


# ================================================================
# ALIASES (names used by test file)
# ================================================================
# IMPORTANT: These must come AFTER the function definitions above
invalid_ccl_negative = negative_ccl
invalid_bank_name_underscore = bank_name_with_underscore
invalid_bank_name_at_symbol = bank_name_with_at_symbol


# ================================================================
# EXPECTED ALERT MESSAGES
# ================================================================
VALIDATION_ALERT_TITLE = "Validation Failed"
VALIDATION_ALERT_SUBTEXT = "Please correct the highlighted fields"

SUCCESS_ALERT_TITLE_ADD = "Your record has been added successfully!"
SUCCESS_ALERT_TITLE_UPDATE = "Your record has been updated successfully!"

# Server-side error messages
ERROR_INVALID_BANK_NAME = "Invalid Bank Name"
ERROR_INVALID_IFSC = "Invalid IFSC"
ERROR_INVALID_CCL = "Invalid Cash Credit Limit"

# Required field error (only 4 of 12 show this - BUG)
REQUIRED_FIELD_ERROR = "This field is required"


# ================================================================
# ERP NAVIGATION
# ================================================================
BANK_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Bank"
