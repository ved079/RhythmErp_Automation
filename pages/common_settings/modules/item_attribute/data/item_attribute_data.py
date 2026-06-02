#!/usr/bin/env python3
"""
Item Attribute — Generic Data Pool + API Payload Builder

Works for ALL 5 Item Attribute screens (Item Attribute1 through Item Attribute5).

Screen structures (discovered 2026-06-02):
  Item Attribute1: name*, base_uom* (FK→UOM), description, status  — Commodities/Products
  Item Attribute2: name*, description, status                       — Packaging
  Item Attribute3: name*, description, status                       — Quality/Tracking
  Item Attribute4: name*, description, status                       — Material/Packaging Type
  Item Attribute5: name*, description, status                       — Certification/Origin

All 5 are FLAT (no steppers/children).
Item Attribute1 has an extra base_uom FK field; the rest are identical.

Discovered FK IDs:
  base_uom (Item Attribute1 only): 42 UOM options
    KG=249, MT=250, QT=251, NOS=252, Litres=253,
    LTR=501, MTR=502, dozens=504, Litre=506, ML=507,
    MUND=528, BIGHA=529, SER=530, CAN=531, SQFT=532,
    SET=533, KM=534, HP=535, MM=536, SET60=537
"""

import random

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
