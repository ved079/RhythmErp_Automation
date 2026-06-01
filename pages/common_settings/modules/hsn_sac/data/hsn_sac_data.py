"""
HSN SAC — Test Data Generators & Field Constants
===================================================
Module has 3 fields: HSN SAC Number (text), HSN SAC Type (dropdown — 4 fixed),
HSN SAC Description (text — REQUIRED).
"""

import random
from datetime import datetime


# ─── Page URL ────────────────────────────────────────────────────────────────
PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/HSN%20SAC"


# ─── Dropdown Fixed Options ─────────────────────────────────────────────────
# HSN SAC Type has exactly 4 STATIC options — NOT dynamic.
HSN_SAC_TYPE_OPTIONS = [
    "Services",
    "Transportation",
    "Commission",
    "Commodity",
]


# ─── Field Name Constants (match input[name='...']) ────────────────────────
FIELD_HSN_NUMBER = "HSN SAC Number"
FIELD_HSN_TYPE = "HSN SAC Type"
FIELD_HSN_DESC = "HSN SAC Description"


# ─── SweetAlert2 Messages ───────────────────────────────────────────────────
SUCCESS_ADD_MESSAGE = "Your record has been added successfully!"
SUCCESS_UPDATE_MESSAGE = "Your record has been updated successfully!"
VALIDATION_FAILED_TITLE = "Validation Failed"
VALIDATION_FAILED_CONTENT = "Please correct the highlighted fields"


# ─── Table Column Constants ─────────────────────────────────────────────────
COL_VIEW = "mat-column-view"
COL_EDIT = "mat-column-edit"
COL_ARCHIVE = "mat-column-archive"  # History button lives here
COL_HSN_NO = "mat-column-hsn_sac_no"
COL_HSN_TYPE = "mat-column-hsn_sac_type"


# ─── Popup Text ─────────────────────────────────────────────────────────────
POPUP_TITLE = "HSN SAC"
HISTORY_POPUP_TITLE = "HSN SAC History"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Data Generators
# ═══════════════════════════════════════════════════════════════════════════════

def generate_hsn_sac_number() -> str:
    """Generate a random HSN SAC Number (e.g. '998300')."""
    return str(random.randint(100000, 999999))


def generate_hsn_sac_description() -> str:
    """Generate a random HSN SAC Description string."""
    return f"Auto Test HSN Desc {random.randint(1000, 9999)}"


def generate_valid_hsn_sac_data(override=None) -> dict:
    """
    Generate a complete dict with all 3 fields for a valid HSN SAC record.

    Args:
        override: Optional dict to override specific fields.
                  e.g. {"hsn_sac_type": "Services", "hsn_sac_description": "Custom"}

    Returns:
        dict with keys: hsn_sac_number, hsn_sac_type, hsn_sac_description
    """
    data = {
        "hsn_sac_number": generate_hsn_sac_number(),
        "hsn_sac_type": random.choice(HSN_SAC_TYPE_OPTIONS),
        "hsn_sac_description": generate_hsn_sac_description(),
    }
    if override:
        data.update(override)
    return data


def generate_create_test_data() -> dict:
    """Generate data specifically for CREATE tests (all fields filled)."""
    return generate_valid_hsn_sac_data()


def generate_edit_test_data(override=None) -> dict:
    """Generate data for EDIT tests (changed values to update)."""
    return generate_valid_hsn_sac_data(override=override)


# ═══════════════════════════════════════════════════════════════════════════════
# Edge-Case / Negative Test Data
# ═══════════════════════════════════════════════════════════════════════════════

def empty_fields_data() -> dict:
    """All fields empty — triggers Validation Failed."""
    return {
        "hsn_sac_number": "",
        "hsn_sac_type": "",
        "hsn_sac_description": "",
    }


def missing_number_data() -> dict:
    """HSN SAC Number empty, rest filled."""
    return {
        "hsn_sac_number": "",
        "hsn_sac_type": "Services",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


def missing_type_data() -> dict:
    """HSN SAC Type empty, rest filled."""
    return {
        "hsn_sac_number": generate_hsn_sac_number(),
        "hsn_sac_type": "",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


def missing_description_data() -> dict:
    """HSN SAC Description empty, rest filled."""
    return {
        "hsn_sac_number": generate_hsn_sac_number(),
        "hsn_sac_type": "Transportation",
        "hsn_sac_description": "",
    }


def special_chars_number_data() -> dict:
    """Special characters in HSN SAC Number."""
    return {
        "hsn_sac_number": "!@#$%^&*()",
        "hsn_sac_type": "Commission",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


def very_long_number_data() -> dict:
    """256+ character HSN SAC Number."""
    return {
        "hsn_sac_number": "A" * 300,
        "hsn_sac_type": "Commodity",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


def spaces_only_number_data() -> dict:
    """Whitespace-only HSN SAC Number."""
    return {
        "hsn_sac_number": "     ",
        "hsn_sac_type": "Services",
        "hsn_sac_description": generate_hsn_sac_description(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# API Payload Builder
# ═══════════════════════════════════════════════════════════════════════════════
# Converts UI data format into the JSON payload that
# POST /core/dynamic-screen-wrapper/ expects.
#
# HSN SAC SCREEN STRUCTURE (flat — no children/steppers):
#   {
#     "id": "",
#     "attribute_name": "HSN SAC",
#     "hsn_sac_no": "998312",
#     "hsn_sac_type": <FK ID>,
#     "description": "IT support services",
#     "status": true
#   }
#
# FIELD KEY MAPPING:
#   hsn_sac_number     -> hsn_sac_no (text)
#   hsn_sac_type       -> hsn_sac_type (FK dropdown)
#   hsn_sac_description -> description (text)
#   status              -> status (boolean)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── FK ID Placeholders (to be filled from discovery or live API) ────────────
HSN_SAC_TYPE_IDS = {
    "Services": None,
    "Transportation": None,
    "Commission": None,
    "Commodity": None,
}

# ─── Realistic Indian HSN/SAC data pool ─────────────────────────────────────
# Real HSN chapters (01-24) and common SAC codes with descriptions
REALISTIC_HSN_SAC_POOL = [
    # Chapter 01 — Live animals
    {"hsn_sac_no": "0101", "type": "Commodity", "description": "Live horses, asses, mules and hinnies"},
    {"hsn_sac_no": "0102", "type": "Commodity", "description": "Live bovine animals including cows and buffaloes"},
    {"hsn_sac_no": "0103", "type": "Commodity", "description": "Live swine and pigs"},
    # Chapter 02 — Meat and edible meat offal
    {"hsn_sac_no": "0201", "type": "Commodity", "description": "Meat of bovine animals fresh or chilled"},
    {"hsn_sac_no": "0203", "type": "Commodity", "description": "Meat of swine fresh, chilled or frozen"},
    # Chapter 03 — Fish and crustaceans
    {"hsn_sac_no": "0301", "type": "Commodity", "description": "Live fish for aquaculture"},
    {"hsn_sac_no": "0302", "type": "Commodity", "description": "Fish fresh or chilled excluding fillets"},
    # Chapter 04 — Dairy produce
    {"hsn_sac_no": "0401", "type": "Commodity", "description": "Milk and cream not concentrated nor sweetened"},
    {"hsn_sac_no": "0402", "type": "Commodity", "description": "Milk and cream concentrated or sweetened"},
    {"hsn_sac_no": "0405", "type": "Commodity", "description": "Butter and other fats derived from milk"},
    # Chapter 07 — Vegetables
    {"hsn_sac_no": "0701", "type": "Commodity", "description": "Potatoes fresh or chilled"},
    {"hsn_sac_no": "0703", "type": "Commodity", "description": "Onions, shallots and garlic fresh or chilled"},
    # Chapter 08 — Edible fruit and nuts
    {"hsn_sac_no": "0801", "type": "Commodity", "description": "Coconuts, Brazil nuts and cashew nuts fresh"},
    {"hsn_sac_no": "0803", "type": "Commodity", "description": "Bananas and plantains fresh or dried"},
    # Chapter 09 — Coffee, tea, spices
    {"hsn_sac_no": "0901", "type": "Commodity", "description": "Coffee whether or not roasted or decaffeinated"},
    {"hsn_sac_no": "0902", "type": "Commodity", "description": "Tea whether or not flavoured"},
    {"hsn_sac_no": "0908", "type": "Commodity", "description": "Nutmeg, mace and cardamoms"},
    # Chapter 10 — Cereals
    {"hsn_sac_no": "1001", "type": "Commodity", "description": "Wheat and meslin"},
    {"hsn_sac_no": "1005", "type": "Commodity", "description": "Maize corn"},
    {"hsn_sac_no": "1006", "type": "Commodity", "description": "Rice including basmati and non-basmati"},
    # Chapter 11 — Products of milling industry
    {"hsn_sac_no": "1101", "type": "Commodity", "description": "Wheat or meslin flour (atta, maida)"},
    {"hsn_sac_no": "1103", "type": "Commodity", "description": "Cereal groats, meal and pellets"},
    # Chapter 12 — Oil seeds and medicinal plants
    {"hsn_sac_no": "1201", "type": "Commodity", "description": "Soya beans whether or not broken"},
    {"hsn_sac_no": "1207", "type": "Commodity", "description": "Other oil seeds and oleaginous fruits"},
    # Chapter 15 — Animal or vegetable fats and oils
    {"hsn_sac_no": "1507", "type": "Commodity", "description": "Soya-bean oil and its fractions"},
    {"hsn_sac_no": "1508", "type": "Commodity", "description": "Ground-nut oil and its fractions"},
    {"hsn_sac_no": "1511", "type": "Commodity", "description": "Palm oil and its fractions"},
    {"hsn_sac_no": "1515", "type": "Commodity", "description": "Other fixed vegetable fats and oils including linseed oil"},
    # Chapter 17 — Sugars and sugar confectionery
    {"hsn_sac_no": "1701", "type": "Commodity", "description": "Cane or beet sugar and sucrose"},
    # Chapter 18 — Cocoa and cocoa preparations
    {"hsn_sac_no": "1801", "type": "Commodity", "description": "Cocoa beans whole or broken"},
    {"hsn_sac_no": "1806", "type": "Commodity", "description": "Chocolate and other cocoa preparations"},
    # Chapter 19 — Preparations of cereals and flour
    {"hsn_sac_no": "1905", "type": "Commodity", "description": "Bread, pastry, cakes and biscuits"},
    # Chapter 20 — Preparations of vegetables and fruit
    {"hsn_sac_no": "2009", "type": "Commodity", "description": "Fruit juices including grape must"},
    # Chapter 21 — Miscellaneous edible preparations
    {"hsn_sac_no": "2101", "type": "Commodity", "description": "Extracts of coffee, tea or mate and preparations thereof"},
    {"hsn_sac_no": "2106", "type": "Commodity", "description": "Food preparations not elsewhere specified"},
    # Chapter 22 — Beverages
    {"hsn_sac_no": "2201", "type": "Commodity", "description": "Waters including mineral and aerated waters"},
    {"hsn_sac_no": "2202", "type": "Commodity", "description": "Other non-alcoholic beverages including soft drinks"},
    # Chapter 23 — Residues and waste food industry
    {"hsn_sac_no": "2301", "type": "Commodity", "description": "Flours, meals and pellets of meat or fish"},
    {"hsn_sac_no": "2309", "type": "Commodity", "description": "Preparations for animal feeding including poultry feed"},
    # Chapter 24 — Tobacco
    {"hsn_sac_no": "2401", "type": "Commodity", "description": "Unmanufactured tobacco and tobacco refuse"},
    {"hsn_sac_no": "2402", "type": "Commodity", "description": "Cigars, cheroots and cigarillos"},
    {"hsn_sac_no": "2403", "type": "Commodity", "description": "Other manufactured tobacco and substitutes"},
    # Chapter 25 — Salt, sulphur, earth and stone
    {"hsn_sac_no": "2501", "type": "Commodity", "description": "Salt including table salt and sea salt"},
    {"hsn_sac_no": "2523", "type": "Commodity", "description": "Portland cement, aluminous cement and hydraulic cement"},
    # Chapter 27 — Mineral fuels and oils
    {"hsn_sac_no": "2701", "type": "Commodity", "description": "Coal, briquettes and ovoids from coal"},
    {"hsn_sac_no": "2709", "type": "Commodity", "description": "Petroleum oils and oils from bituminous minerals crude"},
    {"hsn_sac_no": "2710", "type": "Commodity", "description": "Petroleum oils and oils from bituminous minerals refined"},
    # Chapter 28 — Inorganic chemicals
    {"hsn_sac_no": "2801", "type": "Commodity", "description": "Fluorine, chlorine, bromine and iodine"},
    {"hsn_sac_no": "2814", "type": "Commodity", "description": "Ammonia anhydrous or in aqueous solution"},
    # Chapter 29 — Organic chemicals
    {"hsn_sac_no": "2901", "type": "Commodity", "description": "Acyclic hydrocarbons"},
    # Chapter 30 — Pharmaceutical products
    {"hsn_sac_no": "3001", "type": "Commodity", "description": "Glands and organs for organo-therapeutic uses"},
    {"hsn_sac_no": "3003", "type": "Commodity", "description": "Medicaments not in dosage form excluding antibiotics"},
    {"hsn_sac_no": "3004", "type": "Commodity", "description": "Medicaments in dosage form including tablets and capsules"},
    # Chapter 33 — Essential oils and cosmetics
    {"hsn_sac_no": "3303", "type": "Commodity", "description": "Perfumes and toilet waters"},
    {"hsn_sac_no": "3304", "type": "Commodity", "description": "Beauty or make-up preparations including skincare"},
    # Chapter 34 — Soap and washing preparations
    {"hsn_sac_no": "3401", "type": "Commodity", "description": "Soap and organic surface-active products in bars"},
    # Chapter 38 — Miscellaneous chemical products
    {"hsn_sac_no": "3808", "type": "Commodity", "description": "Insecticides, rodenticides and herbicides"},
    # Chapter 39 — Plastics and articles thereof
    {"hsn_sac_no": "3901", "type": "Commodity", "description": "Polymers of ethylene in primary forms"},
    {"hsn_sac_no": "3902", "type": "Commodity", "description": "Polymers of propylene in primary forms"},
    # Chapter 40 — Rubber and articles thereof
    {"hsn_sac_no": "4001", "type": "Commodity", "description": "Natural rubber in primary forms or plates"},
    {"hsn_sac_no": "4011", "type": "Commodity", "description": "New pneumatic tyres of rubber"},
    # Chapter 44 — Wood and articles of wood
    {"hsn_sac_no": "4401", "type": "Commodity", "description": "Fuel wood in logs, briquettes or pellets"},
    {"hsn_sac_no": "4418", "type": "Commodity", "description": "Builders joinery and carpentry of wood"},
    # Chapter 48 — Paper and paperboard
    {"hsn_sac_no": "4801", "type": "Commodity", "description": "Newsprint in rolls or sheets"},
    {"hsn_sac_no": "4819", "type": "Commodity", "description": "Cartons, boxes and bags of paper or paperboard"},
    # Chapter 49 — Printed books and newspapers
    {"hsn_sac_no": "4901", "type": "Commodity", "description": "Printed books, brochures and similar publications"},
    # Chapter 52 — Cotton
    {"hsn_sac_no": "5201", "type": "Commodity", "description": "Cotton not carded or combed raw fibre"},
    {"hsn_sac_no": "5205", "type": "Commodity", "description": "Cotton yarn not for retail sale"},
    {"hsn_sac_no": "5208", "type": "Commodity", "description": "Woven cotton fabrics containing 85% or more cotton"},
    # Chapter 54 — Man-made filaments
    {"hsn_sac_no": "5401", "type": "Commodity", "description": "Sewing thread of man-made filaments"},
    # Chapter 55 — Man-made staple fibres
    {"hsn_sac_no": "5501", "type": "Commodity", "description": "Man-made filament tow"},
    # Chapter 61 — Articles of apparel knitted
    {"hsn_sac_no": "6109", "type": "Commodity", "description": "T-shirts, singlets and similar knitted garments"},
    {"hsn_sac_no": "6110", "type": "Commodity", "description": "Sweaters, pullovers and similar knitted garments"},
    # Chapter 62 — Articles of apparel not knitted
    {"hsn_sac_no": "6203", "type": "Commodity", "description": "Men's or boys' suits, ensembles and trousers"},
    {"hsn_sac_no": "6204", "type": "Commodity", "description": "Women's or girls' suits, ensembles and trousers"},
    # Chapter 63 — Other made-up textile articles
    {"hsn_sac_no": "6302", "type": "Commodity", "description": "Bed linen, table linen and toilet linen of cotton"},
    # Chapter 64 — Footwear
    {"hsn_sac_no": "6403", "type": "Commodity", "description": "Footwear with outer soles of rubber or plastics"},
    # Chapter 68 — Articles of stone and plaster
    {"hsn_sac_no": "6810", "type": "Commodity", "description": "Articles of cement, concrete or artificial stone"},
    # Chapter 69 — Ceramic products
    {"hsn_sac_no": "6907", "type": "Commodity", "description": "Ceramic flags, paving and wall tiles"},
    # Chapter 70 — Glass and glassware
    {"hsn_sac_no": "7005", "type": "Commodity", "description": "Float glass and surface ground glass in sheets"},
    # Chapter 72 — Iron and steel
    {"hsn_sac_no": "7201", "type": "Commodity", "description": "Pig iron and spiegeleisen in ingot forms"},
    {"hsn_sac_no": "7208", "type": "Commodity", "description": "Flat-rolled products of iron or steel hot-rolled"},
    {"hsn_sac_no": "7210", "type": "Commodity", "description": "Flat-rolled products of iron or steel clad or plated"},
    # Chapter 73 — Articles of iron or steel
    {"hsn_sac_no": "7304", "type": "Commodity", "description": "Tubes, pipes and hollow profiles of iron or steel"},
    {"hsn_sac_no": "7308", "type": "Commodity", "description": "Structures and parts of structures of iron or steel"},
    # Chapter 74 — Copper and articles thereof
    {"hsn_sac_no": "7403", "type": "Commodity", "description": "Copper cathodes and sections of cathodes"},
    # Chapter 76 — Aluminium and articles thereof
    {"hsn_sac_no": "7601", "type": "Commodity", "description": "Unwrought aluminium including aluminium ingots"},
    {"hsn_sac_no": "7604", "type": "Commodity", "description": "Aluminium bars, rods and profiles"},
    # Chapter 78 — Lead and articles thereof
    {"hsn_sac_no": "7801", "type": "Commodity", "description": "Unwrought lead"},
    # Chapter 80 — Tin and articles thereof
    {"hsn_sac_no": "8001", "type": "Commodity", "description": "Unwrought tin"},
    # Chapter 82 — Tools and implements
    {"hsn_sac_no": "8201", "type": "Commodity", "description": "Hand tools including spades, shovels and picks"},
    # Chapter 83 — Miscellaneous articles of base metal
    {"hsn_sac_no": "8301", "type": "Commodity", "description": "Padlocks and locks of base metal"},
    # Chapter 84 — Machinery and mechanical appliances
    {"hsn_sac_no": "8401", "type": "Commodity", "description": "Nuclear reactors and fuel elements"},
    {"hsn_sac_no": "8409", "type": "Commodity", "description": "Parts for spark-ignition engines including pistons"},
    {"hsn_sac_no": "8415", "type": "Commodity", "description": "Air conditioning machines including split AC units"},
    {"hsn_sac_no": "8418", "type": "Commodity", "description": "Refrigerators, freezers and refrigeration equipment"},
    {"hsn_sac_no": "8421", "type": "Commodity", "description": "Centrifuges and filtering machinery"},
    {"hsn_sac_no": "8422", "type": "Commodity", "description": "Dish washing and bottling machines"},
    {"hsn_sac_no": "8427", "type": "Commodity", "description": "Fork-lift trucks and works trucks"},
    {"hsn_sac_no": "8433", "type": "Commodity", "description": "Harvesting or threshing machinery including combine harvesters"},
    {"hsn_sac_no": "8434", "type": "Commodity", "description": "Milking machines and dairy machinery"},
    {"hsn_sac_no": "8435", "type": "Commodity", "description": "Presses for wine, cider and fruit juices"},
    {"hsn_sac_no": "8443", "type": "Commodity", "description": "Printing machinery including inkjet printers"},
    {"hsn_sac_no": "8461", "type": "Commodity", "description": "Machine tools for planing, shaping and slotting"},
    {"hsn_sac_no": "8471", "type": "Commodity", "description": "Automatic data processing machines including computers"},
    {"hsn_sac_no": "8479", "type": "Commodity", "description": "Machines with individual functions not elsewhere specified"},
    # Chapter 85 — Electrical machinery
    {"hsn_sac_no": "8501", "type": "Commodity", "description": "Electric motors and generators"},
    {"hsn_sac_no": "8504", "type": "Commodity", "description": "Electrical transformers and static converters"},
    {"hsn_sac_no": "8517", "type": "Commodity", "description": "Telephone sets including smartphones"},
    {"hsn_sac_no": "8523", "type": "Commodity", "description": "Discs, tapes and solid-state storage devices"},
    {"hsn_sac_no": "8525", "type": "Commodity", "description": "Transmission apparatus for radio-broadcasting including cameras"},
    {"hsn_sac_no": "8528", "type": "Commodity", "description": "Monitors and projectors including television receivers"},
    {"hsn_sac_no": "8531", "type": "Commodity", "description": "Electric sound or visual signalling equipment including panels"},
    {"hsn_sac_no": "8541", "type": "Commodity", "description": "Semiconductor devices including diodes and transistors"},
    {"hsn_sac_no": "8542", "type": "Commodity", "description": "Electronic integrated circuits and microassemblies"},
    {"hsn_sac_no": "8544", "type": "Commodity", "description": "Insulated wire, cable and optical fibre cables"},
    # Chapter 86 — Railway
    {"hsn_sac_no": "8601", "type": "Commodity", "description": "Rail locomotives powered by external electricity"},
    # Chapter 87 — Vehicles other than railway
    {"hsn_sac_no": "8701", "type": "Commodity", "description": "Tractors including road tractors for semi-trailers"},
    {"hsn_sac_no": "8702", "type": "Commodity", "description": "Motor vehicles for transport of 10 or more persons"},
    {"hsn_sac_no": "8703", "type": "Commodity", "description": "Motor cars and other motor vehicles for passenger transport"},
    {"hsn_sac_no": "8704", "type": "Commodity", "description": "Motor vehicles for transport of goods including trucks"},
    {"hsn_sac_no": "8705", "type": "Commodity", "description": "Special purpose motor vehicles including mobile cranes"},
    {"hsn_sac_no": "8708", "type": "Commodity", "description": "Parts and accessories of motor vehicles"},
    # Chapter 88 — Aircraft
    {"hsn_sac_no": "8802", "type": "Commodity", "description": "Other aircraft including helicopters and aeroplanes"},
    # Chapter 89 — Ships
    {"hsn_sac_no": "8901", "type": "Commodity", "description": "Cruise ships, cargo ships and barges"},
    # Chapter 90 — Optical and medical instruments
    {"hsn_sac_no": "9001", "type": "Commodity", "description": "Optical fibres and cables and lenses"},
    {"hsn_sac_no": "9018", "type": "Commodity", "description": "Instruments for medical, surgical or dental use"},
    {"hsn_sac_no": "9022", "type": "Commodity", "description": "Apparatus based on X-rays including CT scanners"},
    # Chapter 91 — Clocks and watches
    {"hsn_sac_no": "9101", "type": "Commodity", "description": "Wrist-watches and pocket-watches of precious metal"},
    # Chapter 92 — Musical instruments
    {"hsn_sac_no": "9201", "type": "Commodity", "description": "Pianos including automatic pianos"},
    # Chapter 94 — Furniture
    {"hsn_sac_no": "9401", "type": "Commodity", "description": "Seats including chairs and sofas"},
    {"hsn_sac_no": "9403", "type": "Commodity", "description": "Furniture including cabinets and desks"},
    # Chapter 95 — Toys and sports equipment
    {"hsn_sac_no": "9503", "type": "Commodity", "description": "Toys, models and puzzles including board games"},
    {"hsn_sac_no": "9506", "type": "Commodity", "description": "Articles for gymnastics, athletics and outdoor games"},
    # Chapter 96 — Miscellaneous manufactured articles
    {"hsn_sac_no": "9603", "type": "Commodity", "description": "Brooms, brushes and mops"},
    # ─── SAC Codes (Services) ─────────────────────────────────────────────
    {"hsn_sac_no": "9981", "type": "Services", "description": "IT design and development services including software"},
    {"hsn_sac_no": "9983", "type": "Services", "description": "IT support and IT infrastructure services"},
    {"hsn_sac_no": "998311", "type": "Services", "description": "Software implementation support services"},
    {"hsn_sac_no": "998312", "type": "Services", "description": "IT consulting and advisory services"},
    {"hsn_sac_no": "998313", "type": "Services", "description": "IT infrastructure and network management services"},
    {"hsn_sac_no": "998314", "type": "Services", "description": "IT education and training services"},
    {"hsn_sac_no": "998315", "type": "Services", "description": "IT hosting and website management services"},
    {"hsn_sac_no": "998319", "type": "Services", "description": "Other IT services not elsewhere classified"},
    {"hsn_sac_no": "9982", "type": "Services", "description": "Business support services including payroll"},
    {"hsn_sac_no": "998211", "type": "Services", "description": "Human resource management and recruitment services"},
    {"hsn_sac_no": "998212", "type": "Services", "description": "Payroll processing and statutory compliance services"},
    {"hsn_sac_no": "998213", "type": "Services", "description": "Accounting and bookkeeping services"},
    {"hsn_sac_no": "998214", "type": "Services", "description": "Taxation and audit advisory services"},
    {"hsn_sac_no": "9984", "type": "Services", "description": "Other professional, technical and business services"},
    {"hsn_sac_no": "998411", "type": "Services", "description": "Legal services including corporate advisory"},
    {"hsn_sac_no": "998412", "type": "Services", "description": "Architectural and engineering advisory services"},
    {"hsn_sac_no": "998413", "type": "Services", "description": "Scientific research and development services"},
    {"hsn_sac_no": "998414", "type": "Services", "description": "Advertising and brand promotion services"},
    {"hsn_sac_no": "9985", "type": "Services", "description": "Rental and leasing services"},
    {"hsn_sac_no": "998511", "type": "Services", "description": "Leasing or rental services of office machinery"},
    {"hsn_sac_no": "9986", "type": "Services", "description": "Support services to agriculture and forestry"},
    {"hsn_sac_no": "9987", "type": "Services", "description": "Support services to mining and oil extraction"},
    {"hsn_sac_no": "9988", "type": "Services", "description": "Financial and insurance services"},
    {"hsn_sac_no": "998811", "type": "Services", "description": "Banking and depository services"},
    {"hsn_sac_no": "998812", "type": "Services", "description": "Life insurance and annuity services"},
    {"hsn_sac_no": "998813", "type": "Services", "description": "Non-life insurance services including motor and health"},
    {"hsn_sac_no": "9989", "type": "Services", "description": "Education and training services"},
    {"hsn_sac_no": "9991", "type": "Services", "description": "Public administration and other services provided to the community"},
    {"hsn_sac_no": "9992", "type": "Services", "description": "Education services including higher and vocational"},
    {"hsn_sac_no": "9993", "type": "Services", "description": "Health and social services including hospital care"},
    # ─── Transportation SAC codes ──────────────────────────────────────────
    {"hsn_sac_no": "9964", "type": "Transportation", "description": "Freight transport services by road"},
    {"hsn_sac_no": "996411", "type": "Transportation", "description": "Freight transport by road in full truck load"},
    {"hsn_sac_no": "996412", "type": "Transportation", "description": "Freight transport by road in part truck load"},
    {"hsn_sac_no": "996413", "type": "Transportation", "description": "Freight transport by road in container"},
    {"hsn_sac_no": "996421", "type": "Transportation", "description": "Freight transport by railway"},
    {"hsn_sac_no": "9965", "type": "Transportation", "description": "Passenger transport services by road"},
    {"hsn_sac_no": "996511", "type": "Transportation", "description": "Passenger transport by motor bus on inter-city routes"},
    {"hsn_sac_no": "996512", "type": "Transportation", "description": "Passenger transport by motor bus on intra-city routes"},
    {"hsn_sac_no": "9966", "type": "Transportation", "description": "Passenger transport services by water"},
    {"hsn_sac_no": "9967", "type": "Transportation", "description": "Passenger transport services by air"},
    {"hsn_sac_no": "996711", "type": "Transportation", "description": "Air transport of passengers in economy class"},
    {"hsn_sac_no": "996712", "type": "Transportation", "description": "Air transport of passengers in business or first class"},
    {"hsn_sac_no": "9968", "type": "Transportation", "description": "Freight transport services by water"},
    {"hsn_sac_no": "9969", "type": "Transportation", "description": "Freight transport services by air"},
    {"hsn_sac_no": "996911", "type": "Transportation", "description": "Air transport of freight including courier"},
    # ─── Commission SAC codes ──────────────────────────────────────────────
    {"hsn_sac_no": "9970", "type": "Commission", "description": "Commission on sale of goods including agency services"},
    {"hsn_sac_no": "997011", "type": "Commission", "description": "Commission on sale of agricultural produce"},
    {"hsn_sac_no": "997012", "type": "Commission", "description": "Commission on sale of manufactured goods"},
    {"hsn_sac_no": "997013", "type": "Commission", "description": "Commission agent services for wholesale trade"},
    {"hsn_sac_no": "9971", "type": "Commission", "description": "Real estate services including brokerage"},
    {"hsn_sac_no": "997111", "type": "Commission", "description": "Real estate brokerage and agency services for sale"},
    {"hsn_sac_no": "997112", "type": "Commission", "description": "Real estate brokerage for rental and leasing"},
    {"hsn_sac_no": "9972", "type": "Commission", "description": "Commission on financial and insurance products"},
    {"hsn_sac_no": "997211", "type": "Commission", "description": "Commission on mutual fund and insurance distribution"},
    {"hsn_sac_no": "9973", "type": "Commission", "description": "Commission on legal and professional services"},
]


def build_hsn_sac_api_payload(data: dict = None, dropdown_ids: dict = None) -> dict:
    """Build the HSN SAC API payload from data + FK IDs.

    Args:
        data: Dict from generate_valid_hsn_sac_data() or None for random.
        dropdown_ids: Dict of FK IDs. Must contain 'hsn_sac_type'.
                      Falls back to HSN_SAC_TYPE_IDS placeholder if not provided.

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    if data is None:
        data = generate_valid_hsn_sac_data()

    # Resolve the FK ID for hsn_sac_type
    hsn_type_name = data.get("hsn_sac_type", "Services")
    default_type_id = HSN_SAC_TYPE_IDS.get(hsn_type_name)

    ids = dropdown_ids or {}
    type_ref_id = ids.get("hsn_sac_type", default_type_id)

    payload = {
        "id": "",
        "attribute_name": "HSN SAC",
        "hsn_sac_no": data.get("hsn_sac_number", generate_hsn_sac_number()),
        "hsn_sac_type": type_ref_id,
        "description": data.get("hsn_sac_description", generate_hsn_sac_description()),
        "status": True,
    }
    return payload


def generate_hsn_sac_api_payload(name_prefix: str = None, dropdown_ids: dict = None) -> dict:
    """One-shot: generate a complete HSN SAC API payload with realistic data.

    Picks a random entry from REALISTIC_HSN_SAC_POOL for authentic Indian
    HSN/SAC codes and descriptions. Falls back to random generation if
    pool is exhausted.

    Args:
        name_prefix: Ignored (HSN SAC has no name field). Kept for API consistency.
        dropdown_ids: Override specific FK IDs (e.g., hsn_sac_type).

    Returns:
        JSON payload ready for POST /core/dynamic-screen-wrapper/
    """
    entry = random.choice(REALISTIC_HSN_SAC_POOL)
    data = {
        "hsn_sac_number": entry["hsn_sac_no"],
        "hsn_sac_type": entry["type"],
        "hsn_sac_description": entry["description"],
    }
    return build_hsn_sac_api_payload(data, dropdown_ids)


def generate_hsn_sac_api_payloads(count: int = 20, prefix: str = None, dropdown_ids: dict = None) -> list:
    """Generate multiple unique HSN SAC API payloads for batch creation.

    Attempts to pick unique entries from the realistic pool (without
    replacement). If count exceeds pool size, remaining entries use
    random generation.

    Args:
        count: Number of payloads to generate (default 20).
        prefix: Ignored (HSN SAC has no name field).
        dropdown_ids: Override specific FK IDs.

    Returns:
        List of JSON payloads.
    """
    pool = list(REALISTIC_HSN_SAC_POOL)  # make a copy for shuffling
    random.shuffle(pool)

    payloads = []
    for i in range(count):
        if i < len(pool):
            entry = pool[i]
            data = {
                "hsn_sac_number": entry["hsn_sac_no"],
                "hsn_sac_type": entry["type"],
                "hsn_sac_description": entry["description"],
            }
        else:
            data = generate_valid_hsn_sac_data()
        payloads.append(build_hsn_sac_api_payload(data, dropdown_ids))

    return payloads