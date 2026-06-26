"""
test_error_code_mst_schema.py — Verify Error Code Mst code matches live ERP schema.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    get_field_validation_rules,
    ERROR_CODE_TYPE_IDS,
)


@pytest.mark.schema
class TestErrorCodeMstSchema:
    def _rules(self):
        return get_field_validation_rules()

    def test_field_validation_rules_has_4_fields(self):
        assert len(self._rules()) == 4

    def test_field_validation_rules_has_all_fields(self):
        assert set(self._rules().keys()) == {
            "error_code_type", "code", "description", "is_qty_amount"
        }

    def test_error_code_type_is_dropdown(self):
        assert self._rules()["error_code_type"]["type"] == "dropdown"

    def test_error_code_type_is_required(self):
        assert self._rules()["error_code_type"]["required"] is True

    def test_error_code_type_has_4_options_with_fk_ids(self):
        fk_ids = {"error_code_type": {"A": 1, "B": 2, "C": 3, "D": 4}}
        rules = get_field_validation_rules(fk_ids)
        assert rules["error_code_type"]["fk_options_count"] == 4

    def test_code_is_required(self):
        assert self._rules()["code"]["required"] is True

    def test_code_max_length_255(self):
        assert self._rules()["code"]["max_length"] == 255

    def test_description_is_required(self):
        assert self._rules()["description"]["required"] is True

    def test_is_qty_amount_is_required(self):
        assert self._rules()["is_qty_amount"]["required"] is True

    def test_error_code_type_ids_has_4_entries(self):
        assert len(ERROR_CODE_TYPE_IDS) == 4

    def test_error_code_type_ids_no_duplicate_values(self):
        values = list(ERROR_CODE_TYPE_IDS.values())
        assert len(values) == len(set(values))

    def test_fk_screen_mapping_returns_1_key(self):
        from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import get_fk_screen_mapping
        m = get_fk_screen_mapping()
        assert set(m.keys()) == {"error_code_type"}

    def test_generate_batch_payloads_accepts_standard_params(self):
        from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import generate_batch_payloads
        result = generate_batch_payloads(count=3, prefix=None, dropdown_ids=None, offset=0, existing_entries=None)
        assert len(result) == 3

    def test_error_code_max_length_is_255(self):
        from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import ERROR_CODE_MAX_LENGTH
        assert ERROR_CODE_MAX_LENGTH == 255
