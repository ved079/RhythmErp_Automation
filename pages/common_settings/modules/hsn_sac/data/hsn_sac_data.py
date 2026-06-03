#!/usr/bin/env python3
"""
HSN SAC — Data pool + API payload builder.

Screen: "HSN SAC" (flat, 1 dropdown: hsn_sac_type)
Fields: hsn_sac_no, hsn_sac_type, hsn_sac_description

Discovered FK IDs (2026-06-02):
  hsn_sac_type:
    Services=212, Transportation=162, Commission=161, Commodity=159
"""

import random

# ── Real FK IDs from live ERP ────────────────────────────────────────
HSN_SAC_TYPE_IDS = {
    "Services":       212,
    "Transportation": 162,
    "Commission":     161,
    "Commodity":      159,
}

# ── Realistic data pools ─────────────────────────────────────────────

# Real HSN codes (Commodity) — Chapter-wise from Indian GST system
HSN_COMMODITY = [
    ("0101", "Live horses, asses, mules"),
    ("0201", "Meat of bovine animals, fresh or chilled"),
    ("0301", "Live fish"),
    ("0401", "Milk and cream, not concentrated nor sweetened"),
    ("0701", "Potatoes, fresh or chilled"),
    ("0801", "Coconuts, Brazil nuts and cashew nuts, fresh"),
    ("1001", "Wheat and meslin"),
    ("1006", "Rice"),
    ("1201", "Soya beans, whether or not broken"),
    ("1511", "Palm oil and its fractions"),
    ("1701", "Cane or beet sugar"),
    ("2523", "Portland cement"),
    ("2601", "Iron ores and concentrates"),
    ("2710", "Petroleum oils and oils from bituminous minerals"),
    ("3004", "Medicaments, put up in measured doses"),
    ("3901", "Polymers of ethylene, in primary forms"),
    ("3923", "Plastic articles for packing of goods"),
    ("4011", "New pneumatic tyres of rubber"),
    ("4801", "Newsprint, in rolls or sheets"),
    ("5201", "Cotton, not carded or combed"),
    ("6109", "T-shirts, singlets and other vests, knitted"),
    ("6203", "Men's suits, ensembles, trousers, bib"),
    ("6403", "Footwear with outer soles of rubber/plastics"),
    ("7208", "Flat-rolled products of iron/steel, hot-rolled"),
    ("7318", "Screws, bolts, nuts, washers of iron/steel"),
    ("8471", "Automatic data processing machines and units"),
    ("8501", "Electric motors and generators"),
    ("8517", "Telephone sets, apparatus for transmission of voice"),
    ("8541", "Diodes, transistors, semiconductor devices"),
    ("8703", "Motor cars and vehicles for transporting persons"),
    ("9401", "Seats, whether or not convertible into beds"),
    ("9403", "Furniture, medical, surgical, dental furniture"),
]

# Real SAC codes (Services)
SAC_SERVICES = [
    ("998311", "Licensing services for the right to use computer software"),
    ("998314", "Data processing and hosting services"),
    ("998315", "Computer and related services n.e.c."),
    ("998321", "Consulting services in information technology"),
    ("998322", "IT design and development services"),
    ("998323", "IT support services"),
    ("998411", "Legal advisory and representation services"),
    ("998412", "Accounting, auditing and bookkeeping services"),
    ("998421", "Management consulting and advisory services"),
    ("998422", "Business consulting services"),
    ("998431", "Architectural services"),
    ("998432", "Engineering advisory and consultancy services"),
    ("998511", "Scientific and technical consulting services"),
    ("998521", "Advertising services"),
    ("998522", "Market research and public opinion polling services"),
    ("998531", "Construction services of commercial buildings"),
    ("998541", "Rental services of transport vehicles with operators"),
    ("998611", "Life insurance services"),
    ("998621", "Banking and deposit services"),
    ("998622", "Lending and credit services"),
    ("998631", "Telecommunications services"),
    ("998711", "Accommodation services of hotels"),
    ("998721", "Food and beverage serving services"),
    ("998811", "Education and training services"),
    ("998911", "Health and medical services"),
    ("998921", "Transport of goods by road"),
    ("998931", "Warehousing and storage services"),
    ("998941", "Courier and parcel delivery services"),
]

# Transportation SAC codes
SAC_TRANSPORTATION = [
    ("996411", "Transport of goods by road in a goods carriage"),
    ("996412", "Transport of goods in a goods carriage by rail"),
    ("996413", "Transport of goods by aircraft"),
    ("996414", "Transport of goods by sea"),
    ("996415", "Transport of goods by inland waterways"),
    ("996421", "Transport of passengers by road in a motor vehicle"),
    ("996422", "Transport of passengers by rail"),
    ("996423", "Transport of passengers by aircraft"),
    ("996511", "Rental of freight aircraft with operator"),
    ("996512", "Rental of freight ship with operator"),
]

# Commission SAC codes
SAC_COMMISSION = [
    ("996111", "Commission on sale of goods"),
    ("996112", "Commission on purchase of goods"),
    ("996121", "Commission on foreign exchange transactions"),
    ("996211", "Commission on insurance services"),
    ("996311", "Commission agent services for wholesale trade"),
    ("996312", "Commission agent services for retail trade"),
    ("996321", "Commission on booking of travel"),
    ("996331", "Commission on booking of accommodation"),
    ("996521", "Commission on clearing and forwarding services"),
    ("996531", "Commission on auction services"),
]


# ── Payload builder ──────────────────────────────────────────────────

def build_hsn_sac_api_payload(hsn_sac_no, hsn_sac_type_id, hsn_sac_description):
    """Build a single API payload for HSN SAC."""
    return {
        "id": "",
        "hsn_sac_no": hsn_sac_no,
        "hsn_sac_type": hsn_sac_type_id,
        "hsn_sac_description": hsn_sac_description,
        "attribute_name": "HSN SAC",
    }


def generate_hsn_sac_api_payloads(count=10, fk_ids=None):
    """
    Generate N API payloads for HSN SAC.

    Args:
        count: Number of payloads to generate
        fk_ids: dict with resolved FK IDs (optional, merged with hardcoded)

    Returns:
        list[dict]: List of API payloads
    """
    if fk_ids is None:
        fk_ids = {}

    # Merge discovered FK IDs with hardcoded ones
    sac_type_ids = {**HSN_SAC_TYPE_IDS, **fk_ids.get("hsn_sac_type", {})}

    # Map type names to their data pools
    type_pools = {
        "Commodity":      HSN_COMMODITY,
        "Services":       SAC_SERVICES,
        "Transportation": SAC_TRANSPORTATION,
        "Commission":     SAC_COMMISSION,
    }

    payloads = []
    used_codes = set()

    # Distribute entries across all 4 types
    type_names = list(sac_type_ids.keys())

    for i in range(count):
        # Cycle through types for variety
        type_name = type_names[i % len(type_names)]
        type_id = sac_type_ids[type_name]

        # Get the pool for this type
        pool = type_pools.get(type_name, SAC_SERVICES)

        # Pick an entry from the pool
        code, desc = pool[i % len(pool)]

        # Ensure uniqueness
        if code in used_codes:
            code = f"{code}-{i+1:02d}"
        used_codes.add(code)

        payload = build_hsn_sac_api_payload(
            hsn_sac_no=code,
            hsn_sac_type_id=type_id,
            hsn_sac_description=desc,
        )
        payloads.append(payload)

    return payloads


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# HSN SAC is a flat screen — no children, no steppers.
# 2 standard fields + 1 FK dropdown = 3 fields.

FIELD_VALIDATION_RULES = {
    "hsn_sac_no": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "HSN code (4+ digits) or SAC code (6 digits). Alphanumeric.",
    },
    "hsn_sac_type": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(HSN_SAC_TYPE_IDS),
        "note": "FK to HSN/SAC Type. 4 options: Services, Transportation, Commission, Commodity.",
    },
    "hsn_sac_description": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Human-readable description of the HSN/SAC code.",
    },
}

# HSN SAC Type display names for schema tests
HSN_SAC_TYPE_NAMES = dict(HSN_SAC_TYPE_IDS)

# Default FK IDs for HSN SAC
DEFAULT_HSN_SAC_FK_IDS = {
    "hsn_sac_type": HSN_SAC_TYPE_IDS,
}


def generate_batch_payloads(
    count: int = 20,
    prefix: str = None,
    dropdown_ids: dict = None,
) -> list:
    """Generate a batch of unique HSN SAC API payloads."""
    return generate_hsn_sac_api_payloads(count=count, fk_ids=dropdown_ids)
