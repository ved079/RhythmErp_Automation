"""
test_item_attribute_schema.py — Verify Item Attribute code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.item_attribute.data.item_attribute_data import (
    FIELD_VALIDATION_RULES,
    get_field_validation_rules,
    get_fk_screen_mapping,
    STATUS_OPTIONS,
    MOCK_FK_IDS,
)


@pytest.mark.schema
class TestItemAttributeSchema:
    """Verify the Item Attribute screen schema matches our code expectations."""

    def test_has_4_fields(self):
        assert len(FIELD_VALIDATION_RULES) == 4

    def test_has_all_fields(self):
        assert "name" in FIELD_VALIDATION_RULES
        assert "description" in FIELD_VALIDATION_RULES
        assert "base_uom" in FIELD_VALIDATION_RULES
        assert "status" in FIELD_VALIDATION_RULES

    def test_name_required(self):
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    def test_description_optional(self):
        assert FIELD_VALIDATION_RULES["description"]["required"] is False

    def test_base_uom_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["base_uom"]["type"] == "dropdown"

    def test_base_uom_required(self):
        assert FIELD_VALIDATION_RULES["base_uom"]["required"] is True

    def test_base_uom_fk_options_count_placeholder(self):
        assert FIELD_VALIDATION_RULES["base_uom"]["fk_options_count"] == 0

    def test_status_is_toggle(self):
        assert FIELD_VALIDATION_RULES["status"]["type"] == "toggle"

    def test_status_default_true(self):
        assert FIELD_VALIDATION_RULES["status"]["default"] is True

    def test_status_options_has_2(self):
        assert len(STATUS_OPTIONS) == 2

    def test_get_field_validation_rules_is_callable(self):
        rules = get_field_validation_rules()
        assert rules == FIELD_VALIDATION_RULES

    def test_get_fk_screen_mapping_has_1_entry(self):
        mapping = get_fk_screen_mapping()
        assert len(mapping) == 1
        assert "base_uom" in mapping
        assert mapping["base_uom"] == "UOM"

    def test_mock_fk_ids_has_base_uom(self):
        assert "base_uom" in MOCK_FK_IDS

    def test_mock_fk_ids_no_duplicate_values(self):
        values = list(MOCK_FK_IDS["base_uom"].values())
        assert len(values) == len(set(values))
