import sys
import os
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.tax_authority.tax_authority_page import TaxAuthorityPage
from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    valid_tax_authority_data,
    generate_tax_name,
    special_chars_tax_name,
)


@pytest.mark.ui
class TestTaxAuthorityUI:
    """UI tests for Tax Authority (replaces test_tax_authority_validation.py)."""

    def _cleanup(self, page):
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.hard_refresh()

    # --- STANDALONE TESTS ---

    def test_empty_form_shows_error(self, logged_in_driver):
        """Submit empty form — must show Validation Failed alert."""
        page = TaxAuthorityPage(logged_in_driver)
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

    def test_missing_tax_name_rejected(self, logged_in_driver):
        """Submit without tax name — must show validation error."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = valid_tax_authority_data()
            page.select_tax_type(data["tax_type"])
            page.select_country(data["country"])
            # Leave tax_name empty
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing tax name must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_missing_tax_type_rejected(self, logged_in_driver):
        """Submit without tax type selected — must show validation error."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = valid_tax_authority_data()
            page.fill_tax_name(data["tax_name"])
            page.select_country(data["country"])
            # Leave tax_type unselected
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing tax type must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_missing_country_rejected(self, logged_in_driver):
        """Submit without country selected — must show validation error."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = valid_tax_authority_data()
            page.fill_tax_name(data["tax_name"])
            page.select_tax_type(data["tax_type"])
            # Leave country unselected
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Missing country must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_special_chars_in_name_rejected(self, logged_in_driver):
        """Tax name with special characters must be rejected."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.open_add_form()
            data = special_chars_tax_name()
            page.fill_tax_name(data["tax_name"])
            page.select_tax_type(data["tax_type"])
            page.select_country(data["country"])
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Special chars in tax name must trigger validation alert"
            page.handle_validation_warning(timeout=5)
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        """Fill form then cancel — record must NOT be created."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = valid_tax_authority_data()
            page.open_add_form()
            page.fill_tax_name(data["tax_name"])
            page.select_tax_type(data["tax_type"])
            page.select_country(data["country"])
            page.cancel()
            page.hard_refresh()
            assert not page.is_record_present(data["tax_name"]), \
                "Cancelled record must not appear in table"
        finally:
            self._cleanup(page)

    def test_successful_create_and_search(self, logged_in_driver):
        """Create a tax authority and verify it appears in the table."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            data = valid_tax_authority_data()
            result = page.create_record(data)
            assert result.get("status") == "success", \
                f"Create failed: {result.get('error')}"
            page.hard_refresh()
            assert page.is_record_present(data["tax_name"]), \
                "Created tax authority must appear in table"
        finally:
            self._cleanup(page)

    # --- TESTS USING shared_tax_authority ---

    def test_view_mode_readonly(self, logged_in_driver, shared_tax_authority):
        """View mode must have all fields disabled."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.click_view_button(row_index=0)
            assert page.is_view_mode(), "All fields must be disabled in view mode"
            page.cancel()
        finally:
            self._cleanup(page)

    def test_history_opens_after_create(self, logged_in_driver, shared_tax_authority):
        """History popup must open for a created tax authority record."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.click_history_button(row_index=0)
            assert page.is_history_popup_open(), \
                "History popup must be open after clicking history button"
        finally:
            self._cleanup(page)

    def test_edit_empty_name_blocked(self, logged_in_driver, shared_tax_authority):
        """Open edit mode, clear tax name, submit — must be blocked by validation."""
        page = TaxAuthorityPage(logged_in_driver)
        try:
            page.navigate_to_page()
            page.click_edit_button(row_index=0)
            assert page.is_edit_mode(), "Form must open in edit mode"
            # Clear the tax name via JS
            page.driver.execute_script("""
                var input = document.querySelector('input[name="Tax Name"]');
                if (!input) return;
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(input, '');
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
            """)
            page.submit()
            assert page.is_validation_alert_present(timeout=3), \
                "Clearing tax name and submitting must trigger validation alert"
            page.handle_validation_warning(timeout=5)
        finally:
            self._cleanup(page)
