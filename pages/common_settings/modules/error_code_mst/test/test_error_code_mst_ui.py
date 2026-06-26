import sys
import os
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.error_code_mst.error_code_mst_page import ErrorCodeMstPage
from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    generate_valid_error_code_mst_data,
    generate_create_without_description,
    missing_code_data,
    missing_dropdown_data,
    special_chars_code_data,
    TOGGLE_AMOUNT,
    TOGGLE_QUANTITY,
)


@pytest.mark.ui
class TestErrorCodeMstUI:
    """UI tests for Error Code Mst (replaces test_error_code_mst_validation.py)."""

    def _cleanup(self, page):
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.hard_refresh()

    # --- STANDALONE TESTS ---

    def test_empty_form_shows_error(self, logged_in_driver):
        """Submit empty form — must show Validation Failed alert."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Empty form must trigger Validation Failed alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_missing_code_shows_error(self, logged_in_driver):
        """Submit with no error code — must show validation error."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = missing_code_data()
            page.fill_all_fields(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing code must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_missing_type_shows_error(self, logged_in_driver):
        """Submit with no Error Code Type — must show validation error."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = missing_dropdown_data()
            page.fill_all_fields(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing type must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_special_chars_in_code_rejected(self, logged_in_driver):
        """Code with @#$%^&*() must be rejected by frontend."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = special_chars_code_data()
            page.fill_all_fields(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Special chars in code must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_description_is_optional(self, logged_in_driver):
        """Create record without description — must succeed (description is optional)."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_create_without_description()
            result = page.create_record(data)
            assert result.get("status") == "success", \
                f"Create without description must succeed. Got: {result.get('error')}"
            assert page.is_code_in_table(data["code"]), \
                "Created record must appear in table"
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        """Fill form then cancel — record must NOT be created."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_error_code_mst_data()
            page.open_add_form()
            page.fill_all_fields(data)
            page.cancel()
            page.hard_refresh()
            assert page.is_code_in_table(data["code"]) is False, \
                "Cancelled record must not appear in table"
        finally:
            self._cleanup(page)

    def test_successful_create_and_search(self, logged_in_driver):
        """Create a record and verify it appears in search results."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_error_code_mst_data()
            result = page.create_record(data)
            assert result.get("status") == "success", f"Create failed: {result.get('error')}"
            page.search_record(data["code"])
            assert page.is_code_in_table(data["code"]), \
                "Created record must appear in search results"
        finally:
            self._cleanup(page)

    # --- TESTS USING shared_error_code_mst ---

    def test_view_mode_readonly(self, logged_in_driver, shared_error_code_mst):
        """View mode must have all fields disabled."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_record(shared_error_code_mst["code"])
            page.click_view_on_row(0)
            assert page.is_view_mode(), "All fields must be disabled in view mode"
            page.close_popup()
        finally:
            self._cleanup(page)

    def test_history_opens_after_create(self, logged_in_driver, shared_error_code_mst):
        """History popup must open for a created record."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_record(shared_error_code_mst["code"])
            page.click_history_on_row(0)
            assert page.is_history_popup_open(), "History popup must open"
            page.close_history_popup()
        finally:
            self._cleanup(page)

    def test_edit_empty_code_blocked(self, logged_in_driver, shared_error_code_mst):
        """Clear code in edit mode — update must be blocked."""
        page = ErrorCodeMstPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_record(shared_error_code_mst["code"])
            page.click_edit_on_row(0)
            assert page.is_edit_mode(), "Form must open in edit mode"
            # Clear code via JS
            el = page.driver.find_element("css selector", "input[name='Code']")
            page.driver.execute_script(
                "var ns=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
                "ns.call(arguments[0],'');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                el
            )
            page.click_update()
            assert page.is_validation_alert_present(timeout=3), \
                "Empty code on edit must be blocked"
            page.handle_validation_warning(timeout=5)
        finally:
            self._cleanup(page)
