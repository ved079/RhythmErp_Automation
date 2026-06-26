import sys
import os
from datetime import datetime
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.tax_rate.tax_rate_page import TaxRatePage


def _make_name(prefix="TR"):
    ts = datetime.now().strftime("%H%M%S%f")[:10]
    return prefix + "".join(chr(ord("A") + int(c)) for c in ts)


def _valid_header(name=None):
    return {
        "tax_rate_name": name or _make_name("TRU"),
        "tax_type": "GST",
        "tax_authority": "CGST Authority",
        "from_date": "2025-04-01",
        "to_date": "2026-03-31",
        "revision_status": "Active",
    }


def _valid_sub_rows():
    return [{"hsn_number": "995411", "tax_rate": 18.0}]


@pytest.mark.ui
class TestTaxRateUI:
    """UI tests for Tax Rate (replaces test_tax_rate_validation.py)."""

    def _cleanup(self, page):
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.hard_refresh()
        except Exception:
            pass

    # --- STANDALONE TESTS ---

    def test_empty_form_shows_error(self, logged_in_driver):
        """Submit empty form — must show Validation Failed alert."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            page.submit()
            assert page.is_validation_alert_present(timeout=5), \
                "Empty form must trigger Validation Failed alert"
        finally:
            self._cleanup(page)

    def test_missing_name_rejected(self, logged_in_driver):
        """Submit with all fields filled except tax_rate_name — must show validation error."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            header = _valid_header(name="")
            page.fill_all_fields(header)
            page.fill_sub_table(_valid_sub_rows())
            page.submit()
            assert page.is_validation_alert_present(timeout=5), \
                "Missing tax rate name must trigger validation alert"
        finally:
            self._cleanup(page)

    def test_missing_from_date_rejected(self, logged_in_driver):
        """Submit without from_date — must show validation error."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            header = _valid_header()
            header["from_date"] = ""
            page.fill_all_fields(header)
            page.fill_sub_table(_valid_sub_rows())
            page.submit()
            assert page.is_validation_alert_present(timeout=5), \
                "Missing from_date must trigger validation alert"
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        """Fill form header then cancel — record must NOT be created."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            header = _valid_header()
            page.open_add_form()
            page.fill_all_fields(header)
            page.cancel()
            page.hard_refresh()
            # Verify the record was not created (search should show no match)
            rows = page.driver.execute_script("""
                var trs = document.querySelectorAll('table#excel-table tbody tr');
                var found = false;
                for (var i=0; i<trs.length; i++) {
                    if (trs[i].textContent.indexOf(arguments[0]) !== -1) {
                        found = true; break;
                    }
                }
                return found;
            """, header["tax_rate_name"])
            assert not rows, "Cancelled record must not appear in table"
        finally:
            self._cleanup(page)

    def test_successful_create(self, logged_in_driver):
        """Create a full tax rate record and verify it appears in the table."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            name = _make_name("CRT")
            data = {"header": _valid_header(name), "sub_table_rows": _valid_sub_rows()}
            result = page.create_record(data)
            assert result.get("status") == "success", \
                f"Create failed: {result.get('error')}"
            page.hard_refresh()
            page.search_and_verify(name)
            found = page.driver.execute_script("""
                var trs = document.querySelectorAll('table#excel-table tbody tr');
                for (var i=0; i<trs.length; i++) {
                    if (trs[i].textContent.indexOf(arguments[0]) !== -1) return true;
                }
                return false;
            """, name)
            assert found, "Created tax rate must appear in table"
        finally:
            self._cleanup(page)

    def test_edit_button_disabled(self, logged_in_driver):
        """Edit button must be disabled for all rows (ERP feature — use Version instead)."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            row_count = page.driver.execute_script(
                "return document.querySelectorAll('table#excel-table tbody tr').length;"
            )
            if row_count == 0:
                pytest.skip("No rows in table to check Edit button state")
            assert page.is_edit_button_disabled(0), \
                "Edit button must be disabled for Tax Rate rows (Version is used instead)"
        finally:
            self._cleanup(page)

    # --- TESTS USING shared_tax_rate ---

    def test_view_mode_readonly(self, logged_in_driver, shared_tax_rate):
        """View mode must have all fields disabled."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            name = shared_tax_rate["header"]["tax_rate_name"]
            page.search_and_verify(name)
            page.click_view_on_row(0)
            assert page.is_view_mode(), "All fields must be disabled in view mode"
            page.cancel()
        finally:
            self._cleanup(page)

    def test_history_opens_after_create(self, logged_in_driver, shared_tax_rate):
        """History popup must open for a created tax rate record."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            name = shared_tax_rate["header"]["tax_rate_name"]
            page.search_and_verify(name)
            page.click_history_on_row(0)
            assert page.is_history_popup_open(timeout=5), \
                "History popup must be open after clicking history button"
            page.close_history_popup()
        finally:
            self._cleanup(page)

    def test_create_version_form_opens(self, logged_in_driver, shared_tax_rate):
        """Click Version on shared record — form must open with 'Create Version' button."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            name = shared_tax_rate["header"]["tax_rate_name"]
            page.search_and_verify(name)
            page.click_version_on_row(0)
            assert page.is_form_open(), "Version form must be open"
            # Verify the form has a Create Version button (not Submit)
            has_version_btn = page.driver.execute_script("""
                var btns = document.querySelectorAll('.popup-footer button');
                for (var i=0; i<btns.length; i++) {
                    if (btns[i].textContent.trim().indexOf('Create Version') !== -1) return true;
                }
                return false;
            """)
            assert has_version_btn, "Form opened via Version must have 'Create Version' button"
            page.cancel()
        finally:
            self._cleanup(page)

    def test_version_empty_name_blocked(self, logged_in_driver, shared_tax_rate):
        """Open Version form, clear name, submit — must be blocked by validation."""
        page = TaxRatePage(logged_in_driver)
        try:
            page.navigate_to_page()
            name = shared_tax_rate["header"]["tax_rate_name"]
            page.search_and_verify(name)
            page.click_version_on_row(0)
            assert page.is_form_open(), "Version form must be open"
            # Clear the tax rate name via JS
            page.driver.execute_script("""
                var input = document.querySelector('input[name="Tax Rate Name"]');
                if (!input) return;
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(input, '');
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
            """)
            page.submit()
            assert page.is_validation_alert_present(timeout=5), \
                "Clearing name and submitting version must trigger validation alert"
        finally:
            self._cleanup(page)
