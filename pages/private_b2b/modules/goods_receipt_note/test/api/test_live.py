import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log


class TestGRNLive:
    @pytest.mark.smoke
    @pytest.mark.api
    def test_grn_create_and_retrieve(self, grn_api, build_payload):
        log.info("GRN-LIVE-01: Create GRN and verify via GET")
        payload = build_payload()
        data = grn_api.create_grn(payload)
        assert data is not None, "Create failed"
        entry_id = data["id"]

        fetched = grn_api.get_grn(entry_id)
        assert fetched is not None, "GET failed"
        assert fetched["id"] == entry_id
        assert fetched["supplier_ref_id"] == payload["supplier_ref_id"]
        assert fetched["po_ref_id_id"] == payload["po_ref_id_id"]

    @pytest.mark.api
    def test_grn_list_contains_created_entry(self, grn_api, build_payload):
        log.info("GRN-LIVE-02: List contains newly created entry")
        payload = build_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]
        ref_no = data.get("transaction_ref_no") or str(entry_id)

        listing = grn_api.list_grns(page=1, page_size=50)
        assert listing is not None
        items = listing.get("screenmatlistingdata_set", [])
        ids_in_list = [item["id"] for item in items if item.get("id")]
        assert entry_id in ids_in_list, (
            f"Created GRN {entry_id} should appear in listing"
        )

    @pytest.mark.api
    def test_grn_create_update_retrieve(self, grn_api, build_payload):
        log.info("GRN-LIVE-03: Create, update, and verify changes")
        payload = build_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]

        update_payload = build_payload()
        update_payload["additional_details"]["transporter_name"] = "Live Update Transporter"
        result = grn_api.update_grn(entry_id, update_payload)
        assert result is not None, "Update failed"

        fetched = grn_api.get_grn(entry_id)
        assert fetched["additional_details"]["transporter_name"] == "Live Update Transporter"
