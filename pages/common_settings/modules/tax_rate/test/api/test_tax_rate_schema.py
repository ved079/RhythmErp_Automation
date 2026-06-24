"""test_tax_rate_schema.py — Verify Tax Rate code matches live ERP schema."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    FIELD_VALIDATION_RULES, REVISION_STATUS_OPTIONS, STEPPER_NAME,
    HSN_SAC_CODES, get_field_validation_rules, get_fk_screen_mapping,
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

    def test_fk_options_count_placeholder(self):
        for fn in ("tax_type_ref_id", "tax_authority_ref_id", "hsn_sac_number"):
            assert FIELD_VALIDATION_RULES[fn]["fk_options_count"] == 0

    def test_revision_status_options_has_active(self):
        assert "Active" in REVISION_STATUS_OPTIONS

    def test_stepper_name_is_correct(self):
        assert STEPPER_NAME == "Define Tax Rate Details"

    def test_hsn_sac_codes_pool_has_24_entries(self):
        assert len(HSN_SAC_CODES) == 24

    def test_get_field_validation_rules_is_callable(self):
        rules = get_field_validation_rules()
        assert rules["tax_rate_name"]["required"] is True

    def test_get_fk_screen_mapping_has_3_entries(self):
        mapping = get_fk_screen_mapping()
        assert len(mapping) == 3
        fields = set(mapping)
        assert fields == {"tax_type_ref_id", "tax_authority_ref_id", "hsn_sac_number"}
