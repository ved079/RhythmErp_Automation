"""
register_of_loan_data.py
-------------------------
Test data & API payload builder for Rhythm ERP Register of Loan screen.
Derived from live ERP schema at /core/dynamic-screen/Register%20of%20Loan/ (tenant 711).

FIELD REFERENCE (flat form — no steppers):

  1. Loan Details             (file, optional)
  2. Sanction Date            (date, required)
  3. Bank Name                (character, required)
     Pattern: ^[A-Za-z ]+$  — letters and spaces only
  4. Sanction Amount          (integer, required)
     Pattern: ^(?!.*[+-])[0-9]+(\\.[0-9]{1,4})?$  — positive, up to 4 decimals
  5. Facility Details         (dropdown, required) — FK to tbl_master (master_type='Loan Type')
     Options: CC(652), Term Loan(651), Non Funded(1547)
  6. Disbursement Amount      (integer, required)
  7. EMI/Servicing Date       (date, required)
  8. Instalment Amount        (integer, required)
     Pattern: ^(?!.*[+-])[0-9]+(\\.[0-9]{1,4})?$  — positive, up to 4 decimals
  9. Reminder period (in days) (integer, required)
     Pattern: ^[1-9]\\d*$  — positive integer, no leading zero
  10. EMI Period              (dropdown, required) — FK to tbl_master (master_type='EMI Period')
      Options: Monthly(1528), Quaterly(1529), Half Yearly(1530), Yearly(1531)
  11. Outstanding Date        (date, optional)
  12. Outstanding Amount      (integer, required)
  13. Is notification applicable? (checkbox, optional)

ENDPOINTS:
  Schema:  GET  /core/dynamic-screen/Register%20of%20Loan/
  List:    GET  /core/dynamic-screen-wrapper/Register%20of%20Loan/
  Create:  POST /core/dynamic-screen-wrapper/
"""

import random
from datetime import datetime, date


# ──────────────────────────────────────────────
# FK ID pools (verified on tenant 711, 2026-06-12)
# ──────────────────────────────────────────────

# Facility Details (Loan Type) — from tbl_master (master_type='Loan Type')
FACILITY_DETAILS_IDS = [652, 651, 1547]
FACILITY_DETAILS_NAMES = {
    652: "CC",
    651: "Term Loan",
    1547: "Non Funded",
}

# EMI Period — from tbl_master (master_type='EMI Period')
EMI_PERIOD_IDS = [1528, 1529, 1530, 1531]
EMI_PERIOD_NAMES = {
    1528: "Monthly",
    1529: "Quaterly",
    1530: "Half Yearly",
    1531: "Yearly",
}

DEFAULT_FK_IDS = {
    "facility_details_ref_id": 652,
    "emi_period": 1528,
}


# ──────────────────────────────────────────────
# Realistic data pools
# ──────────────────────────────────────────────

_BANK_NAMES = [
    "State Bank of India",
    "Bank of Maharashtra",
    "HDFC Bank",
    "ICICI Bank",
    "Axis Bank",
    "Punjab National Bank",
    "Bank of Baroda",
    "Canara Bank",
    "Union Bank of India",
    "Indian Bank",
    "Central Bank of India",
    "Indian Overseas Bank",
    "UCO Bank",
    "Kotak Mahindra Bank",
    "IDBI Bank",
]


# ──────────────────────────────────────────────
# Data generators
# ──────────────────────────────────────────────

def generate_bank_name():
    """Generate a valid bank name (letters and spaces only)."""
    return random.choice(_BANK_NAMES)


def generate_sanction_amount():
    """Generate sanction amount: 500,000 to 50,000,000."""
    return random.randint(500000, 50000000)


def generate_disbursement_amount(sanction_amount):
    """Generate disbursement amount (<= sanction amount)."""
    max_disburse = int(sanction_amount * 0.95)
    min_disburse = int(sanction_amount * 0.5)
    return random.randint(min_disburse, max_disburse)


def generate_instalment_amount():
    """Generate instalment amount: 5,000 to 500,000."""
    return random.randint(5000, 500000)


def generate_reminder_period():
    """Generate reminder period in days (positive integer, 1-90)."""
    return random.choice([7, 15, 30, 45, 60, 90])


def generate_outstanding_amount(disbursement_amount):
    """Generate outstanding amount (<= disbursement amount)."""
    max_out = int(disbursement_amount * 0.9)
    min_out = int(disbursement_amount * 0.1)
    return random.randint(min_out, max_out)


def generate_facility_details_id():
    return random.choice(FACILITY_DETAILS_IDS)


def generate_emi_period_id():
    return random.choice(EMI_PERIOD_IDS)


def generate_date_string(days_ago_range=730):
    """Generate a date string in ISO format."""
    today = date.today()
    days_back = random.randint(1, days_ago_range)
    d = today - __import__("datetime").timedelta(days=days_back)
    return f"{d.strftime('%Y-%m-%d')}T18:30:00Z"


# ──────────────────────────────────────────────
# Valid data
# ──────────────────────────────────────────────

def generate_valid_data():
    """Generate complete valid data for the Register of Loan form."""
    san_amt = generate_sanction_amount()
    disb_amt = generate_disbursement_amount(san_amt)
    return {
        "sanction_date": generate_date_string(),
        "bank_name": generate_bank_name(),
        "sanction_amount": san_amt,
        "facility_details_ref_id": generate_facility_details_id(),
        "disbursement_amount": disb_amt,
        "emi_servicing_date": generate_date_string(),
        "instalment_amount": generate_instalment_amount(),
        "reminder_period_in_days": generate_reminder_period(),
        "emi_period": generate_emi_period_id(),
        "outstanding_date": generate_date_string(),
        "outstanding_amount": generate_outstanding_amount(disb_amt),
        "is_notification_applicable": random.choice([True, False]),
    }


# ──────────────────────────────────────────────
# API Payload Builder
# ──────────────────────────────────────────────

def build_api_payload(data=None, fk_overrides=None):
    """Build JSON payload for POST /core/dynamic-screen-wrapper/.

    Args:
        data: Dict from generate_valid_data(). If None, auto-generates.
        fk_overrides: Dict of FK ID overrides.

    Returns:
        Complete JSON payload dict ready for POST.
    """
    if data is None:
        data = generate_valid_data()
    if fk_overrides is None:
        fk_overrides = {}

    payload = {
        "id": "",
        "attribute_name": "Register of Loan",
        "sanction_date": data.get("sanction_date") or generate_date_string(),
        "bank_name": data.get("bank_name") or generate_bank_name(),
        "sanction_amount": data.get("sanction_amount") or generate_sanction_amount(),
        "facility_details_ref_id": fk_overrides.get("facility_details_ref_id")
                                    or data.get("facility_details_ref_id")
                                    or generate_facility_details_id(),
        "disbursement_amount": data.get("disbursement_amount") or 0,
        "emi_servicing_date": data.get("emi_servicing_date") or generate_date_string(),
        "instalment_amount": data.get("instalment_amount") or generate_instalment_amount(),
        "reminder_period_in_days": data.get("reminder_period_in_days") or generate_reminder_period(),
        "emi_period": fk_overrides.get("emi_period")
                       or data.get("emi_period")
                       or generate_emi_period_id(),
        "outstanding_date": data.get("outstanding_date"),
        "outstanding_amount": data.get("outstanding_amount") or 0,
        "is_notification_applicable": data.get("is_notification_applicable", False),
        "details": [],
        "children": [],
    }

    return payload


def generate_api_payload(**kwargs):
    """One-shot: generate a randomized Register of Loan API payload."""
    data = generate_valid_data()
    payload = build_api_payload(data)
    payload.update(kwargs)
    return payload


def generate_batch_payloads(count, offset=0, **kwargs):
    """Generate multiple unique Register of Loan API payloads."""
    payloads = []
    for i in range(count):
        p = generate_api_payload(**kwargs)
        payloads.append(p)
    return payloads


# ──────────────────────────────────────────────
# SweetAlert titles (used by UI tests)
# ──────────────────────────────────────────────
SWAL_TITLE_SUCCESS = "Your record has been added successfully!"
SWAL_TITLE_VALIDATION_FAILED = "Validation Failed"
SWAL_TITLE_UPDATED = "Your record has been updated successfully!"


def generate_ui_form_data():
    """UI-friendly form data dict for fill_form().

    Number fields are stringified (UI inputs take text).
    facility_details and emi_period are set to True sentinels —
    fill_form uses _select_first_available_mat_option so the actual FK value is ignored.
    """
    data = generate_valid_data()
    data["facility_details"] = True      # sentinel — uses first available option
    data["emi_period_label"] = True      # sentinel — uses first available option
    data["sanction_amount"] = str(int(data["sanction_amount"]))
    data["disbursement_amount"] = str(int(data["disbursement_amount"]))
    data["instalment_amount"] = str(int(data["instalment_amount"]))
    data["outstanding_amount"] = str(int(data["outstanding_amount"]))
    data["reminder_period_in_days"] = str(data["reminder_period_in_days"])
    return data
