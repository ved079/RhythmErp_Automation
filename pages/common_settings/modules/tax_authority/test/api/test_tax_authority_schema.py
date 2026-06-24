"""test_tax_authority_schema.py — Verify Tax Authority code matches live ERP schema."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    FIELD_VALIDATION_RULES, get_field_validation_rules, get_fk_screen_mapping,
)

@pytest.mark.schema
class TestTaxAuthoritySchema:
    def test_has_3_fields(self):
        assert len(FIELD_VALIDATION_RULES) == 3

    def test_has_all_fields(self):
        assert set(FIELD_VALIDATION_RULES.keys()) == {"tax_name", "tax_type_ref_id", "country_ref_id"}

    def test_tax_name_required(self):
        assert FIELD_VALIDATION_RULES["tax_name"]["required"] is True

    def test_tax_type_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["tax_type_ref_id"]["type"] == "dropdown"

    def test_country_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["country_ref_id"]["type"] == "dropdown"

    def test_fk_options_count_placeholder(self):
        for fn in ("tax_type_ref_id", "country_ref_id"):
            assert FIELD_VALIDATION_RULES[fn]["fk_options_count"] == 0

    def test_get_field_validation_rules_is_callable(self):
        rules = get_field_validation_rules()
        assert rules["tax_name"]["required"] is True

    def test_get_fk_screen_mapping_has_2_entries(self):
        mapping = get_fk_screen_mapping()
        assert len(mapping) == 2
        fields = set(mapping)
        assert fields == {"tax_type_ref_id", "country_ref_id"}
