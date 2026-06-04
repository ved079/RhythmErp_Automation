"""
test_member_payload.py — Fast API payload structure tests.
No browser needed. All tests validate in-memory payload generation
and live API CRUD operations.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.member.data.member_data import (
    generate_member_api_payload,
    build_member_api_payload,
    generate_valid_member_data,
    generate_valid_kyc_row,
    generate_batch_payloads,
    generate_member_name,
    generate_member_address,
    generate_pan_number,
    generate_phone,
    generate_folio_number,
    generate_distinctive_number,
    generate_share_class,
    generate_amount_paid,
    generate_percentage_of_shares,
    generate_string_255,
    generate_string_256,
    generate_invalid_name_numbers,
    generate_invalid_name_special_chars,
    generate_invalid_phone_starts_with_5,
    generate_invalid_phone_too_short,
    generate_invalid_phone_too_long,
    generate_invalid_pan_format,
    generate_negative_amount,
    generate_zero_percentage,
    generate_negative_percentage,
    generate_percentage_over_100,
    generate_sql_injection_name,
    generate_xss_name,
    generate_spaces_only_name,
    generate_minimal_member_data,
    generate_empty_member_data,
    PREFIX_IDS,
    PREFIX_NAMES,
    KYC_DOC_IDS,
    KYC_DOC_NAMES,
    PARTY_REF_IDS,
    DEFAULT_MEMBER_FK_IDS,
    FIELD_VALIDATION_RULES,
)


# ═══════════════════════════════════════════════════════════════════
# PAYLOAD STRUCTURE TESTS
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.api
class TestMemberPayloadStructure:
    """Verify that generated API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, details, children."""
        payload = generate_member_api_payload()
        assert "id" in payload
        assert payload["id"] == ""
        assert payload["attribute_name"] == "Member"
        assert "details" in payload
        assert payload["details"] == []
        assert "children" in payload

    def test_payload_has_1_child_stepper(self):
        """Payload must have 1 child stepper: KYC Details."""
        payload = generate_member_api_payload()
        children = payload["children"]
        assert len(children) >= 1
        assert children[0]["stepper_name"] == "KYC Details"

    def test_payload_kyc_details_in_details_array(self):
        """KYC rows must be in children[0].details[] array."""
        payload = generate_member_api_payload()
        kyc_stepper = payload["children"][0]
        assert len(kyc_stepper["details"]) >= 1
        kyc_row = kyc_stepper["details"][0]
        assert "kyc_doc_id" in kyc_row
        assert "kyc_account_no" in kyc_row
        assert "attachment_path" in kyc_row

    def test_payload_kyc_row_has_empty_id(self):
        """Each new KYC row must have id="" for creation."""
        payload = generate_member_api_payload()
        for kyc_row in payload["children"][0]["details"]:
            assert kyc_row["id"] == ""

    def test_payload_all_root_fields_present(self):
        """Payload must have all 15 root-level member fields."""
        payload = generate_member_api_payload()
        expected_root_fields = [
            "party_ref_id", "prefix_ref_id", "name", "member_address",
            "pan_no", "foli_number", "registration_date",
            "no_class_shares_held", "distintive_number",
            "amount_paid_on_shares", "date_of_allotment",
            "date_of_cessation", "percentage_of_shares",
            "mobile_no", "is_member_director",
        ]
        for field in expected_root_fields:
            assert field in payload, f"Missing root field: {field}"

    def test_payload_attribute_name_is_member(self):
        """attribute_name must be 'Member'."""
        payload = generate_member_api_payload()
        assert payload["attribute_name"] == "Member"

    def test_payload_member_name_is_string(self):
        """Member name should be a non-empty string."""
        payload = generate_member_api_payload()
        assert isinstance(payload["name"], str)
        assert len(payload["name"]) > 0

    def test_payload_phone_is_integer(self):
        """Phone (mobile_no) must be an integer."""
        payload = generate_member_api_payload()
        assert isinstance(payload["mobile_no"], int)

    def test_payload_amount_paid_is_integer(self):
        """Amount paid on shares must be an integer."""
        payload = generate_member_api_payload()
        assert isinstance(payload["amount_paid_on_shares"], int)

    def test_payload_percentage_is_integer(self):
        """Percentage of shares must be an integer."""
        payload = generate_member_api_payload()
        assert isinstance(payload["percentage_of_shares"], int)

    def test_payload_pan_format(self):
        """PAN must match ABCDE1234F format (5 letters + 4 digits + 1 letter)."""
        payload = generate_member_api_payload()
        pan = payload.get("pan_no", "")
        if pan and len(pan) == 10:
            assert pan[:5].isalpha()
            assert pan[5:9].isdigit()
            assert pan[9].isalpha()

    def test_payload_prefix_in_valid_pool(self):
        """Prefix FK ID must be from the valid pool."""
        payload = generate_member_api_payload()
        if payload.get("prefix_ref_id"):
            assert payload["prefix_ref_id"] in PREFIX_IDS

    def test_payload_kyc_doc_in_valid_pool(self):
        """KYC document FK ID must be from the valid pool."""
        payload = generate_member_api_payload()
        kyc_row = payload["children"][0]["details"][0]
        if kyc_row.get("kyc_doc_id"):
            assert kyc_row["kyc_doc_id"] in KYC_DOC_IDS

    def test_payload_party_ref_in_valid_pool(self):
        """Party reference FK ID, if set, must be from the valid pool."""
        payload = generate_member_api_payload()
        if payload.get("party_ref_id"):
            assert payload["party_ref_id"] in PARTY_REF_IDS

    def test_payload_is_member_director_is_boolean(self):
        """Is Member Director must be a boolean or None."""
        payload = generate_member_api_payload()
        val = payload.get("is_member_director")
        assert val is None or isinstance(val, bool)

    def test_payload_date_of_cessation_is_optional(self):
        """Date of cessation should be null when not set."""
        payload = generate_member_api_payload()
        assert payload.get("date_of_cessation") is None


# ═══════════════════════════════════════════════════════════════════
# BUILD FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.api
class TestMemberBuildPayload:
    """Verify build_member_api_payload with explicit data and FK overrides."""

    def test_build_with_explicit_data(self):
        """build_member_api_payload with explicit data should use it."""
        member_data = generate_valid_member_data()
        member_data["member_name"] = "Test Build Member Co"
        payload = build_member_api_payload(member_data)
        assert payload["name"] == "Test Build Member Co"

    def test_build_with_fk_overrides(self):
        """build_member_api_payload with fk_ids should override defaults."""
        member_data = generate_valid_member_data()
        payload = build_member_api_payload(
            member_data,
            fk_ids={"prefix_ref_id": 1895}
        )
        assert payload["prefix_ref_id"] == 1895

    def test_build_with_party_ref_override(self):
        """build_member_api_payload with party_ref_id override."""
        payload = build_member_api_payload(
            fk_ids={"party_ref_id": 10}
        )
        assert payload["party_ref_id"] == 10

    def test_build_without_kyc_details(self):
        """build_member_api_payload should add default KYC row if none provided."""
        member_data = generate_valid_member_data()
        member_data["kyc_details"] = []
        payload = build_member_api_payload(member_data)
        # Should have auto-generated a KYC row
        assert len(payload["children"][0]["details"]) >= 1

    def test_build_with_multiple_kyc_rows(self):
        """build_member_api_payload should support multiple KYC rows."""
        member_data = generate_valid_member_data()
        member_data["kyc_details"] = [
            generate_valid_kyc_row(65),  # PAN
            generate_valid_kyc_row(66),  # AADHAR
        ]
        payload = build_member_api_payload(member_data)
        assert len(payload["children"][0]["details"]) == 2

    def test_build_minimal_data(self):
        """build_member_api_payload with minimal data should still produce valid payload."""
        member_data = generate_minimal_member_data()
        payload = build_member_api_payload(member_data)
        assert payload["attribute_name"] == "Member"
        assert payload["id"] == ""

    def test_build_empty_data(self):
        """build_member_api_payload with empty data should still produce valid structure."""
        member_data = generate_empty_member_data()
        payload = build_member_api_payload(member_data)
        assert payload["attribute_name"] == "Member"
        # Name may be auto-generated if empty string provided
        assert "name" in payload


# ═══════════════════════════════════════════════════════════════════
# KYC DETAILS TESTS
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.api
class TestMemberKYCDetails:
    """Verify KYC Details stepper structure and data."""

    def test_kyc_pan_document(self):
        """KYC with PAN document (id=65) should have valid PAN number."""
        kyc_row = generate_valid_kyc_row(65)
        assert kyc_row["kyc_doc_id"] == 65
        assert len(kyc_row["kyc_account_no"]) == 10

    def test_kyc_aadhar_document(self):
        """KYC with AADHAR document (id=66) should have 12-digit number."""
        kyc_row = generate_valid_kyc_row(66)
        assert kyc_row["kyc_doc_id"] == 66
        assert len(kyc_row["kyc_account_no"]) == 12

    def test_kyc_attachment_is_none_by_default(self):
        """KYC attachment path should be None by default (file uploads are separate)."""
        kyc_row = generate_valid_kyc_row()
        assert kyc_row["attachment_path"] is None

    def test_payload_with_no_kyc_children(self):
        """Payload without KYC children (empty) should still have correct structure."""
        payload = generate_member_api_payload(children=[])
        # After override, children should be empty
        assert payload["children"] == []


# ═══════════════════════════════════════════════════════════════════
# BOUNDARY & EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.api
class TestMemberBoundaryValues:
    """Verify boundary values and edge cases for Member fields."""

    def test_name_at_max_length_255(self):
        """Member name at exactly 255 characters should be valid."""
        payload = generate_member_api_payload(name=generate_string_255())
        assert len(payload["name"]) == 255

    def test_name_exceeds_max_length_256(self):
        """Member name at 256 characters exceeds max_length but API accepts it."""
        payload = generate_member_api_payload(name=generate_string_256())
        assert len(payload["name"]) == 256
        # Note: API does not enforce max_length server-side

    def test_pan_at_10_chars(self):
        """PAN at exactly 10 characters (ABCDE1234F format)."""
        pan = generate_pan_number()
        assert len(pan) == 10

    def test_invalid_pan_format(self):
        """Invalid PAN format should still generate valid payload structure."""
        payload = generate_member_api_payload(pan_no=generate_invalid_pan_format())
        assert payload["pan_no"] == "INVALIDPAN"
        # Note: API does not validate PAN format server-side

    def test_negative_amount_paid(self):
        """Negative amount paid on shares should still create valid payload."""
        payload = generate_member_api_payload(amount_paid_on_shares=generate_negative_amount())
        assert payload["amount_paid_on_shares"] < 0
        # Note: API accepts negative values (no server-side validation)

    def test_zero_percentage_shares(self):
        """Zero percentage of shares should generate valid payload."""
        payload = generate_member_api_payload(percentage_of_shares=generate_zero_percentage())
        assert payload["percentage_of_shares"] == 0

    def test_negative_percentage_shares(self):
        """Negative percentage of shares should generate valid payload."""
        payload = generate_member_api_payload(percentage_of_shares=generate_negative_percentage())
        assert payload["percentage_of_shares"] < 0
        # Note: API accepts negative values (no server-side validation)

    def test_percentage_over_100(self):
        """Percentage over 100 should generate valid payload."""
        payload = generate_member_api_payload(percentage_of_shares=generate_percentage_over_100())
        assert payload["percentage_of_shares"] > 100
        # Note: API accepts percentages > 100 (no server-side validation)

    def test_empty_name(self):
        """Empty name should still produce structurally valid payload."""
        payload = generate_member_api_payload(name="")
        assert payload["name"] == ""

    def test_null_party_ref(self):
        """Null party_ref_id should be valid (manual entry mode)."""
        payload = generate_member_api_payload(party_ref_id=None)
        assert payload["party_ref_id"] is None

    def test_null_date_of_cessation(self):
        """Null date_of_cessation should be valid (optional field)."""
        payload = generate_member_api_payload(date_of_cessation=None)
        assert payload["date_of_cessation"] is None

    def test_is_member_director_true(self):
        """is_member_director = true should be valid."""
        payload = generate_member_api_payload(is_member_director=True)
        assert payload["is_member_director"] is True

    def test_is_member_director_false(self):
        """is_member_director = false should be valid."""
        payload = generate_member_api_payload(is_member_director=False)
        assert payload["is_member_director"] is False

    def test_is_member_director_none(self):
        """is_member_director = None should be valid (optional toggle)."""
        payload = generate_member_api_payload(is_member_director=None)
        assert payload["is_member_director"] is None


# ═══════════════════════════════════════════════════════════════════
# SECURITY / INJECTION TESTS
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.api
class TestMemberSecurity:
    """Verify payload handling of injection and malicious inputs."""

    def test_sql_injection_name(self):
        """SQL injection in name should be included as-is (no server-side sanitization expected)."""
        payload = generate_member_api_payload(name=generate_sql_injection_name())
        assert "DROP TABLE" in payload["name"]

    def test_xss_name(self):
        """XSS payload in name should be included as-is (no server-side sanitization expected)."""
        payload = generate_member_api_payload(name=generate_xss_name())
        assert "<script>" in payload["name"]

    def test_spaces_only_name(self):
        """Spaces-only name should be included in payload."""
        payload = generate_member_api_payload(name=generate_spaces_only_name())
        assert payload["name"].strip() == ""


# ═══════════════════════════════════════════════════════════════════
# BATCH GENERATION TESTS
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.api
class TestMemberBatchGeneration:
    """Verify batch generation produces unique, valid payloads."""

    def test_batch_generates_correct_count(self):
        payloads = generate_batch_payloads(5)
        assert len(payloads) == 5

    def test_batch_names_are_unique(self):
        payloads = generate_batch_payloads(20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"

    def test_batch_pans_are_unique(self):
        payloads = generate_batch_payloads(20)
        pans = [p.get("pan_no", "") for p in payloads if p.get("pan_no")]
        assert len(pans) == len(set(pans)), "Duplicate PANs found in batch"

    def test_batch_phones_are_unique(self):
        payloads = generate_batch_payloads(20)
        phones = [p.get("mobile_no") for p in payloads if p.get("mobile_no")]
        assert len(phones) == len(set(phones)), "Duplicate phones found in batch"

    def test_batch_folio_numbers_are_unique(self):
        payloads = generate_batch_payloads(20)
        folios = [p.get("foli_number", "") for p in payloads if p.get("foli_number")]
        assert len(folios) == len(set(folios)), "Duplicate folio numbers found in batch"


# ═══════════════════════════════════════════════════════════════════
# LIVE API CRUD TESTS (requires ERP_TOKEN)
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.api
class TestMemberLiveCRUD:
    """Live API CRUD tests — requires valid ERP_TOKEN env var.

    These tests create, read, and verify entries against the live ERP.
    Skipped gracefully if no token is available.
    """

    def test_create_member_all_fields(self, api_client):
        """Create a member with all fields populated via API."""
        payload = generate_member_api_payload()
        result = api_client.create_entry(payload)
        assert result is not None, "Create entry returned None"
        assert result.get("id"), "Created entry has no ID"
        assert result.get("name") == payload["name"]
        # Verify key fields in response
        assert result.get("pan_no") == payload["pan_no"]
        assert result.get("prefix_ref_id") == payload["prefix_ref_id"]
        assert result.get("is_member_director") == payload["is_member_director"]

    def test_create_member_with_party_ref(self, api_client):
        """Create a member with party_ref_id set (auto-patch flow)."""
        payload = generate_member_api_payload(party_ref_id=10)
        result = api_client.create_entry(payload)
        assert result is not None, "Create with party_ref returned None"
        assert result.get("id"), "Created entry has no ID"
        # party_ref_id should be preserved
        assert result.get("party_ref_id") == 10

    def test_create_member_without_party_ref(self, api_client):
        """Create a member without party_ref_id (manual entry)."""
        payload = generate_member_api_payload(party_ref_id=None)
        result = api_client.create_entry(payload)
        assert result is not None
        assert result.get("id")
        assert result.get("party_ref_id") is None

    def test_create_member_with_kyc(self, api_client):
        """Create a member with KYC Details (both PAN and AADHAR)."""
        member_data = generate_valid_member_data()
        member_data["kyc_details"] = [
            generate_valid_kyc_row(65),  # PAN
            generate_valid_kyc_row(66),  # AADHAR
        ]
        payload = build_member_api_payload(member_data)
        result = api_client.create_entry(payload)
        assert result is not None

    def test_create_member_without_kyc(self, api_client):
        """Create a member without KYC Details (empty children)."""
        payload = generate_member_api_payload(children=[])
        result = api_client.create_entry(payload)
        assert result is not None

    def test_read_member_detail(self, api_client):
        """Read a member entry via detail endpoint and verify structure."""
        # First create one
        payload = generate_member_api_payload()
        created = api_client.create_entry(payload)
        assert created is not None
        entry_id = created.get("id")

        # Then read it back
        detail = api_client.get_entry("Member", entry_id)
        assert detail is not None
        assert detail.get("id") == entry_id
        assert detail.get("attribute_name") == "Member"
        # Should have children with KYC stepper
        assert "children" in detail

    def test_list_members(self, api_client):
        """List member entries and verify response structure."""
        result = api_client.list_entries("Member", page=1, page_size=5)
        assert result is not None
        assert "screenmatlistingdata_set" in result
        assert "screen_name" in result
        assert result["screen_name"] == "Member"

    def test_create_member_with_each_prefix(self, api_client):
        """Create a member with each prefix option (Mrs, Mr, Ms)."""
        for prefix_id in PREFIX_IDS:
            payload = generate_member_api_payload(prefix_ref_id=prefix_id)
            result = api_client.create_entry(payload)
            assert result is not None, f"Failed with prefix_ref_id={prefix_id}"
            assert result.get("prefix_ref_id") == prefix_id

    def test_create_member_with_each_kyc_doc(self, api_client):
        """Create a member with each KYC document type (PAN, AADHAR)."""
        for kyc_id in KYC_DOC_IDS:
            member_data = generate_valid_member_data()
            member_data["kyc_details"] = [generate_valid_kyc_row(kyc_id)]
            payload = build_member_api_payload(member_data)
            result = api_client.create_entry(payload)
            assert result is not None, f"Failed with kyc_doc_id={kyc_id}"

    def test_create_member_is_director_true(self, api_client):
        """Create a member who is also a director."""
        payload = generate_member_api_payload(is_member_director=True)
        result = api_client.create_entry(payload)
        assert result is not None
        assert result.get("is_member_director") is True

    def test_create_member_is_director_false(self, api_client):
        """Create a member who is not a director."""
        payload = generate_member_api_payload(is_member_director=False)
        result = api_client.create_entry(payload)
        assert result is not None
        assert result.get("is_member_director") is False

    def test_create_member_empty_payload_accepted(self, api_client):
        """Verify API accepts empty payload (no server-side required validation)."""
        payload = {"id": "", "attribute_name": "Member"}
        result = api_client.create_entry(payload)
        # The ERP accepts empty payloads — this documents the behavior
        assert result is not None, "Empty payload was rejected"
        assert result.get("id"), "Empty payload entry has no ID"

    def test_create_member_duplicate_pan_rejected(self, api_client):
        """Verify API rejects duplicate PAN numbers (server enforces uniqueness)."""
        pan = generate_pan_number()
        # Create first member with this PAN
        payload1 = generate_member_api_payload(pan_no=pan)
        result1 = api_client.create_entry(payload1)
        assert result1 is not None

        # Create second member with same PAN — should be rejected
        payload2 = generate_member_api_payload(pan_no=pan)
        result2 = api_client.create_entry(payload2)
        assert result2 is None, "Duplicate PAN was accepted (expected: rejected)"

    def test_create_member_distinctive_number_must_be_integer(self, api_client):
        """Verify API rejects string distinctive numbers like 'DN-001'."""
        payload = generate_member_api_payload(distintive_number="DN-001")
        result = api_client.create_entry(payload)
        # Server rejects non-integer distinctive numbers
        assert result is None, "String distinctive number was accepted (expected: rejected)"

    def test_create_member_short_phone_accepted(self, api_client):
        """Verify API accepts short phone numbers (no server-side length validation)."""
        payload = generate_member_api_payload(mobile_no=123)
        result = api_client.create_entry(payload)
        # Documents that the API does not validate phone length
        assert result is not None, "Short phone number was rejected"
