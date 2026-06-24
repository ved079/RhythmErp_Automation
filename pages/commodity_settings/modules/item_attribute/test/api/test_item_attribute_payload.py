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
    generate_ia_name,
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    MOCK_FK_IDS,
)


@pytest.mark.api
class TestItemAttributeAPIPayload:
    """Verify that generated Item Attribute API payloads are structurally correct."""

    # ── Item Attribute1 specific tests ──

    def test_ia1_payload_has_required_keys(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=1, fk_ids=MOCK_FK_IDS)
        payload = payloads[0]
        required_keys = {"id", "attribute_name", "name", "description", "base_uom", "status"}
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_ia1_is_flat(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=1, fk_ids=MOCK_FK_IDS)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_ia1_attribute_name(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=1, fk_ids=MOCK_FK_IDS)
        assert payloads[0]["attribute_name"] == "Item Attribute1"

    def test_ia1_id_empty(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=1, fk_ids=MOCK_FK_IDS)
        assert payloads[0]["id"] == ""

    def test_ia1_name_is_string(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=1, fk_ids=MOCK_FK_IDS)
        assert isinstance(payloads[0]["name"], str)
        assert len(payloads[0]["name"]) > 0

    def test_ia1_base_uom_is_integer(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=1, fk_ids=MOCK_FK_IDS)
        assert isinstance(payloads[0]["base_uom"], int)

    def test_ia1_base_uom_in_valid_pool(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=5, fk_ids=MOCK_FK_IDS)
        valid_uom_values = set(MOCK_FK_IDS["base_uom"].values())
        for p in payloads:
            assert p["base_uom"] in valid_uom_values, \
                f"base_uom={p['base_uom']} not found in MOCK_FK_IDS values"

    def test_ia1_status_is_boolean(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=1, fk_ids=MOCK_FK_IDS)
        assert isinstance(payloads[0]["status"], bool)

    def test_ia1_status_default_true(self):
        payloads = generate_item_attribute_payloads(attr_number=1, count=1, fk_ids=MOCK_FK_IDS)
        assert payloads[0]["status"] is True

    def test_build_ia1_with_explicit_values(self):
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
        payloads = generate_item_attribute_payloads(attr_number=2, count=1)
        assert "base_uom" not in payloads[0]

    def test_ia3_payload_no_base_uom(self):
        payloads = generate_item_attribute_payloads(attr_number=3, count=1)
        assert "base_uom" not in payloads[0]

    def test_ia4_payload_no_base_uom(self):
        payloads = generate_item_attribute_payloads(attr_number=4, count=1)
        assert "base_uom" not in payloads[0]

    def test_ia5_payload_no_base_uom(self):
        payloads = generate_item_attribute_payloads(attr_number=5, count=1)
        assert "base_uom" not in payloads[0]

    def test_ia2_attribute_name(self):
        payloads = generate_item_attribute_payloads(attr_number=2, count=1)
        assert payloads[0]["attribute_name"] == "Item Attribute2"

    def test_all_5_screens_generate_payloads(self):
        all_payloads = generate_all_attribute_payloads(count=3, fk_ids=MOCK_FK_IDS)
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
        payloads = generate_batch_payloads(count=5, dropdown_ids=MOCK_FK_IDS)
        assert len(payloads) == 5

    def test_default_20(self):
        payloads = generate_batch_payloads(dropdown_ids=MOCK_FK_IDS)
        assert len(payloads) == 20

    def test_all_attribute_name_is_ia1(self):
        payloads = generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS)
        for p in payloads:
            assert p["attribute_name"] == "Item Attribute1"

    def test_all_flat(self):
        payloads = generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_names_unique(self):
        generate_ia_name.used = set()
        payloads = generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"
