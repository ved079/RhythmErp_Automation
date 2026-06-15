import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.quality_check.data.quality_check_data import (
    build_qc_payload,
    generate_qc_payload,
)


@pytest.mark.api
class TestQCLive:
    @pytest.mark.smoke
    def test_QC_L01_create_and_get(self, qc_api):
        log.info("QC-L01: Create QC and fetch by ID")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None, "Create should succeed"
        entry_id = data["id"]
        ref_no = data.get("transaction_ref_no", "N/A")
        log.info(f"  Created QC #{entry_id}, ref={ref_no}")

        fetched = qc_api.get_qc(entry_id)
        assert fetched is not None, "GET should succeed"
        assert fetched.get("id") == entry_id, "ID should match"
        log.info(f"  GET verified ID={fetched['id']}")

    def test_QC_L02_create_and_list(self, qc_api):
        log.info("QC-L02: List QCs")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        ref_no = data.get("transaction_ref_no", str(data["id"]))
        log.info(f"  Created QC ref={ref_no}")

        listing = qc_api.list_qcs()
        if listing:
            log.info(f"  List returned {len(list(listing.values())[0]) if isinstance(listing, dict) else 'OK'}")

    @pytest.mark.xfail(reason="QC PUT endpoint has server-side IntegrityError", strict=False)
    def test_QC_L03_create_update_get(self, qc_api):
        log.info("QC-L03: Create, update, and verify")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None
        entry_id = data["id"]

        updated = build_qc_payload(
            additional_details={"vehicle_number": "LiveTest", "driver_name": None, "remark": None},
        )
        update_result = qc_api.update_qc(entry_id, updated)
        assert update_result is not None, f"Update failed (status {qc_api._last_status})"
        log.info(f"  Update succeeded for QC {entry_id}")
        fetched = qc_api.get_qc(entry_id)
        assert fetched is not None
