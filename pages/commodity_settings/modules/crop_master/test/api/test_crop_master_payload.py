"""
test_crop_master_payload.py — Fast API payload structure tests for Crop Master.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.crop_master.data.crop_master_data import (
    build_crop_master_api_payload,
    generate_crop_master_payloads,
    generate_batch_payloads,
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    DEFAULT_CROP_MASTER_FK_IDS,
)


@pytest.mark.api
class TestCropMasterAPIPayload:
    """Verify that generated Crop Master API payloads are structurally correct."""

    def test_has_required_keys(self):
        """Payload must include id, attribute_name, name, description, status."""
        payloads = generate_crop_master_payloads(count=1)
        payload = payloads[0]
        required_keys = {"id", "attribute_name", "name", "description", "status"}
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_is_flat_no_children(self):
        """Crop Master is a flat screen — payload must NOT have children or details."""
        payloads = generate_crop_master_payloads(count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_attribute_name(self):
        """attribute_name must be exactly 'Crop Master'."""
        payloads = generate_crop_master_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Crop Master"

    def test_id_empty(self):
        """id must be empty string for create operations."""
        payloads = generate_crop_master_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_name_is_string(self):
        """name must be a non-empty string."""
        payloads = generate_crop_master_payloads(count=1)
        assert isinstance(payloads[0]["name"], str)
        assert len(payloads[0]["name"]) > 0

    def test_description_is_string(self):
        """description must be a string."""
        payloads = generate_crop_master_payloads(count=1)
        assert isinstance(payloads[0]["description"], str)

    def test_status_is_boolean(self):
        """status must be a boolean."""
        payloads = generate_crop_master_payloads(count=1)
        assert isinstance(payloads[0]["status"], bool)

    def test_status_default_true(self):
        """status must default to True (Active)."""
        payloads = generate_crop_master_payloads(count=1)
        assert payloads[0]["status"] is True

    def test_build_with_explicit_values(self):
        """build_crop_master_api_payload with explicit values should use them."""
        payload = build_crop_master_api_payload(
            name="Test Crop",
            description="Test description",
            status=False,
        )
        assert payload["name"] == "Test Crop"
        assert payload["description"] == "Test description"
        assert payload["status"] is False
        assert payload["attribute_name"] == "Crop Master"
        assert payload["id"] == ""

    def test_no_fk_ids_needed(self):
        """Crop Master has no FK dropdowns — DEFAULT_CROP_MASTER_FK_IDS should be empty."""
        assert DEFAULT_CROP_MASTER_FK_IDS == {}


@pytest.mark.api
class TestCropMasterBatchGeneration:
    """Verify batch payload generation for Crop Master."""

    def test_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_default_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_all_attribute_name(self):
        """Every payload in batch must have attribute_name='Crop Master'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Crop Master"

    def test_all_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_all_status_true(self):
        """Every payload in a default batch should have status=True."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["status"] is True

    def test_names_unique(self):
        """All names in a batch should be unique."""
        payloads = generate_batch_payloads(count=20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"
