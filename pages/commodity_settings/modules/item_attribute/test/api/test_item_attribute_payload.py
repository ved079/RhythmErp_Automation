"""
test_item_attribute_payload.py — Fast API payload structure tests for Item Attribute.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.item_attribute.data.item_attribute_data import (
    build_item_attribute_payload,
    generate_item_attribute_payloads,
    generate_all_attribute_payloads,
    generate_batch_payloads,
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    DEFAULT_ITEM_ATTRIBUTE_FK_IDS,
    UOM_IDS,
)


@pytest.mark.api
class TestItemAttributeAPIPayload:
    """Verify that generated Item Attribute API payloads are structurally correct."""

    # ── Item Attribute1 specific tests ──

    def test_ia1_payload_has_required_keys(self):
        """IA1 payload must include id, attribute_name, name, description, base_uom, status."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=1)
        payload = payloads[0]
        required_keys = {"id", "attribute_name", "name", "description", "base_uom", "status"}
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_ia1_is_flat(self):
        """Item Attribute1 is a flat screen — no children or details."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_ia1_attribute_name(self):
        """IA1 attribute_name must be exactly 'Item Attribute1'."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=1)
        assert payloads[0]["attribute_name"] == "Item Attribute1"

    def test_ia1_id_empty(self):
        """IA1 id must be empty string for create operations."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=1)
        assert payloads[0]["id"] == ""

    def test_ia1_name_is_string(self):
        """IA1 name must be a non-empty string."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=1)
        assert isinstance(payloads[0]["name"], str)
        assert len(payloads[0]["name"]) > 0

    def test_ia1_base_uom_is_integer(self):
        """IA1 base_uom must be an integer FK ID."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=1)
        assert isinstance(payloads[0]["base_uom"], int)

    def test_ia1_base_uom_in_valid_pool(self):
        """IA1 base_uom value must exist in the UOM_IDS pool."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=5)
        valid_uom_values = set(UOM_IDS.values())
        for p in payloads:
            assert p["base_uom"] in valid_uom_values, \
                f"base_uom={p['base_uom']} not found in UOM_IDS values"

    def test_ia1_status_is_boolean(self):
        """IA1 status must be a boolean."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=1)
        assert isinstance(payloads[0]["status"], bool)

    def test_ia1_status_default_true(self):
        """IA1 status must default to True (Active)."""
        payloads = generate_item_attribute_payloads(attr_number=1, count=1)
        assert payloads[0]["status"] is True

    def test_build_ia1_with_explicit_values(self):
        """build_item_attribute_payload with explicit values should use them."""
        payload = build_item_attribute_payload(
            attr_number=1,
            name="Test Attr",
            description="Test description",
            base_uom_id=249,
            status=False,
        )
        assert payload["name"] == "Test Attr"
        assert payload["description"] == "Test description"
        assert payload["base_uom"] == 249
        assert payload["status"] is False
        assert payload["attribute_name"] == "Item Attribute1"
        assert payload["id"] == ""

    # ── Item Attribute2-5 generic tests ──

    def test_ia2_payload_no_base_uom(self):
        """Item Attribute2 should NOT have base_uom in payload."""
        payloads = generate_item_attribute_payloads(attr_number=2, count=1)
        assert "base_uom" not in payloads[0]

    def test_ia3_payload_no_base_uom(self):
        """Item Attribute3 should NOT have base_uom in payload."""
        payloads = generate_item_attribute_payloads(attr_number=3, count=1)
        assert "base_uom" not in payloads[0]

    def test_ia4_payload_no_base_uom(self):
        """Item Attribute4 should NOT have base_uom in payload."""
        payloads = generate_item_attribute_payloads(attr_number=4, count=1)
        assert "base_uom" not in payloads[0]

    def test_ia5_payload_no_base_uom(self):
        """Item Attribute5 should NOT have base_uom in payload."""
        payloads = generate_item_attribute_payloads(attr_number=5, count=1)
        assert "base_uom" not in payloads[0]

    def test_ia2_attribute_name(self):
        """Item Attribute2 attribute_name must be 'Item Attribute2'."""
        payloads = generate_item_attribute_payloads(attr_number=2, count=1)
        assert payloads[0]["attribute_name"] == "Item Attribute2"

    def test_all_5_screens_generate_payloads(self):
        """All 5 Item Attribute screens should generate valid payloads."""
        all_payloads = generate_all_attribute_payloads(count=3)
        assert len(all_payloads) == 5
        for attr_num in range(1, 6):
            assert attr_num in all_payloads
            assert len(all_payloads[attr_num]) == 3
            for p in all_payloads[attr_num]:
                assert p["attribute_name"] == f"Item Attribute{attr_num}"


@pytest.mark.api
class TestItemAttributeBatchGeneration:
    """Verify batch payload generation for Item Attribute."""

    def test_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_default_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_all_attribute_name_is_ia1(self):
        """Every payload in batch must have attribute_name='Item Attribute1'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Item Attribute1"

    def test_all_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_names_unique(self):
        """All names in a batch should be unique."""
        payloads = generate_batch_payloads(count=20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"
