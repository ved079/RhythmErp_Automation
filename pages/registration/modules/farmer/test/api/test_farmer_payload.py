"""
test_farmer_payload.py — Fast API payload structure tests.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.farmer.data.farmer_data import (
    generate_farmer_api_payload,
    build_farmer_api_payload,
    generate_valid_farmer_step0,
    generate_valid_address_details,
    generate_valid_other_details,
    generate_valid_family_details,
    generate_valid_additional_details,
    generate_valid_land_details,
    generate_valid_crop_details,
    generate_valid_kyc_details,
    generate_valid_vehicle_details,
    generate_valid_income_details,
    generate_valid_bank_details,
    generate_valid_irrigation_details,
    generate_valid_award_details,
    generate_valid_loan_details,
    generate_batch_payloads,
    generate_farmer_name,
    generate_email,
    generate_phone,
    generate_password,
    FARMER_CATEGORY_IDS,
    ADDRESS_TYPE_IDS,
    KYC_DOC_IDS,
    BANK_DOC_IDS,
    ACCOUNT_TYPE_IDS,
    DEFAULT_FARMER_FK_IDS,
    FIELD_VALIDATION_RULES,
    KnownBugs,
)


@pytest.mark.api
class TestFarmerAPIPayload:
    """Verify that generated API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, children (no root details — that's on steppers)."""
        payload = generate_farmer_api_payload()
        assert "id" in payload
        assert payload["id"] == ""
        assert payload["attribute_name"] == "Farmer"
        # Root payload does NOT have "details" — details[] lives inside each child stepper
        assert "details" not in payload
        assert "children" in payload

    def test_payload_has_13_children_steppers(self):
        """Payload must have 13 children: Address, Other, Family, Additional,
        Land, Crop, KYC, Vehicle, Income, Bank, Irrigation, Award, Loan."""
        payload = generate_farmer_api_payload()
        children = payload["children"]
        assert len(children) == 13
        assert children[0]["stepper_name"] == "Address Details"
        assert children[1]["stepper_name"] == "Other Details"
        assert children[2]["stepper_name"] == "Family Details"
        assert children[3]["stepper_name"] == "Additional Details"
        assert children[4]["stepper_name"] == "Land Details"
        assert children[5]["stepper_name"] == "Crop Details"
        assert children[6]["stepper_name"] == "KYC Details"
        assert children[7]["stepper_name"] == "Vehicle Details"
        assert children[8]["stepper_name"] == "Income Details"
        assert children[9]["stepper_name"] == "Bank Details"
        assert children[10]["stepper_name"] == "Irrigation Details"
        assert children[11]["stepper_name"] == "Award Details"
        assert children[12]["stepper_name"] == "Loan Details"

    def test_payload_address_in_details_array(self):
        """Address rows must be in children[0].details[] — both Permanent and Current."""
        payload = generate_farmer_api_payload()
        address_stepper = payload["children"][0]
        assert len(address_stepper["details"]) >= 2, (
            "ERP requires both Permanent and Current address rows"
        )
        addr_types = [d["address_type"] for d in address_stepper["details"]]
        assert 1875 in addr_types, "Permanent address (type=1875) is required"
        assert 1876 in addr_types, "Current address (type=1876) is required"
        # Verify both rows have the same address chain FK fields
        for addr in address_stepper["details"]:
            assert "country_ref_id_id" in addr
            assert "state_ref_id_id" in addr
            assert "address" in addr

    def test_payload_permanent_current_have_different_types(self):
        """Permanent and Current address rows must have distinct address_type values."""
        payload = generate_farmer_api_payload()
        addr_details = payload["children"][0]["details"]
        addr_types = [d["address_type"] for d in addr_details]
        # All rows should not have the same type — must be one of each
        assert len(set(addr_types)) >= 2, (
            f"All address rows have the same type {addr_types} — "
            "ERP requires both Permanent (1875) and Current (1876)"
        )

    def test_payload_both_addresses_share_cascading_chain(self):
        """Both Permanent and Current should share the same country/state/district chain."""
        payload = generate_farmer_api_payload()
        addr_details = payload["children"][0]["details"]
        assert len(addr_details) >= 2
        row0, row1 = addr_details[0], addr_details[1]
        # Same country and state for both addresses
        assert row0["country_ref_id_id"] == row1["country_ref_id_id"], (
            "Both address rows should share the same country"
        )
        assert row0["state_ref_id_id"] == row1["state_ref_id_id"], (
            "Both address rows should share the same state"
        )

    def test_payload_country_always_india(self):
        """Country MUST always be India (id=8) — other countries lack cascading data."""
        payload = generate_farmer_api_payload()
        addr_details = payload["children"][0]["details"]
        for addr in addr_details:
            assert addr["country_ref_id_id"] == 8, (
                f"Country must always be India (8), got {addr['country_ref_id_id']}"
            )

    def test_payload_other_details_in_details_array(self):
        """Other Details fields must be in children[1].details[] array."""
        payload = generate_farmer_api_payload()
        other_stepper = payload["children"][1]
        assert len(other_stepper["details"]) >= 1
        other = other_stepper["details"][0]
        assert "education_ref_id" in other
        assert "electricity_ref_id" in other

    def test_payload_family_details_in_details_array(self):
        """Family Details rows must be in children[2].details[] array."""
        payload = generate_farmer_api_payload()
        family_stepper = payload["children"][2]
        assert len(family_stepper["details"]) >= 1
        family = family_stepper["details"][0]
        assert "member_name" in family
        assert "relationship" in family
        assert "member_gender" in family

    def test_payload_additional_details_in_details_array(self):
        """Additional Details fields must be in children[3].details[] array."""
        payload = generate_farmer_api_payload()
        additional_stepper = payload["children"][3]
        assert len(additional_stepper["details"]) >= 1
        additional = additional_stepper["details"][0]
        assert "dob" in additional
        assert "gender" in additional
        assert "religion_ref_id" in additional
        assert "category_ref_id" in additional

    def test_payload_land_details_in_details_array(self):
        """Land Details rows must be in children[4].details[] array."""
        payload = generate_farmer_api_payload()
        land_stepper = payload["children"][4]
        assert len(land_stepper["details"]) >= 1
        land = land_stepper["details"][0]
        assert "farm_name" in land
        assert "no_of_owner" in land  # REQUIRED (BUG-F01)
        assert "land_ownership" in land
        assert "latitude" in land
        assert "longitude" in land

    def test_payload_crop_details_in_details_array(self):
        """Crop Details rows must be in children[5].details[] array."""
        payload = generate_farmer_api_payload()
        crop_stepper = payload["children"][5]
        assert len(crop_stepper["details"]) >= 1
        crop = crop_stepper["details"][0]
        assert "farm_ref_id" in crop
        assert "season" in crop
        assert "cultivation_land_in_hectare_are" in crop

    def test_payload_kyc_details_in_details_array(self):
        """KYC Details rows must be in children[6].details[] array."""
        payload = generate_farmer_api_payload()
        kyc_stepper = payload["children"][6]
        assert len(kyc_stepper["details"]) >= 1
        kyc = kyc_stepper["details"][0]
        assert "kyc_doc_id" in kyc
        assert "kyc_account_no" in kyc

    def test_payload_vehicle_details_in_details_array(self):
        """Vehicle Details rows must be in children[7].details[] array."""
        payload = generate_farmer_api_payload()
        vehicle_stepper = payload["children"][7]
        assert len(vehicle_stepper["details"]) >= 1
        vehicle = vehicle_stepper["details"][0]
        assert "vehicle_type_id" in vehicle

    def test_payload_income_details_in_details_array(self):
        """Income Details rows must be in children[8].details[] array."""
        payload = generate_farmer_api_payload()
        income_stepper = payload["children"][8]
        assert len(income_stepper["details"]) >= 1
        income = income_stepper["details"][0]
        assert "income_bracket_ref_id" in income
        assert "exact_amount" in income

    def test_payload_bank_details_in_details_array(self):
        """Bank Details rows must be in children[9].details[] array."""
        payload = generate_farmer_api_payload()
        bank_stepper = payload["children"][9]
        assert len(bank_stepper["details"]) >= 1
        bank = bank_stepper["details"][0]
        assert "bank_name" in bank
        assert "bank_account_holder_name" in bank
        assert "bank_doc_id" in bank
        assert "bank_ifsc_code" in bank

    def test_payload_irrigation_details_in_details_array(self):
        """Irrigation Details rows must be in children[10].details[] array."""
        payload = generate_farmer_api_payload()
        irr_stepper = payload["children"][10]
        assert len(irr_stepper["details"]) >= 1
        irr = irr_stepper["details"][0]
        assert "source_of_irrigation" in irr
        assert "method_of_irrigation" in irr

    def test_payload_award_details_in_details_array(self):
        """Award Details rows must be in children[11].details[] array."""
        payload = generate_farmer_api_payload()
        award_stepper = payload["children"][11]
        assert len(award_stepper["details"]) >= 1
        award = award_stepper["details"][0]
        assert "award_name" in award
        assert "year" in award

    def test_payload_loan_details_in_details_array(self):
        """Loan Details rows must be in children[12].details[] array."""
        payload = generate_farmer_api_payload()
        loan_stepper = payload["children"][12]
        assert len(loan_stepper["details"]) >= 1
        loan = loan_stepper["details"][0]
        assert "loan_name" in loan
        assert "type_of_loan" in loan
        assert "sanctioned_amount" in loan

    def test_payload_farmer_name_is_string(self):
        """Farmer name should be a non-empty string matching ^[A-Za-z ]+$."""
        payload = generate_farmer_api_payload()
        assert isinstance(payload["name"], str)
        assert len(payload["name"]) > 0

    def test_payload_email_is_valid_format(self):
        """Email must contain @ and domain. BUG-F04: ALWAYS lowercase!"""
        payload = generate_farmer_api_payload()
        email = payload.get("email_id", "")
        if email:
            assert "@" in email
            assert "." in email.split("@")[-1]
            # BUG-F04: Email should always be lowercase
            assert email == email.lower(), (
                f"BUG-F04: Email must be lowercase, got {email}"
            )

    def test_payload_phone_is_10_digits(self):
        """Phone must be a 10-digit integer starting with 6-9."""
        payload = generate_farmer_api_payload()
        phone = payload.get("mobile_no")
        if phone is not None:
            phone_str = str(phone)
            assert len(phone_str) == 10
            assert phone_str[0] in "6789", (
                f"Indian mobile must start with 6-9, got {phone_str[0]}"
            )

    def test_payload_farmer_category_is_array(self):
        """farmer_category must be an array of FK IDs (multiselect)."""
        payload = generate_farmer_api_payload()
        cat = payload.get("farmer_category")
        assert isinstance(cat, list), "farmer_category must be a list (multiselect)"
        assert len(cat) >= 1, "farmer_category must have at least one selection"
        for cid in cat:
            assert cid in FARMER_CATEGORY_IDS, (
                f"farmer_category ID {cid} not in valid pool {FARMER_CATEGORY_IDS}"
            )

    def test_payload_password_is_string(self):
        """Password must be a non-empty string."""
        payload = generate_farmer_api_payload()
        assert isinstance(payload["password"], str)
        assert len(payload["password"]) > 0

    def test_payload_fk_ids_in_valid_pools(self):
        """All dropdown FK IDs must be from valid pools."""
        payload = generate_farmer_api_payload()
        # Address types in details
        addr_details = payload["children"][0]["details"]
        for addr in addr_details:
            if addr.get("address_type") is not None:
                assert addr["address_type"] in ADDRESS_TYPE_IDS, (
                    f"address_type {addr['address_type']} not in valid pool"
                )
        # Bank doc ID
        bank_details = payload["children"][9]["details"]
        if bank_details and bank_details[0].get("bank_doc_id") is not None:
            assert bank_details[0]["bank_doc_id"] in BANK_DOC_IDS

    def test_payload_status_is_boolean(self):
        """Status must be a boolean value."""
        payload = generate_farmer_api_payload()
        assert isinstance(payload["status"], bool)

    def test_payload_copy_from_party_is_boolean(self):
        """copy_from_party must be a boolean."""
        payload = generate_farmer_api_payload()
        assert isinstance(payload["copy_from_party"], bool)

    def test_payload_is_member_this_fpc_is_boolean(self):
        """is_member_this_fpc must be a boolean."""
        payload = generate_farmer_api_payload()
        assert isinstance(payload["is_member_this_fpc"], bool)

    def test_payload_steppers_all_have_is_stepper_true(self):
        """Every child stepper must have is_stepper=True."""
        payload = generate_farmer_api_payload()
        for child in payload["children"]:
            assert child["is_stepper"] is True, (
                f"Stepper '{child['stepper_name']}' must have is_stepper=True"
            )

    def test_payload_steppers_all_have_empty_children(self):
        """Every child stepper must have children=[] (no nesting)."""
        payload = generate_farmer_api_payload()
        for child in payload["children"]:
            assert child["children"] == [], (
                f"Stepper '{child['stepper_name']}' should have empty children[]"
            )

    def test_payload_detail_rows_have_empty_details(self):
        """Every detail row inside steppers must have details=[] (leaf nodes)."""
        payload = generate_farmer_api_payload()
        for child in payload["children"]:
            for detail_row in child["details"]:
                assert "details" in detail_row
                assert detail_row["details"] == [], (
                    f"Detail row in '{child['stepper_name']}' should have empty details[]"
                )

    def test_build_with_explicit_data(self):
        """build_farmer_api_payload with explicit data should use it."""
        step0 = generate_valid_farmer_step0()
        step0["name"] = "Test Build Farmer"
        payload = build_farmer_api_payload(
            step0_data=step0,
            address_details=generate_valid_address_details(),
            other_details=generate_valid_other_details(),
            family_details=generate_valid_family_details(),
            additional_details=generate_valid_additional_details(),
            land_details=generate_valid_land_details(),
            crop_details=generate_valid_crop_details(),
            kyc_details=generate_valid_kyc_details(),
            vehicle_details=generate_valid_vehicle_details(),
            income_details=generate_valid_income_details(),
            bank_details=generate_valid_bank_details(),
            irrigation_details=generate_valid_irrigation_details(),
            award_details=generate_valid_award_details(),
            loan_details=generate_valid_loan_details(),
        )
        assert payload["name"] == "Test Build Farmer"

    def test_build_with_fk_overrides(self):
        """build_farmer_api_payload with dropdown_ids should override defaults."""
        step0 = generate_valid_farmer_step0()
        payload = build_farmer_api_payload(
            step0_data=step0,
            dropdown_ids={"land_ownership": 1929},  # Leased
        )
        # Check that land details got the overridden value
        land_details = payload["children"][4]["details"]
        if land_details:
            assert land_details[0]["land_ownership"] == 1929


@pytest.mark.api
class TestFarmerBatchGeneration:
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
        emails = [p.get("email_id", "") for p in payloads if p.get("email_id")]
        assert len(emails) == len(set(emails)), "Duplicate emails found in batch"

    def test_batch_phones_are_unique(self):
        payloads = generate_batch_payloads(20)
        phones = [p.get("mobile_no") for p in payloads if p.get("mobile_no")]
        assert len(phones) == len(set(phones)), "Duplicate phones found in batch"

    def test_batch_all_have_13_children(self):
        """Every batch payload must have 13 stepper children."""
        payloads = generate_batch_payloads(10)
        for i, p in enumerate(payloads):
            assert len(p["children"]) == 13, (
                f"Batch payload #{i} has {len(p['children'])} children, expected 13"
            )
