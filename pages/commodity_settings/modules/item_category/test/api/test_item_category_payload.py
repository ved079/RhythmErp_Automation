"""
test_item_category_payload.py — Fast API payload structure tests for Item Category.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.item_category.data.item_category_data import (
    build_item_category_api_payload,
    generate_item_category_payloads,
    generate_batch_payloads,
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    DEFAULT_ITEM_CATEGORY_FK_IDS,
)


@pytest.mark.api
class TestItemCategoryAPIPayload:
    """Verify that generated Item Category API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, item_code, item_description, level, status."""
        payloads = generate_item_category_payloads(count=1)
        payload = payloads[0]
        required_keys = {"id", "attribute_name", "item_code", "item_description", "level", "status"}
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_payload_is_flat_no_children(self):
        """Item Category is a flat screen — payload must NOT have children or details."""
        payloads = generate_item_category_payloads(count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name_is_item_category(self):
        """attribute_name must be exactly 'Item Category'."""
        payloads = generate_item_category_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Item Category"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_item_category_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_payload_item_code_is_string(self):
        """item_code must be a non-empty string."""
        payloads = generate_item_category_payloads(count=1)
        assert isinstance(payloads[0]["item_code"], str)
        assert len(payloads[0]["item_code"]) > 0

    def test_payload_item_description_is_string(self):
        """item_description must be a string."""
        payloads = generate_item_category_payloads(count=1)
        assert isinstance(payloads[0]["item_description"], str)

    def test_payload_level_is_integer(self):
        """level must be an integer."""
        payloads = generate_item_category_payloads(count=1)
        assert isinstance(payloads[0]["level"], int)

    def test_payload_status_is_boolean(self):
        """status must be a boolean (True=Active, False=Inactive)."""
        payloads = generate_item_category_payloads(count=1)
        assert isinstance(payloads[0]["status"], bool)

    def test_payload_status_default_is_true(self):
        """Default status should be True (Active)."""
        payloads = generate_item_category_payloads(count=1)
        assert payloads[0]["status"] is True

    def test_build_with_explicit_values(self):
        """build_item_category_api_payload with explicit values should use them."""
        payload = build_item_category_api_payload(
            item_code="Test Category",
            item_description="Test description",
            level=2,
            status=False,
        )
        assert payload["item_code"] == "Test Category"
        assert payload["item_description"] == "Test description"
        assert payload["level"] == 2
        assert payload["status"] is False
        assert payload["attribute_name"] == "Item Category"
        assert payload["id"] == ""

    def test_build_with_default_status(self):
        """build_item_category_api_payload without status should default to True."""
        payload = build_item_category_api_payload(
            item_code="DefaultStatus",
            item_description="Testing default status",
            level=1,
        )
        assert payload["status"] is True

    def test_payload_level_values_are_valid(self):
        """Level values should be 1, 2, or 3 (top, sub, sub-sub)."""
        payloads = generate_item_category_payloads(count=20)
        valid_levels = {1, 2, 3}
        for p in payloads:
            assert p["level"] in valid_levels, \
                f"level {p['level']} not in valid range {{1, 2, 3}}"


@pytest.mark.api
class TestItemCategoryBatchGeneration:
    """Verify batch payload generation for Item Category."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='Item Category'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Item Category"

    def test_batch_all_are_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_batch_all_status_true(self):
        """Every payload in batch must have status=True (default)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["status"] is True

    def test_batch_item_codes_unique(self):
        """All item_codes in a small batch should be unique."""
        payloads = generate_batch_payloads(count=20)
        codes = [p["item_code"] for p in payloads]
        assert len(codes) == len(set(codes)), "Duplicate item_codes found in batch"
