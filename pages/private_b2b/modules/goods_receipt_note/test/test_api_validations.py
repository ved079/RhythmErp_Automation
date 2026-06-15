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


def _payload_without(d: dict, key: str) -> dict:
    copy = dict(d)
    copy.pop(key, None)
    return copy


class TestCreateValidation:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_GRN_C01_empty_payload(self, grn_api):
        log.info("GRN-C01: Sending empty payload should be rejected")
        grn_api.create_and_expect_failure({})
        grn_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_GRN_C02_missing_supplier(self, grn_api):
        log.info("GRN-C02: Missing supplier_ref_id")
        payload = _payload_without(build_grn_payload(), "supplier_ref_id")
        grn_api.create_and_expect_failure(payload)
        grn_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend does not validate gate_pass_ref_id_id as required on dedicated endpoint")
    def test_GRN_C03_missing_gate_pass(self, grn_api):
        log.info("GRN-C03: Missing gate_pass_ref_id_id")
        payload = _payload_without(build_grn_payload(), "gate_pass_ref_id_id")
        grn_api.create_and_expect_failure(payload)
        grn_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend does not validate po_ref_id_id as required on dedicated endpoint")
    def test_GRN_C04_missing_po_ref(self, grn_api):
        log.info("GRN-C04: Missing po_ref_id_id")
        payload = _payload_without(build_grn_payload(), "po_ref_id_id")
        grn_api.create_and_expect_failure(payload)
        grn_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend does not validate grn_item_details as required on dedicated endpoint")
    def test_GRN_C05_missing_items(self, grn_api):
        log.info("GRN-C05: Missing grn_item_details")
        payload = _payload_without(build_grn_payload(), "grn_item_details")
        grn_api.create_and_expect_failure(payload)
        grn_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_GRN_C06_missing_txn_currency(self, grn_api):
        log.info("GRN-C06: Missing txn_currency (DB NOT NULL)")
        payload = _payload_without(build_grn_payload(), "txn_currency")
        grn_api.create_and_expect_failure(payload)
        grn_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend accepts empty grn_item_details list on dedicated endpoint")
    def test_GRN_C07_empty_items_list(self, grn_api):
        log.info("GRN-C07: Empty grn_item_details list")
        payload = build_grn_payload(items=[])
        grn_api.create_and_expect_failure(payload)
        grn_api.assert_validation_error(accept_statuses=[400, 500])


class TestOptionalFields:
    @pytest.mark.api
    def test_GRN_O01_optional_fields_omitted(self, grn_api):
        log.info("GRN-O01: Optional fields can be omitted")
        payload = build_grn_payload(
            additional_details={
                "vehicle_no": None,
                "transporter_name": None,
                "supplier_bill_date": None,
                "vehicle_receipt_no": None,
                "supplier_bill_no": None,
                "e_way_bill_no": None,
                "bill_of_entry_no": None,
                "remark": None,
            }
        )
        data = grn_api.create_grn(payload)
        assert data is not None, "Create should succeed with only required fields"

    @pytest.mark.api
    def test_GRN_O02_remark_accepted(self, grn_api):
        log.info("GRN-O02: Remark field is accepted")
        payload = build_grn_payload()
        payload["additional_details"]["remark"] = "Test GRN remark"
        data = grn_api.create_grn(payload)
        assert data is not None
        fetched = grn_api.get_grn(data["id"])
        assert fetched.get("additional_details", {}).get("remark") == "Test GRN remark"


class TestStepperItems:
    @pytest.mark.api
    def test_GRN_S01_single_item(self, grn_api):
        log.info("GRN-S01: Create GRN with single grn_item_details item")
        payload = build_grn_payload(items=[
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3, "received_qty": 10.0,
             "rate": 20.0, "no_of_bags": 1, "alternate_uom": 4, "accepted_qty": 10.0, "rejected_qty": 0.0},
        ])
        data = grn_api.create_grn(payload)
        assert data is not None, "Should create with 1 detail item"

    @pytest.mark.api
    def test_GRN_S02_multiple_items(self, grn_api):
        log.info("GRN-S02: Create GRN with multiple grn_item_details items")
        payload = build_grn_payload(items=[
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3, "received_qty": 10.0,
             "rate": 20.0, "no_of_bags": 1, "alternate_uom": 4, "accepted_qty": 10.0, "rejected_qty": 0.0},
            {"item_ref_id": 12, "hsn_sac_no": 2, "uom": 3, "received_qty": 5.0,
             "rate": 30.0, "no_of_bags": 1, "alternate_uom": 4, "accepted_qty": 5.0, "rejected_qty": 0.0},
        ])
        data = grn_api.create_grn(payload)
        assert data is not None, "Should create with 2 detail items"


class TestTransactionRef:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_GRN_T01_transaction_ref_format(self, grn_api):
        log.info("GRN-T01: transaction_ref_no has correct format")
        payload = build_grn_payload()
        data = grn_api.create_grn(payload)
        assert data is not None
        entry_id = data["id"]
        fetched = grn_api.get_grn(entry_id)
        ref = fetched.get("transaction_ref_no")
        assert ref is not None, "transaction_ref_no should be auto-generated"
        assert ref.startswith("GRN/"), f"Ref should start with GRN/: {ref}"

    @pytest.mark.api
    def test_GRN_T02_transaction_ref_increments(self, grn_api):
        log.info("GRN-T02: Consecutive creates produce incrementing refs")
        refs = []
        for i in range(2):
            payload = build_grn_payload()
            data = grn_api.create_grn(payload)
            assert data is not None
            entry_id = data["id"]
            fetched = grn_api.get_grn(entry_id)
            ref = fetched.get("transaction_ref_no")
            assert ref is not None
            refs.append(ref)
        assert refs[0] != refs[1], "Ref numbers should differ"
        log.info(f"Refs: {refs[0]}, {refs[1]}")


class TestBoundaries:
    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend rejects zero received_qty")
    def test_GRN_B01_zero_received_qty(self, grn_api):
        log.info("GRN-B01: Zero received_qty")
        payload = build_grn_payload(items=[
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3, "received_qty": 0.0,
             "rate": 20.0, "no_of_bags": 0, "alternate_uom": 4, "accepted_qty": 0.0, "rejected_qty": 0.0},
        ])
        data = grn_api.create_grn(payload)
        assert data is not None, "Zero qty should be accepted"

    @pytest.mark.api
    def test_GRN_B02_large_rate(self, grn_api):
        log.info("GRN-B02: Large rate value")
        payload = build_grn_payload(items=[
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3, "received_qty": 1.0,
             "rate": 999999.0, "no_of_bags": 1, "alternate_uom": 4, "accepted_qty": 1.0, "rejected_qty": 0.0},
        ])
        data = grn_api.create_grn(payload)
        assert data is not None, "Large rate should be accepted"

    @pytest.mark.api
    def test_GRN_B03_negative_received_qty(self, grn_api):
        log.info("GRN-B03: Negative received_qty should be rejected")
        payload = build_grn_payload(items=[
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3, "received_qty": -10.0,
             "rate": 20.0, "no_of_bags": 1, "alternate_uom": 4, "accepted_qty": -10.0, "rejected_qty": 0.0},
        ])
        status = grn_api.create_and_expect_failure(payload)
        grn_api.assert_validation_error(accept_statuses=[400, 500])


class TestSecurityVulnerabilities:
    @pytest.mark.api
    @pytest.mark.xfail(reason="BUG-GRN-SEC-01: Django DEBUG page leaks DATABASES, REDIS, SECRET_KEY settings")
    def test_GRN_SEC01_debug_mode_leak_on_invalid_gate_pass(self, grn_api):
        log.info("GRN-SEC01: DEBUG mode leak via invalid gate_pass_ref_id_id")
        from pages.private_b2b.modules.goods_receipt_note.api.endpoints import build_create_url
        payload = {
            "transaction_date": "2026-06-15", "supplier_ref_id": 1,
            "supplier_ref_type": "Supplier", "gate_pass_ref_id_id": 999999999,
            "po_ref_id_id": 200, "base_currency": 1, "txn_currency": 1,
            "conversion_rate": 1.0, "parameter1": 1, "parameter2": 1,
            "parameter5": 25, "parameter6": 1,
            "grn_item_details": [
                {"item_ref_id": 999999999, "hsn_sac_no": 2, "uom": 3,
                 "received_qty": 10.0, "rate": 20.0, "no_of_bags": 1,
                 "alternate_uom": 4, "accepted_qty": 10.0, "rejected_qty": 0.0}
            ],
        }
        url = build_create_url(grn_api.client.BASE_URL)
        resp = grn_api.client.session.post(url, json=payload, timeout=30)
        grn_api._last_response = resp
        grn_api._last_status = resp.status_code

        assert resp.status_code == 500
        text = resp.text
        leaks = []
        for keyword in ["DATABASES", "REDIS", "SECRET_KEY", "192.168",
                        "erp_procure", "CORE_URL", "envconfig", "Exception Type"]:
            if keyword in text:
                idx = text.index(keyword)
                leaks.append(f"{keyword} at pos {idx}")
        assert len(leaks) == 0, (
            f"CRITICAL: Django DEBUG page leaked {len(leaks)} settings!\n"
            f"Leaks found: {', '.join(leaks)}\n"
            f"Response size: {len(text)} bytes"
        )
