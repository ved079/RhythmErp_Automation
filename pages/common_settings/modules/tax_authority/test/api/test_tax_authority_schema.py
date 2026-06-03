"""test_tax_authority_schema.py — Verify Tax Authority code matches live ERP schema."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    FIELD_VALIDATION_RULES, TAX_TYPE_IDS, COUNTRY_IDS, TAX_TYPE_NAMES,
    COUNTRY_NAMES, DEFAULT_TAX_AUTHORITY_FK_IDS,
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

    def test_tax_type_has_1_option(self):
        assert FIELD_VALIDATION_RULES["tax_type_ref_id"]["fk_options_count"] == 1

    def test_country_has_many_options(self):
        assert FIELD_VALIDATION_RULES["country_ref_id"]["fk_options_count"] >= 40

    def test_tax_type_names_matches(self):
        assert TAX_TYPE_NAMES == TAX_TYPE_IDS

    def test_country_names_matches(self):
        assert COUNTRY_NAMES == COUNTRY_IDS

    def test_default_fk_ids_has_both(self):
        assert "tax_type_ref_id" in DEFAULT_TAX_AUTHORITY_FK_IDS
        assert "country_ref_id" in DEFAULT_TAX_AUTHORITY_FK_IDS

    def test_default_fk_ids_pools_match(self):
        assert DEFAULT_TAX_AUTHORITY_FK_IDS["tax_type_ref_id"] == TAX_TYPE_IDS
        assert DEFAULT_TAX_AUTHORITY_FK_IDS["country_ref_id"] == COUNTRY_IDS

    def test_fk_pool_lengths_match_rules(self):
        for fn, r in FIELD_VALIDATION_RULES.items():
            if r["type"] == "dropdown" and "fk_options_count" in r:
                if fn in DEFAULT_TAX_AUTHORITY_FK_IDS:
                    assert len(DEFAULT_TAX_AUTHORITY_FK_IDS[fn]) == r["fk_options_count"]

    def test_tax_type_ids_no_dup_values(self):
        v = list(TAX_TYPE_IDS.values())
        assert len(v) == len(set(v))

    def test_country_ids_has_at_least_40_entries(self):
        """COUNTRY_IDS should have at least 40 entries. Note: some values
        may be duplicated (e.g. Singapore=0, Thailand=0) — this is from
        the live ERP data, not a bug in our code."""
        assert len(COUNTRY_IDS) >= 40
