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
    get_field_validation_rules,
    STATUS_OPTIONS,
)


@pytest.mark.schema
class TestSeasonSchema:
    """Verify the Season screen schema matches our code expectations."""

    def _rules(self):
        return get_field_validation_rules()

    def test_field_validation_rules_has_name(self):
        assert "name" in self._rules()

    def test_field_validation_rules_has_description(self):
        assert "description" in self._rules()

    def test_field_validation_rules_has_status(self):
        assert "status" in self._rules()

    def test_field_validation_rules_has_3_fields(self):
        rules = self._rules()
        assert len(rules) == 3
        assert set(rules.keys()) == {"name", "description", "status"}

    def test_name_is_required(self):
        assert self._rules()["name"]["required"] is True

    def test_description_is_optional(self):
        assert self._rules()["description"]["required"] is False

    def test_name_max_length_is_255(self):
        assert self._rules()["name"]["max_length"] == 255

    def test_description_max_length_is_255(self):
        assert self._rules()["description"]["max_length"] == 255

    def test_name_type_is_character(self):
        assert self._rules()["name"]["type"] == "character"

    def test_description_type_is_character(self):
        assert self._rules()["description"]["type"] == "character"

    def test_status_type_is_toggle(self):
        assert self._rules()["status"]["type"] == "toggle"

    def test_status_default_is_true(self):
        assert self._rules()["status"]["default"] is True

    def test_status_options_has_2_entries(self):
        assert len(STATUS_OPTIONS) == 2

    def test_status_options_active_is_true(self):
        assert STATUS_OPTIONS["Active"] is True

    def test_status_options_inactive_is_false(self):
        assert STATUS_OPTIONS["Inactive"] is False

    def test_status_is_not_required(self):
        assert self._rules()["status"]["required"] is False

    def test_fk_screen_mapping_is_empty(self):
        from pages.common_settings.modules.season.data.season_data import get_fk_screen_mapping
        assert get_fk_screen_mapping() == {}

    def test_generate_batch_payloads_accepts_standard_params(self):
        from pages.common_settings.modules.season.data.season_data import generate_batch_payloads
        result = generate_batch_payloads(count=3, prefix=None, dropdown_ids=None, offset=0, existing_entries=None)
        assert len(result) == 3

    def test_season_name_max_length_is_255(self):
        from pages.common_settings.modules.season.data.season_data import SEASON_NAME_MAX_LENGTH
        assert SEASON_NAME_MAX_LENGTH == 255
