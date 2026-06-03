#!/usr/bin/env python3
"""
Vehicle Master — Data pool + API payload builder + test data generators.

Screen: "Vehicle Master" (flat, 2 FK dropdowns: vehicle_type_id, fuel_type_ref_id)
Fields: name, vehicle_price, vehicle_type_id, fuel_type_ref_id, description

Discovered FK IDs (2026-06-02):
  vehicle_type_id:   Truck=1, Trailer=2, Tanker=3, Mini Truck=4, Pickup=5
  fuel_type_ref_id:  Diesel=1, Petrol=2, CNG=3, Electric=4, LPG=5
"""

import random
import string
from datetime import datetime

# ── Real FK IDs from live ERP ────────────────────────────────────────
VEHICLE_TYPE_IDS = {
    "Truck":      1,
    "Trailer":    2,
    "Tanker":     3,
    "Mini Truck": 4,
    "Pickup":     5,
}

FUEL_TYPE_IDS = {
    "Diesel":   1,
    "Petrol":   2,
    "CNG":      3,
    "Electric": 4,
    "LPG":      5,
}

# ── Realistic data pools ─────────────────────────────────────────────

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


def generate_vehicle_name(prefix="VM"):
    """Generate a unique vehicle name with prefix + random chars + timestamp."""
    return f"{prefix}_{_random_alpha(4)}_{_timestamp_suffix()}"


def generate_vehicle_price():
    """Generate a random vehicle price (integer, 100000–5000000)."""
    return str(random.randint(100000, 5000000))


def generate_description(prefix="Test"):
    """Generate a unique description string."""
    return f"{prefix} Vehicle Description {_timestamp_suffix()}"


def generate_valid_vehicle_data(prefix="VM"):
    """Generate a complete valid vehicle data dict for Create form.
    
    Returns dict with keys: name, price, vehicle_type, fuel_type, description
    """
    vehicle = random.choice(VEHICLES)
    ts = _timestamp_suffix()
    return {
        "name": f"{prefix}_{vehicle['name']}_{ts}",
        "price": str(vehicle["price"]),
        "vehicle_type": vehicle["vehicle_type"],
        "fuel_type": vehicle["fuel_type"],
        "description": f"{prefix} {vehicle['desc']} {ts}",
    }


def generate_valid_edit_data():
    """Generate data suitable for editing a vehicle (description change)."""
    return {
        "description": f"Edited Description {_timestamp_suffix()}",
    }


def generate_empty_data():
    """Return a dict with all empty/blank values."""
    return {
        "name": "",
        "price": "",
        "vehicle_type": "",
        "fuel_type": "",
        "description": "",
    }


def generate_name_only_data(prefix="NameOnly"):
    """Return data with only the name filled in."""
    return {
        "name": generate_vehicle_name(prefix),
        "price": "",
        "vehicle_type": "",
        "fuel_type": "",
        "description": "",
    }


def generate_spaces_only(count=5):
    """Return a string of only spaces."""
    return " " * count


def generate_zero_price():
    """Return '0' as a price string."""
    return "0"


def generate_negative_price():
    """Return a negative price string."""
    return f"-{random.randint(100, 9999)}"


def generate_alpha_price():
    """Return alphabetic characters as price (invalid)."""
    return f"abc{_random_alpha(3)}"


def generate_decimal_price():
    """Return a decimal price string (e.g., '1500.50')."""
    return f"{random.randint(100, 9999)}.{random.randint(10, 99)}"


def generate_price_with_special_chars():
    """Return price with special characters (invalid)."""
    return "500$%@"


def generate_price_with_spaces():
    """Return price with leading/trailing spaces."""
    return f"  {random.randint(100, 9999)}  "


def generate_special_char_name():
    """Return a name with special characters."""
    return f"Test!@#$%^&*_{_timestamp_suffix()}"


def generate_string_255():
    """Return a string of exactly 255 characters."""
    return "A" * 255


def generate_string_256():
    """Return a string of exactly 256 characters."""
    return "A" * 256


def generate_duplicate_name_data(existing_name):
    """Return valid data dict that uses an existing vehicle name (for dup test)."""
    vehicle = random.choice(VEHICLES)
    return {
        "name": existing_name,
        "price": str(vehicle["price"]),
        "vehicle_type": vehicle["vehicle_type"],
        "fuel_type": vehicle["fuel_type"],
        "description": f"Dup test {_timestamp_suffix()}",
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


def generate_vehicle_master_api_payloads(count=10, fk_ids=None):
    """
    Generate N API payloads for Vehicle Master.
    """
    if fk_ids is None:
        fk_ids = {}

    # Merge FK IDs
    vehicle_type_ids = {**VEHICLE_TYPE_IDS, **fk_ids.get("vehicle_type_id", {})}
    fuel_type_ids = {**FUEL_TYPE_IDS, **fk_ids.get("fuel_type_ref_id", {})}

    payloads = []

    for i in range(count):
        entry = VEHICLES[i % len(VEHICLES)]

        vt_id = vehicle_type_ids.get(entry["vehicle_type"], 1)
        ft_id = fuel_type_ids.get(entry["fuel_type"], 1)

        payload = build_vehicle_master_api_payload(
            name=entry["name"],
            vehicle_price=entry["price"],
            vehicle_type_id=vt_id,
            fuel_type_ref_id=ft_id,
            description=entry["desc"],
        )
        payloads.append(payload)

    return payloads
