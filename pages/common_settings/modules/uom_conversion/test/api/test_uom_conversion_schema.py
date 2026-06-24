"""
test_uom_conversion_schema.py — Verify UOM Conversion code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    get_field_validation_rules,
    UOM_IDS,
)


@pytest.mark.schema
class TestUOMConversionSchema:
    """Verify the UOM Conversion screen schema matches our code expectations."""

    def test_field_validation_rules_has_source_uom_code(self):
        """FIELD_VALIDATION_RULES must include source_uom_code."""
        rules = get_field_validation_rules()
        assert "source_uom_code" in rules

    def test_field_validation_rules_has_target_uom_code(self):
        """FIELD_VALIDATION_RULES must include target_uom_code."""
        rules = get_field_validation_rules()
        assert "target_uom_code" in rules

    def test_field_validation_rules_has_conversion_factor(self):
        """FIELD_VALIDATION_RULES must include conversion_factor."""
        rules = get_field_validation_rules()
        assert "conversion_factor" in rules

    def test_field_validation_rules_has_3_fields(self):
        """UOM Conversion has exactly 3 fields."""
        rules = get_field_validation_rules()
        assert len(rules) == 3
        assert set(rules.keys()) == {
            "source_uom_code", "target_uom_code", "conversion_factor"
        }

    def test_source_uom_code_is_required(self):
        """source_uom_code must be marked as required."""
        rules = get_field_validation_rules()
        assert rules["source_uom_code"]["required"] is True

    def test_target_uom_code_is_required(self):
        """target_uom_code must be marked as required."""
        rules = get_field_validation_rules()
        assert rules["target_uom_code"]["required"] is True

    def test_conversion_factor_is_required(self):
        """conversion_factor must be marked as required."""
        rules = get_field_validation_rules()
        assert rules["conversion_factor"]["required"] is True

    def test_source_uom_code_is_dropdown(self):
        """source_uom_code type should be 'dropdown'."""
        rules = get_field_validation_rules()
        assert rules["source_uom_code"]["type"] == "dropdown"

    def test_target_uom_code_is_dropdown(self):
        """target_uom_code type should be 'dropdown'."""
        rules = get_field_validation_rules()
        assert rules["target_uom_code"]["type"] == "dropdown"

    def test_conversion_factor_is_number(self):
        """conversion_factor type should be 'number'."""
        rules = get_field_validation_rules()
        assert rules["conversion_factor"]["type"] == "number"

    def test_source_uom_code_fk_options_count_with_fk_ids(self):
        """source_uom_code fk_options_count should match FK-resolved pool."""
        fk_ids = {"source_uom_code": {"A": 1, "B": 2, "C": 3}, "target_uom_code": {"X": 10, "Y": 20}}
        rules = get_field_validation_rules(fk_ids)
        assert rules["source_uom_code"]["fk_options_count"] == 3

    def test_target_uom_code_fk_options_count_with_fk_ids(self):
        """target_uom_code fk_options_count should match FK-resolved pool."""
        fk_ids = {"source_uom_code": {"A": 1, "B": 2}, "target_uom_code": {"X": 10, "Y": 20, "Z": 30}}
        rules = get_field_validation_rules(fk_ids)
        assert rules["target_uom_code"]["fk_options_count"] == 3

    def test_uom_ids_has_at_least_10_entries(self):
        """UOM_IDS should have at least 10 entries for meaningful conversions."""
        assert len(UOM_IDS) >= 10

    def test_uom_ids_values_are_integers(self):
        """All UOM_IDS values should be integers."""
        for name, uid in UOM_IDS.items():
            assert isinstance(uid, int), f"UOM_IDS['{name}'] = {uid} is not int"

    def test_uom_ids_keys_are_strings(self):
        """All UOM_IDS keys should be strings."""
        for name in UOM_IDS:
            assert isinstance(name, str), f"UOM_IDS key {name!r} is not str"

    def test_uom_ids_no_duplicate_values(self):
        """UOM_IDS should not have duplicate ID values."""
        values = list(UOM_IDS.values())
        assert len(values) == len(set(values)), "Duplicate ID values found in UOM_IDS"
