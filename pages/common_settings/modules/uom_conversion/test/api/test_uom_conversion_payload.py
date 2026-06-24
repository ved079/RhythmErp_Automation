"""
test_uom_conversion_payload.py — Fast API payload structure tests for UOM Conversion.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    build_uom_conversion_api_payload,
    generate_uom_conversion_api_payloads,
    generate_batch_payloads,
    UOM_IDS,
)


@pytest.mark.api
class TestUOMConversionAPIPayload:
    """Verify that generated UOM Conversion API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, source_uom_code, target_uom_code, conversion_factor."""
        payloads = generate_uom_conversion_api_payloads(count=1)
        assert len(payloads) >= 1
        payload = payloads[0]
        assert "id" in payload
        assert payload["id"] == ""
        assert "attribute_name" in payload
        assert "source_uom_code" in payload
        assert "target_uom_code" in payload
        assert "conversion_factor" in payload

    def test_payload_is_flat_no_children(self):
        """UOM Conversion is a flat screen — payload must NOT have children or details."""
        payloads = generate_uom_conversion_api_payloads(count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name_is_uom_conversion(self):
        """attribute_name must be exactly 'UOM Conversion'."""
        payloads = generate_uom_conversion_api_payloads(count=1)
        assert payloads[0]["attribute_name"] == "UOM Conversion"

    def test_payload_source_uom_code_is_integer(self):
        """source_uom_code must be an integer FK ID."""
        payloads = generate_uom_conversion_api_payloads(count=1)
        assert isinstance(payloads[0]["source_uom_code"], int)

    def test_payload_target_uom_code_is_integer(self):
        """target_uom_code must be an integer FK ID."""
        payloads = generate_uom_conversion_api_payloads(count=1)
        assert isinstance(payloads[0]["target_uom_code"], int)

    def test_payload_conversion_factor_is_numeric(self):
        """conversion_factor must be a number (int or float)."""
        payloads = generate_uom_conversion_api_payloads(count=1)
        factor = payloads[0]["conversion_factor"]
        assert isinstance(factor, (int, float))

    def test_payload_source_fk_in_uom_ids(self):
        """source_uom_code value must be a valid UOM ID from our pool."""
        payloads = generate_uom_conversion_api_payloads(count=5)
        valid_ids = set(UOM_IDS.values())
        for p in payloads:
            assert p["source_uom_code"] in valid_ids, \
                f"source_uom_code {p['source_uom_code']} not in UOM_IDS"

    def test_payload_target_fk_in_uom_ids(self):
        """target_uom_code value must be a valid UOM ID from our pool."""
        payloads = generate_uom_conversion_api_payloads(count=5)
        valid_ids = set(UOM_IDS.values())
        for p in payloads:
            assert p["target_uom_code"] in valid_ids, \
                f"target_uom_code {p['target_uom_code']} not in UOM_IDS"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_uom_conversion_api_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_build_with_explicit_values(self):
        """build_uom_conversion_api_payload with explicit values should use them."""
        payload = build_uom_conversion_api_payload(
            source_uom_code=249,
            target_uom_code=250,
            conversion_factor=1000.0,
        )
        assert payload["source_uom_code"] == 249
        assert payload["target_uom_code"] == 250
        assert payload["conversion_factor"] == 1000.0
        assert payload["attribute_name"] == "UOM Conversion"

    def test_build_with_integer_factor(self):
        """conversion_factor can be an integer."""
        payload = build_uom_conversion_api_payload(
            source_uom_code=249,
            target_uom_code=252,
            conversion_factor=1,
        )
        assert payload["conversion_factor"] == 1

    def test_build_with_decimal_factor(self):
        """conversion_factor can be a decimal."""
        payload = build_uom_conversion_api_payload(
            source_uom_code=252,
            target_uom_code=504,
            conversion_factor=0.083333,
        )
        assert abs(payload["conversion_factor"] - 0.083333) < 0.0001

    def test_payload_same_source_and_target_allowed(self):
        """Self-conversion (same source and target) is allowed."""
        payload = build_uom_conversion_api_payload(
            source_uom_code=249,
            target_uom_code=249,
            conversion_factor=1.0,
        )
        assert payload["source_uom_code"] == payload["target_uom_code"]


@pytest.mark.api
class TestUOMConversionBatchGeneration:
    """Verify batch payload generation for UOM Conversion."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='UOM Conversion'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "UOM Conversion"

    def test_batch_all_fk_ids_valid(self):
        """All FK IDs in batch must be valid UOM IDs."""
        payloads = generate_batch_payloads(count=10)
        valid_ids = set(UOM_IDS.values())
        for p in payloads:
            assert p["source_uom_code"] in valid_ids
            assert p["target_uom_code"] in valid_ids

    def test_batch_all_are_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_batch_conversion_factors_are_numeric(self):
        """All conversion_factor values in batch must be numeric."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert isinstance(p["conversion_factor"], (int, float))
