"""
constituent_documents_data.py
------------------------------
Test data & API payload builder for Rhythm ERP Constituent Documents screen.
Derived from live ERP schema at /core/dynamic-screen/Constituent%20Documents/ (tenant 711).

FIELD REFERENCE:

TOP-LEVEL FIELDS (persist via API):
  1. CIN No                 (character, required, UNIQUE)
     Pattern: ^[A-Z][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$
     Standard CIN (Corporate Identification Number) format
  2. CIN Date               (date, required)

DOCUMENTS STEPPER (grid with 2 fields per row — does NOT persist via API):
  1. Document Name          (dropdown, required) — FK to tbl_master (master_type='Document Name')
     12 options: Certificate Of Incorporation(1912), MOA(1913), AOA(1914), ...
  2. Upload File            (file, optional)

NOTE: The screen has no detail_table (detail_table_name=""), so grid child data
is silently dropped by the POST /core/dynamic-screen-wrapper/ endpoint.
Only top-level fields (cin_no, cin_date) are saved.
"""

import random
import string
from datetime import datetime, date


# ──────────────────────────────────────────────
# FK ID pools (from tbl_master, master_type='Document Name')
# Reference only — not used in payload since grid children don't persist
# ──────────────────────────────────────────────

DOCUMENT_NAME_IDS = [1912, 1913, 1914, 1915, 1916, 1917, 1918, 1919, 1920, 1921, 1922, 1923]
DOCUMENT_NAME_NAMES = {
    1912: "Certificate Of Incorporation",
    1913: "MOA",
    1914: "AOA",
    1915: "GST",
    1916: "PAN",
    1917: "Address Proof",
    1918: "Audited Balance Sheet (Last 2 Years)",
    1919: "Income Tax - Last 2 Years (If available)",
    1920: "Bank Account Details",
    1921: "Bank Statement (Last 1 Year)",
    1922: "Loan Statement",
    1923: "Attachments",
}

DEFAULT_FK_IDS = {
    "document_name": 1912,
}


# ──────────────────────────────────────────────
# Data generators
# ──────────────────────────────────────────────

_generated_cins = set()


def generate_cin_no():
    """Generate a valid CIN number.

    Pattern: ^[A-Z][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$
    Format: L12345AB1234XYZ123456
    """
    for _ in range(500):
        cin = (
            random.choice(string.ascii_uppercase)
            + "".join(random.choices(string.digits, k=5))
            + "".join(random.choices(string.ascii_uppercase, k=2))
            + "".join(random.choices(string.digits, k=4))
            + "".join(random.choices(string.ascii_uppercase, k=3))
            + "".join(random.choices(string.digits, k=6))
        )
        if cin not in _generated_cins:
            _generated_cins.add(cin)
            return cin
    fallback = "L" + datetime.now().strftime("%m%d1") + "AB" + datetime.now().strftime("%y%M") + "XYZ" + "9".join(random.choices(string.digits, k=5))
    _generated_cins.add(fallback)
    return fallback


def generate_date_string(days_ago_range=730):
    today = date.today()
    days_back = random.randint(1, days_ago_range)
    d = today - __import__("datetime").timedelta(days=days_back)
    return f"{d.strftime('%Y-%m-%d')}T18:30:00Z"


# ──────────────────────────────────────────────
# Valid data
# ──────────────────────────────────────────────

def generate_valid_data():
    """Generate complete valid data for the Constituent Documents form.

    Only top-level fields — grid children are excluded since they don't persist.
    """
    return {
        "cin_no": generate_cin_no(),
        "cin_date": generate_date_string(),
    }


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────

def build_api_payload(data=None):
    """Build JSON payload for POST /core/dynamic-screen-wrapper/.

    Args:
        data: Dict from generate_valid_data(). If None, auto-generates.

    Returns:
        Complete JSON payload dict ready for POST.
    """
    if data is None:
        data = generate_valid_data()

    payload = {
        "id": "",
        "attribute_name": "Constituent Documents",
        "cin_no": data.get("cin_no") or generate_cin_no(),
        "cin_date": data.get("cin_date") or generate_date_string(),
        "details": [],
    }

    return payload


def generate_api_payload(**kwargs):
    """One-shot: generate a randomized Constituent Documents API payload."""
    data = generate_valid_data()
    payload = build_api_payload(data)
    payload.update(kwargs)
    return payload


def generate_batch_payloads(count, offset=0, **kwargs):
    """Generate multiple unique Constituent Documents API payloads."""
    payloads = []
    for i in range(count):
        p = generate_api_payload(**kwargs)
        payloads.append(p)
    return payloads
