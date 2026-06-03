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
    {"name": "State Bank of India",            "code": "SBI",  "branch": "Fort, Mumbai",      "ifsc": "SBIN0000300"},
    {"name": "HDFC Bank",                      "code": "HDFC", "branch": "Churchgate, Mumbai", "ifsc": "HDFC0000060"},
    {"name": "ICICI Bank",                     "code": "ICIC", "branch": "BKC, Mumbai",        "ifsc": "ICIC0000002"},
    {"name": "Punjab National Bank",           "code": "PUNB", "branch": "Connaught Place",    "ifsc": "PUNB0000500"},
    {"name": "Bank of Baroda",                 "code": "BARB", "branch": "Alkapuri, Vadodara", "ifsc": "BARB0ALKA01"},
    {"name": "Canara Bank",                    "code": "CNRB", "branch": "Jayanagar, Bangalore","ifsc": "CNRB0000250"},
    {"name": "Union Bank of India",            "code": "UBIN", "branch": "Nariman Point",      "ifsc": "UBIN0530000"},
    {"name": "Axis Bank",                      "code": "UTIB", "branch": "MG Road, Pune",      "ifsc": "UTIB0000100"},
    {"name": "Bank of India",                  "code": "BKID", "branch": "Star House, Mumbai", "ifsc": "BKID0000001"},
    {"name": "Central Bank of India",          "code": "CBIN", "branch": "Chanderi, Bhopal",   "ifsc": "CBIN0280001"},
    {"name": "Indian Bank",                    "code": "IDIB", "branch": "Mount Road, Chennai","ifsc": "IDIB000M001"},
    {"name": "Kotak Mahindra Bank",            "code": "KKBK", "branch": "BKC, Mumbai",        "ifsc": "KKBK0000100"},
    {"name": "IndusInd Bank",                  "code": "INDB", "branch": "Elphinstone, Mumbai","ifsc": "INDB0000001"},
    {"name": "Yes Bank",                       "code": "YESB", "branch": "Nehru Place, Delhi", "ifsc": "YESB0000001"},
    {"name": "Federal Bank",                   "code": "FDRL", "branch": "Aluva, Kerala",      "ifsc": "FDRL0000001"},
    {"name": "South Indian Bank",              "code": "SIBL", "branch": "Thrissur, Kerala",   "ifsc": "SIBL0000001"},
    {"name": "IDFC First Bank",                "code": "IDFB", "branch": "Nungambakkam, Chennai","ifsc":"IDFB0000001"},
    {"name": "Bandhan Bank",                   "code": "BDBL", "branch": "Salt Lake, Kolkata", "ifsc": "BDBL0000001"},
    {"name": "RBL Bank",                       "code": "RATN", "branch": "BKC, Mumbai",        "ifsc": "RATN0000001"},
    {"name": "UCO Bank",                       "code": "UCBA", "branch": "Brabourne, Kolkata", "ifsc": "UCBA0000001"},
]

BRANCH_CODES = ["BR001", "BR002", "BR003", "BR004", "BR005",
                "BR006", "BR007", "BR008", "BR009", "BR010"]

BANK_ACCOUNT_REFS = ["BANK 1", "BANK 2", "BANK 3", "BANK 4", "BANK 5"]


def _gen_account_number():
    """Generate a realistic 12-digit account number."""
    return ''.join(random.choices(string.digits, k=12))

def _gen_swift():
    """Generate a SWIFT code (8 chars: 4 bank + 2 country + 2 location)."""
    bank = ''.join(random.choices(string.ascii_uppercase, k=4))
    return f"{bank}IN{random.choice('MM')}"


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


def generate_bank_api_payloads(count=10, fk_ids=None):
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
        entry = BANKS[i % len(BANKS)]

        # Alternate between Current and Saving
        acct_type_name = "Current" if i % 2 == 0 else "Saving"
        acct_type_id = account_type_ids.get(acct_type_name, 1849)

        # Pick a bank account ref (cycle through BANK 1-5)
        ref_name = BANK_ACCOUNT_REFS[i % len(BANK_ACCOUNT_REFS)]
        acct_ref_id = account_ref_ids.get(ref_name)
        if acct_ref_id is None and account_ref_ids:
            acct_ref_id = list(account_ref_ids.values())[i % len(account_ref_ids)]

        # Credit limit varies by account type
        if acct_type_name == "Current":
            credit_limit = random.choice([500000, 1000000, 2000000, 5000000, 10000000])
        else:
            credit_limit = None

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

FIELD_VALIDATION_RULES = {
    # Text fields
    "bank_name": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Uppercase alpha only, >= 10 chars. Frontend rejects special chars.",
    },
    "bank_code": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Alphanumeric accepted.",
    },
    "branch_name": {
        "type": "character",
        "required": True,
        "max_length": 255,
    },
    "branch_code": {
        "type": "character",
        "required": True,
        "max_length": 255,
    },
    "account_number": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Numeric input (type='character' but accepts digits).",
    },
    "swift_number": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "Optional. SWIFT/BIC format.",
    },
    "iban_number": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "Optional. IBAN format.",
    },
    "ifsc_code": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Exactly 11 chars in standard IFSC format.",
    },
    "cash_credit_limit": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Numeric value. Required for Current accounts, can be None for Saving.",
    },
    "bank_address": {
        "type": "character",
        "required": True,
        "max_length": 255,
    },

    # FK Dropdowns
    "account_type": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(ACCOUNT_TYPE_IDS),
        "note": "2 options: Current (1849), Saving (1850).",
    },
    "account_ref_id": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(ACCOUNT_REF_IDS),
        "note": "GL Account / Chart of Accounts. ~10 bank-related options in our pool.",
    },

    # Toggles
    "is_default_bank": {
        "type": "toggle",
        "required": False,
        "default": False,
        "note": "Default: No (OFF).",
    },
    "status": {
        "type": "toggle",
        "required": False,
        "default": True,
        "note": "Default: Active (ON). Boolean in API payload.",
    },
}

# Status toggle options (display name -> API boolean value)
STATUS_OPTIONS = {
    "Active": True,
    "Inactive": False,
}

# Account Type display names for schema tests
ACCOUNT_TYPE_NAMES = dict(ACCOUNT_TYPE_IDS)

# GL Account display names for schema tests
ACCOUNT_REF_NAMES = dict(ACCOUNT_REF_IDS)

# Default FK IDs for Bank (standardized naming pattern)
DEFAULT_BANK_FK_IDS = {
    "account_type": ACCOUNT_TYPE_IDS,
    "account_ref_id": ACCOUNT_REF_IDS,
}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
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
