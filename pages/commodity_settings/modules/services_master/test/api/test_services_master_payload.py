"""
test_services_master_payload.py — Fast API payload structure tests for Services Master.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.services_master.data.services_master_data import (
    build_services_master_api_payload,
    generate_services_master_payloads,
    generate_batch_payloads,
    UOM_ID_MAP,
    HSN_SAC_SERVICES_ID_MAP,
    DEFAULT_SERVICES_MASTER_FK_IDS,
    FIELD_VALIDATION_RULES,
)


@pytest.mark.api
class TestServicesMasterAPIPayload:
    """Verify that generated Services Master API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, and all 6 Services Master fields."""
        payloads = generate_services_master_payloads(count=1)
        payload = payloads[0]
        required_keys = {
            "id", "attribute_name", "name", "uom",
            "base_uom", "base_uom_conversion", "hsn_code", "status",
        }
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_payload_is_flat_no_children(self):
        """Services Master is a flat screen — payload must NOT have children or details."""
        payloads = generate_services_master_payloads(count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name(self):
        """attribute_name must be exactly 'Services Master'."""
        payloads = generate_services_master_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Services Master"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_services_master_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_payload_name_is_string(self):
        """name must be a non-empty string."""
        payloads = generate_services_master_payloads(count=1)
        assert isinstance(payloads[0]["name"], str)
        assert len(payloads[0]["name"]) > 0

    def test_payload_uom_is_integer(self):
        """uom must be an integer FK ID."""
        payloads = generate_services_master_payloads(count=1)
        assert isinstance(payloads[0]["uom"], int)

    def test_payload_base_uom_is_integer(self):
        """base_uom must be an integer FK ID."""
        payloads = generate_services_master_payloads(count=1)
        assert isinstance(payloads[0]["base_uom"], int)

    def test_payload_base_uom_conversion_is_string(self):
        """base_uom_conversion must be a string."""
        payloads = generate_services_master_payloads(count=1)
        assert isinstance(payloads[0]["base_uom_conversion"], str)

    def test_payload_hsn_code_is_integer(self):
        """hsn_code must be an integer FK ID."""
        payloads = generate_services_master_payloads(count=1)
        assert isinstance(payloads[0]["hsn_code"], int)

    def test_payload_status_is_boolean(self):
        """status must be a boolean (True=Active, False=Inactive)."""
        payloads = generate_services_master_payloads(count=1)
        assert isinstance(payloads[0]["status"], bool)

    def test_payload_status_default_true(self):
        """Default status should be True (Active)."""
        payloads = generate_services_master_payloads(count=1)
        assert payloads[0]["status"] is True

    def test_payload_uom_in_valid_pool(self):
        """uom value must be from UOM_ID_MAP."""
        payloads = generate_services_master_payloads(count=5)
        valid_ids = set(UOM_ID_MAP.values())
        for p in payloads:
            assert p["uom"] in valid_ids, \
                f"uom {p['uom']} not in UOM_ID_MAP"

    def test_payload_base_uom_in_valid_pool(self):
        """base_uom value must be from UOM_ID_MAP (same pool as uom)."""
        payloads = generate_services_master_payloads(count=5)
        valid_ids = set(UOM_ID_MAP.values())
        for p in payloads:
            assert p["base_uom"] in valid_ids, \
                f"base_uom {p['base_uom']} not in UOM_ID_MAP"

    def test_payload_hsn_code_in_valid_pool(self):
        """hsn_code value must be from HSN_SAC_SERVICES_ID_MAP."""
        payloads = generate_services_master_payloads(count=5)
        valid_ids = set(HSN_SAC_SERVICES_ID_MAP.values())
        for p in payloads:
            assert p["hsn_code"] in valid_ids, \
                f"hsn_code {p['hsn_code']} not in HSN_SAC_SERVICES_ID_MAP"

    def test_build_with_explicit_values(self):
        """build_services_master_api_payload with explicit values should use them."""
        payload = build_services_master_api_payload(
            name="Test Service",
            uom=249,
            base_uom=250,
            base_uom_conversion="100",
            hsn_code=108,
            status=True,
        )
        assert payload["name"] == "Test Service"
        assert payload["uom"] == 249
        assert payload["base_uom"] == 250
        assert payload["base_uom_conversion"] == "100"
        assert payload["hsn_code"] == 108
        assert payload["status"] is True


@pytest.mark.api
class TestServicesMasterBatchGeneration:
    """Verify batch payload generation for Services Master."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='Services Master'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Services Master"

    def test_batch_all_are_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_batch_all_status_true(self):
        """Every payload in batch must have status=True."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["status"] is True

    def test_batch_names_unique(self):
        """All names in a batch should be unique."""
        payloads = generate_batch_payloads(count=10)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names in batch"

    def test_batch_all_fk_valid(self):
        """All FK values in batch must be from valid pools."""
        payloads = generate_batch_payloads(count=10)
        valid_uom = set(UOM_ID_MAP.values())
        valid_hsn = set(HSN_SAC_SERVICES_ID_MAP.values())
        for p in payloads:
            assert p["uom"] in valid_uom
            assert p["base_uom"] in valid_uom
            assert p["hsn_code"] in valid_hsn
