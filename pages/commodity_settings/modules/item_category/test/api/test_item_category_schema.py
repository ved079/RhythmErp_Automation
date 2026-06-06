"""
test_item_category_schema.py — Verify Item Category code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.item_category.data.item_category_data import (
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    DEFAULT_ITEM_CATEGORY_FK_IDS,
)


@pytest.mark.schema
class TestItemCategorySchema:
    """Verify the Item Category screen schema matches our code expectations."""

    # ── Field count and presence ──

    def test_field_validation_rules_has_4_fields(self):
        """Item Category should have exactly 4 fields in FIELD_VALIDATION_RULES."""
        assert len(FIELD_VALIDATION_RULES) == 4

    def test_field_validation_rules_has_all_fields(self):
        """FIELD_VALIDATION_RULES must include item_code, item_description, level, status."""
        expected_fields = {"item_code", "item_description", "level", "status"}
        assert set(FIELD_VALIDATION_RULES.keys()) == expected_fields

    # ── Required fields ──

    def test_item_code_is_required(self):
        """item_code field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["item_code"]["required"] is True

    def test_item_description_is_required(self):
        """item_description field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["item_description"]["required"] is True

    def test_level_is_required(self):
        """level field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["level"]["required"] is True

    def test_status_is_not_required(self):
        """status field should be marked as required=False (optional toggle)."""
        assert FIELD_VALIDATION_RULES["status"]["required"] is False

    # ── Field types ──

    def test_level_is_number_type(self):
        """level field should be type='number'."""
        assert FIELD_VALIDATION_RULES["level"]["type"] == "number"

    def test_status_is_toggle_type(self):
        """status field should be type='toggle'."""
        assert FIELD_VALIDATION_RULES["status"]["type"] == "toggle"

    def test_item_code_is_character_type(self):
        """item_code field should be type='character'."""
        assert FIELD_VALIDATION_RULES["item_code"]["type"] == "character"

    def test_item_description_is_character_type(self):
        """item_description field should be type='character'."""
        assert FIELD_VALIDATION_RULES["item_description"]["type"] == "character"

    # ── Status defaults and options ──

    def test_status_default_is_true(self):
        """status default should be True (Active)."""
        assert FIELD_VALIDATION_RULES["status"]["default"] is True

    def test_status_options_has_2_entries(self):
        """STATUS_OPTIONS should have 2 entries: Active and Inactive."""
        assert len(STATUS_OPTIONS) == 2

    def test_status_options_active_is_true(self):
        """Active status should map to True."""
        assert STATUS_OPTIONS["Active"] is True

    def test_status_options_inactive_is_false(self):
        """Inactive status should map to False."""
        assert STATUS_OPTIONS["Inactive"] is False

    # ── Max length checks ──

    def test_item_code_max_length_is_255(self):
        """item_code field should have max_length of 255."""
        assert FIELD_VALIDATION_RULES["item_code"]["max_length"] == 255

    def test_item_description_max_length_is_255(self):
        """item_description field should have max_length of 255."""
        assert FIELD_VALIDATION_RULES["item_description"]["max_length"] == 255

    # ── Default FK IDs ──

    def test_default_fk_ids_is_empty(self):
        """DEFAULT_ITEM_CATEGORY_FK_IDS should be empty (no FK dropdowns)."""
        assert DEFAULT_ITEM_CATEGORY_FK_IDS == {}
