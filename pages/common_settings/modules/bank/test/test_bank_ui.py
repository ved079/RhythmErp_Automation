import sys
import os
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.bank.bank_page import BankPage
from pages.common_settings.modules.bank.data.bank_data import (
    generate_valid_bank_data,
    generate_bank_name_with_digits,
    generate_special_char_name,
)


@pytest.mark.ui
class TestBankUI:
    """UI tests for Bank (replaces test_bank_validation.py)."""

    def _cleanup(self, page):
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.hard_refresh()

    # --- STANDALONE TESTS ---

    def test_empty_form_shows_error(self, logged_in_driver):
        """Submit empty form — must show Validation Failed alert."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Empty form must trigger Validation Failed alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_bank_name_with_digits_rejected(self, logged_in_driver):
        """Bank name containing digits must be rejected by frontend (alpha-only rule)."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_bank_data()
            data["bank_name"] = generate_bank_name_with_digits()
            page.fill_bank_form(data)
            page._force_close_panels()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Bank name with digits must trigger validation alert (alpha-only rule)"
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_bank_name_special_chars_rejected(self, logged_in_driver):
        """Bank name with @#$ must be rejected by frontend."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_bank_data()
            data["bank_name"] = generate_special_char_name()
            page.fill_bank_form(data)
            page._force_close_panels()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Special chars in bank name must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_bank_name_too_short_rejected(self, logged_in_driver):
        """Bank name shorter than 10 chars must be rejected by frontend."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = generate_valid_bank_data()
            data["bank_name"] = "SHORT"  # 5 chars, below 10-char minimum
            page.fill_bank_form(data)
            page._force_close_panels()
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Bank name shorter than 10 chars must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open()
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        """Fill form then cancel — record must NOT be created."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_bank_data()
            page.open_add_form()
            page.fill_bank_form(data)
            page.cancel()
            page.hard_refresh()
            assert page.is_bank_in_table(data["bank_name"]) is False, \
                "Cancelled record must not appear in table"
        finally:
            self._cleanup(page)

    def test_successful_create_and_search(self, logged_in_driver):
        """Create a bank and verify it appears in search results."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = generate_valid_bank_data()
            result = page.create_bank(data)
            assert result.get("status") == "PASSED", \
                f"Create failed: {result.get('error')}"
            page.search_and_verify(data["bank_name"])
            assert page.is_bank_in_table(data["bank_name"]), \
                "Created bank must appear in search results"
        finally:
            self._cleanup(page)

    def test_status_default_is_active(self, logged_in_driver):
        """New bank record status must default to Active (True)."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            state = page.get_toggle_state("Status")
            assert state is True, "Status toggle must default to Active (True)"
        finally:
            self._cleanup(page)

    # --- TESTS USING shared_bank ---

    def test_view_mode_readonly(self, logged_in_driver, shared_bank):
        """View mode must have all fields disabled."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_and_verify(shared_bank["bank_name"])
            page.click_view_button(shared_bank["bank_name"])
            assert page.is_view_mode(), "All fields must be disabled in view mode"
            page.close_popup()
        finally:
            self._cleanup(page)

    def test_history_opens_after_create(self, logged_in_driver, shared_bank):
        """History popup must open for a created bank record."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_and_verify(shared_bank["bank_name"])
            page.click_history_button(shared_bank["bank_name"])
            history_els = page.driver.find_elements(
                "css selector", "app-dynamic-history"
            )
            assert len(history_els) > 0, "History component must be present after click"
        finally:
            self._cleanup(page)

    def test_edit_mode_loads_prepopulated(self, logged_in_driver, shared_bank):
        """Open edit mode — form must open with existing values prepopulated."""
        page = BankPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.search_and_verify(shared_bank["bank_name"])
            page.click_edit_button(shared_bank["bank_name"])
            assert page.is_edit_mode(), "Form must open in edit mode"
            actual_name = page.get_input_value("Bank Name")
            assert shared_bank["bank_name"] in actual_name, \
                f"Bank name must be prepopulated in edit mode. Got: '{actual_name}'"
        finally:
            self._cleanup(page)
