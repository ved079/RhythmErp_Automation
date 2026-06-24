"""
test_error_code_mst_payload.py — Fast API payload structure tests for Error Code Mst.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    build_error_code_mst_api_payload,
    generate_error_code_mst_api_payloads,
    generate_batch_payloads,
    ERROR_CODE_TYPE_IDS,
)


@pytest.mark.api
class TestErrorCodeMstAPIPayload:
    def test_payload_has_required_keys(self):
        payloads = generate_error_code_mst_api_payloads(count=1)
        p = payloads[0]
        for key in ["id", "attribute_name", "error_code_type", "code", "description", "is_qty_amount"]:
            assert key in p, f"Missing key: {key}"

    def test_payload_is_flat_no_children(self):
        p = generate_error_code_mst_api_payloads(count=1)[0]
        assert "children" not in p
        assert "details" not in p

    def test_payload_attribute_name(self):
        p = generate_error_code_mst_api_payloads(count=1)[0]
        assert p["attribute_name"] == "Error Code Mst"

    def test_payload_id_is_empty_string(self):
        p = generate_error_code_mst_api_payloads(count=1)[0]
        assert p["id"] == ""

    def test_payload_error_code_type_is_integer(self):
        p = generate_error_code_mst_api_payloads(count=1)[0]
        assert isinstance(p["error_code_type"], int)

    def test_payload_code_is_string(self):
        p = generate_error_code_mst_api_payloads(count=1)[0]
        assert isinstance(p["code"], str)
        assert len(p["code"]) > 0

    def test_payload_description_is_string(self):
        p = generate_error_code_mst_api_payloads(count=1)[0]
        assert isinstance(p["description"], str)

    def test_payload_is_qty_amount_is_string(self):
        p = generate_error_code_mst_api_payloads(count=1)[0]
        assert isinstance(p["is_qty_amount"], str)
        assert p["is_qty_amount"] in ("Qty", "Amount")

    def test_payload_error_code_type_in_valid_pool(self):
        payloads = generate_error_code_mst_api_payloads(count=5)
        valid_ids = set(ERROR_CODE_TYPE_IDS.values())
        for p in payloads:
            assert p["error_code_type"] in valid_ids

    def test_build_with_explicit_values(self):
        p = build_error_code_mst_api_payload(
            error_code_type_id=643, code="FM-TEST", description="Test error code", is_qty_amount="Qty"
        )
        assert p["error_code_type"] == 643
        assert p["code"] == "FM-TEST"
        assert p["is_qty_amount"] == "Qty"


@pytest.mark.api
class TestErrorCodeMstBatchGeneration:
    def test_batch_generates_correct_count(self):
        assert len(generate_batch_payloads(count=5)) == 5

    def test_batch_default_count_is_20(self):
        assert len(generate_batch_payloads()) == 20

    def test_batch_all_have_attribute_name(self):
        for p in generate_batch_payloads(count=10):
            assert p["attribute_name"] == "Error Code Mst"

    def test_batch_all_fk_ids_valid(self):
        valid_ids = set(ERROR_CODE_TYPE_IDS.values())
        for p in generate_batch_payloads(count=10):
            assert p["error_code_type"] in valid_ids

    def test_batch_all_are_flat(self):
        for p in generate_batch_payloads(count=10):
            assert "children" not in p
            assert "details" not in p

    def test_batch_codes_are_unique(self):
        payloads = generate_batch_payloads(count=10)
        codes = [p["code"] for p in payloads]
        assert len(codes) == len(set(codes))

    def test_batch_is_qty_amount_alternates(self):
        payloads = generate_batch_payloads(count=4)
        for p in payloads:
            assert p["is_qty_amount"] in ("Qty", "Amount")
