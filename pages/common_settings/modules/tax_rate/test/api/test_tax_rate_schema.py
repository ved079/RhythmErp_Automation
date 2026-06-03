"""test_tax_rate_schema.py — Verify Tax Rate code matches live ERP schema."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    FIELD_VALIDATION_RULES, TAX_TYPE_IDS, TAX_AUTHORITY_IDS,
    HSN_SAC_NUMBER_IDS, TAX_TYPE_NAMES, TAX_AUTHORITY_NAMES,
    HSN_SAC_NUMBER_NAMES, DEFAULT_TAX_RATE_FK_IDS, REVISION_STATUS_OPTIONS,
    STEPPER_NAME,
)

@pytest.mark.schema
class TestTaxRateSchema:
    def test_has_8_fields(self):
        assert len(FIELD_VALIDATION_RULES) == 8

    def test_has_root_fields(self):
        root = {"tax_rate_name", "tax_type_ref_id", "tax_authority_ref_id",
                "from_date", "to_date", "revision_status"}
        assert root.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_has_stepper_fields(self):
        stepper = {"hsn_sac_number", "tax_rate"}
        assert stepper.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_tax_rate_name_required(self):
        assert FIELD_VALIDATION_RULES["tax_rate_name"]["required"] is True

    def test_tax_type_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["tax_type_ref_id"]["type"] == "dropdown"

    def test_tax_authority_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["tax_authority_ref_id"]["type"] == "dropdown"

    def test_from_date_is_date(self):
        assert FIELD_VALIDATION_RULES["from_date"]["type"] == "date"

    def test_to_date_is_date(self):
        assert FIELD_VALIDATION_RULES["to_date"]["type"] == "date"

    def test_revision_status_is_character(self):
        assert FIELD_VALIDATION_RULES["revision_status"]["type"] == "character"

    def test_hsn_sac_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_number"]["type"] == "dropdown"

    def test_tax_rate_is_number(self):
        assert FIELD_VALIDATION_RULES["tax_rate"]["type"] == "number"

    def test_tax_type_has_1_option(self):
        assert FIELD_VALIDATION_RULES["tax_type_ref_id"]["fk_options_count"] == 1

    def test_tax_authority_has_20_options(self):
        assert FIELD_VALIDATION_RULES["tax_authority_ref_id"]["fk_options_count"] == 20

    def test_hsn_sac_has_24_options(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_number"]["fk_options_count"] == 24

    def test_tax_type_names_matches(self):
        assert TAX_TYPE_NAMES == TAX_TYPE_IDS

    def test_tax_authority_names_matches(self):
        assert TAX_AUTHORITY_NAMES == TAX_AUTHORITY_IDS

    def test_hsn_sac_names_matches(self):
        assert HSN_SAC_NUMBER_NAMES == HSN_SAC_NUMBER_IDS

    def test_default_fk_ids_has_all_3(self):
        assert "tax_type_ref_id" in DEFAULT_TAX_RATE_FK_IDS
        assert "tax_authority_ref_id" in DEFAULT_TAX_RATE_FK_IDS
        assert "hsn_sac_number" in DEFAULT_TAX_RATE_FK_IDS

    def test_default_fk_ids_pools_match(self):
        assert DEFAULT_TAX_RATE_FK_IDS["tax_type_ref_id"] == TAX_TYPE_IDS
        assert DEFAULT_TAX_RATE_FK_IDS["tax_authority_ref_id"] == TAX_AUTHORITY_IDS
        assert DEFAULT_TAX_RATE_FK_IDS["hsn_sac_number"] == HSN_SAC_NUMBER_IDS

    def test_fk_pool_lengths_match_rules(self):
        for fn, r in FIELD_VALIDATION_RULES.items():
            if r["type"] == "dropdown" and "fk_options_count" in r:
                if fn in DEFAULT_TAX_RATE_FK_IDS:
                    assert len(DEFAULT_TAX_RATE_FK_IDS[fn]) == r["fk_options_count"]

    def test_revision_status_options_has_active(self):
        assert "Active" in REVISION_STATUS_OPTIONS

    def test_stepper_name_is_correct(self):
        assert STEPPER_NAME == "Define Tax Rate Details"

    def test_tax_authority_ids_no_dup_values(self):
        v = list(TAX_AUTHORITY_IDS.values())
        assert len(v) == len(set(v))

    def test_hsn_sac_ids_no_dup_values(self):
        v = list(HSN_SAC_NUMBER_IDS.values())
        assert len(v) == len(set(v))
