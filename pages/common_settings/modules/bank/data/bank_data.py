"""
bank_data.py
------------
Test data generators and constants for Bank screen automation.
Each function returns data safe for a specific test scenario.

14 fields total: 10 text inputs + 2 dropdowns + 2 toggles.

FIELD RULES (discovered from ERP exploration):
  Bank Name:         ONLY letters (a-z, A-Z), max 255 chars, NO digits, NO special chars
  Bank Code:         Alphanumeric, FIXED length 4, no special chars
  Branch Name:       ONLY numbers accepted, max 255 chars (BUG: should accept text)
  Branch Code:       ONLY numbers, FIXED length 6
  Account Number:    ONLY numbers, FIXED length 9
  IFSC Code:         Exactly 11 chars: 4 UPPERCASE letters + '0' + 6 alphanumeric
  Cash Credit Limit: Only numbers, max 255 (BUG: scientific notation on edit)
  Bank Address:      Max 255 chars, all chars accepted (nums, chars, special, mixed)
  Account Type:      Dropdown: Current / Saving
  GL Account:        Dropdown: 115+ searchable options
  Is Default Bank:   Toggle: Yes / No
  Status:            Toggle: Active / Inactive

VALIDATION BEHAVIOUR:
  - Real-time: mat-error shown when moving to next field with invalid input
  - On submit: SweetAlert2 "Validation Failed" + "Please correct the highlighted fields" + OK
  - Inline errors: "Invalid Name", "Invalid Code", "Invalid IFSC", etc.
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
# FIELD RULES REFERENCE (for documentation & assertions)
# ================================================================
FIELD_RULES = {
    FIELD_BANK_NAME: {
        "type": "text",
        "format": "alphanumeric",
        "max_length": 255,
        "special_chars": "rejected",
        "required": True,
        "notes": "No special characters allowed",
    },
    FIELD_BANK_CODE: {
        "type": "text",
        "format": "alphanumeric",
        "fixed_length": 4,
        "special_chars": "rejected",
        "required": True,
        "notes": "Exactly 4 alphanumeric characters",
    },
    FIELD_BRANCH_NAME: {
        "type": "text",
        "format": "numbers_only",
        "max_length": 255,
        "special_chars": "rejected",
        "required": False,
        "notes": "BUG: Only numbers accepted, should accept text characters",
        "bug": True,
    },
    FIELD_BRANCH_CODE: {
        "type": "text",
        "format": "numbers_only",
        "fixed_length": 6,
        "special_chars": "rejected",
        "required": False,
        "notes": "Exactly 6 numeric digits",
    },
    FIELD_ACCOUNT_NUMBER: {
        "type": "text",
        "format": "numbers_only",
        "fixed_length": 9,
        "special_chars": "rejected",
        "required": True,
        "notes": "Exactly 9 numeric digits",
    },
    FIELD_IFSC_CODE: {
        "type": "text",
        "format": "IFSC",
        "length": 11,
        "required": False,
        "notes": "4 UPPERCASE letters + '0' + 6 alphanumeric (e.g. SBIN0001234)",
    },
    FIELD_CASH_CREDIT_LIMIT: {
        "type": "text",
        "format": "numbers_only",
        "max_length": 255,
        "special_chars": "rejected",
        "required": False,
        "notes": "BUG: 255-digit number becomes scientific notation on edit (e.g. 1.1e+254)",
        "bug": True,
    },
    FIELD_BANK_ADDRESS: {
        "type": "text",
        "format": "any",
        "max_length": 255,
        "special_chars": "accepted",
        "required": False,
        "notes": "All characters accepted: numbers, letters, special chars, mixed",
    },
}


# ================================================================
# HELPERS
# ================================================================

def _random_suffix(length=6):
    """Generate a random alphanumeric suffix to avoid collisions."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _random_alpha_suffix(length=6):
    """Generate a random LETTERS-ONLY suffix for Bank Name (no digits, no special chars)."""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


def _valid_ifsc():
    """Generate a valid IFSC code: 4 UPPERCASE + '0' + 6 alphanumeric.
    Total = 11 characters.
    """
    bank_chars = ''.join(random.choices(string.ascii_uppercase, k=4))
    branch_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{bank_chars}0{branch_chars}"


def _valid_account_number():
    """Generate a valid account number: exactly 9 numeric digits."""
    return ''.join(random.choices(string.digits, k=9))


def _valid_bank_code():
    """Generate a valid bank code: exactly 4 alphanumeric characters."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))


def _valid_branch_code():
    """Generate a valid branch code: exactly 6 numeric digits."""
    return ''.join(random.choices(string.digits, k=6))


def _valid_branch_name():
    """Generate a valid branch name: numbers only (BUG: text rejected).
    Returns a random numeric string up to 10 digits.
    """
    return str(random.randint(1000000000, 9999999999))


# ================================================================
# VALID TEST DATA - Happy Path
# ================================================================

def valid_bank_data():
    """Full bank record with all 12 required fields + optional fields filled.

    Returns dict with keys matching FIELD_* constants.
    All values comply with the actual ERP field rules.
    """
    return {
        FIELD_BANK_NAME: f"Bank{_random_alpha_suffix()}",
        FIELD_BANK_CODE: _valid_bank_code(),                  # 4 alphanumeric
        FIELD_BRANCH_NAME: _valid_branch_name(),              # numbers only (bug)
        FIELD_BRANCH_CODE: _valid_branch_code(),              # 6 digits
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),        # 9 digits
        # SWIFT and IBAN are optional - skip to avoid server-side format validation
        FIELD_IFSC_CODE: _valid_ifsc(),                       # 11 chars
        FIELD_CASH_CREDIT_LIMIT: "500000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Test Street, City",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_CURRENT,
        FIELD_GL_ACCOUNT: "Cash",
        FIELD_IS_DEFAULT_BANK: TOGGLE_DEFAULT_NO,             # FIX #1: string not bool
        FIELD_STATUS: TOGGLE_STATUS_ACTIVE,                   # FIX #1: string not bool
    }


def valid_bank_required_only():
    """Bank record with only required fields (no optional Swift/IBAN).

    All values comply with the actual ERP field rules.
    FIX #2: Now includes FIELD_IS_DEFAULT_BANK and FIELD_STATUS so
    edit tests that call data.get() get explicit values instead of
    falling through to defaults.
    """
    return {
        FIELD_BANK_NAME: f"Bank{_random_alpha_suffix()}",
        FIELD_BANK_CODE: _valid_bank_code(),                  # 4 alphanumeric
        FIELD_BRANCH_NAME: _valid_branch_name(),              # numbers only (bug)
        FIELD_BRANCH_CODE: _valid_branch_code(),              # 6 digits
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),        # 9 digits
        FIELD_IFSC_CODE: _valid_ifsc(),                       # 11 chars
        FIELD_CASH_CREDIT_LIMIT: "300000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Test Street",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_SAVING,
        FIELD_GL_ACCOUNT: "Cash",
        FIELD_IS_DEFAULT_BANK: TOGGLE_DEFAULT_NO,             # FIX #2: was missing
        FIELD_STATUS: TOGGLE_STATUS_ACTIVE,                   # FIX #2: was missing
    }


def valid_bank_with_saving_type():
    """Bank record with Saving account type."""
    data = valid_bank_data()
    data[FIELD_ACCOUNT_TYPE] = ACCOUNT_TYPE_SAVING
    return data


def valid_bank_inactive():
    """Bank record with Inactive status."""
    data = valid_bank_data()
    data[FIELD_STATUS] = STATUS_INACTIVE                      # FIX #3: was False (bool)
    return data


def valid_bank_default():
    """Bank record with Is Default Bank set to Yes."""
    data = valid_bank_data()
    data[FIELD_IS_DEFAULT_BANK] = TOGGLE_DEFAULT_YES          # FIX #4: was True (bool)
    return data


def valid_bank_name():
    """Just a unique bank name string - for simple tests."""
    return f"Bank{_random_alpha_suffix()}"


# ================================================================
# NEGATIVE / BUG TEST DATA
# ================================================================

def empty_submit():
    """All fields blank - should trigger Validation Failed."""
    return {}


def bank_name_with_underscore():
    """Underscore in Bank Name - server REJECTS with 'Invalid Bank Name'."""
    return {
        FIELD_BANK_NAME: f"Test{_random_suffix()}Underscore",
        FIELD_BANK_CODE: _valid_bank_code(),
        FIELD_BRANCH_NAME: _valid_branch_name(),
        FIELD_BRANCH_CODE: _valid_branch_code(),
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),
        FIELD_IFSC_CODE: _valid_ifsc(),
        FIELD_CASH_CREDIT_LIMIT: "500000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Street",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_CURRENT,
        FIELD_GL_ACCOUNT: "Cash",
        FIELD_IS_DEFAULT_BANK: TOGGLE_DEFAULT_NO,
        FIELD_STATUS: TOGGLE_STATUS_ACTIVE,
    }


def bank_name_with_at_symbol():
    """@ symbol in Bank Name - server REJECTS with 'Invalid Bank Name'."""
    return {
        FIELD_BANK_NAME: f"Test{random.randint(100,999)}@Bank",
        FIELD_BANK_CODE: _valid_bank_code(),
        FIELD_BRANCH_NAME: _valid_branch_name(),
        FIELD_BRANCH_CODE: _valid_branch_code(),
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),
        FIELD_IFSC_CODE: _valid_ifsc(),
        FIELD_CASH_CREDIT_LIMIT: "500000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Street",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_CURRENT,
        FIELD_GL_ACCOUNT: "Cash",
        FIELD_IS_DEFAULT_BANK: TOGGLE_DEFAULT_NO,
        FIELD_STATUS: TOGGLE_STATUS_ACTIVE,
    }


def invalid_ifsc_lowercase():
    """Lowercase IFSC - server REJECTS with 'Invalid IFSC'."""
    data = valid_bank_required_only()
    data[FIELD_IFSC_CODE] = "sbin0001234"
    return data


def invalid_ifsc_wrong_length():
    """Wrong length IFSC (7 chars) - server REJECTS with 'Invalid IFSC'.

    FIX #5: Changed from 'INVALID' to 'SBIN0ABC'.
    'INVALID' was triple-invalid (lowercase + no '0' + wrong length).
    'SBIN0ABC' is single-invalid: valid format (4 uppercase + '0')
    but only 7 chars total instead of required 11.
    """
    data = valid_bank_required_only()
    data[FIELD_IFSC_CODE] = "SBIN0ABC"  # 7 chars — valid prefix format, wrong length
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
        FIELD_BRANCH_NAME: _valid_branch_name(),
        FIELD_BRANCH_CODE: _valid_branch_code(),
        FIELD_ACCOUNT_NUMBER: _valid_account_number(),
        FIELD_IFSC_CODE: _valid_ifsc(),
        FIELD_CASH_CREDIT_LIMIT: "500000",
        FIELD_BANK_ADDRESS: f"{random.randint(1, 999)} Street",
        FIELD_ACCOUNT_TYPE: ACCOUNT_TYPE_CURRENT,
        FIELD_GL_ACCOUNT: "Cash",
        FIELD_IS_DEFAULT_BANK: TOGGLE_DEFAULT_NO,
        FIELD_STATUS: TOGGLE_STATUS_ACTIVE,
    }


def bank_code_special_chars():
    """Special characters in Bank Code - ERP behavior TBD.

    Bank Code = alphanumeric, fixed length 4. '@#$' is 3 special chars
    (also wrong length — double-invalid).
    Used in T18 to test whether ERP rejects non-alphanumeric input.
    """
    data = valid_bank_required_only()
    data[FIELD_BANK_CODE] = "@#$"  # 3 special chars (also wrong length)
    return data


def bank_code_wrong_length():
    """Bank Code with wrong length (8 chars instead of fixed 4) - server REJECTS."""
    data = valid_bank_required_only()
    data[FIELD_BANK_CODE] = "ABCDEFGH"  # 8 chars, should be exactly 4
    return data


def bank_code_letters_in_numbers_field():
    """Bank Code is alphanumeric so this is valid - for contrast with Branch Code."""
    data = valid_bank_required_only()
    data[FIELD_BANK_CODE] = "AB12"  # valid: 4 alphanumeric
    return data


def branch_code_letters():
    """Letters in Branch Code (numbers-only, fixed 6) - server REJECTS.

    Used in T18 to test that Branch Code only accepts numeric digits.
    'ABCDEF' has 6 chars (correct length) but all letters (wrong format).
    """
    data = valid_bank_required_only()
    data[FIELD_BRANCH_CODE] = "ABCDEF"  # letters not allowed, should be 6 digits
    return data


# Alias for backward compatibility — test file imports this name
branch_code_special_chars = branch_code_letters


def branch_code_wrong_length():
    """Branch Code with wrong length (4 digits instead of fixed 6) - server REJECTS."""
    data = valid_bank_required_only()
    data[FIELD_BRANCH_CODE] = "1234"  # 4 digits, should be exactly 6
    return data


def account_number_wrong_length():
    """Account Number with wrong length (12 digits instead of fixed 9) - server REJECTS."""
    data = valid_bank_required_only()
    data[FIELD_ACCOUNT_NUMBER] = "123456789012"  # 12 digits, should be exactly 9
    return data


def account_number_letters():
    """Account Number with letters - server REJECTS (numbers only, fixed 9)."""
    data = valid_bank_required_only()
    data[FIELD_ACCOUNT_NUMBER] = "ABCDEFGHI"  # letters not allowed
    return data


def branch_name_with_text():
    """BUG: Branch Name with text characters - server REJECTS (only numbers accepted).
    Branch Name SHOULD accept text but ERP has a bug.
    """
    data = valid_bank_required_only()
    data[FIELD_BRANCH_NAME] = "TestBranch"  # text rejected (bug)
    return data


def ccl_long_number_bug():
    """BUG: Cash Credit Limit with 255 digits - saves fine, but on edit becomes
    scientific notation (1.1e+254) which then gets rejected as 'Invalid Cash Credit Limit'
    because it contains letters.
    """
    data = valid_bank_required_only()
    data[FIELD_CASH_CREDIT_LIMIT] = "1" + "1" * 254  # 255 digits
    return data


def bank_name_exceeds_255():
    """Bank Name with 256 chars - server REJECTS (max 255)."""
    data = valid_bank_required_only()
    data[FIELD_BANK_NAME] = "A" * 256
    return data


def bank_address_exceeds_255():
    """Bank Address with 256 chars - server REJECTS (max 255)."""
    data = valid_bank_required_only()
    data[FIELD_BANK_ADDRESS] = "X" * 256
    return data


def sql_injection_bank_name():
    """SQL injection attempt in Bank Name with space (special char).

    Server REJECTS 'Invalid Bank Name' because space is a special char.
    NOTE: 'DROPTABLE' (all alphanumeric) would be ACCEPTED by ERP.
    """
    data = valid_bank_required_only()
    data[FIELD_BANK_NAME] = "DROP TABLE banks"  # space = special char → rejected
    return data


def xss_script_tag_bank_name():
    """XSS script tag in Bank Name - server REJECTS (special chars not allowed)."""
    data = valid_bank_required_only()
    data[FIELD_BANK_NAME] = "<script>alert('xss')</script>"  # <, >, ', / = special chars
    return data


def very_long_bank_name(length=255):
    """Bank Name at exactly 255 chars (max boundary) - should be ACCEPTED."""
    data = valid_bank_required_only()
    # Use alphanumeric to avoid special char rejection
    name = "A" * (length - 6) + _random_alpha_suffix(6)
    data[FIELD_BANK_NAME] = name[:255]  # ensure exactly 255
    return data


def leading_trailing_spaces_bank():
    """Bank Name with leading and trailing spaces - tests trim behavior."""
    data = valid_bank_required_only()
    data[FIELD_BANK_NAME] = f"   Bank{_random_suffix()}   "
    return data


# ================================================================
# ALIASES (names used by test file)
# ================================================================
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
ERROR_INVALID_CODE = "Invalid Code"
ERROR_INVALID_IFSC = "Invalid IFSC"
ERROR_INVALID_CCL = "Invalid Cash Credit Limit"

# Required field error
REQUIRED_FIELD_ERROR = "This field is required"


# ================================================================
# ERP NAVIGATION
# ================================================================
BANK_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Bank"
