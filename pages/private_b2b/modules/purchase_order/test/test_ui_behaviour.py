import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    generate_po_payload,
    build_po_payload,
)


class TestUIBehaviour:
    """UI behaviour tests. Data is created via API — Selenium only checks rendering."""

    def _create_and_get_ref(self, po_api, payload=None, **overrides):
        if payload is None:
            payload = generate_po_payload(fk_overrides=overrides)
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        return entry_id, entry.get("transaction_ref_no", "")

    @pytest.mark.smoke
    @pytest.mark.hybrid
    def test_UI01_api_create_ui_search_verify_row(self, po_page, po_api):
        log.info("UI-01: API creates PO → UI search finds it with correct row")
        page = po_page
        entry_id, ref_no = self._create_and_get_ref(po_api, supplier_ref_id=1,
            parameter2=1, parameter3=25, parameter4=1)

        if page.get_table_row_count() == 0:
            page.navigate_to_page()
        page.click_refresh(retry_on_empty=True)
        found = page.search_po_verify_row(ref_no)
        assert found, f"UI search failed to find or verify PO ref={ref_no}"

    @pytest.mark.hybrid
    def test_UI02_view_popup_readonly(self, po_page, po_api):
        log.info("UI-02: View popup has no Submit/Update buttons")
        page = po_page
        entry_id, ref_no = self._create_and_get_ref(po_api, supplier_ref_id=1,
            parameter2=1, parameter3=25, parameter4=1)

        page.click_refresh()
        found = page.search_po(ref_no)
        assert found, f"Search failed for ref={ref_no}"
        page.click_view_first_row()
        read_only = page.verify_view_popup_read_only()
        assert read_only, "View popup should be read-only"
        page.close_popup()

    @pytest.mark.hybrid
    def test_UI03_view_popup_crosscheck_with_api(self, po_page, po_api):
        log.info("UI-03: View popup values cross-checked against API response")
        page = po_page
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[{"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                    "quantity": 10.0, "rate": 100.0,
                    "expected_delivery_date": "2026-06-20"}],
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        api_ref_no = entry.get("transaction_ref_no", "")
        api_total = str(float(entry.get("txn_currency_total_amount", 0)))

        page.click_refresh()
        found = page.search_po(api_ref_no)
        assert found, f"Search failed for ref={api_ref_no}"
        page.click_view_first_row()
        ui_ref_no = page.get_form_field_value("Transaction Ref No")
        ui_total = page.get_form_field_value("Total PO Amount")
        assert ui_ref_no.strip() == api_ref_no, f"Ref No mismatch: UI='{ui_ref_no}' API='{api_ref_no}'"
        assert float(ui_total.strip()) == float(api_total), f"Total mismatch: UI='{ui_total}' API='{api_total}'"
        log.info(f"UI values match API: Ref={api_ref_no}, Total={api_total}")
        page.close_popup()

    @pytest.mark.hybrid
    def test_UI04_add_form_opens_and_cancels(self, po_page):
        log.info("UI-04: Add form opens on click, closes on cancel")
        page = po_page
        page.open_add_form()
        assert page._is_form_popup_open(), "Add form popup should be visible after clicking Add"
        page.force_close_form_popup()
        assert not page._is_form_popup_open(), "Form popup should close after clicking Cancel"

    @pytest.mark.hybrid
    def test_UI05_negative_search_no_results(self, po_page):
        log.info("UI-05: Search non-existent ID returns empty results")
        page = po_page
        page.click_refresh()
        found = page.search_po("ID-DOES-NOT-EXIST-999999")
        assert not found, "Search for non-existent ID should return False"

    @pytest.mark.hybrid
    def test_UI06_refresh_loads_latest_data(self, po_page, po_api):
        log.info("UI-06: Create via API, refresh, new row appears in table")
        page = po_page
        entry_id, ref_no = self._create_and_get_ref(po_api, supplier_ref_id=1,
            parameter2=1, parameter3=25, parameter4=1)

        page.click_refresh()
        found = page.search_po_verify_row(ref_no)
        assert found, f"PO {ref_no} not found in table after refresh"

    @pytest.mark.hybrid
    def test_UI07_edit_form_opens(self, po_page, po_api):
        log.info("UI-07: Edit form opens from row menu")
        page = po_page
        entry_id, ref_no = self._create_and_get_ref(po_api, supplier_ref_id=1,
            parameter2=1, parameter3=25, parameter4=1)

        page.click_refresh()
        found = page.search_po(ref_no)
        assert found, f"Search failed for ref={ref_no}"
        page.edit_first_row()
        assert page._is_form_popup_open(), "Edit form popup should be visible"
        assert page.has_update_button(), "Edit form should show Submit button"
        page.close_popup()
