import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.gate_pass.data.gate_pass_data import build_gp_payload, generate_gp_payload


class TestUpdateGP:
    @pytest.mark.update
    @pytest.mark.api
    def test_GP_U01_update_driver_name(self, gp_api):
        log.info("GP-U01: Update driver_name")
        payload = build_gp_payload(driver_name="Original Driver")
        data = gp_api.create_gp(payload)
        entry_id = data["id"]

        update_payload = build_gp_payload(driver_name="Updated Driver")
        result = gp_api.update_gp(entry_id, update_payload)
        assert result is not None, "Update should succeed"

        fetched = gp_api.get_gp(entry_id)
        assert fetched["driver_name"] == "Updated Driver"

    @pytest.mark.update
    @pytest.mark.api
    def test_GP_U02_update_distance(self, gp_api):
        log.info("GP-U02: Update distance")
        payload = build_gp_payload(distance=50)
        data = gp_api.create_gp(payload)
        entry_id = data["id"]

        update_payload = build_gp_payload(distance=200)
        result = gp_api.update_gp(entry_id, update_payload)
        assert result is not None

        fetched = gp_api.get_gp(entry_id)
        assert fetched["distance"] == 200

    @pytest.mark.update
    @pytest.mark.api
    def test_GP_U03_update_vehicle_no(self, gp_api):
        log.info("GP-U03: Update vehicle_no")
        payload = build_gp_payload(vehicle_no="MH01AB1234")
        data = gp_api.create_gp(payload)
        entry_id = data["id"]

        update_payload = build_gp_payload(vehicle_no="MH99XY5678")
        result = gp_api.update_gp(entry_id, update_payload)
        assert result is not None

        fetched = gp_api.get_gp(entry_id)
        assert fetched["vehicle_no"] == "MH99XY5678"

    @pytest.mark.update
    @pytest.mark.api
    def test_GP_U04_update_gate_pass_details(self, gp_api):
        log.info("GP-U04: Update gate_pass_details items")
        payload = build_gp_payload(items=[
            {"item_ref_id": 5, "no_of_bags": 10, "quantity": 100.0, "base_uom": 4, "hsn_sac_no": 2},
        ])
        data = gp_api.create_gp(payload)
        entry_id = data["id"]

        update_payload = build_gp_payload(items=[
            {"item_ref_id": 12, "no_of_bags": 5, "quantity": 50.0, "base_uom": 4, "hsn_sac_no": 2},
        ])
        result = gp_api.update_gp(entry_id, update_payload)
        assert result is not None

        fetched = gp_api.get_gp(entry_id)
        details = fetched.get("gate_pass_details", [])
        assert len(details) >= 1
        assert details[0]["item_ref_id"] == 12

    @pytest.mark.update
    @pytest.mark.api
    def test_GP_U05_update_succeeds_with_full_payload(self, gp_api):
        log.info("GP-U05: Full payload update")
        payload = build_gp_payload(
            driver_name="Initial",
            vehicle_no="MH01AB1234",
            distance=50,
        )
        data = gp_api.create_gp(payload)
        entry_id = data["id"]

        update_payload = build_gp_payload(
            driver_name="Full Update",
            vehicle_no="MH99XY5678",
            distance=999,
            remark="Updated via full payload",
        )
        result = gp_api.update_gp(entry_id, update_payload)
        assert result is not None

    @pytest.mark.update
    @pytest.mark.api
    def test_GP_U06_update_nonexistent_gp(self, gp_api):
        log.info("GP-U06: Update non-existent GP")
        payload = build_gp_payload()
        result = gp_api.update_gp(999999, payload)
        assert result is None, "Should fail for non-existent ID"
        assert gp_api._last_status in (404, 400, 424, 500), (
            f"Unexpected status: {gp_api._last_status}"
        )

    @pytest.mark.update
    @pytest.mark.api
    def test_GP_U07_update_returns_updated_status(self, gp_api):
        log.info("GP-U07: Update returns success message")
        payload = build_gp_payload()
        data = gp_api.create_gp(payload)
        entry_id = data["id"]

        update_payload = build_gp_payload()
        result = gp_api.update_gp(entry_id, update_payload)
        assert result is not None
        status_text = str(result.get("status", ""))
        assert "updated" in status_text.lower() or "success" in status_text.lower(), (
            f"Response should indicate update: {result}"
        )

    @pytest.mark.update
    @pytest.mark.api
    def test_GP_U08_update_supplier_changes_data(self, gp_api):
        log.info("GP-U08: Update supplier")
        payload = build_gp_payload(supplier_ref_id=1)
        data = gp_api.create_gp(payload)
        entry_id = data["id"]

        update_payload = build_gp_payload(supplier_ref_id=2)
        result = gp_api.update_gp(entry_id, update_payload)
        assert result is not None

        fetched = gp_api.get_gp(entry_id)
        assert fetched["supplier_ref_id"] == 2

    @pytest.mark.update
    @pytest.mark.api
    @pytest.mark.xfail(reason="BUG-GP-24: PUT with empty gate_pass_details clears existing items (data loss)")
    def test_GP_U09_update_with_empty_gate_pass_details(self, gp_api):
        log.info("GP-U09: Update with empty gate_pass_details (data-loss check)")
        payload = generate_gp_payload()
        data = gp_api.create_gp(payload)
        entry_id = data["id"]

        fetched_initial = gp_api.get_gp(entry_id)
        initial_items = fetched_initial.get("gate_pass_details", [])
        assert len(initial_items) >= 1, "Should have at least 1 detail item"

        update_payload = build_gp_payload(items=[])
        result = gp_api.update_gp(entry_id, update_payload)

        if result is None and gp_api._last_status in (400, 500):
            return

        fetched_after = gp_api.get_gp(entry_id)
        after_items = fetched_after.get("gate_pass_details", [])
        assert len(after_items) >= 1, (
            "BUG: Update with empty gate_pass_details cleared existing items. "
            f"Expected at least 1 detail, got {len(after_items)}"
        )
