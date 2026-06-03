"""
test_company_onboarding_payload.py — Fast API payload structure tests.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.company_onboarding.data.company_onboarding_data import (
    generate_company_onboarding_api_payload,
    build_company_onboarding_api_payload,
    generate_batch_payloads,
    _generate_single_company,
    ENTITY_GROUP_IDS,
    BASE_CURRENCY_IDS,
    ADDRESS_TYPE_IDS,
    INFRASTRUCTURE_TYPE_IDS,
    OWNERSHIP_TYPE_IDS,
    AUTHENTICATION_TYPE_IDS,
    COUNTRY_IDS,
    DEFAULT_CO_FK_IDS,
    FIELD_VALIDATION_RULES,
)


@pytest.mark.api
class TestCompanyOnboardingAPIPayload:
    """Verify that generated API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, children (no root details)."""
        payload = generate_company_onboarding_api_payload()
        assert "id" in payload
        assert payload["id"] == ""
        assert payload["attribute_name"] == "Company Onboarding"
        # Root payload does NOT have "details" — details[] lives inside each child stepper
        assert "details" not in payload
        assert "children" in payload

    def test_payload_has_5_children_steppers(self):
        """Payload must have 5 children: Company Details, Promoters, Address, Business, Infrastructure."""
        payload = generate_company_onboarding_api_payload()
        children = payload["children"]
        assert len(children) == 5
        assert children[0]["stepper_name"] == "Company Details"
        assert children[1]["stepper_name"] == "Promoters Details"
        assert children[2]["stepper_name"] == "Address Details"
        assert children[3]["stepper_name"] == "Business Activities"
        assert children[4]["stepper_name"] == "Infrastructure Details"

    def test_payload_company_details_on_stepper(self):
        """Company Details fields must be ON the stepper object, NOT in details[]."""
        payload = generate_company_onboarding_api_payload()
        company_details = payload["children"][0]
        # details must be empty — fields are directly on stepper (NOT a grid)
        assert company_details["details"] == []
        # Key Company Details fields should exist directly on the stepper
        assert "tenant_short_name" in company_details
        assert "tenant_code" in company_details
        assert "contact_person_name" in company_details
        assert "company_background" in company_details
        assert "email_id" in company_details
        assert "phone_no" in company_details
        assert "pan_no" in company_details
        assert "cin_no" in company_details
        # Base Currency is in Company Details (not a separate Configuration stepper)
        assert "base_currency" in company_details
        # 2FA and authentication
        assert "is_2fa_applicable" in company_details
        assert "authentication_type" in company_details

    def test_payload_company_details_includes_base_currency(self):
        """Base Currency must be inside Company Details stepper (UI Step 6 merged into Step 1)."""
        payload = generate_company_onboarding_api_payload()
        company_details = payload["children"][0]
        assert company_details["base_currency"] in BASE_CURRENCY_IDS

    def test_payload_authentication_type_is_string(self):
        """authentication_type uses STRING values ('email'/'scanner'), not integer IDs."""
        payload = generate_company_onboarding_api_payload()
        company_details = payload["children"][0]
        auth_type = company_details["authentication_type"]
        assert isinstance(auth_type, str)
        assert auth_type in AUTHENTICATION_TYPE_IDS

    def test_payload_root_has_entity_group(self):
        """Root must have user_type_id (Entity Group) as integer FK."""
        payload = generate_company_onboarding_api_payload()
        assert "user_type_id" in payload
        assert payload["user_type_id"] in ENTITY_GROUP_IDS

    def test_payload_root_has_level_and_is_parent(self):
        """Root must have level and is_parent fields."""
        payload = generate_company_onboarding_api_payload()
        assert "level" in payload
        assert "is_parent" in payload
        assert isinstance(payload["is_parent"], bool)

    def test_payload_promoters_in_details_array(self):
        """Promoters rows must be in children[1].details[] array."""
        payload = generate_company_onboarding_api_payload()
        promoters_stepper = payload["children"][1]
        assert len(promoters_stepper["details"]) >= 1
        promoter = promoters_stepper["details"][0]
        assert "promoter_name" in promoter
        assert "remark" in promoter

    def test_payload_address_in_details_array(self):
        """Address rows must be in children[2].details[] array."""
        payload = generate_company_onboarding_api_payload()
        address_stepper = payload["children"][2]
        assert len(address_stepper["details"]) >= 1
        addr = address_stepper["details"][0]
        assert "address_type_ref_id" in addr
        assert "country" in addr
        assert "state" in addr
        assert "district" in addr
        assert "taluka" in addr
        assert "address" in addr
        assert "pin_code" in addr

    def test_payload_business_in_details_array(self):
        """Business Activities rows must be in children[3].details[] array."""
        payload = generate_company_onboarding_api_payload()
        business_stepper = payload["children"][3]
        assert len(business_stepper["details"]) >= 1
        biz = business_stepper["details"][0]
        assert "business_model" in biz
        assert "market_linkages" in biz
        assert "line_of_business" in biz
        assert "additional_business_activities" in biz

    def test_payload_infrastructure_in_details_array(self):
        """Infrastructure Details rows must be in children[4].details[] array."""
        payload = generate_company_onboarding_api_payload()
        infra_stepper = payload["children"][4]
        assert len(infra_stepper["details"]) >= 1
        infra = infra_stepper["details"][0]
        assert "infrastructure_type_ref_id" in infra
        assert "location" in infra
        assert "ownership_type" in infra
        assert "remarks" in infra

    def test_payload_company_name_is_string(self):
        """Company name should be a non-empty string."""
        payload = generate_company_onboarding_api_payload()
        assert isinstance(payload["name"], str)
        assert len(payload["name"]) > 0

    def test_payload_email_is_valid_format(self):
        """Email must contain @ and domain."""
        payload = generate_company_onboarding_api_payload()
        email = payload["children"][0].get("email_id", "")
        if email:
            assert "@" in email
            assert "." in email.split("@")[-1]

    def test_payload_phone_is_10_digits(self):
        """Phone must be a 10-digit number."""
        payload = generate_company_onboarding_api_payload()
        phone = payload["children"][0].get("phone_no")
        if phone:
            phone_str = str(phone)
            assert len(phone_str) == 10

    def test_payload_pan_format(self):
        """PAN must be 10 characters: 5 letters + 4 digits + 1 letter."""
        payload = generate_company_onboarding_api_payload()
        pan = payload["children"][0].get("pan_no", "")
        if pan:
            assert len(pan) == 10
            assert pan[:5].isalpha()
            assert pan[5:9].isdigit()
            assert pan[9].isalpha()

    def test_payload_tenant_code_max_4_chars(self):
        """Company Code (tenant_code) must be at most 4 characters."""
        payload = generate_company_onboarding_api_payload()
        code = payload["children"][0].get("tenant_code", "")
        if code:
            assert len(code) <= 4

    def test_payload_cin_format(self):
        """CIN should start with U and follow standard format."""
        payload = generate_company_onboarding_api_payload()
        cin = payload["children"][0].get("cin_no", "")
        if cin:
            assert cin[0] == "U"
            assert len(cin) <= 21

    def test_payload_fk_ids_in_valid_pools(self):
        """All dropdown FK IDs must be from valid pools."""
        payload = generate_company_onboarding_api_payload()
        # Root-level FKs
        if payload.get("user_type_id"):
            assert payload["user_type_id"] in ENTITY_GROUP_IDS
        # Company Details FKs
        cd = payload["children"][0]
        if cd.get("base_currency"):
            assert cd["base_currency"] in BASE_CURRENCY_IDS
        # Address FKs
        addr = payload["children"][2]["details"][0]
        if addr.get("address_type_ref_id"):
            assert addr["address_type_ref_id"] in ADDRESS_TYPE_IDS
        if addr.get("country"):
            assert addr["country"] in COUNTRY_IDS
        # Infrastructure FKs
        infra = payload["children"][4]["details"][0]
        if infra.get("infrastructure_type_ref_id"):
            assert infra["infrastructure_type_ref_id"] in INFRASTRUCTURE_TYPE_IDS
        if infra.get("ownership_type"):
            assert infra["ownership_type"] in OWNERSHIP_TYPE_IDS

    def test_payload_is_2fa_is_boolean(self):
        """is_2fa_applicable must be a boolean value."""
        payload = generate_company_onboarding_api_payload()
        assert isinstance(payload["children"][0]["is_2fa_applicable"], bool)

    def test_build_with_explicit_data(self):
        """build_company_onboarding_api_payload with explicit data should use it."""
        company_data = _generate_single_company()
        company_data["company_name"] = "Test Build Company Co"
        payload = build_company_onboarding_api_payload(company_data)
        assert payload["name"] == "Test Build Company Co"

    def test_build_with_fk_overrides(self):
        """build_company_onboarding_api_payload with dropdown_ids should override defaults."""
        company_data = _generate_single_company()
        payload = build_company_onboarding_api_payload(
            company_data,
            dropdown_ids={"base_currency": 39}  # USD
        )
        assert payload["children"][0]["base_currency"] == 39


@pytest.mark.api
class TestCompanyOnboardingBatchGeneration:
    """Verify batch generation produces unique, valid payloads."""

    def test_batch_generates_correct_count(self):
        payloads = generate_batch_payloads(5)
        assert len(payloads) == 5

    def test_batch_names_are_unique(self):
        payloads = generate_batch_payloads(20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"

    def test_batch_emails_are_unique(self):
        payloads = generate_batch_payloads(20)
        emails = [p["children"][0].get("email_id", "") for p in payloads if p["children"][0].get("email_id")]
        assert len(emails) == len(set(emails)), "Duplicate emails found in batch"

    def test_batch_pans_are_unique(self):
        payloads = generate_batch_payloads(20)
        pans = [p["children"][0].get("pan_no", "") for p in payloads if p["children"][0].get("pan_no")]
        assert len(pans) == len(set(pans)), "Duplicate PANs found in batch"
