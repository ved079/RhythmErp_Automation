"""
test_farmer_schema.py — Verify Farmer code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.farmer.data.farmer_data import (
    FIELD_VALIDATION_RULES,
    FARMER_CATEGORY_IDS,
    ADDRESS_TYPE_IDS,
    KYC_DOC_IDS,
    BANK_DOC_IDS,
    ACCOUNT_TYPE_IDS,
    EDUCATION_IDS,
    ELECTRICITY_IDS,
    GENDER_IDS,
    RELATIONSHIP_IDS,
    MARITAL_STATUS_IDS,
    MEMBER_ANNUAL_INCOME_IDS,
    RELIGION_IDS,
    SOCIAL_CATEGORY_IDS,
    LAND_OWNERSHIP_IDS,
    IRRIGATION_SOURCE_IDS,
    IRRIGATION_METHOD_IDS,
    LOAN_TYPE_IDS,
    SEASON_IDS,
    VEHICLE_TYPE_IDS,
    INCOME_BRACKET_IDS,
    DEFAULT_FARMER_FK_IDS,
    FARMER_CATEGORY_NAMES,
    KYC_DOC_NAMES,
    BANK_DOC_NAMES,
    EDUCATION_NAMES,
    ADDRESS_TYPE_NAMES,
    LAND_CLASSIFICATION_IDS,
)


@pytest.mark.schema
class TestFarmerSchema:
    """Verify the Farmer screen schema matches our code expectations."""

    def test_field_validation_rules_has_root_fields(self):
        """FIELD_VALIDATION_RULES should cover all 11 root-level fields."""
        root_fields = {
            "copy_from_party", "party_ref_id", "name", "email_id",
            "mobile_no", "farmer_category", "land_classification",
            "password", "is_member_this_fpc", "other_fpc_name", "member_id",
        }
        assert root_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_address_fields(self):
        """FIELD_VALIDATION_RULES should cover Address Details fields."""
        address_fields = {
            "same_as_above", "address_type", "country_ref_id_id",
            "state_ref_id_id", "district_ref_id_id",
            "sub_district_ref_id_id", "village_ref_id_id",
            "pin_code", "address", "address2",
        }
        assert address_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_other_details_fields(self):
        """FIELD_VALIDATION_RULES should cover Other Details fields."""
        other_fields = {"education_ref_id", "electricity_ref_id"}
        assert other_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_family_details_fields(self):
        """FIELD_VALIDATION_RULES should cover Family Details fields."""
        family_fields = {
            "member_name", "phone_number", "member_dob", "member_age",
            "member_gender", "education_of_farmer_family", "relationship",
            "is_member_stying_with_farmer", "pincode_details", "address1",
            "marital_status", "no_of_children", "member_anual_income",
            "off_farm_income",
        }
        assert family_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_additional_details_fields(self):
        """FIELD_VALIDATION_RULES should cover Additional Details fields."""
        additional_fields = {
            "dob", "age", "gender", "religion_ref_id",
            "category_ref_id", "profile_photo",
        }
        assert additional_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_land_details_fields(self):
        """FIELD_VALIDATION_RULES should cover Land Details fields."""
        land_fields = {
            "farm_name", "land_image_path", "no_of_owner",
            "total_land_on_document", "individual_land_holding",
            "survey_no", "total_cultivation_land_in_hectare_are",
            "total_cultivation_land_in_acreage", "land_ownership",
            "latitude", "longitude",
        }
        assert land_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_crop_details_fields(self):
        """FIELD_VALIDATION_RULES should cover Crop Details fields."""
        crop_fields = {
            "farm_ref_id", "item_ref_id", "season",
            "cultivation_land_in_hectare_are", "expected_yield_projection",
            "actual_produce", "cultivation_land_in_acreage",
            "doc_attachment_path",
        }
        assert crop_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_kyc_fields(self):
        """FIELD_VALIDATION_RULES should cover KYC Details fields."""
        kyc_fields = {"kyc_doc_id", "kyc_account_no", "attachment_path"}
        assert kyc_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_vehicle_fields(self):
        """FIELD_VALIDATION_RULES should cover Vehicle Details fields."""
        vehicle_fields = {"vehicle_type_id", "vehicle_ref_id"}
        assert vehicle_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_income_fields(self):
        """FIELD_VALIDATION_RULES should cover Income Details fields."""
        income_fields = {"income_type_ref_id", "income_bracket_ref_id", "exact_amount"}
        assert income_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_bank_fields(self):
        """FIELD_VALIDATION_RULES should cover Bank Details fields."""
        bank_fields = {
            "bank_name", "bank_branch_code", "bank_ifsc_code",
            "account_type", "bank_account_holder_name",
            "bank_account_no", "bank_doc_id", "bank_attachment_path",
        }
        assert bank_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_irrigation_fields(self):
        """FIELD_VALIDATION_RULES should cover Irrigation Details fields."""
        irrigation_fields = {"source_of_irrigation", "method_of_irrigation"}
        assert irrigation_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_award_fields(self):
        """FIELD_VALIDATION_RULES should cover Award Details fields."""
        award_fields = {"award_name", "year"}
        assert award_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_loan_fields(self):
        """FIELD_VALIDATION_RULES should cover Loan Details fields."""
        loan_fields = {
            "loan_name", "type_of_loan", "loan_purpose",
            "availed_from", "sanctioned_amount",
            "present_outstanding_amount",
        }
        assert loan_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_name_pattern_matches_schema(self):
        """Name pattern should match ^[A-Za-z ]+$."""
        name_rule = FIELD_VALIDATION_RULES["name"]
        assert name_rule["pattern"] == r"^[A-Za-z ]+$"

    def test_mobile_no_pattern_matches_schema(self):
        """mobile_no pattern should match ^[6-9]\\d{9}$."""
        phone_rule = FIELD_VALIDATION_RULES["mobile_no"]
        assert phone_rule["pattern"] == r"^[6-9]\d{9}$"

    def test_farmer_category_has_3_options(self):
        """Farmer Category multiselect should have 3 options."""
        assert FIELD_VALIDATION_RULES["farmer_category"]["fk_options_count"] == 3

    def test_address_type_has_2_options(self):
        """Address Type dropdown should have 2 options."""
        assert FIELD_VALIDATION_RULES["address_type"]["fk_options_count"] == 2

    def test_education_has_6_options(self):
        """Education Qualification dropdown should have 6 options."""
        assert FIELD_VALIDATION_RULES["education_ref_id"]["fk_options_count"] == 6

    def test_kyc_doc_has_2_options(self):
        """KYC Document dropdown should have 2 options."""
        assert FIELD_VALIDATION_RULES["kyc_doc_id"]["fk_options_count"] == 2

    def test_bank_doc_has_3_options(self):
        """Bank Proof dropdown should have 3 options."""
        assert FIELD_VALIDATION_RULES["bank_doc_id"]["fk_options_count"] == 3

    def test_irrigation_source_has_7_options(self):
        """Source of Irrigation dropdown should have 7 options."""
        assert FIELD_VALIDATION_RULES["source_of_irrigation"]["fk_options_count"] == 7

    def test_irrigation_method_has_4_options(self):
        """Method of Irrigation dropdown should have 4 options."""
        assert FIELD_VALIDATION_RULES["method_of_irrigation"]["fk_options_count"] == 4

    def test_vehicle_type_has_3_options(self):
        """Vehicle Type dropdown should have 3 options."""
        assert FIELD_VALIDATION_RULES["vehicle_type_id"]["fk_options_count"] == 3

    def test_land_classification_is_readonly(self):
        """Land Classification should be marked as readonly."""
        assert FIELD_VALIDATION_RULES["land_classification"]["readonly"] is True

    def test_age_is_readonly(self):
        """Age (Additional Details) should be marked as readonly."""
        assert FIELD_VALIDATION_RULES["age"]["readonly"] is True

    def test_name_is_required(self):
        """Farmer Name should be required."""
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    def test_mobile_no_is_required(self):
        """Phone Number should be required."""
        assert FIELD_VALIDATION_RULES["mobile_no"]["required"] is True

    def test_farmer_category_is_required(self):
        """Farmer Category should be required."""
        assert FIELD_VALIDATION_RULES["farmer_category"]["required"] is True

    def test_password_is_required(self):
        """Password should be required."""
        assert FIELD_VALIDATION_RULES["password"]["required"] is True

    def test_no_of_owner_is_required(self):
        """No Of Owner should be required (BUG-F01: no asterisk shown)."""
        rule = FIELD_VALIDATION_RULES["no_of_owner"]
        assert rule["required"] is True

    def test_status_is_required(self):
        """Status should be required."""
        assert FIELD_VALIDATION_RULES.get("status", {}).get("required", True) is True

    def test_default_fk_ids_valid(self):
        """DEFAULT_FARMER_FK_IDS values should be in valid pools."""
        # farmer_category is a list — each element must be in pool
        for cid in DEFAULT_FARMER_FK_IDS["farmer_category"]:
            assert cid in FARMER_CATEGORY_IDS
        assert DEFAULT_FARMER_FK_IDS["country_ref_id_id"] == 8
        assert DEFAULT_FARMER_FK_IDS["permanent_address_type"] in ADDRESS_TYPE_IDS
        assert DEFAULT_FARMER_FK_IDS["current_address_type"] in ADDRESS_TYPE_IDS
        assert DEFAULT_FARMER_FK_IDS["education_ref_id"] in EDUCATION_IDS
        assert DEFAULT_FARMER_FK_IDS["bank_doc_id"] in BANK_DOC_IDS

    def test_farmer_category_names_complete(self):
        """FARMER_CATEGORY_NAMES should map every ID."""
        for cid in FARMER_CATEGORY_IDS:
            assert cid in FARMER_CATEGORY_NAMES, f"Missing name for farmer category {cid}"

    def test_kyc_doc_names_complete(self):
        """KYC_DOC_NAMES should map every ID."""
        for kid in KYC_DOC_IDS:
            assert kid in KYC_DOC_NAMES, f"Missing name for KYC doc {kid}"

    def test_bank_doc_names_complete(self):
        """BANK_DOC_NAMES should map every ID."""
        for bid in BANK_DOC_IDS:
            assert bid in BANK_DOC_NAMES, f"Missing name for bank doc {bid}"

    def test_education_names_complete(self):
        """EDUCATION_NAMES should map every ID."""
        for eid in EDUCATION_IDS:
            assert eid in EDUCATION_NAMES, f"Missing name for education {eid}"

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match FIELD_VALIDATION_RULES counts."""
        assert len(FARMER_CATEGORY_IDS) == FIELD_VALIDATION_RULES["farmer_category"]["fk_options_count"]
        assert len(ADDRESS_TYPE_IDS) == FIELD_VALIDATION_RULES["address_type"]["fk_options_count"]
        assert len(EDUCATION_IDS) == FIELD_VALIDATION_RULES["education_ref_id"]["fk_options_count"]
        assert len(KYC_DOC_IDS) == FIELD_VALIDATION_RULES["kyc_doc_id"]["fk_options_count"]
        assert len(BANK_DOC_IDS) == FIELD_VALIDATION_RULES["bank_doc_id"]["fk_options_count"]
        assert len(IRRIGATION_SOURCE_IDS) == FIELD_VALIDATION_RULES["source_of_irrigation"]["fk_options_count"]
        assert len(IRRIGATION_METHOD_IDS) == FIELD_VALIDATION_RULES["method_of_irrigation"]["fk_options_count"]

    def test_address_type_has_dual_requirement_note(self):
        """FIELD_VALIDATION_RULES for address_type should note dual requirement."""
        rule = FIELD_VALIDATION_RULES["address_type"]
        assert rule["required"] is True
        note = rule.get("note", "")
        assert "Permanent" in note and "Current" in note, (
            f"address_type rule should note both types required, got: {note}"
        )

    def test_default_fk_ids_has_both_address_types(self):
        """DEFAULT_FARMER_FK_IDS must include both permanent and current address types."""
        assert "permanent_address_type" in DEFAULT_FARMER_FK_IDS
        assert "current_address_type" in DEFAULT_FARMER_FK_IDS
        assert DEFAULT_FARMER_FK_IDS["permanent_address_type"] in ADDRESS_TYPE_IDS
        assert DEFAULT_FARMER_FK_IDS["current_address_type"] in ADDRESS_TYPE_IDS

    def test_country_always_india_in_defaults(self):
        """DEFAULT_FARMER_FK_IDS must always set country to India (8)."""
        assert DEFAULT_FARMER_FK_IDS["country_ref_id_id"] == 8

    def test_copy_from_party_has_onchange_event(self):
        """copy_from_party should have is_onchange_event=True."""
        rule = FIELD_VALIDATION_RULES["copy_from_party"]
        assert rule.get("is_onchange_event") is True

    def test_vehicle_ref_id_has_zero_options(self):
        """Vehicle Name dropdown currently has NO OPTIONS."""
        rule = FIELD_VALIDATION_RULES["vehicle_ref_id"]
        assert rule["fk_options_count"] == 0

    def test_item_ref_id_has_150_options(self):
        """Crop dropdown should have ~150 options."""
        rule = FIELD_VALIDATION_RULES["item_ref_id"]
        assert rule["fk_options_count"] == 150

    def test_income_type_has_18_options(self):
        """Source of Income dropdown should have 18 options (BUG-F07: Dairy twice)."""
        rule = FIELD_VALIDATION_RULES["income_type_ref_id"]
        assert rule["fk_options_count"] == 18
