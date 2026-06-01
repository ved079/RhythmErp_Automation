import random
import string
from datetime import datetime


def generate_vehicle_name(prefix="AutoVeh"):
    """Generate a random vehicle name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_vehicle_price():
    """Generate a random valid vehicle price (positive integer)."""
    return random.randint(10000, 9999999)


def generate_description():
    """Generate a random description text."""
    words = [
        "Test vehicle entry", "Automated test data", "Selenium validation",
        "Regression test vehicle", "QA automation entry", "Smoke test data",
        "Performance test vehicle", "Integration test entry"
    ]
    return f"{random.choice(words)} - {random.randint(1000, 9999)}"


def generate_valid_vehicle_data(name_prefix="AutoVeh"):
    """Generate a complete dict of valid vehicle data for Create form.
    Dropdown values (vehicle_type, fuel_type) are set to None — 
    must be populated from live UI at runtime via page methods.
    """
    return {
        "name": generate_vehicle_name(name_prefix),
        "price": str(generate_vehicle_price()),
        "vehicle_type": None,  # To be picked from live UI dropdown
        "fuel_type": None,     # To be picked from live UI dropdown
        "description": generate_description()
    }


def generate_valid_edit_data(name_prefix="EditVeh"):
    """Generate valid data for Edit form — only fields we want to change."""
    return {
        "name": generate_vehicle_name(name_prefix),
        "price": str(generate_vehicle_price()),
        "description": generate_description()
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_string_255():
    """Generate a string of exactly 255 characters (max boundary for Name)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds max for Name)."""
    return "A" * 256


def generate_spaces_only(length=10):
    """Generate a string of only spaces (for Name validation test)."""
    return " " * length


def generate_special_char_name():
    """Generate a name with special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"Vehicle{special}"


def generate_negative_price():
    """Return a negative price string."""
    return f"-{random.randint(1, 9999)}"


def generate_zero_price():
    """Return zero price string."""
    return "0"


def generate_alpha_price():
    """Return alphabetic characters to test price field rejects letters."""
    return "abcDEF"


def generate_decimal_price():
    """Return a decimal price to test if decimals are accepted."""
    return f"{random.randint(1, 999)}.{random.randint(10, 99)}"


def generate_price_with_special_chars():
    """Return special characters to test price field rejects them."""
    return "!@#$"


def generate_price_with_spaces():
    """Return spaces to test price field rejects them."""
    return "   "


def generate_empty_data():
    """Return dict with all empty strings — for mandatory field validation."""
    return {
        "name": "",
        "price": "",
        "vehicle_type": "",
        "fuel_type": "",
        "description": ""
    }


def generate_name_only_data(name_prefix="NameOnly"):
    """Return dict with only name filled — for partial field validation."""
    return {
        "name": generate_vehicle_name(name_prefix),
        "price": "",
        "vehicle_type": "",
        "fuel_type": "",
        "description": ""
    }


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing name — for duplicate name test."""
    return {
        "name": existing_name,
        "price": str(generate_vehicle_price()),
        "vehicle_type": None,
        "fuel_type": None,
        "description": generate_description()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# API Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Converts UI data format into the JSON payload that
# POST /core/dynamic-screen-wrapper/ expects.
#
# VEHICLE MASTER SCREEN STRUCTURE (flat — no children/steppers):
#   {
#     "id": "",
#     "attribute_name": "Vehicle Master",
#     "name": "Tata Ace Gold",
#     "vehicle_price": 500000,
#     "vehicle_type_id": <FK ID>,
#     "fuel_type_ref_id": <FK ID>,
#     "description": "Mini truck for last mile delivery",
#     "status": true
#   }
#
# FIELD KEY MAPPING:
#   name          -> name (text)
#   price         -> vehicle_price (numeric)
#   vehicle_type  -> vehicle_type_id (FK dropdown)
#   fuel_type     -> fuel_type_ref_id (FK dropdown)
#   description   -> description (text)
#   status        -> status (boolean)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── FK ID Placeholders (to be filled from discovery or live API) ────────────
VEHICLE_TYPE_IDS = {
    "Truck": None,
    "Tempo": None,
    "Tractor": None,
    "Trailer": None,
    "Tanker": None,
    "Mini Truck": None,
    "Pick Up": None,
    "Container": None,
}

FUEL_TYPE_IDS = {
    "Diesel": None,
    "Petrol": None,
    "CNG": None,
    "Electric": None,
    "LPG": None,
}

# ─── Realistic Indian vehicle data pool ──────────────────────────────────────
REALISTIC_VEHICLE_POOL = [
    # Tata Motors
    {"name": "Tata Ace Gold", "price": 500000, "vehicle_type": "Mini Truck", "fuel_type": "Diesel",
     "description": "Mini truck for last mile delivery in urban areas"},
    {"name": "Tata Ace Mega", "price": 600000, "vehicle_type": "Mini Truck", "fuel_type": "Diesel",
     "description": "High payload mini truck for intra-city logistics"},
    {"name": "Tata Intra V10", "price": 700000, "vehicle_type": "Mini Truck", "fuel_type": "Diesel",
     "description": "Compact truck for small business transportation needs"},
    {"name": "Tata Intra V30", "price": 800000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Light commercial vehicle for regional freight movement"},
    {"name": "Tata Intra V50", "price": 900000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Medium commercial vehicle for inter-district transport"},
    {"name": "Tata 407", "price": 1200000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Medium duty truck for regional cargo transportation"},
    {"name": "Tata 709", "price": 1800000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy duty truck for inter-state freight movement"},
    {"name": "Tata 1109", "price": 2200000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy truck for long haul transportation"},
    {"name": "Tata 1615", "price": 2800000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Rigid truck for bulk cargo and construction material"},
    {"name": "Tata 2518", "price": 3500000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Multi-axle truck for heavy freight operations"},
    {"name": "Tata Prima 2830", "price": 4500000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Premium heavy duty truck for long distance logistics"},
    {"name": "Tata Prima 4030", "price": 5000000, "vehicle_type": "Tractor", "fuel_type": "Diesel",
     "description": "Prime mover for trailer operations across India"},
    {"name": "Tata Signa 2818", "price": 3200000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Medium heavy truck for construction and mining"},
    {"name": "Tata Signa 3525", "price": 4200000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy duty signa series truck for bulk transport"},
    {"name": "Tata Ultra 1518", "price": 2500000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Ultra series intermediate truck for city-to-city freight"},
    {"name": "Tata LPT 3723", "price": 3800000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Long platform truck for steel and cement transportation"},
    {"name": "Tata Ace EV", "price": 750000, "vehicle_type": "Mini Truck", "fuel_type": "Electric",
     "description": "Electric mini truck for emission-free urban delivery"},
    # Ashok Leyland
    {"name": "Ashok Leyland Ecomet 1015", "price": 1600000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Light duty truck for regional distribution and logistics"},
    {"name": "Ashok Leyland Ecomet 1215", "price": 1900000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Medium duty ecomet truck for inter-city freight"},
    {"name": "Ashok Leyland Ecomet 1615", "price": 2400000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy duty ecomet truck for construction material"},
    {"name": "Ashok Leyland Partner", "price": 1400000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Intermediate commercial vehicle for multi-purpose logistics"},
    {"name": "Ashok Leyland Guru", "price": 1700000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy truck for state-wide cargo operations"},
    {"name": "Ashok Leyland Captain 3723", "price": 4000000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Captain series heavy truck for mining and construction"},
    {"name": "Ashok Leyland U 3520", "price": 3800000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "AVL series truck for heavy freight and long distance"},
    {"name": "Ashok Leyland U 2820", "price": 3400000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Multi-axle truck for bulk commodity transport"},
    {"name": "Ashok Leyland 3116", "price": 2600000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Intermediate truck for FMCG and agri product distribution"},
    {"name": "Ashok Leyland 3120", "price": 2900000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy intermediate truck for industrial logistics"},
    {"name": "Ashok Leyland 4825", "price": 4800000, "vehicle_type": "Tractor", "fuel_type": "Diesel",
     "description": "Prime mover for 40 ton trailer operations"},
    {"name": "Ashok Leyland 5525", "price": 5200000, "vehicle_type": "Tractor", "fuel_type": "Diesel",
     "description": "Heavy prime mover for container and ODC transport"},
    # Eicher (VE Commercial Vehicles)
    {"name": "Eicher Pro 2049", "price": 900000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Light duty pro series truck for city logistics"},
    {"name": "Eicher Pro 2059", "price": 1000000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Medium duty pro truck for regional distribution"},
    {"name": "Eicher Pro 3015", "price": 1800000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Intermediate pro truck for inter-city freight movement"},
    {"name": "Eicher Pro 6025", "price": 3500000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy duty pro truck for long haul logistics"},
    {"name": "Eicher Pro 6040", "price": 4600000, "vehicle_type": "Tractor", "fuel_type": "Diesel",
     "description": "Prime mover for heavy trailer and container transport"},
    {"name": "Eicher Pro 8035", "price": 5000000, "vehicle_type": "Tractor", "fuel_type": "Diesel",
     "description": "Premium tractor for ODC and heavy cargo movement"},
    {"name": "Eicher Pro 2114", "price": 1500000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Medium truck for FMCG and consumer goods logistics"},
    {"name": "Eicher Pro 3019", "price": 2200000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy intermediate truck for steel and cement transport"},
    # BharatBenz
    {"name": "BharatBenz 1215R", "price": 1700000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Rigid truck for regional cargo and distribution"},
    {"name": "BharatBenz 1617R", "price": 2300000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Rigid truck for construction material transportation"},
    {"name": "BharatBenz 2823R", "price": 3200000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Multi-axle rigid truck for heavy freight operations"},
    {"name": "BharatBenz 3523R", "price": 4000000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy rigid truck for mining and bulk cargo"},
    {"name": "BharatBenz 4023T", "price": 4500000, "vehicle_type": "Tractor", "fuel_type": "Diesel",
     "description": "Tractor for 37 ton trailer and container transport"},
    {"name": "BharatBenz 4923T", "price": 5100000, "vehicle_type": "Tractor", "fuel_type": "Diesel",
     "description": "Heavy tractor for ODC and long distance haulage"},
    {"name": "BharatBenz 1015R", "price": 1300000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Light rigid truck for intra-city logistics and e-commerce"},
    # Mahindra
    {"name": "Mahindra Loadking", "price": 1100000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Intermediate truck for agricultural and rural transport"},
    {"name": "Mahindra Loadking Optimo", "price": 1400000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Optimo series truck for construction and infrastructure"},
    {"name": "Mahindra Furio 7", "price": 1200000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Furio series truck for city-to-city freight"},
    {"name": "Mahindra Furio 12", "price": 1600000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy furio truck for inter-state cargo movement"},
    {"name": "Mahindra Furio 16", "price": 2000000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Multi-axle furio truck for bulk freight operations"},
    {"name": "Mahindra Blazo X 28", "price": 3300000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Blazo series heavy truck for long haul logistics"},
    {"name": "Mahindra Blazo X 35", "price": 3900000, "vehicle_type": "Truck", "fuel_type": "Diesel",
     "description": "Heavy blazo truck for mining and construction material"},
    {"name": "Mahindra Blazo X 42", "price": 4400000, "vehicle_type": "Tractor", "fuel_type": "Diesel",
     "description": "Prime mover for container and trailer transport"},
    {"name": "Mahindra Bolero Pickup", "price": 700000, "vehicle_type": "Pick Up", "fuel_type": "Diesel",
     "description": "Pickup truck for agricultural and small cargo transport"},
    {"name": "Mahindra Bolero Camper", "price": 800000, "vehicle_type": "Pick Up", "fuel_type": "Diesel",
     "description": "Camper variant for multi-utility rural transport"},
    # Tempo / Three-wheelers / CNG variants
    {"name": "Tata Ace Zip", "price": 300000, "vehicle_type": "Mini Truck", "fuel_type": "Diesel",
     "description": "Micro truck for narrow lane urban delivery"},
    {"name": "Mahindra Zeo", "price": 400000, "vehicle_type": "Mini Truck", "fuel_type": "Electric",
     "description": "Electric mini truck for green urban logistics"},
    {"name": "Piaggio Ape Auto", "price": 250000, "vehicle_type": "Tempo", "fuel_type": "CNG",
     "description": "Three-wheeler CNG tempo for intra-city last mile delivery"},
    {"name": "Piaggio Ape Xtra", "price": 280000, "vehicle_type": "Tempo", "fuel_type": "CNG",
     "description": "CNG three-wheeler for urban cargo distribution"},
    {"name": "Bajaj RE Auto", "price": 220000, "vehicle_type": "Tempo", "fuel_type": "CNG",
     "description": "CNG auto rickshaw adapted for small cargo transport"},
    {"name": "Atul Gem Paxx", "price": 260000, "vehicle_type": "Tempo", "fuel_type": "CNG",
     "description": "Three-wheeler cargo tempo for perishable goods delivery"},
    # Trailers
    {"name": "Tata 20 FT Container Trailer", "price": 1500000, "vehicle_type": "Trailer", "fuel_type": "Diesel",
     "description": "20 foot container trailer for port-to-warehouse logistics"},
    {"name": "Tata 40 FT Flatbed Trailer", "price": 2200000, "vehicle_type": "Trailer", "fuel_type": "Diesel",
     "description": "40 foot flatbed trailer for steel and machinery transport"},
    {"name": "Ashok Leyland 40 FT Trailer", "price": 2400000, "vehicle_type": "Trailer", "fuel_type": "Diesel",
     "description": "40 foot trailer for heavy cargo and container movement"},
    # Tankers
    {"name": "Tata Water Tanker 1615", "price": 2600000, "vehicle_type": "Tanker", "fuel_type": "Diesel",
     "description": "Water tanker for municipal and construction site supply"},
    {"name": "Ashok Leyland Fuel Tanker", "price": 3200000, "vehicle_type": "Tanker", "fuel_type": "Diesel",
     "description": "Fuel tanker for petroleum product distribution"},
    {"name": "Eicher Milk Tanker 3015", "price": 2800000, "vehicle_type": "Tanker", "fuel_type": "Diesel",
     "description": "Insulated milk tanker for dairy industry logistics"},
]


def build_vehicle_master_api_payload(data: dict = None, dropdown_ids: dict = None) -> dict:
    """Build the Vehicle Master API payload from data + FK IDs.

    Args:
        data: Dict from generate_valid_vehicle_data() or None for random.
        dropdown_ids: Dict of FK IDs. Must contain 'vehicle_type_id'
                      and 'fuel_type_ref_id'. Falls back to placeholder dicts.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    if data is None:
        data = generate_valid_vehicle_data()

    # Resolve FK IDs
    vehicle_type_name = data.get("vehicle_type", "Truck")
    fuel_type_name = data.get("fuel_type", "Diesel")

    default_vehicle_type_id = VEHICLE_TYPE_IDS.get(vehicle_type_name)
    default_fuel_type_id = FUEL_TYPE_IDS.get(fuel_type_name)

    ids = dropdown_ids or {}
    vehicle_type_id = ids.get("vehicle_type_id", default_vehicle_type_id)
    fuel_type_ref_id = ids.get("fuel_type_ref_id", default_fuel_type_id)

    # Price must be numeric
    try:
        price = int(data.get("price", generate_vehicle_price()))
    except (ValueError, TypeError):
        price = generate_vehicle_price()

    payload = {
        "id": "",
        "attribute_name": "Vehicle Master",
        "name": data.get("name", generate_vehicle_name()),
        "vehicle_price": price,
        "vehicle_type_id": vehicle_type_id,
        "fuel_type_ref_id": fuel_type_ref_id,
        "description": data.get("description", generate_description()),
        "status": True,
    }
    return payload


def generate_vehicle_master_api_payload(name_prefix: str = None, dropdown_ids: dict = None) -> dict:
    """One-shot: generate a complete Vehicle Master API payload with realistic data.

    Picks a random entry from REALISTIC_VEHICLE_POOL for authentic Indian
    truck/vehicle names, prices, and descriptions.

    Args:
        name_prefix: If provided, prepended to the vehicle name.
        dropdown_ids: Override specific FK IDs (e.g., vehicle_type_id, fuel_type_ref_id).

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    entry = random.choice(REALISTIC_VEHICLE_POOL)
    name = entry["name"]
    if name_prefix:
        name = f"{name_prefix} {name}"

    data = {
        "name": name,
        "price": entry["price"],
        "vehicle_type": entry["vehicle_type"],
        "fuel_type": entry["fuel_type"],
        "description": entry["description"],
    }
    return build_vehicle_master_api_payload(data, dropdown_ids)


def generate_vehicle_master_api_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None) -> list:
    """Generate multiple unique Vehicle Master API payloads for batch creation.

    Picks unique entries from REALISTIC_VEHICLE_POOL (without replacement).
    If count exceeds pool size, wraps around with random suffix for uniqueness.

    Args:
        count: Number of payloads to generate (default 20).
        prefix: Optional prefix for each vehicle name.
        dropdown_ids: Override specific FK IDs.

    Returns:
        List of JSON payloads.
    """
    pool = list(REALISTIC_VEHICLE_POOL)
    random.shuffle(pool)

    payloads = []
    for i in range(count):
        if i < len(pool):
            entry = pool[i]
            name = entry["name"]
        else:
            entry = random.choice(REALISTIC_VEHICLE_POOL)
            name = f"{entry['name']} {random.randint(100, 999)}"

        if prefix:
            name = f"{prefix} {name}"

        data = {
            "name": name,
            "price": entry["price"],
            "vehicle_type": entry["vehicle_type"],
            "fuel_type": entry["fuel_type"],
            "description": entry["description"],
        }
        payloads.append(build_vehicle_master_api_payload(data, dropdown_ids))

    return payloads