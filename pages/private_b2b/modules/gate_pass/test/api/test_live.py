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
)


class TestLiveCRUD:
    @pytest.mark.api
    @pytest.mark.smoke
    def test_GP_L01_create_gate_pass(self, gp_api):
        log.info("GP-L01: Create gate pass via dedicated endpoint")
        payload = build_gp_payload()
        data = gp_api.create_gp(payload)
        assert data is not None, "Create should return data"
        entry_id = data.get("id")
        assert entry_id is not None, "Response should have an id"
        log.info(f"Created GP #{entry_id}")

    @pytest.mark.api
    @pytest.mark.smoke
    def test_GP_L02_get_gate_pass(self, gp_api):
        log.info("GP-L02: Fetch gate pass by ID")
        payload = build_gp_payload()
        data = gp_api.create_gp(payload)
        entry_id = data["id"]
        fetched = gp_api.get_gp(entry_id)
        assert fetched is not None, "Get should return data"
        assert fetched["id"] == entry_id, "Fetched ID should match"

    @pytest.mark.api
    def test_GP_L03_list_gate_passes(self, gp_api):
        log.info("GP-L03: List gate passes")
        result = gp_api.list_gps(page=1, page_size=5)
        assert result is not None, "List should return data"
        assert "screenmatlistingdata_set" in result, "List should contain listing data"

    @pytest.mark.api
    def test_GP_L04_create_then_verify_all_fields(self, gp_api):
        log.info("GP-L04: Create GP and verify all fields return correctly")
        payload = build_gp_payload(
            driver_name="Verify All Fields",
            distance=99.0,
            vehicle_no="MH12AB1234",
            driver_contact_no=9876543210,
        )
        data = gp_api.create_gp(payload)
        entry_id = data["id"]
        fetched = gp_api.get_gp(entry_id)
        assert fetched["driver_name"] == "Verify All Fields"
        assert fetched["distance"] == 99.0
        assert fetched["vehicle_no"] == "MH12AB1234"

    @pytest.mark.api
    def test_GP_L05_generated_transaction_ref_no(self, gp_api):
        log.info("GP-L05: transaction_ref_no is auto-generated (via GET after create)")
        payload = build_gp_payload()
        data = gp_api.create_gp(payload)
        assert data is not None
        entry_id = data["id"]
        fetched = gp_api.get_gp(entry_id)
        ref = fetched.get("transaction_ref_no")
        assert ref is not None, "transaction_ref_no should be auto-generated"
        assert ref.startswith("GP/"), f"Ref should start with 'GP/', got '{ref}'"

    @pytest.mark.api
    def test_GP_L06_gate_pass_details_in_response(self, gp_api):
        log.info("GP-L06: Verify gate_pass_details in response")
        payload = build_gp_payload(items=[
            {"item_ref_id": 5, "no_of_bags": 5, "quantity": 50.0, "base_uom": 4, "hsn_sac_no": 2},
            {"item_ref_id": 12, "no_of_bags": 3, "quantity": 30.0, "base_uom": 4, "hsn_sac_no": 2},
        ])
        data = gp_api.create_gp(payload)
        entry_id = data["id"]
        fetched = gp_api.get_gp(entry_id)
        details = fetched.get("gate_pass_details", [])
        assert len(details) == 2, f"Expected 2 details, got {len(details)}"
