import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.gate_pass.data.gate_pass_data import (
    build_gp_payload,
    generate_gp_payload,
)


def _payload_without(d: dict, key: str) -> dict:
    """Return a copy of dict with key removed."""
    copy = dict(d)
    copy.pop(key, None)
    return copy


class TestCreateValidation:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_GP_C01_empty_payload(self, gp_api):
        log.info("GP-C01: Sending empty payload should be rejected")
        gp_api.create_and_expect_failure({})
        gp_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_GP_C02_missing_supplier(self, gp_api):
        log.info("GP-C02: Missing supplier_ref_id")
        payload = _payload_without(build_gp_payload(), "supplier_ref_id")
        gp_api.create_and_expect_failure(payload)
        gp_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_GP_C03_missing_item_type(self, gp_api):
        log.info("GP-C03: Missing item_type_ref_id")
        payload = _payload_without(build_gp_payload(), "item_type_ref_id")
        gp_api.create_and_expect_failure(payload)
        gp_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend does not validate driver_name as required on dedicated endpoint")
    def test_GP_C04_missing_driver_name(self, gp_api):
        log.info("GP-C04: Missing driver_name")
        payload = _payload_without(build_gp_payload(), "driver_name")
        gp_api.create_and_expect_failure(payload)
        gp_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend does not validate distance as required on dedicated endpoint")
    def test_GP_C05_missing_distance(self, gp_api):
        log.info("GP-C05: Missing distance")
        payload = _payload_without(build_gp_payload(), "distance")
        gp_api.create_and_expect_failure(payload)
        gp_api.assert_validation_error(accept_statuses=[400, 500])

    @pytest.mark.api
    def test_GP_C06_missing_in_time(self, gp_api):
        log.info("GP-C06: Missing in_time")
        payload = _payload_without(build_gp_payload(), "in_time")
        gp_api.create_and_expect_failure(payload)
        gp_api.assert_validation_error(accept_statuses=[400, 500])


class TestOptionalFields:
    @pytest.mark.api
    def test_GP_O01_optional_fields_omitted(self, gp_api):
        log.info("GP-O01: Optional fields can be omitted")
        payload = build_gp_payload(
            agent_ref_id=None,
            vehicle_no=None,
            driver_contact_no=None,
            parameter2=None,
            parameter5=None,
            parameter6=None,
            out_time=None,
            remark=None,
        )
        data = gp_api.create_gp(payload)
        assert data is not None, "Create should succeed with only required fields"

    @pytest.mark.api
    def test_GP_O02_remark_accepted(self, gp_api):
        log.info("GP-O02: Remark field is accepted")
        payload = build_gp_payload(remark="Test remark for GP")
        data = gp_api.create_gp(payload)
        assert data is not None
        fetched = gp_api.get_gp(data["id"])
        assert fetched.get("remark") == "Test remark for GP"


class TestStepperItems:
    @pytest.mark.api
    def test_GP_S01_single_stepper_item(self, gp_api):
        log.info("GP-S01: Create GP with single gate_pass_details item")
        payload = build_gp_payload(items=[
            {"item_ref_id": 5, "no_of_bags": 10, "quantity": 100.0, "base_uom": 4, "hsn_sac_no": 2},
        ])
        data = gp_api.create_gp(payload)
        assert data is not None, "Should create with 1 detail item"

    @pytest.mark.api
    def test_GP_S02_multiple_stepper_items(self, gp_api):
        log.info("GP-S02: Create GP with multiple gate_pass_details items")
        payload = build_gp_payload(items=[
            {"item_ref_id": 5, "no_of_bags": 5, "quantity": 50.0, "base_uom": 4, "hsn_sac_no": 2},
            {"item_ref_id": 12, "no_of_bags": 3, "quantity": 30.0, "base_uom": 4, "hsn_sac_no": 2},
            {"item_ref_id": 7, "no_of_bags": 8, "quantity": 80.0, "base_uom": 4, "hsn_sac_no": 2},
        ])
        data = gp_api.create_gp(payload)
        assert data is not None, "Should create with 3 detail items"


class TestTransactionRef:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_GP_T01_transaction_ref_format(self, gp_api):
        log.info("GP-T01: transaction_ref_no has correct format (via GET after create)")
        payload = build_gp_payload()
        data = gp_api.create_gp(payload)
        assert data is not None
        entry_id = data["id"]
        fetched = gp_api.get_gp(entry_id)
        ref = fetched.get("transaction_ref_no")
        assert ref is not None, "transaction_ref_no should be auto-generated"
        parts = ref.split("/")
        assert len(parts) >= 2, f"Ref should have at least 2 parts: {ref}"

    @pytest.mark.api
    def test_GP_T02_transaction_ref_increments(self, gp_api):
        log.info("GP-T02: Consecutive creates produce incrementing refs")
        refs = []
        for i in range(2):
            payload = build_gp_payload(driver_name=f"Inc Test {i}")
            data = gp_api.create_gp(payload)
            assert data is not None
            entry_id = data["id"]
            fetched = gp_api.get_gp(entry_id)
            ref = fetched.get("transaction_ref_no")
            assert ref is not None
            refs.append(ref)
        assert refs[0] != refs[1], "Ref numbers should differ"
        log.info(f"Refs: {refs[0]}, {refs[1]}")


class TestBoundaries:
    @pytest.mark.api
    @pytest.mark.xfail(reason="Backend rejects zero distance: 'does not match required pattern'")
    def test_GP_B01_zero_distance(self, gp_api):
        log.info("GP-B01: Zero distance")
        payload = build_gp_payload(distance=0)
        data = gp_api.create_gp(payload)
        assert data is not None, "Zero distance should be accepted"

    @pytest.mark.api
    def test_GP_B02_large_distance(self, gp_api):
        log.info("GP-B02: Large distance value")
        payload = build_gp_payload(distance=99999)
        data = gp_api.create_gp(payload)
        assert data is not None, "Large distance should be accepted"
        fetched = gp_api.get_gp(data["id"])
        assert fetched["distance"] == 99999

    @pytest.mark.api
    def test_GP_B03_large_quantity(self, gp_api):
        log.info("GP-B03: Large quantity in gate_pass_details")
        payload = build_gp_payload(items=[
            {"item_ref_id": 5, "no_of_bags": 1000, "quantity": 99999.0, "base_uom": 4, "hsn_sac_no": 2},
        ])
        data = gp_api.create_gp(payload)
        assert data is not None, "Large qty should be accepted"

    @pytest.mark.api
    def test_GP_B04_negative_distance(self, gp_api):
        log.info("GP-B04: Negative distance should be rejected")
        payload = build_gp_payload(distance=-50)
        status = gp_api.create_and_expect_failure(payload)
        gp_api.assert_validation_error(accept_statuses=[400, 500])
