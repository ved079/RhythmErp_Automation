"""
test_cqp_payload.py — Fast API payload structure tests for Commodity Quality Parameter.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.commodity_quality_parameter.data.commodity_quality_parameter_data import (
    build_cqp_api_payload,
    generate_cqp_payloads,
    generate_batch_payloads,
    ITEM_ID_MAP,
    TRANSACTION_TYPE_ID_MAP,
    QUALITY_PARAM_ID_MAP,
    DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS,
    STEPPER_NAME,
)


@pytest.mark.api
class TestCQPAPIPayload:
    """Verify that generated Commodity Quality Parameter API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, and all CQP root fields + children."""
        payloads = generate_cqp_payloads(count=1)
        payload = payloads[0]
        required_keys = {
            "id", "attribute_name", "item_ref_id", "transaction_type",
            "from_date", "to_date", "revision_status", "details", "children",
        }
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_payload_has_children_with_stepper(self):
        """Payload must have children list with at least 1 stepper."""
        payloads = generate_cqp_payloads(count=1)
        p = payloads[0]
        assert isinstance(p["children"], list)
        assert len(p["children"]) >= 1
        child = p["children"][0]
        assert child["stepper_name"] == STEPPER_NAME
        assert child["is_stepper"] is True
        assert "details" in child

    def test_payload_attribute_name(self):
        """attribute_name must be exactly 'Commodity Quality Parameter'."""
        payloads = generate_cqp_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Commodity Quality Parameter"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_cqp_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_payload_item_ref_id_is_integer(self):
        """item_ref_id must be an integer FK ID."""
        payloads = generate_cqp_payloads(count=1)
        assert isinstance(payloads[0]["item_ref_id"], int)

    def test_payload_transaction_type_is_integer(self):
        """transaction_type must be an integer FK ID."""
        payloads = generate_cqp_payloads(count=1)
        assert isinstance(payloads[0]["transaction_type"], int)

    def test_payload_from_date_is_string(self):
        """from_date must be a string (ISO datetime)."""
        payloads = generate_cqp_payloads(count=1)
        assert isinstance(payloads[0]["from_date"], str)

    def test_payload_to_date_is_string(self):
        """to_date must be a string (ISO datetime)."""
        payloads = generate_cqp_payloads(count=1)
        assert isinstance(payloads[0]["to_date"], str)

    def test_payload_revision_status_is_string(self):
        """revision_status must be a string."""
        payloads = generate_cqp_payloads(count=1)
        assert isinstance(payloads[0]["revision_status"], str)

    def test_payload_item_ref_id_in_valid_pool(self):
        """item_ref_id value must be from ITEM_ID_MAP."""
        payloads = generate_cqp_payloads(count=5)
        valid_ids = set(ITEM_ID_MAP.values())
        for p in payloads:
            assert p["item_ref_id"] in valid_ids, \
                f"item_ref_id {p['item_ref_id']} not in ITEM_ID_MAP"

    def test_payload_transaction_type_in_valid_pool(self):
        """transaction_type value must be from TRANSACTION_TYPE_ID_MAP."""
        payloads = generate_cqp_payloads(count=5)
        valid_ids = set(TRANSACTION_TYPE_ID_MAP.values())
        for p in payloads:
            assert p["transaction_type"] in valid_ids, \
                f"transaction_type {p['transaction_type']} not in TRANSACTION_TYPE_ID_MAP"

    def test_payload_stepper_details_have_quality_type(self):
        """Each detail row in stepper must have quality_type field."""
        payloads = generate_cqp_payloads(count=1)
        p = payloads[0]
        details = p["children"][0]["details"]
        for line in details:
            assert "quality_type" in line
            assert "min_quality_value" in line
            assert "max_quality_value" in line

    def test_payload_stepper_quality_type_in_valid_pool(self):
        """quality_type in stepper details must be from QUALITY_PARAM_ID_MAP."""
        payloads = generate_cqp_payloads(count=1)
        p = payloads[0]
        valid_ids = set(QUALITY_PARAM_ID_MAP.values())
        for line in p["children"][0]["details"]:
            assert line["quality_type"] in valid_ids, \
                f"quality_type {line['quality_type']} not in QUALITY_PARAM_ID_MAP"

    def test_payload_root_details_is_empty_list(self):
        """Root payload 'details' should be an empty list (details live in children)."""
        payloads = generate_cqp_payloads(count=1)
        p = payloads[0]
        assert "details" in p
        assert isinstance(p["details"], list)
        assert len(p["details"]) == 0

    def test_payload_stepper_children_is_empty(self):
        """Stepper child's 'children' should be an empty list (no nested children)."""
        payloads = generate_cqp_payloads(count=1)
        p = payloads[0]
        stepper = p["children"][0]
        assert isinstance(stepper["children"], list)
        assert len(stepper["children"]) == 0

    def test_build_with_explicit_values(self):
        """build_cqp_api_payload with explicit values should use them."""
        payload = build_cqp_api_payload(
            item_ref_id=94,
            transaction_type=154,
            quality_params=[
                {"quality_type": 1, "min_quality_value": "5", "max_quality_value": "10",
                 "rate_percentage": True, "multiplier": "1.0"},
            ],
            from_date="2025-04-01",
            to_date="2099-12-30T18:30:00Z",
            revision_status="Rev-001",
        )
        assert payload["item_ref_id"] == 94
        assert payload["transaction_type"] == 154
        assert payload["children"][0]["details"][0]["quality_type"] == 1
        assert payload["revision_status"] == "Rev-001"


@pytest.mark.api
class TestCQPBatchGeneration:
    """Verify batch payload generation for Commodity Quality Parameter."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='Commodity Quality Parameter'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Commodity Quality Parameter"

    def test_batch_all_have_children(self):
        """Every payload in batch must have children with stepper."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert isinstance(p["children"], list)
            assert len(p["children"]) >= 1

    def test_batch_all_fk_valid(self):
        """All FK values in batch must be from valid pools."""
        payloads = generate_batch_payloads(count=10)
        valid_item = set(ITEM_ID_MAP.values())
        valid_txn = set(TRANSACTION_TYPE_ID_MAP.values())
        for p in payloads:
            assert p["item_ref_id"] in valid_item
            assert p["transaction_type"] in valid_txn
