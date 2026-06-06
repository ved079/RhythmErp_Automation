"""
test_quality_parameter_master_payload.py — Fast API payload structure tests for Quality Parameter Master.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.quality_parameter_master.data.quality_parameter_master_data import (
    build_quality_parameter_payload,
    generate_quality_parameter_payloads,
    generate_batch_payloads,
    FIELD_VALIDATION_RULES,
    DEFAULT_QUALITY_PARAMETER_MASTER_FK_IDS,
)


@pytest.mark.api
class TestQualityParameterMasterAPIPayload:
    """Verify that generated Quality Parameter Master API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, and name."""
        payloads = generate_quality_parameter_payloads(count=1)
        payload = payloads[0]
        required_keys = {"id", "attribute_name", "name"}
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_payload_is_flat_no_children(self):
        """QPM is a flat screen — payload must NOT have children or details."""
        payloads = generate_quality_parameter_payloads(count=1)
        payload = payloads[0]
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name_is_quality_parameter_master(self):
        """attribute_name must be exactly 'Quality Parameter Master'."""
        payloads = generate_quality_parameter_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Quality Parameter Master"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_quality_parameter_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_payload_name_is_string(self):
        """name must be a non-empty string."""
        payloads = generate_quality_parameter_payloads(count=1)
        assert isinstance(payloads[0]["name"], str)
        assert len(payloads[0]["name"]) > 0

    def test_payload_has_exactly_3_keys(self):
        """QPM payload should have exactly 3 keys: id, attribute_name, name."""
        payloads = generate_quality_parameter_payloads(count=1)
        assert set(payloads[0].keys()) == {"id", "attribute_name", "name"}

    def test_payload_no_fk_ids_needed(self):
        """QPM has no FK dropdowns — DEFAULT_QUALITY_PARAMETER_MASTER_FK_IDS should be empty."""
        assert DEFAULT_QUALITY_PARAMETER_MASTER_FK_IDS == {}

    def test_build_with_explicit_values(self):
        """build_quality_parameter_payload with explicit name should use it."""
        payload = build_quality_parameter_payload(name="Test Moisture Content")
        assert payload["name"] == "Test Moisture Content"
        assert payload["attribute_name"] == "Quality Parameter Master"
        assert payload["id"] == ""

    def test_build_with_special_char_name(self):
        """build_quality_parameter_payload should accept special character names."""
        payload = build_quality_parameter_payload(name="Moisture (%) Content")
        assert payload["name"] == "Moisture (%) Content"

    def test_build_with_empty_name(self):
        """build_quality_parameter_payload should accept empty name (validation is server-side)."""
        payload = build_quality_parameter_payload(name="")
        assert payload["name"] == ""


@pytest.mark.api
class TestQualityParameterMasterBatchGeneration:
    """Verify batch payload generation for Quality Parameter Master."""

    def test_batch_generates_correct_count(self):
        """generate_batch_payloads should return the requested number of payloads."""
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        """Default batch size should be 20."""
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_all_have_attribute_name(self):
        """Every payload in batch must have attribute_name='Quality Parameter Master'."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Quality Parameter Master"

    def test_batch_all_are_flat(self):
        """Every payload in batch must be flat (no children/details)."""
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p

    def test_batch_names_unique(self):
        """All names in a small batch should be unique."""
        payloads = generate_batch_payloads(count=20)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"
