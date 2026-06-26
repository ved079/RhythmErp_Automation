import sys
import os
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.hsn_sac.hsn_sac_page import HsnSacPage
from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    generate_valid_hsn_sac_data,
    missing_number_data,
    missing_type_data,
    missing_description_data,
    special_chars_number_data,
)


@pytest.mark.ui
class TestHsnSacUI:
    """UI tests for HSN SAC (replaces test_hsn_sac_validation.py)."""

    def _cleanup(self, page):
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.hard_refresh()

    # --- STANDALONE TESTS ---

    def test_empty_form_shows_error(self, logged_in_driver):
        """Submit empty form — must show Validation Failed alert."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Empty form submit must trigger Validation Failed alert"
            page.handle_validation_warning(timeout=3)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_missing_hsn_number_shows_error(self, logged_in_driver):
        """Submit with no HSN number — must show validation error."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = missing_number_data()
            page.fill_all_fields(data)
            page._force_close_panels()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing HSN number must trigger validation alert"
            page.handle_validation_warning(timeout=3)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_missing_type_shows_error(self, logged_in_driver):
        """Submit with no HSN SAC Type — must show validation error."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = missing_type_data()
            page.fill_all_fields(data)
            page._force_close_panels()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing type must trigger validation alert"
            page.handle_validation_warning(timeout=3)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_missing_description_shows_error(self, logged_in_driver):
        """Submit with no description — must show validation error."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = missing_description_data()
            page.fill_all_fields(data)
            page._force_close_panels()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing description must trigger validation alert"
            page.handle_validation_warning(timeout=3)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_special_chars_in_number_rejected(self, logged_in_driver):
        """HSN number with @#$% must be rejected by frontend."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = special_chars_number_data()
            page.fill_all_fields(data)
            page._force_close_panels()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Special chars in HSN number must trigger validation alert"
            page.handle_validation_warning(timeout=3)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        """Fill form then cancel — record must NOT be created."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_hsn_sac_data()
            page.open_add_form()
            page.fill_all_fields(data)
            page.cancel()
            page.hard_refresh()
            assert page.is_hsn_in_table(data["hsn_sac_number"]) is False, \
                "Cancelled record must not appear in table"
        finally:
            self._cleanup(page)

    def test_successful_create_and_search(self, logged_in_driver):
        """Create a record and verify it appears in search results."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_hsn_sac_data()
            result = page.create_hsn_sac(data)
            assert result.get("status") == "success", f"Create failed: {result.get('error')}"
            page.search_and_verify(data["hsn_sac_number"])
            assert page.is_hsn_in_table(data["hsn_sac_number"]), \
                "Created record must appear in search results"
        finally:
            self._cleanup(page)

    # --- TESTS USING shared_hsn_sac ---

    def test_view_mode_readonly(self, logged_in_driver, shared_hsn_sac):
        """View mode must have all fields disabled."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_and_verify(shared_hsn_sac["hsn_sac_number"])
            page.click_view_button(hsn_number=shared_hsn_sac["hsn_sac_number"])
            assert page.is_view_mode(), "All fields must be disabled in view mode"
            page.close_popup()
        finally:
            self._cleanup(page)

    def test_history_opens_after_create(self, logged_in_driver, shared_hsn_sac):
        """History popup must open for a created record."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_and_verify(shared_hsn_sac["hsn_sac_number"])
            page.click_history_button(hsn_number=shared_hsn_sac["hsn_sac_number"])
            assert page.is_history_popup_open(), "History popup must open"
            page.close_history_popup()
        finally:
            self._cleanup(page)

    def test_edit_empty_number_blocked(self, logged_in_driver, shared_hsn_sac):
        """Clear HSN number in edit mode — update must be blocked."""
        page = HsnSacPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_and_verify(shared_hsn_sac["hsn_sac_number"])
            page.click_edit_button(hsn_number=shared_hsn_sac["hsn_sac_number"])
            assert page.is_edit_mode(), "Form must open in edit mode"
            # Clear HSN number via JS
            el = page.driver.find_element("css selector", "input[name='HSN SAC No']")
            page.driver.execute_script(
                "var ns=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
                "ns.call(arguments[0],'');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                el
            )
            page.click_update()
            assert page.is_validation_alert_present(timeout=3), \
                "Empty HSN number on edit must be blocked"
            page.handle_validation_warning(timeout=3)
        finally:
            self._cleanup(page)
