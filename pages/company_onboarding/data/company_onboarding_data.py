"""Batch payload generator for Company Onboarding."""

import random
import string

# Constants confirmed identical across all tenants sampled
_OWNERSHIP_STATUS           = 1263
_BASE_CURRENCY              = 8
_ADDRESS_TYPE_REGISTERED    = 1649
_ADDRESS_TYPE_COMMUNICATION = 1650
_STATE                      = 98
_COUNTRY                    = 8
_DISTRICT                   = 479
_TALUKA                     = 11462
_PINCODE                    = 2148
_USER_TYPE_ID               = 4
_LEVEL                      = 2

_SUFFIXES = [
    "Traders", "Enterprises", "Industries", "Agro", "Foods", "Seeds",
    "Organics", "Commodities", "Corp", "Solutions",
]

_PREFIXES = [
    "Shree", "Sri", "Royal", "Golden", "Green", "Prime", "Pioneer",
    "National", "Global", "United",
]


def _rand_pan() -> str:
    return (
        "".join(random.choices(string.ascii_uppercase, k=5))
        + "".join(random.choices(string.digits, k=4))
        + random.choice(string.ascii_uppercase)
    )


def _rand_cin() -> str:
    return (
        "U"
        + "".join(random.choices(string.digits, k=5))
        + "".join(random.choices(string.ascii_uppercase, k=2))
        + "".join(random.choices(string.digits, k=4))
        + "PTC"
        + "".join(random.choices(string.digits, k=6))
    )


def _rand_email(slug: str) -> str:
    clean = slug.lower().replace(" ", "").replace("'", "")[:20]
    return f"{clean}{random.randint(100, 9999)}@example.com"


def _rand_phone() -> int:
    return int("9" + "".join(random.choices(string.digits, k=9)))


def _rand_tenant_code() -> int:
    return random.randint(10000000, 99999999)


def enrich_existing_entries(client, existing_entries: list) -> list:
    """Fetch full detail for the oldest listing row so sniffing can read nested children."""
    if not existing_entries:
        return existing_entries
    if "children" in existing_entries[0]:
        return existing_entries  # already enriched
    # Oldest entry (min id) is most likely manually-created with correct parent_id
    oldest = min(existing_entries, key=lambda e: e.get("id", float("inf")))
    detail = client.get_entry("Company Onboarding", oldest["id"])
    if not detail:
        return existing_entries
    rest = [e for e in existing_entries if e.get("id") != oldest.get("id")]
    return [detail] + rest


def _sniff_from_existing(existing_entries: list) -> dict:
    """Extract tenant-specific FK IDs from existing company records."""
    sniffed = {}

    # Collect all non-null parent_ids; minimum = root company (universal across tenants)
    parent_ids = [e["parent_id"] for e in existing_entries if e.get("parent_id")]
    if parent_ids:
        sniffed["parent_id"] = min(parent_ids)

    for entry in existing_entries:
        children = entry.get("children", [])
        for child in children:
            if child.get("stepper_name") == "Company Details":
                if child.get("native_language"):
                    sniffed["native_language"] = child["native_language"]

            if child.get("stepper_name") == "Address Details":
                for addr in child.get("details", []):
                    if addr.get("taluka"):
                        sniffed["taluka"] = addr["taluka"]
                    if addr.get("district"):
                        sniffed["district"] = addr["district"]
                    if addr.get("state"):
                        sniffed["state"] = addr["state"]
                    if addr.get("pincode_ref_id_id"):
                        sniffed["pincode"] = addr["pincode_ref_id_id"]
                    break

        if len(sniffed) >= 5:
            break

    return sniffed


def generate_batch_payloads(
    count: int = 10,
    existing_entries=None,
    config=None,
) -> list[dict]:
    config = config or {}

    # Sniff tenant-specific IDs from existing records
    sniffed = _sniff_from_existing(existing_entries or [])

    # parent_id: config override → sniffed → no default (must be resolved)
    parent_id = config.get("parent_id") or sniffed.get("parent_id")
    native_language = 1959  # hardcoded — tenant-universal
    taluka   = config.get("taluka")   or sniffed.get("taluka")   or _TALUKA
    district = config.get("district") or sniffed.get("district") or _DISTRICT
    state    = config.get("state")    or sniffed.get("state")    or _STATE
    pincode  = config.get("pincode")  or sniffed.get("pincode")  or _PINCODE

    existing_pans = set()
    if existing_entries:
        for e in existing_entries:
            pan = e.get("pan_no") or ""
            if pan:
                existing_pans.add(pan.upper())

    payloads = []
    for _ in range(count):
        short_name = f"{random.choice(_PREFIXES)} {random.choice(_SUFFIXES)}"
        company_name = f"Company {short_name}"

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
            "parent_id": parent_id,
            "tenant_linked": [parent_id] if parent_id else [],
            "level": _LEVEL,
            "is_parent": False,
            "children": [
                {
                    "stepper_name": "Company Details",
                    "is_stepper": True,
                    "details": [],
                    "children": [],
                    "native_language": native_language,
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
                            "pincode_ref_id_id": pincode,
                            "address_type_ref_id": _ADDRESS_TYPE_REGISTERED,
                            "address": f"{random.randint(1, 999)} Main Road",
                            "taluka": taluka,
                            "district": district,
                            "state": state,
                            "country": _COUNTRY,
                            "same_as_above": None,
                            "longitude": None,
                            "latitude": None,
                            "details": [],
                        },
                        {
                            "pincode_ref_id_id": pincode,
                            "address_type_ref_id": _ADDRESS_TYPE_COMMUNICATION,
                            "address": f"{random.randint(1, 999)} Main Road",
                            "taluka": taluka,
                            "district": district,
                            "state": state,
                            "country": _COUNTRY,
                            "same_as_above": None,
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

        # Conflict mode: override specific fields on Company Details stepper
        override = config.get("_conflict_override", {})
        if override:
            payload["children"][0].update(override)

        payloads.append(payload)

    return payloads
