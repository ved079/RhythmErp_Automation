"""
test_member_schema.py â€” Verify Member code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.documents.modules.member.data.member_data import (
    FIELD_VALIDATION_RULES,
    PREFIX_IDS,
    PREFIX_NAMES,
    KYC_DOC_IDS,
    KYC_DOC_NAMES,
    PARTY_REF_IDS,
    DEFAULT_MEMBER_FK_IDS,
)


@pytest.mark.schema
class TestMemberSchema:
    """Verify the Member screen schema matches our code expectations."""

    def test_field_validation_rules_has_root_fields(self):
        """FIELD_VALIDATION_RULES should cover root-level fields."""
        root_fields = {
            "party_ref_id", "prefix_ref_id", "name", "member_address",
            "pan_no", "foli_number", "registration_date",
            "no_class_shares_held", "distintive_number",
            "amount_paid_on_shares", "date_of_allotment",
            "date_of_cessation", "percentage_of_shares",
            "mobile_no", "is_member_director",
        }
        assert root_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_kyc_fields(self):
        """FIELD_VALIDATION_RULES should cover KYC Details child fields."""
        kyc_fields = {"kyc_doc_id", "kyc_account_no", "attachment_path"}
        assert kyc_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_prefix_has_3_options(self):
        """Prefix dropdown should have 3 options (Mrs, Mr, Ms)."""
        assert FIELD_VALIDATION_RULES["prefix_ref_id"]["fk_options_count"] == 3

    def test_kyc_doc_has_2_options(self):
        """KYC Document dropdown should have 2 options (PAN, AADHAR)."""
        assert FIELD_VALIDATION_RULES["kyc_doc_id"]["fk_options_count"] == 2

    def test_party_ref_has_329_options(self):
        """Party Reference dropdown should have 329 options."""
        assert FIELD_VALIDATION_RULES["party_ref_id"]["fk_options_count"] == 329

    def test_pan_is_unique(self):
        """PAN should be marked as unique (server enforces uniqueness)."""
        assert FIELD_VALIDATION_RULES["pan_no"]["unique"] is True

    def test_name_is_required(self):
        """Member Name should be marked as required."""
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    def test_member_address_is_required(self):
        """Member Address should be marked as required."""
        assert FIELD_VALIDATION_RULES["member_address"]["required"] is True

    def test_pan_is_required(self):
        """PAN/Other should be marked as required."""
        assert FIELD_VALIDATION_RULES["pan_no"]["required"] is True

    def test_folio_number_is_required(self):
        """Folio Number should be marked as required."""
        assert FIELD_VALIDATION_RULES["foli_number"]["required"] is True

    def test_registration_date_is_required(self):
        """Registration Date should be marked as required."""
        assert FIELD_VALIDATION_RULES["registration_date"]["required"] is True

    def test_no_class_shares_held_is_required(self):
        """Number and Class of Shares should be marked as required."""
        assert FIELD_VALIDATION_RULES["no_class_shares_held"]["required"] is True

    def test_distintive_number_is_required(self):
        """Distinctive Number should be marked as required."""
        assert FIELD_VALIDATION_RULES["distintive_number"]["required"] is True

    def test_amount_paid_on_shares_is_required(self):
        """Amount Paid on Shares should be marked as required."""
        assert FIELD_VALIDATION_RULES["amount_paid_on_shares"]["required"] is True

    def test_date_of_allotment_is_required(self):
        """Date of Allotment should be marked as required."""
        assert FIELD_VALIDATION_RULES["date_of_allotment"]["required"] is True

    def test_date_of_cessation_is_optional(self):
        """Date of Cessation should be optional."""
        assert FIELD_VALIDATION_RULES["date_of_cessation"]["required"] is False

    def test_percentage_of_shares_is_required(self):
        """Percentage of Shares should be marked as required."""
        assert FIELD_VALIDATION_RULES["percentage_of_shares"]["required"] is True

    def test_mobile_no_is_required(self):
        """Phone Number should be marked as required."""
        assert FIELD_VALIDATION_RULES["mobile_no"]["required"] is True

    def test_is_member_director_is_optional(self):
        """Is Member Director should be optional."""
        assert FIELD_VALIDATION_RULES["is_member_director"]["required"] is False

    def test_party_ref_is_optional(self):
        """Party Reference should be optional."""
        assert FIELD_VALIDATION_RULES["party_ref_id"]["required"] is False

    def test_party_ref_has_onchange_event(self):
        """Party Reference should have onchange event (auto-patches fields)."""
        assert FIELD_VALIDATION_RULES["party_ref_id"]["is_onchange"] is True

    def test_party_ref_auto_patch_fields(self):
        """Party Reference auto-patch should cover expected fields."""
        auto_patch = FIELD_VALIDATION_RULES["party_ref_id"]["auto_patch_fields"]
        expected_patches = [
            "prefix_ref_id", "name", "pan_no", "mobile_no",
            "date_of_cessation", "no_class_shares_held",
            "percentage_of_shares",
        ]
        for field in expected_patches:
            assert field in auto_patch, f"Missing auto-patch field: {field}"

    def test_name_max_length_255(self):
        """Member Name max length should be 255."""
        assert FIELD_VALIDATION_RULES["name"]["max_length"] == 255

    def test_member_address_max_length_255(self):
        """Member Address max length should be 255."""
        assert FIELD_VALIDATION_RULES["member_address"]["max_length"] == 255

    def test_pan_max_length_255(self):
        """PAN max length should be 255."""
        assert FIELD_VALIDATION_RULES["pan_no"]["max_length"] == 255

    def test_mobile_no_max_length_10(self):
        """Phone Number max length should be 10."""
        assert FIELD_VALIDATION_RULES["mobile_no"]["max_length"] == 10

    def test_name_visible_in_table(self):
        """Member Name should be visible in listing table."""
        assert FIELD_VALIDATION_RULES["name"]["visible_in_table"] is True

    def test_pan_visible_in_table(self):
        """PAN should be visible in listing table."""
        assert FIELD_VALIDATION_RULES["pan_no"]["visible_in_table"] is True

    def test_mobile_no_visible_in_table(self):
        """Phone Number should be visible in listing table."""
        assert FIELD_VALIDATION_RULES["mobile_no"]["visible_in_table"] is True

    def test_amount_paid_is_integer_type(self):
        """Amount Paid on Shares should be integer type."""
        assert FIELD_VALIDATION_RULES["amount_paid_on_shares"]["type"] == "integer"

    def test_percentage_is_integer_type(self):
        """Percentage of Shares should be integer type."""
        assert FIELD_VALIDATION_RULES["percentage_of_shares"]["type"] == "integer"

    def test_mobile_no_is_integer_type(self):
        """Phone Number should be integer type."""
        assert FIELD_VALIDATION_RULES["mobile_no"]["type"] == "integer"

    def test_is_member_director_is_toggle_type(self):
        """Is Member Director should be toggle type."""
        assert FIELD_VALIDATION_RULES["is_member_director"]["type"] == "toggle"

    def test_kyc_doc_is_dropdown_type(self):
        """KYC Document should be dropdown type."""
        assert FIELD_VALIDATION_RULES["kyc_doc_id"]["type"] == "dropdown"

    def test_kyc_account_no_is_character_type(self):
        """KYC Number should be character type."""
        assert FIELD_VALIDATION_RULES["kyc_account_no"]["type"] == "character"

    def test_attachment_path_is_file_type(self):
        """KYC Attachment should be file type."""
        assert FIELD_VALIDATION_RULES["attachment_path"]["type"] == "file"

    def test_kyc_fields_are_grid_fields(self):
        """KYC fields should be marked as grid fields."""
        assert FIELD_VALIDATION_RULES["kyc_doc_id"]["is_grid"] is True
        assert FIELD_VALIDATION_RULES["kyc_account_no"]["is_grid"] is True
        assert FIELD_VALIDATION_RULES["attachment_path"]["is_grid"] is True

    def test_kyc_doc_is_required(self):
        """KYC Document should be required in the grid."""
        assert FIELD_VALIDATION_RULES["kyc_doc_id"]["required"] is True

    def test_kyc_account_no_is_required(self):
        """KYC Number should be required in the grid."""
        assert FIELD_VALIDATION_RULES["kyc_account_no"]["required"] is True

    def test_kyc_attachment_is_optional(self):
        """KYC Attachment should be optional."""
        assert FIELD_VALIDATION_RULES["attachment_path"]["required"] is False


@pytest.mark.schema
class TestMemberFKPools:
    """Verify FK ID pools are consistent and complete."""

    def test_prefix_ids_match_names(self):
        """Every PREFIX_ID should have a corresponding name."""
        for pid in PREFIX_IDS:
            assert pid in PREFIX_NAMES, f"Missing name for prefix ID {pid}"

    def test_prefix_names_match_ids(self):
        """Every PREFIX_NAME key should be in PREFIX_IDS."""
        for pid in PREFIX_NAMES:
            assert pid in PREFIX_IDS, f"Extra name for prefix ID {pid}"

    def test_kyc_doc_ids_match_names(self):
        """Every KYC_DOC_ID should have a corresponding name."""
        for kid in KYC_DOC_IDS:
            assert kid in KYC_DOC_NAMES, f"Missing name for KYC doc ID {kid}"

    def test_kyc_doc_names_match_ids(self):
        """Every KYC_DOC_NAME key should be in KYC_DOC_IDS."""
        for kid in KYC_DOC_NAMES:
            assert kid in KYC_DOC_IDS, f"Extra name for KYC doc ID {kid}"

    def test_prefix_ids_are_3(self):
        """Prefix pool should have exactly 3 options."""
        assert len(PREFIX_IDS) == 3

    def test_kyc_doc_ids_are_2(self):
        """KYC Document pool should have exactly 2 options."""
        assert len(KYC_DOC_IDS) == 2

    def test_default_fk_ids_valid(self):
        """DEFAULT_MEMBER_FK_IDS values should be in valid pools."""
        if DEFAULT_MEMBER_FK_IDS["prefix_ref_id"] is not None:
            assert DEFAULT_MEMBER_FK_IDS["prefix_ref_id"] in PREFIX_IDS
        if DEFAULT_MEMBER_FK_IDS["kyc_doc_id"] is not None:
            assert DEFAULT_MEMBER_FK_IDS["kyc_doc_id"] in KYC_DOC_IDS

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match FIELD_VALIDATION_RULES counts."""
        assert len(PREFIX_IDS) == FIELD_VALIDATION_RULES["prefix_ref_id"]["fk_options_count"]
        assert len(KYC_DOC_IDS) == FIELD_VALIDATION_RULES["kyc_doc_id"]["fk_options_count"]
        assert len(PARTY_REF_IDS) == FIELD_VALIDATION_RULES["party_ref_id"]["fk_options_count"]
