"""
test_item_group_schema.py — Verify Item Group code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.item_group.data.item_group_data import (
    FIELD_VALIDATION_RULES,
    DEFAULT_ITEM_GROUP_FK_IDS,
)


@pytest.mark.schema
class TestItemGroupSchema:
    """Verify the Item Group screen schema matches our code expectations."""

    # ── Field count and presence ──

    def test_field_validation_rules_has_2_fields(self):
        """Item Group should have exactly 2 fields in FIELD_VALIDATION_RULES."""
        assert len(FIELD_VALIDATION_RULES) == 2

    def test_field_validation_rules_has_both_fields(self):
        """FIELD_VALIDATION_RULES must include both 'code' and 'description'."""
        assert "code" in FIELD_VALIDATION_RULES
        assert "description" in FIELD_VALIDATION_RULES

    # ── Required fields ──

    def test_code_is_required(self):
        """code field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["code"]["required"] is True

    def test_description_is_required(self):
        """description field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["description"]["required"] is True

    # ── Max length checks ──

    def test_code_max_length_is_255(self):
        """code field should have max_length of 255."""
        assert FIELD_VALIDATION_RULES["code"]["max_length"] == 255

    def test_description_max_length_is_255(self):
        """description field should have max_length of 255."""
        assert FIELD_VALIDATION_RULES["description"]["max_length"] == 255

    # ── Field types ──

    def test_code_is_character_type(self):
        """code field should be type='character'."""
        assert FIELD_VALIDATION_RULES["code"]["type"] == "character"

    def test_description_is_character_type(self):
        """description field should be type='character'."""
        assert FIELD_VALIDATION_RULES["description"]["type"] == "character"

    # ── Default FK IDs ──

    def test_default_fk_ids_is_empty(self):
        """DEFAULT_ITEM_GROUP_FK_IDS should be empty (no FK dropdowns)."""
        assert DEFAULT_ITEM_GROUP_FK_IDS == {}

    # ── No status field ──

    def test_no_status_field(self):
        """Item Group has no status field — it should NOT appear in FIELD_VALIDATION_RULES."""
        assert "status" not in FIELD_VALIDATION_RULES
