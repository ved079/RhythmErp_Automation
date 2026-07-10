import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
    build_grn_payload,
    generate_grn_payload,
)


class TestUpdateGRN:
    @pytest.mark.update
    @pytest.mark.api
    def test_GRN_U01_update_transporter_name(self, grn_api):
        log.info("GRN-U01: Update transporter_name")
        payload = build_grn_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]

        update_payload = build_grn_payload()
        update_payload["additional_details"]["transporter_name"] = "Updated Transporter"
        result = grn_api.update_grn(entry_id, update_payload)
        assert result is not None, "Update should succeed"

        fetched = grn_api.get_grn(entry_id)
        assert fetched["additional_details"]["transporter_name"] == "Updated Transporter"

    @pytest.mark.update
    @pytest.mark.api
    def test_GRN_U02_update_vehicle_no(self, grn_api):
        log.info("GRN-U02: Update vehicle_no")
        payload = build_grn_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]

        update_payload = build_grn_payload()
        update_payload["additional_details"]["vehicle_no"] = "MH99XY5678"
        result = grn_api.update_grn(entry_id, update_payload)
        assert result is not None

        fetched = grn_api.get_grn(entry_id)
        assert fetched["additional_details"]["vehicle_no"] == "MH99XY5678"

    @pytest.mark.update
    @pytest.mark.api
    def test_GRN_U03_update_grn_item_details(self, grn_api):
        log.info("GRN-U03: Update grn_item_details items")
        payload = build_grn_payload(items=[
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3, "received_qty": 10.0,
             "rate": 20.0, "no_of_bags": 1, "alternate_uom": 4, "accepted_qty": 10.0, "rejected_qty": 0.0},
        ])
        data = grn_api.create_grn(payload)
        entry_id = data["id"]

        update_payload = build_grn_payload(items=[
            {"item_ref_id": 12, "hsn_sac_no": 2, "uom": 3, "received_qty": 5.0,
             "rate": 30.0, "no_of_bags": 2, "alternate_uom": 4, "accepted_qty": 5.0, "rejected_qty": 0.0},
        ])
        result = grn_api.update_grn(entry_id, update_payload)
        assert result is not None

        fetched = grn_api.get_grn(entry_id)
        details = fetched.get("grn_item_details", [])
        assert len(details) >= 1
        assert details[0]["item_ref_id"] == 12

    @pytest.mark.update
    @pytest.mark.api
    def test_GRN_U04_update_succeeds_with_full_payload(self, grn_api):
        log.info("GRN-U04: Full payload update")
        payload = build_grn_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]

        update_payload = build_grn_payload(
            additional_details={
                "vehicle_no": "MH99XY5678",
                "transporter_name": "Full Update Transporter",
                "supplier_bill_date": "2026-06-15",
                "vehicle_receipt_no": "REC-999",
                "supplier_bill_no": "BILL-UPDATE",
                "e_way_bill_no": "EWB-UPDATE",
                "bill_of_entry_no": "BOE-UPDATE",
                "remark": "Updated via full payload",
            }
        )
        result = grn_api.update_grn(entry_id, update_payload)
        assert result is not None

    @pytest.mark.update
    @pytest.mark.api
    def test_GRN_U05_update_nonexistent_grn(self, grn_api):
        log.info("GRN-U05: Update non-existent GRN")
        payload = build_grn_payload()
        result = grn_api.update_grn(999999, payload)
        assert result is None, "Should fail for non-existent ID"
        assert grn_api._last_status in (404, 400, 424, 500), (
            f"Unexpected status: {grn_api._last_status}"
        )

    @pytest.mark.update
    @pytest.mark.api
    def test_GRN_U06_update_returns_updated_status(self, grn_api):
        log.info("GRN-U06: Update returns success message")
        payload = build_grn_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]

        update_payload = build_grn_payload()
        result = grn_api.update_grn(entry_id, update_payload)
        assert result is not None
        status_text = str(result.get("status", ""))
        assert "updated" in status_text.lower() or "success" in status_text.lower(), (
            f"Response should indicate update: {result}"
        )

    @pytest.mark.update
    @pytest.mark.api
    @pytest.mark.xfail(reason="BUG-GRN-U07: PUT with empty grn_item_details clears existing items (data loss)")
    def test_GRN_U07_update_with_empty_grn_item_details(self, grn_api):
        log.info("GRN-U07: Update with empty grn_item_details")
        payload = build_grn_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]

        update_payload = build_grn_payload(items=[])
        result = grn_api.update_grn(entry_id, update_payload)

        if result is None and grn_api._last_status in (400, 500):
            log.info("Backend rejected empty items — acceptable")
            return

        fetched = grn_api.get_grn(entry_id)
        after_items = fetched.get("grn_item_details", [])
        assert len(after_items) >= 1, (
            "Update with empty grn_item_details should not clear existing items"
        )
