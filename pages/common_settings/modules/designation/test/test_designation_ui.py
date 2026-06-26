import sys
import os
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.designation.designation_page import DesignationPage
from pages.common_settings.modules.designation.data.designation_data import (
    generate_valid_designation_data,
    generate_string_255,
    generate_special_char_name,
    generate_digits_only,
    generate_spaces_only,
)


@pytest.mark.ui
class TestDesignationUI:
    """UI validation tests for Designation (replaces old test_designation_validation.py)."""

    def _cleanup(self, page):
        if page.is_add_form_open():
            page.force_close_form_popup()
        page.hard_refresh()

    def test_empty_name_shows_error(self, logged_in_driver):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            page.submit()
            assert page.is_validation_alert_present(timeout=3) is True
            page.handle_validation_warning()
            assert page.get_mat_error_text(page.NAME_INPUT) != ""
            assert page.is_add_form_open() is True
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_special_char_name_rejected(self, logged_in_driver):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_designation_data()
            data["name"] = generate_special_char_name()
            page.fill_designation_form(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3) is True
            page.handle_validation_warning()
            assert page.has_field_error("Name") is True or page.has_name_invalid_class() is True
            assert page.is_add_form_open() is True
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_digits_only_name_rejected(self, logged_in_driver):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_designation_data()
            data["name"] = generate_digits_only()
            page.fill_designation_form(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3) is True
            page.handle_validation_warning()
            assert page.has_field_error("Name") is True or page.has_name_invalid_class() is True
            assert page.is_add_form_open() is True
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_spaces_only_name_rejected(self, logged_in_driver):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_designation_data()
            data["name"] = generate_spaces_only()
            page.fill_designation_form(data)
            page.submit()
            assert page.is_validation_alert_present(timeout=3) is True
            page.handle_validation_warning()
            assert page.has_field_error("Name") is True or page.has_name_invalid_class() is True
            assert page.is_add_form_open() is True
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_designation_data()
            page.fill_designation_form(data)
            page.cancel()
            page.hard_refresh()
            page.search_designation(data["name"])
            assert page.is_designation_in_table(data["name"]) is False
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_255_char_name_accepted(self, logged_in_driver):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_designation_data()
            data["name"] = generate_string_255()
            page.fill_designation_form(data)
            page.submit()
            page.handle_success_alert()
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_view_mode_readonly(self, logged_in_driver, shared_designation):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            name = shared_designation["name"]
            page.search_and_verify(name)
            page.click_view_button(name)
            page.verify_view_popup_read_only()
            page.close_popup()
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_edit_empty_name_blocked(self, logged_in_driver, shared_designation):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            name = shared_designation["name"]
            page.search_and_verify(name)
            page.click_edit_button(name)
            el = page.driver.find_element("css selector", "input[name='Name']")
            page.driver.execute_script(
                "var ns=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
                "ns.call(arguments[0],'');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                el
            )
            page.click_update()
            assert page.is_validation_alert_present(timeout=3) is True
            page.handle_validation_warning()
            assert page.get_mat_error_text(page.NAME_INPUT) != ""
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_history_opens_for_shared_record(self, logged_in_driver, shared_designation):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            name = shared_designation["name"]
            page.search_and_verify(name)
            page.click_history_button(name)
            assert page.is_history_popup_open(), "History popup must open"
            page.close_history_popup()
        except Exception:
            raise
        finally:
            self._cleanup(page)

    def test_status_toggle_persists(self, logged_in_driver):
        page = DesignationPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_designation_data()
            page.fill_designation_form(data)
            page.submit()
            page.handle_success_alert()
            page.hard_refresh()
            name = data["name"]
            page.search_and_verify(name)
            page.click_edit_button(name)
            was_active = page.get_toggle_state()
            page.toggle_status()
            page.click_update()
            page.handle_success_alert()
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_edit_button(name)
            assert page.get_toggle_state() is not was_active, \
                "Toggle state must change after update"
        except Exception:
            raise
        finally:
            self._cleanup(page)
