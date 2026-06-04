"""
test_cbr_payload.py — Fast API payload structure tests for Commodity Base Rate.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.commodity_base_rate.data.cbr_data import (
    build_cbr_api_payload,
    generate_cbr_payloads,
    generate_batch_payloads,
    PRICING_TYPE_ID_MAP,
    LOCATION_ID_MAP,
    DEFAULT_COMMODITY_BASE_RATE_FK_IDS,
    FIELD_VALIDATION_RULES,
)


@pytest.mark.api
class TestCBRAPIPayload:
    """Verify that generated Commodity Base Rate API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, and all CBR header fields."""
        payloads = generate_cbr_payloads(count=1)
        payload = payloads[0]
        required_keys = {
            "id", "attribute_name", "pricing_type_ref_id",
            "from_date", "to_date", "location_ref_id",
        }
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_payload_is_flat_no_children(self):
        """CBR is a header-only screen — payload must NOT have children or details."""
        payloads = generate_cbr_payloads(count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name(self):
        """attribute_name must be exactly 'Commodity Base Rate'."""
        payloads = generate_cbr_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Commodity Base Rate"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_cbr_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_payload_pricing_type_is_integer(self):
        """pricing_type_ref_id must be an integer FK ID."""
        payloads = generate_cbr_payloads(count=1)
        assert isinstance(payloads[0]["pricing_type_ref_id"], int)

    def test_payload_from_date_is_string(self):
        """from_date must be a string (ISO datetime)."""
        payloads = generate_cbr_payloads(count=1)
        assert isinstance(payloads[0]["from_date"], str)

    def test_payload_to_date_is_string(self):
        """to_date must be a string (ISO datetime)."""
        payloads = generate_cbr_payloads(count=1)
        assert isinstance(payloads[0]["to_date"], str)

    def test_payload_location_ref_id_is_integer(self):
        """location_ref_id must be an integer FK ID."""
        payloads = generate_cbr_payloads(count=1)
        assert isinstance(payloads[0]["location_ref_id"], int)

    def test_payload_no_status_field(self):
        """CBR does not have a status field."""
        payloads = generate_cbr_payloads(count=1)
        assert "status" not in payloads[0]

    def test_payload_pricing_type_in_valid_pool(self):
        """pricing_type_ref_id value must be from PRICING_TYPE_ID_MAP."""
        payloads = generate_cbr_payloads(count=5)
        valid_ids = set(PRICING_TYPE_ID_MAP.values())
        for p in payloads:
            assert p["pricing_type_ref_id"] in valid_ids, \
                f"pricing_type_ref_id {p['pricing_type_ref_id']} not in PRICING_TYPE_ID_MAP"

    def test_payload_location_in_valid_pool(self):
        """location_ref_id value must be from LOCATION_ID_MAP."""
        payloads = generate_cbr_payloads(count=5)
        valid_ids = set(LOCATION_ID_MAP.values())
        for p in payloads:
            assert p["location_ref_id"] in valid_ids, \
                f"location_ref_id {p['location_ref_id']} not in LOCATION_ID_MAP"

    def test_build_with_explicit_values(self):
        """build_cbr_api_payload with explicit values should use them."""
        payload = build_cbr_api_payload(
            pricing_type_ref_id=118,
            location_ref_id=1,
            from_date="2025-04-01T00:00:00Z",
            to_date="2099-12-30T18:30:00Z",
        )
        assert payload["pricing_type_ref_id"] == 118
        assert payload["location_ref_id"] == 1
        assert payload["from_date"] == "2025-04-01T00:00:00Z"
        assert payload["to_date"] == "2099-12-30T18:30:00Z"
        assert payload["attribute_name"] == "Commodity Base Rate"

    def test_payload_to_date_format(self):
        """to_date should follow ISO datetime format with Z suffix."""
        payloads = generate_cbr_payloads(count=5)
        for p in payloads:
            assert p["to_date"].endswith("Z"), \
                f"to_date should end with Z, got: {p['to_date']}"


@pytest.mark.api
class TestCBRBatchGeneration:
    """Verify batch payload generation for Commodity Base Rate."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='Commodity Base Rate'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Commodity Base Rate"

    def test_batch_all_are_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_batch_all_fk_valid(self):
        """All FK values in batch must be from valid pools."""
        payloads = generate_batch_payloads(count=10)
        valid_pt = set(PRICING_TYPE_ID_MAP.values())
        valid_loc = set(LOCATION_ID_MAP.values())
        for p in payloads:
            assert p["pricing_type_ref_id"] in valid_pt
            assert p["location_ref_id"] in valid_loc

    def test_batch_no_status_field(self):
        """No payload in batch should have a status field."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "status" not in p
