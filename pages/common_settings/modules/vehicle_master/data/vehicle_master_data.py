#!/usr/bin/env python3
"""
Vehicle Master — Data pool + API payload builder + test data generators.

Screen: "Vehicle Master" (flat, 2 FK dropdowns: vehicle_type_id, fuel_type_ref_id)
Fields: name, vehicle_price, vehicle_type_id, fuel_type_ref_id, description

FK IDs are resolved at runtime via FkResolver. No hardcoded IDs.
"""

import random
import string
from datetime import datetime

# ── Tenant-agnostic data pools (display names only) ──────────────────

VEHICLES = [
    {"name": "Tata Ace",               "price": 500000,  "vehicle_type": "Mini Truck", "fuel_type": "Diesel",   "desc": "Mini truck for intra-city goods transport"},
    {"name": "Ashok Leyland Dost",     "price": 750000,  "vehicle_type": "Pickup",     "fuel_type": "Diesel",   "desc": "Light commercial vehicle for regional logistics"},
    {"name": "Mahindra Bolero Pickup",  "price": 850000,  "vehicle_type": "Pickup",     "fuel_type": "Diesel",   "desc": "Pickup truck for agriculture and small loads"},
    {"name": "Tata 407",              "price": 1200000, "vehicle_type": "Truck",       "fuel_type": "Diesel",   "desc": "Medium duty truck for city distribution"},
    {"name": "Eicher Pro 1059",        "price": 1500000, "vehicle_type": "Truck",       "fuel_type": "Diesel",   "desc": "Medium commercial vehicle for logistics"},
    {"name": "BharatBenz 1215R",       "price": 2200000, "vehicle_type": "Truck",       "fuel_type": "Diesel",   "desc": "Heavy duty truck for long haul transport"},
    {"name": "Tata Prima 4028",        "price": 3500000, "vehicle_type": "Trailer",     "fuel_type": "Diesel",   "desc": "Prime mover for container and bulk transport"},
    {"name": "Mahindra Champion Load", "price": 350000,  "vehicle_type": "Mini Truck",  "fuel_type": "CNG",      "desc": "Three-wheeler cargo for last mile delivery"},
    {"name": "Piaggio Ape Xtra LDX",   "price": 280000,  "vehicle_type": "Mini Truck",  "fuel_type": "Diesel",   "desc": "Three-wheeler goods carrier for urban use"},
    {"name": "Tata Ultra T.7",        "price": 1800000, "vehicle_type": "Truck",       "fuel_type": "Diesel",   "desc": "ICV truck for distribution and logistics"},
    {"name": "Mahindra Furio 7",      "price": 1600000, "vehicle_type": "Truck",       "fuel_type": "Diesel",   "desc": "ICV for regional distribution operations"},
    {"name": "Eicher Pro 6048",        "price": 4200000, "vehicle_type": "Trailer",     "fuel_type": "Diesel",   "desc": "Heavy truck for mining and construction"},
    {"name": "Tata Signa 5528",       "price": 4500000, "vehicle_type": "Trailer",     "fuel_type": "Diesel",   "desc": "55-tonne tractor trailer for bulk logistics"},
    {"name": "Ashok Leyland Partner",  "price": 900000,  "vehicle_type": "Truck",       "fuel_type": "Diesel",   "desc": "Light truck for city delivery operations"},
    {"name": "Mahindra Jeeto",        "price": 250000,  "vehicle_type": "Mini Truck",   "fuel_type": "Diesel",   "desc": "Micro truck for small business deliveries"},
    {"name": "Tata Intra V30",        "price": 650000,  "vehicle_type": "Pickup",       "fuel_type": "Diesel",   "desc": "Pickup for agri and retail distribution"},
    {"name": "Eicher Pro 2049 CNG",    "price": 1100000, "vehicle_type": "Truck",       "fuel_type": "CNG",      "desc": "CNG light truck for eco-friendly delivery"},
    {"name": "Bajaj RE Cargo",         "price": 200000,  "vehicle_type": "Mini Truck",   "fuel_type": "CNG",      "desc": "Compact cargo vehicle for dense urban areas"},
    {"name": "Tata Yodha Pickup",      "price": 950000,  "vehicle_type": "Pickup",       "fuel_type": "Diesel",   "desc": "Rugged pickup for rural and semi-urban use"},
    {"name": "Ashok Leyland Bada Dost","price": 800000,  "vehicle_type": "Pickup",       "fuel_type": "Diesel",   "desc": "Light commercial vehicle for multi-use"},
]


# ================================================================
# TEST DATA GENERATORS — used by test_vehicle_master_validation.py
# ================================================================

def _timestamp_suffix():
    """Return a compact timestamp for uniqueness."""
    return datetime.now().strftime("%H%M%S")


def _random_alpha(length=6):
    """Return a random alphabetic string."""
    return "".join(random.choices(string.ascii_uppercase, k=length))


_vm_name_counter = 0

def generate_vehicle_name(prefix="VM"):
    """Generate a unique vehicle name — LETTERS ONLY (A-Z a-z).
    ERP rejects underscores, digits, and special chars in name field.
    Uses prefix + random alpha + counter-based suffix for uniqueness."""
    global _vm_name_counter
    _vm_name_counter += 1
    # Convert counter to letters (1->A, 2->B, 27->AA, etc.)
    n = _vm_name_counter
    suffix = ""
    while n > 0:
        n -= 1
        suffix = chr(ord('A') + (n % 26)) + suffix
        n //= 26
    return f"{prefix} {_random_alpha(4)} {suffix}"


def generate_vehicle_price():
    """Generate a random vehicle price (integer, 100000–5000000)."""
    return str(random.randint(100000, 5000000))


def generate_description(prefix="Test"):
    """Generate a unique description string."""
    return f"{prefix} Vehicle Description {_timestamp_suffix()}"


def generate_valid_vehicle_data(prefix="VM"):
    """Generate a complete valid vehicle data dict for Create form.
    
    Name field uses alpha-only format (no underscores/digits).
    Returns dict with keys: name, price, vehicle_type, fuel_type, description
    """
    vehicle = random.choice(VEHICLES)
    name = generate_vehicle_name(prefix)
    # Description can have special chars (not restricted)
    desc_suffix = _random_alpha(4)
    return {
        "name": name,
        "price": str(vehicle["price"]),
        "vehicle_type": vehicle["vehicle_type"],
        "fuel_type": vehicle["fuel_type"],
        "description": f"{prefix} Test Vehicle {desc_suffix}",
    }


# ── Payload builder ──────────────────────────────────────────────────

def build_vehicle_master_api_payload(name, vehicle_price, vehicle_type_id,
                                      fuel_type_ref_id, description=""):
    """Build a single API payload for Vehicle Master."""
    return {
        "id": "",
        "name": name,
        "vehicle_price": vehicle_price,
        "vehicle_type_id": vehicle_type_id,
        "fuel_type_ref_id": fuel_type_ref_id,
        "description": description,
        "attribute_name": "Vehicle Master",
    }


def generate_vehicle_master_api_payloads(count=10, offset=0, fk_ids=None):
    """
    Generate N API payloads for Vehicle Master.

    Args:
        count: Number of payloads to generate
        offset: Start index in data pool
        fk_ids: dict with resolved FK IDs (must include vehicle_type_id, fuel_type_ref_id)
    """
    if not fk_ids:
        raise ValueError(
            "fk_ids is required. Resolve FK IDs via FkResolver first: "
            "from common.fk_resolver import FkResolver"
        )

    vt_values = list(fk_ids.get("vehicle_type_id", {}).values())
    ft_values = list(fk_ids.get("fuel_type_ref_id", {}).values())

    payloads = []

    for i in range(count):
        idx = offset + i
        entry = VEHICLES[idx % len(VEHICLES)]

        vt_id = vt_values[i % len(vt_values)] if vt_values else None
        ft_id = ft_values[i % len(ft_values)] if ft_values else None

        payload = build_vehicle_master_api_payload(
            name=entry["name"],
            vehicle_price=entry["price"],
            vehicle_type_id=vt_id,
            fuel_type_ref_id=ft_id,
            description=entry["desc"],
        )
        payloads.append(payload)

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────

def get_field_validation_rules():
    """Return field validation rules (FK counts resolved at runtime)."""
    return {
        "name": {
            "type": "character",
            "required": True,
            "max_length": 255,
        },
        "vehicle_price": {
            "type": "character",
            "required": True,
            "max_length": 255,
            "note": "Numeric value as string. Input type='character' in UI.",
        },
        "vehicle_type_id": {
            "type": "dropdown",
            "required": True,
            "fk_options_count": 0,
            "note": "FK to Vehicle Type. Resolved at runtime via FkResolver.",
        },
        "fuel_type_ref_id": {
            "type": "dropdown",
            "required": True,
            "fk_options_count": 0,
            "note": "FK to Fuel Type. Resolved at runtime via FkResolver.",
        },
        "description": {
            "type": "character",
            "required": False,
            "max_length": 255,
        },
    }


def get_fk_screen_mapping():
    """Return FK field → screen name mapping for live FkResolver resolution."""
    return {
        "vehicle_type_id":  "Accounting Template",
        "fuel_type_ref_id": "Ledger Group",
    }


def generate_batch_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None, offset: int = 0, existing_entries: list = None) -> list:
    """Generate a batch of unique Vehicle Master API payloads, deduping against existing_entries.

    Args:
        dropdown_ids: Must contain resolved FK IDs (vehicle_type_id, fuel_type_ref_id).
                      Resolve via FkResolver before calling.
    """
    if not dropdown_ids:
        raise ValueError("dropdown_ids is required. Resolve FK IDs via FkResolver first.")
    fk_ids = dropdown_ids
    if existing_entries:
        used_names = {e.get("name", "").lower().strip() for e in existing_entries if e.get("name")}
        vt_values = list(fk_ids.get("vehicle_type_id", {}).values())
        ft_values = list(fk_ids.get("fuel_type_ref_id", {}).values())
        unique_payloads = []
        pool_idx = 0
        while len(unique_payloads) < count:
            entry = VEHICLES[(offset + pool_idx) % len(VEHICLES)]
            name = entry["name"]
            if name.lower().strip() not in used_names:
                used_names.add(name.lower().strip())
                unique_payloads.append(build_vehicle_master_api_payload(
                    name=name,
                    vehicle_price=entry["price"],
                    vehicle_type_id=vt_values[pool_idx % len(vt_values)] if vt_values else None,
                    fuel_type_ref_id=ft_values[pool_idx % len(ft_values)] if ft_values else None,
                    description=entry["desc"],
                ))
            pool_idx += 1
        return unique_payloads
    return generate_vehicle_master_api_payloads(count=count, offset=offset, fk_ids=fk_ids)
