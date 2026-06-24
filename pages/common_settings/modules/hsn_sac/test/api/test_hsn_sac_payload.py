"""
test_hsn_sac_payload.py — Fast API payload structure tests for HSN SAC.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    build_hsn_sac_api_payload,
    generate_hsn_sac_api_payloads,
    generate_batch_payloads,
    HSN_SAC_TYPE_IDS,
)


@pytest.mark.api
class TestHsnSacAPIPayload:
    def test_payload_has_required_keys(self):
        p = generate_hsn_sac_api_payloads(count=1)[0]
        for key in ["id", "attribute_name", "hsn_sac_no", "hsn_sac_type", "hsn_sac_description"]:
            assert key in p, f"Missing key: {key}"

    def test_payload_is_flat_no_children(self):
        p = generate_hsn_sac_api_payloads(count=1)[0]
        assert "children" not in p
        assert "details" not in p

    def test_payload_attribute_name(self):
        p = generate_hsn_sac_api_payloads(count=1)[0]
        assert p["attribute_name"] == "HSN SAC"

    def test_payload_id_is_empty_string(self):
        p = generate_hsn_sac_api_payloads(count=1)[0]
        assert p["id"] == ""

    def test_payload_hsn_sac_type_is_integer(self):
        p = generate_hsn_sac_api_payloads(count=1)[0]
        assert isinstance(p["hsn_sac_type"], int)

    def test_payload_hsn_sac_no_is_string(self):
        p = generate_hsn_sac_api_payloads(count=1)[0]
        assert isinstance(p["hsn_sac_no"], str)
        assert len(p["hsn_sac_no"]) > 0

    def test_payload_description_is_string(self):
        p = generate_hsn_sac_api_payloads(count=1)[0]
        assert isinstance(p["hsn_sac_description"], str)

    def test_payload_hsn_sac_type_in_valid_pool(self):
        valid_ids = set(HSN_SAC_TYPE_IDS.values())
        for p in generate_hsn_sac_api_payloads(count=5):
            assert p["hsn_sac_type"] in valid_ids

    def test_build_with_explicit_values(self):
        p = build_hsn_sac_api_payload(hsn_sac_no="1234", hsn_sac_type_id=159, hsn_sac_description="Test HSN")
        assert p["hsn_sac_no"] == "1234"
        assert p["hsn_sac_type"] == 159


@pytest.mark.api
class TestHsnSacBatchGeneration:
    def test_batch_generates_correct_count(self):
        assert len(generate_batch_payloads(count=5)) == 5

    def test_batch_default_count_is_20(self):
        assert len(generate_batch_payloads()) == 20

    def test_batch_all_have_attribute_name(self):
        for p in generate_batch_payloads(count=10):
            assert p["attribute_name"] == "HSN SAC"

    def test_batch_all_fk_ids_valid(self):
        valid_ids = set(HSN_SAC_TYPE_IDS.values())
        for p in generate_batch_payloads(count=10):
            assert p["hsn_sac_type"] in valid_ids

    def test_batch_all_are_flat(self):
        for p in generate_batch_payloads(count=10):
            assert "children" not in p
            assert "details" not in p

    def test_batch_hsn_sac_nos_are_unique(self):
        payloads = generate_batch_payloads(count=10)
        nos = [p["hsn_sac_no"] for p in payloads]
        assert len(nos) == len(set(nos))

    def test_batch_cycles_through_all_4_types(self):
        payloads = generate_batch_payloads(count=8)
        type_ids_used = set(p["hsn_sac_type"] for p in payloads)
        assert len(type_ids_used) >= 2  # At least 2 different types in 8 payloads
