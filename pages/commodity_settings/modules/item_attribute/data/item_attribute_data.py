#!/usr/bin/env python3
"""
Item Attribute — Combined Data Provider & API Payload Builder

Covers all 5 Item Attribute screens (Item Attribute1 through Item Attribute5).
- Realistic data pools with discovered FK IDs
- API payload construction
- Test data generators for validation & boundary testing
"""

import random
import string
from datetime import datetime

# =============================================================================
# Part 1: Generic Data Pool + API Payload Builder
# =============================================================================

# ── Real FK IDs from live ERP ────────────────────────────────────────
UOM_IDS = {
    "KG":      249,
    "MT":      250,
    "QT":      251,
    "NOS":     252,
    "Litres":  253,
    "LTR":     501,
    "MTR":     502,
    "dozens":  504,
    "Litre":   506,
    "ML":      507,
    "MUND":    528,
    "BIGHA":   529,
    "SER":     530,
    "CAN":     531,
    "SQFT":    532,
    "SET":     533,
    "KM":      534,
    "HP":      535,
    "MM":      536,
    "SET60":   537,
}

# ── Realistic data pools per attribute type ──────────────────────────

# Item Attribute1 — Commodities / Products (with base_uom)
# Each entry: (name, base_uom_name, description)
ATTRIBUTE1_DATA = [
    # Cereals & Grains
    ("Wheat",           "MT",  "Wheat grain for flour milling and food processing"),
    ("Rice",            "MT",  "Rice paddy and processed rice varieties"),
    ("Maize",           "MT",  "Maize corn for animal feed and industrial use"),
    ("Bajra",           "QT",  "Pearl millet for food and fodder"),
    ("Jowar",           "QT",  "Sorghum grain for food and brewing"),
    ("Ragi",            "KG",  "Finger millet for flour and nutritional products"),
    ("Barley",          "MT",  "Barley grain for brewing and animal feed"),
    ("Oats",            "KG",  "Oats for breakfast cereals and animal feed"),
    ("Millets",         "KG",  "Mixed millets for health food products"),
    ("Quinoa",          "KG",  "Quinoa seeds for premium health food market"),
    # Pulses & Legumes
    ("Tur Dal",         "QT",  "Pigeon pea for dal production"),
    ("Chana Dal",       "QT",  "Split chickpea for dal and flour"),
    ("Moong Dal",       "KG",  "Mung bean for dal and sprouting"),
    ("Urad Dal",        "KG",  "Black gram for dal and batter"),
    ("Masoor Dal",      "KG",  "Red lentil for dal preparation"),
    ("Soybean",         "MT",  "Soybean for oil extraction and protein products"),
    ("Groundnut",       "KG",  "Groundnut for oil and confectionery"),
    ("Chickpea",        "QT",  "Kabuli and desi chickpea varieties"),
    ("Kidney Beans",    "KG",  "Rajma kidney beans for food processing"),
    ("Peas",            "KG",  "Dried peas for food and snack industry"),
    # Oilseeds
    ("Mustard",         "KG",  "Mustard oilseeds for oil extraction"),
    ("Sunflower",       "MT",  "Sunflower seeds for oil and snacks"),
    ("Sesame",          "KG",  "Sesame seeds for oil and confectionery"),
    ("Safflower",       "KG",  "Safflower seeds for edible oil"),
    ("Linseed",         "KG",  "Linseed for industrial oil and nutrition"),
    # Spices
    ("Turmeric",        "KG",  "Turmeric rhizomes for spice and dye"),
    ("Chilli",          "KG",  "Red chilli for spice and oleoresin"),
    ("Coriander",       "KG",  "Coriander seeds for spice production"),
    ("Cumin",           "KG",  "Cumin seeds for spice blending"),
    ("Black Pepper",    "KG",  "Black pepper corns for spice industry"),
    ("Cardamom",        "KG",  "Green cardamom for premium spice market"),
    ("Clove",           "KG",  "Clove buds for spice and essential oil"),
    ("Cinnamon",        "KG",  "Cinnamon bark for spice and flavoring"),
    ("Ginger",          "KG",  "Ginger rhizome for spice and medicinal use"),
    ("Garlic",          "KG",  "Garlic bulbs for food and health products"),
    # Vegetables
    ("Potato",          "QT",  "Potato tubers for food and processing"),
    ("Onion",           "QT",  "Onion bulbs for fresh market and dehydration"),
    ("Tomato",          "KG",  "Tomatoes for fresh market and paste production"),
    ("Cabbage",         "KG",  "Cabbage for fresh market and processing"),
    ("Cauliflower",     "KG",  "Cauliflower for fresh market"),
    # Fruits
    ("Mango",           "MT",  "Mangoes for fresh market and pulp processing"),
    ("Apple",           "MT",  "Apples for fresh market and juice"),
    ("Banana",          "QT",  "Bananas for fresh market and chips"),
    ("Grapes",          "KG",  "Grapes for fresh market and wine production"),
    ("Orange",          "KG",  "Oranges for fresh market and juice"),
    # Cash Crops
    ("Cotton",          "QT",  "Raw cotton for ginning and textile industry"),
    ("Sugarcane",       "MT",  "Sugarcane for sugar and ethanol production"),
    ("Coffee",          "KG",  "Coffee beans for roasting and export"),
    ("Tea",             "KG",  "Tea leaves for processing and packaging"),
    ("Rubber",          "KG",  "Natural rubber latex for industrial use"),
    ("Tobacco",         "KG",  "Tobacco leaves for cigarette and export"),
    ("Jute",            "MT",  "Jute fiber for bags and textile industry"),
    ("Coconut",         "NOS", "Coconuts for copra, oil and coir products"),
    ("Arecanut",        "KG",  "Arecanut for gutkha and traditional use"),
]

# Item Attribute2 — Packaging Type
ATTRIBUTE2_DATA = [
    ("Vacuum Sealed",       "Packed with vacuum sealing for extended freshness and shelf life"),
    ("Packed in Jute",      "Stored and transported in breathable jute bags for agricultural produce"),
    ("PP Bag",              "Polypropylene woven bag packaging for bulk commodities"),
    ("HDPE Bag",            "High-density polyethylene bag for moisture-resistant storage"),
    ("Paper Bag",           "Multi-wall paper bag for flour and cement packaging"),
    ("Tin Container",       "Metal tin container for oil and processed food products"),
    ("Glass Jar",           "Glass jar packaging for preserves and premium products"),
    ("Plastic Crate",       "Reusable plastic crate for fresh produce transport"),
    ("Wooden Box",          "Wooden box packaging for heavy and fragile items"),
    ("Corrugated Box",      "Corrugated cardboard box for shipping and distribution"),
    ("Shrink Wrapped",      "Shrink wrap film packaging for unit bundling"),
    ("Bulk Container",      "Large bulk container for industrial commodity shipping"),
    ("FIBC Jumbo Bag",      "Flexible intermediate bulk container for dry goods"),
    ("Drum Barrel",         "Steel or plastic drum for liquid and chemical storage"),
    ("Pouch Pack",          "Flexible pouch packaging for retail and single-serve"),
    ("Laminated Pouch",     "Multi-layer laminated pouch for extended shelf life"),
    ("Carton Pack",         "Paperboard carton for retail display packaging"),
    ("Mesh Bag",            "Net mesh bag for onion and citrus produce"),
    ("Retort Pouch",        "Heat-resistant retort pouch for ready-to-eat meals"),
    ("Aseptic Bag",         "Aseptic bulk bag for fruit pulp and liquid storage"),
]

# Item Attribute3 — Quality / Tracking
ATTRIBUTE3_DATA = [
    ("Product Grade",       "Product quality grade classification"),
    ("Lot Number",          "Batch or lot identification for traceability"),
    ("Organic Certified",   "Certified organic produce under NPOP standards"),
    ("Conventional",        "Conventionally grown produce without organic certification"),
    ("Premium Grade",       "Top-tier quality grade meeting highest specifications"),
    ("Standard Grade",      "Standard quality grade meeting baseline specifications"),
    ("Economy Grade",       "Economy quality grade for price-sensitive markets"),
    ("Export Quality",       "Quality grade meeting export standards and phytosanitary norms"),
    ("First Sort",          "First sorting grade with minimal defect tolerance"),
    ("Second Sort",         "Second sorting grade with acceptable defect levels"),
    ("Rejected",            "Rejected quality — does not meet minimum standards"),
    ("Quarantine Hold",     "Under quarantine inspection — pending quality clearance"),
    ("Lab Tested",          "Laboratory tested and certified for quality parameters"),
    ("Sample Lot",          "Sample lot for quality evaluation and testing"),
    ("Reprocess Grade",     "Material requiring reprocessing before acceptance"),
    ("Food Grade",          "Meets food-grade safety and hygiene standards"),
    ("Industrial Grade",    "Suitable for industrial processing but not direct consumption"),
    ("Pharma Grade",        "Meets pharmaceutical purity and quality standards"),
    ("Fresh Produce",       "Freshly harvested produce with minimal storage time"),
    ("Cold Stored",         "Properly cold-stored produce maintaining freshness"),
]

# Item Attribute4 — Material / Packaging Type
ATTRIBUTE4_DATA = [
    ("Multi Layered",       "Triple layer construction for superior protection and durability"),
    ("Recyclable",          "Made from fully recyclable materials for sustainability"),
    ("Biodegradable",       "Made from biodegradable materials reducing environmental impact"),
    ("Single Use",          "Designed for one-time use — disposable packaging"),
    ("Reusable",            "Designed for multiple use cycles — returnable packaging"),
    ("Laminated",           "Multi-layer lamination for barrier and strength properties"),
    ("Uncoated",            "Raw uncoated material without surface treatment"),
    ("Coated",              "Surface-coated material for moisture or chemical resistance"),
    ("Foil Lined",          "Aluminum foil lining for thermal and moisture barrier"),
    ("BOPP Film",           "Biaxially oriented polypropylene film wrapping"),
    ("Kraft Paper",         "Natural kraft paper for eco-friendly packaging"),
    ("Bleached Paper",      "White bleached paper for premium product packaging"),
    ("Woven Fabric",        "Woven polypropylene or jute fabric bag construction"),
    ("Non-Woven Fabric",    "Non-woven fabric bag for lightweight packaging"),
    ("Rigid Plastic",       "Hard plastic container for structural integrity"),
    ("Flexible Film",       "Thin flexible film for wrapping and sealing"),
    ("Metal Tinplate",      "Tinplate metal container for canned products"),
    ("Composite",           "Multi-material composite packaging for performance"),
    ("Foam Insulated",      "Foam-insulated container for temperature-sensitive goods"),
    ("Vacuum Formed",       "Vacuum-formed plastic tray for product presentation"),
]

# Item Attribute5 — Certification / Origin
ATTRIBUTE5_DATA = [
    ("Certified Origin",          "Geographical indication certified origin produce"),
    ("Sorted Graded",             "Sorted and graded quality produce"),
    ("FSSAI Approved",            "Approved by Food Safety and Standards Authority of India"),
    ("ISO 22000",                 "Certified under ISO 22000 food safety management system"),
    ("HACCP Certified",           "Hazard Analysis Critical Control Point certified facility"),
    ("GMP Certified",             "Good Manufacturing Practice certified production"),
    ("Fair Trade",                "Fair trade certified ensuring equitable trading practices"),
    ("Rainforest Alliance",       "Rainforest Alliance certified for sustainable farming"),
    ("UTZ Certified",             "UTZ certified for sustainable agricultural practices"),
    ("Global GAP",                "Global Good Agricultural Practice certified"),
    ("India Organic",             "Certified organic under India Organic standards"),
    ("USDA Organic",              "Certified organic under USDA National Organic Program"),
    ("EU Organic",                "Certified organic under European Union organic standards"),
    ("APEDA Certified",           "Agricultural and Processed Food Products Export certification"),
    ("AGMARK",                    "AGMARK quality certification by Directorate of Marketing"),
    ("BIS Certified",             "Bureau of Indian Standards certified product quality"),
    ("Halal Certified",           "Halal certification for permissible food products"),
    ("Kosher Certified",          "Kosher certification meeting Jewish dietary requirements"),
    ("Non-GMO Verified",          "Verified non-GMO product — no genetic modification"),
    ("Gluten Free",               "Certified gluten-free for dietary restriction compliance"),
]

# Map attribute number to its data pool and label
ATTRIBUTE_POOLS = {
    1: ("Commodity/Product",  ATTRIBUTE1_DATA),
    2: ("Packaging Type",    ATTRIBUTE2_DATA),
    3: ("Quality/Tracking",  ATTRIBUTE3_DATA),
    4: ("Material Type",     ATTRIBUTE4_DATA),
    5: ("Certification",     ATTRIBUTE5_DATA),
}


# ── Payload builder ──────────────────────────────────────────────────

def build_item_attribute_payload(attr_number, name, description="", base_uom_id=None, status=True):
    """
    Build a single API payload for an Item Attribute screen.

    Args:
        attr_number: 1-5 (determines the attribute_name)
        name: Attribute value name (e.g., "Wheat", "Vacuum Sealed")
        description: Optional description text
        base_uom_id: FK ID for UOM (only used for Item Attribute1)
        status: Active/inactive status
    """
    payload = {
        "id": "",
        "attribute_name": f"Item Attribute{attr_number}",
        "name": name,
        "description": description,
        "status": status,
    }

    # Item Attribute1 has an extra base_uom FK field
    if attr_number == 1 and base_uom_id is not None:
        payload["base_uom"] = base_uom_id

    return payload


def generate_item_attribute_payloads(attr_number, count=10, fk_ids=None):
    """
    Generate N API payloads for a specific Item Attribute screen.

    Args:
        attr_number: 1-5
        count: Number of payloads to generate
        fk_ids: dict with resolved FK IDs (optional, merged with hardcoded)

    Returns:
        list[dict]: List of API payloads
    """
    if fk_ids is None:
        fk_ids = {}

    if attr_number not in ATTRIBUTE_POOLS:
        raise ValueError(f"Invalid attr_number: {attr_number}. Must be 1-5.")

    label, pool = ATTRIBUTE_POOLS[attr_number]

    # For Attribute1, merge UOM IDs
    uom_ids = {**UOM_IDS, **fk_ids.get("base_uom", {})}

    payloads = []
    used_names = set()

    for i in range(count):
        # Get existing entry names to avoid duplicates
        entry = pool[i % len(pool)]

        if attr_number == 1:
            # Attribute1: (name, base_uom_name, description)
            name = entry[0]
            uom_name = entry[1]
            desc = entry[2]
            base_uom_id = uom_ids.get(uom_name, 249)  # Default to KG

            # Handle duplicate names
            if name in used_names:
                name = f"{name}-{i+1:02d}"
            used_names.add(name)

            payload = build_item_attribute_payload(
                attr_number=attr_number,
                name=name,
                description=desc,
                base_uom_id=base_uom_id,
            )
        else:
            # Attribute2-5: (name, description)
            name = entry[0]
            desc = entry[1]

            if name in used_names:
                name = f"{name}-{i+1:02d}"
            used_names.add(name)

            payload = build_item_attribute_payload(
                attr_number=attr_number,
                name=name,
                description=desc,
            )

        payloads.append(payload)

    return payloads


def generate_all_attribute_payloads(count=10, fk_ids=None):
    """
    Generate payloads for ALL 5 Item Attribute screens.

    Args:
        count: Number of payloads per screen
        fk_ids: dict with resolved FK IDs

    Returns:
        dict: {attr_number: [payloads], ...}
    """
    all_payloads = {}
    for attr_number in range(1, 6):
        all_payloads[attr_number] = generate_item_attribute_payloads(
            attr_number, count=count, fk_ids=fk_ids
        )
    return all_payloads


# =============================================================================
# Part 2: Test Data Providers for Automation
# =============================================================================

"""
item_attribute_data.py
----------------------
Test data provider for RhythmERP Item Attribute 1-5 automation.

Generates realistic test data for all screens. Key differences:
  - Item Attribute 1 has an extra "Base UOM" dropdown (required)
  - Item Attributes 2-5 have only: Name (required), Description, Status
  - Name input uses capital 'N' attribute: name="Name"
  - Status toggle: Active/Inactive (default ON = Active)
  - Base UOM options: 5, 10, 15 (simple numeric values)
  - Duplicate Names: ALLOWED (BUG-001, same as Item Master pattern)
  - Simple popup form (NOT a stepper)
"""

# ------------------------------------------------------------------
# Valid Data Generators
# ------------------------------------------------------------------

def generate_name(prefix="AutoIA"):
    """Generate a unique attribute name with prefix and timestamp.
    Format: PREFIX_HHMMSS_RAND
    """
    timestamp = datetime.now().strftime("%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_data(attr_num=1, name_prefix="AutoIA"):
    """Generate a complete dict of valid Item Attribute data.

    attr_num=1 includes base_uom field; attr_num 2-5 omit it.
    Dropdowns use "" (empty string) which means "select random at runtime".
    """
    data = {
        "name": generate_name(name_prefix),
        "description": f"Auto test attribute {datetime.now().strftime('%H%M%S')}",
    }

    # Item Attribute 1 has Base UOM
    if attr_num == 1:
        data["base_uom"] = ""  # Random selection from live UI

    # Status toggle — default is ON (Active)
    data["status"] = True

    return data


def generate_minimal_valid_data(attr_num=1):
    """Generate only the required fields.
    Required: Name (always), Base UOM (IA1 only).
    """
    data = {
        "name": generate_name("MIN"),
    }
    if attr_num == 1:
        data["base_uom"] = ""  # Random selection
    return data


# ------------------------------------------------------------------
# Validation Test Data — Missing Required Fields
# ------------------------------------------------------------------

def generate_empty_name(attr_num=1):
    """Data with Name field empty (required field)."""
    data = {
        "name": "",
        "description": "Testing empty name",
    }
    if attr_num == 1:
        data["base_uom"] = ""  # Will be selected
    data["status"] = True
    return data


def generate_spaces_name(attr_num=1):
    """Data with Name containing only spaces."""
    data = generate_valid_data(attr_num, name_prefix="   ")
    data["name"] = "     "
    return data


def generate_missing_base_uom():
    """Data with Base UOM missing (IA1 only, required field).
    Only valid for attr_num=1.
    """
    data = {
        "name": generate_name("NOUOM"),
        "description": "Testing missing Base UOM",
        # base_uom key NOT included — skip dropdown entirely
        "status": True,
    }
    return data


def generate_all_required_missing(attr_num=1):
    """Data with ALL required fields missing."""
    data = {
        "name": "",
        "description": "",
    }
    if attr_num == 1:
        data["base_uom"] = ""  # Will NOT be selected (empty = skip)
        del data["base_uom"]   # Actually remove it to skip the dropdown
    data["status"] = True
    return data


# ------------------------------------------------------------------
# Duplicate Name Data
# ------------------------------------------------------------------

def generate_duplicate_name_data(attr_num=1):
    """Data for duplicate attribute name test.
    BUG-001: Duplicate Names are ALLOWED (expected behavior).
    """
    return generate_valid_data(attr_num, name_prefix="DUP")


# ------------------------------------------------------------------
# Boundary Test Data
# ------------------------------------------------------------------

def generate_long_name(length=256, attr_num=1):
    """Generate a Name of extreme length to test maxlength constraint.
    Server accepts up to 255 chars, rejects 256+.
    BUG-004: No maxlength attribute on Name field.
    """
    data = {
        "name": "X" * length,
        "description": "Testing long name",
    }
    if attr_num == 1:
        data["base_uom"] = ""
    data["status"] = True
    return data


def generate_long_description(length=256, attr_num=1):
    """Generate a Description of extreme length to test maxlength constraint.
    Server accepts up to 255 chars, rejects 256+.
    BUG-004: No maxlength attribute on Description field.
    """
    data = {
        "name": f"AutoIA_DescLen{length}",
        "description": "D" * length,
    }
    if attr_num == 1:
        data["base_uom"] = ""
    data["status"] = True
    return data


def generate_special_char_name(attr_num=1):
    """Generate a Name with special characters."""
    specials = [
        "!@#$_Test",
        "Attr-Code.v2",
        "Test (Copy)",
        "Attr & Co.",
        "Code+Plus=Minus",
    ]
    data = generate_valid_data(attr_num, name_prefix="SPC")
    data["name"] = random.choice(specials)
    return data


def generate_sql_injection_name(attr_num=1):
    """Generate SQL injection strings for Name field."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE items; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM items --",
    ]
    data = generate_valid_data(attr_num, name_prefix="SQL")
    data["name"] = random.choice(injections)
    return data


def generate_xss_name(attr_num=1):
    """Generate XSS payload strings for Name field."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
    ]
    data = generate_valid_data(attr_num, name_prefix="XSS")
    data["name"] = random.choice(payloads)
    return data


def generate_unicode_name(attr_num=1):
    """Generate a Name with unicode/international characters."""
    unicode_samples = [
        f"Attr\u00e9{random.randint(100, 999)}",         # Latin e-acute
        f"\u4e2d\u6587{random.randint(100, 999)}",        # Chinese
        f"Attr\u00fc{random.randint(100, 999)}",          # Latin u-umlaut
    ]
    data = generate_valid_data(attr_num, name_prefix="UNI")
    data["name"] = random.choice(unicode_samples)
    return data


def generate_numeric_name(attr_num=1):
    """Generate a purely numeric Name."""
    data = generate_valid_data(attr_num, name_prefix="NUM")
    data["name"] = str(random.randint(100000, 999999))
    return data


# ------------------------------------------------------------------
# Toggle State Data
# ------------------------------------------------------------------

def generate_status_on(attr_num=1):
    """Data with Status toggle ON (Active)."""
    data = generate_minimal_valid_data(attr_num)
    data["status"] = True
    return data


def generate_status_off(attr_num=1):
    """Data with Status toggle OFF (Inactive)."""
    data = generate_minimal_valid_data(attr_num)
    data["status"] = False
    return data


# ------------------------------------------------------------------
# Edit Mode Specific Data
# ------------------------------------------------------------------

def generate_edit_only_name(attr_num=1):
    """Edit data: only Name changed."""
    return {
        "name": generate_name("EDITNM"),
    }


def generate_edit_only_description(attr_num=1):
    """Edit data: only Description changed."""
    return {
        "description": f"Updated desc {datetime.now().strftime('%H%M%S')}",
    }


def generate_edit_change_base_uom():
    """Edit data: change Base UOM (IA1 only)."""
    return {
        "base_uom": "",  # Will select a different random option
    }


def generate_edit_toggle_status():
    """Edit data: toggle Status."""
    return {
        "status": False,  # Toggle to Inactive
    }


def generate_edit_all_fields(attr_num=1):
    """Edit data: change all fields."""
    data = {
        "name": generate_name("EDITALL"),
        "description": f"Edited all {datetime.now().strftime('%H%M%S')}",
        "status": False,
    }
    if attr_num == 1:
        data["base_uom"] = ""
    return data


# ──────────────────────────────────────────────
# FIELD VALIDATION RULES (from live ERP schema)
# ──────────────────────────────────────────────
# Item Attribute1 has 4 fields (including base_uom FK)
# Item Attribute2-5 have 3 fields each (no FK)

FIELD_VALIDATION_RULES = {
    "name": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Attribute value name. Duplicates currently allowed (BUG-001).",
    },
    "description": {
        "type": "character",
        "required": False,
        "max_length": 255,
        "note": "Optional description of the attribute value.",
    },
    "base_uom": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": len(UOM_IDS),
        "note": "FK to UOM. Only present on Item Attribute1. ~20 UOM options.",
    },
    "status": {
        "type": "toggle",
        "required": False,
        "default": True,
        "note": "Active/Inactive toggle. Default: Active (True).",
    },
}

STATUS_OPTIONS = {"Active": True, "Inactive": False}

UOM_NAMES = dict(UOM_IDS)

DEFAULT_ITEM_ATTRIBUTE_FK_IDS = {
    "base_uom": UOM_IDS,
}


def generate_batch_payloads(count=20, prefix=None, dropdown_ids=None):
    """Generate batch payloads for Item Attribute1 (the primary screen with FK)."""
    return generate_item_attribute_payloads(attr_number=1, count=count, fk_ids=dropdown_ids)