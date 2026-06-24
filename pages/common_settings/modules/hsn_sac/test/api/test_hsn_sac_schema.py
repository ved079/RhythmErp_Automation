"""
test_hsn_sac_schema.py — Verify HSN SAC code matches live ERP schema.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    get_field_validation_rules,
    HSN_SAC_TYPE_IDS,
)


@pytest.mark.schema
class TestHsnSacSchema:
    def _rules(self):
        return get_field_validation_rules()

    def test_field_validation_rules_has_3_fields(self):
        assert len(self._rules()) == 3

    def test_field_validation_rules_has_all_fields(self):
        assert set(self._rules().keys()) == {"hsn_sac_no", "hsn_sac_type", "hsn_sac_description"}

    def test_hsn_sac_no_is_required(self):
        assert self._rules()["hsn_sac_no"]["required"] is True

    def test_hsn_sac_no_max_length_255(self):
        assert self._rules()["hsn_sac_no"]["max_length"] == 255

    def test_hsn_sac_type_is_dropdown(self):
        assert self._rules()["hsn_sac_type"]["type"] == "dropdown"

    def test_hsn_sac_type_is_required(self):
        assert self._rules()["hsn_sac_type"]["required"] is True

    def test_hsn_sac_type_has_4_options_with_fk_ids(self):
        fk_ids = {"hsn_sac_type": {"A": 1, "B": 2, "C": 3, "D": 4}}
        rules = get_field_validation_rules(fk_ids)
        assert rules["hsn_sac_type"]["fk_options_count"] == 4

    def test_hsn_sac_description_is_required(self):
        assert self._rules()["hsn_sac_description"]["required"] is True

    def test_hsn_sac_type_ids_has_4_entries(self):
        assert len(HSN_SAC_TYPE_IDS) == 4

    def test_hsn_sac_type_ids_no_duplicate_values(self):
        values = list(HSN_SAC_TYPE_IDS.values())
        assert len(values) == len(set(values))

    def test_hsn_sac_type_ids_values_are_integers(self):
        for name, uid in HSN_SAC_TYPE_IDS.items():
            assert isinstance(uid, int)
