import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.gate_pass.data.gate_pass_data import (
    build_gp_payload,
    generate_gp_payload,
    generate_gp_payloads,
    generate_random_fk_ids,
    SUPPLIER_IDS,
    ITEM_TYPE_IDS,
    DIVISION_IDS,
    DEPARTMENT_IDS,
    DELIVERY_TYPE_IDS,
    ITEM_IDS,
    AGENT_IDS,
    UOM_IDS,
    HSN_SAC_IDS,
    DEFAULT_FK_IDS,
)


class TestPayloadStructure:
    @pytest.mark.api
    def test_GP_P01_minimal_payload(self):
        log.info("GP-P01: Minimal payload has required keys")
        payload = build_gp_payload()
        assert "supplier_ref_id" in payload
        assert "item_type_ref_id" in payload
        assert "driver_name" in payload
        assert "in_time" in payload
        assert "distance" in payload
        assert "gate_pass_details" in payload

    @pytest.mark.api
    def test_GP_P02_full_payload(self):
        log.info("GP-P02: Payload with all optional fields")
        payload = build_gp_payload(
            agent_ref_id=15,
            delivery_type=29,
            parameter1=1,
            parameter2=2,
            vehicle_no="MH12AB1234",
            driver_contact_no=9876543210,
            out_time="2026-06-14T17:00:00Z",
            remark="Test remark",
            grn_check=True,
            qc_check=True,
        )
        assert payload["agent_ref_id"] == 15
        assert payload["delivery_type"] == 29
        assert payload["parameter2"] == 2
        assert payload["vehicle_no"] == "MH12AB1234"
        assert payload["driver_contact_no"] == 9876543210
        assert payload["grn_check"] is True
        assert payload["qc_check"] is True

    @pytest.mark.api
    def test_GP_P03_gate_pass_details_structure(self):
        log.info("GP-P03: gate_pass_details items have required fields")
        items = [
            {"item_ref_id": 5, "no_of_bags": 10.0, "quantity": 100.0, "base_uom": 4, "hsn_sac_no": 2},
        ]
        payload = build_gp_payload(items=items)
        details = payload["gate_pass_details"]
        assert len(details) == 1
        assert details[0]["item_ref_id"] == 5
        assert details[0]["quantity"] == 100.0
        assert details[0]["no_of_bags"] == 10.0

    @pytest.mark.api
    def test_GP_P04_supplier_ref_type(self):
        log.info("GP-P04: supplier_ref_type is Supplier")
        payload = build_gp_payload()
        assert payload.get("supplier_ref_type") == "Supplier"


class TestGeneratePayload:
    @pytest.mark.api
    def test_GP_G01_generate_has_mandatory_fields(self):
        log.info("GP-G01: Generated payload has all mandatory keys")
        payload = generate_gp_payload()
        assert "supplier_ref_id" in payload
        assert "driver_name" in payload
        assert "distance" in payload
        assert "in_time" in payload
        assert "gate_pass_details" in payload

    @pytest.mark.api
    def test_GP_G02_generate_valid_fk_ids(self):
        log.info("GP-G02: FK IDs in generated payload are valid")
        payload = generate_gp_payload()
        assert payload["supplier_ref_id"] in SUPPLIER_IDS
        assert payload["item_type_ref_id"] in ITEM_TYPE_IDS

    @pytest.mark.api
    def test_GP_G03_generate_multiple_payloads(self):
        log.info("GP-G03: generate_gp_payloads returns correct count")
        payloads = generate_gp_payloads(5)
        assert len(payloads) == 5

    @pytest.mark.api
    def test_GP_G04_generate_with_fk_overrides(self):
        log.info("GP-G04: FK overrides are applied")
        payload = generate_gp_payload(fk_overrides={"supplier_ref_id": 5})
        assert payload["supplier_ref_id"] == 5
