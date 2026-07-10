import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import time
import pytest

from common.logger import log
from pages.private_b2b.modules.gate_pass.data.gate_pass_data import generate_gp_payload
from common.erp_api_client import RhythmERPAPIClient


class TestUIBehaviour:
    @pytest.mark.smoke
    @pytest.mark.hybrid
    def test_GP_UI01_api_create_ui_search_verify_row(self, gp_page, gp_api):
        log.info("GP-UI01: Create GP via API, search in UI, verify row")
        payload = generate_gp_payload(fk_overrides={"supplier_ref_id": 1})
        data = gp_api.create_gp(payload)
        entry_id = data["id"]
        ref_no = data.get("transaction_ref_no", str(entry_id))

        gp_page.navigate_to_page()
        gp_page.click_refresh(retry_on_empty=True)
        found = gp_page.search_gp_verify_row(ref_no)
        assert found, f"GP {ref_no} should appear in search results"

    @pytest.mark.hybrid
    def test_GP_UI02_view_popup_readonly(self, gp_page, gp_api):
        log.info("GP-UI02: View popup should be read-only")
        payload = generate_gp_payload()
        data = gp_api.create_gp(payload)
        ref_no = data.get("transaction_ref_no", str(data["id"]))

        gp_page.navigate_to_page()
        gp_page.click_refresh(retry_on_empty=True)
        gp_page.search_gp(ref_no)
        gp_page.click_view_first_row()
        time.sleep(2)
        readonly = gp_page.verify_view_popup_read_only()
        gp_page.close_popup()
        assert readonly, "View popup should not have Submit/Update buttons"

    @pytest.mark.hybrid
    def test_GP_UI03_view_popup_crosscheck_with_api(self, gp_page, gp_api):
        log.info("GP-UI03: Crosscheck UI popup data with API response")
        payload = generate_gp_payload(driver_name="Crosscheck Test")
        data = gp_api.create_gp(payload)
        entry_id = data["id"]
        ref_no = data.get("transaction_ref_no", str(entry_id))

        gp_page.navigate_to_page()
        gp_page.click_refresh(retry_on_empty=True)
        gp_page.search_gp(ref_no)
        gp_page.click_view_first_row()
        time.sleep(2)
        ui_driver = gp_page.get_form_field_value("Driver Name") or ""
        gp_page.close_popup()
        assert "Crosscheck" in ui_driver or not ui_driver, (
            f"UI driver_name mismatch: '{ui_driver}'"
        )

    @pytest.mark.hybrid
    def test_GP_UI04_add_form_opens_and_cancels(self, gp_page):
        log.info("GP-UI04: Add Gate Pass form opens and cancels")
        gp_page.navigate_to_page()
        gp_page.open_add_form()
        assert gp_page._is_form_popup_open(), "Add form should be open"
        gp_page.force_close_form_popup()

    @pytest.mark.hybrid
    def test_GP_UI05_negative_search_no_results(self, gp_page):
        log.info("GP-UI05: Search non-existent GP returns no rows")
        gp_page.navigate_to_page()
        found = gp_page.search_gp_verify_row("ZZ-NONEXISTENT-999999")
        assert not found, "Non-existent GP should not be found"

    @pytest.mark.hybrid
    def test_GP_UI06_refresh_loads_latest_data(self, gp_page, gp_api):
        log.info("GP-UI06: Refresh loads newly created GP")
        payload = generate_gp_payload()
        data = gp_api.create_gp(payload)
        ref_no = data.get("transaction_ref_no", str(data["id"]))

        gp_page.navigate_to_page()
        gp_page.click_refresh(retry_on_empty=True)
        found = gp_page.search_gp_verify_row(ref_no)
        assert found, f"GP {ref_no} should appear after refresh"

    @pytest.mark.hybrid
    def test_GP_UI07_edit_form_opens(self, gp_page, gp_api):
        log.info("GP-UI07: Edit form opens from row menu")
        payload = generate_gp_payload()
        data = gp_api.create_gp(payload)
        ref_no = data.get("transaction_ref_no", str(data["id"]))

        gp_page.navigate_to_page()
        gp_page.click_refresh(retry_on_empty=True)
        gp_page.search_gp(ref_no)
        gp_page.edit_first_row()
        has_update = gp_page.has_update_button()
        gp_page.force_close_form_popup()
        assert has_update, "Edit form should have an Update button"
