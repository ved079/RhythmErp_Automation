import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import time
import pytest

from common.logger import log
from pages.private_b2b.modules.quality_check.data.quality_check_data import (
    generate_qc_payload,
    build_qc_payload,
)


class TestUIBehaviour:
    @pytest.mark.smoke
    @pytest.mark.hybrid
    def test_QC_UI01_api_create_ui_search_verify_row(self, qc_page, qc_api):
        log.info("QC-UI01: Create QC via API, search in UI, verify row")
        payload = generate_qc_payload(fk_overrides={"supplier_ref_id": 1})
        data = qc_api.create_qc(payload)
        entry_id = data["id"]
        entry = qc_api.get_qc(entry_id)
        ref_no = entry.get("transaction_ref_no", str(entry_id))

        qc_page.navigate_to_page()
        qc_page.click_refresh(retry_on_empty=True)
        found = qc_page.row_contains_text(ref_no)
        if not found:
            log.info(f"First row text: {qc_page.get_first_row_text()}")
        assert found, f"QC {ref_no} should appear in the table"

    @pytest.mark.hybrid
    def test_QC_UI02_view_popup_readonly(self, qc_page, qc_api):
        log.info("QC-UI02: View popup should be read-only")
        payload = generate_qc_payload()
        data = qc_api.create_qc(payload)
        entry = qc_api.get_qc(data["id"])
        ref_no = entry.get("transaction_ref_no", str(data["id"]))

        qc_page.navigate_to_page()
        qc_page.click_refresh(retry_on_empty=True)
        qc_page.search_qc(ref_no)
        qc_page.click_view_first_row()
        time.sleep(2)
        readonly = qc_page.verify_view_popup_read_only()
        qc_page.close_popup()
        assert readonly, "View popup should not have Submit/Update buttons"

    @pytest.mark.hybrid
    def test_QC_UI03_view_popup_crosscheck_with_api(self, qc_page, qc_api):
        log.info("QC-UI03: Crosscheck UI popup data with API response")
        payload = build_qc_payload(
            additional_details={"vehicle_number": "Cross01",
                                "driver_name": None,
                                "remark": "Crosscheck test"}
        )
        data = qc_api.create_qc(payload)
        entry = qc_api.get_qc(data["id"])
        ref_no = entry.get("transaction_ref_no", str(data["id"]))
        api_vehicle = (entry.get("qc_additional_details") or {}).get("vehicle_number", "")

        qc_page.navigate_to_page()
        qc_page.click_refresh(retry_on_empty=True)
        qc_page.search_qc(ref_no)
        qc_page.click_view_first_row()
        time.sleep(2)
        ui_vehicle = qc_page.get_form_field_value("Vehicle Number") or ""
        qc_page.close_popup()
        if api_vehicle:
            assert api_vehicle in ui_vehicle or ui_vehicle in api_vehicle, (
                f"UI vehicle '{ui_vehicle}' != API '{api_vehicle}'"
            )

    @pytest.mark.hybrid
    def test_QC_UI04_add_form_opens_and_cancels(self, qc_page):
        log.info("QC-UI04: Add QC form opens and cancels")
        qc_page.navigate_to_page()
        qc_page.open_add_form()
        assert qc_page._is_form_popup_open(), "Add form should be open"
        qc_page.force_close_form_popup()

    @pytest.mark.hybrid
    def test_QC_UI05_negative_search_no_results(self, qc_page):
        log.info("QC-UI05: Search non-existent QC returns no rows")
        qc_page.navigate_to_page()
        qc_page.search_qc("ZZ-NONEXISTENT-999999")
        found = qc_page.row_contains_text("ZZ-NONEXISTENT-999999")
        assert not found, "Non-existent QC should not be found"

    @pytest.mark.hybrid
    def test_QC_UI06_refresh_loads_latest_data(self, qc_page, qc_api):
        log.info("QC-UI06: Refresh loads newly created QC")
        payload = generate_qc_payload()
        data = qc_api.create_qc(payload)
        entry = qc_api.get_qc(data["id"])
        ref_no = entry.get("transaction_ref_no", str(data["id"]))

        qc_page.navigate_to_page()
        qc_page.click_refresh(retry_on_empty=True)
        found = qc_page.row_contains_text(ref_no)
        if not found:
            log.info(f"First row text: {qc_page.get_first_row_text()}")
        assert found, f"QC {ref_no} should appear after refresh"

    @pytest.mark.hybrid
    def test_QC_UI07_edit_form_opens(self, qc_page, qc_api):
        log.info("QC-UI07: Edit form opens from row menu")
        payload = generate_qc_payload()
        data = qc_api.create_qc(payload)
        entry = qc_api.get_qc(data["id"])
        ref_no = entry.get("transaction_ref_no", str(data["id"]))

        qc_page.navigate_to_page()
        qc_page.click_refresh(retry_on_empty=True)
        qc_page.search_qc(ref_no)
        qc_page.edit_first_row()
        has_update = qc_page.has_update_button()
        qc_page.force_close_form_popup()
        assert has_update, "Edit form should have an Update button"
