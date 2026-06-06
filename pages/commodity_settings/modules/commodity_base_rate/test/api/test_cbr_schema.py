"""
test_cbr_schema.py — Verify Commodity Base Rate code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.commodity_base_rate.data.cbr_data import (
    FIELD_VALIDATION_RULES,
    PRICING_TYPE_ID_MAP,
    LOCATION_ID_MAP,
    PRICING_TYPE_NAMES,
    LOCATION_NAMES,
    DEFAULT_COMMODITY_BASE_RATE_FK_IDS,
)


@pytest.mark.schema
class TestCBRSchema:
    """Verify the Commodity Base Rate screen schema matches our code expectations."""

    # ── Field count and presence ──

    def test_has_4_fields(self):
        """CBR should have exactly 4 fields in FIELD_VALIDATION_RULES."""
        assert len(FIELD_VALIDATION_RULES) == 4

    def test_has_all_fields(self):
        """FIELD_VALIDATION_RULES must include all CBR payload fields."""
        expected = {"pricing_type_ref_id", "from_date", "to_date", "location_ref_id"}
        assert expected.issubset(set(FIELD_VALIDATION_RULES.keys()))

    # ── Required fields ──

    def test_all_fields_required(self):
        """All CBR fields should be required."""
        for field_name in FIELD_VALIDATION_RULES:
            assert FIELD_VALIDATION_RULES[field_name]["required"] is True, \
                f"{field_name} should be required"

    # ── Field types ──

    def test_pricing_type_is_dropdown(self):
        """pricing_type_ref_id should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["pricing_type_ref_id"]["type"] == "dropdown"

    def test_location_ref_id_is_dropdown(self):
        """location_ref_id should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["location_ref_id"]["type"] == "dropdown"

    def test_from_date_is_date(self):
        """from_date should be type='date'."""
        assert FIELD_VALIDATION_RULES["from_date"]["type"] == "date"

    def test_to_date_is_date(self):
        """to_date should be type='date'."""
        assert FIELD_VALIDATION_RULES["to_date"]["type"] == "date"

    # ── FK options counts ──

    def test_pricing_type_has_2_options(self):
        """Pricing Type should have 2 options (Common, Supplier)."""
        assert FIELD_VALIDATION_RULES["pricing_type_ref_id"]["fk_options_count"] == 2

    def test_location_has_10_options(self):
        """Location should have 10 options."""
        assert FIELD_VALIDATION_RULES["location_ref_id"]["fk_options_count"] == 10

    # ── No status field in schema ──

    def test_no_status_field(self):
        """CBR schema should NOT have a status field."""
        assert "status" not in FIELD_VALIDATION_RULES

    # ── Default FK IDs structure ──

    def test_default_fk_ids_has_pricing_type(self):
        """DEFAULT_COMMODITY_BASE_RATE_FK_IDS must have pricing_type_ref_id pool."""
        assert "pricing_type_ref_id" in DEFAULT_COMMODITY_BASE_RATE_FK_IDS

    def test_default_fk_ids_has_location(self):
        """DEFAULT_COMMODITY_BASE_RATE_FK_IDS must have location_ref_id pool."""
        assert "location_ref_id" in DEFAULT_COMMODITY_BASE_RATE_FK_IDS

    def test_default_fk_ids_pools_match_source(self):
        """DEFAULT_COMMODITY_BASE_RATE_FK_IDS pools should match source ID maps."""
        assert DEFAULT_COMMODITY_BASE_RATE_FK_IDS["pricing_type_ref_id"] == PRICING_TYPE_ID_MAP
        assert DEFAULT_COMMODITY_BASE_RATE_FK_IDS["location_ref_id"] == LOCATION_ID_MAP

    # ── FK pool lengths match rules ──

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match the fk_options_count in FIELD_VALIDATION_RULES."""
        for field_name, rules in FIELD_VALIDATION_RULES.items():
            if rules["type"] == "dropdown" and "fk_options_count" in rules:
                if field_name in DEFAULT_COMMODITY_BASE_RATE_FK_IDS:
                    actual = len(DEFAULT_COMMODITY_BASE_RATE_FK_IDS[field_name])
                    expected = rules["fk_options_count"]
                    assert actual == expected, \
                        f"{field_name}: pool has {actual} options, rules say {expected}"

    # ── Name mappings ──

    def test_pricing_type_names_matches(self):
        """PRICING_TYPE_NAMES should match PRICING_TYPE_ID_MAP."""
        assert PRICING_TYPE_NAMES == PRICING_TYPE_ID_MAP

    def test_location_names_matches(self):
        """LOCATION_NAMES should match LOCATION_ID_MAP."""
        assert LOCATION_NAMES == LOCATION_ID_MAP

    # ── No duplicate ID values ──

    def test_pricing_type_ids_no_dup_values(self):
        """PRICING_TYPE_ID_MAP should not have duplicate ID values."""
        values = list(PRICING_TYPE_ID_MAP.values())
        assert len(values) == len(set(values))

    def test_location_ids_no_dup_values(self):
        """LOCATION_ID_MAP should not have duplicate ID values."""
        values = list(LOCATION_ID_MAP.values())
        assert len(values) == len(set(values))
