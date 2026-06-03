"""
test_company_onboarding_schema.py — Verify Company Onboarding code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.company_onboarding.data.company_onboarding_data import (
    FIELD_VALIDATION_RULES,
    ENTITY_GROUP_IDS,
    ENTITY_GROUP_NAMES,
    BASE_CURRENCY_IDS,
    BASE_CURRENCY_NAMES,
    ADDRESS_TYPE_IDS,
    ADDRESS_TYPE_NAMES,
    COUNTRY_IDS,
    COUNTRY_NAMES,
    INFRASTRUCTURE_TYPE_IDS,
    INFRASTRUCTURE_TYPE_NAMES,
    OWNERSHIP_TYPE_IDS,
    OWNERSHIP_TYPE_NAMES,
    AUTHENTICATION_TYPE_IDS,
    AUTHENTICATION_TYPE_NAMES,
    DEFAULT_CO_FK_IDS,
)


@pytest.mark.schema
class TestCompanyOnboardingSchema:
    """Verify the Company Onboarding screen schema matches our code expectations."""

    def test_field_validation_rules_has_root_fields(self):
        """FIELD_VALIDATION_RULES should cover root-level fields."""
        root_fields = {"name", "user_type_id", "parent_id", "tenant_linked",
                       "level", "is_parent"}
        assert root_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_company_details(self):
        """FIELD_VALIDATION_RULES should cover Company Details stepper fields."""
        company_fields = {"tenant_short_name", "tenant_code", "contact_person_name",
                          "company_background", "email_id", "phone_no", "pan_no",
                          "tan_no", "gst_no", "cin_no", "plan_type_ref_id",
                          "is_2fa_applicable", "authentication_type", "base_currency"}
        assert company_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_promoters(self):
        """FIELD_VALIDATION_RULES should cover Promoters fields."""
        promoter_fields = {"promoter_name", "remark"}
        assert promoter_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_address_fields(self):
        """FIELD_VALIDATION_RULES should cover Address fields."""
        address_fields = {"address_type_ref_id", "country", "state", "district",
                          "taluka", "address", "pin_code"}
        assert address_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_business_fields(self):
        """FIELD_VALIDATION_RULES should cover Business Activities fields."""
        business_fields = {"business_model", "market_linkages",
                           "line_of_business", "additional_business_activities"}
        assert business_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_infrastructure_fields(self):
        """FIELD_VALIDATION_RULES should cover Infrastructure fields."""
        infra_fields = {"infrastructure_type_ref_id", "location",
                        "ownership_type", "remarks"}
        assert infra_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_tenant_code_max_length_is_4(self):
        """Company Code (tenant_code) should have max_length=4."""
        assert FIELD_VALIDATION_RULES["tenant_code"]["max_length"] == 4

    def test_phone_no_max_length_is_10(self):
        """Phone number should have max_length=10."""
        assert FIELD_VALIDATION_RULES["phone_no"]["max_length"] == 10

    def test_cin_no_max_length_is_21(self):
        """CIN should have max_length=21."""
        assert FIELD_VALIDATION_RULES["cin_no"]["max_length"] == 21

    def test_pin_code_max_length_is_6(self):
        """Pin Code should have max_length=6."""
        assert FIELD_VALIDATION_RULES["pin_code"]["max_length"] == 6

    def test_entity_group_has_1_option(self):
        """Entity Group dropdown should have 1 option (Branch only)."""
        assert FIELD_VALIDATION_RULES["user_type_id"]["fk_options_count"] == 1

    def test_base_currency_has_30_options(self):
        """Base Currency dropdown should have 30 options."""
        assert FIELD_VALIDATION_RULES["base_currency"]["fk_options_count"] == 30

    def test_address_type_has_2_options(self):
        """Address Type dropdown should have 2 options."""
        assert FIELD_VALIDATION_RULES["address_type_ref_id"]["fk_options_count"] == 2

    def test_country_has_30_options(self):
        """Country dropdown should have 30 options."""
        assert FIELD_VALIDATION_RULES["country"]["fk_options_count"] == 30

    def test_infrastructure_type_has_5_options(self):
        """Infrastructure Type dropdown should have 5 options."""
        assert FIELD_VALIDATION_RULES["infrastructure_type_ref_id"]["fk_options_count"] == 5

    def test_ownership_type_has_2_options(self):
        """Ownership Type dropdown should have 2 options."""
        assert FIELD_VALIDATION_RULES["ownership_type"]["fk_options_count"] == 2

    def test_authentication_type_has_2_options(self):
        """Authentication Type dropdown should have 2 options."""
        assert FIELD_VALIDATION_RULES["authentication_type"]["fk_options_count"] == 2

    def test_email_has_pattern(self):
        """Email should have a validation pattern."""
        email_rule = FIELD_VALIDATION_RULES["email_id"]
        assert email_rule.get("pattern") is not None

    def test_is_parent_is_not_required(self):
        """is_parent should not be required."""
        assert FIELD_VALIDATION_RULES["is_parent"]["required"] is False

    def test_default_fk_ids_valid(self):
        """DEFAULT_CO_FK_IDS values should be in valid pools."""
        assert DEFAULT_CO_FK_IDS["user_type_id"] in ENTITY_GROUP_IDS
        assert DEFAULT_CO_FK_IDS["base_currency"] in BASE_CURRENCY_IDS
        assert DEFAULT_CO_FK_IDS["address_type_ref_id"] in ADDRESS_TYPE_IDS
        assert DEFAULT_CO_FK_IDS["country"] in COUNTRY_IDS
        assert DEFAULT_CO_FK_IDS["infrastructure_type_ref_id"] in INFRASTRUCTURE_TYPE_IDS
        assert DEFAULT_CO_FK_IDS["ownership_type"] in OWNERSHIP_TYPE_IDS
        assert DEFAULT_CO_FK_IDS["authentication_type"] in AUTHENTICATION_TYPE_IDS

    def test_entity_group_names_complete(self):
        """ENTITY_GROUP_NAMES should map every ID."""
        for eid in ENTITY_GROUP_IDS:
            assert eid in ENTITY_GROUP_NAMES, f"Missing name for entity group {eid}"

    def test_base_currency_names_complete(self):
        """BASE_CURRENCY_NAMES should map every ID."""
        for cid in BASE_CURRENCY_IDS:
            assert cid in BASE_CURRENCY_NAMES, f"Missing name for currency {cid}"

    def test_address_type_names_complete(self):
        """ADDRESS_TYPE_NAMES should map every ID."""
        for aid in ADDRESS_TYPE_IDS:
            assert aid in ADDRESS_TYPE_NAMES, f"Missing name for address type {aid}"

    def test_country_names_complete(self):
        """COUNTRY_NAMES should map every ID."""
        for cid in COUNTRY_IDS:
            assert cid in COUNTRY_NAMES, f"Missing name for country {cid}"

    def test_infrastructure_type_names_complete(self):
        """INFRASTRUCTURE_TYPE_NAMES should map every ID."""
        for iid in INFRASTRUCTURE_TYPE_IDS:
            assert iid in INFRASTRUCTURE_TYPE_NAMES, f"Missing name for infra type {iid}"

    def test_ownership_type_names_complete(self):
        """OWNERSHIP_TYPE_NAMES should map every ID."""
        for oid in OWNERSHIP_TYPE_IDS:
            assert oid in OWNERSHIP_TYPE_NAMES, f"Missing name for ownership type {oid}"

    def test_authentication_type_names_complete(self):
        """AUTHENTICATION_TYPE_NAMES should map every ID (string values)."""
        for aid in AUTHENTICATION_TYPE_IDS:
            assert aid in AUTHENTICATION_TYPE_NAMES, f"Missing name for auth type {aid}"

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match FIELD_VALIDATION_RULES counts."""
        assert len(ENTITY_GROUP_IDS) == FIELD_VALIDATION_RULES["user_type_id"]["fk_options_count"]
        assert len(BASE_CURRENCY_IDS) == FIELD_VALIDATION_RULES["base_currency"]["fk_options_count"]
        assert len(ADDRESS_TYPE_IDS) == FIELD_VALIDATION_RULES["address_type_ref_id"]["fk_options_count"]
        assert len(COUNTRY_IDS) == FIELD_VALIDATION_RULES["country"]["fk_options_count"]
        assert len(INFRASTRUCTURE_TYPE_IDS) == FIELD_VALIDATION_RULES["infrastructure_type_ref_id"]["fk_options_count"]
        assert len(OWNERSHIP_TYPE_IDS) == FIELD_VALIDATION_RULES["ownership_type"]["fk_options_count"]
        assert len(AUTHENTICATION_TYPE_IDS) == FIELD_VALIDATION_RULES["authentication_type"]["fk_options_count"]
