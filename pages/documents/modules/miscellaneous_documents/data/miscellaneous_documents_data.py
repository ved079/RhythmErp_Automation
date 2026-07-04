"""
miscellaneous_documents_data.py
--------------------------------
Test data & API payload builder for Rhythm ERP Miscellaneous Documents screen.
Derived from live ERP schema at /core/dynamic-screen/Miscellaneous%20Documents/ (tenant 711).

FIELD REFERENCE (6 top-level fields, no steppers):

  1. name              Document Name     (character, required, UNIQUE)
     Pattern: ^[A-Za-z0-9&.,()_/\\\\- ]+$
  2. document_no       Document Number   (integer, required, UNIQUE)
     Pattern: ^[A-Za-z0-9._/\\\\- ]+$
  3. registered_date   Registered Date   (date, required)
  4. expiry_date       Expiry Date       (date, optional)
  5. brief_details     Brief Details     (text, required)
  6. attachment        Document Attachment (file, optional)
"""

import random
import string
from datetime import datetime, date, timedelta

# ──────────────────────────────────────────────
# SweetAlert titles (used by UI tests)
# ──────────────────────────────────────────────
SWAL_TITLE_SUCCESS = "Your record has been added successfully!"
SWAL_TITLE_VALIDATION_FAILED = "Validation Failed"
SWAL_TITLE_UPDATED = "Your record has been updated successfully!"


# ──────────────────────────────────────────────
# Name pools
# ──────────────────────────────────────────────

DOCUMENT_NAMES = [
    "Certificate Of Incorporation",
    "MOA",
    "AOA",
    "GST",
    "PAN",
    "Address Proof",
    "Audited Balance Sheet",
    "Income Tax Returns",
    "Bank Account Details",
    "Bank Statement",
    "Loan Statement",
    "Project Report",
    "Board Resolution",
    "Share Certificate",
    "Partnership Deed",
    "Registration Certificate",
    "Insurance Policy",
    "Property Deed",
    "NOC Letter",
    "KYC Document",
]

_generated_names = set()
_generated_doc_nos = set()


# ──────────────────────────────────────────────
# Data generators
# ──────────────────────────────────────────────

def generate_name():
    """Generate a unique Document Name."""
    for _ in range(200):
        prefix = random.choice(DOCUMENT_NAMES)
        suffix = "".join(random.choices(string.ascii_uppercase, k=4))
        name = f"{prefix} - {suffix}"
        if name not in _generated_names:
            _generated_names.add(name)
            return name
    name = f"Document - {datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    _generated_names.add(name)
    return name


def generate_document_no():
    """Generate a unique document number."""
    for _ in range(500):
        doc_no = random.randint(10000, 99999)
        if doc_no not in _generated_doc_nos:
            _generated_doc_nos.add(doc_no)
            return doc_no
    doc_no = random.randint(100000, 999999)
    _generated_doc_nos.add(doc_no)
    return doc_no


def generate_date_string(days_ago_range=730):
    today = date.today()
    days_back = random.randint(1, days_ago_range)
    d = today - timedelta(days=days_back)
    return f"{d.strftime('%Y-%m-%d')}T18:30:00Z"


def generate_expiry_date_string(from_date_str=None):
    today = date.today()
    if from_date_str:
        d = datetime.strptime(from_date_str[:10], "%Y-%m-%d").date()
    else:
        d = today
    days_forward = random.randint(30, 1825)
    d = d + timedelta(days=days_forward)
    return f"{d.strftime('%Y-%m-%d')}T18:30:00Z"


def generate_brief_details():
    templates = [
        "Document for {} record",
        "{} related to business operations",
        "Supporting document for {}",
        "Official {} as per regulatory requirements",
        "Certified copy of {}",
        "Original {} submitted for verification",
    ]
    template = random.choice(templates)
    doc_type = random.choice(DOCUMENT_NAMES).lower()
    return template.format(doc_type)[:255]


# ──────────────────────────────────────────────
# Valid data
# ──────────────────────────────────────────────

def generate_valid_data():
    """Generate complete valid data for the Miscellaneous Documents form."""
    reg_date = generate_date_string()
    return {
        "name": generate_name(),
        "document_no": generate_document_no(),
        "registered_date": reg_date,
        "expiry_date": generate_expiry_date_string(reg_date),
        "brief_details": generate_brief_details(),
        "attachment": None,
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
        "attribute_name": "Miscellaneous Documents",
        "name": data.get("name") or generate_name(),
        "document_no": data.get("document_no") or generate_document_no(),
        "registered_date": data.get("registered_date") or generate_date_string(),
        "expiry_date": data.get("expiry_date"),
        "brief_details": data.get("brief_details") or generate_brief_details(),
        "attachment": data.get("attachment"),
    }

    return payload


def generate_api_payload(**kwargs):
    """One-shot: generate a randomized Miscellaneous Documents API payload."""
    data = generate_valid_data()
    payload = build_api_payload(data)
    payload.update(kwargs)
    return payload


def generate_batch_payloads(count, offset=0, **kwargs):
    """Generate multiple unique Miscellaneous Documents API payloads."""
    payloads = []
    for i in range(count):
        p = generate_api_payload(**kwargs)
        payloads.append(p)
    return payloads


def generate_ui_form_data():
    """UI-friendly form data dict for fill_form().

    document_no is stringified (UI input takes text).
    """
    data = generate_valid_data()
    data["document_no"] = str(data["document_no"])
    return data
