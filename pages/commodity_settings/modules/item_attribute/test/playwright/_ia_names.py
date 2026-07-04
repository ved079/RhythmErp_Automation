import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

# ── IA1: actual crop names + grade/season qualifier ──────────────────
_IA1_CROPS = [
    # Rice varieties
    "Basmati 1121 Rice", "Basmati 1509 Rice", "Sona Masoori Rice", "IR-64 Rice",
    "PR-106 Rice", "Pusa Basmati Rice", "Swarna Rice", "MTU-7029 Rice",
    "BPT-5204 Rice", "Sarjoo-52 Rice", "Dubraj Rice", "Indrayani Rice",
    "Kolam Rice", "HMT Rice", "Minikit Rice",
    # Wheat varieties
    "Sharbati Wheat", "Lok-1 Wheat", "GW-322 Wheat", "HD-2967 Wheat",
    "PBW-343 Wheat", "K-307 Wheat", "NW-1014 Wheat", "HI-8498 Wheat",
    "MP-3173 Wheat", "GW-496 Wheat",
    # Pulses
    "Chana Dal", "Tur Dal", "Moong Dal", "Urad Dal", "Masoor Dal",
    "Rajma", "Chawli", "Vatana", "Kulthi Dal", "Moth Dal",
    # Oilseeds
    "Soybean", "Groundnut Bold", "Groundnut Java", "Sunflower Seed",
    "Mustard Seed", "Sesame Seed", "Linseed", "Castor Seed",
    "Safflower Seed", "Niger Seed",
    # Cotton
    "Shankar-6 Cotton", "H-4 Cotton", "MCU-5 Cotton", "DCH-32 Cotton",
    "Bunny BT Cotton",
    # Coarse cereals
    "Jowar", "Bajra", "Maize", "Ragi", "Kodo Millet", "Foxtail Millet",
    # Spices & cash crops
    "Turmeric Finger", "Red Chilli Teja", "Coriander Seed", "Cumin Seed",
    "Fenugreek Seed", "Ginger Dry", "Garlic", "Onion Dry",
    # Horticulture
    "Sugarcane", "Potato", "Tomato", "Banana Robusta", "Mango Alphonso",
]

_IA1_QUALIFIERS = [
    "FAQ Grade", "Premium Grade", "Grade A", "Grade B", "Grade C",
    "Export Quality", "Sortex Quality", "Bold Grade", "Medium Grade", "Small Grade",
    "Sun Dried", "Machine Dried", "Raw", "Processed", "Milled",
    "Certified Seed", "Foundation Seed", "Hybrid Seed", "OPV",
    "Kharif Lot", "Rabi Lot",
]

# ── IA2-5: single-word or 2-word real commodity attribute terms ───────
_IA25_TERMS = [
    # Single-word processing/condition
    "Parboiled", "Polished", "Milled", "Sortex", "Graded", "Cleaned",
    "Sieved", "Husked", "Dehusked", "Bleached", "Roasted", "Puffed",
    "Flaked", "Powdered", "Crushed", "Dried", "Fermented", "Sprouted",
    "Steamed", "Pressed", "Refined", "Extracted", "Filtered", "Decorticated",
    # Single-word grade/size
    "Bold", "Fine", "Medium", "Small", "Large", "Extra", "Super",
    "Regular", "Special", "Desi", "Hybrid", "Organic", "Raw", "Premium",
    "Standard", "FAQ", "Certified", "Export", "Local", "Commercial",
    # 2-word combinations
    "Bold Grade", "Fine Meal", "Raw Paddy", "Sun Dried", "Hand Picked",
    "Machine Cleaned", "Double Sortex", "Triple Cleaned", "Steam Processed", "Cold Pressed",
    "Light Weight", "Heavy Weight", "Short Grain", "Long Grain", "Medium Grain",
    "Thin Flake", "Thick Flake", "Coarse Ground", "Fine Ground", "Extra Bold",
    "New Crop", "Old Stock", "Kharif Crop", "Rabi Crop", "Mixed Lot",
    "Dry Milled", "Wet Milled", "Air Cleaned", "Screen Cleaned", "Gravity Sorted",
]


def _unique_ia1_name():
    global _counter
    _counter += 1
    crop      = _rng.choice(_IA1_CROPS)
    qualifier = _rng.choice(_IA1_QUALIFIERS)
    return f"{crop} - {qualifier} {_counter}"


def _unique_ia25_name():
    global _counter
    _counter += 1
    term = _rng.choice(_IA25_TERMS)
    return f"{term} {_counter}"


def _unique_data(attr_num=1):
    if attr_num == 1:
        name = _unique_ia1_name()
    else:
        name = _unique_ia25_name()
    return {
        "name":        name,
        "description": f"Automated attribute entry {_counter}",
    }
