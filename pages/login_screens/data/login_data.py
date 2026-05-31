"""
login_data.py
-------------
Test data for Login and Forgot Password test cases.
Contains credentials and inputs for positive and negative test scenarios.

This file acts as a central data source — tests import from here.
No hardcoded credentials in test files!
"""

# ================================================================
# VALID CREDENTIALS (loaded from .env via config.py)
# ================================================================
# For valid login tests, always import from config:
#   from config import PACS_EMAIL, PACS_PASSWORD, PACS_FACILITY

# ================================================================
# INVALID EMAIL TEST DATA
# ================================================================
INVALID_EMAILS = [
    {
        "test_name": "Invalid email format - no @ sign",
        "email": "invalidemail",
        "description": "Email without @ symbol"
    },
    {
        "test_name": "Invalid email format - no domain",
        "email": "user@",
        "description": "Email with @ but no domain"
    },
    {
        "test_name": "Invalid email format - no username",
        "email": "@domain.com",
        "description": "Email with @ but no username"
    },
    {
        "test_name": "Invalid email format - spaces",
        "email": "user @mail.com",
        "description": "Email with spaces"
    },
    {
        "test_name": "Invalid email - non-existent",
        "email": "nonexistent_user_12345@randomdomain999.com",
        "description": "Valid format but non-existent email"
    },
    {
        "test_name": "Empty email field",
        "email": "",
        "description": "Submit with empty email field"
    },
]

# ================================================================
# WRONG PASSWORD TEST DATA
# ================================================================
WRONG_PASSWORDS = [
    {"test_name": "Completely wrong password", "password": "CompletelyWrongPassword999"},
    {"test_name": "Password with spaces", "password": "Wrong Pass 123"},
    {"test_name": "Short password", "password": "abc"},
    {"test_name": "Empty password", "password": ""},
]

# ================================================================
# NEGATIVE COMBINATION TEST DATA
# ================================================================
NEGATIVE_LOGIN_COMBINATIONS = [
    {
        "test_name": "Wrong email, correct password",
        "email": "wrongemail@mail.com",
        "password": "Dcb@12345",
        "facility": "dcb1",
        "expected": "error"
    },
    {
        "test_name": "Correct email, wrong password",
        "email": "dcb1@mail.com",
        "password": "WrongPassword123",
        "facility": "dcb1",
        "expected": "error"
    },
    {
        "test_name": "Wrong email, wrong password",
        "email": "wrongemail@mail.com",
        "password": "WrongPassword123",
        "facility": "dcb1",
        "expected": "error"
    },
    {
        "test_name": "Empty email, correct password",
        "email": "",
        "password": "Dcb@12345",
        "facility": "dcb1",
        "expected": "validation_error"
    },
    {
        "test_name": "Correct email, empty password",
        "email": "dcb1@mail.com",
        "password": "",
        "facility": "dcb1",
        "expected": "validation_error"
    },
    {
        "test_name": "All fields empty",
        "email": "",
        "password": "",
        "facility": "",
        "expected": "validation_error"
    },
]

# ================================================================
# CASE VARIATIONS — for TC-14
# ================================================================
CASE_VARIATIONS = [
    {"test_name": "All uppercase", "email": "DCB1@MAIL.COM"},
    {"test_name": "All lowercase", "email": "dcb1@mail.com"},
    {"test_name": "Mixed case", "email": "DcB1@MaIl.CoM"},
    {"test_name": "Title case", "email": "Dcb1@Mail.Com"},
]

# ================================================================
# SPACE VARIATIONS — for TC-15
# ================================================================
SPACE_VARIATIONS = [
    {"test_name": "Leading space in email", "email": " dcb1@mail.com"},
    {"test_name": "Trailing space in email", "email": "dcb1@mail.com "},
    {"test_name": "Both spaces in email", "email": " dcb1@mail.com "},
    {"test_name": "Leading space in password", "password": " Dcb@12345"},
    {"test_name": "Trailing space in password", "password": "Dcb@12345 "},
    {"test_name": "Both spaces in password", "password": " Dcb@12345 "},
]

# ================================================================
# SPECIAL CHARACTER TESTS — for TC-16
# ================================================================
SPECIAL_CHAR_EMAILS = [
    {"test_name": "Plus sign", "email": "dcb1+test@mail.com"},
    {"test_name": "Dot before @", "email": "dcb.1@mail.com"},
    {"test_name": "Underscore", "email": "dcb_1@mail.com"},
    {"test_name": "Hyphen", "email": "dcb-1@mail.com"},
]

SPECIAL_CHAR_PASSWORDS = [
    {"test_name": "XSS script tag", "password": "<script>alert(1)</script>"},
    {"test_name": "SQL injection attempt", "password": "' OR 1=1 --"},
    {"test_name": "HTML tags", "password": "<img src=x onerror=alert(1)>"},
    {"test_name": "Quotes and slashes", "password": "pass'\"word\\"},
]

# ================================================================
# UNICODE TESTS — for TC-17
# ================================================================
UNICODE_EMAILS = [
    {"test_name": "Accented e", "email": "dcb1\u00e9@mail.com"},
    {"test_name": "Chinese chars", "email": "\u7528\u6237@mail.com"},
]

# ================================================================
# BOUNDARY / EDGE CASE DATA
# ================================================================
BOUNDARY_TEST_DATA = [
    {"test_name": "Email with special characters", "email": "user+test@mail.com"},
    {"test_name": "Very long email", "email": "a" * 100 + "@mail.com"},
    {"test_name": "Very long password", "password": "A" * 200},
]

# ================================================================
# EXPECTED MESSAGES (may need adjustment based on actual app)
# ================================================================
EXPECTED_MESSAGES = {
    "invalid_credentials": "Invalid credentials",
    "required_field": "This field is required",
    "login_success": "",
}


# ================================================================
# ================================================================
# FORGOT PASSWORD TEST DATA
# ================================================================
# ================================================================

from config import (
    FP_EMAIL,
    FP_CURRENT_PASSWORD,
    FP_NEW_PASSWORD,
    FP_OLD_PASSWORDS,
)


class ForgotPasswordData:

    # --- Screen 1: Email Input ---
    VALID_EMAIL = FP_EMAIL
    UNREGISTERED_EMAIL = "nobody@doesnotexist.com"
    BLANK_EMAIL = ""
    INVALID_FORMAT_EMAILS = [
        "abc",
        "abc@",
        "@mail.com",
        "abc@mail",
        "abc@.com",
    ]
    LONG_EMAIL = "a" * 100 + "@mail.com"

    # --- Screen 2: OTP Input ---
    VALID_OTP = ""          # Not used directly; OTP entered manually
    BLANK_OTP = ""
    PARTIAL_OTP = "123"
    INVALID_OTP = "000000"

    # --- Screen 2: Password Input ---
    VALID_NEW_PASSWORD = FP_NEW_PASSWORD
    VALID_CONFIRM_PASSWORD = FP_NEW_PASSWORD
    BLANK_PASSWORD = ""

    WEAK_PASSWORDS = {
        "no_uppercase": "vedant@12345",
        "no_lowercase": "VEDANT@12345",
        "no_number": "Vedant@abcdx",
        "no_special": "Vedant123456",
        "too_short": "Ved@1",
    }

    MISMATCH_PASSWORD = FP_CURRENT_PASSWORD
    RECENTLY_USED_PASSWORDS = FP_OLD_PASSWORDS
    LONG_PASSWORD = "A" * 50 + "@1a"

    # --- Expected Messages ---
    SUCCESS_MESSAGE = "Password Reset Successful"
    PASSWORD_POLICY_LABELS = [
        "Minimum 12 characters",
        "One uppercase letter",
        "One lowercase letter",
        "One number",
        "One special character",
    ]



# ================================================================
# ================================================================
# LOGIN TEST DATA
# ================================================================
# ================================================================

from config import RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD


class LoginData:

    # --- RhythmERP Valid Credentials (for positive test) ---
    VALID_EMAIL = RHYTHMERP_EMAIL
    VALID_PASSWORD = RHYTHMERP_PASSWORD

    # --- Wrong Credentials ---
    WRONG_EMAIL = "wronguser@random.com"
    WRONG_PASSWORD = "WrongPass@99999"

    # --- Invalid Emails (reuses generic data from top of file) ---
    INVALID_EMAIL_FORMATS = [
        {"label": "No @ sign", "email": "invalidemail"},
        {"label": "No domain", "email": "user@"},
        {"label": "No username", "email": "@domain.com"},
    ]

    # --- Space Variations (reuses generic data from top of file) ---
    EMAIL_WITH_SPACES = {
        "leading": f" {RHYTHMERP_EMAIL}",
        "trailing": f"{RHYTHMERP_EMAIL} ",
        "both": f" {RHYTHMERP_EMAIL} ",
        "middle": "test @gmail.com",
    }

class ForgotPasswordData:
    """Test data for forgot password tests."""

    UNREGISTERED_EMAIL = "nonexistent_user_99999@random.com"

    INVALID_OTP = "000000"

    MISMATCH_PASSWORD = "CompletelyDifferent@99999"

    RECENTLY_USED_PASSWORDS = [
        "Vedant@oldpass1x",
        "Vedant@oldpass2x",
        "Vedant@oldpass3x",
    ]