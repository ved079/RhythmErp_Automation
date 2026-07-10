import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import time
import pytest

from common.logger import log
from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
    generate_grn_payload,
    build_grn_payload,
)


class TestUIBehaviour:
    @pytest.mark.smoke
    @pytest.mark.hybrid
    def test_GRN_UI01_api_create_ui_search_verify_row(self, grn_page, grn_api):
        log.info("GRN-UI01: Create GRN via API, search in UI, verify row")
        payload = generate_grn_payload(fk_overrides={"supplier_ref_id": 1})
        data = grn_api.create_grn(payload)
        entry_id = data["id"]
        entry = grn_api.get_grn(entry_id)
        ref_no = entry.get("transaction_ref_no", str(entry_id))

        grn_page.navigate_to_page()
        grn_page.click_refresh(retry_on_empty=True)
        found = grn_page.row_contains_text(ref_no)
        if not found:
            log.info(f"First row text: {grn_page.get_first_row_text()}")
        assert found, f"GRN {ref_no} should appear in the table"

    @pytest.mark.hybrid
    def test_GRN_UI02_view_popup_readonly(self, grn_page, grn_api):
        log.info("GRN-UI02: View popup should be read-only")
        payload = generate_grn_payload()
        data = grn_api.create_grn(payload)
        entry = grn_api.get_grn(data["id"])
        ref_no = entry.get("transaction_ref_no", str(data["id"]))

        grn_page.navigate_to_page()
        grn_page.click_refresh(retry_on_empty=True)
        grn_page.search_grn(ref_no)
        grn_page.click_view_first_row()
        time.sleep(2)
        readonly = grn_page.verify_view_popup_read_only()
        grn_page.close_popup()
        assert readonly, "View popup should not have Submit/Update buttons"

    @pytest.mark.hybrid
    def test_GRN_UI03_view_popup_crosscheck_with_api(self, grn_page, grn_api):
        log.info("GRN-UI03: Crosscheck UI popup data with API response")
        payload = build_grn_payload(
            additional_details={"vehicle_no": "Cross01",
                                "supplier_bill_date": "2026-06-15"}
        )
        data = grn_api.create_grn(payload)
        entry_id = data["id"]
        entry = grn_api.get_grn(entry_id)
        ref_no = entry.get("transaction_ref_no", str(entry_id))
        api_transporter = (entry.get("additional_details") or {}).get("transporter_name", "")

        grn_page.navigate_to_page()
        grn_page.click_refresh(retry_on_empty=True)
        grn_page.search_grn(ref_no)
        grn_page.click_view_first_row()
        time.sleep(2)
        ui_transporter = grn_page.get_form_field_value("Transporter Name") or ""
        grn_page.close_popup()
        if api_transporter:
            assert api_transporter in ui_transporter or ui_transporter in api_transporter, (
                f"UI transporter_name '{ui_transporter}' != API '{api_transporter}'"
            )

    @pytest.mark.hybrid
    def test_GRN_UI04_add_form_opens_and_cancels(self, grn_page):
        log.info("GRN-UI04: Add GRN form opens and cancels")
        grn_page.navigate_to_page()
        grn_page.open_add_form()
        assert grn_page._is_form_popup_open(), "Add form should be open"
        grn_page.force_close_form_popup()

    @pytest.mark.hybrid
    def test_GRN_UI05_negative_search_no_results(self, grn_page):
        log.info("GRN-UI05: Search non-existent GRN returns no rows")
        grn_page.navigate_to_page()
        grn_page.search_grn("ZZ-NONEXISTENT-999999")
        found = grn_page.row_contains_text("ZZ-NONEXISTENT-999999")
        assert not found, "Non-existent GRN should not be found"

    @pytest.mark.hybrid
    def test_GRN_UI06_refresh_loads_latest_data(self, grn_page, grn_api):
        log.info("GRN-UI06: Refresh loads newly created GRN")
        payload = generate_grn_payload()
        data = grn_api.create_grn(payload)
        entry_id = data["id"]
        entry = grn_api.get_grn(entry_id)
        ref_no = entry.get("transaction_ref_no", str(entry_id))

        grn_page.navigate_to_page()
        grn_page.click_refresh(retry_on_empty=True)
        found = grn_page.row_contains_text(ref_no)
        if not found:
            log.info(f"First row text: {grn_page.get_first_row_text()}")
        assert found, f"GRN {ref_no} should appear after refresh"

    @pytest.mark.hybrid
    def test_GRN_UI07_edit_form_opens(self, grn_page, grn_api):
        log.info("GRN-UI07: Edit form opens from row menu")
        payload = generate_grn_payload()
        data = grn_api.create_grn(payload)
        entry = grn_api.get_grn(data["id"])
        ref_no = entry.get("transaction_ref_no", str(data["id"]))

        grn_page.navigate_to_page()
        grn_page.click_refresh(retry_on_empty=True)
        grn_page.search_grn(ref_no)
        grn_page.edit_first_row()
        has_update = grn_page.has_update_button()
        grn_page.force_close_form_popup()
        assert has_update, "Edit form should have an Update button"
