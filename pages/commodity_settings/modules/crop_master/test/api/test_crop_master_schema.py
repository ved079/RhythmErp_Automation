"""
test_crop_master_schema.py — Verify Crop Master code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.crop_master.data.crop_master_data import (
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    DEFAULT_CROP_MASTER_FK_IDS,
)


@pytest.mark.schema
class TestCropMasterSchema:
    """Verify the Crop Master screen schema matches our code expectations."""

    def test_has_3_fields(self):
        """Crop Master should have exactly 3 fields (name, description, status — attachment NOT in API)."""
        assert len(FIELD_VALIDATION_RULES) == 3
        assert set(FIELD_VALIDATION_RULES.keys()) == {"name", "description", "status"}

    def test_has_all_fields(self):
        """FIELD_VALIDATION_RULES must include all expected fields."""
        assert "name" in FIELD_VALIDATION_RULES
        assert "description" in FIELD_VALIDATION_RULES
        assert "status" in FIELD_VALIDATION_RULES

    def test_name_required(self):
        """name field should be marked as required=True."""
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    def test_description_optional(self):
        """description field should be marked as required=False."""
        assert FIELD_VALIDATION_RULES["description"]["required"] is False

    def test_name_max_length_255(self):
        """name field should have max_length of 255."""
        assert FIELD_VALIDATION_RULES["name"]["max_length"] == 255

    def test_description_max_length_255(self):
        """description field should have max_length of 255."""
        assert FIELD_VALIDATION_RULES["description"]["max_length"] == 255

    def test_name_is_character(self):
        """name field should be type='character'."""
        assert FIELD_VALIDATION_RULES["name"]["type"] == "character"

    def test_status_is_toggle(self):
        """status field should be type='toggle'."""
        assert FIELD_VALIDATION_RULES["status"]["type"] == "toggle"

    def test_status_default_true(self):
        """status field should default to True."""
        assert FIELD_VALIDATION_RULES["status"]["default"] is True

    def test_status_options_has_2(self):
        """STATUS_OPTIONS should have exactly 2 entries (Active, Inactive)."""
        assert len(STATUS_OPTIONS) == 2

    def test_default_fk_ids_empty(self):
        """DEFAULT_CROP_MASTER_FK_IDS should be empty (no FK dropdowns)."""
        assert DEFAULT_CROP_MASTER_FK_IDS == {}
