"""
company_onboarding_update_data.py
----------------------------------
Test data for Company Onboarding UPDATE tests.

Step order (matches actual app):
  Step 1 = Company Details  (contact_name, email, mobile_number, company_code)
  Step 2 = Promoters         (promoter_name, promoter_remark)
  Step 3 = Address           (address, pin_code)
  Step 4 = Business Details  (business_model, market_linkages)
  Step 5 = Infrastructure
  Step 6 = Configuration     (base_currency)
"""

import random
import string

# Company name must already exist in the system
UPDATE_COMPANY_NAME = "Orion Link Services"


# ---- Random data generators ----

def _gen_name():
    first = random.choice(["Manoj", "Vijay", "Rajesh", "Sanjay", "Amit", "Pradeep", "Suresh", "Deepak"])
    last = random.choice(["Jadhav", "Sharma", "Patil", "Kulkarni", "Desai", "Joshi", "More", "Pawar"])
    return f"{first} {last}"


def _gen_email():
    name = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"{name}@testmail.com"


def _gen_mobile():
    return "".join([random.choice(["9", "8", "7", "6"])] + [str(random.randint(0, 9)) for _ in range(9)])


def _gen_remark():
    return f"Updated remark {random.randint(100, 999)}"


def _gen_address():
    return f"{random.randint(1, 200)}, Test Street, Sector {random.randint(1, 50)}"


def _gen_pin():
    return str(random.randint(110000, 899999))


def _gen_business_model():
    return f"Model-{random.choice(['B2B', 'B2C', 'D2C', 'Marketplace'])}-{random.randint(100, 999)}"


def _gen_market_linkages():
    return f"Link-{random.choice(['National', 'Regional', 'Local', 'Global'])}-{random.randint(100, 999)}"


def _gen_company_code():
    """Generate a valid 4-char Company Code for update."""
    return "".join(random.choices(string.ascii_uppercase, k=4))


# ---- Per-step update dictionaries ----

STEP1_UPDATES = {
    "contact_name": _gen_name(),
    "email": _gen_email(),
    "mobile_number": _gen_mobile(),
    "company_code": _gen_company_code(),
}

STEP2_UPDATES = {
    "1": {
        "promoter_name": _gen_name(),
        "promoter_remark": _gen_remark(),
    }
}

STEP3_UPDATES = {
    "1": {
        "address": _gen_address(),
        "pin_code": _gen_pin(),
    }
}

STEP4_UPDATES = {
    "1": {
        "business_model": _gen_business_model(),
        "market_linkages": _gen_market_linkages(),
    }
}

STEP5_UPDATES = {
    "1": {
        "infra_location": f"Test Location {random.randint(100, 999)}",
    }
}

STEP6_UPDATES = {
    "1": {
        "base_currency": "INR",
    }
}

ALL_UPDATES = {
    1: STEP1_UPDATES,
    2: STEP2_UPDATES,
    3: STEP3_UPDATES,
    4: STEP4_UPDATES,
    5: STEP5_UPDATES,
    6: STEP6_UPDATES,
}
