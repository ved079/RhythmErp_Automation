"""
test_services_master_schema.py — Verify Services Master code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.services_master.data.services_master_data import (
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    UOM_ID_MAP,
    HSN_SAC_SERVICES_ID_MAP,
    UOM_NAMES,
    HSN_SAC_NAMES,
    DEFAULT_SERVICES_MASTER_FK_IDS,
)


@pytest.mark.schema
class TestServicesMasterSchema:
    """Verify the Services Master screen schema matches our code expectations."""

    # ── Field count and presence ──

    def test_has_6_fields(self):
        """Services Master should have exactly 6 fields in FIELD_VALIDATION_RULES."""
        assert len(FIELD_VALIDATION_RULES) == 6

    def test_has_all_fields(self):
        """FIELD_VALIDATION_RULES must include all 6 Services Master fields."""
        expected = {"name", "uom", "base_uom", "base_uom_conversion", "hsn_code", "status"}
        assert expected.issubset(set(FIELD_VALIDATION_RULES.keys()))

    # ── Required fields ──

    def test_name_required(self):
        """name should be marked as required."""
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    def test_uom_is_dropdown(self):
        """uom should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["uom"]["type"] == "dropdown"

    def test_base_uom_is_dropdown(self):
        """base_uom should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["base_uom"]["type"] == "dropdown"

    def test_hsn_code_is_dropdown(self):
        """hsn_code should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["hsn_code"]["type"] == "dropdown"

    def test_base_uom_conversion_required(self):
        """base_uom_conversion should be marked as required."""
        assert FIELD_VALIDATION_RULES["base_uom_conversion"]["required"] is True

    def test_status_not_required(self):
        """status should be marked as NOT required (has default)."""
        assert FIELD_VALIDATION_RULES["status"]["required"] is False

    # ── Max length checks ──

    def test_name_max_length_255(self):
        """name max_length should be 255."""
        assert FIELD_VALIDATION_RULES["name"]["max_length"] == 255

    def test_conversion_max_length_10(self):
        """base_uom_conversion max_length should be 10."""
        assert FIELD_VALIDATION_RULES["base_uom_conversion"]["max_length"] == 10

    # ── FK options counts ──

    def test_uom_has_9_options(self):
        """uom should have 9 options (UOM_ID_MAP size)."""
        assert FIELD_VALIDATION_RULES["uom"]["fk_options_count"] == 9

    def test_base_uom_has_9_options(self):
        """base_uom should have 9 options (same pool as uom)."""
        assert FIELD_VALIDATION_RULES["base_uom"]["fk_options_count"] == 9

    def test_hsn_code_has_6_options(self):
        """hsn_code should have 6 options (HSN_SAC_SERVICES_ID_MAP size)."""
        assert FIELD_VALIDATION_RULES["hsn_code"]["fk_options_count"] == 6

    # ── Toggle fields ──

    def test_status_is_toggle(self):
        """status should be type='toggle'."""
        assert FIELD_VALIDATION_RULES["status"]["type"] == "toggle"

    def test_status_default_true(self):
        """status default should be True (Active)."""
        assert FIELD_VALIDATION_RULES["status"]["default"] is True

    # ── Default FK IDs structure ──

    def test_default_fk_ids_has_3_pools(self):
        """DEFAULT_SERVICES_MASTER_FK_IDS must have 3 FK pools."""
        assert "uom" in DEFAULT_SERVICES_MASTER_FK_IDS
        assert "base_uom" in DEFAULT_SERVICES_MASTER_FK_IDS
        assert "hsn_code" in DEFAULT_SERVICES_MASTER_FK_IDS

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match the fk_options_count in FIELD_VALIDATION_RULES."""
        for field_name, rules in FIELD_VALIDATION_RULES.items():
            if rules["type"] == "dropdown" and "fk_options_count" in rules:
                if field_name in DEFAULT_SERVICES_MASTER_FK_IDS:
                    actual = len(DEFAULT_SERVICES_MASTER_FK_IDS[field_name])
                    expected = rules["fk_options_count"]
                    assert actual == expected, \
                        f"{field_name}: pool has {actual} options, rules say {expected}"

    # ── Name mappings ──

    def test_uom_names_matches(self):
        """UOM_NAMES should match UOM_ID_MAP."""
        assert UOM_NAMES == UOM_ID_MAP

    def test_hsn_sac_names_matches(self):
        """HSN_SAC_NAMES should match HSN_SAC_SERVICES_ID_MAP."""
        assert HSN_SAC_NAMES == HSN_SAC_SERVICES_ID_MAP

    # ── No duplicate ID values ──

    def test_uom_ids_no_dup_values(self):
        """UOM_ID_MAP should not have duplicate ID values."""
        values = list(UOM_ID_MAP.values())
        assert len(values) == len(set(values))

    def test_hsn_sac_ids_no_dup_values(self):
        """HSN_SAC_SERVICES_ID_MAP should not have duplicate ID values."""
        values = list(HSN_SAC_SERVICES_ID_MAP.values())
        assert len(values) == len(set(values))
