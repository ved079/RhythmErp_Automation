"""
test_uom_payload.py — Fast API payload structure tests for UOM.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.uom.data.uom_data import (
    build_uom_api_payload,
    generate_uom_api_payload,
    generate_uom_data,
    generate_batch_payloads,
    STATUS_OPTIONS,
)


@pytest.mark.api
class TestUOMAPIPayload:
    """Verify that generated UOM API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, uom_code, uom_description, status."""
        payload = generate_uom_api_payload()
        assert "id" in payload
        assert payload["id"] == ""
        assert "attribute_name" in payload
        assert payload["attribute_name"] == "UOM"
        assert "uom_code" in payload
        assert "uom_description" in payload
        assert "status" in payload

    def test_payload_is_flat_no_children(self):
        """UOM is a flat screen — payload must NOT have children or details."""
        payload = generate_uom_api_payload()
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name_is_uom(self):
        """attribute_name must be exactly 'UOM'."""
        payload = generate_uom_api_payload()
        assert payload["attribute_name"] == "UOM"

    def test_payload_uom_code_is_string(self):
        """uom_code must be a non-empty string."""
        payload = generate_uom_api_payload()
        assert isinstance(payload["uom_code"], str)
        assert len(payload["uom_code"]) > 0

    def test_payload_uom_code_no_special_chars(self):
        """uom_code should not contain special characters in generated payloads."""
        payload = generate_uom_api_payload()
        special_chars = set("!@#$%^&*()")
        assert not any(c in special_chars for c in payload["uom_code"])

    def test_payload_uom_description_is_string_or_none(self):
        """uom_description must be a string or None."""
        payload = generate_uom_api_payload()
        assert payload["uom_description"] is None or isinstance(payload["uom_description"], str)

    def test_payload_status_is_boolean(self):
        """status must be a boolean (True=Active, False=Inactive)."""
        payload = generate_uom_api_payload()
        assert isinstance(payload["status"], bool)

    def test_payload_status_default_is_true(self):
        """Default status should be True (Active)."""
        payload = generate_uom_api_payload()
        assert payload["status"] is True

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payload = generate_uom_api_payload()
        assert payload["id"] == ""

    def test_build_with_explicit_data(self):
        """build_uom_api_payload with explicit data should use those values."""
        data = {
            "uom_code": "TEST",
            "uom_description": "Test Unit",
            "status": "Active",
        }
        payload = build_uom_api_payload(data=data)
        assert payload["uom_code"] == "TEST"
        assert payload["uom_description"] == "Test Unit"
        # status in payload is always True (default), UI data "Active" is mapped by toggle

    def test_build_with_empty_description(self):
        """build_uom_api_payload with empty description should set None."""
        data = {
            "uom_code": "TEST",
            "uom_description": "",
            "status": "Active",
        }
        payload = build_uom_api_payload(data=data)
        assert payload["uom_description"] is None

    def test_build_with_none_description(self):
        """build_uom_api_payload with None description should keep None."""
        data = {
            "uom_code": "TEST",
            "uom_description": None,
            "status": "Active",
        }
        payload = build_uom_api_payload(data=data)
        assert payload["uom_description"] is None

    def test_build_with_no_data_generates_random(self):
        """build_uom_api_payload with no data should generate random values."""
        payload = build_uom_api_payload()
        assert payload["uom_code"] != ""
        assert isinstance(payload["uom_code"], str)

@pytest.mark.api
class TestUOMBatchGeneration:
    """Verify batch payload generation for UOM."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_codes_are_unique(self):
        """All uom_code values in a batch should be unique."""
        payloads = generate_batch_payloads(count=15)
        codes = [p["uom_code"] for p in payloads]
        assert len(codes) == len(set(codes)), f"Duplicate codes found in batch"

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='UOM'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "UOM"

    def test_batch_all_have_status_true(self):
        """Every payload in batch must have status=True."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["status"] is True

    def test_batch_all_are_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p
