import sys
import os
import time
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.uom.uom_page import UOMPage
from pages.common_settings.modules.uom.data.uom_data import (
    generate_uom_data, generate_special_char_uom_code
)


@pytest.mark.ui
class TestUOMUI:
    """UI validation tests for UOM (replaces old test_uom_validation.py)."""

    def _cleanup(self, uom_page):
        if uom_page.is_add_form_open():
            uom_page.force_close_form_popup()
        uom_page.hard_refresh()

    def test_special_char_code_rejected_by_frontend(self, logged_in_driver):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.open_add_form()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, "AB!@#$%^")
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "special char test")
            uom_page.submit()
            assert uom_page.is_validation_alert_present(timeout=3) is True
            uom_page.handle_validation_warning()
            assert uom_page.is_add_form_open() is True
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_256_char_code_autocutoff_in_browser(self, logged_in_driver):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.open_add_form()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, "A" * 256)
            value = uom_page.get_field_value(uom_page.UOM_CODE_INPUT)
            assert len(value) == 255
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_256_char_description_autocutoff_in_browser(self, logged_in_driver):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.open_add_form()
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "D" * 256)
            value = uom_page.get_field_value(uom_page.UOM_DESCRIPTION_INPUT)
            assert len(value) == 255
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_empty_code_shows_mat_error(self, logged_in_driver):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.open_add_form()
            uom_page.submit()
            assert uom_page.is_validation_alert_present(timeout=3) is True
            uom_page.handle_validation_warning()
            assert uom_page.get_mat_error_text(uom_page.UOM_CODE_INPUT) != ""
            assert uom_page.is_add_form_open() is True
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_hyphen_underscore_code_accepted_by_frontend(self, logged_in_driver):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.open_add_form()
            uom_data = generate_uom_data()
            uom_code = uom_data["uom_code"][:4] + "-_AB"
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "hyphen underscore test")
            uom_page.submit()
            assert uom_page.is_validation_alert_present(timeout=3) is False, \
                "Hyphen and underscore should be accepted — no validation alert expected"
            uom_page.handle_success_alert()
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_cancel_discards_form(self, logged_in_driver):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.open_add_form()
            uom_data = generate_uom_data()
            uom_code = uom_data["uom_code"]
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "cancel test")
            uom_page.close_popup()
            uom_page.hard_refresh()
            uom_page.search_uom(uom_code)
            assert uom_page.is_uom_in_table(uom_code) is False
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_view_mode_readonly(self, logged_in_driver, shared_uom_code):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.search_and_verify(shared_uom_code)
            uom_page.click_view_button(shared_uom_code)
            uom_page.verify_view_popup_read_only()
            uom_page.close_popup()
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_edit_empty_code_blocked_by_frontend(self, logged_in_driver, shared_uom_code):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.search_and_verify(shared_uom_code)
            uom_page.click_edit_button(shared_uom_code)
            css = uom_page.UOM_CODE_INPUT[1]
            el = uom_page.driver.find_element("css selector", css)
            uom_page.driver.execute_script(
                "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                "nativeSetter.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                el
            )
            uom_page.click_update()
            assert uom_page.is_validation_alert_present(timeout=3) is True
            uom_page.handle_validation_warning()
            assert uom_page.get_mat_error_text(uom_page.UOM_CODE_INPUT) != ""
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_history_shows_after_edit(self, logged_in_driver, shared_uom_code):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.search_and_verify(shared_uom_code)
            uom_page.click_edit_button(shared_uom_code)
            uom_page.update_uom_description("History test edit")
            uom_page.click_update()
            uom_page.handle_success_alert()
            uom_page.hard_refresh()
            uom_page.search_and_verify(shared_uom_code)
            uom_page.click_history_button(shared_uom_code)
            assert uom_page.is_history_empty() is False
            assert uom_page.get_history_row_count() >= 1
            uom_page.close_history_popup()
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_status_toggle_persists(self, logged_in_driver):
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        try:
            uom_page.navigate_to_page()
            uom_page.open_add_form()
            uom_data = generate_uom_data()
            uom_code = uom_data["uom_code"]
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "status toggle test")
            uom_page.submit()
            uom_page.handle_success_alert()
            uom_page.hard_refresh()
            uom_page.search_and_verify(uom_code)
            uom_page.click_edit_button(uom_code)
            uom_page.toggle_status()
            uom_page.click_update()
            uom_page.handle_success_alert()
            uom_page.hard_refresh()
            uom_page.search_and_verify(uom_code)
            uom_page.click_edit_button(uom_code)
            assert uom_page.get_toggle_status() == "Inactive"
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)
