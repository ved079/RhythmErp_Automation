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
class TestQCPayload:
    def test_QC_P01_minimal_payload_structure(self):
        log.info("QC-P01: Minimal payload has required fields")
        payload = build_qc_payload()
        assert "supplier_ref_id" in payload
        assert "gate_pass_ref_id_id" in payload
        assert "grn_ref_id_id" in payload
        assert "qc_details" in payload
        assert isinstance(payload["qc_details"], list)
        assert len(payload["qc_details"]) > 0
        log.info(f"  Payload has {len(payload['qc_details'])} item(s)")

    def test_QC_P02_full_payload_structure(self):
        log.info("QC-P02: Full payload has all expected fields")
        payload = build_qc_payload(
            gate_pass_ref_id_id=505,
            grn_ref_id_id=146,
            additional_details={"vehicle_number": "MH14KK2533",
                                "driver_name": "Test",
                                "remark": None},
        )
        assert "supplier_ref_id" in payload
        assert "gate_pass_ref_id_id" in payload
        assert "grn_ref_id_id" in payload
        assert "qc_additional_details" in payload
        assert "qc_details" in payload
        assert payload["base_currency"] is not None
        assert payload["txn_currency"] is not None

    def test_QC_P03_item_has_quality_details(self):
        log.info("QC-P03: Items contain nested quality parameters")
        payload = build_qc_payload()
        for item in payload["qc_details"]:
            assert "details" in item, "Each item should have quality details"
            assert isinstance(item["details"], list), "Details should be a list"
            assert len(item["details"]) > 0, "Should have at least one quality param"
            for d in item["details"]:
                assert "item_quality_parameter_ref_id" in d
                assert "actual_value" in d

    def test_QC_P04_sendback_omitted(self):
        log.info("QC-P04: sendback not required in payload")
        payload = build_qc_payload()
        assert "sendback" not in payload, "sendback should not be in payload"
