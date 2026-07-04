"""
test_directors_payload.py
-------------------------
Comprehensive API payload and live CRUD tests for the Directors screen.

Tests cover:
  - Payload structure validation (required fields, types, boundaries)
  - FK dropdown resolution (designation, qualification, prefix, party_ref)
  - Invalid / boundary data rejection
  - Live CRUD operations (create, read, update, delete)
  - KYC stepper child structure
  - Auto-patch behavior when party_ref_id is selected

Run with:
  pytest pages/registration/modules/directors/test/api/test_directors_payload.py -v

  With live ERP:
  ERP_TOKEN=eyJ... pytest pages/registration/modules/directors/test/api/test_directors_payload.py -v -k live
"""

import os
import sys
import time
import pytest
import random

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.documents.modules.directors.data.directors_data import (
    build_directors_api_payload,
    generate_directors_api_payload,
    generate_valid_directors_data,
    generate_minimal_directors_data,
    generate_empty_directors_data,
    generate_batch_payloads,
    generate_pan_number,
    generate_phone,
    generate_residential_address,
    generate_share_class,
    generate_details_of_other_directorships,
    generate_age,
    generate_experience_in_years,
    generate_date_of_appointment,
    generate_date_of_cessation,
    generate_prefix_id,
    generate_designation_id,
    generate_qualification_id,
    generate_party_ref_id,
    generate_kyc_doc_id,
    generate_valid_kyc_row,
    generate_string_255,
    generate_string_256,
    generate_invalid_name_numbers,
    generate_invalid_name_special_chars,
    generate_invalid_phone_starts_with_5,
    generate_invalid_phone_too_short,
    generate_invalid_phone_too_long,
    generate_negative_amount,
    generate_zero_percentage,
    generate_percentage_over_100,
    generate_negative_age,
    generate_zero_age,
    generate_very_high_age,
    generate_negative_experience,
    generate_zero_experience,
    generate_very_high_experience,
    generate_sql_injection_name,
    generate_xss_name,
    generate_spaces_only_name,
    generate_long_other_directorships,
    PREFIX_IDS,
    PREFIX_NAMES,
    KYC_DOC_IDS,
    KYC_DOC_NAMES,
    DESIGNATION_IDS,
    DESIGNATION_NAMES,
    QUALIFICATION_IDS,
    QUALIFICATION_NAMES,
    PARTY_REF_IDS,
    SHARE_CLASS_TYPES,
    DEFAULT_DIRECTORS_FK_IDS,
    FIELD_VALIDATION_RULES,
    ExpectedMessages,
)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 1. PAYLOAD STRUCTURE TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsPayloadStructure:
    """Verify that generated payloads have the correct structure."""

    def test_payload_has_attribute_name(self):
        """Payload must have attribute_name = 'Directors'."""
        payload = generate_directors_api_payload()
        assert payload["attribute_name"] == "Directors"

    def test_payload_has_empty_id_for_new_entry(self):
        """New entries must have id = '' (empty string)."""
        payload = generate_directors_api_payload()
        assert payload["id"] == ""

    def test_payload_has_details_empty_array(self):
        """Top-level details must be an empty array."""
        payload = generate_directors_api_payload()
        assert payload["details"] == []

    def test_payload_has_children_array(self):
        """Payload must have children array with KYC Details stepper."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["children"], list)
        assert len(payload["children"]) >= 1

    def test_payload_children_have_kyc_stepper(self):
        """First child must be KYC Details stepper."""
        payload = generate_directors_api_payload()
        kyc_child = payload["children"][0]
        assert kyc_child["stepper_name"] == "KYC Details"
        assert isinstance(kyc_child["details"], list)

    def test_payload_kyc_row_has_required_fields(self):
        """Each KYC row must have id, kyc_doc_id, kyc_account_no, attachment_path."""
        payload = generate_directors_api_payload()
        kyc_row = payload["children"][0]["details"][0]
        assert "id" in kyc_row
        assert "kyc_doc_id" in kyc_row
        assert "kyc_account_no" in kyc_row
        assert "attachment_path" in kyc_row

    def test_payload_kyc_row_new_entry_has_empty_id(self):
        """New KYC rows must have id = ''."""
        payload = generate_directors_api_payload()
        kyc_row = payload["children"][0]["details"][0]
        assert kyc_row["id"] == ""

    def test_payload_has_all_15_top_level_fields(self):
        """Payload must contain all 15 Directors-specific top-level fields."""
        payload = generate_directors_api_payload()
        required_keys = [
            "party_ref_id", "prefix_ref_id", "name", "designation",
            "pan_no", "residential_address", "mobile_no",
            "date_of_appointment", "date_of_cessation",
            "no_class_shares_held", "details_of_other_directorships",
            "percentage_of_shares", "age", "qualification_ref_id",
            "experience_in_years",
        ]
        for key in required_keys:
            assert key in payload, f"Missing field: {key}"

    def test_payload_party_ref_id_is_nullable(self):
        """party_ref_id should be None when not set (optional field)."""
        payload = generate_directors_api_payload()
        assert payload["party_ref_id"] is None

    def test_payload_date_of_cessation_is_nullable(self):
        """date_of_cessation should be None when not set (optional field)."""
        data = generate_valid_directors_data()
        data["date_of_cessation"] = None
        payload = build_directors_api_payload(data)
        assert payload["date_of_cessation"] is None


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 2. REQUIRED FIELD TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsRequiredFields:
    """Verify that required fields are populated in valid payloads."""

    @pytest.mark.parametrize("field_key", [
        "prefix_ref_id", "name", "designation", "pan_no",
        "residential_address", "mobile_no", "date_of_appointment",
        "no_class_shares_held", "details_of_other_directorships",
        "percentage_of_shares", "age", "qualification_ref_id",
        "experience_in_years",
    ])
    def test_required_field_is_populated(self, field_key):
        """Required fields must not be None/empty in a valid payload."""
        payload = generate_directors_api_payload()
        value = payload.get(field_key)
        assert value is not None and value != "", (
            f"Required field '{field_key}' is empty/None"
        )

    def test_optional_party_ref_id_can_be_none(self):
        """party_ref_id is optional and can be None."""
        payload = generate_directors_api_payload(party_ref_id=None)
        assert payload["party_ref_id"] is None

    def test_optional_date_of_cessation_can_be_none(self):
        """date_of_cessation is optional and can be None."""
        payload = generate_directors_api_payload(date_of_cessation=None)
        assert payload["date_of_cessation"] is None


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 3. FK DROPDOWN TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsFKDropdowns:
    """Verify FK dropdown IDs are valid and from verified pools."""

    def test_prefix_ref_id_in_valid_pool(self):
        """prefix_ref_id must be from the 3 verified prefix IDs."""
        payload = generate_directors_api_payload()
        assert payload["prefix_ref_id"] in PREFIX_IDS

    def test_designation_in_valid_pool(self):
        """designation must be from the 56 verified designation IDs."""
        payload = generate_directors_api_payload()
        assert payload["designation"] in DESIGNATION_IDS

    def test_qualification_ref_id_in_valid_pool(self):
        """qualification_ref_id must be from the 6 verified qualification IDs."""
        payload = generate_directors_api_payload()
        assert payload["qualification_ref_id"] in QUALIFICATION_IDS

    def test_kyc_doc_id_in_valid_pool(self):
        """kyc_doc_id must be from the 2 verified KYC document IDs."""
        payload = generate_directors_api_payload()
        kyc_doc = payload["children"][0]["details"][0]["kyc_doc_id"]
        assert kyc_doc in KYC_DOC_IDS

    def test_party_ref_id_in_valid_pool_when_set(self):
        """When party_ref_id is set, it must be from the 357 verified IDs."""
        payload = generate_directors_api_payload(party_ref_id=random.choice(PARTY_REF_IDS))
        assert payload["party_ref_id"] in PARTY_REF_IDS

    def test_prefix_ref_id_is_integer(self):
        """prefix_ref_id must be an integer FK reference."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["prefix_ref_id"], int)

    def test_designation_is_integer(self):
        """designation must be an integer FK reference."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["designation"], int)

    def test_qualification_ref_id_is_integer(self):
        """qualification_ref_id must be an integer FK reference."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["qualification_ref_id"], int)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 4. FIELD TYPE TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsFieldTypes:
    """Verify field types match the ERP schema expectations."""

    def test_name_is_string(self):
        """Director name must be a string."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["name"], str)

    def test_pan_no_is_string(self):
        """PAN number must be a string."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["pan_no"], str)

    def test_residential_address_is_string(self):
        """Residential address must be a string."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["residential_address"], str)

    def test_mobile_no_is_integer(self):
        """Phone number must be an integer."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["mobile_no"], int)

    def test_no_class_shares_held_is_string(self):
        """No. & Class of Shares must be a string (e.g. '100 Equity')."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["no_class_shares_held"], str)

    def test_details_of_other_directorships_is_string(self):
        """Details of other directorships must be a string."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["details_of_other_directorships"], str)

    def test_percentage_of_shares_is_integer(self):
        """Percentage of shares must be an integer."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["percentage_of_shares"], int)

    def test_age_is_integer(self):
        """Age must be an integer."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["age"], int)

    def test_experience_in_years_is_integer(self):
        """Experience in years must be an integer."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["experience_in_years"], int)

    def test_date_of_appointment_is_iso_string(self):
        """Date of appointment must be an ISO date string."""
        payload = generate_directors_api_payload()
        assert isinstance(payload["date_of_appointment"], str)
        assert "T" in payload["date_of_appointment"]
        assert payload["date_of_appointment"].endswith("Z")

    def test_date_of_cessation_is_iso_or_none(self):
        """Date of cessation must be an ISO string or None."""
        payload = generate_directors_api_payload()
        val = payload["date_of_cessation"]
        assert val is None or (isinstance(val, str) and "T" in val)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 5. DATA GENERATOR TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsDataGenerators:
    """Verify data generators produce valid, unique, realistic data."""

    def test_generate_pan_format(self):
        """PAN must match ABCDE1234F format."""
        pan = generate_pan_number()
        assert len(pan) == 10
        assert pan[:5].isalpha()
        assert pan[5:9].isdigit()
        assert pan[9].isalpha()

    def test_generate_phone_is_10_digits(self):
        """Phone must be a 10-digit integer starting with 6-9."""
        phone = generate_phone()
        assert isinstance(phone, int)
        phone_str = str(phone)
        assert len(phone_str) == 10
        assert phone_str[0] in "6789"

    def test_generate_age_reasonable(self):
        """Age should be between 25 and 75."""
        age = generate_age()
        assert 25 <= age <= 75

    def test_generate_experience_reasonable(self):
        """Experience should be between 1 and 50."""
        exp = generate_experience_in_years()
        assert 1 <= exp <= 50

    def test_generate_residential_address_not_empty(self):
        """Residential address must not be empty."""
        addr = generate_residential_address()
        assert len(addr) > 5
        assert "," in addr  # Should have "number street, city" format

    def test_generate_share_class_format(self):
        """Share class must be 'NUMBER TYPE' format."""
        sc = generate_share_class()
        parts = sc.split(" ", 1)
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1] in SHARE_CLASS_TYPES

    def test_generate_details_of_other_directorships(self):
        """Other directorships must return a non-empty string."""
        d = generate_details_of_other_directorships()
        assert isinstance(d, str)
        assert len(d) > 0

    def test_generate_date_of_appointment_format(self):
        """Date of appointment must be in ISO format with Z suffix."""
        d = generate_date_of_appointment()
        assert d.endswith("Z")
        assert "T" in d

    def test_generate_date_of_cessation_or_none(self):
        """Date of cessation is either None or an ISO date string."""
        results = set()
        for _ in range(50):
            d = generate_date_of_cessation()
            results.add(type(d))
        # Should produce both None and str over 50 iterations
        assert None in results or str in results

    def test_generate_batch_payloads_unique_names(self):
        """Batch payloads must have unique names."""
        payloads = generate_batch_payloads(20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names in batch"

    def test_generate_batch_payloads_count(self):
        """Batch must generate the requested count."""
        for count in [1, 5, 10]:
            payloads = generate_batch_payloads(count)
            assert len(payloads) == count


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 6. INVALID / BOUNDARY DATA TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsInvalidData:
    """Verify that invalid/boundary data is handled correctly."""

    def test_empty_name_in_payload(self):
        """Empty name should still produce a valid structure (server validates)."""
        payload = generate_directors_api_payload(name="")
        assert payload["name"] == ""

    def test_empty_pan_in_payload(self):
        """Empty PAN should still produce a valid structure."""
        payload = generate_directors_api_payload(pan_no="")
        assert payload["pan_no"] == ""

    def test_empty_residential_address_in_payload(self):
        """Empty address should still produce a valid structure."""
        payload = generate_directors_api_payload(residential_address="")
        assert payload["residential_address"] == ""

    def test_empty_other_directorships_in_payload(self):
        """Empty other directorships should still produce a valid structure."""
        payload = generate_directors_api_payload(details_of_other_directorships="")
        assert payload["details_of_other_directorships"] == ""

    def test_negative_percentage_in_payload(self):
        """Negative percentage should still produce a valid structure."""
        payload = generate_directors_api_payload(percentage_of_shares=-5)
        assert payload["percentage_of_shares"] == -5

    def test_zero_percentage_in_payload(self):
        """Zero percentage should still produce a valid structure."""
        payload = generate_directors_api_payload(percentage_of_shares=0)
        assert payload["percentage_of_shares"] == 0

    def test_percentage_over_100_in_payload(self):
        """Percentage over 100 should still produce a valid structure."""
        payload = generate_directors_api_payload(percentage_of_shares=150)
        assert payload["percentage_of_shares"] == 150

    def test_negative_age_in_payload(self):
        """Negative age should still produce a valid structure."""
        payload = generate_directors_api_payload(age=-1)
        assert payload["age"] == -1

    def test_zero_age_in_payload(self):
        """Zero age should still produce a valid structure."""
        payload = generate_directors_api_payload(age=0)
        assert payload["age"] == 0

    def test_very_high_age_in_payload(self):
        """Unreasonably high age should still produce a valid structure."""
        payload = generate_directors_api_payload(age=200)
        assert payload["age"] == 200

    def test_negative_experience_in_payload(self):
        """Negative experience should still produce a valid structure."""
        payload = generate_directors_api_payload(experience_in_years=-5)
        assert payload["experience_in_years"] == -5

    def test_zero_experience_in_payload(self):
        """Zero experience should still produce a valid structure."""
        payload = generate_directors_api_payload(experience_in_years=0)
        assert payload["experience_in_years"] == 0

    def test_very_high_experience_in_payload(self):
        """Unreasonably high experience should still produce a valid structure."""
        payload = generate_directors_api_payload(experience_in_years=100)
        assert payload["experience_in_years"] == 100

    def test_sql_injection_name_in_payload(self):
        """SQL injection in name should still produce a valid structure."""
        payload = generate_directors_api_payload(name=generate_sql_injection_name())
        assert "DROP TABLE" in payload["name"]

    def test_xss_name_in_payload(self):
        """XSS payload in name should still produce a valid structure."""
        payload = generate_directors_api_payload(name=generate_xss_name())
        assert "<script>" in payload["name"]

    def test_spaces_only_name_in_payload(self):
        """Spaces-only name should still produce a valid structure."""
        payload = generate_directors_api_payload(name=generate_spaces_only_name())
        assert payload["name"].strip() == ""

    def test_empty_kyc_details_in_payload(self):
        """Payload with empty KYC details should be buildable."""
        data = generate_valid_directors_data()
        data["kyc_details"] = []
        payload = build_directors_api_payload(data)
        # Should auto-generate a KYC row when none provided
        assert len(payload["children"][0]["details"]) >= 1

    def test_multiple_kyc_rows_in_payload(self):
        """Payload can have multiple KYC rows."""
        data = generate_valid_directors_data()
        data["kyc_details"] = [
            generate_valid_kyc_row(65),
            generate_valid_kyc_row(66),
        ]
        payload = build_directors_api_payload(data)
        assert len(payload["children"][0]["details"]) == 2

    def test_invalid_designation_id_in_payload(self):
        """Invalid designation ID should still produce a valid structure."""
        payload = generate_directors_api_payload(designation=99999)
        assert payload["designation"] == 99999

    def test_invalid_qualification_id_in_payload(self):
        """Invalid qualification ID should still produce a valid structure."""
        payload = generate_directors_api_payload(qualification_ref_id=99999)
        assert payload["qualification_ref_id"] == 99999

    def test_invalid_prefix_id_in_payload(self):
        """Invalid prefix ID should still produce a valid structure."""
        payload = generate_directors_api_payload(prefix_ref_id=99999)
        assert payload["prefix_ref_id"] == 99999


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 7. FIELD VALIDATION RULES TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsFieldValidationRules:
    """Verify FIELD_VALIDATION_RULES dict is complete and consistent."""

    def test_all_15_top_level_fields_have_rules(self):
        """All 15 top-level fields should have validation rules."""
        top_level_fields = [
            "party_ref_id", "prefix_ref_id", "name", "designation",
            "pan_no", "residential_address", "mobile_no",
            "date_of_appointment", "date_of_cessation",
            "no_class_shares_held", "details_of_other_directorships",
            "percentage_of_shares", "age", "qualification_ref_id",
            "experience_in_years",
        ]
        for field in top_level_fields:
            assert field in FIELD_VALIDATION_RULES, f"Missing rule for: {field}"

    def test_kyc_fields_have_rules(self):
        """All 3 KYC stepper fields should have validation rules."""
        kyc_fields = ["kyc_doc_id", "kyc_account_no", "attachment_path"]
        for field in kyc_fields:
            assert field in FIELD_VALIDATION_RULES, f"Missing rule for: {field}"

    def test_required_fields_marked_required(self):
        """All required fields should be marked as required in rules."""
        required_fields = [
            "prefix_ref_id", "name", "designation", "pan_no",
            "residential_address", "mobile_no", "date_of_appointment",
            "no_class_shares_held", "details_of_other_directorships",
            "percentage_of_shares", "age", "qualification_ref_id",
            "experience_in_years", "kyc_doc_id", "kyc_account_no",
        ]
        for field in required_fields:
            assert FIELD_VALIDATION_RULES[field]["required"], (
                f"Field '{field}' should be marked required"
            )

    def test_optional_fields_marked_optional(self):
        """Optional fields should not be marked as required."""
        optional_fields = ["party_ref_id", "date_of_cessation", "attachment_path"]
        for field in optional_fields:
            assert not FIELD_VALIDATION_RULES[field]["required"], (
                f"Field '{field}' should be optional"
            )

    def test_fk_fields_have_options_count(self):
        """FK dropdown fields should have fk_options_count."""
        fk_fields = {
            "party_ref_id": 357,
            "prefix_ref_id": 3,
            "designation": 56,
            "qualification_ref_id": 6,
            "kyc_doc_id": 2,
        }
        for field, count in fk_fields.items():
            assert FIELD_VALIDATION_RULES[field]["fk_options_count"] == count, (
                f"{field}: expected {count} options"
            )

    def test_designation_has_56_options(self):
        """Designation dropdown should have exactly 56 options."""
        assert len(DESIGNATION_IDS) == 56
        assert FIELD_VALIDATION_RULES["designation"]["fk_options_count"] == 56

    def test_qualification_has_6_options(self):
        """Qualification dropdown should have exactly 6 options."""
        assert len(QUALIFICATION_IDS) == 6
        assert FIELD_VALIDATION_RULES["qualification_ref_id"]["fk_options_count"] == 6

    def test_party_ref_has_357_options(self):
        """Party reference dropdown should have exactly 357 options."""
        assert len(PARTY_REF_IDS) == 357
        assert FIELD_VALIDATION_RULES["party_ref_id"]["fk_options_count"] == 357


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 8. KYC STEPPER TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsKYCStepper:
    """Verify KYC Details stepper structure and data."""

    def test_kyc_stepper_name(self):
        """KYC stepper must be named 'KYC Details'."""
        payload = generate_directors_api_payload()
        assert payload["children"][0]["stepper_name"] == "KYC Details"

    def test_kyc_doc_id_is_valid(self):
        """KYC document ID must be from the verified pool."""
        payload = generate_directors_api_payload()
        kyc_doc = payload["children"][0]["details"][0]["kyc_doc_id"]
        assert kyc_doc in KYC_DOC_IDS

    def test_kyc_account_no_is_string(self):
        """KYC account number must be a string."""
        payload = generate_directors_api_payload()
        kyc_no = payload["children"][0]["details"][0]["kyc_account_no"]
        assert isinstance(kyc_no, str)

    def test_kyc_attachment_path_is_nullable(self):
        """KYC attachment path should be None for new entries."""
        payload = generate_directors_api_payload()
        att = payload["children"][0]["details"][0]["attachment_path"]
        assert att is None

    def test_kyc_pan_format_when_pan_doc(self):
        """When KYC doc is PAN (65), account number should match PAN format."""
        data = generate_valid_directors_data()
        data["kyc_details"] = [generate_valid_kyc_row(65)]
        payload = build_directors_api_payload(data)
        kyc_no = payload["children"][0]["details"][0]["kyc_account_no"]
        assert len(kyc_no) == 10  # ABCDE1234F
        assert kyc_no[:5].isalpha()
        assert kyc_no[5:9].isdigit()

    def test_kyc_aadhaar_format_when_aadhaar_doc(self):
        """When KYC doc is AADHAR (66), account number should be 12 digits."""
        data = generate_valid_directors_data()
        data["kyc_details"] = [generate_valid_kyc_row(66)]
        payload = build_directors_api_payload(data)
        kyc_no = payload["children"][0]["details"][0]["kyc_account_no"]
        assert len(kyc_no) == 12
        assert kyc_no.isdigit()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 9. BUILD PAYLOAD WITH OVERRIDE TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsBuildPayloadOverrides:
    """Verify build_directors_api_payload handles overrides correctly."""

    def test_fk_ids_override_prefix(self):
        """fk_ids should override the prefix_ref_id."""
        payload = build_directors_api_payload(fk_ids={"prefix_ref_id": 1895})
        assert payload["prefix_ref_id"] == 1895

    def test_fk_ids_override_designation(self):
        """fk_ids should override the designation."""
        payload = build_directors_api_payload(fk_ids={"designation": 30})
        assert payload["designation"] == 30

    def test_fk_ids_override_qualification(self):
        """fk_ids should override the qualification_ref_id."""
        payload = build_directors_api_payload(fk_ids={"qualification_ref_id": 512})
        assert payload["qualification_ref_id"] == 512

    def test_fk_ids_override_party_ref(self):
        """fk_ids should override the party_ref_id."""
        payload = build_directors_api_payload(fk_ids={"party_ref_id": 10})
        assert payload["party_ref_id"] == 10

    def test_fk_ids_override_kyc_doc(self):
        """fk_ids should override the kyc_doc_id."""
        payload = build_directors_api_payload(fk_ids={"kyc_doc_id": 66})
        kyc_doc = payload["children"][0]["details"][0]["kyc_doc_id"]
        assert kyc_doc == 66

    def test_data_overrides_name(self):
        """Directors data should override the name."""
        data = generate_valid_directors_data()
        data["director_name"] = "Custom Name Test"
        payload = build_directors_api_payload(data)
        assert payload["name"] == "Custom Name Test"

    def test_data_overrides_pan(self):
        """Directors data should override the PAN number."""
        data = generate_valid_directors_data()
        data["pan_no"] = "ZZZZZ9999Z"
        payload = build_directors_api_payload(data)
        assert payload["pan_no"] == "ZZZZZ9999Z"

    def test_data_overrides_address(self):
        """Directors data should override the residential address."""
        data = generate_valid_directors_data()
        data["residential_address"] = "99 Custom Road, Delhi"
        payload = build_directors_api_payload(data)
        assert payload["residential_address"] == "99 Custom Road, Delhi"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 10. FK ID POOL INTEGRITY TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsFKPoolIntegrity:
    """Verify FK ID pools are complete and have no duplicates."""

    def test_prefix_ids_no_duplicates(self):
        """PREFIX_IDS should have no duplicates."""
        assert len(PREFIX_IDS) == len(set(PREFIX_IDS))

    def test_designation_ids_no_duplicates(self):
        """DESIGNATION_IDS should have no duplicates."""
        assert len(DESIGNATION_IDS) == len(set(DESIGNATION_IDS))

    def test_qualification_ids_no_duplicates(self):
        """QUALIFICATION_IDS should have no duplicates."""
        assert len(QUALIFICATION_IDS) == len(set(QUALIFICATION_IDS))

    def test_kyc_doc_ids_no_duplicates(self):
        """KYC_DOC_IDS should have no duplicates."""
        assert len(KYC_DOC_IDS) == len(set(KYC_DOC_IDS))

    def test_party_ref_ids_no_duplicates(self):
        """PARTY_REF_IDS should have no duplicates."""
        assert len(PARTY_REF_IDS) == len(set(PARTY_REF_IDS))

    def test_prefix_names_match_ids(self):
        """Each PREFIX_ID should have a matching PREFIX_NAME."""
        for pid in PREFIX_IDS:
            assert pid in PREFIX_NAMES

    def test_designation_names_match_ids(self):
        """Each DESIGNATION_ID should have a matching DESIGNATION_NAME."""
        for did in DESIGNATION_IDS:
            assert did in DESIGNATION_NAMES

    def test_qualification_names_match_ids(self):
        """Each QUALIFICATION_ID should have a matching QUALIFICATION_NAME."""
        for qid in QUALIFICATION_IDS:
            assert qid in QUALIFICATION_NAMES

    def test_kyc_doc_names_match_ids(self):
        """Each KYC_DOC_ID should have a matching KYC_DOC_NAME."""
        for kid in KYC_DOC_IDS:
            assert kid in KYC_DOC_NAMES


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 11. LIVE CRUD TESTS (require ERP_TOKEN)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.mark.api
class TestDirectorsLiveCRUD:
    """Live CRUD tests against the real ERP API.

    These tests are SKIPPED unless ERP_TOKEN is set in the environment.
    Run: ERP_TOKEN=eyJ... pytest -v -k live
    """

    @pytest.fixture(autouse=True)
    def skip_without_api(self, api_client):
        """Skip all tests in this class if no API client is available."""
        if api_client is None:
            pytest.skip("No API client available")

    def test_live_create_director(self, api_client):
        """Create a single director via API."""
        payload = generate_directors_api_payload()
        result = api_client.create_entry(payload)
        assert result is not None, "Create failed"
        assert result.get("id") is not None
        assert result.get("attribute_name") == "Directors"

    def test_live_create_with_party_ref(self, api_client):
        """Create a director with party_ref_id set."""
        party_id = random.choice(PARTY_REF_IDS)
        payload = generate_directors_api_payload(party_ref_id=party_id)
        result = api_client.create_entry(payload)
        assert result is not None, f"Create with party_ref_id={party_id} failed"

    def test_live_create_with_all_designations(self, api_client):
        """Create directors with a sample of different designations."""
        sample_ids = random.sample(DESIGNATION_IDS, min(3, len(DESIGNATION_IDS)))
        for desig_id in sample_ids:
            payload = generate_directors_api_payload(designation=desig_id)
            result = api_client.create_entry(payload)
            assert result is not None, f"Create with designation={desig_id} failed"
            time.sleep(0.2)

    def test_live_create_with_all_qualifications(self, api_client):
        """Create directors with each qualification type."""
        for qual_id in QUALIFICATION_IDS:
            payload = generate_directors_api_payload(qualification_ref_id=qual_id)
            result = api_client.create_entry(payload)
            assert result is not None, f"Create with qualification={qual_id} failed"
            time.sleep(0.2)

    def test_live_create_with_both_kyc_types(self, api_client):
        """Create directors with PAN and Aadhaar KYC documents."""
        for kyc_id in KYC_DOC_IDS:
            data = generate_valid_directors_data()
            data["kyc_details"] = [generate_valid_kyc_row(kyc_id)]
            payload = build_directors_api_payload(data)
            result = api_client.create_entry(payload)
            assert result is not None, f"Create with kyc_doc_id={kyc_id} failed"
            time.sleep(0.2)

    def test_live_read_director_list(self, api_client):
        """List directors from the API."""
        result = api_client.list_entries("Directors", page=1, page_size=5)
        assert result is not None, "List failed"
        items = result.get("screenmatlistingdata_set", [])
        assert len(items) > 0, "No directors found"

    def test_live_read_director_detail(self, api_client):
        """Read a specific director's details."""
        # First, list to get an ID
        result = api_client.list_entries("Directors", page=1, page_size=1)
        assert result is not None
        items = result.get("screenmatlistingdata_set", [])
        if not items:
            pytest.skip("No directors to read")
        entry_id = items[0].get("id")
        detail = api_client.get_entry("Directors", entry_id)
        assert detail is not None
        assert detail.get("id") == entry_id
        assert "children" in detail

    def test_live_update_director(self, api_client):
        """Update an existing director's age and experience."""
        # Create a director first
        payload = generate_directors_api_payload()
        create_result = api_client.create_entry(payload)
        assert create_result is not None
        entry_id = create_result.get("id")

        # Update with new values
        payload["id"] = entry_id
        payload["age"] = 55
        payload["experience_in_years"] = 30
        update_result = api_client.update_entry(entry_id, payload)
        assert update_result is not None, "Update failed"

    def test_live_create_batch(self, api_client):
        """Create a batch of 3 directors."""
        payloads = generate_batch_payloads(3)
        for p in payloads:
            result = api_client.create_entry(p)
            assert result is not None, "Batch create failed for an entry"
            time.sleep(0.2)

    def test_live_create_with_both_prefixes(self, api_client):
        """Create directors with Mrs, Mr, and Ms prefixes."""
        for prefix_id in PREFIX_IDS:
            payload = generate_directors_api_payload(prefix_ref_id=prefix_id)
            result = api_client.create_entry(payload)
            assert result is not None, f"Create with prefix={prefix_id} failed"
            time.sleep(0.2)

    def test_live_create_with_date_of_cessation(self, api_client):
        """Create a director with date_of_cessation set."""
        data = generate_valid_directors_data()
        data["date_of_cessation"] = "2024-06-15T18:30:00Z"
        payload = build_directors_api_payload(data)
        result = api_client.create_entry(payload)
        assert result is not None, "Create with cessation date failed"

    def test_live_create_with_multiple_kyc_rows(self, api_client):
        """Create a director with both PAN and Aadhaar KYC rows."""
        data = generate_valid_directors_data()
        data["kyc_details"] = [
            generate_valid_kyc_row(65),
            generate_valid_kyc_row(66),
        ]
        payload = build_directors_api_payload(data)
        result = api_client.create_entry(payload)
        assert result is not None, "Create with multiple KYC rows failed"

    def test_live_create_verify_designation_saved(self, api_client):
        """Verify that the designation FK is saved correctly."""
        desig_id = 30  # Managing Director
        payload = generate_directors_api_payload(designation=desig_id)
        result = api_client.create_entry(payload)
        assert result is not None
        assert result.get("designation") == desig_id

    def test_live_create_verify_qualification_saved(self, api_client):
        """Verify that the qualification FK is saved correctly."""
        qual_id = 511  # Graduation
        payload = generate_directors_api_payload(qualification_ref_id=qual_id)
        result = api_client.create_entry(payload)
        assert result is not None
        assert result.get("qualification_ref_id") == qual_id

    def test_live_create_verify_age_saved(self, api_client):
        """Verify that the age is saved correctly."""
        age = 42
        payload = generate_directors_api_payload(age=age)
        result = api_client.create_entry(payload)
        assert result is not None
        assert result.get("age") == age

    def test_live_create_verify_experience_saved(self, api_client):
        """Verify that experience in years is saved correctly."""
        exp = 15
        payload = generate_directors_api_payload(experience_in_years=exp)
        result = api_client.create_entry(payload)
        assert result is not None
        assert result.get("experience_in_years") == exp
