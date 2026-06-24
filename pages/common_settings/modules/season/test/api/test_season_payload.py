"""
test_season_payload.py — Fast API payload structure tests for Season.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.season.data.season_data import (
    build_season_api_payload,
    generate_season_api_payload,
    generate_batch_payloads,
)


@pytest.mark.api
class TestSeasonAPIPayload:
    """Verify that generated Season API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        payload = generate_season_api_payload()
        assert "id" in payload
        assert payload["id"] == ""
        assert "attribute_name" in payload
        assert payload["attribute_name"] == "Season"
        assert "name" in payload
        assert "description" in payload
        assert "status" in payload

    def test_payload_is_flat_no_children(self):
        payload = generate_season_api_payload()
        assert "children" not in payload
        assert "details" not in payload

    def test_payload_attribute_name_is_season(self):
        payload = generate_season_api_payload()
        assert payload["attribute_name"] == "Season"

    def test_payload_name_is_string(self):
        payload = generate_season_api_payload()
        assert isinstance(payload["name"], str)
        assert len(payload["name"]) > 0

    def test_payload_name_has_no_special_chars(self):
        """Generated names should be letters and spaces only."""
        payload = generate_season_api_payload()
        special_chars = set("!@#$%^&*()_0123456789")
        assert not any(c in special_chars for c in payload["name"])

    def test_payload_description_is_string_or_none(self):
        payload = generate_season_api_payload()
        assert payload["description"] is None or isinstance(payload["description"], str)

    def test_payload_status_is_boolean(self):
        payload = generate_season_api_payload()
        assert isinstance(payload["status"], bool)

    def test_payload_status_default_is_true(self):
        payload = generate_season_api_payload()
        assert payload["status"] is True

    def test_payload_id_is_empty_string(self):
        payload = generate_season_api_payload()
        assert payload["id"] == ""

    def test_build_with_explicit_data(self):
        data = {"Name": "Test Kharif", "Description": "Monsoon season", "status": True}
        payload = build_season_api_payload(data=data)
        assert payload["name"] == "Test Kharif"
        assert payload["description"] == "Monsoon season"

    def test_build_with_empty_description(self):
        data = {"Name": "Test Season", "Description": "", "status": True}
        payload = build_season_api_payload(data=data)
        assert payload["description"] is None

    def test_build_with_no_data_generates_random(self):
        payload = build_season_api_payload()
        assert payload["name"] != ""

@pytest.mark.api
class TestSeasonBatchGeneration:
    """Verify batch payload generation for Season."""

    def test_batch_generates_correct_count(self):
        payloads = generate_batch_payloads(count=5)
        assert len(payloads) == 5

    def test_batch_default_count_is_20(self):
        payloads = generate_batch_payloads()
        assert len(payloads) == 20

    def test_batch_names_are_unique(self):
        payloads = generate_batch_payloads(count=15)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names found in batch"

    def test_batch_all_have_attribute_name(self):
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["attribute_name"] == "Season"

    def test_batch_all_have_status_true(self):
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert p["status"] is True

    def test_batch_all_are_flat(self):
        payloads = generate_batch_payloads(count=10)
        for p in payloads:
            assert "children" not in p
            assert "details" not in p
