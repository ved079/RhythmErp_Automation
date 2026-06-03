"""
test_season_schema.py — Verify Season code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.season.data.season_data import (
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    DEFAULT_SEASON_FK_IDS,
)


@pytest.mark.schema
class TestSeasonSchema:
    """Verify the Season screen schema matches our code expectations."""

    def test_field_validation_rules_has_name(self):
        assert "name" in FIELD_VALIDATION_RULES

    def test_field_validation_rules_has_description(self):
        assert "description" in FIELD_VALIDATION_RULES

    def test_field_validation_rules_has_status(self):
        assert "status" in FIELD_VALIDATION_RULES

    def test_field_validation_rules_has_3_fields(self):
        assert len(FIELD_VALIDATION_RULES) == 3
        assert set(FIELD_VALIDATION_RULES.keys()) == {"name", "description", "status"}

    def test_name_is_required(self):
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    def test_description_is_optional(self):
        assert FIELD_VALIDATION_RULES["description"]["required"] is False

    def test_name_max_length_is_255(self):
        assert FIELD_VALIDATION_RULES["name"]["max_length"] == 255

    def test_description_max_length_is_255(self):
        assert FIELD_VALIDATION_RULES["description"]["max_length"] == 255

    def test_name_type_is_character(self):
        assert FIELD_VALIDATION_RULES["name"]["type"] == "character"

    def test_description_type_is_character(self):
        assert FIELD_VALIDATION_RULES["description"]["type"] == "character"

    def test_status_type_is_toggle(self):
        assert FIELD_VALIDATION_RULES["status"]["type"] == "toggle"

    def test_status_default_is_true(self):
        assert FIELD_VALIDATION_RULES["status"]["default"] is True

    def test_status_options_has_2_entries(self):
        assert len(STATUS_OPTIONS) == 2

    def test_status_options_active_is_true(self):
        assert STATUS_OPTIONS["Active"] is True

    def test_status_options_inactive_is_false(self):
        assert STATUS_OPTIONS["Inactive"] is False

    def test_default_fk_ids_is_empty(self):
        assert DEFAULT_SEASON_FK_IDS == {}

    def test_status_is_not_required(self):
        assert FIELD_VALIDATION_RULES["status"]["required"] is False
