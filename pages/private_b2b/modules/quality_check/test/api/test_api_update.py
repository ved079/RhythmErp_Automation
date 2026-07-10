import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.quality_check.data.quality_check_data import (
    build_qc_payload,
    generate_qc_payload,
    generate_random_fk_ids,
)


@pytest.mark.update
class TestUpdateQC:
    @pytest.mark.smoke
    def test_QC_U01_update_driver_name(self, qc_api):
        log.info("QC-U01: Update driver_name")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None, "Create should succeed"
        entry_id = data["id"]

        updated = build_qc_payload()
        updated["qc_additional_details"]["driver_name"] = "Updated Driver"
        result = qc_api.update_qc(entry_id, updated)
        assert result is not None, "Update should succeed"

        fetched = qc_api.get_qc(entry_id)
        if fetched:
            add = fetched.get("qc_additional_details", {}) or {}
            log.info(f"  driver_name = {add.get('driver_name')}")

    def test_QC_U02_update_vehicle_number(self, qc_api):
        log.info("QC-U02: Update vehicle_number")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        entry_id = data["id"]

        updated = build_qc_payload()
        updated["qc_additional_details"]["vehicle_number"] = "MH99XX9999"
        result = qc_api.update_qc(entry_id, updated)
        assert result is not None, "Update should succeed"

        fetched = qc_api.get_qc(entry_id)
        if fetched:
            add = fetched.get("qc_additional_details", {}) or {}
            log.info(f"  vehicle_number = {add.get('vehicle_number')}")

    def test_QC_U03_update_qc_items(self, qc_api):
        log.info("QC-U03: Update QC items")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        entry_id = data["id"]

        new_items = [{
            "item_ref_id": 5,
            "no_of_bags": 5,
            "grn_qty": 50.0,
            "accepted_qty": 50.0,
            "rejected_qty": 0.0,
            "base_rate": 25.0,
            "deduction_percent": None,
            "deduction_rate": None,
            "qc_rate": None,
            "net_rate": 25.0,
            "uom": 4,
            "hsn_sac_no": 2,
            "details": [
                {"item_quality_parameter_ref_id": 1, "actual_value": 2},
            ],
        }]
        updated = build_qc_payload(items=new_items)
        result = qc_api.update_qc(entry_id, updated)
        assert result is not None, "Update items should succeed"

    def test_QC_U04_full_payload_update(self, qc_api):
        log.info("QC-U04: Full payload update")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        entry_id = data["id"]

        full = build_qc_payload(
            gate_pass_ref_id_id=505,
            grn_ref_id_id=146,
            additional_details={"vehicle_number": "MH14AB1234", "driver_name": "FullUpdate", "remark": "test"},
        )
        result = qc_api.update_qc(entry_id, full)
        assert result is not None, "Full update should succeed"
        log.info(f"  Update successful for QC {entry_id}")

    def test_QC_U05_update_nonexistent(self, qc_api):
        log.info("QC-U05: Update non-existent QC should fail")
        payload = build_qc_payload()
        result = qc_api.update_qc(9999999, payload)
        assert result is None, "Non-existent QC update should fail"
        log.info(f"  Got status {qc_api._last_status}")

    def test_QC_U06_update_returns_200(self, qc_api):
        log.info("QC-U06: Update should return 200/201")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        entry_id = data["id"]

        updated = build_qc_payload()
        result = qc_api.update_qc(entry_id, updated)
        assert result is not None, "Update should return data"
        log.info(f"  Update returned {list(result.keys())}")

    def test_QC_U07_empty_items_edge(self, qc_api):
        log.info("QC-U07: Update with empty qc_details")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        entry_id = data["id"]

        updated = build_qc_payload(items=[])
        result = qc_api.update_qc(entry_id, updated)
        if result is not None:
            log.info("  Backend accepted empty items")
        else:
            log.info("  Backend rejected empty items")
