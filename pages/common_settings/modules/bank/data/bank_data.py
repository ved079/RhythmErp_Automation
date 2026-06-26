#!/usr/bin/env python3
"""
Bank — Data pool + API payload builder.

Screen: "Bank" (flat, 2 FK dropdowns: account_type, account_ref_id)
Fields: bank_name, bank_code, branch_name, branch_code, account_number,
        account_type, swift_number, iban_number, ifsc_code,
        cash_credit_limit, bank_address, account_ref_id,
        is_default_bank, status

Discovered FK IDs (2026-06-02):
  account_type:     Current=1849, Saving=1850
  account_ref_id:   116 chart of accounts (Cash=767, BANK 1=1005, etc.)
"""

import random
import string

# ── Field length constraints ──────────────────────────────────────────
BANK_NAME_MAX_LENGTH = 255   # frontend caps at 255
BANK_NAME_MIN_LENGTH = 10    # frontend enforces minimum 10 chars

# ── Real FK IDs from live ERP ────────────────────────────────────────
ACCOUNT_TYPE_IDS = {
    "Current": 1849,
    "Saving":  1850,
}

# Selected account_ref_id values (chart of accounts) — bank-related ones
ACCOUNT_REF_IDS = {
    "BANK 1":                          1005,
    "BANK 2":                          778,
    "BANK 3":                          777,
    "BANK 4":                          776,
    "BANK 5":                          775,
    "Cash":                             767,
    "Bank Charges":                     863,
    "FD in Bank":                       23,
    "Central Bank of India Loan A/c":  34,
    "Bank of Maharashtra TL":          35,
}

# ── Realistic data pools ─────────────────────────────────────────────

BANKS = [
    {"name": "State Bank of India",            "code": "0001",  "branch": "Fort, Mumbai",      "ifsc": "SBIN0000300"},
    {"name": "HDFC Bank",                      "code": "0002", "branch": "Churchgate, Mumbai", "ifsc": "HDFC0000060"},
    {"name": "ICICI Bank",                     "code": "0003", "branch": "BKC, Mumbai",        "ifsc": "ICIC0000002"},
    {"name": "Punjab National Bank",           "code": "0004", "branch": "Connaught Place",    "ifsc": "PUNB0000500"},
    {"name": "Bank of Baroda",                 "code": "0005", "branch": "Alkapuri, Vadodara", "ifsc": "BARB0ALKA01"},
    {"name": "Canara Bank",                    "code": "0006", "branch": "Jayanagar, Bangalore","ifsc": "CNRB0000250"},
    {"name": "Union Bank of India",            "code": "0007", "branch": "Nariman Point",      "ifsc": "UBIN0530000"},
    {"name": "Axis Bank",                      "code": "0008", "branch": "MG Road, Pune",      "ifsc": "UTIB0000100"},
    {"name": "Bank of India",                  "code": "0009", "branch": "Star House, Mumbai", "ifsc": "BKID0000001"},
    {"name": "Central Bank of India",          "code": "0010", "branch": "Chanderi, Bhopal",   "ifsc": "CBIN0280001"},
    {"name": "Indian Bank",                    "code": "0011", "branch": "Mount Road, Chennai","ifsc": "IDIB000M001"},
    {"name": "Kotak Mahindra Bank",            "code": "0012", "branch": "BKC, Mumbai",        "ifsc": "KKBK0000100"},
    {"name": "IndusInd Bank",                  "code": "0013", "branch": "Elphinstone, Mumbai","ifsc": "INDB0000001"},
    {"name": "Yes Bank",                       "code": "0014", "branch": "Nehru Place, Delhi", "ifsc": "YESB0000001"},
    {"name": "Federal Bank",                   "code": "0015", "branch": "Aluva, Kerala",      "ifsc": "FDRL0000001"},
    {"name": "South Indian Bank",              "code": "0016", "branch": "Thrissur, Kerala",   "ifsc": "SIBL0000001"},
    {"name": "IDFC First Bank",                "code": "0017", "branch": "Nungambakkam, Chennai","ifsc":"IDFB0000001"},
    {"name": "Bandhan Bank",                   "code": "0018", "branch": "Salt Lake, Kolkata", "ifsc": "BDBL0000001"},
    {"name": "RBL Bank",                       "code": "0019", "branch": "BKC, Mumbai",        "ifsc": "RATN0000001"},
    {"name": "UCO Bank",                       "code": "0020", "branch": "Brabourne, Kolkata", "ifsc": "UCBA0000001"},
]

BRANCH_CODES = ["BR0001", "BR0002", "BR0003", "BR0004", "BR0005",
                "BR0006", "BR0007", "BR0008", "BR0009", "BR0010"]

BANK_ACCOUNT_REFS = ["BANK 1", "BANK 2", "BANK 3", "BANK 4", "BANK 5"]


def _gen_account_number():
    """Generate a realistic 12-digit account number."""
    return ''.join(random.choices(string.digits, k=12))

def _gen_swift():
    """Generate a SWIFT code (11 chars: letters only, like MXBZNYSHTDI).
    ERP validates swift_number as letters-only (A-Z a-z)."""
    return ''.join(random.choices(string.ascii_uppercase, k=11))


# ── Payload builder ──────────────────────────────────────────────────

def build_bank_api_payload(bank_name, bank_code, branch_name, branch_code,
                           account_number, account_type_id, swift_number="",
                           iban_number="", ifsc_code="", cash_credit_limit=None,
                           bank_address="", account_ref_id=None,
                           is_default_bank=False, status=True):
    """Build a single API payload for Bank."""
    payload = {
        "id": "",
        "bank_name": bank_name,
        "bank_code": bank_code,
        "branch_name": branch_name,
        "branch_code": branch_code,
        "account_number": account_number,
        "account_type": account_type_id,
        "swift_number": swift_number,
        "iban_number": iban_number,
        "ifsc_code": ifsc_code,
        "cash_credit_limit": cash_credit_limit,
        "bank_address": bank_address,
        "is_default_bank": is_default_bank,
        "status": status,
        "attribute_name": "Bank",
    }
    if account_ref_id is not None:
        payload["account_ref_id"] = account_ref_id
    return payload


def generate_bank_api_payloads(count=10, offset=0, fk_ids=None):
    """
    Generate N API payloads for Bank.
    """
    if fk_ids is None:
        fk_ids = {}

    # Merge FK IDs
    account_type_ids = {**ACCOUNT_TYPE_IDS, **fk_ids.get("account_type", {})}
    account_ref_ids = {**ACCOUNT_REF_IDS, **fk_ids.get("account_ref_id", {})}

    payloads = []

    for i in range(count):
        idx = (offset + i) % len(BANKS)
        entry = BANKS[idx]

        # Alternate between Current and Saving
        acct_type_name = "Current" if i % 2 == 0 else "Saving"
        acct_type_id = account_type_ids.get(acct_type_name, 1849)

        # Pick a bank account ref (cycle through BANK 1-5)
        ref_name = BANK_ACCOUNT_REFS[i % len(BANK_ACCOUNT_REFS)]
        acct_ref_id = account_ref_ids.get(ref_name)
        if acct_ref_id is None and account_ref_ids:
            acct_ref_id = list(account_ref_ids.values())[i % len(account_ref_ids)]

        # Credit limit for all account types
        credit_limit = random.choice([500000, 1000000, 2000000, 5000000, 10000000])

        bank_address = f"{entry['branch']}, {entry['name']}"

        payload = build_bank_api_payload(
            bank_name=entry["name"],
            bank_code=entry["code"],
            branch_name=entry["branch"],
            branch_code=BRANCH_CODES[i % len(BRANCH_CODES)],
            account_number=_gen_account_number(),
            account_type_id=acct_type_id,
            swift_number=_gen_swift(),
            iban_number="",
            ifsc_code=entry["ifsc"],
            cash_credit_limit=credit_limit,
            bank_address=bank_address,
            account_ref_id=acct_ref_id,
            is_default_bank=(i == 0),
            status=True,
        )
        payloads.append(payload)

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Bank is a flat screen — no children, no steppers.
# 12 text/number fields + 2 FK dropdowns + 2 toggles = 14 fields total.

def get_field_validation_rules(fk_ids=None):
    """Return validation rules dict with dynamic fk_options_count from FK-resolved data."""
    acct_type_count = len(fk_ids.get("account_type", {})) if fk_ids else len(ACCOUNT_TYPE_IDS)
    acct_ref_count = len(fk_ids.get("account_ref_id", {})) if fk_ids else len(ACCOUNT_REF_IDS)
    return {
        "bank_name": {
            "type": "character", "required": True, "max_length": 255,
            "note": "Uppercase alpha only, >= 10 chars. Frontend rejects special chars.",
        },
        "bank_code": {
            "type": "character", "required": True, "max_length": 255,
            "note": "ONLY 4-digit integer accepted (e.g., 1234). No letters, no special chars.",
        },
        "branch_name": {
            "type": "character", "required": True, "max_length": 255,
        },
        "branch_code": {
            "type": "character", "required": True, "max_length": 255,
        },
        "account_number": {
            "type": "character", "required": True, "max_length": 255,
            "note": "Numeric input (type='character' but accepts digits).",
        },
        "swift_number": {
            "type": "character", "required": False, "max_length": 255,
            "note": "Optional. Letters-only format (e.g., MXBZNYSHTDI). No digits or special chars.",
        },
        "iban_number": {
            "type": "character", "required": False, "max_length": 255,
            "note": "Optional. IBAN format.",
        },
        "ifsc_code": {
            "type": "character", "required": True, "max_length": 255,
            "note": "Exactly 11 chars in standard IFSC format.",
        },
        "cash_credit_limit": {
            "type": "character", "required": True, "max_length": 255,
            "note": "Numeric value. Required for Current accounts, can be None for Saving.",
        },
        "bank_address": {
            "type": "character", "required": True, "max_length": 255,
        },
        "account_type": {
            "type": "dropdown", "required": True,
            "fk_options_count": acct_type_count,
            "note": "2 options: Current (1849), Saving (1850).",
        },
        "account_ref_id": {
            "type": "dropdown", "required": True,
            "fk_options_count": acct_ref_count,
            "note": "GL Account / Chart of Accounts.",
        },
        "is_default_bank": {
            "type": "toggle", "required": False, "default": False,
            "note": "Default: No (OFF).",
        },
        "status": {
            "type": "toggle", "required": False, "default": True,
            "note": "Default: Active (ON). Boolean in API payload.",
        },
    }


# Backward-compat constant
FIELD_VALIDATION_RULES = get_field_validation_rules()

# Status toggle options (display name -> API boolean value)
STATUS_OPTIONS = {
    "Active": True,
    "Inactive": False,
}

SCREEN_NAME_FIELDS = {
    "account_type": "Account Type",
    "account_ref_id": "Account",
}


def get_fk_screen_mapping():
    """Declare which FK dropdown fields need live resolution from which ERP screen."""
    return dict(SCREEN_NAME_FIELDS)


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
    offset: int = 0,
    existing_entries: list = None,
) -> list:
    """Generate a batch of unique Bank API payloads.

    Standardized batch generator matching the pattern used across all
    RhythmERP modules (Customer, Supplier, Company Onboarding, etc.).

    Args:
        count: Number of payloads to generate.
        prefix: Ignored for Bank (realistic bank names are used instead).
        dropdown_ids: Override specific FK ID pools.

    Returns:
        List of JSON payloads ready for POST /core/dynamic-screen-wrapper/
    """
    return generate_bank_api_payloads(count=count, fk_ids=dropdown_ids)


# ── UI Validation Helpers (restored for test compatibility) ──

# Validation message constants
VALIDATION_MSG_REQUIRED = "This field is required"
VALIDATION_MSG_INVALID_BANK_NAME = "Invalid Bank Name"
VALIDATION_MSG_INVALID_BANK_CODE = "Invalid Bank Code"
VALIDATION_MSG_INVALID_BRANCH_NAME = "Invalid Branch Name"
VALIDATION_MSG_INVALID_IFSC = "Invalid IFSC Code"
VALIDATION_MSG_INVALID_SWIFT = "Invalid Swift Number"
VALIDATION_MSG_INVALID_IBAN = "Invalid IBAN Number"
SWAL_TITLE_VALIDATION_FAILED = "Validation Failed"
SWAL_TITLE_SUCCESS = "Success"

_bnk_counter = 0

def _bnk_next():
    global _bnk_counter
    _bnk_counter += 1
    return _bnk_counter

def generate_bank_name(prefix="BANK"):
    """Return a valid alpha-only bank name (A-Z a-z only, >= 10 chars).
    ERP validates bank_name as character type — only A-Z a-z accepted."""
    n = _bnk_next()
    # Convert counter to letter-based suffix to avoid digits
    # e.g., 1 -> A, 2 -> B, 27 -> AA, 28 -> AB
    suffix = ""
    val = n
    while val > 0:
        val -= 1
        suffix = chr(ord('A') + (val % 26)) + suffix
        val //= 26
    # Build alpha-only name
    clean_prefix = "".join(c for c in prefix if c.isalpha()) or "BANK"
    base = f"{clean_prefix}{suffix}XXNM"
    if len(base) < 10:
        base = base + "X" * (10 - len(base))
    return base.upper()


def generate_bank_code():
    """Return a valid 4-digit integer bank code (e.g., '1234').
    ERP validates bank_code as ONLY 4-digit integer — no less, no more, no chars/special."""
    n = _bnk_next()
    # Ensure exactly 4 digits: cycle through 0001-9999
    code_num = ((n - 1) % 9999) + 1
    return f"{code_num:04d}"


def generate_branch_name():
    """Return a valid branch name (alphanumeric)."""
    n = _bnk_next()
    return f"Branch-{n:04d}"


def generate_branch_code():
    """Return a valid branch code."""
    n = _bnk_next()
    return f"BR{n:04d}"


def generate_account_number():
    """Return a valid 12-digit account number."""
    return ''.join(random.choices(string.digits, k=12))


def generate_ifsc_code():
    """Return a valid 11-char IFSC code."""
    bank = ''.join(random.choices(string.ascii_uppercase, k=4))
    branch = ''.join(random.choices(string.digits, k=6))
    return f"{bank}0{branch}"


def generate_cash_credit_limit():
    """Return a valid cash credit limit string."""
    return str(random.choice([500000, 1000000, 2000000, 5000000]))


def generate_bank_address():
    """Return a valid bank address string."""
    n = _bnk_next()
    return f"Auto Test Address {n}, Mumbai"


def generate_swift_number():
    """Return a valid SWIFT/BIC code (8 or 11 chars)."""
    return _gen_swift()


def generate_iban_number():
    """Return a valid IBAN number."""
    bank = ''.join(random.choices(string.digits, k=10))
    return f"IN{random.randint(10, 99)}BANK{bank}"


def generate_spaces_only():
    """Return spaces-only string for validation testing."""
    return "     "


def generate_string_255():
    """Return a string of exactly 255 characters."""
    return "A" * 255


def generate_string_256():
    """Return a string of exactly 256 characters."""
    return "A" * 256


def generate_special_char_name():
    """Return a bank name with special characters (invalid)."""
    return "BANK@#$%^TEST"


def generate_special_char_value():
    """Return a value with special characters (invalid)."""
    return "@#$%^&*!"


def generate_sql_injection():
    """Return a SQL injection payload string."""
    return "' OR 1=1; --"


def generate_xss_payload():
    """Return an XSS payload string."""
    return '<script>alert("XSS")</script>'


def generate_negative_limit():
    """Return a negative cash credit limit string."""
    return "-5000"


def generate_zero_limit():
    """Return a zero cash credit limit string."""
    return "0"


def generate_alpha_limit():
    """Return an alphabetic cash credit limit string (invalid)."""
    return "abcde"


def generate_special_char_limit():
    """Return a special character cash credit limit string (invalid)."""
    return "@#$%"


def generate_limit_with_spaces():
    """Return a cash credit limit with spaces (invalid)."""
    return "100 000"


def generate_leading_trailing_spaces():
    """Return a bank name with leading/trailing spaces."""
    return "  BANKTESTXX  "


def generate_lowercase_bank_name():
    """Return a lowercase bank name (invalid per validation rules)."""
    return "banktestlow"


def generate_bank_name_with_digits():
    """Return a bank name with digits (invalid per alpha-only rule).
    ERP only accepts A-Z a-z in bank_name."""
    return "BANK123TEST"


def generate_bank_name_too_short():
    """Return a bank name shorter than 10 chars (invalid)."""
    return "SHORT"


def generate_ifsc_too_short():
    """Return an IFSC code shorter than 11 chars."""
    return "SBIN0003"


def generate_ifsc_too_long():
    """Return an IFSC code longer than 11 chars."""
    return "SBIN00003003"


def generate_alpha_branch_name():
    """Return an all-alpha branch name."""
    return "MAINBRANCHX"


def generate_alpha_account_number():
    """Return an all-alpha account number (invalid)."""
    return "ABCDEF12345"


def generate_valid_bank_data(prefix="AUTO"):
    """Return a complete valid bank data dict for create_bank."""
    n = _bnk_next()
    return {
        "bank_name": generate_bank_name(prefix),
        "bank_code": generate_bank_code(),
        "branch_name": generate_branch_name(),
        "branch_code": generate_branch_code(),
        "account_number": generate_account_number(),
        "account_type": random.choice(list(ACCOUNT_TYPE_IDS.keys())),
        "swift_number": generate_swift_number(),
        "iban_number": generate_iban_number(),
        "ifsc_code": generate_ifsc_code(),
        "cash_credit_limit": generate_cash_credit_limit(),
        "bank_address": generate_bank_address(),
        "gl_account": random.choice(list(ACCOUNT_REF_IDS.keys())),
        "is_default_bank": False,
        "status": True,
    }


def generate_valid_edit_data():
    """Return a dict with editable fields for edit_record."""
    return {
        "bank_code": generate_bank_code(),
        "branch_name": generate_branch_name(),
        "branch_code": generate_branch_code(),
        "bank_address": generate_bank_address(),
    }


def generate_empty_data():
    """Return a dict with all required fields empty."""
    return {
        "bank_name": "",
        "bank_code": "",
        "branch_name": "",
        "branch_code": "",
        "account_number": "",
        "account_type": "",
        "ifsc_code": "",
        "cash_credit_limit": "",
        "bank_address": "",
        "gl_account": "",
    }


def generate_partial_required_data():
    """Return a dict with only some required fields filled."""
    return {
        "bank_name": generate_bank_name(),
        "bank_code": generate_bank_code(),
        "branch_name": "",
        "branch_code": "",
        "account_number": "",
        "account_type": "",
        "ifsc_code": "",
        "cash_credit_limit": "",
        "bank_address": "",
        "gl_account": "",
    }
