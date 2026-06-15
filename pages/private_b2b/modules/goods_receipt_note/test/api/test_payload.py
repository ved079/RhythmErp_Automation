import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log


class TestGRNPayload:
    @pytest.mark.api
    def test_valid_payload_returns_201(self, grn_api, build_payload):
        log.info("GRN-PAYLOAD-01: Valid payload returns 201")
        payload = build_payload()
        data = grn_api.create_grn(payload)
        assert data is not None
        assert "id" in data
        assert data["id"] is not None

    @pytest.mark.api
    def test_payload_with_all_additional_details(self, grn_api, build_payload):
        log.info("GRN-PAYLOAD-02: Payload with all additional details fields")
        payload = build_payload(
            additional_details={
                "vehicle_no": "MH01AB1234",
                "vehicle_receipt_no": "REC-001",
                "transporter_name": "Test Transporter",
                "supplier_bill_no": "BILL-001",
                "supplier_bill_date": "2026-06-15",
                "e_way_bill_no": "EWB-001",
                "bill_of_entry_no": "BOE-001",
                "remark": "Full details test",
            }
        )
        data = grn_api.create_grn(payload)
        assert data is not None, "Should create with all additional details"

    @pytest.mark.api
    def test_payload_without_additional_details(self, grn_api, build_payload):
        log.info("GRN-PAYLOAD-03: Payload without additional details")
        payload = build_payload()
        del payload["additional_details"]
        data = grn_api.create_grn(payload)
        assert data is not None, "Should create without additional_details"

    @pytest.mark.api
    def test_payload_with_different_parameters(self, grn_api, build_payload):
        log.info("GRN-PAYLOAD-04: Payload with different parameter combinations")
        for param1 in [1, 2]:
            for param2 in [1, 2]:
                payload = build_payload(parameter1=param1, parameter2=param2)
                data = grn_api.create_grn(payload)
                assert data is not None, (
                    f"Should create with parameter1={param1}, parameter2={param2}"
                )
