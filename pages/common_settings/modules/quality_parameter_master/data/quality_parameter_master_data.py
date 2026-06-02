#!/usr/bin/env python3
"""
Quality Parameter Master — Data Pool + API Payload Builder

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

This data pool provides additional quality parameter names NOT already
in the system, covering agricultural, food processing, pharma, and
industrial quality parameters.
"""

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
