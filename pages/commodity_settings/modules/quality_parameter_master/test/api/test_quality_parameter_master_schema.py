"""
test_quality_parameter_master_schema.py — Verify Quality Parameter Master code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.quality_parameter_master.data.quality_parameter_master_data import (
    FIELD_VALIDATION_RULES,
    DEFAULT_QUALITY_PARAMETER_MASTER_FK_IDS,
)


@pytest.mark.schema
class TestQualityParameterMasterSchema:
    """Verify the Quality Parameter Master screen schema matches our code expectations."""

    # ── Field count and presence ──

    def test_field_validation_rules_has_1_field(self):
        """QPM should have exactly 1 field in FIELD_VALIDATION_RULES."""
        assert len(FIELD_VALIDATION_RULES) == 1

    def test_field_validation_rules_has_name_field(self):
        """FIELD_VALIDATION_RULES must include the 'name' field."""
        assert "name" in FIELD_VALIDATION_RULES

    # ── Required fields ──

    def test_name_is_required(self):
        """name field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    # ── Max length checks ──

    def test_name_max_length_is_255(self):
        """name field should have max_length of 255."""
        assert FIELD_VALIDATION_RULES["name"]["max_length"] == 255

    # ── Field types ──

    def test_name_is_character_type(self):
        """name field should be type='character'."""
        assert FIELD_VALIDATION_RULES["name"]["type"] == "character"

    # ── Default FK IDs ──

    def test_default_fk_ids_is_empty(self):
        """DEFAULT_QUALITY_PARAMETER_MASTER_FK_IDS should be empty (no FK dropdowns)."""
        assert DEFAULT_QUALITY_PARAMETER_MASTER_FK_IDS == {}

    # ── No status field ──

    def test_no_status_field(self):
        """QPM has no status field — it should NOT appear in FIELD_VALIDATION_RULES."""
        assert "status" not in FIELD_VALIDATION_RULES

    # ── No toggle fields ──

    def test_no_toggle_fields(self):
        """QPM has no toggle fields — all fields should be character type."""
        for field_name, rules in FIELD_VALIDATION_RULES.items():
            assert rules["type"] != "toggle", \
                f"{field_name} should NOT be toggle type in QPM"
