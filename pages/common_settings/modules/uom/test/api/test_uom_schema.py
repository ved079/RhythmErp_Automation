"""
test_uom_schema.py — Verify UOM code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.uom.data.uom_data import (
    get_field_validation_rules,
    STATUS_OPTIONS,
)


@pytest.mark.schema
class TestUOMSchema:
    """Verify the UOM screen schema matches our code expectations."""

    def _rules(self):
        return get_field_validation_rules()

    def test_field_validation_rules_has_uom_code(self):
        """FIELD_VALIDATION_RULES must include uom_code."""
        assert "uom_code" in self._rules()

    def test_field_validation_rules_has_uom_description(self):
        """FIELD_VALIDATION_RULES must include uom_description."""
        assert "uom_description" in self._rules()

    def test_field_validation_rules_has_status(self):
        """FIELD_VALIDATION_RULES must include status."""
        assert "status" in self._rules()

    def test_field_validation_rules_has_3_fields(self):
        """UOM has exactly 3 fields: uom_code, uom_description, status."""
        rules = self._rules()
        assert len(rules) == 3
        assert set(rules.keys()) == {
            "uom_code", "uom_description", "status"
        }

    def test_uom_code_is_required(self):
        """uom_code must be marked as required."""
        assert self._rules()["uom_code"]["required"] is True

    def test_uom_description_is_optional(self):
        """uom_description must be marked as NOT required."""
        assert self._rules()["uom_description"]["required"] is False

    def test_uom_code_max_length_is_255(self):
        """uom_code must have max_length of 255."""
        assert self._rules()["uom_code"]["max_length"] == 255

    def test_uom_description_max_length_is_255(self):
        """uom_description must have max_length of 255."""
        assert self._rules()["uom_description"]["max_length"] == 255

    def test_uom_code_type_is_text(self):
        """uom_code type should be 'text' (accepts letters + numbers)."""
        assert self._rules()["uom_code"]["type"] == "text"

    def test_uom_description_type_is_text(self):
        """uom_description type should be 'text'."""
        assert self._rules()["uom_description"]["type"] == "text"

    def test_status_type_is_toggle(self):
        """status type should be 'toggle'."""
        assert self._rules()["status"]["type"] == "toggle"

    def test_status_default_is_true(self):
        """status default should be True (Active)."""
        assert self._rules()["status"]["default"] is True

    def test_status_options_has_2_entries(self):
        """STATUS_OPTIONS should have 2 entries: Active and Inactive."""
        assert len(STATUS_OPTIONS) == 2

    def test_status_options_active_is_true(self):
        """Active status should map to True."""
        assert STATUS_OPTIONS["Active"] is True

    def test_status_options_inactive_is_false(self):
        """Inactive status should map to False."""
        assert STATUS_OPTIONS["Inactive"] is False

    def test_status_is_not_required(self):
        """status should not be marked as required (has a default)."""
        assert self._rules()["status"]["required"] is False
