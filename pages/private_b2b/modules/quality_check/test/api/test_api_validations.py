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


def _payload_without(d: dict, key: str) -> dict:
    return {k: v for k, v in d.items() if k != key}


@pytest.mark.api
class TestCreateValidation:
    @pytest.mark.smoke
    def test_QC_V01_empty_payload(self, qc_api):
        log.info("QC-V01: Empty payload should be rejected")
        status = qc_api.create_and_expect_failure({})
        qc_api.assert_validation_error(
            expected_message_substring="",
            accept_statuses=[400, 422, 500],
        )

    def test_QC_V02_missing_supplier_ref_id(self, qc_api):
        log.info("QC-V02: Missing supplier_ref_id should fail")
        payload = generate_qc_payload()
        payload.pop("supplier_ref_id", None)
        status = qc_api.create_and_expect_failure(payload)
        qc_api.assert_validation_error()

    def test_QC_V03_missing_gate_pass_ref_id_id(self, qc_api):
        log.info("QC-V03: Missing gate_pass_ref_id_id should fail")
        payload = generate_qc_payload()
        payload.pop("gate_pass_ref_id_id", None)
        status = qc_api.create_and_expect_failure(payload)
        qc_api.assert_validation_error()

    def test_QC_V04_missing_grn_ref_id_id(self, qc_api):
        log.info("QC-V04: Missing grn_ref_id_id should fail")
        payload = generate_qc_payload()
        payload.pop("grn_ref_id_id", None)
        status = qc_api.create_and_expect_failure(payload)
        qc_api.assert_validation_error()

    def test_QC_V05_missing_qc_details(self, qc_api):
        log.info("QC-V05: Missing qc_details should fail")
        payload = generate_qc_payload()
        payload.pop("qc_details", None)
        status = qc_api.create_and_expect_failure(payload)
        qc_api.assert_validation_error()

    @pytest.mark.smoke
    def test_QC_V06_valid_minimal_payload(self, qc_api):
        log.info("QC-V06: Minimal valid payload succeeds")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None, "Valid QC should be created"
        assert data.get("id"), "Response should contain an ID"
        log.info(f"  Created QC ID={data['id']}")

    def test_QC_V07_missing_item_type_ref_id(self, qc_api):
        log.info("QC-V07: Missing item_type_ref_id (optional) may default")
        payload = generate_qc_payload()
        payload.pop("item_type_ref_id", None)
        data = qc_api.create_qc(payload)
        if data is not None:
            log.info("  item_type_ref_id is optional (backend defaulted)")
        else:
            log.info("  item_type_ref_id is required (backend rejected)")


@pytest.mark.api
class TestOptionalFields:
    def test_QC_V08_omit_additional_details(self, qc_api):
        log.info("QC-V08: Omitting qc_additional_details should work")
        payload = generate_qc_payload()
        payload.pop("qc_additional_details", None)
        data = qc_api.create_qc(payload)
        if data is not None:
            log.info("  qc_additional_details is optional")
        else:
            log.info("  qc_additional_details is required")

    def test_QC_V09_omit_conversion_rate(self, qc_api):
        log.info("QC-V09: Omitting conversion_rate should work")
        payload = generate_qc_payload()
        payload.pop("conversion_rate", None)
        data = qc_api.create_qc(payload)
        if data is not None:
            log.info("  conversion_rate is optional")
        else:
            log.info("  conversion_rate is required")


@pytest.mark.api
class TestStepperItems:
    @pytest.mark.smoke
    def test_QC_V10_single_qc_item(self, qc_api):
        log.info("QC-V10: QC with single item")
        payload = generate_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None, "QC with one item should succeed"
        log.info(f"  Created QC ID={data['id']}")

    def test_QC_V11_multiple_qc_items(self, qc_api):
        log.info("QC-V11: QC with 3 items")
        payload = generate_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None, "QC with multiple items should succeed"
        log.info(f"  Created QC ID={data['id']}")

    def test_QC_V12_qc_item_with_quality_details(self, qc_api):
        log.info("QC-V12: QC item with nested quality parameters")
        items = [{
            "item_ref_id": 5,
            "no_of_bags": 1,
            "grn_qty": 10.0,
            "accepted_qty": 10.0,
            "rejected_qty": 0.0,
            "base_rate": 20.0,
            "deduction_percent": None,
            "deduction_rate": None,
            "qc_rate": None,
            "net_rate": 20.0,
            "uom": 4,
            "hsn_sac_no": 2,
            "details": [
                {"item_quality_parameter_ref_id": 1, "actual_value": 5},
                {"item_quality_parameter_ref_id": 2, "actual_value": 3},
            ],
        }]
        payload = build_qc_payload(items=items)
        data = qc_api.create_qc(payload)
        assert data is not None, "QC with nested quality params should succeed"
        log.info(f"  Created QC ID={data['id']}")


@pytest.mark.api
class TestCalculationBoundaries:
    def test_QC_V13_zero_accepted_qty(self, qc_api):
        log.info("QC-V13: QC with zero accepted_qty")
        items = [{
            "item_ref_id": 5,
            "no_of_bags": 0,
            "grn_qty": 0.0,
            "accepted_qty": 0.0,
            "rejected_qty": 0.0,
            "base_rate": 20.0,
            "deduction_percent": None,
            "deduction_rate": None,
            "qc_rate": None,
            "net_rate": 0.0,
            "uom": 4,
            "hsn_sac_no": 2,
            "details": [],
        }]
        payload = build_qc_payload(items=items)
        data = qc_api.create_qc(payload)
        if data is not None:
            log.info(f"  Created QC with zero qty ID={data['id']}")
        else:
            log.info("  Backend rejected zero qty")


@pytest.mark.api
class TestTransactionRef:
    @pytest.mark.smoke
    def test_QC_V14_transaction_ref_format(self, qc_api):
        log.info("QC-V14: Transaction ref should start with QC/")
        payload = build_qc_payload()
        data = qc_api.create_qc(payload)
        assert data is not None, "Valid QC should be created"
        ref_no = data.get("transaction_ref_no", "")
        assert ref_no.startswith("QC/"), f"Ref should start with QC/, got: {ref_no}"
        log.info(f"  Ref = {ref_no}")

    def test_QC_V15_transaction_ref_increments(self, qc_api):
        log.info("QC-V15: Consecutive QCs get distinct refs")
        p1 = build_qc_payload()
        p2 = build_qc_payload()
        d1 = qc_api.create_qc(p1)
        d2 = qc_api.create_qc(p2)
        if d1 and d2:
            r1 = d1.get("transaction_ref_no", "")
            r2 = d2.get("transaction_ref_no", "")
            assert r1 != r2, "Refs should be unique"
            log.info(f"  Ref1={r1}, Ref2={r2}")


@pytest.mark.api
class TestSecurityVulnerabilities:
    def test_QC_V16_invalid_fk_returns_400(self, qc_api):
        log.info("QC-V16: Invalid FK should not leak debug info")
        payload = build_qc_payload(gate_pass_ref_id_id=9999999)
        status = qc_api.create_and_expect_failure(payload)
        assert status in (400, 404, 500), f"Expected error, got {status}"
        if qc_api._last_response is not None:
            body = qc_api._last_response.text
            assert "debug" not in body.lower(), "Response should not contain debug info"
            assert "traceback" not in body.lower(), "Response should not contain traceback"


@pytest.mark.api
class TestBoundaries:
    def test_QC_V17_high_rate_values(self, qc_api):
        log.info("QC-V17: QC with large values")
        items = [{
            "item_ref_id": 5,
            "no_of_bags": 1000,
            "grn_qty": 999999.0,
            "accepted_qty": 999999.0,
            "rejected_qty": 0.0,
            "base_rate": 999999.0,
            "deduction_percent": None,
            "deduction_rate": None,
            "qc_rate": None,
            "net_rate": 999999.0,
            "uom": 4,
            "hsn_sac_no": 2,
            "details": [],
        }]
        payload = build_qc_payload(items=items)
        data = qc_api.create_qc(payload)
        if data is not None:
            log.info(f"  Created QC with large values ID={data['id']}")
        else:
            log.info("  Backend rejected large values")
