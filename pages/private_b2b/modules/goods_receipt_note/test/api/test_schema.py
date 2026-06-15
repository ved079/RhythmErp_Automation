import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log


class TestGRNSchema:
    @pytest.mark.schema
    @pytest.mark.api
    def test_grn_create_response_has_id(self, grn_api, build_payload):
        log.info("GRN-SCHEMA-01: Create response includes id")
        payload = build_payload()
        data = grn_api.create_grn(payload)
        assert data is not None
        assert "id" in data, "Response should contain id"
        assert data["id"] is not None, "id should not be null"

    @pytest.mark.schema
    @pytest.mark.api
    def test_grn_get_response_has_expected_fields(self, grn_api, build_payload):
        log.info("GRN-SCHEMA-02: GET response has expected fields")
        payload = build_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]
        entry = grn_api.get_grn(entry_id)
        assert entry is not None

        for key in ["id", "transaction_date", "transaction_ref_no",
                     "supplier_ref_id", "supplier_ref_type",
                     "gate_pass_ref_id_id", "po_ref_id_id",
                     "grn_item_details", "additional_details"]:
            assert key in entry, f"Response missing key: {key}"

    @pytest.mark.schema
    @pytest.mark.api
    def test_grn_list_response_has_pagination(self, grn_api):
        log.info("GRN-SCHEMA-03: List response has pagination fields")
        result = grn_api.list_grns()
        assert result is not None
        for key in ["screenmatlistingdata_set", "page_total_records", "page_count"]:
            assert key in result, f"List response missing key: {key}"
