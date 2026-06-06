"""
test_item_group_payload.py — Fast API payload structure tests for Item Group.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.item_group.data.item_group_data import (
    build_item_group_api_payload,
    generate_item_group_payloads,
    generate_batch_payloads,
    FIELD_VALIDATION_RULES,
    DEFAULT_ITEM_GROUP_FK_IDS,
)


@pytest.mark.api
class TestItemGroupAPIPayload:
    """Verify that generated Item Group API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, code, and description."""
        payloads = generate_item_group_payloads(count=1)
        payload = payloads[0]
        required_keys = {"id", "attribute_name", "code", "description"}
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_payload_is_flat_no_children(self):
        """Item Group is a flat screen — payload must NOT have children or details."""
        payloads = generate_item_group_payloads(count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name_is_item_group(self):
        """attribute_name must be exactly 'Item Group'."""
        payloads = generate_item_group_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Item Group"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_item_group_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_payload_code_is_string(self):
        """code must be a non-empty string."""
        payloads = generate_item_group_payloads(count=1)
        assert isinstance(payloads[0]["code"], str)
        assert len(payloads[0]["code"]) > 0

    def test_payload_description_is_string(self):
        """description must be a string."""
        payloads = generate_item_group_payloads(count=1)
        assert isinstance(payloads[0]["description"], str)

    def test_payload_has_exactly_4_keys(self):
        """Item Group payload should have exactly 4 keys: id, attribute_name, code, description."""
        payloads = generate_item_group_payloads(count=1)
        assert set(payloads[0].keys()) == {"id", "attribute_name", "code", "description"}

    def test_payload_no_fk_ids_needed(self):
        """Item Group has no FK dropdowns — DEFAULT_ITEM_GROUP_FK_IDS should be empty."""
        assert DEFAULT_ITEM_GROUP_FK_IDS == {}

    def test_build_with_explicit_values(self):
        """build_item_group_api_payload with explicit values should use them."""
        payload = build_item_group_api_payload(
            code="TEST01",
            description="Test Group Description",
        )
        assert payload["code"] == "TEST01"
        assert payload["description"] == "Test Group Description"
        assert payload["attribute_name"] == "Item Group"
        assert payload["id"] == ""

    def test_build_with_empty_description(self):
        """build_item_group_api_payload with empty description should work."""
        payload = build_item_group_api_payload(
            code="NODESC01",
            description="",
        )
        assert payload["description"] == ""
        assert payload["code"] == "NODESC01"


@pytest.mark.api
class TestItemGroupBatchGeneration:
    """Verify batch payload generation for Item Group."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='Item Group'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Item Group"

    def test_batch_all_are_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_batch_codes_unique(self):
        """All codes in a small batch should be unique."""
        payloads = generate_batch_payloads(count=20)
        codes = [p["code"] for p in payloads]
        assert len(codes) == len(set(codes)), "Duplicate codes found in batch"
