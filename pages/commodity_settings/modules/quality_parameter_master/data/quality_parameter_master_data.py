#!/usr/bin/env python3
"""
Quality Parameter Master — Combined Data Pool + API Payload Builder
& Test Data Providers for Automation

Screen structure (discovered 2026-06-02):
  Quality Parameter Master: name* (text, required, unique)
  FLAT screen — no steppers, no children, no detail tables.
  Only 1 field: name (the quality parameter name).

Existing entries in ERP (as of 2026-06-02):
  Moisture Content, Protein Content, Foreign Matter, Damaged Grains,
  Broken Grains, Weeviled Grains, Admixture Content, Oil Content,
  Ash Content, Fiber Content, Gluten Content, Fat Content,
  Hardness Index, Test Weight, Impurities, Insect Damage,
  Mould Damage, Germination Rate, Shrivelled Grains, Chalky Grains

This module provides:
  - Realistic quality parameter data pool (over 100 entries)
  - API payload construction utilities
  - Test data generators for all validation/boundary scenarios
"""

import random
import string
from datetime import datetime

# =============================================================================
# Part 1: Realistic Data Pool & API Payload Builder
# =============================================================================

# ── Quality Parameter data pool ──────────────────────────────────────
# Each entry is just a name string (the only field on this screen).
#
# Categories covered:
#   - Physical properties (size, shape, color, texture)
#   - Chemical composition (nutrients, contaminants, additives)
#   - Microbiological parameters (bacteria, fungi, toxins)
#   - Sensory parameters (taste, aroma, appearance)
#   - Storage & shelf-life parameters
#   - Regulatory & compliance parameters
#   - Process quality parameters

QUALITY_PARAMETER_DATA = [
    # ── Physical Properties ──────────────────────────────────────────
    "Bulk Density",
    "Particle Size",
    "Color Value",
    "Hardness",
    "Texture Score",
    "Thousand Grain Weight",
    "Hectoliter Weight",
    "Grain Uniformity",
    "Length-Breadth Ratio",
    "Grain Whiteness",
    "Transparency",
    "Water Activity",
    "Viscosity",
    "Specific Gravity",
    "Refractive Index",

    # ── Chemical Composition ─────────────────────────────────────────
    "Starch Content",
    "Sugar Content",
    "Carbohydrate Content",
    "Acid Value",
    "Free Fatty Acid",
    "Peroxide Value",
    "Saponification Value",
    "Iodine Value",
    "pH Level",
    "Titritable Acidity",
    "Total Solids",
    "Total Dissolved Solids",
    "Crude Protein",
    "Crude Fiber",
    "Crude Fat",
    "Nitrogen Content",
    "Phosphorus Content",
    "Potassium Content",
    "Calcium Content",
    "Iron Content",
    "Zinc Content",
    "Sodium Content",
    "Manganese Content",
    "Copper Content",

    # ── Contaminants & Residues ──────────────────────────────────────
    "Pesticide Residue",
    "Heavy Metal Lead",
    "Heavy Metal Arsenic",
    "Heavy Metal Cadmium",
    "Heavy Metal Mercury",
    "Aflatoxin B1",
    "Aflatoxin Total",
    "Ochratoxin A",
    "Deoxynivalenol",
    "Fumonisin",
    "Zearalenone",
    "Mycotoxin Level",
    "Microbial Count",
    "E Coli Count",
    "Salmonella",
    "Coliform Count",
    "Yeast Mold Count",
    "Total Plate Count",

    # ── Food Safety & Regulatory ─────────────────────────────────────
    "Melamine",
    "Antibiotic Residue",
    "Hormone Residue",
    "Dioxin Level",
    "PCB Level",
    "Acrylamide",
    "Benzopyrene",
    "Sudan Dye",
    "Formalin Content",
    "Urea Content",
    "Adulterant Test",
    "Food Additive Level",
    "Preservative Content",
    "Color Additive Level",

    # ── Milling & Processing Quality ─────────────────────────────────
    "Milling Yield",
    "Head Rice Yield",
    "Broken Percentage",
    "Polishing Grade",
    "Grinding Fineness",
    "Extraction Rate",
    "Refining Loss",
    "Dehusking Efficiency",
    "Shelling Efficiency",
    "Parboiling Quality",
    "Cooking Quality",
    "Baking Quality",
    "Swelling Capacity",
    "Water Absorption",
    "Oil Absorption",
    "Cooking Time",

    # ── Storage & Shelf-Life ─────────────────────────────────────────
    "Shelf Life Days",
    "Rancidity Index",
    "Oxidation Level",
    "Moisture Absorption Rate",
    "Storage Stability",
    "Freeze Thaw Stability",
    "Thermal Stability",
    "Odor Score",
    "Freshness Index",
    "Ripeness Index",
    "Maturity Index",

    # ── Sensory Parameters ───────────────────────────────────────────
    "Appearance Score",
    "Aroma Score",
    "Taste Score",
    "Texture Score Mouthfeel",
    "Overall Acceptability",
    "Color Consistency",
    "Flavor Intensity",
    "Bitterness Level",
    "Sweetness Level",
    "Pungency Level",

    # ── Industrial / Process Parameters ──────────────────────────────
    "Tensile Strength",
    "Elongation Percentage",
    "Elasticity",
    "Moisture Regain",
    "Ash Melting Point",
    "Flash Point",
    "Smoke Point",
    "Cloud Point",
    "Pour Point",
    "Cetane Number",
    "Octane Number",
]


def build_quality_parameter_payload(name: str) -> dict:
    """
    Build a single API payload for Quality Parameter Master.

    Args:
        name: Quality parameter name (e.g., "Moisture Content")

    Returns:
        dict: API payload with attribute_name set to "Quality Parameter Master"
    """
    return {
        "id": "",
        "attribute_name": "Quality Parameter Master",
        "name": name,
    }


def generate_quality_parameter_payloads(count: int = 10, offset: int = 0) -> list:
    """
    Generate N API payloads for Quality Parameter Master.

    Args:
        count: Number of payloads to generate
        offset: Start index in the data pool (to skip already-used names)

    Returns:
        list[dict]: List of API payloads
    """
    pool = QUALITY_PARAMETER_DATA
    payloads = []

    for i in range(count):
        idx = (offset + i) % len(pool)
        name = pool[idx]

        # Handle potential duplicate names when wrapping around
        if i >= len(pool):
            name = f"{name}-{i // len(pool) + 1}"

        payloads.append(build_quality_parameter_payload(name))

    return payloads


# =============================================================================
# Part 2: Test Data Providers for Automation
# =============================================================================

# ──────────────────────────────────────────────
# Valid Data Generators
# ──────────────────────────────────────────────

def generate_quality_parameter_name(prefix="AutoQP"):
    """Generate a random Quality Parameter name with prefix and timestamp for uniqueness."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}"


def generate_valid_quality_parameter_data(name_prefix="AutoQP"):
    """Generate a complete dict of valid Quality Parameter data for Create form.
    QPM has only ONE form field: Name (text, required).
    No dropdowns, no price, no description.
    """
    return {
        "name": generate_quality_parameter_name(name_prefix)
    }


def generate_valid_edit_data(name_prefix="EditQP"):
    """Generate valid data for Edit form — new name to update to."""
    return {
        "name": generate_quality_parameter_name(name_prefix)
    }


# ──────────────────────────────────────────────
# Validation Test Data Helpers
# ──────────────────────────────────────────────

def generate_empty_data():
    """Return dict with empty name — for mandatory field validation.
    QPM has only one field, so this is the only empty-case.
    """
    return {
        "name": ""
    }


def generate_spaces_only(length=10):
    """Generate a string of only spaces (for Name validation test).
    BUG-001: Spaces-only name currently creates an empty record.
    Test should expect rejection — will fail until ERP is fixed.
    """
    return " " * length


def generate_spaces_only_data(length=10):
    """Return dict with spaces-only name — for spaces validation test."""
    return {
        "name": generate_spaces_only(length)
    }


def generate_duplicate_name_data(existing_name):
    """Return valid data using an existing name — for duplicate name test.
    BUG-002: Duplicate names are currently allowed with no check.
    Test documents current behavior (known bug, passes as-is).
    """
    return {
        "name": existing_name
    }


def generate_string_255():
    """Generate a string of exactly 255 characters (typical max boundary)."""
    return "A" * 255


def generate_string_256():
    """Generate a string of exactly 256 characters (exceeds typical max).
    BUG-003: No maxlength on input, 300+ char names accepted.
    """
    return "A" * 256


def generate_long_string(length=300):
    """Generate a string of specified length (for maxlength boundary testing).
    BUG-003: ERP accepts very long names without maxlength.
    """
    return "X" * length


def generate_special_char_name():
    """Generate a name with common special characters."""
    special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    return f"QP{special}"


def generate_special_char_data():
    """Return dict with special-character name."""
    return {
        "name": generate_special_char_name()
    }


def generate_sql_injection_name():
    """Generate SQL injection strings to test input sanitization."""
    injections = [
        "' OR '1'='1",
        "'; DROP TABLE quality_parameters; --",
        "1; SELECT * FROM users --",
        "' UNION SELECT * FROM quality_parameters --",
        "\" OR \"1\"=\"1",
    ]
    return random.choice(injections)


def generate_sql_injection_data():
    """Return dict with SQL injection name."""
    return {
        "name": generate_sql_injection_name()
    }


def generate_xss_name():
    """Generate XSS payload strings to test input sanitization."""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(XSS)'>",
    ]
    return random.choice(payloads)


def generate_xss_data():
    """Return dict with XSS payload name."""
    return {
        "name": generate_xss_name()
    }


def generate_unicode_name():
    """Generate a name with unicode/international characters."""
    unicode_samples = [
        "Quality\u00e9",           # Latin é
        "Quality\u00fc",           # Latin ü
        "\u4e2d\u6587\u8d28\u91cf", # 中文质量 (Chinese quality)
        "\u0917\u0941\u0923\u0935\u0924\u094d\u0924\u093e", # गुणवत्ता (Hindi quality)
        "\u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e", # качество (Russian quality)
        "\u54c1\u8cea",             # 品質 (Traditional Chinese quality)
        "Qualit\u00e0",            # Italian à
        "Calid\u00e1d",            # Spanish á
    ]
    return random.choice(unicode_samples)


def generate_unicode_data():
    """Return dict with unicode name."""
    return {
        "name": generate_unicode_name()
    }


def generate_name_with_leading_trailing_spaces():
    """Generate a name with leading and trailing spaces.
    Tests whether ERP trims whitespace before storing.
    """
    base = generate_quality_parameter_name("SpaceQP")
    return f"   {base}   "


def generate_name_with_inner_spaces():
    """Generate a valid name containing inner spaces (should be accepted)."""
    return f"Quality Parameter {random.randint(1000, 9999)}"


def generate_name_with_numbers():
    """Generate a name that is purely numeric."""
    return str(random.randint(100000, 999999))


def generate_name_with_mixed_case():
    """Generate a name with mixed upper/lower case to test case sensitivity."""
    name = generate_quality_parameter_name("MixQP")
    # Alternate case for every other character
    return ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(name))


def generate_tab_character_name():
    """Generate a name containing tab characters."""
    return f"QP\tName\tTest"


def generate_newline_name():
    """Generate a name containing newline characters."""
    return f"QP\nName"


def generate_single_char_name():
    """Generate a single-character name (minimum meaningful input)."""
    return random.choice(string.ascii_uppercase)


def generate_name_with_emoji():
    """Generate a name containing emoji characters."""
    emojis = ["\u2728", "\u2705", "\u26a0", "\u274c", "\u2b50"]
    return f"QP{random.choice(emojis)}Test"