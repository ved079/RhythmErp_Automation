"""Batch payload generator for Company Onboarding."""

import random
import string
import time

# Fixed FK IDs (from confirmed sample record)
_PARENT_ID         = 795
_USER_TYPE_ID      = 4
_LEVEL             = 2
_NATIVE_LANGUAGE   = 1959
_OWNERSHIP_STATUS  = 1263
_BASE_CURRENCY     = 8
_ADDRESS_TYPE_REGISTERED = 1649
_ADDRESS_TYPE_COMMUNICATION = 1650
_PINCODE           = 18513
_TALUKA            = 5322
_DISTRICT          = 276
_STATE             = 111
_COUNTRY           = 8

_STATES = [
    "Maharashtra", "Karnataka", "Gujarat", "Rajasthan", "Tamil Nadu",
    "Uttar Pradesh", "Madhya Pradesh", "Telangana", "Kerala", "Punjab",
]

_SUFFIXES = [
    "Traders", "Enterprises", "Industries", "Agro", "Foods", "Seeds",
    "Organics", "Commodities", "Corp", "Solutions",
]


def _rand_pan() -> str:
    """Generate a random PAN-format string (5 alpha + 4 digit + 1 alpha)."""
    return (
        "".join(random.choices(string.ascii_uppercase, k=5))
        + "".join(random.choices(string.digits, k=4))
        + random.choice(string.ascii_uppercase)
    )


def _rand_cin() -> str:
    """Generate a CIN-format string: U + 5 digits + 2 alpha + 4 digits + PTC + 6 digits."""
    return (
        "U"
        + "".join(random.choices(string.digits, k=5))
        + "".join(random.choices(string.ascii_uppercase, k=2))
        + "".join(random.choices(string.digits, k=4))
        + "PTC"
        + "".join(random.choices(string.digits, k=6))
    )


def _rand_email(name: str) -> str:
    slug = name.lower().replace(" ", "").replace("'", "")[:20]
    return f"{slug}{random.randint(100, 9999)}@example.com"


def _rand_phone() -> int:
    return int("9" + "".join(random.choices(string.digits, k=9)))


def _rand_tenant_code() -> int:
    return random.randint(10000000, 99999999)


def generate_batch_payloads(count: int = 10, existing_entries=None, config=None) -> list[dict]:
    existing_pans = set()
    if existing_entries:
        for e in existing_entries:
            pan = e.get("pan_no") or ""
            if pan:
                existing_pans.add(pan.upper())

    payloads = []
    for _ in range(count):
        first = random.choice(_STATES).split()[0]
        suffix = random.choice(_SUFFIXES)
        short_name = f"{first} {suffix}"
        company_name = f"Company {short_name}"

        # Unique PAN
        for _ in range(20):
            pan = _rand_pan()
            if pan not in existing_pans:
                existing_pans.add(pan)
                break

        promoter_name = f"Promoter {random.randint(1000, 9999)}"

        payload = {
            "id": "",
            "attribute_name": "Company Onboarding",
            "name": company_name,
            "user_type_id": _USER_TYPE_ID,
            "parent_id": _PARENT_ID,
            "tenant_linked": [_PARENT_ID],
            "level": _LEVEL,
            "is_parent": False,
            "children": [
                {
                    "stepper_name": "Company Details",
                    "is_stepper": True,
                    "details": [],
                    "children": [],
                    "native_language": _NATIVE_LANGUAGE,
                    "company_background": "bg",
                    "pan_no": pan,
                    "tan_no": None,
                    "authentication_type": None,
                    "ownership_status_id": _OWNERSHIP_STATUS,
                    "tenant_short_name": short_name,
                    "contact_person_name": f"Contact {random.randint(100, 999)}",
                    "email_id": _rand_email(short_name),
                    "phone_no": _rand_phone(),
                    "gst_no": None,
                    "cin_no": _rand_cin(),
                    "plan_type_ref_id": None,
                    "is_2fa_applicable": False,
                    "base_currency": _BASE_CURRENCY,
                    "tenant_code": _rand_tenant_code(),
                },
                {
                    "stepper_name": "Promoters Details",
                    "is_stepper": True,
                    "details": [
                        {
                            "remark": promoter_name,
                            "promoter_name": promoter_name,
                            "details": [],
                        }
                    ],
                    "children": [],
                },
                {
                    "stepper_name": "Address Details",
                    "is_stepper": True,
                    "details": [
                        {
                            "pincode_ref_id_id": _PINCODE,
                            "address_type_ref_id": _ADDRESS_TYPE_REGISTERED,
                            "address": f"{random.randint(1, 999)} Main Road",
                            "taluka": _TALUKA,
                            "district": _DISTRICT,
                            "state": _STATE,
                            "country": _COUNTRY,
                            "same_as_above": True,
                            "longitude": None,
                            "latitude": None,
                            "details": [],
                        },
                        {
                            "pincode_ref_id_id": _PINCODE,
                            "address_type_ref_id": _ADDRESS_TYPE_COMMUNICATION,
                            "address": f"{random.randint(1, 999)} Main Road",
                            "taluka": _TALUKA,
                            "district": _DISTRICT,
                            "state": _STATE,
                            "country": _COUNTRY,
                            "same_as_above": True,
                            "longitude": None,
                            "latitude": None,
                            "details": [],
                        },
                    ],
                    "children": [],
                },
                {
                    "stepper_name": "Infrastructure Details",
                    "is_stepper": True,
                    "details": [],
                    "children": [],
                },
                {
                    "stepper_name": "Business Activities",
                    "is_stepper": True,
                    "details": [],
                    "children": [],
                },
            ],
        }

        # Conflict override (concurrency mode)
        override = (config or {}).get("_conflict_override", {})
        if override:
            company_details = payload["children"][0]
            company_details.update(override)

        payloads.append(payload)

    return payloads
