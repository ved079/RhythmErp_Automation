"""
test_error_code_mst_schema.py — Verify Error Code Mst code matches live ERP schema.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    FIELD_VALIDATION_RULES,
    ERROR_CODE_TYPE_IDS,
    ERROR_CODE_TYPE_NAMES,
    DEFAULT_ERROR_CODE_MST_FK_IDS,
)


@pytest.mark.schema
class TestErrorCodeMstSchema:
    def test_field_validation_rules_has_4_fields(self):
        assert len(FIELD_VALIDATION_RULES) == 4

    def test_field_validation_rules_has_all_fields(self):
        assert set(FIELD_VALIDATION_RULES.keys()) == {
            "error_code_type", "code", "description", "is_qty_amount"
        }

    def test_error_code_type_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["error_code_type"]["type"] == "dropdown"

    def test_error_code_type_is_required(self):
        assert FIELD_VALIDATION_RULES["error_code_type"]["required"] is True

    def test_error_code_type_has_4_options(self):
        assert FIELD_VALIDATION_RULES["error_code_type"]["fk_options_count"] == 4

    def test_code_is_required(self):
        assert FIELD_VALIDATION_RULES["code"]["required"] is True

    def test_code_max_length_255(self):
        assert FIELD_VALIDATION_RULES["code"]["max_length"] == 255

    def test_description_is_required(self):
        assert FIELD_VALIDATION_RULES["description"]["required"] is True

    def test_is_qty_amount_is_required(self):
        assert FIELD_VALIDATION_RULES["is_qty_amount"]["required"] is True

    def test_error_code_type_ids_has_4_entries(self):
        assert len(ERROR_CODE_TYPE_IDS) == 4

    def test_error_code_type_names_matches_ids(self):
        assert ERROR_CODE_TYPE_NAMES == ERROR_CODE_TYPE_IDS

    def test_default_fk_ids_has_error_code_type(self):
        assert "error_code_type" in DEFAULT_ERROR_CODE_MST_FK_IDS

    def test_default_fk_ids_pools_match_source(self):
        assert DEFAULT_ERROR_CODE_MST_FK_IDS["error_code_type"] == ERROR_CODE_TYPE_IDS

    def test_fk_pool_lengths_match_rules(self):
        for field_name, rules in FIELD_VALIDATION_RULES.items():
            if rules["type"] == "dropdown" and "fk_options_count" in rules:
                if field_name in DEFAULT_ERROR_CODE_MST_FK_IDS:
                    actual = len(DEFAULT_ERROR_CODE_MST_FK_IDS[field_name])
                    expected = rules["fk_options_count"]
                    assert actual == expected

    def test_error_code_type_ids_no_duplicate_values(self):
        values = list(ERROR_CODE_TYPE_IDS.values())
        assert len(values) == len(set(values))
