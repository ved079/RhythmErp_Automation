"""
bank_data.py
--------------
Test data generators for RhythmERP Bank screen.

Location: Common Settings > Bank
URL:      /#/dynamic-screens/Bank

FORM LAYOUT (simple popup — verified 2026-05-19 on live app):
  Single-page popup (NO stepper):
    - Bank Name              (text input,   required, maxlength=255, alpha-only uppercase)
    - Bank Code              (text input,   required, maxlength=255, alphanumeric)
    - Branch Name            (text input,   required, maxlength=255, alphanumeric)
    - Branch Code            (text input,   required, maxlength=255, alphanumeric)
    - Account Number         (text input,   required, maxlength=255, numeric)
    - Account Type           (mat-select,   required, searchable)
                              Options: Current, Saving
    - Swift Number           (text input,   optional, maxlength=255, SWIFT/BIC format)
    - IBAN Number            (text input,   optional, maxlength=255, IBAN format)
    - IFSC Code              (text input,   required, maxlength=255, 11 chars)
    - Cash Credit Limit      (text input,   required, maxlength=255, numeric)
    - Bank Address           (text input,   required, maxlength=255, alphanumeric+spaces)
    - GL Account             (mat-select,   required, searchable, 116+ options)
    - Is Default Bank?       (toggle switch, default No)
    - Status                 (toggle switch, default Active)

TABLE COLUMNS (main listing):
  - View / Edit / History   (action buttons per row)
  - Bank Name
  - Account Number
  - IFSC Code
  - Status

KEY RULES (verified from live application 2026-05-19):
  - Bank Name: All UPPERCASE letters only, appears to require >= 10 chars
    Existing records all follow pattern: "BankXXXXXX" (10 chars, uppercase)
    Lowercase, digits, spaces, and special characters are rejected.
  - Bank Code: Alphanumeric accepted. Numeric-only works (e.g., "5448", "C688").
    All-alpha codes may be rejected (needs further verification).
  - Branch Name: Numeric works (e.g., "5729175282"). All-alpha rejected.
  - Branch Code: Alphanumeric accepted. Both numeric and mixed work.
  - Account Number: Numeric only.
  - IFSC Code: Exactly 11 characters. "SBIN0001234" valid, "SBIN95BKGJDM" (12) invalid.
  - Swift Number: Optional. Valid SWIFT/BIC format accepted.
  - IBAN Number: Optional. Valid IBAN format accepted.
  - Cash Credit Limit: Numeric. Positive integers work.
  - Bank Address: Alphanumeric with spaces works.
  - NO formcontrolname attributes — only name attributes used.
  - Simple popup (not stepper). Submit button on create, Update on edit.
  - View popup: All fields DISABLED with character counters visible.
  - SweetAlert2: "Validation Failed" / "Your record has been added successfully!"

KNOWN BUGS:
  BUG-001 (MEDIUM): Account Type & GL Account dropdowns show NO mat-error
           text when required but empty. Only red highlight.
  BUG-002 (MEDIUM): Bank Address shows NO mat-error text when required but empty.
  BUG-003 (MEDIUM): Global search does not filter the Bank table at all.
  BUG-004 (CRITICAL): Browser-clicked mat-select options do NOT reliably update
           Angular reactive form model. Must use JS value-setter + dispatchEvent.
  BUG-005 (LOW): No Delete functionality anywhere on the Bank screen.
  BUG-006 (LOW): History button opens View popup instead of audit trail.
"""

import random
import string
from datetime import datetime


# ──────────────────────────────────────────────
# Core Data Generators
# ──────────────────────────────────────────────

def _rand_upper(n):
    """Generate n random uppercase ASCII letters."""
    return "".join(random.choices(string.ascii_uppercase, k=n))


def _rand_digits(n):
    """Generate n random digits as a string."""
    return "".join(random.choices(string.digits, k=n))


def _rand_alnum(n):
    """Generate n random alphanumeric characters."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def generate_bank_name(prefix="BNK"):
    """Generate a valid Bank Name (10 chars, all uppercase letters).

    Existing records follow pattern 'BankXXXXXX' (10 uppercase chars).
    Lowercase, digits, spaces, special chars are rejected.
    """
    return f"{prefix}{_rand_upper(7)}"  # prefix(3) + random(7) = 10


def generate_bank_code():
    """Generate a valid Bank Code (4-digit numeric string).

    Both numeric-only and alphanumeric values accepted by the ERP.
    Existing records use 4-digit numeric codes (e.g., '5448', 'C688').
    """
    return _rand_digits(4)


def generate_branch_name():
    """Generate a valid Branch Name (10-digit numeric string).

    Existing records use 10-digit numbers (e.g., '5729175282', '7769437757').
    All-alpha branch names appear to be rejected.
    """
    return _rand_digits(10)


def generate_branch_code():
    """Generate a valid Branch Code (6-digit numeric string).

    Both numeric and alphanumeric accepted (e.g., '528215', 'MBC001').
    """
    return _rand_digits(6)


def generate_account_number():
    """Generate a valid Account Number (10-digit numeric string).

    Numeric-only field. Existing records: '692215021', '2235164425'.
    """
    return _rand_digits(10)


# ──────────────────────────────────────────────
# IFSC Code Generator (corrected format)
# ──────────────────────────────────────────────

def generate_ifsc_code(bank_prefix="SBIN"):
    """Generate a valid IFSC Code (11 characters: 4 letters + '0' + 6 alphanumeric).

    Format: BBBB0######
      - First 4 chars: Bank code (A-Z letters only) → e.g., 'SBIN', 'HDFC', 'ICIC'
      - 5th char: Always '0' (zero, reserved for future use)
      - Last 6 chars: Branch identifier (usually numeric, but can be alphanumeric)

    Valid examples:
      - SBIN0001234  (State Bank of India, branch code '001234')
      - HDFC0000123  (HDFC Bank, branch code '000123')
      - ICIC0004567  (ICICI Bank, branch code '004567')
      - UTIB0007890  (Axis Bank, branch code '007890')
      - YESB0001122  (Yes Bank, branch code '001122')

    Invalid examples (will cause server validation error):
      - 'SBIN95BKGJDM' → 12 characters, missing the '0' in 5th position
      - 'SBI00012345'  → 11 chars but 5th char is '0'? Actually this would be 'SBI' (3 letters) + '0' + '0012345' (7 digits) -> total 11, but first 4 chars must be all letters.
        Correct: 'SBIN0' + '012345' would be 11 chars. The Wikipedia says first 4 are bank code.
        So 'SBI' is only 3 letters — invalid. Must be exactly 4 letters for the bank code.
    """
    # Ensure bank_prefix is exactly 4 uppercase letters
    bank_code = bank_prefix[:4].upper()
    if len(bank_code) < 4:
        bank_code = bank_code.ljust(4, 'X')  # Pad with 'X' if too short
    
    # Generate 6-character branch identifier (default: numeric)
    branch_code = ''.join(random.choices(string.digits, k=6))
    
    # Assemble IFSC: BBBB0######
    return f"{bank_code}0{branch_code}"


def generate_cash_credit_limit():
    """Generate a valid Cash Credit Limit (positive integer string).

    Positive integers work. Negative / alpha values need verification.
    """
    return str(random.randint(100000, 9999999))


def generate_bank_address():
    """Generate a valid Bank Address (alphanumeric with spaces).

    'Test Address Mumbai', '456 Andheri West Mumbai' both accepted.
    """
    streets = [
        "MG Road", "FC Road", "Andheri West", "Bandra East",
        "Pune", "Mumbai Central", "Thane West", "Navi Mumbai",
    ]
    city = random.choice(["Mumbai", "Pune", "Nagpur", "Nashik", "Thane"])
    return f"{random.randint(1, 999)} {random.choice(streets)} {city}"


def generate_swift_number():
    """Generate a valid SWIFT/BIC Number (8 or 11 uppercase alphanumeric chars).

    Standard SWIFT/BIC format: 8-char bank code or 11-char with branch.
    'SBIINBB123', 'SBIINBBXXX' both accepted.
    Empty value also accepted (optional field).
    """
    return f"{_rand_upper(8)}{_rand_upper(3)}"  # 11-char BIC with branch


def generate_iban_number():
    """Generate a valid IBAN Number.

    'IN1234567890' and 'GB29NWBK60161331926819' both accepted.
    Empty value also accepted (optional field).
    """
    return f"IN{_rand_digits(2)}{_rand_upper(4)}{_rand_digits(7)}"


# ──────────────────────────────────────────────
# Complete Valid Data for Create
# ──────────────────────────────────────────────

def generate_valid_bank_data(prefix="BNK"):
    """Generate a complete dict of valid bank data for the Create form.

    Dropdown values set to None — must be populated from live UI at runtime.
    The calling code or page object will select random valid options.
    """
    return {
        "bank_name": generate_bank_name(prefix),
        "bank_code": generate_bank_code(),
        "branch_name": generate_branch_name(),
        "branch_code": generate_branch_code(),
        "account_number": generate_account_number(),
        "account_type": None,       # Pick from live UI (REQUIRED) — "Current" or "Saving"
        "swift_number": generate_swift_number(),
        "iban_number": generate_iban_number(),
        "ifsc_code": generate_ifsc_code(),
        "cash_credit_limit": generate_cash_credit_limit(),
        "bank_address": generate_bank_address(),
        "gl_account": None,         # Pick from live UI (REQUIRED) — 116+ options
        "is_default_bank": False,   # Toggle: No (default)
        "status": True,             # Toggle: Active (default)
    }


def generate_valid_edit_data():
    """Generate valid data for Edit form modifications.

    Bank Name is editable in Edit mode (unlike Item Master).
    Dropdown values set to None — caller should specify or let
    page object preserve existing selections.
    """
    return {
        "bank_name": generate_bank_name("EDT"),
        "bank_code": generate_bank_code(),
        "branch_name": generate_branch_name(),
        "branch_code": generate_branch_code(),
        "account_number": generate_account_number(),
        "swift_number": generate_swift_number(),
        "iban_number": generate_iban_number(),
        "ifsc_code": generate_ifsc_code(),
        "cash_credit_limit": generate_cash_credit_limit(),
        "bank_address": generate_bank_address(),
        "is_default_bank": False,
        "status": True,
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_spaces_only(length=10):
    """Generate a string of only spaces."""
    return " " * length


def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds max)."""
    return "A" * 256


def generate_special_char_name():
    """Generate a name with special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"Bank{special}"


def generate_special_char_value():
    """Generate a value with common special characters."""
    return "!@#$%^&*()"


def generate_sql_injection():
    """SQL injection payload string."""
    return "'; DROP TABLE Bank; --"


def generate_xss_payload():
    """XSS payload string."""
    return "<script>alert('xss')</script>"


def generate_negative_limit():
    """Negative Cash Credit Limit value."""
    return f"-{random.randint(1, 999)}"


def generate_zero_limit():
    """Zero Cash Credit Limit value."""
    return "0"


def generate_alpha_limit():
    """Alphabetic Cash Credit Limit value."""
    return "abcDEF"


def generate_special_char_limit():
    """Special character Cash Credit Limit value."""
    return "!@#$"


def generate_limit_with_spaces():
    """Spaces-only Cash Credit Limit value."""
    return "   "


def generate_leading_trailing_spaces():
    """Bank Name with leading and trailing spaces."""
    return f"  {generate_bank_name()}  "


def generate_lowercase_bank_name():
    """Generate Bank Name with lowercase letters (should be invalid)."""
    return f"bank{_rand_upper(7)}".lower()


def generate_bank_name_with_digits():
    """Generate Bank Name with digits (should be invalid)."""
    return f"BNK{_rand_digits(7)}"


def generate_bank_name_too_short():
    """Generate Bank Name with < 10 chars (should be invalid)."""
    return f"BNK{_rand_upper(2)}"  # 5 chars


def generate_ifsc_too_short():
    """Generate IFSC Code with < 11 chars (should be invalid)."""
    return f"{_rand_upper(4)}{_rand_digits(5)}"  # 9 chars


def generate_ifsc_too_long():
    """Generate IFSC Code with > 11 chars (should be invalid)."""
    return f"{_rand_upper(4)}{_rand_digits(8)}"  # 12 chars


def generate_alpha_branch_name():
    """Generate Branch Name with letters only (may be invalid)."""
    return "MumbaiBranch"


def generate_alpha_account_number():
    """Generate Account Number with letters (should be invalid)."""
    return "ABCDEFGHIJ"


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "bank_name": "",
        "bank_code": "",
        "branch_name": "",
        "branch_code": "",
        "account_number": "",
        "account_type": "",
        "swift_number": "",
        "iban_number": "",
        "ifsc_code": "",
        "cash_credit_limit": "",
        "bank_address": "",
        "gl_account": "",
        "is_default_bank": False,
        "status": True,
    }


def generate_partial_required_data():
    """Return dict with only some required fields filled — for partial validation test."""
    return {
        "bank_name": generate_bank_name("Partial"),
        "bank_code": "",
        "branch_name": "",
        "branch_code": "",
        "account_number": "",
        "account_type": "",
        "swift_number": "",
        "iban_number": "",
        "ifsc_code": "",
        "cash_credit_limit": "",
        "bank_address": "",
        "gl_account": "",
        "is_default_bank": False,
        "status": True,
    }


# ──────────────────────────────────────────────
# Expected Validation Messages
# ──────────────────────────────────────────────

VALIDATION_MSG_REQUIRED = "This field is required"
VALIDATION_MSG_INVALID_BANK_NAME = "Invalid Bank Name"
VALIDATION_MSG_INVALID_BANK_CODE = "Invalid Bank Code"
VALIDATION_MSG_INVALID_BRANCH_NAME = "Invalid Name"
VALIDATION_MSG_INVALID_IFSC = "Invalid IFSC"
VALIDATION_MSG_INVALID_SWIFT = "Invalid Swift Number"
VALIDATION_MSG_INVALID_IBAN = "Invalid IBAN Number"

SWAL_TITLE_VALIDATION_FAILED = "Validation Failed"
SWAL_CONTENT_VALIDATION_FAILED = "Please correct the highlighted fields"
SWAL_TITLE_SUCCESS = "Your record has been added successfully!"
SWAL_TITLE_UPDATED = "Your record has been updated successfully!"


# ═══════════════════════════════════════════════════════════════════════════════
# API Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Converts UI data format into the JSON payload that
# POST /core/dynamic-screen-wrapper/ expects.
#
# BANK SCREEN STRUCTURE (flat — no children/steppers):
#   {
#     "id": "",
#     "attribute_name": "Bank",
#     "bank_name": "STATE BANK OF INDIA",
#     "bank_code": "5448",
#     "branch_name": "5729175282",
#     "branch_code": "528215",
#     "account_no": "6922150211",
#     "account_type": 1849,
#     "swift_code": "SBININBB123",
#     "iban_number": "IN91SBIN0001234",
#     "ifsc_code": "SBIN0001234",
#     "cash_credit_limit": 500000,
#     "bank_address": "123 MG Road Mumbai",
#     "account_ref_id": <FK ID>,
#     "is_default_bank": false,
#     "status": true
#   }
#
# FIELD KEY MAPPING:
#   bank_name          -> bank_name (text, uppercase only)
#   bank_code          -> bank_code (text, alphanumeric)
#   branch_name        -> branch_name (text, numeric per validation)
#   branch_code        -> branch_code (text, alphanumeric)
#   account_number     -> account_no (text, numeric)
#   account_type       -> account_type (FK: 1849=Current, 1850=Saving)
#   swift_number       -> swift_code (text, optional)
#   iban_number        -> iban_number (text, optional)
#   ifsc_code          -> ifsc_code (text, 11 chars)
#   cash_credit_limit  -> cash_credit_limit (numeric)
#   bank_address       -> bank_address (text, alphanumeric+spaces)
#   gl_account         -> account_ref_id (FK, placeholder)
#   is_default_bank    -> is_default_bank (boolean)
#   status             -> status (boolean)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── FK ID constants (verified on tenant 599) ────────────────────────────────
ACCOUNT_TYPE_IDS = {
    "Current": 1849,
    "Saving": 1850,
}

# ─── FK ID Placeholder (too many options, will fill from discovery) ──────────
ACCOUNT_REF_ID = None  # Placeholder — to be filled from discovery or live API

# ─── Realistic Indian bank data pool ─────────────────────────────────────────
REALISTIC_BANK_POOL = [
    {
        "bank_name": "STATE BANK OF INDIA",
        "bank_code": "0001",
        "branch_name": "0023456789",
        "branch_code": "SBIN01",
        "ifsc_code": "SBIN0000001",
        "swift_code": "SBININBB001",
        "iban_number": "IN91SBIN0000001",
        "bank_address": "1 Sansad Marg New Delhi",
    },
    {
        "bank_name": "HDFC BANK",
        "bank_code": "0248",
        "branch_name": "0034567891",
        "branch_code": "HDFC01",
        "ifsc_code": "HDFC0000001",
        "swift_code": "HDFCINBB001",
        "iban_number": "IN91HDFC0000001",
        "bank_address": "1 Ramdoot Sion Trombay Road Mumbai",
    },
    {
        "bank_name": "ICICI BANK",
        "bank_code": "0029",
        "branch_name": "0045678912",
        "branch_code": "ICIC01",
        "ifsc_code": "ICIC0000001",
        "swift_code": "ICICINBB001",
        "iban_number": "IN91ICIC0000001",
        "bank_address": "ICICI Bank Tower Bandra Kurla Complex Mumbai",
    },
    {
        "bank_name": "BANK OF BARODA",
        "bank_code": "0020",
        "branch_name": "0056789123",
        "branch_code": "BARB01",
        "ifsc_code": "BARB0000001",
        "swift_code": "BARBINBB001",
        "iban_number": "IN91BARB0000001",
        "bank_address": "12 Sayajigunj Vadodara Gujarat",
    },
    {
        "bank_name": "PUNJAB NATIONAL BANK",
        "bank_code": "0026",
        "branch_name": "0067891234",
        "branch_code": "PUNB01",
        "ifsc_code": "PUNB0000001",
        "swift_code": "PUNBINBB001",
        "iban_number": "IN91PUNB0000001",
        "bank_address": "7 Bhikaiji Cama Place New Delhi",
    },
    {
        "bank_name": "CANARA BANK",
        "bank_code": "0017",
        "branch_name": "0078912345",
        "branch_code": "CNRB01",
        "ifsc_code": "CNRB0000001",
        "swift_code": "CNRBINBB001",
        "iban_number": "IN91CNRB0000001",
        "bank_address": "14 JC Road Bangalore Karnataka",
    },
    {
        "bank_name": "UNION BANK OF INDIA",
        "bank_code": "0031",
        "branch_name": "0089123456",
        "branch_code": "UBIN01",
        "ifsc_code": "UBIN0000001",
        "swift_code": "UBININBB001",
        "iban_number": "IN91UBIN0000001",
        "bank_address": "239 Vidhan Bhavan Marg Mumbai",
    },
    {
        "bank_name": "BANK OF INDIA",
        "bank_code": "0022",
        "branch_name": "0091234567",
        "branch_code": "BKID01",
        "ifsc_code": "BKID0000001",
        "swift_code": "BKIDINBB001",
        "iban_number": "IN91BKID0000001",
        "bank_address": "Star House BKC Mumbai",
    },
    {
        "bank_name": "INDIAN BANK",
        "bank_code": "0033",
        "branch_name": "0012345678",
        "branch_code": "IDIB01",
        "ifsc_code": "IDIB0000001",
        "swift_code": "IDIBINBB001",
        "iban_number": "IN91IDIB0000001",
        "bank_address": "66 Mount Road Chennai Tamil Nadu",
    },
    {
        "bank_name": "CENTRAL BANK OF INDIA",
        "bank_code": "0019",
        "branch_name": "0023456780",
        "branch_code": "CBIN01",
        "ifsc_code": "CBIN0000001",
        "swift_code": "CBININBB001",
        "iban_number": "IN91CBIN0000001",
        "bank_address": "MG Road Fort Mumbai",
    },
    {
        "bank_name": "UCO BANK",
        "bank_code": "0030",
        "branch_name": "0034567801",
        "branch_code": "UCBA01",
        "ifsc_code": "UCBA0000001",
        "swift_code": "UCBAINBB001",
        "iban_number": "IN91UCBA0000001",
        "bank_address": "10 BTM Sarani Kolkata West Bengal",
    },
    {
        "bank_name": "INDIAN OVERSEAS BANK",
        "bank_code": "0032",
        "branch_name": "0045678012",
        "branch_code": "IOBA01",
        "ifsc_code": "IOBA0000001",
        "swift_code": "IOBAINBB001",
        "iban_number": "IN91IOBA0000001",
        "bank_address": "763 Anna Salai Chennai Tamil Nadu",
    },
    {
        "bank_name": "FEDERAL BANK",
        "bank_code": "0046",
        "branch_name": "0056780123",
        "branch_code": "FDRL01",
        "ifsc_code": "FDRL0000001",
        "swift_code": "FDRLINBB001",
        "iban_number": "IN91FDRL0000001",
        "bank_address": "Federal Towers Aluva Kerala",
    },
    {
        "bank_name": "KOTAK MAHINDRA BANK",
        "bank_code": "0999",
        "branch_name": "0067801234",
        "branch_code": "KKBK01",
        "ifsc_code": "KKBK0000001",
        "swift_code": "KKBKINBB001",
        "iban_number": "IN91KKBK0000001",
        "bank_address": "27 BKC Mumbai Maharashtra",
    },
    {
        "bank_name": "AXIS BANK",
        "bank_code": "0063",
        "branch_name": "0078012345",
        "branch_code": "UTIB01",
        "ifsc_code": "UTIB0000001",
        "swift_code": "AXISINBB001",
        "iban_number": "IN91UTIB0000001",
        "bank_address": "Axis House Worli Mumbai",
    },
    {
        "bank_name": "YES BANK",
        "bank_code": "0054",
        "branch_name": "0080123456",
        "branch_code": "YESB01",
        "ifsc_code": "YESB0000001",
        "swift_code": "YESBINBB001",
        "iban_number": "IN91YESB0000001",
        "bank_address": "Nehru Centre Worli Mumbai",
    },
    {
        "bank_name": "IDBI BANK",
        "bank_code": "0023",
        "branch_name": "0091234056",
        "branch_code": "IBKL01",
        "ifsc_code": "IBKL0000001",
        "swift_code": "IBKLINBB001",
        "iban_number": "IN91IBKL0000001",
        "bank_address": "IDBI Tower WTC Complex Mumbai",
    },
    {
        "bank_name": "BANDHAN BANK",
        "bank_code": "0078",
        "branch_name": "0012345067",
        "branch_code": "BDBL01",
        "ifsc_code": "BDBL0000001",
        "swift_code": "BDBLINBB001",
        "iban_number": "IN91BDBL0000001",
        "bank_address": "Bandhan Bank Tower Kolkata",
    },
    {
        "bank_name": "INDUSIND BANK",
        "bank_code": "0052",
        "branch_name": "0023456078",
        "branch_code": "INDB01",
        "ifsc_code": "INDB0000001",
        "swift_code": "INDBINBB001",
        "iban_number": "IN91INDB0000001",
        "bank_address": "IndusInd Tower Mumbai",
    },
    {
        "bank_name": "RBL BANK",
        "bank_code": "0061",
        "branch_name": "0034567089",
        "branch_code": "RATN01",
        "ifsc_code": "RATN0000001",
        "swift_code": "RATNINBB001",
        "iban_number": "IN91RATN0000001",
        "bank_address": "RBL House Kolbad Thane",
    },
]


def build_bank_api_payload(data: dict = None, dropdown_ids: dict = None) -> dict:
    """Build the Bank API payload from data + FK IDs.

    Args:
        data: Dict from generate_valid_bank_data() or None for random.
        dropdown_ids: Dict of FK IDs. Must contain 'account_type'
                      and 'account_ref_id'. Falls back to ACCOUNT_TYPE_IDS /
                      ACCOUNT_REF_ID placeholders.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    if data is None:
        data = generate_valid_bank_data()

    # Resolve FK IDs
    account_type_name = data.get("account_type", "Current")
    default_account_type_id = ACCOUNT_TYPE_IDS.get(account_type_name)

    ids = dropdown_ids or {}
    account_type_id = ids.get("account_type", default_account_type_id)
    account_ref_id = ids.get("account_ref_id", ACCOUNT_REF_ID)

    # Cash credit limit must be numeric
    try:
        cash_credit_limit = int(data.get("cash_credit_limit", generate_cash_credit_limit()))
    except (ValueError, TypeError):
        cash_credit_limit = int(generate_cash_credit_limit())

    payload = {
        "id": "",
        "attribute_name": "Bank",
        "bank_name": data.get("bank_name", generate_bank_name()),
        "bank_code": data.get("bank_code", generate_bank_code()),
        "branch_name": data.get("branch_name", generate_branch_name()),
        "branch_code": data.get("branch_code", generate_branch_code()),
        "account_no": data.get("account_number", generate_account_number()),
        "account_type": account_type_id,
        "swift_code": data.get("swift_number", generate_swift_number()) or None,
        "iban_number": data.get("iban_number", generate_iban_number()) or None,
        "ifsc_code": data.get("ifsc_code", generate_ifsc_code()),
        "cash_credit_limit": cash_credit_limit,
        "bank_address": data.get("bank_address", generate_bank_address()),
        "account_ref_id": account_ref_id,
        "is_default_bank": data.get("is_default_bank", False),
        "status": data.get("status", True),
    }
    return payload


def generate_bank_api_payload(name_prefix: str = None, dropdown_ids: dict = None) -> dict:
    """One-shot: generate a complete Bank API payload with realistic Indian data.

    Picks a random entry from REALISTIC_BANK_POOL for authentic Indian bank
    names, IFSC codes, and addresses. Generates fresh account numbers and
    other variable fields for uniqueness.

    Args:
        name_prefix: Ignored (Bank Name must be uppercase per validation).
                     Kept for API consistency.
        dropdown_ids: Override specific FK IDs (e.g., account_type, account_ref_id).

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    entry = random.choice(REALISTIC_BANK_POOL)

    data = {
        "bank_name": entry["bank_name"],
        "bank_code": entry["bank_code"],
        "branch_name": generate_branch_name(),  # Fresh numeric branch name per validation
        "branch_code": entry["branch_code"],
        "account_number": generate_account_number(),  # Fresh account number
        "account_type": random.choice(["Current", "Saving"]),
        "swift_number": entry.get("swift_code", generate_swift_number()),
        "iban_number": entry.get("iban_number", generate_iban_number()),
        "ifsc_code": generate_ifsc_code(entry["ifsc_code"][:4]),  # Use bank's IFSC prefix
        "cash_credit_limit": generate_cash_credit_limit(),
        "bank_address": entry["bank_address"],
        "gl_account": None,
        "is_default_bank": False,
        "status": True,
    }
    return build_bank_api_payload(data, dropdown_ids)


def generate_bank_api_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None) -> list:
    """Generate multiple unique Bank API payloads for batch creation.

    Picks unique entries from REALISTIC_BANK_POOL (without replacement).
    If count exceeds pool size, wraps around with fresh generated data.

    Args:
        count: Number of payloads to generate (default 20).
        prefix: Ignored (Bank Name must be uppercase per validation).
        dropdown_ids: Override specific FK IDs.

    Returns:
        List of JSON payloads.
    """
    pool = list(REALISTIC_BANK_POOL)
    random.shuffle(pool)

    payloads = []
    for i in range(count):
        if i < len(pool):
            entry = pool[i]
        else:
            entry = random.choice(REALISTIC_BANK_POOL)

        data = {
            "bank_name": entry["bank_name"],
            "bank_code": entry["bank_code"],
            "branch_name": generate_branch_name(),
            "branch_code": entry["branch_code"],
            "account_number": generate_account_number(),
            "account_type": random.choice(["Current", "Saving"]),
            "swift_number": entry.get("swift_code", generate_swift_number()),
            "iban_number": entry.get("iban_number", generate_iban_number()),
            "ifsc_code": generate_ifsc_code(entry["ifsc_code"][:4]),
            "cash_credit_limit": generate_cash_credit_limit(),
            "bank_address": entry["bank_address"],
            "gl_account": None,
            "is_default_bank": False,
            "status": True,
        }
        payloads.append(build_bank_api_payload(data, dropdown_ids))

    return payloads
