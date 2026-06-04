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
    STATUS_OPTIONS,
    DEFAULT_ITEM_ATTRIBUTE_FK_IDS,
    UOM_IDS,
    UOM_NAMES,
)


@pytest.mark.schema
class TestItemAttributeSchema:
    """Verify the Item Attribute screen schema matches our code expectations."""

    def test_has_4_fields(self):
        """Item Attribute schema should have exactly 4 fields (name, description, base_uom, status)."""
        assert len(FIELD_VALIDATION_RULES) == 4

    def test_has_all_fields(self):
        """FIELD_VALIDATION_RULES must include all expected fields."""
        assert "name" in FIELD_VALIDATION_RULES
        assert "description" in FIELD_VALIDATION_RULES
        assert "base_uom" in FIELD_VALIDATION_RULES
        assert "status" in FIELD_VALIDATION_RULES

    def test_name_required(self):
        """name field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    def test_description_optional(self):
        """description field should be marked as required=False."""
        assert FIELD_VALIDATION_RULES["description"]["required"] is False

    def test_base_uom_is_dropdown(self):
        """base_uom field should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["base_uom"]["type"] == "dropdown"

    def test_base_uom_required(self):
        """base_uom field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["base_uom"]["required"] is True

    def test_base_uom_has_uom_count_options(self):
        """base_uom should have fk_options_count matching the UOM_IDS pool size."""
        assert FIELD_VALIDATION_RULES["base_uom"]["fk_options_count"] == len(UOM_IDS)

    def test_status_is_toggle(self):
        """status field should be type='toggle'."""
        assert FIELD_VALIDATION_RULES["status"]["type"] == "toggle"

    def test_status_default_true(self):
        """status field should default to True."""
        assert FIELD_VALIDATION_RULES["status"]["default"] is True

    def test_status_options_has_2(self):
        """STATUS_OPTIONS should have exactly 2 entries (Active, Inactive)."""
        assert len(STATUS_OPTIONS) == 2

    def test_default_fk_ids_has_base_uom(self):
        """DEFAULT_ITEM_ATTRIBUTE_FK_IDS should contain base_uom key."""
        assert "base_uom" in DEFAULT_ITEM_ATTRIBUTE_FK_IDS

    def test_default_fk_ids_pools_match(self):
        """DEFAULT_ITEM_ATTRIBUTE_FK_IDS['base_uom'] should match UOM_IDS."""
        assert DEFAULT_ITEM_ATTRIBUTE_FK_IDS["base_uom"] == UOM_IDS

    def test_uom_ids_no_duplicate_values(self):
        """UOM_IDS should have no duplicate values (all FK IDs unique)."""
        values = list(UOM_IDS.values())
        assert len(values) == len(set(values)), "Duplicate FK IDs found in UOM_IDS"
