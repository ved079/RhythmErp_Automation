"""
test_bank_payload.py — Fast API payload structure tests for Bank.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.bank.data.bank_data import (
    build_bank_api_payload,
    generate_bank_api_payloads,
    generate_batch_payloads,
    ACCOUNT_TYPE_IDS,
    ACCOUNT_REF_IDS,
    DEFAULT_BANK_FK_IDS,
    FIELD_VALIDATION_RULES,
)


@pytest.mark.api
class TestBankAPIPayload:
    """Verify that generated Bank API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, and all 14 Bank fields."""
        payloads = generate_bank_api_payloads(count=1)
        payload = payloads[0]
        required_keys = {
            "id", "attribute_name", "bank_name", "bank_code",
            "branch_name", "branch_code", "account_number",
            "account_type", "swift_number", "iban_number",
            "ifsc_code", "cash_credit_limit", "bank_address",
            "account_ref_id", "is_default_bank", "status",
        }
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_payload_is_flat_no_children(self):
        """Bank is a flat screen — payload must NOT have children or details."""
        payloads = generate_bank_api_payloads(count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name_is_bank(self):
        """attribute_name must be exactly 'Bank'."""
        payloads = generate_bank_api_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Bank"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_bank_api_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_payload_bank_name_is_string(self):
        """bank_name must be a non-empty string."""
        payloads = generate_bank_api_payloads(count=1)
        assert isinstance(payloads[0]["bank_name"], str)
        assert len(payloads[0]["bank_name"]) > 0

    def test_payload_bank_code_is_string(self):
        """bank_code must be a non-empty string."""
        payloads = generate_bank_api_payloads(count=1)
        assert isinstance(payloads[0]["bank_code"], str)
        assert len(payloads[0]["bank_code"]) > 0

    def test_payload_branch_name_is_string(self):
        """branch_name must be a non-empty string."""
        payloads = generate_bank_api_payloads(count=1)
        assert isinstance(payloads[0]["branch_name"], str)
        assert len(payloads[0]["branch_name"]) > 0

    def test_payload_account_number_is_string(self):
        """account_number must be a string of digits."""
        payloads = generate_bank_api_payloads(count=1)
        assert isinstance(payloads[0]["account_number"], str)
        assert payloads[0]["account_number"].isdigit()

    def test_payload_ifsc_code_is_11_chars(self):
        """ifsc_code must be exactly 11 characters (standard IFSC format)."""
        payloads = generate_bank_api_payloads(count=1)
        assert len(payloads[0]["ifsc_code"]) == 11

    def test_payload_account_type_is_integer(self):
        """account_type must be an integer FK ID."""
        payloads = generate_bank_api_payloads(count=1)
        assert isinstance(payloads[0]["account_type"], int)

    def test_payload_account_ref_id_is_integer(self):
        """account_ref_id must be an integer FK ID."""
        payloads = generate_bank_api_payloads(count=1)
        assert isinstance(payloads[0]["account_ref_id"], int)

    def test_payload_account_type_in_valid_pool(self):
        """account_type value must be from ACCOUNT_TYPE_IDS."""
        payloads = generate_bank_api_payloads(count=5)
        valid_ids = set(ACCOUNT_TYPE_IDS.values())
        for p in payloads:
            assert p["account_type"] in valid_ids, \
                f"account_type {p['account_type']} not in ACCOUNT_TYPE_IDS"

    def test_payload_account_ref_id_in_valid_pool(self):
        """account_ref_id value must be from ACCOUNT_REF_IDS."""
        payloads = generate_bank_api_payloads(count=5)
        valid_ids = set(ACCOUNT_REF_IDS.values())
        for p in payloads:
            assert p["account_ref_id"] in valid_ids, \
                f"account_ref_id {p['account_ref_id']} not in ACCOUNT_REF_IDS"

    def test_payload_status_is_boolean(self):
        """status must be a boolean (True=Active, False=Inactive)."""
        payloads = generate_bank_api_payloads(count=1)
        assert isinstance(payloads[0]["status"], bool)

    def test_payload_is_default_bank_is_boolean(self):
        """is_default_bank must be a boolean."""
        payloads = generate_bank_api_payloads(count=1)
        assert isinstance(payloads[0]["is_default_bank"], bool)

    def test_payload_status_default_is_true(self):
        """Default status should be True (Active)."""
        payloads = generate_bank_api_payloads(count=1)
        assert payloads[0]["status"] is True

    def test_payload_cash_credit_limit_types(self):
        """cash_credit_limit must be numeric (int/float) or None."""
        payloads = generate_bank_api_payloads(count=10)
        for p in payloads:
            assert p["cash_credit_limit"] is None or isinstance(p["cash_credit_limit"], (int, float))

    def test_build_with_explicit_values(self):
        """build_bank_api_payload with explicit values should use them."""
        payload = build_bank_api_payload(
            bank_name="Test Bank",
            bank_code="TSTB",
            branch_name="Main Branch",
            branch_code="BR001",
            account_number="123456789012",
            account_type_id=1849,
            swift_number="TSTBINMM",
            iban_number="",
            ifsc_code="TSTB0000001",
            cash_credit_limit=500000,
            bank_address="123 Bank Street",
            account_ref_id=1005,
            is_default_bank=False,
            status=True,
        )
        assert payload["bank_name"] == "Test Bank"
        assert payload["account_type"] == 1849
        assert payload["account_ref_id"] == 1005
        assert payload["cash_credit_limit"] == 500000

    def test_build_without_optional_fields(self):
        """build_bank_api_payload without optional fields should work."""
        payload = build_bank_api_payload(
            bank_name="Minimal Bank",
            bank_code="MINB",
            branch_name="Branch1",
            branch_code="BR001",
            account_number="999999999999",
            account_type_id=1850,
            ifsc_code="MINB0000001",
            cash_credit_limit=None,
            bank_address="Somewhere",
        )
        assert payload["swift_number"] == ""
        assert payload["iban_number"] == ""
        assert payload["cash_credit_limit"] is None
        # account_ref_id should not be in payload when not provided
        assert "account_ref_id" not in payload

    def test_payload_swift_format(self):
        """swift_number should be uppercase alphanumeric when provided."""
        payloads = generate_bank_api_payloads(count=5)
        for p in payloads:
            swift = p["swift_number"]
            if swift:  # optional, may be empty
                assert swift.isupper() or swift.replace(" ", "").isupper()
                assert swift.isalnum(), f"SWIFT should be alphanumeric, got: {swift}"


@pytest.mark.api
class TestBankBatchGeneration:
    """Verify batch payload generation for Bank."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='Bank'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Bank"

    def test_batch_all_account_types_valid(self):
        """All account_type values in batch must be valid."""
        payloads = generate_batch_payloads(count=10)
        valid_ids = set(ACCOUNT_TYPE_IDS.values())
        for p in payloads:
            assert p["account_type"] in valid_ids

    def test_batch_all_account_ref_ids_valid(self):
        """All account_ref_id values in batch must be valid."""
        payloads = generate_batch_payloads(count=10)
        valid_ids = set(ACCOUNT_REF_IDS.values())
        for p in payloads:
            assert p["account_ref_id"] in valid_ids

    def test_batch_all_are_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_batch_alternates_account_types(self):
        """Batch should alternate between Current and Saving account types."""
        payloads = generate_batch_payloads(count=4)
        current_id = ACCOUNT_TYPE_IDS["Current"]
        saving_id = ACCOUNT_TYPE_IDS["Saving"]
        for i, p in enumerate(payloads):
            expected = current_id if i % 2 == 0 else saving_id
            assert p["account_type"] == expected

    def test_batch_first_is_default_bank(self):
        """First bank in batch should be marked as default."""
        payloads = generate_batch_payloads(count=5)
        assert payloads[0]["is_default_bank"] is True
        for p in payloads[1:]:
            assert p["is_default_bank"] is False

    def test_batch_account_numbers_are_unique(self):
        """All account numbers in a batch should be unique."""
        payloads = generate_batch_payloads(count=10)
        acct_nos = [p["account_number"] for p in payloads]
        assert len(acct_nos) == len(set(acct_nos)), "Duplicate account numbers in batch"

    def test_batch_all_statuses_are_true(self):
        """Every payload in batch must have status=True."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["status"] is True
