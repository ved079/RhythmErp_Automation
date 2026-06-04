"""
test_hsn_sac_schema.py — Verify HSN SAC code matches live ERP schema.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    FIELD_VALIDATION_RULES,
    HSN_SAC_TYPE_IDS,
    HSN_SAC_TYPE_NAMES,
    DEFAULT_HSN_SAC_FK_IDS,
)


@pytest.mark.schema
class TestHsnSacSchema:
    def test_field_validation_rules_has_3_fields(self):
        assert len(FIELD_VALIDATION_RULES) == 3

    def test_field_validation_rules_has_all_fields(self):
        assert set(FIELD_VALIDATION_RULES.keys()) == {"hsn_sac_no", "hsn_sac_type", "hsn_sac_description"}

    def test_hsn_sac_no_is_required(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_no"]["required"] is True

    def test_hsn_sac_no_max_length_255(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_no"]["max_length"] == 255

    def test_hsn_sac_type_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_type"]["type"] == "dropdown"

    def test_hsn_sac_type_is_required(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_type"]["required"] is True

    def test_hsn_sac_type_has_4_options(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_type"]["fk_options_count"] == 4

    def test_hsn_sac_description_is_required(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_description"]["required"] is True

    def test_hsn_sac_type_ids_has_4_entries(self):
        assert len(HSN_SAC_TYPE_IDS) == 4

    def test_hsn_sac_type_names_matches_ids(self):
        assert HSN_SAC_TYPE_NAMES == HSN_SAC_TYPE_IDS

    def test_default_fk_ids_has_hsn_sac_type(self):
        assert "hsn_sac_type" in DEFAULT_HSN_SAC_FK_IDS

    def test_default_fk_ids_pools_match_source(self):
        assert DEFAULT_HSN_SAC_FK_IDS["hsn_sac_type"] == HSN_SAC_TYPE_IDS

    def test_fk_pool_lengths_match_rules(self):
        for field_name, rules in FIELD_VALIDATION_RULES.items():
            if rules["type"] == "dropdown" and "fk_options_count" in rules:
                if field_name in DEFAULT_HSN_SAC_FK_IDS:
                    actual = len(DEFAULT_HSN_SAC_FK_IDS[field_name])
                    expected = rules["fk_options_count"]
                    assert actual == expected

    def test_hsn_sac_type_ids_no_duplicate_values(self):
        values = list(HSN_SAC_TYPE_IDS.values())
        assert len(values) == len(set(values))

    def test_hsn_sac_type_ids_values_are_integers(self):
        for name, uid in HSN_SAC_TYPE_IDS.items():
            assert isinstance(uid, int)
