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
    FIELD_VALIDATION_RULES,
    DEFAULT_UOM_CONVERSION_FK_IDS,
    UOM_IDS,
    UOM_NAMES,
)


@pytest.mark.schema
class TestUOMConversionSchema:
    """Verify the UOM Conversion screen schema matches our code expectations."""

    def test_field_validation_rules_has_source_uom_code(self):
        """FIELD_VALIDATION_RULES must include source_uom_code."""
        assert "source_uom_code" in FIELD_VALIDATION_RULES

    def test_field_validation_rules_has_target_uom_code(self):
        """FIELD_VALIDATION_RULES must include target_uom_code."""
        assert "target_uom_code" in FIELD_VALIDATION_RULES

    def test_field_validation_rules_has_conversion_factor(self):
        """FIELD_VALIDATION_RULES must include conversion_factor."""
        assert "conversion_factor" in FIELD_VALIDATION_RULES

    def test_field_validation_rules_has_3_fields(self):
        """UOM Conversion has exactly 3 fields: source_uom_code, target_uom_code, conversion_factor."""
        assert len(FIELD_VALIDATION_RULES) == 3
        assert set(FIELD_VALIDATION_RULES.keys()) == {
            "source_uom_code", "target_uom_code", "conversion_factor"
        }

    def test_source_uom_code_is_required(self):
        """source_uom_code must be marked as required."""
        assert FIELD_VALIDATION_RULES["source_uom_code"]["required"] is True

    def test_target_uom_code_is_required(self):
        """target_uom_code must be marked as required."""
        assert FIELD_VALIDATION_RULES["target_uom_code"]["required"] is True

    def test_conversion_factor_is_required(self):
        """conversion_factor must be marked as required."""
        assert FIELD_VALIDATION_RULES["conversion_factor"]["required"] is True

    def test_source_uom_code_is_dropdown(self):
        """source_uom_code type should be 'dropdown'."""
        assert FIELD_VALIDATION_RULES["source_uom_code"]["type"] == "dropdown"

    def test_target_uom_code_is_dropdown(self):
        """target_uom_code type should be 'dropdown'."""
        assert FIELD_VALIDATION_RULES["target_uom_code"]["type"] == "dropdown"

    def test_conversion_factor_is_number(self):
        """conversion_factor type should be 'number'."""
        assert FIELD_VALIDATION_RULES["conversion_factor"]["type"] == "number"

    def test_source_uom_code_fk_options_count(self):
        """source_uom_code fk_options_count should match UOM_IDS length."""
        assert FIELD_VALIDATION_RULES["source_uom_code"]["fk_options_count"] == len(UOM_IDS)

    def test_target_uom_code_fk_options_count(self):
        """target_uom_code fk_options_count should match UOM_IDS length."""
        assert FIELD_VALIDATION_RULES["target_uom_code"]["fk_options_count"] == len(UOM_IDS)

    def test_default_fk_ids_has_source_and_target(self):
        """DEFAULT_UOM_CONVERSION_FK_IDS must have both source and target pools."""
        assert "source_uom_code" in DEFAULT_UOM_CONVERSION_FK_IDS
        assert "target_uom_code" in DEFAULT_UOM_CONVERSION_FK_IDS

    def test_default_fk_ids_pools_match_uom_ids(self):
        """Both FK pools in DEFAULT_UOM_CONVERSION_FK_IDS should match UOM_IDS."""
        assert DEFAULT_UOM_CONVERSION_FK_IDS["source_uom_code"] == UOM_IDS
        assert DEFAULT_UOM_CONVERSION_FK_IDS["target_uom_code"] == UOM_IDS

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

    def test_uom_names_matches_uom_ids(self):
        """UOM_NAMES should be a copy of UOM_IDS."""
        assert UOM_NAMES == UOM_IDS

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match the fk_options_count in FIELD_VALIDATION_RULES."""
        for field_name, rules in FIELD_VALIDATION_RULES.items():
            if rules["type"] == "dropdown" and "fk_options_count" in rules:
                if field_name in DEFAULT_UOM_CONVERSION_FK_IDS:
                    actual = len(DEFAULT_UOM_CONVERSION_FK_IDS[field_name])
                    expected = rules["fk_options_count"]
                    assert actual == expected, \
                        f"{field_name}: pool has {actual} options, rules say {expected}"

    def test_uom_ids_no_duplicate_values(self):
        """UOM_IDS should not have duplicate ID values."""
        values = list(UOM_IDS.values())
        assert len(values) == len(set(values)), "Duplicate ID values found in UOM_IDS"
